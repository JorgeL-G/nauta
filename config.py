import logging
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings"""
    
    # MongoDB settings
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "nauta"
    
    # Logging settings
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global configuration instance
settings = Settings()


def setup_logging():
    """Setup basic logging configuration for the application"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.log_level}")
    return logger

