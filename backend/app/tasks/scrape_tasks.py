"""Celery tasks — orchestrate scraping and persist to Supabase."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

import httpx

from .celery_app import app
from ..scrapers.gsmarena   import GSMArenaScraper, TARGET_BRANDS
from ..scrapers.jumia      import JumiaScraper
from ..scrapers.noon       import NoonScraper
from ..scrapers.btech      import BTechScraper
from ..scrapers.amazon_eg  import AmazonEgScraper
from ..utils.normalizer    import DeviceNameIndex

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROXY_LIST   = [p.strip() for p in os.environ.get("PROXY_LIST", "").split(",") if p.strip()]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal",
}


# ── Supabase REST helpers ────────────────────────────────────────────────────

async def sb_upsert(client: httpx.AsyncClient, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    r = await client.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        json=rows,
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=minimal"},
    )
    r.raise_for_status()


async def sb_get(client: httpx.AsyncClient, table: str, params: str = "") -> list[dict]:
    r = await client.get(
        f"{SUPABASE_URL}/rest/v1/{table}?{params}",
        headers=HEADERS,
    )
    r.raise_for_status()
    return r.json()


async def sb_insert(client: httpx.AsyncClient, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    r = await client.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        json=rows,
        headers={**HEADERS, "Prefer": "return=minimal"},
    )
    r.raise_for_status()


# ── Task: full metadata + price scrape ──────────────────────────────────────

@app.task(bind=True, max_retries=2, default_retry_delay=300)
def run_full_scrape(self):
    """Scrape GSMArena metadata for all brands then refresh prices."""
    try:
        asyncio.run(_full_scrape())
    except Exception as exc:
        logger.error("full_scrape failed: %s", exc)
        raise self.retry(exc=exc)


async def _full_scrape():
    async with httpx.AsyncClient(timeout=30) as client:
        gsm = GSMArenaScraper(proxy_list=PROXY_LIST)

        # 1. Upsert brands
        brand_rows = [
            {"name": b[0], "slug": b[1]}
            for b in TARGET_BRANDS
        ]
        await sb_upsert(client, "brands", brand_rows)
        logger.info("upserted %d brands", len(brand_rows))

        # 2. Load brand id map
        brands_db = await sb_get(client, "brands", "select=id,slug")
        brand_map = {b["slug"]: b["id"] for b in brands_db}

        # 3. Scrape + upsert devices
        count = 0
        async for device in gsm.scrape_all():
            brand_id = brand_map.get(device.brand_slug)
            if not brand_id:
                continue
            row = {
                "name":         device.name,
                "slug":         device.slug,
                "brand_id":     brand_id,
                "image_url":    device.image_url,
                "display":      device.display,
                "chipset":      device.chipset,
                "ram":          device.ram,
                "storage":      device.storage,
                "camera":       device.camera,
                "battery":      device.battery,
                "os":           device.os,
                "release_year": device.release_year,
                "gsmarena_url": device.gsmarena_url,
            }
            await sb_upsert(client, "devices", [row])
            count += 1

        logger.info("upserted %d devices", count)

    # Then refresh prices
    await _price_refresh()


# ── Task: price-only refresh ─────────────────────────────────────────────────

@app.task(bind=True, max_retries=2, default_retry_delay=120)
def run_price_refresh(self):
    """Refresh prices from all retailers for known devices."""
    try:
        asyncio.run(_price_refresh())
    except Exception as exc:
        logger.error("price_refresh failed: %s", exc)
        raise self.retry(exc=exc)


async def _price_refresh():
    async with httpx.AsyncClient(timeout=30) as client:
        # Load devices + retailers
        devices_db  = await sb_get(client, "devices",   "select=id,name,slug")
        retailers_db= await sb_get(client, "retailers",  "select=id,slug")

        name_index   = DeviceNameIndex([d["name"] for d in devices_db])
        device_by_name = {d["name"]: d["id"] for d in devices_db}
        retailer_map   = {r["slug"]: r["id"] for r in retailers_db}

        scrapers = [
            JumiaScraper(proxy_list=PROXY_LIST),
            NoonScraper(proxy_list=PROXY_LIST),
            BTechScraper(proxy_list=PROXY_LIST),
            AmazonEgScraper(proxy_list=PROXY_LIST),
        ]

        price_rows: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for scraper in scrapers:
            retailer_id = retailer_map.get(scraper.RETAILER_SLUG)
            if not retailer_id:
                logger.warning("retailer not found: %s", scraper.RETAILER_SLUG)
                continue

            logger.info("scraping %s ...", scraper.RETAILER_SLUG)
            try:
                # Scrape first 5 pages of phone listings
                for page_num in range(1, 6):
                    async for item in scraper.scrape_phones_page(page_num):
                        match = name_index.match(item.device_name_raw)
                        if match is None:
                            continue
                        canonical_name, score = match
                        device_id = device_by_name.get(canonical_name)
                        if not device_id:
                            continue

                        price_rows.append({
                            "device_id":           device_id,
                            "retailer_id":         retailer_id,
                            "price_egp":           item.price_egp,
                            "original_price_egp":  item.original_price_egp,
                            "product_url":         item.product_url,
                            "in_stock":            item.in_stock,
                            "scraped_at":          now,
                            "match_score":         score,
                        })
            except Exception as exc:
                logger.error("[%s] scrape error: %s", scraper.RETAILER_SLUG, exc)

        # Bulk insert price snapshot
        if price_rows:
            await sb_insert(client, "prices", price_rows)
            logger.info("inserted %d price records", len(price_rows))
        else:
            logger.warning("no price records collected")
