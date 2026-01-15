"""
Lightweight specs pipeline orchestrator.
- Runs GSMArena scraper
- Validates using optional Pydantic validators if available
- Writes data/specs.json and returns a status dict
"""

from typing import List, Dict, Any
import json
import uuid
import logging
from datetime import datetime
import os

from scrapers.gsmarena_scraper import GSMArenaScrapers

logger = logging.getLogger(__name__)

DATA_DIR = "data"
DATA_PATH = os.path.join(DATA_DIR, "specs.json")

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def run_specs_pipeline(save: bool = True) -> Dict[str, Any]:
    """Run the GSMArena specs scraper, optionally validate and save results.

    Returns a status dictionary with basic metrics and any errors.
    """
    execution_id = f"specs_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
    status: Dict[str, Any] = {
        "execution_id": execution_id,
        "pipeline_type": "specs",
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "specs_scraped": 0,
        "errors": [],
    }

    _ensure_data_dir()

    scraper = GSMArenaScrapers()
    try:
        phones = scraper.scrape()
        validated = []

        # Attempt to validate with Pydantic validators if available
        try:
            from utils.validators import PhoneSpecsDatabase
            use_validators = True
        except Exception:
            PhoneSpecsDatabase = None
            use_validators = False

        for phone in phones:
            if use_validators and PhoneSpecsDatabase is not None:
                try:
                    validated_item = PhoneSpecsDatabase(**phone)
                    validated.append(validated_item.dict_for_storage() if hasattr(validated_item, 'dict_for_storage') else validated_item.dict())
                except Exception as e:
                    logger.warning(f"Validation failed for {phone.get('model', '<unknown>')}: {e}")
                    status["errors"].append({"source": "GSMArena", "error": str(e), "url": phone.get('gsmarena_url')})
            else:
                # No validators available; accept raw phone dict if it has minimal fields
                if phone and phone.get('model') and phone.get('brand'):
                    validated.append(phone)
                else:
                    status["errors"].append({"source": "GSMArena", "error": "Missing minimal fields", "url": phone.get('gsmarena_url') if isinstance(phone, dict) else None})

        status["specs_scraped"] = len(validated)
        status["status"] = "success" if not status["errors"] else "partial_failure"

        if save:
            payload = {"phones": validated, "generated_at": datetime.utcnow().isoformat()}
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(validated)} phone specs to {DATA_PATH}")

    except Exception as e:
        logger.exception("Specs pipeline failed")
        status["status"] = "failure"
        status["errors"].append({"source": "GSMArena", "error": str(e)})

    finally:
        try:
            scraper.close()
        except Exception:
            pass
        status["completed_at"] = datetime.utcnow().isoformat()
        return status
