"""Noon Egypt price scraper using Scrapling."""
from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from .base import ScraplingBase
from .jumia import RetailPrice

logger = logging.getLogger(__name__)

BASE   = "https://www.noon.com"
SEARCH = f"{BASE}/egypt-en/search/?q={{query}}&c=Electronics_MobilesTablets_Mobiles"


class NoonScraper(ScraplingBase):
    RETAILER_SLUG = "noon"

    async def search(self, query: str) -> AsyncIterator[RetailPrice]:
        url = SEARCH.format(query=query.replace(" ", "+"))
        logger.info("[Noon] search: %s", url)
        page = await self.fetch_html(url, dynamic=True)
        if page is None:
            return

        # Noon product grid uses <div data-qa="product-block">
        cards = page.css("[data-qa='product-block']")
        logger.info("[Noon] %d cards for '%s'", len(cards), query)

        for card in cards:
            try:
                name_el  = card.css_first("[data-qa='product-name']")
                price_el = card.css_first("[data-qa='price-value']")
                link_el  = card.css_first("a")
                img_el   = card.css_first("img")

                if not name_el or not price_el:
                    continue

                price = self._parse_price(price_el.text)
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
                logger.debug("[Noon] card error: %s", exc)

    async def scrape_phones_page(self, page_num: int = 1) -> AsyncIterator[RetailPrice]:
        url = f"{BASE}/egypt-en/search/?q=smartphone&c=Electronics_MobilesTablets_Mobiles&page={page_num}"
        page = await self.fetch_html(url, dynamic=True)
        if page is None:
            return
        for card in page.css("[data-qa='product-block']"):
            try:
                name_el  = card.css_first("[data-qa='product-name']")
                price_el = card.css_first("[data-qa='price-value']")
                link_el  = card.css_first("a")
                if not name_el or not price_el:
                    continue
                price = self._parse_price(price_el.text)
                if price <= 0:
                    continue
                href  = link_el.attrib.get("href", "") if link_el else ""
                url_p = f"{BASE}{href}" if href.startswith("/") else href
                yield RetailPrice(
                    retailer_slug=self.RETAILER_SLUG,
                    device_name_raw=name_el.text.strip(),
                    price_egp=price,
                    original_price_egp=None,
                    product_url=url_p,
                    in_stock=True,
                )
            except Exception as exc:
                logger.debug("[Noon] card error: %s", exc)

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", (text or "").replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
