"""B.Tech Egypt price scraper using Scrapling."""
from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from .base import ScraplingBase
from .jumia import RetailPrice

logger = logging.getLogger(__name__)

BASE   = "https://btech.com"
SEARCH = f"{BASE}/en/catalogsearch/result/?q={{query}}"
CAT    = f"{BASE}/en/smartphones.html"


class BTechScraper(ScraplingBase):
    RETAILER_SLUG = "btech"

    async def search(self, query: str) -> AsyncIterator[RetailPrice]:
        url = SEARCH.format(query=query.replace(" ", "+"))
        logger.info("[BTech] search: %s", url)
        page = await self.fetch_html(url)
        if page is None:
            return
        async for item in self._parse_page(page):
            yield item

    async def scrape_phones_page(self, page_num: int = 1) -> AsyncIterator[RetailPrice]:
        url = f"{CAT}?p={page_num}"
        page = await self.fetch_html(url)
        if page is None:
            return
        async for item in self._parse_page(page):
            yield item

    async def _parse_page(self, page) -> AsyncIterator[RetailPrice]:
        # B.Tech uses Magento 2 — product items inside ol.products li.product-item
        for card in page.css("ol.products li.product-item"):
            try:
                name_el  = card.css_first(".product-item-name a")
                price_el = card.css_first(".price")
                link_el  = card.css_first(".product-item-name a")
                img_el   = card.css_first("img.product-image-photo")
                stock_el = card.css_first(".stock.unavailable")

                if not name_el or not price_el:
                    continue

                price = self._parse_price(price_el.text)
                if price <= 0:
                    continue

                href  = link_el.attrib.get("href", "") if link_el else ""
                img   = img_el.attrib.get("src", "") if img_el else ""

                yield RetailPrice(
                    retailer_slug=self.RETAILER_SLUG,
                    device_name_raw=name_el.text.strip(),
                    price_egp=price,
                    original_price_egp=None,
                    product_url=href,
                    in_stock=stock_el is None,
                    image_url=img,
                )
            except Exception as exc:
                logger.debug("[BTech] card error: %s", exc)

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", (text or "").replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
