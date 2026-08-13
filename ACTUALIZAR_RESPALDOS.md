# Actualizar existencias SICAR

El cotizador conserva sus precios y carrito actuales. Las existencias se generan desde los cinco respaldos SICAR mediante la `clave` del artículo.

1. Guarda un respaldo `.sr` de cada sucursal en una misma carpeta: Santa Rosa, Juárez, Clouthier, Libramiento 3 y Real del Valle.
2. Desde la carpeta del proyecto ejecuta:

```bash
python3 -m services.sicar_respaldo /ruta/a/la/carpeta/de/respaldos --salida data/existencias_sucursales.json
```

3. Reinicia o vuelve a publicar el cotizador. La búsqueda tomará las nuevas existencias automáticamente.

El proceso valida que haya una fuente para las cinco sucursales y que la tabla `articulo` contenga `clave`, `existencia` y `disponible`. No reemplaza el Excel usado actualmente para los precios 1, 2 y 3.
