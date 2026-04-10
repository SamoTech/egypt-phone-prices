"""Vercel Python serverless entry point.

Vercel's @vercel/python runtime looks for `app` in api/index.py.
Mangum wraps the ASGI FastAPI app for AWS Lambda / Vercel compatibility.
"""
import sys
import os

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: F401 — Vercel imports `app`

# Mangum handler for ASGI → Lambda/Vercel bridge
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Fallback: Vercel can also use the raw ASGI app
    handler = app
