"""Jumia Egypt price scraper using Scrapling."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import AsyncIterator

from .base import ScraplingBase

logger = logging.getLogger(__name__)

BASE = "https://www.jumia.com.eg"
SEARCH = f"{BASE}/catalog/?q={{query}}&category=114" # 114 = Phones


@dataclass
class RetailPrice:
    retailer_slug: str
    device_name_raw: str   # as listed on retailer site
    price_egp: float
    original_price_egp: float | None
    product_url: str
    in_stock: bool = True
    image_url: str = ""


class JumiaScraper(ScraplingBase):
    """Scrape smartphone prices from Jumia Egypt."""

    RETAILER_SLUG = "jumia"

    async def search(self, query: str) -> AsyncIterator[RetailPrice]:
        url = SEARCH.format(query=query.replace(" ", "+"))
        logger.info("[Jumia] search: %s", url)
        page = await self.fetch_html(url, dynamic=True)
        if page is None:
            return

        # Product cards
        cards = page.css("article.prd")
        logger.info("[Jumia] %d results for '%s'", len(cards), query)

        for card in cards:
            try:
                name_el  = card.css_first("h3.name")
                price_el = card.css_first("div.prc")
                old_el   = card.css_first("div.old")
                link_el  = card.css_first("a.core")
                img_el   = card.css_first("img.img")

                if not name_el or not price_el or not link_el:
                    continue

                name  = name_el.text.strip()
                price = self._parse_price(price_el.text)
                old   = self._parse_price(old_el.text) if old_el else None
                href  = link_el.attrib.get("href", "")
                url_p = f"{BASE}{href}" if href.startswith("/") else href
                img   = img_el.attrib.get("data-src") or img_el.attrib.get("src") or "" if img_el else ""

                if price <= 0:
                    continue

                yield RetailPrice(
                    retailer_slug=self.RETAILER_SLUG,
                    device_name_raw=name,
                    price_egp=price,
                    original_price_egp=old,
                    product_url=url_p,
                    in_stock=True,
                    image_url=img,
                )
            except Exception as exc:
                logger.debug("[Jumia] card parse error: %s", exc)

    async def scrape_phones_page(self, page_num: int = 1) -> AsyncIterator[RetailPrice]:
        """Scrape full phones category — used for bulk daily refresh."""
        url = f"{BASE}/catalog/?q=smartphone&category=114&page={page_num}"
        page = await self.fetch_html(url, dynamic=True)
        if page is None:
            return
        async for item in self._parse_cards(page):
            yield item

    async def _parse_cards(self, page) -> AsyncIterator[RetailPrice]:
        for card in page.css("article.prd"):
            try:
                name_el  = card.css_first("h3.name")
                price_el = card.css_first("div.prc")
                old_el   = card.css_first("div.old")
                link_el  = card.css_first("a.core")
                img_el   = card.css_first("img.img")
                stock_el = card.css_first("div.bdg._out")

                if not name_el or not price_el:
                    continue

                price = self._parse_price(price_el.text)
                if price <= 0:
                    continue

                href  = link_el.attrib.get("href", "") if link_el else ""
                url_p = f"{BASE}{href}" if href.startswith("/") else href
                img   = img_el.attrib.get("data-src") or img_el.attrib.get("src") or "" if img_el else ""

                yield RetailPrice(
                    retailer_slug=self.RETAILER_SLUG,
                    device_name_raw=name_el.text.strip(),
                    price_egp=price,
                    original_price_egp=self._parse_price(old_el.text) if old_el else None,
                    product_url=url_p,
                    in_stock=stock_el is None,
                    image_url=img,
                )
            except Exception as exc:
                logger.debug("[Jumia] card error: %s", exc)

    @staticmethod
    def _parse_price(text: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", (text or "").replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
