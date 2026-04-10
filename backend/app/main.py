"""FastAPI app — exposes /health and /api/admin/trigger-scrape."""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .tasks.scrape_tasks import run_full_scrape, run_price_refresh

app = FastAPI(title="Egypt Phone Prices API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/admin/trigger-scrape")
async def trigger_scrape(full: bool = False):
    """Manually trigger a scrape job."""
    if full:
        task = run_full_scrape.delay()
    else:
        task = run_price_refresh.delay()
    return {"queued": True, "task_id": task.id, "type": "full" if full else "price"}


@app.get("/api/admin/trigger-seed")
async def trigger_seed():
    """Trigger a full metadata + price scrape (alias for onboarding)."""
    task = run_full_scrape.delay()
    return {"queued": True, "task_id": task.id}
