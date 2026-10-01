import os
import re
import unicodedata
from threading import RLock

import pandas as pd


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


def normalizar_codigo(valor):
    """Normaliza claves quitando guiones, puntos, espacios y otros separadores."""
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).casefold())
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^a-z0-9]+", "", texto)


def parece_codigo(texto):
    """Detecta búsquedas del tipo UF-0005.30, VC-0200, IM4340, etc."""
    compacto = normalizar_codigo(texto)
    return bool(compacto and re.search(r"[a-z]", compacto) and re.search(r"\d", compacto))


def buscar(texto):
    global df, _mtime

    mtime_actual = os.stat(archivo).st_mtime_ns
    if mtime_actual != _mtime:
        recargar_catalogo()

    consulta = str(texto or "").strip()
    if not consulta:
        with _lock:
            return df.copy()

    with _lock:
        catalogo = df.copy()

    # Para búsquedas de código, primero intentamos sobre CLAVE.
    # Esto evita que partes del código se encuentren accidentalmente
    # en precios, presentaciones u otros campos.
    if parece_codigo(consulta):
        consulta_codigo = normalizar_codigo(consulta)
        codigos = catalogo["CLAVE"].map(normalizar_codigo)

        exactos = catalogo[codigos == consulta_codigo]
        if not exactos.empty:
            return exactos

        # Si no existe el código exacto, mostramos coincidencias cercanas:
        # primero las que empiezan igual y luego las que contienen la consulta.
        empieza = codigos.str.startswith(consulta_codigo, na=False)
        contiene = codigos.str.contains(consulta_codigo, regex=False, na=False)
        similares = catalogo[empieza | contiene].copy()

        if not similares.empty:
            similares["_orden_busqueda"] = [
                0 if emp else 1
                for emp in empieza[similares.index]
            ]
            similares["_longitud_codigo"] = codigos[similares.index].str.len()
            similares = similares.sort_values(
                by=["_orden_busqueda", "_longitud_codigo"],
                kind="stable",
            )
            return similares.drop(columns=["_orden_busqueda", "_longitud_codigo"])

    # Búsqueda por nombre/descripción: cada palabra debe aparecer,
    # sin importar el orden y tolerando acentos y separadores.
    terminos = normalizar_texto(consulta).split()
    if not terminos:
        return catalogo.iloc[0:0]

    texto_productos = (
        catalogo["CLAVE"].fillna("").astype(str)
        .str.cat(catalogo["DESCRIPCION"].fillna("").astype(str), sep=" ")
        .map(normalizar_texto)
    )

    coincide = pd.Series(True, index=catalogo.index)
    for termino in terminos:
        coincide &= texto_productos.str.contains(termino, regex=False, na=False)

    return catalogo[coincide]


