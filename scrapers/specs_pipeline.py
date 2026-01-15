"""
Lightweight specs pipeline orchestrator.
- Runs GSMArena scraper
- Validates using Pydantic validators (utils.validators)
- Writes data/specs.json and returns PipelineStatus as dict
"""

from typing import List, Dict, Any
import json
import uuid
import logging
from datetime import datetime

from scrapers.gsmarena_scraper import GSMArenaScraper
from utils.validators import PhoneSpecsDatabase, PipelineStatus, ScraperErrorLog
from utils.logger import pipeline_logger

logger = logging.getLogger(__name__)

DATA_PATH = "data/specs.json"

def run_specs_pipeline(save: bool = True) -> Dict[str, Any]:
    run_id = f"specs_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
    status = PipelineStatus(
        execution_id=run_id,
        pipeline_type="specs",
        status="running",
        timestamp=datetime.utcnow().isoformat(),
        started_at=datetime.utcnow().isoformat(),
    )

    pipeline_logger.log_scrape_start("GSMArena", "gsmarena.com")

    scraper = GSMArenaScraper()
    try:
        phones = scraper.scrape()

        validated_phones = []
        errors: List[ScraperErrorLog] = []
        for phone in phones:
            try:
                db_item = PhoneSpecsDatabase(**phone)
                validated_phones.append(db_item.dict_for_storage())
            except Exception as e:
                logger.warning(f"Validation failed for {phone.get('model', 'unknown')}: {e}")
                errors.append(ScraperErrorLog(source="GSMArena", error_type=type(e).__name__, error_message=str(e), url=phone.get('gsmarena_url')))

        status.specs_scraped = len(validated_phones)
        status.errors = [err for err in errors]
        status.status = "success" if not errors else "partial_failure"

        if save:
            payload = {"phones": validated_phones, "generated_at": datetime.utcnow().isoformat()}
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

        pipeline_logger.log_scrape_end("GSMArena", items_scraped=len(validated_phones), duration_seconds=0)

    except Exception as e:
        logger.exception("Specs pipeline failed")
        status.status = "failure"
        status.errors.append(ScraperErrorLog(source="GSMArena", error_type=type(e).__name__, error_message=str(e)))

    finally:
        try:
            scraper.close()
        except Exception:
            pass
        status.completed_at = datetime.utcnow().isoformat()
        return status.dict()