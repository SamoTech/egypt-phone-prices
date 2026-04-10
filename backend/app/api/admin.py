"""Admin endpoints — protected by bearer token."""
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Device, Price, ScrapeLog
from app.db.session import get_db
from app.tasks.scrape_tasks import run_all_scrapers

router = APIRouter()
bearer = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(bearer)):
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")


@router.get("/stats", dependencies=[Depends(verify_token)])
async def admin_stats(db: AsyncSession = Depends(get_db)):
    devices_total = (await db.execute(select(func.count()).select_from(Device))).scalar_one()
    prices_total = (await db.execute(select(func.count()).select_from(Price))).scalar_one()
    last_log = (
        await db.execute(
            select(ScrapeLog).order_by(ScrapeLog.started_at.desc()).limit(10)
        )
    ).scalars().all()
    return {
        "devices": devices_total,
        "prices": prices_total,
        "recent_scrapes": [
            {
                "retailer": l.retailer_slug,
                "status": l.status,
                "scraped": l.devices_scraped,
                "started": str(l.started_at),
            }
            for l in last_log
        ],
    }


@router.post("/trigger-scrape", dependencies=[Depends(verify_token)])
async def trigger_scrape():
    run_all_scrapers.delay()
    return {"message": "Scrape task dispatched"}
