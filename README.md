# nauta-backend-api

API backend desarrollada con FastAPI.

## Requisitos

- Python 3.11
- Anaconda o Miniconda

## Configuración del Entorno

### Paso 1: Crear y activar el entorno virtual con Anaconda

```bash
conda create -n nauta-backend-api python=3.11 -y
conda activate nauta-backend-api
```

### Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
uvicorn main:app --reload
```

La aplicación estará disponible en: `http://localhost:8000`

## Documentación de la API

Una vez que la aplicación esté corriendo, puedes acceder a:
- Documentación interactiva (Swagger UI): `http://localhost:8000/docs`
- Documentación alternativa (ReDoc): `http://localhost:8000/redoc`

## Endpoints

- `GET /` - Mensaje de bienvenida
- `GET /health` - Verificación del estado de la API
