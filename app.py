from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services.buscador import buscar

app = FastAPI(title="SERBI STOCK")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def inicio(request: Request):

    texto = request.query_params.get("buscar", "")

    resultados = buscar(texto).copy()

    resultados["PRECIO COMPRA"] = (resultados["PRECIO COMPRA"] * 1.16).round(2)
    resultados["PRECIO 1"] = (resultados["PRECIO 1"] * 1.16).round(2)
    resultados["PRECIO 2"] = (resultados["PRECIO 2"] * 1.16).round(2)
    resultados["PRECIO 3"] = (resultados["PRECIO 3"] * 1.16).round(2)

    resultados = resultados.fillna(0)

    productos = resultados.head(50).to_dict(orient="records")

    return templates.TemplateResponse(
        request=request,
        name="cotizador_v2.html",
        context={
            "request": request,
            "productos": productos,
            "texto": texto
        }
    )


@app.get("/v2")
def cotizador_v2(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="cotizador_v2.html",
        context={
            "request": request
        }
    )


@app.get("/buscar")
def buscar_ajax(texto: str = ""):

    resultados = buscar(texto).copy()

    resultados["PRECIO COMPRA"] = (resultados["PRECIO COMPRA"] * 1.16).round(2)
    resultados["PRECIO 1"] = (resultados["PRECIO 1"] * 1.16).round(2)
    resultados["PRECIO 2"] = (resultados["PRECIO 2"] * 1.16).round(2)
    resultados["PRECIO 3"] = (resultados["PRECIO 3"] * 1.16).round(2)

    resultados = resultados.fillna(0)

    productos = resultados.head(50).to_dict(orient="records")

    return JSONResponse(content=productos)