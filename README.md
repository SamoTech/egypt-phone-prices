# Egyptian Phone Price & Specs Comparison Platform

**Fully automated system** that discovers phones from GSMArena and tracks Egyptian market prices across multiple retailers.

## 🚀 Features

- ✅ **Automatic phone discovery** - No manual data entry required
- ✅ **Weekly specs updates** - Always up-to-date phone specifications from GSMArena
- ✅ **6-hour price updates** - Fresh pricing from Amazon.eg, Jumia, Noon
- ✅ **Intelligent matching** - Fuzzy matching with confidence scores (0.7-1.0)
- ✅ **Variant support** - Tracks different RAM/storage combinations
- ✅ **Historical tracking** - 30-day price history snapshots
- ✅ **GitHub Pages deployment** - Free static hosting, no server required
- ✅ **Production-grade** - Error handling, rate limiting, retry logic

## 🏗️ Architecture

### Automated Pipelines

1. **Specs Pipeline** (Weekly - Sundays 3 AM UTC)
   - Scrapes GSMArena for new phones released 2023+
   - Extracts detailed specifications (display, chipset, camera, battery, etc.)
   - Generates `data/phones_specs.json` and `data/phone_variants.json`

2. **Price Pipeline** (Every 6 hours)
   - Scrapes Egyptian retailers (Amazon.eg, Jumia, Noon)
   - Uses Playwright for JavaScript-heavy sites
   - Validates matches using fuzzy logic and confidence scoring
   - Generates `data/prices.json` with best prices

### Data Flow

```
GSMArena → specs_pipeline → phones_specs.json + phone_variants.json
                                         ↓
Egyptian Stores → price_pipeline → prices.json → GitHub Pages
```

### Technology Stack

- **Specs Scraping**: BeautifulSoup + Requests (GSMArena)
- **Price Scraping**: Playwright (headless Chromium)
- **Matching Engine**: FuzzyWuzzy (Levenshtein distance)
- **Validation**: Custom rules (accessory detection, price outliers, variant matching)
- **Automation**: GitHub Actions (scheduled workflows)
- **Frontend**: Vanilla HTML/CSS/JavaScript

## 📊 Data Files

- `data/phones_specs.json` - Complete phone specifications database
- `data/phone_variants.json` - RAM/storage variant combinations
- `data/prices.json` - Latest market prices with confidence scores
- `data/scrape_errors.json` - Error logs for debugging
- `data/history/` - 30-day price history snapshots (auto-cleanup)
- `docs/specs.json` - Copy of specs for GitHub Pages
- `docs/prices.json` - Copy of prices for GitHub Pages

## 🛠️ Development

### Prerequisites

```bash
Python 3.11+
pip install -r requirements.txt
playwright install chromium  # For price scraping
```

### Run Specs Scraper Locally

```bash
# Test mode (2 brands, 3 phones each)
python -m scrapers.specs_pipeline_new --test

# Full run (all priority brands, phones from 2023+)
python -m scrapers.specs_pipeline_new

# Custom options
python -m scrapers.specs_pipeline_new --min-year 2024 --all-brands --max-phones 10
```

### Run Price Scraper Locally

```bash
# Test mode (5 phones only)
python -m scrapers.price_pipeline --test

# Full run
python -m scrapers.price_pipeline

# Specific stores
python -m scrapers.price_pipeline --stores amazon_eg jumia_eg
```

### Test Matching Engine

```bash
python3 << 'EOF'
from engine.matcher import fuzzy_match_phone
from engine.validator import validate_offer, is_accessory
from engine.normalizer import normalize_brand, create_slug

# Test fuzzy matching
result = {"title": "Samsung Galaxy S24 Ultra 256GB", "description": ""}
phone = {"brand": "Samsung", "model": "Galaxy S24 Ultra", "storage": "256GB"}
score = fuzzy_match_phone(result, phone)
print(f"Confidence: {score:.2f}")

# Test normalization
print(normalize_brand("SAMSUNG"))  # → "Samsung"
print(create_slug("Samsung", "Galaxy S24 Ultra"))  # → "samsung_galaxy_s24_ultra"
EOF
```

## 🔧 Configuration

### Supported Brands (Priority)
Samsung, Apple, Xiaomi, Oppo, Realme, OnePlus, Google, Motorola, Nokia, Vivo, Infinix, Tecno

### Supported Stores
- Amazon Egypt (amazon.eg)
- Jumia Egypt (jumia.com.eg)
- Noon Egypt (noon.com/egypt-en)

### Scraping Parameters

| Parameter | Specs Pipeline | Price Pipeline |
|-----------|---------------|----------------|
| Rate Limiting | 2-3 seconds | 1.5-4 seconds |
| Timeout | 15 seconds | 30 seconds |
| Confidence Threshold | N/A | 0.70 |
| Min Release Year | 2023 | N/A |

## 📈 Reliability & Error Handling

- **Fault-tolerant**: Pipeline continues if one phone/store fails
- **Rate limiting**: Respects delays to avoid blocking
- **Error logging**: All failures logged to `data/scrape_errors.json`
- **Last known good**: Retains previous prices if scrape fails
- **Retry logic**: Built-in retry for transient errors
- **Validation**: Rejects accessories, refurbished phones, wrong variants

## 🚫 Constraints & Design Decisions

- ❌ No paid APIs - Uses free web scraping only
- ❌ No manual phone entry - 100% automated discovery
- ❌ No external databases - All data in Git repository
- ✅ 100% GitHub infrastructure (Actions + Pages)
- ✅ Defensive coding - Handles site changes gracefully
- ✅ Privacy-first - No user tracking, no analytics

## 📝 Project Structure

```
egypt-phone-prices/
├── .github/workflows/
│   ├── update-specs.yml       # Weekly specs scraper
│   └── update-prices.yml      # 6-hourly price scraper
├── scrapers/
│   ├── gsmarena/              # GSMArena specs scrapers
│   │   ├── brands.py          # Brand discovery
│   │   ├── phones.py          # Phone listing
│   │   └── specs.py           # Detailed specs extraction
│   ├── prices/                # Marketplace price scrapers
│   │   ├── base.py            # Base Playwright scraper
│   │   ├── amazon.py          # Amazon.eg scraper
│   │   ├── jumia.py           # Jumia scraper
│   │   └── noon.py            # Noon scraper
│   ├── specs_pipeline_new.py  # Specs orchestrator
│   └── price_pipeline.py      # Price orchestrator
├── engine/
│   ├── matcher.py             # Fuzzy matching logic
│   ├── validator.py           # Validation rules
│   └── normalizer.py          # Brand/model normalization
├── data/
│   ├── phones_specs.json      # Generated specs
│   ├── phone_variants.json    # Generated variants
│   ├── prices.json            # Latest prices
│   ├── scrape_errors.json     # Error logs
│   └── history/               # Price history
├── docs/
│   ├── index.html             # Frontend
│   ├── specs.json             # Public specs API
│   └── prices.json            # Public prices API
└── requirements.txt           # Python dependencies
```

## 🚀 Deployment

1. **Fork this repository**
2. **Enable GitHub Actions** (Settings → Actions → Allow all actions)
3. **Enable GitHub Pages** (Settings → Pages → Source: Deploy from branch → Branch: main → Folder: /docs)
4. **Wait for workflows to run** (or trigger manually: Actions → Run workflow)
5. **Access your site** at `https://[username].github.io/egypt-phone-prices/`

### Manual Workflow Triggers

- Go to **Actions** tab
- Select **Update Phone Specs** or **Update Prices**
- Click **Run workflow**
- Choose branch: `main`
- Click **Run workflow**

## 📜 License

MIT License

## 🤝 Contributing

Contributions welcome! Please:

1. Test changes locally before submitting PR
2. Follow existing code style
3. Add error handling for new scrapers
4. Update documentation for new features

## ⚠️ Disclaimer

This project is for educational purposes. Please respect:
- Website Terms of Service
- robots.txt files
- Rate limiting policies
- Copyright and intellectual property laws

The authors are not responsible for misuse of this software.
