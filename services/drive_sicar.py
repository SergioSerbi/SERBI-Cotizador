"""Descarga los respaldos SICAR desde Google Drive y actualiza existencias."""

from pathlib import Path
import tempfile

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from services.sicar_respaldo import consolidar_respaldos


BASE = Path(__file__).resolve().parent.parent
TOKEN = BASE / "token_drive.json"
SALIDA_JSON = BASE / "data" / "existencias_sucursales.json"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Identificador único de cada sucursal en el nombre de su respaldo UNIQUE.
SUCURSALES = {
    "A844E": "Santa Rosa",
    "3CB40": "Real del Valle",
    "D9435": "Clouthier",
    "D179": "Libramiento 3",
    "6717C": "Juárez",
}


def conectar_drive():
    """Obtiene una conexión autenticada de solo lectura con Google Drive."""
    if not TOKEN.exists():
        raise FileNotFoundError(f"No existe {TOKEN}")

    creds = Credentials.from_authorized_user_file(
        str(TOKEN),
        SCOPES,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds.valid:
        raise RuntimeError("Las credenciales de Google Drive no son válidas.")

    return build("drive", "v3", credentials=creds)


def buscar_respaldo_drive(drive, codigo: str) -> dict:
    """Busca en Drive el respaldo UNIQUE de una sucursal."""

    resultado = drive.files().list(
        pageSize=100,
        q="trashed = false",
        fields="files(id,name,size,modifiedTime)",
        orderBy="modifiedTime desc",
    ).execute()

    archivos = resultado.get("files", [])

    candidatos = [
    archivo
    for archivo in archivos
    if archivo.get("name", "").lower().endswith(".sr")
    and codigo in archivo.get("name", "")
]

    if not candidatos:
        raise RuntimeError(
            f"No se encontró respaldo UNIQUE para "
            f"{SUCURSALES[codigo]} ({codigo})."
        )

    return candidatos[0]


def descargar_archivo(drive, archivo: dict, destino: Path):
    """Descarga un archivo de Google Drive al destino indicado."""

    request = drive.files().get_media(fileId=archivo["id"])

    with destino.open("wb") as salida:
        downloader = MediaIoBaseDownload(salida, request)

        terminado = False

        while not terminado:
            estado, terminado = downloader.next_chunk()

            if estado:
                porcentaje = int(estado.progress() * 100)
                print(f"    {archivo['name']}: {porcentaje}%")


def actualizar_existencias():
    """Descarga los 5 respaldos y genera el JSON consolidado."""

    print("===== ACTUALIZANDO EXISTENCIAS DESDE GOOGLE DRIVE =====")

    drive = conectar_drive()

    # Todo se descarga primero a una carpeta temporal.
    # El JSON actual no se toca hasta que los 5 respaldos hayan sido procesados.
    with tempfile.TemporaryDirectory(prefix="serbi_sicar_") as temporal:
        carpeta = Path(temporal)

        archivos_descargados = []

        for codigo, sucursal in SUCURSALES.items():
            archivo = buscar_respaldo_drive(drive, codigo)

            print()
            print(f"{sucursal}")
            print(f"  Archivo: {archivo['name']}")
            print(f"  Fecha Drive: {archivo.get('modifiedTime', 'N/D')}")
            print(f"  Tamaño: {archivo.get('size', 'N/D')} bytes")

            destino = carpeta / archivo["name"]

            print("  Descargando...")
            descargar_archivo(drive, archivo, destino)

            if not destino.exists() or destino.stat().st_size == 0:
                raise RuntimeError(
                    f"La descarga de {archivo['name']} quedó vacía."
                )

            archivos_descargados.append(destino)

        print()
        print("===== 5 RESPALDOS DESCARGADOS =====")

        for archivo in archivos_descargados:
            print(f"- {archivo.name}: {archivo.stat().st_size:,} bytes")

        # Generamos el JSON en una ubicación temporal.
        json_temporal = carpeta / "existencias_sucursales.json"

        print()
        print("===== PROCESANDO RESPALDOS SICAR =====")

        resultado = consolidar_respaldos(
            carpeta,
            json_temporal,
        )

        if not json_temporal.exists():
            raise RuntimeError(
                "SICAR no generó el archivo existencias_sucursales.json."
            )

        # Solo después de que TODO salió bien reemplazamos el JSON utilizado
        # por el Cotizador.
        SALIDA_JSON.parent.mkdir(parents=True, exist_ok=True)

        json_temporal.replace(SALIDA_JSON)

        print()
        print("==========================================")
        print("ACTUALIZACIÓN COMPLETADA CORRECTAMENTE")
        print("==========================================")
        print(f"Productos: {len(resultado.get('inventarios', {}))}")
        print(f"Archivo: {SALIDA_JSON}")


if __name__ == "__main__":
    actualizar_existencias()