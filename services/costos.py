import base64
import json
import lzma
import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "serbi_costos.db"
DB_XZ_PREFIX = Path(__file__).resolve().parent.parent / "data" / "serbi_costos.db.xz.b64.part"
DB_GZIP_PREFIX = Path(__file__).resolve().parent.parent / "data" / "serbi_costos.db.gz.part"
MAX_RESULTS = 30


def normalizar_texto(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor).casefold())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^\w]+", " ", texto).strip()


def compacto(valor: str) -> str:
    return re.sub(r"[^a-z0-9]", "", normalizar_texto(valor))


def _materializar_db() -> None:
    if DB_PATH.exists():
        return

    parts_xz = sorted(DB_XZ_PREFIX.parent.glob(DB_XZ_PREFIX.name + "*"))
    if parts_xz:
        try:
            encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts_xz)
            DB_PATH.write_bytes(lzma.decompress(base64.b64decode(encoded)))
            return
        except (OSError, EOFError, lzma.LZMAError, ValueError):
            if DB_PATH.exists():
                DB_PATH.unlink()

    parts_gzip = sorted(DB_GZIP_PREFIX.parent.glob(DB_GZIP_PREFIX.name + "*"))
    if not parts_gzip:
        return
    import gzip
    try:
        encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts_gzip)
        DB_PATH.write_bytes(gzip.decompress(base64.b64decode(encoded)))
    except (OSError, EOFError, gzip.BadGzipFile, ValueError):
        if DB_PATH.exists():
            DB_PATH.unlink()


def _token_matches(token: str, producto: dict) -> bool:
    return token in producto["search_text"] or (len(token) >= 3 and token in producto["search_compact"])


def _score(query: str, producto: dict, tokens: list[str]) -> int:
    q_norm = normalizar_texto(query)
    q_compact = compacto(query)
    codigo = normalizar_texto(producto["codigo"])
    base = normalizar_texto(producto["codigo_base"])
    descripcion = normalizar_texto(producto["descripcion"])
    presentacion = normalizar_texto(producto["presentacion"])
    score = 0

    if codigo == q_norm:
        return 1000
    if compacto(producto["codigo"]) == q_compact and q_compact:
        return 950
    if base == q_norm or compacto(base) == q_compact:
        score += 800
    elif q_norm and q_norm in codigo:
        score += 600
    elif q_norm and q_norm in descripcion:
        score += 450

    for token in tokens:
        if token in codigo or token in base:
            score += 70
        elif token in descripcion:
            score += 50
        elif token in presentacion:
            score += 35
        elif token in producto["search_text"]:
            score += 20
        elif len(token) >= 3 and token in producto["search_compact"]:
            score += 15

    if tokens and all(_token_matches(token, producto) for token in tokens):
        score += 200
    else:
        return 0

    return score


@lru_cache(maxsize=1)
def cargar_productos() -> list[dict]:
    _materializar_db()
    if not DB_PATH.exists():
        return []
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT id,codigo,codigo_base,descripcion,lineas_json,presentacion,"
            "costos_por_linea_json,publico_por_linea_json,fuentes_costos_json,"
            "fuentes_publico_json,fecha_lista_display,paquete,search_text,search_compact "
            "FROM productos"
        ).fetchall()
    finally:
        con.close()

    productos = []
    for row in rows:
        try:
            productos.append(
                {
                    "id": row["id"],
                    "codigo": row["codigo"],
                    "codigo_base": row["codigo_base"],
                    "descripcion": row["descripcion"],
                    "lineas": json.loads(row["lineas_json"] or "[]"),
                    "presentacion": row["presentacion"] or "",
                    "costos_por_linea": json.loads(row["costos_por_linea_json"] or "{}"),
                    "publico_por_linea": json.loads(row["publico_por_linea_json"] or "{}"),
                    "fuentes_costos": json.loads(row["fuentes_costos_json"] or "[]"),
                    "fuentes_publico": json.loads(row["fuentes_publico_json"] or "[]"),
                    "fecha_lista_display": row["fecha_lista_display"] or "",
                    "paquete": row["paquete"] or "",
                    "search_text": row["search_text"] or "",
                    "search_compact": row["search_compact"] or "",
                }
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return productos


def recargar_costos() -> None:
    cargar_productos.cache_clear()


def buscar_costos(texto: str) -> list[dict]:
    query = (texto or "").strip()
    if len(query) < 2:
        return []
    normalizado = normalizar_texto(query)
    tokens = normalizado.split()
    candidatos = []
    for indice, producto in enumerate(cargar_productos()):
        score = _score(query, producto, tokens)
        if score > 0:
            candidatos.append((score, indice, producto))
    candidatos.sort(key=lambda item: (-item[0], item[1]))

    salida = []
    for score, _, producto in candidatos[:MAX_RESULTS]:
        item = dict(producto)
        item.pop("search_text", None)
        item.pop("search_compact", None)
        item["score"] = score
        salida.append(item)
    return salida


def resumen_costos() -> dict:
    productos = cargar_productos()
    return {
        "productos": len(productos),
        "fecha": productos[0]["fecha_lista_display"] if productos else "",
        "paquete": productos[0]["paquete"] if productos else "",
    }
