"""Async SQLAlchemy engine — Supabase/PgBouncer compatible."""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Supabase uses PgBouncer in transaction mode which does not support
# prepared statements. Setting statement_cache_size=0 disables them.
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={"statement_cache_size": 0},
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db():
    async with async_session() as session:
        yield session
