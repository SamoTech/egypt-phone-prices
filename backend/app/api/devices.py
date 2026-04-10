"""GET /devices and GET /devices/{id}"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Brand, Device
from app.db.schemas import DeviceOut, PaginatedDevices
from app.db.session import get_db
from app.utils.cache import cache_response

router = APIRouter()


@router.get("", response_model=PaginatedDevices)
async def list_devices(
    brand: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"devices:{brand}:{search}:{year}:{page}:{per_page}"
    cached = await cache_response(cache_key)
    if cached:
        return cached

    stmt = select(Device).options(selectinload(Device.brand)).where(Device.is_active.is_(True))

    if brand:
        stmt = stmt.join(Brand).where(func.lower(Brand.slug) == brand.lower())
    if search:
        stmt = stmt.where(Device.name.ilike(f"%{search}%"))
    if year:
        stmt = stmt.where(Device.release_year == year)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * per_page).limit(per_page).order_by(Device.release_year.desc())
    items = (await db.execute(stmt)).scalars().all()

    result = PaginatedDevices(
        total=total, page=page, per_page=per_page, items=[DeviceOut.model_validate(d) for d in items]
    )
    await cache_response(cache_key, result, ttl=300)
    return result


@router.get("/{slug}", response_model=DeviceOut)
async def get_device(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Device)
        .options(selectinload(Device.brand))
        .where(Device.slug == slug, Device.is_active.is_(True))
    )
    device = (await db.execute(stmt)).scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceOut.model_validate(device)
