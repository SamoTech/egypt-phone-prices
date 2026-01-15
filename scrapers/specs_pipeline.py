"""
Orchestration pipeline to scrape phone specifications from GSMArena, validate them with Pydantic validators,
and write output to data/specs.json and docs/specs.json. Designed to be used by CI (weekly job).
"""

from datetime import datetime
import json
import os
import uuid
import logging
from typing import List

from scrapers.gsmarena_scraper import GSMArenaScrapers
from utils.validators import PhoneSpecsDatabase, PhoneSpecsBatch, PipelineStatus, ScraperErrorLog
from utils.logger import pipeline_logger

logger = logging.getLogger(__name__)

def run_specs_pipeline(batch_id: str = None) -> PipelineStatus:
    pipeline_id = batch_id or f"specs_{uuid.uuid4().hex[:8]}"
    started_at = datetime.utcnow().isoformat()

    status = PipelineStatus(
        execution_id=pipeline_id,
        pipeline_type="specs",
        status="running",
        specs_scraped=0,
        prices_scraped=0,
        items_updated=0,
        errors=[],
        started_at=started_at
    )

    try:
        scraper = GSMArenaScrapers()
        phones = []

        pipeline_logger.info("Starting GSMArena specs scraper", extra_data={"execution_id": pipeline_id})

        # Scrape popular brands (scraper internally iterates whitelist)
        scraped = scraper.scrape()

        for p in scraped:
            try:
                # Validate using Pydantic model
                model = PhoneSpecsDatabase(**{
                    "brand": p.get("brand"),
                    "model": p.get("model"),
                    "release_year": p.get("release_year") or 2023,
                    "release_date": p.get("release_date"),
                    "specs": p.get("specs"),
                    "gsmarena_url": p.get("gsmarena_url"),
                    "last_updated": p.get("last_updated") or datetime.utcnow().isoformat()
                })

                phones.append(model.dict_for_storage())
                status.specs_scraped += 1

            except Exception as e:
                logger.warning(f"Validation failed for phone: {p.get('model')} - {e}")
                status.errors.append(ScraperErrorLog(
                    source="GSMArena",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    url=p.get("gsmarena_url")
                ).dict())

        # Persist data
        os.makedirs('data', exist_ok=True)
        with open('data/specs.json', 'w', encoding='utf-8') as f:
            json.dump({"phones": phones, "generated_at": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)

        # Also write to docs so GitHub Pages can read it
        os.makedirs('docs', exist_ok=True)
        with open('docs/specs.json', 'w', encoding='utf-8') as f:
            json.dump({"phones": phones, "generated_at": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)

        status.status = "success"
        status.items_updated = len(phones)

    except Exception as e:
        logger.exception(f"Specs pipeline failed: {e}")
        status.status = "failure"
        status.errors.append(ScraperErrorLog(
            source="GSMArena",
            error_type=type(e).__name__,
            error_message=str(e)
        ).dict())

    finally:
        status.completed_at = datetime.utcnow().isoformat()
        status.duration_seconds = (datetime.fromisoformat(status.completed_at) - datetime.fromisoformat(status.started_at)).total_seconds() if status.started_at and status.completed_at else None

        # Persist pipeline status to data
        with open('data/specs_pipeline_status.json', 'w', encoding='utf-8') as f:
            json.dump(status.dict(), f, ensure_ascii=False, indent=2)

    return status


if __name__ == '__main__':
    run_specs_pipeline()