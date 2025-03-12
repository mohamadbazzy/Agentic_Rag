from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    APP_NAME: str = "Academic Advisor API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API configuration
    API_PREFIX: str = "/api"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production!
    
    class Config:
        env_file = ".env"

# Create a global instance
settings = Settings()
