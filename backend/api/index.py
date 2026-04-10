"""Vercel serverless entry point — wraps FastAPI app with Mangum."""
import sys
import os

# Ensure backend/ is on the path so 'app.*' imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mangum import Mangum  # noqa: E402
from app.main import app    # noqa: E402

# Strip /api prefix so FastAPI router sees /devices, /prices, etc.
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from starlette.requests import Request  # noqa: E402


class StripApiPrefix(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        scope = request.scope
        path = scope.get("path", "")
        if path.startswith("/api"):
            scope["path"] = path[4:] or "/"
            raw = scope.get("raw_path", b"")
            if raw.startswith(b"/api"):
                scope["raw_path"] = raw[4:] or b"/"
        return await call_next(request)


app.add_middleware(StripApiPrefix)

handler = Mangum(app, lifespan="off")
