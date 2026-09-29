import pandas as pd
import os
import re
import unicodedata
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


def normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor).casefold())
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^\w]+", " ", texto).strip()


def buscar(texto):
    global df, _mtime
    mtime_actual = os.stat(archivo).st_mtime_ns
    if mtime_actual != _mtime:
        recargar_catalogo()

    terminos = normalizar_texto(texto).split()

    with _lock:
        catalogo = df.copy()

    if not terminos:
        return catalogo

    texto_productos = catalogo.apply(
        lambda fila: normalizar_texto(" ".join(str(valor) for valor in fila.values)),
        axis=1,
    )
    coincide = pd.Series(True, index=catalogo.index)
    for termino in terminos:
        coincide &= texto_productos.str.contains(termino, regex=False)

    resultados = catalogo[coincide]

    return resultados
