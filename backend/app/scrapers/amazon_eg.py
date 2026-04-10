"""Amazon Egypt price scraper using Scrapling."""
from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from .base import ScraplingBase
from .jumia import RetailPrice

logger = logging.getLogger(__name__)

BASE   = "https://www.amazon.eg"
SEARCH = f"{BASE}/s?k={{query}}&rh=n%3A21639082031" # Mobiles node


class AmazonEgScraper(ScraplingBase):
    RETAILER_SLUG = "amazon"

    async def search(self, query: str) -> AsyncIterator[RetailPrice]:
        url = SEARCH.format(query=query.replace(" ", "+"))
        logger.info("[Amazon.eg] search: %s", url)
        page = await self.fetch_html(url, dynamic=True)
        if page is None:
            return
        async for item in self._parse_page(page):
            yield item

    async def scrape_phones_page(self, page_num: int = 1) -> AsyncIterator[RetailPrice]:
        url = f"{BASE}/s?k=smartphone&rh=n%3A21639082031&page={page_num}"
        page = await self.fetch_html(url, dynamic=True)
        if page is None:
            return
        async for item in self._parse_page(page):
            yield item

    async def _parse_page(self, page) -> AsyncIterator[RetailPrice]:
        # Amazon product cards: [data-component-type="s-search-result"]
        for card in page.css("[data-component-type='s-search-result']"):
            try:
                name_el   = card.css_first("h2 a span")
                whole_el  = card.css_first(".a-price-whole")
                link_el   = card.css_first("h2 a")
                img_el    = card.css_first("img.s-image")

                if not name_el or not whole_el:
                    continue

                price_text = whole_el.text.replace(",", "").replace(".", "")
                price = float(re.sub(r"[^\d]", "", price_text) or "0")
                if price <= 0:
                    continue

                href  = link_el.attrib.get("href", "") if link_el else ""
                url_p = f"{BASE}{href}" if href.startswith("/") else href
                img   = img_el.attrib.get("src", "") if img_el else ""

                yield RetailPrice(
                    retailer_slug=self.RETAILER_SLUG,
                    device_name_raw=name_el.text.strip(),
                    price_egp=price,
                    original_price_egp=None,
                    product_url=url_p,
                    in_stock=True,
                    image_url=img,
                )
            except Exception as exc:
                logger.debug("[Amazon.eg] card error: %s", exc)
