import pandas as pd

archivo = "data/articulosExportados Santa Rosa.xlsx"

df = pd.read_excel(archivo)


def buscar(texto):

    texto = str(texto).upper()

    resultados = df[
        df.astype(str)
        .apply(lambda fila: fila.str.upper().str.contains(texto))
        .any(axis=1)
    ]

    return resultados
print(df.columns.tolist())