import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Class to handle MongoDB connection"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None
        self.is_connected = False
    
    async def connect(self):
        """Establishes connection to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB at: {settings.mongodb_uri}")
            self.client = AsyncIOMotorClient(settings.mongodb_uri)
            
            # Verify the connection
            await self.client.admin.command('ping')
            
            self.db = self.client[settings.mongodb_db_name]
            self.is_connected = True
            logger.info(f"Successfully connected to MongoDB. Database: {settings.mongodb_db_name}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            self.is_connected = False
            raise
    
    async def close(self):
        """Closes the MongoDB connection"""
        try:
            if self.client:
                self.client.close()
                self.is_connected = False
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
    
    def get_status(self) -> dict:
        """Returns the current connection status"""
        return {
            "connected": self.is_connected,
            "database": settings.mongodb_db_name if self.is_connected else None,
            "uri": settings.mongodb_uri if self.is_connected else None
        }

