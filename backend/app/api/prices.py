"""GET /prices?device_id=..."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device, Price
from app.db.schemas import PriceOut
from app.db.session import get_db

router = APIRouter()


@router.get("", response_model=list[PriceOut])
async def get_prices(
    device_id: uuid.UUID = Query(...),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Price)
        .options(selectinload(Price.retailer))
        .where(Price.device_id == device_id)
        .order_by(desc(Price.scraped_at))
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [PriceOut.model_validate(r) for r in rows]
