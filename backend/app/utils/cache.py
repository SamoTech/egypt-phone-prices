"""Simple Redis cache wrapper."""
import json
from typing import Any, Optional

from loguru import logger

try:
    import redis.asyncio as aioredis
    from app.core.config import settings
    _pool = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    _pool = None  # type: ignore

DEFAULT_TTL = 300  # 5 minutes


async def cache_response(key: str, value: Any = None, ttl: int = DEFAULT_TTL) -> Optional[Any]:
    """Get from cache if value is None, else set cache."""
    if _pool is None:
        return None
    try:
        if value is None:
            raw = await _pool.get(key)
            return json.loads(raw) if raw else None
        else:
            payload = value.model_dump_json() if hasattr(value, "model_dump_json") else json.dumps(value)
            await _pool.setex(key, ttl, payload)
            return value
    except Exception as exc:
        logger.warning(f"Cache error for key={key}: {exc}")
        return None
