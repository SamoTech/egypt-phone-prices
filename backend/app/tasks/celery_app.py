"""Celery application with beat schedule for daily scraping."""
from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "egypt_phones",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scrape_tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Cairo",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        # Daily full scrape at 03:00 Cairo time
        "daily-full-scrape": {
            "task": "app.tasks.scrape_tasks.run_full_scrape",
            "schedule": crontab(hour=3, minute=0),
        },
        # Lightweight price-only refresh every 6 hours
        "price-refresh": {
            "task": "app.tasks.scrape_tasks.run_price_refresh",
            "schedule": crontab(minute=0, hour="*/6"),
        },
    },
)
