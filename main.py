import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import setup_logging
from database.mongodb import MongoDBConnection
from routers import health, database, transaction

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager to handle the application lifecycle"""
    # Startup: Connect to MongoDB
    logger.info("Starting application...")
    mongodb = MongoDBConnection()
    try:
        await mongodb.connect()
        app.state.mongodb = mongodb
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise
    
    yield
    
    # Shutdown: Close MongoDB connection
    logger.info("Shutting down application...")
    try:
        await mongodb.close()
        logger.info("Application closed successfully")
    except Exception as e:
        logger.error(f"Error closing application: {e}")


app = FastAPI(
    title="nauta-backend-api",
    description="API backend with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Register routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(database.router, prefix="/db", tags=["database"])
app.include_router(transaction.router, prefix="/transactions", tags=["transactions"])


@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    logger.info("Root endpoint requested")
    return {"message": "Welcome to nauta-backend-api"}
