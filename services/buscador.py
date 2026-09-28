import pandas as pd
import os
from threading import RLock

archivo = "data/articulosExportados Santa Rosa.xlsx"
columnas_requeridas = {"CLAVE", "DESCRIPCION", "PRECIO 1", "PRECIO 2", "PRECIO 3"}
_lock = RLock()

df = pd.read_excel(archivo)
_mtime = os.stat(archivo).st_mtime_ns


def recargar_catalogo():
    """Lee el catálogo vigente después de que se reemplaza el Excel."""
    global df, _mtime
    nuevo = pd.read_excel(archivo)
    faltantes = columnas_requeridas.difference(nuevo.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(sorted(faltantes))}")
    with _lock:
        df = nuevo
        _mtime = os.stat(archivo).st_mtime_ns


def buscar(texto):
    global df, _mtime
    mtime_actual = os.stat(archivo).st_mtime_ns
    if mtime_actual != _mtime:
        recargar_catalogo()

    texto = str(texto).upper()

    with _lock:
        catalogo = df.copy()

    resultados = catalogo[
        catalogo.astype(str)
        .apply(lambda fila: fila.str.upper().str.contains(texto, regex=False))
        .any(axis=1)
    ]

    return resultados
