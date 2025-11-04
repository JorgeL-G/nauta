import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health():
    """Endpoint to verify the API status"""
    logger.info("Health check requested")
    return {"status": "healthy"}

