"""Amazon.eg smartphone price scraper."""
import re
import asyncio
from loguru import logger
from app.scrapers.base import BaseScraper, ScrapingError

AMAZON_EG_URL = (
    "https://www.amazon.eg/-/en/s?i=electronics&rh=n%3A21832980031"
)


class AmazonEgScraper(BaseScraper):
    slug = "amazon_eg"
    name = "Amazon Egypt"

    async def scrape(self) -> list[dict]:
        results = []
        for page_num in range(1, 21):
            url = f"{AMAZON_EG_URL}&page={page_num}"
            try:
                page = await self.fetch(url)
                items = self._parse(page)
                if not items:
                    break
                results.extend(items)
                logger.info(f"[amazon_eg] page {page_num}: {len(items)} items")
            except ScrapingError as exc:
                logger.error(f"[amazon_eg] page {page_num} failed: {exc}")
                break
            await asyncio.sleep(2.5)
        return results

    def _parse(self, page) -> list[dict]:
        items = []
        if not hasattr(page, "css"):
            return items

        for card in page.css("div[data-component-type='s-search-result']"):
            name_el  = card.css_first("span.a-text-normal")
            price_el = card.css_first("span.a-price-whole")
            link_el  = card.css_first("a.a-link-normal.s-no-outline")

            if not name_el or not price_el:
                continue

            price = self._parse_price(price_el.text_content)
            href  = link_el.attrib.get("href", "") if link_el else ""

            items.append({
                "device_name": name_el.text_content.strip(),
                "price_egp": price,
                "original_price_egp": None,
                "product_url": f"https://www.amazon.eg{href}" if href.startswith("/") else href,
                "in_stock": True,
            })
        return items

    @staticmethod
    def _parse_price(text: str) -> float | None:
        cleaned = re.sub(r"[^\d]", "", (text or ""))
        try:
            return float(cleaned)
        except ValueError:
            return None
