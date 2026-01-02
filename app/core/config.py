import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import model_validator

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ASSEMBLYAI_API_KEY: str
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    UPLOAD_DIR: str = "uploads"
    CORS_ORIGINS: List[str] = ["*"]
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @model_validator(mode='after')
    def check_google_key(self):
        if not self.GOOGLE_API_KEY and self.GEMINI_API_KEY:
            self.GOOGLE_API_KEY = self.GEMINI_API_KEY
        return self

settings = Settings()
