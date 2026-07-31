from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from config import ADMIN_USER, ADMIN_PASSWORD

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/admin")
def admin(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "request": request,
            "error": ""
        }
    )


@router.post("/admin")
def login(
    request: Request,
    usuario: str = Form(...),
    password: str = Form(...)
):

    if usuario == ADMIN_USER and password == ADMIN_PASSWORD:
        return RedirectResponse(
            url="/panel",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "request": request,
            "error": "Usuario o contraseña incorrectos"
        }
    )


@router.get("/panel")
def panel(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="panel.html",
        context={
            "request": request
        }
    )