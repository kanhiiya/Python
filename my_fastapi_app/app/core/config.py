from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Modular App"
    VERSION: str = "1.0.0"
    
    # App settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: Optional[List[str]] = []

    # HTTPS enforcement
    FORCE_HTTPS: bool = False

    # Simple rate limiting (per-IP)
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    # Redis (optional) for centralized rate limiting
    REDIS_URL: str | None = None

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
