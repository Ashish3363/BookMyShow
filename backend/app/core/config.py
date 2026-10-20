"""App settings.

Phase: Step 2 (cities and cinemas APIs).
Will hold: a Settings class (pydantic-settings) that reads .env.
Values: APP_NAME, DATABASE_URL. Later: REDIS_URL, ELASTICSEARCH_URL, JWT and provider keys.
"""
#settings read from the env file.

from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../env/backend.env", extra="ignore")
    app_name: str = "BookMyShow"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bookmyshow"
    
    
@lru_cache
def get_settings() -> Settings:
    return Settings()