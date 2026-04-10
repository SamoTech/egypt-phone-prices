"""SQLAlchemy ORM models."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    devices: Mapped[list["Device"]] = relationship(back_populates="brand")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    gsmarena_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))
    display: Mapped[str | None] = mapped_column(String(200))
    chipset: Mapped[str | None] = mapped_column(String(200))
    ram: Mapped[str | None] = mapped_column(String(100))
    storage: Mapped[str | None] = mapped_column(String(100))
    camera: Mapped[str | None] = mapped_column(String(200))
    battery: Mapped[str | None] = mapped_column(String(100))
    os: Mapped[str | None] = mapped_column(String(100))
    release_year: Mapped[int | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    brand: Mapped["Brand"] = relationship(back_populates="devices")
    prices: Mapped[list["Price"]] = relationship(back_populates="device")


class Retailer(Base):
    __tablename__ = "retailers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(300), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    prices: Mapped[list["Price"]] = relationship(back_populates="retailer")


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("devices.id"), nullable=False)
    retailer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("retailers.id"), nullable=False)
    price_egp: Mapped[float] = mapped_column(Float, nullable=False)
    original_price_egp: Mapped[float | None] = mapped_column(Float)
    product_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    device: Mapped["Device"] = relationship(back_populates="prices")
    retailer: Mapped["Retailer"] = relationship(back_populates="prices")

    __table_args__ = (
        UniqueConstraint("device_id", "retailer_id", "scraped_at", name="uq_price_record"),
    )


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    retailer_slug: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    devices_scraped: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
