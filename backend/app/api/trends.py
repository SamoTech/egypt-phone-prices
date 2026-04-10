"""GET /trends — price history per device."""
import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Price, Retailer
from app.db.schemas import PriceTrendPoint
from app.db.session import get_db

router = APIRouter()


@router.get("", response_model=list[PriceTrendPoint])
async def get_trends(
    device_id: uuid.UUID = Query(...),
    days: int = Query(90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    since = date.today() - timedelta(days=days)
    stmt = (
        select(
            func.date(Price.scraped_at).label("day"),
            Retailer.name.label("retailer"),
            func.min(Price.price_egp).label("price_egp"),
        )
        .join(Retailer)
        .where(Price.device_id == device_id, func.date(Price.scraped_at) >= since)
        .group_by(func.date(Price.scraped_at), Retailer.name)
        .order_by(func.date(Price.scraped_at))
    )
    rows = (await db.execute(stmt)).all()
    return [
        PriceTrendPoint(date=str(r.day), retailer=r.retailer, price_egp=r.price_egp)
        for r in rows
    ]
