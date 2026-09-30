# Despliegue del Cotizador SERBI

## Variables obligatorias

- `ACCESS_PIN`: PIN compartido por el personal. No se guarda en el código.
- `SECRET_KEY`: secreto aleatorio largo usado para firmar la sesión. No reutilizar el PIN como secreto.
- `ENVIRONMENT=production` en producción; activa el atributo `Secure` de la cookie. Render también activa ese atributo automáticamente mediante `RENDER=true`.

La sesión dura 30 días y usa cookie `HttpOnly`, `SameSite=Lax` y `Secure` en producción.

## Render

Usar un servicio web Python con el directorio del proyecto como raíz, instalar `requirements.txt` y configurar el comando de inicio:

```text
uvicorn app:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'
```

Configurar `ACCESS_PIN` y `SECRET_KEY` en Environment. No poner sus valores en el repositorio.

## cPanel / Passenger

Esta aplicación es FastAPI y expone una aplicación **ASGI** (`app:app`). No es WSGI; el `passenger_wsgi.py` tradicional no puede ejecutarla directamente. Solo usarla en cPanel si el proveedor habilita un modo ASGI/ASGI-to-Passenger compatible y configura el punto de entrada ASGI. Si la cuenta solo ofrece WSGI, se necesita un servicio ASGI compatible (por ejemplo, Render) o soporte específico del proveedor; no se debe cambiar el cotizador a WSGI.

El servidor debe mantener disponibles los archivos `templates/`, `static/` y `data/` con sus rutas relativas actuales.
