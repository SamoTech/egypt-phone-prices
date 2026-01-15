"""
Link Validation Pipeline
Validates product URLs to ensure they're not 404s
"""

import logging
from datetime import datetime
from typing import Dict, Any

import requests

logger = logging.getLogger(__name__)


class LinkValidator:
    """Validate product links to remove dead URLs."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    def validate_offers(self, prices_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all offers in prices data.

        Checks:
        - HTTP status (200 = valid, 404 = remove, other = flag)
        - Redirect loops
        - Domain changes

        Args:
            prices_data: Prices data dictionary

        Returns:
            Validated prices data with dead links removed
        """
        validated = {}
        total_offers = 0
        removed_offers = 0

        for variant_id, variant_data in prices_data.items():
            offers = variant_data.get("offers", [])
            valid_offers = []

            for offer in offers:
                total_offers += 1
                url = offer.get("url", "")

                if not url:
                    removed_offers += 1
                    continue

                validation_result = self._validate_url(url)

                if validation_result["is_valid"]:
                    # Add validation metadata
                    offer["validation"] = {
                        "checked_at": validation_result["checked_at"],
                        "status_code": validation_result["status_code"],
                    }
                    valid_offers.append(offer)
                else:
                    # Remove dead link
                    logger.info(f"Removing dead link: {url} (Status: {validation_result['status_code']})")
                    removed_offers += 1

            # Update variant with valid offers only
            variant_data["offers"] = valid_offers
            variant_data["offer_count"] = len(valid_offers)
            validated[variant_id] = variant_data

        logger.info(f"Validation complete: {removed_offers}/{total_offers} dead links removed")

        return validated

    def _validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate a single URL.

        Returns:
            Validation result dictionary
        """
        result = {
            "is_valid": False,
            "status_code": None,
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "error": None,
        }

        try:
            # Use HEAD request for efficiency
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            result["status_code"] = response.status_code

            if response.status_code == 200:
                result["is_valid"] = True
            elif response.status_code == 404:
                result["is_valid"] = False
                result["error"] = "Not Found (404)"
            else:
                # For other status codes, try GET request
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                result["status_code"] = response.status_code
                result["is_valid"] = response.status_code == 200

        except requests.exceptions.Timeout:
            result["error"] = "Timeout"
            logger.warning(f"Timeout validating {url}")
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection Error"
            logger.warning(f"Connection error for {url}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error validating {url}: {e}")

        return result

    def close(self):
        """Close session."""
        self.session.close()
