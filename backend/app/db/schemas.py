"""Pydantic response schemas."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BrandOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class DeviceOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    brand: BrandOut
    image_url: Optional[str] = None
    display: Optional[str] = None
    chipset: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    camera: Optional[str] = None
    battery: Optional[str] = None
    os: Optional[str] = None
    release_year: Optional[int] = None

    model_config = {"from_attributes": True}


class RetailerOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    base_url: str
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class PriceOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    retailer: RetailerOut
    price_egp: float
    original_price_egp: Optional[float] = None
    product_url: str
    in_stock: bool
    scraped_at: datetime

    model_config = {"from_attributes": True}


class PriceTrendPoint(BaseModel):
    date: str
    retailer: str
    price_egp: float


class PaginatedDevices(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[DeviceOut]
