"""Lee respaldos SICAR (.sr) y consolida existencias por clave de artículo."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

SUCURSALES = ("Santa Rosa", "Juárez", "Clouthier", "Libramiento 3", "Real del Valle")


def _sucursal_desde_nombre(nombre: str) -> str:
    normalizado = re.sub(r"[^A-Z0-9]", "", nombre.upper())
    for marcador, sucursal in {
        "SANTAROSA": "Santa Rosa", "JUAREZ": "Juárez", "CLOUTHIER": "Clouthier",
        "LIBRAMIENTO3": "Libramiento 3", "REALDELVALLE": "Real del Valle",
    }.items():
        if marcador in normalizado:
            return sucursal
    raise ValueError(f"No se pudo identificar la sucursal del respaldo: {nombre}")


def _campos_articulo(sql: str) -> list[str]:
    tabla = re.search(r"CREATE TABLE `articulo` \((.*?)\n\) ENGINE", sql, re.DOTALL)
    if not tabla:
        raise ValueError("No se encontró la definición de la tabla `articulo`.")
    return re.findall(r"^\s*`([^`]+)`", tabla.group(1), re.MULTILINE)


def _fin_sentencia(sql: str, inicio: int) -> int:
    en_cadena = False
    escape = False
    for posicion in range(inicio, len(sql)):
        caracter = sql[posicion]
        if en_cadena:
            if escape:
                escape = False
            elif caracter == "\\":
                escape = True
            elif caracter == "'":
                en_cadena = False
        elif caracter == "'":
            en_cadena = True
        elif caracter == ";":
            return posicion
    raise ValueError("Inserción de `articulo` incompleta en el respaldo.")


def _tuplas_insert(sql: str) -> Iterator[list[str]]:
    inicio, posicion = "INSERT INTO `articulo` VALUES ", 0
    while True:
        posicion = sql.find(inicio, posicion)
        if posicion == -1:
            return
        fin = _fin_sentencia(sql, posicion)
        bloque, posicion = sql[posicion + len(inicio):fin], fin + 1
        valores, campo, en_cadena, escape, en_tupla = [], [], False, False, False
        for caracter in bloque:
            if en_cadena:
                campo.append(caracter)
                if escape:
                    escape = False
                elif caracter == "\\":
                    escape = True
                elif caracter == "'":
                    en_cadena = False
            elif caracter == "'":
                en_cadena, campo = True, campo + [caracter]
            elif caracter == "(":
                en_tupla, valores, campo = True, [], []
            elif caracter == "," and en_tupla:
                valores.append("".join(campo).strip())
                campo = []
            elif caracter == ")" and en_tupla:
                valores.append("".join(campo).strip())
                yield valores
                en_tupla, campo = False, []
            elif en_tupla:
                campo.append(caracter)


def _texto_sql(valor: str) -> str:
    if valor == "NULL":
        return ""
    if len(valor) >= 2 and valor[0] == "'" and valor[-1] == "'":
        valor = valor[1:-1]
    return bytes(valor, "utf-8").decode("unicode_escape")


def _numero_sql(valor: str) -> float:
    return 0.0 if valor == "NULL" else float(valor)


def _leer_respaldo(archivo: Path) -> tuple[str, dict[str, dict[str, float]], int]:
    sucursal = _sucursal_desde_nombre(archivo.name)
    with zipfile.ZipFile(archivo) as respaldo:
        sqls = [nombre for nombre in respaldo.namelist() if nombre.lower().endswith(".sql")]
        if len(sqls) != 1:
            raise ValueError(f"{archivo.name} debe contener exactamente un archivo SQL.")
        sql = respaldo.read(sqls[0]).decode("utf-8")
    campos = _campos_articulo(sql)
    requeridos = {"clave", "existencia", "disponible"}
    if not requeridos.issubset(campos):
        raise ValueError(f"Faltan campos requeridos en {archivo.name}.")
    indices = {campo: campos.index(campo) for campo in requeridos}
    articulos: dict[str, dict[str, float]] = {}
    for valores in _tuplas_insert(sql):
        if len(valores) != len(campos):
            raise ValueError(f"Cantidad de campos inesperada en {archivo.name}.")
        clave = _texto_sql(valores[indices["clave"]]).strip()
        if clave:
            articulos[clave] = {"existencia": _numero_sql(valores[indices["existencia"]]), "disponible": _numero_sql(valores[indices["disponible"]])}
    return sucursal, articulos, len(campos)


def consolidar_respaldos(carpeta: Path, salida: Path) -> dict:
    respaldos = sorted(carpeta.glob("*.sr"))
    if not respaldos:
        raise ValueError(f"No se encontraron respaldos .sr en {carpeta}")
    inventarios: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    resumen: dict[str, dict[str, int | str]] = {}
    for respaldo in respaldos:
        sucursal, articulos, columnas = _leer_respaldo(respaldo)
        if sucursal in resumen:
            raise ValueError(f"Hay más de un respaldo para {sucursal}.")
        resumen[sucursal] = {"archivo": respaldo.name, "articulos": len(articulos), "columnas_articulo": columnas}
        for clave, existencia in articulos.items():
            inventarios[clave][sucursal] = existencia
    faltantes = set(SUCURSALES) - set(resumen)
    if faltantes:
        raise ValueError(f"Faltan sucursales: {', '.join(sorted(faltantes))}")
    resultado = {"generado_en": datetime.now(timezone.utc).isoformat(), "sucursales": list(SUCURSALES), "fuentes": resumen, "inventarios": dict(inventarios)}
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(resultado, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza existencias del cotizador desde respaldos SICAR.")
    parser.add_argument("carpeta", type=Path, help="Carpeta con un respaldo .sr por sucursal")
    parser.add_argument("--salida", type=Path, default=Path("data/existencias_sucursales.json"))
    args = parser.parse_args()
    resultado = consolidar_respaldos(args.carpeta, args.salida)
    print(f"Se consolidaron {len(resultado['inventarios'])} claves en {args.salida}.")


if __name__ == "__main__":
    main()
