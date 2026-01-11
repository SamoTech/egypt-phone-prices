import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from utils.price_calculator import compute_metrics_for_row
from utils.error_handler import with_retry, log_error
from scrapers.amazon import scrape_amazon_prices
from scrapers.jumia import scrape_jumia_prices
from scrapers.noon import scrape_noon_prices
from scrapers.stores import scrape_other_stores

DATA_DIR = Path("data")
PHONES_CSV = DATA_DIR / "phones.csv"
HISTORY_CSV = DATA_DIR / "phones_history.csv"

STORE_COLUMNS = [
    "amazon_eg", "jumia_eg", "noon_eg", "btech", "2b", "raya",
    "carrefour", "emax", "xcite", "sharafdg", "extra",
    "orange_eg", "vodafone_eg", "we_eg",
    "mobileshop", "megastore", "technologystore",
    "virgin", "tradeline", "master",
    "lg_store", "samsung_store", "xiaomi_store", "oppo_store", "realme_store",
    "yallashabab", "smartbuy", "elnekhely", "cairosales", "alborg",
]

URL_COLUMNS = [c + "_url" for c in STORE_COLUMNS]


def load_phones():
    with PHONES_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    return rows, fieldnames


def save_phones(rows, fieldnames):
    tmp = PHONES_CSV.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    tmp.replace(PHONES_CSV)


def append_history(rows):
    history_fieldnames = ["timestamp", "id"] + STORE_COLUMNS
    exists = HISTORY_CSV.exists()
    with HISTORY_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=history_fieldnames)
        if not exists:
            writer.writeheader()
        ts = datetime.now(timezone.utc).isoformat()
        for row in rows:
            writer.writerow(
                {"timestamp": ts, "id": row["id"], **{s: row.get(s, "") for s in STORE_COLUMNS}}
            )


@with_retry(max_retries=3, backoff_seconds=5)
def scrape_stores_for_phone(phone_row):
    brand = phone_row["brand"]
    model = phone_row["model"]
    results = {}

    results.update(scrape_amazon_prices(brand, model))
    time.sleep(3)
    results.update(scrape_jumia_prices(brand, model))
    time.sleep(3)
    results.update(scrape_noon_prices(brand, model))
    time.sleep(3)
    results.update(scrape_other_stores(brand, model))

    return results


def main(flagship_only=False):
    rows, fieldnames = load_phones()
    changed = False
    failures = 0
    total = 0

    for row in rows:
        total += 1
        if flagship_only and row.get("price_segment") != "flagship":
            continue

        try:
            updates = scrape_stores_for_phone(row)
        except Exception as e:
            log_error(f"Failed all scrapers for {row['id']} {row['brand']} {row['model']}: {e}")
            failures += 1
            continue

        for col in STORE_COLUMNS + URL_COLUMNS:
            if col in updates and updates[col] is not None:
                row[col] = str(updates[col])

        compute_metrics_for_row(row, STORE_COLUMNS)
        row["last_price_update"] = datetime.now(timezone.utc).isoformat()
        changed = True
        time.sleep(2)

    if changed:
        save_phones(rows, fieldnames)
        append_history(rows)
        print(f"Scrape complete. Processed {total} phones, {failures} failures.")

    if total > 0 and failures / total > 0.5:
        try:
            from utils.notifier import notify_many_failures
            notify_many_failures(failures, total)
        except Exception as e:
            log_error(f"Notifier failed: {e}")


if __name__ == "__main__":
    flagship_only = "--flagship-only" in sys.argv
    main(flagship_only=flagship_only)
