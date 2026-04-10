"""Base scraper using Scrapling with stealth mode + retry logic."""
import asyncio
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

try:
    from scrapling import StealthyFetcher, Fetcher
except ImportError:
    StealthyFetcher = None  # type: ignore
    Fetcher = None  # type: ignore


class ScrapingError(Exception):
    pass


class BaseScraper(ABC):
    """Abstract base for all store scrapers."""

    slug: str = ""
    name: str = ""

    def __init__(self):
        self.started_at = datetime.now(tz=timezone.utc)
        self.proxies = settings.proxy_list

    def _get_proxy(self) -> str | None:
        return random.choice(self.proxies) if self.proxies else None

    @retry(
        retry=retry_if_exception_type(ScrapingError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        reraise=True,
    )
    async def fetch(self, url: str) -> Any:
        """Fetch a URL using Scrapling StealthyFetcher with optional proxy."""
        proxy = self._get_proxy()
        delay = random.uniform(settings.SCRAPE_DELAY_MIN, settings.SCRAPE_DELAY_MAX)
        await asyncio.sleep(delay)

        if StealthyFetcher and settings.SCRAPLING_STEALTH:
            try:
                fetcher = StealthyFetcher()
                page = await fetcher.async_fetch(
                    url,
                    proxy=proxy,
                    headless=True,
                    network_idle=True,
                )
                return page
            except Exception as exc:
                logger.warning(f"[{self.slug}] StealthyFetcher failed for {url}: {exc}")
                raise ScrapingError(str(exc)) from exc
        else:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    raise ScrapingError(f"HTTP {resp.status_code} for {url}")
                return resp

    @abstractmethod
    async def scrape(self) -> list[dict]:
        """
        Returns a list of dicts with keys:
            device_name, price_egp, original_price_egp, product_url, in_stock
        """
        ...
