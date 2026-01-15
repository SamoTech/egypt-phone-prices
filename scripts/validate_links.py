#!/usr/bin/env python3
"""
Link Validation Script
Validates all product links in prices.json and removes dead links
"""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# flake8: noqa: E402
from engine.pipelines import LinkValidator  # noqa: E402


def main():
    """Validate all product links."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    prices_file = os.path.join(data_dir, "prices.json")

    if not os.path.exists(prices_file):
        print("⚠️  prices.json not found")
        return 1

    # Load prices data
    with open(prices_file, "r", encoding="utf-8") as f:
        prices_data = json.load(f)

    print(f"Validating links in {len(prices_data)} variants...")

    # Validate
    validator = LinkValidator(timeout=10)
    validated_data = validator.validate_offers(prices_data)
    validator.close()

    # Save validated data
    with open(prices_file, "w", encoding="utf-8") as f:
        json.dump(validated_data, f, indent=2, ensure_ascii=False)

    # Copy to docs/
    docs_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "prices.json")
    with open(docs_file, "w", encoding="utf-8") as f:
        json.dump(validated_data, f, indent=2, ensure_ascii=False)

    print("✅ Link validation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
