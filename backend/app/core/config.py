"""Application settings — loaded from environment variables."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/egypt_phones"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/egypt_phones"

    # Supabase (optional — for direct Supabase client usage)
    NEXT_PUBLIC_SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Redis (optional — graceful degradation if not set)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Admin
    ADMIN_TOKEN: str = "dev-token"

    # Cron
    CRON_SECRET: str = "dev-cron-secret"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Scraping
    SCRAPLING_STEALTH: bool = True
    SCRAPE_DELAY_MIN: int = 2
    SCRAPE_DELAY_MAX: int = 6
    PROXY_LIST: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
