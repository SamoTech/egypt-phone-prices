# Migration Guide: CSV to JSON

## Overview

The system has been upgraded from manual CSV-based data entry to fully automated JSON-based pipelines.

## What Changed

### Old System (Deprecated)
- ❌ `data/phones.csv` - Manual phone entry
- ❌ `scraper.py` - Basic scraper with hardcoded phones
- ❌ Manual updates required for new phones

### New System (Active)
- ✅ `data/phones_specs.json` - Auto-generated from GSMArena
- ✅ `data/phone_variants.json` - Auto-detected variants
- ✅ `data/prices.json` - Scraped prices with confidence scores
- ✅ `scrapers/specs_pipeline_new.py` - Automated specs scraping
- ✅ `scrapers/price_pipeline.py` - Automated price scraping

## Data Format Changes

### Phone Specifications (OLD: CSV → NEW: JSON)

**OLD Format (phones.csv):**
```csv
id,brand,model,ram,storage,price...
1,Samsung,Galaxy S24,12GB,256GB,32000...
```

**NEW Format (phones_specs.json):**
```json
{
  "brand": "Samsung",
  "model": "Galaxy S24 Ultra",
  "slug": "samsung_galaxy_s24_ultra",
  "release_year": 2024,
  "release_date": "2024-01-25",
  "display": {
    "size": 6.8,
    "type": "Dynamic AMOLED",
    "refresh_rate": 120
  },
  "chipset": "Snapdragon 8 Gen 3",
  "ram_options": ["12GB", "16GB"],
  "storage_options": ["256GB", "512GB", "1TB"],
  "battery": 5000,
  "5g": true,
  "gsmarena_url": "https://www.gsmarena.com/..."
}
```

### Prices (NEW: JSON with Confidence Scores)

**NEW Format (prices.json):**
```json
{
  "samsung_galaxy_s24_ultra_12_256": {
    "phone_slug": "samsung_galaxy_s24_ultra",
    "variant": "12GB/256GB",
    "offers": [
      {
        "store": "amazon_eg",
        "price": 32999,
        "currency": "EGP",
        "url": "https://www.amazon.eg/...",
        "confidence": 0.92,
        "availability": "in_stock",
        "scraped_at": "2026-01-15T12:30:00Z"
      }
    ],
    "best_price": 32999,
    "best_store": "amazon_eg"
  }
}
```

## Migration Steps (Already Complete)

1. ✅ Created new pipeline infrastructure
2. ✅ Implemented GSMArena scrapers
3. ✅ Implemented marketplace price scrapers
4. ✅ Created matching and validation engine
5. ✅ Updated GitHub Actions workflows
6. ✅ Updated documentation

## Transition Period

- **CSV files remain** in repository for reference
- **New pipelines are active** and will populate JSON files
- **Frontend needs update** to read from JSON (Phase 7)
- **CSV will be removed** after frontend migration

## For Developers

### To Add New Phones
**OLD:** Edit `data/phones.csv` manually  
**NEW:** Automatically discovered from GSMArena (2023+)

### To Update Prices
**OLD:** Run `scraper.py` manually  
**NEW:** Runs automatically every 6 hours via GitHub Actions

### To Run Locally
```bash
# Specs scraping (weekly)
python -m scrapers.specs_pipeline_new --test

# Price scraping (6-hourly)
python -m scrapers.price_pipeline --test
```

## API Changes for Frontend

### OLD API (phones.json)
```javascript
fetch('phones.json').then(r => r.json())
// Returns: [{ name, price, store, ... }]
```

### NEW APIs (Multiple Files)
```javascript
// Load specs
const specs = await fetch('specs.json').then(r => r.json());
// Returns: [{ brand, model, display, chipset, ... }]

// Load prices
const prices = await fetch('prices.json').then(r => r.json());
// Returns: { variant_slug: { offers: [...], best_price, ... } }
```

## Breaking Changes

⚠️ **Frontend must be updated** to use new JSON structure (Phase 7)  
⚠️ **Old scraper.py deprecated** - use new pipelines  
⚠️ **CSV format no longer updated** - JSON is source of truth

## Benefits

✅ Zero manual data entry  
✅ Always up-to-date phone specs  
✅ Multiple price sources with confidence scores  
✅ Variant support (different RAM/storage)  
✅ Historical price tracking  
✅ Better error handling and logging  

## Questions?

See [README.md](README.md) for detailed documentation.
