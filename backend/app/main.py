"""Egypt Phone Prices — FastAPI entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import devices, prices, trends, admin
from app.core.config import settings
from app.db.session import engine
from app.db import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield


app = FastAPI(
    title="Egypt Phone Prices API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(prices.router, prefix="/prices", tags=["prices"])
app.include_router(trends.router, prefix="/trends", tags=["trends"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}
