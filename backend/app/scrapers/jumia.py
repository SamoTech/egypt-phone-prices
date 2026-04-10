"""Jumia Egypt smartphone price scraper."""
import re
import asyncio
from loguru import logger
from app.scrapers.base import BaseScraper, ScrapingError

JUMIA_SEARCH = "https://www.jumia.com.eg/mlp-mobile-phones/"


class JumiaScraper(BaseScraper):
    slug = "jumia"
    name = "Jumia Egypt"

    async def scrape(self) -> list[dict]:
        results = []
        page_num = 1
        while True:
            url = f"{JUMIA_SEARCH}?page={page_num}#catalog-listing"
            try:
                page = await self.fetch(url)
                items = self._parse(page)
                if not items:
                    break
                results.extend(items)
                logger.info(f"[jumia] page {page_num}: {len(items)} items")
                page_num += 1
                if page_num > 30:  # safety cap
                    break
            except ScrapingError as exc:
                logger.error(f"[jumia] page {page_num} failed: {exc}")
                break
            await asyncio.sleep(1.5)
        return results

    def _parse(self, page) -> list[dict]:
        items = []
        if not hasattr(page, "css"):
            return items

        for card in page.css("article.prd"):
            name_el = card.css_first("h3.name")
            price_el = card.css_first("div.prc")
            old_el   = card.css_first("div.old")
            link_el  = card.css_first("a.core")

            if not name_el or not price_el:
                continue

            price  = self._parse_price(price_el.text_content)
            old_p  = self._parse_price(old_el.text_content) if old_el else None
            href   = link_el.attrib.get("href", "") if link_el else ""

            items.append({
                "device_name": name_el.text_content.strip(),
                "price_egp": price,
                "original_price_egp": old_p,
                "product_url": f"https://www.jumia.com.eg{href}",
                "in_stock": True,
            })
        return items

    @staticmethod
    def _parse_price(text: str) -> float | None:
        if not text:
            return None
        cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return None
