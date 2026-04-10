"""GSMArena spider — scrapes device metadata for Egyptian market brands."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import AsyncIterator

from .base import ScraplingBase

logger = logging.getLogger(__name__)

BASE = "https://www.gsmarena.com"

# Brands active in Egypt with their GSMArena URL slugs
TARGET_BRANDS: list[tuple[str, str]] = [
    ("Samsung",  "samsung"),
    ("Apple",    "apple"),
    ("Xiaomi",   "xiaomi"),
    ("Oppo",     "oppo"),
    ("Realme",   "realme"),
    ("Huawei",   "huawei"),
    ("Honor",    "honor"),
    ("Vivo",     "vivo"),
    ("OnePlus",  "oneplus"),
    ("Tecno",    "tecno"),
    ("Infinix",  "infinix"),
    ("itel",     "itel"),
    ("Nokia",    "nokia"),
    ("Motorola", "motorola"),
    ("Sony",     "sony"),
    ("Google",   "google"),
    ("Lenovo",   "lenovo"),
    ("Asus",     "asus"),
    ("ZTE",      "zte"),
    ("TCL",      "tcl"),
    ("Alcatel",  "alcatel"),
    ("Blackview","blackview"),
    ("Umidigi",  "umidigi"),
    ("Doogee",   "doogee"),
]


@dataclass
class GSMDevice:
    name: str
    slug: str
    brand_name: str
    brand_slug: str
    gsmarena_url: str
    image_url: str = ""
    display: str = ""
    chipset: str = ""
    ram: str = ""
    storage: str = ""
    camera: str = ""
    battery: str = ""
    os: str = ""
    release_year: int | None = None
    extra: dict = field(default_factory=dict)


class GSMArenaScraper(ScraplingBase):
    """Scrape device list + specs from GSMArena."""

    async def scrape_brand(self, brand_name: str, brand_slug: str) -> AsyncIterator[GSMDevice]:
        url = f"{BASE}/{brand_slug}-phones-{self._brand_id(brand_slug)}.php"
        logger.info("[GSMArena] brand page: %s", url)

        page = await self.fetch_html(url)
        if page is None:
            return

        # Device cards: <li> inside #review-body ul.makers
        cards = page.css("#review-body ul.makers li")
        logger.info("[GSMArena] %s → %d devices", brand_name, len(cards))

        for card in cards:
            a = card.css_first("a")
            if not a:
                continue
            href = a.attrib.get("href", "")
            img  = card.css_first("img")
            name = (card.css_first("strong span") or card.css_first("span")).text if card.css_first("strong span") else ""
            if not name:
                name = a.text.strip()

            device_url = f"{BASE}/{href}" if not href.startswith("http") else href
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

            device = GSMDevice(
                name=name.strip(),
                slug=slug,
                brand_name=brand_name,
                brand_slug=brand_slug,
                gsmarena_url=device_url,
                image_url=img.attrib.get("src", "") if img else "",
            )

            # Fetch specs page for each device
            try:
                specs = await self._scrape_specs(device_url)
                device.display      = specs.get("display", "")
                device.chipset      = specs.get("chipset", "")
                device.ram          = specs.get("ram", "")
                device.storage      = specs.get("storage", "")
                device.camera       = specs.get("camera", "")
                device.battery      = specs.get("battery", "")
                device.os           = specs.get("os", "")
                device.release_year = specs.get("year")
            except Exception as exc:
                logger.warning("[GSMArena] specs failed for %s: %s", name, exc)

            yield device

    async def _scrape_specs(self, url: str) -> dict:
        page = await self.fetch_html(url)
        if page is None:
            return {}

        specs: dict = {}

        # Spec table rows: td.ttl (label) + td.nfo (value)
        rows = page.css("#specs-list table tr")
        for row in rows:
            label_el = row.css_first("td.ttl")
            value_el = row.css_first("td.nfo")
            if not label_el or not value_el:
                continue
            label = label_el.text.strip().lower()
            value = value_el.text.strip()

            if "display" in label or "size" in label:
                specs.setdefault("display", value[:60])
            elif "chipset" in label or "cpu" in label:
                specs.setdefault("chipset", value[:60])
            elif "ram" in label:
                specs.setdefault("ram", value[:30])
            elif "storage" in label or "internal" in label:
                specs.setdefault("storage", value[:60])
            elif "main camera" in label or "single" in label:
                specs.setdefault("camera", value[:60])
            elif "battery" in label:
                specs.setdefault("battery", value[:40])
            elif "os" in label:
                specs.setdefault("os", value[:40])
            elif "announced" in label or "status" in label:
                m = re.search(r"20(2[0-9]|3[0-9])", value)
                if m:
                    specs["year"] = int(m.group())

        return specs

    @staticmethod
    def _brand_id(slug: str) -> str:
        """GSMArena encodes a numeric brand ID in the URL. Map known ones."""
        ids = {
            "samsung": "9", "apple": "48", "xiaomi": "80", "oppo": "82",
            "realme": "118", "huawei": "58", "honor": "121", "vivo": "98",
            "oneplus": "95", "tecno": "116", "infinix": "119", "itel": "131",
            "nokia": "61", "motorola": "4", "sony": "7", "google": "107",
            "lenovo": "73", "asus": "46", "zte": "62", "tcl": "66",
            "alcatel": "3", "blackview": "246", "umidigi": "249", "doogee": "260",
        }
        return ids.get(slug, "1")

    async def scrape_all(self) -> AsyncIterator[GSMDevice]:
        for brand_name, brand_slug in TARGET_BRANDS:
            async for device in self.scrape_brand(brand_name, brand_slug):
                yield device
