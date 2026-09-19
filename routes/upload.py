from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse
import shutil

router = APIRouter()


@router.post("/upload")
async def upload_excel(archivo: UploadFile = File(...)):

    destino = "data/articulosExportados Santa Rosa.xlsx"

    with open(destino, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)

    return HTMLResponse("""
    <h2>✅ Catálogo actualizado correctamente.</h2>
    <br>
    <a href="/panel">Regresar al Panel</a>
    """)