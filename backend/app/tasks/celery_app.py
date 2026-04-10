"""Celery application and beat schedule."""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "egypt_phones",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.scrape_tasks"],
)

celery_app.conf.beat_schedule = {
    "daily-scrape": {
        "task": "app.tasks.scrape_tasks.run_all_scrapers",
        "schedule": crontab(
            hour=str(settings.SCRAPE_CRON_HOUR),
            minute=str(settings.SCRAPE_CRON_MINUTE),
        ),
    }
}

celery_app.conf.timezone = "Africa/Cairo"
