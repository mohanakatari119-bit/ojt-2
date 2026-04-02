from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://monitor:monitor@db:5432/apimonitor"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://monitor:monitor@db:5432/apimonitor"
    SECRET_KEY: str = "change-me-in-production-please"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
