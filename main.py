from fastapi import FastAPI

app = FastAPI(
    title="nauta-backend-api",
    description="API backend con FastAPI",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Endpoint raíz que devuelve un mensaje de bienvenida"""
    return {"message": "Bienvenido a nauta-backend-api"}


@app.get("/health")
async def health():
    """Endpoint para verificar el estado de la API"""
    return {"status": "healthy"}

