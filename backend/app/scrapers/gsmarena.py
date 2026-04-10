"""GSMArena scraper — fetches device metadata for target brands."""
import asyncio
import re
from typing import Optional

from loguru import logger

from app.scrapers.base import BaseScraper, ScrapingError

BRANDS = [
    ("Samsung",  "samsung",  "https://www.gsmarena.com/samsung-phones-9.php"),
    ("Apple",    "apple",    "https://www.gsmarena.com/apple-phones-48.php"),
    ("Xiaomi",   "xiaomi",   "https://www.gsmarena.com/xiaomi-phones-80.php"),
    ("Oppo",     "oppo",     "https://www.gsmarena.com/oppo-phones-82.php"),
    ("Realme",   "realme",   "https://www.gsmarena.com/realme-phones-118.php"),
    ("Huawei",   "huawei",   "https://www.gsmarena.com/huawei-phones-58.php"),
    ("Honor",    "honor",    "https://www.gsmarena.com/honor-phones-121.php"),
    ("Vivo",     "vivo",     "https://www.gsmarena.com/vivo-phones-98.php"),
    ("OnePlus",  "oneplus",  "https://www.gsmarena.com/oneplus-phones-95.php"),
    ("Tecno",    "tecno",    "https://www.gsmarena.com/tecno-phones-120.php"),
    ("Infinix",  "infinix",  "https://www.gsmarena.com/infinix-phones-119.php"),
    ("Nokia",    "nokia",    "https://www.gsmarena.com/nokia-phones-1.php"),
    ("Motorola", "motorola", "https://www.gsmarena.com/motorola-phones-8.php"),
    ("Sony",     "sony",     "https://www.gsmarena.com/sony-phones-7.php"),
    ("Google",   "google",   "https://www.gsmarena.com/google-phones-107.php"),
    ("Asus",     "asus",     "https://www.gsmarena.com/asus-phones-46.php"),
    ("Lenovo",   "lenovo",   "https://www.gsmarena.com/lenovo-phones-73.php"),
    ("ZTE",      "zte",      "https://www.gsmarena.com/zte-phones-62.php"),
    ("TCL",      "tcl",      "https://www.gsmarena.com/tcl-phones-123.php"),
    ("Alcatel",  "alcatel",  "https://www.gsmarena.com/alcatel-phones-5.php"),
    ("Blackview","blackview","https://www.gsmarena.com/blackview-phones-116.php"),
    ("itel",     "itel",     "https://www.gsmarena.com/itel-phones-124.php"),
    ("Umidigi",  "umidigi",  "https://www.gsmarena.com/umidigi-phones-117.php"),
    ("Doogee",   "doogee",   "https://www.gsmarena.com/doogee-phones-129.php"),
]


class GSMArenaScaper(BaseScraper):
    slug = "gsmarena"
    name = "GSMArena"

    async def scrape(self) -> list[dict]:
        """Returns device metadata dicts for all target brands."""
        all_devices = []
        for brand_name, brand_slug, listing_url in BRANDS:
            try:
                devices = await self._scrape_brand(brand_name, brand_slug, listing_url)
                all_devices.extend(devices)
                logger.info(f"[gsmarena] {brand_name}: {len(devices)} devices")
            except ScrapingError as exc:
                logger.error(f"[gsmarena] Failed {brand_name}: {exc}")
            await asyncio.sleep(2)
        return all_devices

    async def _scrape_brand(self, brand_name: str, brand_slug: str, url: str) -> list[dict]:
        page = await self.fetch(url)
        devices = []

        if hasattr(page, "css"):
            # Scrapling page object
            items = page.css(".makers li") or page.css(".device-list li")
            for item in items:
                a_tag = item.css_first("a")
                if not a_tag:
                    continue
                href = a_tag.attrib.get("href", "")
                img = item.css_first("img")
                name = img.attrib.get("title") if img else a_tag.text_content
                if not name:
                    continue
                devices.append({
                    "brand_name": brand_name,
                    "brand_slug": brand_slug,
                    "name": name.strip(),
                    "slug": self._slugify(name),
                    "gsmarena_url": f"https://www.gsmarena.com/{href}" if href else None,
                    "image_url": img.attrib.get("src") if img else None,
                })
        else:
            # httpx response
            from html.parser import HTMLParser
            html = page.text
            pattern = r'<div class="makers">.*?</div>'
            logger.debug(f"[gsmarena] Falling back to regex for {brand_name}")

        return devices

    @staticmethod
    def _slugify(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_]+", "-", text)
        return text
