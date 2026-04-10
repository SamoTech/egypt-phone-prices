"""Application settings loaded from environment variables."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/egypt_phones"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost/egypt_phones"
    REDIS_URL: str = "redis://localhost:6379/0"

    PROXY_LIST: str = ""
    SCRAPLING_STEALTH: bool = True
    SCRAPE_DELAY_MIN: float = 2.0
    SCRAPE_DELAY_MAX: float = 6.0

    ADMIN_TOKEN: str = "change-me"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://*.vercel.app"]

    SCRAPE_CRON_HOUR: int = 3
    SCRAPE_CRON_MINUTE: int = 0

    @property
    def proxy_list(self) -> List[str]:
        return [p.strip() for p in self.PROXY_LIST.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
