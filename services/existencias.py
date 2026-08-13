"""Acceso de solo lectura al catálogo consolidado de existencias SICAR."""

import json
from pathlib import Path

ARCHIVO = Path("data/existencias_sucursales.json")
_marca_archivo: int | None = None
_catalogo: dict = {"sucursales": [], "inventarios": {}}


def _cargar_si_cambio() -> dict:
    global _marca_archivo, _catalogo
    if not ARCHIVO.exists():
        return _catalogo
    marca = ARCHIVO.stat().st_mtime_ns
    if marca != _marca_archivo:
        _catalogo = json.loads(ARCHIVO.read_text(encoding="utf-8"))
        _marca_archivo = marca
    return _catalogo


def agregar_existencias(productos: list[dict]) -> list[dict]:
    catalogo = _cargar_si_cambio()
    inventarios = catalogo.get("inventarios", {})
    sucursales = catalogo.get("sucursales", [])
    for producto in productos:
        clave = str(producto.get("CLAVE", "")).strip()
        producto["EXISTENCIAS_SUCURSALES"] = [
            {"sucursal": sucursal, **inventarios.get(clave, {}).get(sucursal, {"existencia": 0, "disponible": 0})}
            for sucursal in sucursales
        ]
    return productos
