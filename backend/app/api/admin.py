from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger

from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_token(authorization: str = ""):
    """Simple bearer token auth for admin endpoints."""
    from fastapi import Header
    return authorization


async def _require_token(authorization: str = ""):
    expected = f"Bearer {settings.ADMIN_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token")


# ─── Trigger full scrape ──────────────────────────────────────────────────────
@router.post("/trigger-scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    _: None = Depends(_require_token),
):
    """Kick off a full scrape run as a FastAPI background task.
    
    Called by:
    - Vercel Cron Job via /api/cron/scrape (Next.js route)
    - Manual curl for testing
    """
    background_tasks.add_task(_run_scrape_background)
    return {"message": "Scrape started in background", "status": "ok"}


async def _run_scrape_background():
    """Full scrape pipeline: GSMArena metadata → all store prices."""
    try:
        from app.scrapers.gsmarena import GSMArenaScaper
        from app.tasks.scrape_tasks import (
            _upsert_device_metadata,
            _run_store_scraper,
            STORE_SCRAPERS,
        )

        logger.info("[scrape] Starting GSMArena metadata fetch ...")
        gsm = GSMArenaScaper()
        meta = await gsm.scrape()
        await _upsert_device_metadata(meta)
        logger.info(f"[scrape] GSMArena: {len(meta)} devices upserted")

        for cls in STORE_SCRAPERS:
            logger.info(f"[scrape] Running {cls.slug} scraper ...")
            await _run_store_scraper(cls)
            logger.info(f"[scrape] {cls.slug}: done")

        logger.info("[scrape] Full scrape run complete")

    except Exception as e:
        logger.error(f"[scrape] Background scrape failed: {e}")


# ─── Health / stats ───────────────────────────────────────────────────────────
@router.get("/stats")
async def admin_stats(_: None = Depends(_require_token)):
    """Return row counts for all tables."""
    from app.db.session import async_session
    from sqlalchemy import text

    async with async_session() as db:
        result = await db.execute(text("""
            select
                (select count(*) from brands)      as brands,
                (select count(*) from devices)     as devices,
                (select count(*) from retailers)   as retailers,
                (select count(*) from prices)      as prices,
                (select count(*) from scrape_logs) as scrape_logs
        """))
        row = result.mappings().one()
        return dict(row)


@router.get("/logs")
async def scrape_logs(
    limit: int = 20,
    _: None = Depends(_require_token),
):
    """Return the last N scrape log entries."""
    from app.db.session import async_session
    from sqlalchemy import text

    async with async_session() as db:
        result = await db.execute(text("""
            select * from scrape_logs
            order by started_at desc
            limit :limit
        """), {"limit": limit})
        return result.mappings().all()
