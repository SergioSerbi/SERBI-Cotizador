import pandas as pd

archivo = "data/articulosExportados Santa Rosa.xlsx"

df = pd.read_excel(archivo)

print(df["PRECIO 1"].head(20))
print(df["PRECIO 1"].dtype)


def buscar(texto):

    texto = str(texto).upper()

    resultados = df[
        df.astype(str)
        .apply(lambda fila: fila.str.upper().str.contains(texto))
        .any(axis=1)
    ]

    return resultados