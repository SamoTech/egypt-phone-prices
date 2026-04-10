"""Noon Egypt smartphone price scraper."""
import re
import asyncio
from loguru import logger
from app.scrapers.base import BaseScraper, ScrapingError

NOON_URL = "https://www.noon.com/egypt-en/mobile-phones/smartphones-16116/"


class NoonScraper(BaseScraper):
    slug = "noon"
    name = "Noon Egypt"

    async def scrape(self) -> list[dict]:
        results = []
        page_num = 1
        while page_num <= 20:
            url = f"{NOON_URL}?page={page_num}"
            try:
                page = await self.fetch(url)
                items = self._parse(page)
                if not items:
                    break
                results.extend(items)
                logger.info(f"[noon] page {page_num}: {len(items)} items")
                page_num += 1
            except ScrapingError as exc:
                logger.error(f"[noon] page {page_num} failed: {exc}")
                break
            await asyncio.sleep(2)
        return results

    def _parse(self, page) -> list[dict]:
        items = []
        if not hasattr(page, "css"):
            return items

        for card in page.css("div[data-qa='product-block']") or page.css(".sc-fhzFiK"):
            name_el  = card.css_first("div[data-qa='product-name']")
            price_el = card.css_first("strong.amount")
            link_el  = card.css_first("a")

            if not name_el or not price_el:
                continue

            price = self._parse_price(price_el.text_content)
            href  = link_el.attrib.get("href", "") if link_el else ""

            items.append({
                "device_name": name_el.text_content.strip(),
                "price_egp": price,
                "original_price_egp": None,
                "product_url": f"https://www.noon.com{href}" if href.startswith("/") else href,
                "in_stock": True,
            })
        return items

    @staticmethod
    def _parse_price(text: str) -> float | None:
        cleaned = re.sub(r"[^\d.]", "", (text or "").replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return None
