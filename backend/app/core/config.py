from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    AI_PROVIDER: str = "openai"
    AI_API_KEY: Optional[str] = None
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4"
    AI_TIMEOUT: int = 30

    DATABASE_URL: str = "sqlite+aiosqlite:///./deepaudit.db"

    REDIS_URL: str = "redis://localhost:6379/0"

    UPLOAD_DIR: str = "./uploads"
    REPORT_DIR: str = "./reports"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_settings() -> Settings:
    return settings
