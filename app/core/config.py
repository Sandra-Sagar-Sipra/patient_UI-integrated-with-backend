import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ASSEMBLYAI_API_KEY: str
    GEMINI_API_KEY: str
    UPLOAD_DIR: str = "uploads"
    CORS_ORIGINS: List[str] = ["*"]
    PORT: int = 8000

settings = Settings()
