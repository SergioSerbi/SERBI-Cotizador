from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import os
from datetime import datetime

from services.buscador import buscar
from routes.admin import router as admin_router
from routes.upload import router as upload_router

app = FastAPI(title="SERBI STOCK")

app.include_router(admin_router)
app.include_router(upload_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def inicio(request: Request):

    texto = request.query_params.get("buscar", "")

    resultados = buscar(texto).copy()

    # El nuevo Excel solo tiene una columna de Precio
    resultados["PRECIO COMPRA"] = (resultados["PRECIO COMPRA"] * 1.16).round(2)
    resultados["PRECIO 1"] = (resultados["PRECIO 1"] * 1.16).round(2)
    resultados["PRECIO 2"] = (resultados["PRECIO 2"] * 1.16).round(2)
    resultados["PRECIO 3"] = (resultados["PRECIO 3"] * 1.16).round(2)



    productos = resultados.head(50).to_dict(orient="records")

    archivo_excel = "data/articulosExportados Santa Rosa.xlsx"

    fecha_actualizacion = datetime.fromtimestamp(
        os.path.getmtime(archivo_excel)
    ).strftime("%d/%m/%Y %I:%M %p")

    return templates.TemplateResponse(
        request=request,
        name="cotizador_v3.html",
        context={
            "request": request,
            "productos": productos,
            "texto": texto,
            "fecha_actualizacion": fecha_actualizacion
        }
    )


@app.get("/buscar")
def buscar_ajax(texto: str = ""):

    import numpy as np

    resultados = buscar(texto).copy()

    resultados["PRECIO COMPRA"] = (resultados["PRECIO COMPRA"] * 1.16).round(2)
    resultados["PRECIO 1"] = (resultados["PRECIO 1"] * 1.16).round(2)
    resultados["PRECIO 2"] = (resultados["PRECIO 2"] * 1.16).round(2)
    resultados["PRECIO 3"] = (resultados["PRECIO 3"] * 1.16).round(2)

    resultados = resultados.replace({np.nan: ""})

    productos = resultados.head(50).to_dict(orient="records")

    return JSONResponse(content=productos)