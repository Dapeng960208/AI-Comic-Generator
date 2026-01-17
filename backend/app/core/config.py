import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Comic Generator"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./comic_app.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
