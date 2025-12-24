import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    @model_validator(mode='after')
    def check_google_key(self) -> 'Settings':
        if not self.GOOGLE_API_KEY and self.GEMINI_API_KEY:
             self.GOOGLE_API_KEY = self.GEMINI_API_KEY
        if not self.GOOGLE_API_KEY:
             # Warn or let it fail later? For now, we allow it to be None during import but genericai might fail
             pass 
        return self

settings = Settings()
