import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Veritabanı
    DATABASE_URL: str
    
    # Instagram API
    INSTAGRAM_BUSINESS_ID: str
    ACCESS_TOKEN: str
    
    # Google Gemini API
    GOOGLE_API_KEY: str
    
    # Uygulama Ayarları
    API_VERSION: str = "v24.0"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Ayarları başlat
settings = Settings()