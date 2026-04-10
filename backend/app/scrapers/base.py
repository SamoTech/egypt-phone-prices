"""Base scraper using Scrapling StealthyFetcher."""
from __future__ import annotations

import asyncio
import random
import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from scrapling import StealthyFetcher, PlayWrightFetcher

logger = logging.getLogger(__name__)

# Delay range between requests (seconds)
MIN_DELAY = 2.0
MAX_DELAY = 5.0


class ScraplingBase:
    """Shared Scrapling fetcher wrapper with retry + rate limiting."""

    def __init__(self, proxy_list: list[str] | None = None):
        self.proxy_list = proxy_list or []
        self._fetcher = StealthyFetcher(auto_match=True)
        self._pw_fetcher = PlayWrightFetcher(auto_match=True)

    def _pick_proxy(self) -> str | None:
        return random.choice(self.proxy_list) if self.proxy_list else None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=3, max=15),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def fetch(self, url: str, dynamic: bool = False) -> Any:
        """Fetch a page. Uses Playwright for JS-heavy pages."""
        proxy = self._pick_proxy()
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        kwargs: dict[str, Any] = {"url": url}
        if proxy:
            kwargs["proxy"] = proxy

        if dynamic:
            logger.debug("[PW] %s", url)
            return await self._pw_fetcher.async_fetch(**kwargs)
        else:
            logger.debug("[Stealth] %s", url)
            return await self._fetcher.async_fetch(**kwargs)

    async def fetch_html(self, url: str, dynamic: bool = False) -> Any:
        """Return parsed Scrapling page object."""
        return await self.fetch(url, dynamic=dynamic)
