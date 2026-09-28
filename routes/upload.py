from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
import os
import shutil
import tempfile
import pandas as pd
from services.buscador import recargar_catalogo

router = APIRouter()


@router.post("/upload")
async def upload_excel(archivo: UploadFile = File(...)):
    destino = "data/articulosExportados Santa Rosa.xlsx"
    columnas_requeridas = {"CLAVE", "DESCRIPCION", "PRECIO 1", "PRECIO 2", "PRECIO 3"}
    temporal = None

    try:
        with tempfile.NamedTemporaryFile(dir="data", suffix=".xlsx", delete=False) as tmp:
            temporal = tmp.name
            shutil.copyfileobj(archivo.file, tmp)

        nuevo = pd.read_excel(temporal)
        faltantes = columnas_requeridas.difference(nuevo.columns)
        if faltantes:
            raise HTTPException(
                status_code=400,
                detail=f"El Excel no contiene las columnas requeridas: {', '.join(sorted(faltantes))}",
            )

        os.replace(temporal, destino)
        temporal = None
        recargar_catalogo()
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"No se pudo procesar el Excel: {error}") from error
    finally:
        if temporal and os.path.exists(temporal):
            os.remove(temporal)

    return HTMLResponse("""
    <h2>✅ Catálogo actualizado correctamente.</h2>
    <br>
    <a href="/panel">Regresar al Panel</a>
    """)
