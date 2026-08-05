import os
import pandas as pd

if os.path.exists("data/articulosExportados Santa Rosa.xlsx"):
    archivo = "data/articulosExportados Santa Rosa.xlsx"
elif os.path.exists("data/articulosExportados Santa Rosa.xls"):
    archivo = "data/articulosExportados Santa Rosa.xls"
else:
    raise FileNotFoundError("No existe ningún catálogo.")

df = pd.read_excel(archivo)

# Eliminar todos los NaN desde el origen
df = df.where(pd.notnull(df), "")

def buscar(texto):

    texto = str(texto).upper()

    resultados = df[
        df.astype(str)
        .apply(lambda fila: fila.str.upper().str.contains(texto, na=False))
        .any(axis=1)
    ]

    return resultados