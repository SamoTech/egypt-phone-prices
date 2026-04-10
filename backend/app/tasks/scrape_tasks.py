"""Celery tasks — orchestrate all scrapers and persist results."""
import asyncio
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Brand, Device, Price, Retailer, ScrapeLog
from app.db.session import AsyncSessionLocal
from app.scrapers.gsmarena import GSMArenaScaper
from app.scrapers.jumia import JumiaScraper
from app.scrapers.noon import NoonScraper
from app.scrapers.btech import BTechScraper
from app.scrapers.amazon_eg import AmazonEgScraper
from app.tasks.celery_app import celery_app
from app.utils.normalizer import match_device


STORE_SCRAPERS = [JumiaScraper, NoonScraper, BTechScraper, AmazonEgScraper]


async def _upsert_device_metadata(items: list[dict]):
    """Upsert brands + devices from GSMArena data."""
    async with AsyncSessionLocal() as db:
        for item in items:
            brand_slug = item["brand_slug"]
            brand_name = item["brand_name"]

            brand = (await db.execute(
                select(Brand).where(Brand.slug == brand_slug)
            )).scalars().first()

            if not brand:
                brand = Brand(name=brand_name, slug=brand_slug)
                db.add(brand)
                await db.flush()

            device = (await db.execute(
                select(Device).where(Device.slug == item["slug"])
            )).scalars().first()

            if not device:
                device = Device(
                    brand_id=brand.id,
                    name=item["name"],
                    slug=item["slug"],
                    gsmarena_url=item.get("gsmarena_url"),
                    image_url=item.get("image_url"),
                )
                db.add(device)
        await db.commit()


async def _run_store_scraper(scraper_cls):
    scraper = scraper_cls()
    log_started = datetime.now(tz=timezone.utc)
    status = "success"
    scraped_count = 0
    error_msg = None

    try:
        async with AsyncSessionLocal() as db:
            retailer = (await db.execute(
                select(Retailer).where(Retailer.slug == scraper.slug)
            )).scalars().first()

            if not retailer:
                logger.warning(f"Retailer not found: {scraper.slug}")
                return

            devices = (await db.execute(
                select(Device).options(selectinload(Device.brand))
            )).scalars().all()
            canonical_names = [d.name for d in devices]
            device_map = {d.name: d for d in devices}

        raw_items = await scraper.scrape()

        async with AsyncSessionLocal() as db:
            for item in raw_items:
                if not item.get("price_egp"):
                    continue

                matched = match_device(item["device_name"], canonical_names)
                if not matched:
                    continue

                device = device_map[matched]
                retailer_obj = (await db.execute(
                    select(Retailer).where(Retailer.slug == scraper.slug)
                )).scalars().first()

                price = Price(
                    device_id=device.id,
                    retailer_id=retailer_obj.id,
                    price_egp=item["price_egp"],
                    original_price_egp=item.get("original_price_egp"),
                    product_url=item["product_url"],
                    in_stock=item.get("in_stock", True),
                )
                db.add(price)
                scraped_count += 1

            await db.commit()

    except Exception as exc:
        status = "failure"
        error_msg = str(exc)
        logger.error(f"[{scraper.slug}] scrape failed: {exc}")

    async with AsyncSessionLocal() as db:
        db.add(ScrapeLog(
            retailer_slug=scraper.slug,
            status=status,
            devices_scraped=scraped_count,
            error_message=error_msg,
            started_at=log_started,
            finished_at=datetime.now(tz=timezone.utc),
        ))
        await db.commit()


@celery_app.task(name="app.tasks.scrape_tasks.run_all_scrapers")
def run_all_scrapers():
    """Entry point: refresh GSMArena metadata then scrape all stores."""
    loop = asyncio.get_event_loop()

    gsm = GSMArenaScaper()
    meta = loop.run_until_complete(gsm.scrape())
    loop.run_until_complete(_upsert_device_metadata(meta))

    for cls in STORE_SCRAPERS:
        loop.run_until_complete(_run_store_scraper(cls))
