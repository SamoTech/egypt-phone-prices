"""Standalone scrape runner for GitHub Actions cron.

Run with:  python -m app.tasks.run_scrape

This replaces the Celery worker for the Vercel-only deployment:
the GitHub Actions cron job (scrape.yml) calls this script daily.
"""
import asyncio
import sys
from loguru import logger

from app.tasks.scrape_tasks import (
    _upsert_device_metadata,
    _run_store_scraper,
    STORE_SCRAPERS,
)
from app.scrapers.gsmarena import GSMArenaScaper


async def main():
    logger.info("=== Starting full scrape run ===")

    logger.info("Step 1/2: Refreshing GSMArena metadata ...")
    gsm = GSMArenaScaper()
    meta = await gsm.scrape()
    await _upsert_device_metadata(meta)
    logger.info(f"GSMArena: {len(meta)} devices upserted")

    logger.info("Step 2/2: Scraping store prices ...")
    for cls in STORE_SCRAPERS:
        await _run_store_scraper(cls)
        logger.info(f"{cls.slug}: done")

    logger.info("=== Scrape run complete ===")


if __name__ == "__main__":
    asyncio.run(main())
