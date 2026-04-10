"""Vercel serverless entry point — exposes the FastAPI app.

Vercel looks for a file at api/index.py and imports `app` from it.
All routes defined in app.main are served through this handler.

Note: Celery workers cannot run inside Vercel serverless functions.
For the daily scrape job, use one of these free-tier options:
  - GitHub Actions cron (see .github/workflows/scrape.yml)
  - Vercel Cron Jobs (vercel.json `crons` key, Pro plan)
  - A free Render.com background worker
"""
import sys
import os

# Make sure the backend/ directory is on the path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app  # noqa: F401  — Vercel imports `app` from this module
