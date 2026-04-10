"""Egypt Phone Prices — FastAPI entry point (Vercel serverless)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are created via Alembic migrations, not auto-create
    # (auto-create on every cold start is too slow for serverless)
    yield


app = FastAPI(
    title="Egypt Phone Prices API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers — imported here to avoid top-level heavy imports on cold start
from app.api import devices, prices, trends, admin  # noqa: E402

app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(prices.router, prefix="/prices", tags=["prices"])
app.include_router(trends.router, prefix="/trends", tags=["trends"])
app.include_router(admin.router, tags=["admin"])


@app.get("/health")
async def health():
    from app.db.session import engine
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
