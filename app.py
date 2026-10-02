from collections import defaultdict, deque
from datetime import datetime
import hmac
import json
import base64
import binascii
from http.cookies import SimpleCookie
import os
import threading
import time

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import tempfile
import os

from services.buscador import buscar
from services.costos import buscar_costos, resumen_costos

app = FastAPI(title="SERBI Cotizador")
SECRET_KEY = os.getenv("SECRET_KEY", "")
ACCESS_PIN = os.getenv("ACCESS_PIN", "")
if not SECRET_KEY:
    raise RuntimeError("Falta configurar SECRET_KEY en el entorno")
if not ACCESS_PIN:
    raise RuntimeError("Falta configurar ACCESS_PIN en el entorno")

IS_PRODUCTION = (
    os.getenv("ENVIRONMENT", "").lower() == "production"
    or os.getenv("APP_ENV", "").lower() == "production"
    or os.getenv("RENDER", "").lower() == "true"
)
SESSION_MAX_AGE = 30 * 24 * 60 * 60
SESSION_COOKIE = "serbi_session"


class SignedSessionMiddleware:
    """Small ASGI cookie-session middleware using stdlib HMAC-SHA256."""

    def __init__(self, app, secret_key: str, secure: bool):
        self.app = app
        self.secret = secret_key.encode("utf-8")
        self.secure = secure

    def _decode(self, raw: str):
        try:
            payload, issued, signature = raw.split(".", 2)
            signed = f"{payload}.{issued}".encode("ascii")
            expected = hmac.new(self.secret, signed, "sha256").hexdigest()
            timestamp = int(issued)
            if not hmac.compare_digest(signature, expected) or time.time() - timestamp > SESSION_MAX_AGE or timestamp > time.time() + 60:
                return None
            encoded = payload + "=" * (-len(payload) % 4)
            value = json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")))
            return value if isinstance(value, dict) else None
        except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
            return None

    def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        cookies = SimpleCookie()
        try:
            cookies.load(headers.get(b"cookie", b"").decode("latin-1"))
        except Exception:
            pass
        morsel = cookies.get(SESSION_COOKIE)
        raw = morsel.value if morsel else ""
        loaded = self._decode(raw) if raw else None
        session = loaded or {}
        scope["session"] = session
        initial = dict(session)
        invalid_cookie = bool(raw and loaded is None)

        async def send_with_session(message):
            if message["type"] == "http.response.start":
                changed = scope["session"] != initial
                if changed or invalid_cookie:
                    headers_out = list(message.get("headers", []))
                    if scope["session"]:
                        issued = str(int(time.time()))
                        payload = base64.urlsafe_b64encode(
                            json.dumps(scope["session"], separators=(",", ":")).encode("utf-8")
                        ).decode("ascii").rstrip("=")
                        signed = f"{payload}.{issued}"
                        signature = hmac.new(self.secret, signed.encode("ascii"), "sha256").hexdigest()
                        value = f"{signed}.{signature}"
                        cookie = f"{SESSION_COOKIE}={value}; Path=/; Max-Age={SESSION_MAX_AGE}; HttpOnly; SameSite=Lax"
                        if self.secure:
                            cookie += "; Secure"
                    else:
                        cookie = f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
                        if self.secure:
                            cookie += "; Secure"
                    headers_out.append((b"set-cookie", cookie.encode("latin-1")))
                    message["headers"] = headers_out
            await send(message)

        return self.app(scope, receive, send_with_session)


templates = Jinja2Templates(directory="templates")

_failed_attempts = defaultdict(deque)
_attempts_lock = threading.Lock()
RATE_LIMIT = 5
RATE_WINDOW_SECONDS = 60


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def require_pin(request: Request, call_next):
    path = request.url.path
    if path == "/login" or path.startswith("/static/"):
        return await call_next(request)
    if request.session.get("authenticated") is True:
        return await call_next(request)
    if path.startswith("/api/") or path in {"/buscar", "/upload"} or path.startswith("/buscar/"):
        return JSONResponse({"detail": "Autenticación requerida"}, status_code=401)
    return RedirectResponse(url="/login", status_code=303)


app.add_middleware(SignedSessionMiddleware, secret_key=SECRET_KEY, secure=IS_PRODUCTION)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("authenticated") is True:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": ""})


@app.post("/login")
def login(request: Request, pin: str = Form(...)):
    now = time.monotonic()
    ip = client_ip(request)
    with _attempts_lock:
        attempts = _failed_attempts[ip]
        while attempts and now - attempts[0] >= RATE_WINDOW_SECONDS:
            attempts.popleft()
        if len(attempts) >= RATE_LIMIT:
            retry_after = max(1, int(RATE_WINDOW_SECONDS - (now - attempts[0])))
            return templates.TemplateResponse(
                request=request, name="login.html",
                context={"request": request, "error": "Demasiados intentos. Espera un minuto e inténtalo de nuevo."},
                status_code=429, headers={"Retry-After": str(retry_after)},
            )
        if hmac.compare_digest(pin, ACCESS_PIN):
            attempts.clear()
            request.session.clear()
            request.session["authenticated"] = True
            return RedirectResponse(url="/", status_code=303)
        attempts.append(now)
    return templates.TemplateResponse(
        request=request, name="login.html",
        context={"request": request, "error": "PIN incorrecto. Verifica e inténtalo de nuevo."},
        status_code=401,
    )


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


app.mount("/static", StaticFiles(directory="static"), name="static")


def productos_para(texto: str):
    resultados = buscar(texto).copy()
    for columna in ("PRECIO COMPRA", "PRECIO 1", "PRECIO 2", "PRECIO 3"):
        if columna in resultados:
            resultados[columna] = (resultados[columna] * 1.16).round(2)
    return resultados.fillna(0).head(50).to_dict(orient="records")


@app.get("/costos", response_class=HTMLResponse)
def costos_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="costos.html",
        context={"request": request, "resumen": resumen_costos()},
    )


@app.get("/api/costos")
def costos_ajax(texto: str = ""):
    return JSONResponse(content=buscar_costos(texto))


@app.get("/")
def inicio(request: Request):
    texto = request.query_params.get("buscar", "")
    productos = productos_para(texto)
    archivo_excel = "data/articulosExportados Santa Rosa.xlsx"
    fecha_actualizacion = datetime.fromtimestamp(os.path.getmtime(archivo_excel)).strftime("%d/%m/%Y %I:%M %p")
    return templates.TemplateResponse(
        request=request, name="cotizador_v3.html",
        context={"request": request, "productos": productos, "texto": texto, "fecha_actualizacion": fecha_actualizacion},
    )


@app.get("/v3")
def cotizador_v3(request: Request):
    return RedirectResponse(url="/", status_code=307)


@app.get("/buscar")
def buscar_ajax(texto: str = ""):
    return JSONResponse(content=productos_para(texto))


class ItemCotizacion(BaseModel):
    clave: str
    descripcion: str
    precio: float
    cantidad: int


class ExportarPDFRequest(BaseModel):
    productos: List[ItemCotizacion]
    mostrar_logo: bool = True


@app.post("/exportar-pdf")
def exportar_pdf(request: Request, datos: ExportarPDFRequest):
    from weasyprint import HTML, CSS
    from datetime import datetime

    total = sum(item.precio * item.cantidad for item in datos.productos)
    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    ruta_logo = os.path.join(os.path.dirname(__file__), "static", "img", "logo.png")

    html_content = templates.get_template("cotizacion_pdf.html").render(
        productos=datos.productos,
        total=total,
        fecha=fecha,
        mostrar_logo=datos.mostrar_logo,
        ruta_logo=ruta_logo,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        HTML(string=html_content).write_pdf(tmp.name)
        return FileResponse(
            tmp.name,
            media_type="application/pdf",
            filename=f"cotizacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            background=None,
        )
