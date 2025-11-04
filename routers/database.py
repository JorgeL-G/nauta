import logging
from fastapi import APIRouter, Request
from database.mongodb import MongoDBConnection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def db_status(request: Request):
    """Endpoint to verify the MongoDB connection status"""
    logger.info("Database status requested")
    
    # Get MongoDBConnection instance from app state
    mongodb: MongoDBConnection = request.app.state.mongodb
    
    status = mongodb.get_status()
    logger.info(f"MongoDB status: {status}")
    
    return status

