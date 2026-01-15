# Egyptian Phone Price & Specs Intelligence Platform

**AI-assisted search intelligence engine** that discovers phones and tracks Egyptian market prices using pattern extraction and heuristic analysis.

## 🚀 Core Philosophy

**🚫 NO traditional web scraping** (no BeautifulSoup, Selenium, Playwright)  
**✅ AI-assisted search + text extraction + confidence scoring**

This system behaves like a **search + intelligence engine**, not a crawler.

---

## 🆕 What's New in This Version

### Jina AI Search Integration
- ✅ **Jina AI Search API** - Free tier available, optional authentication for better results
- ✅ **API key authentication** - Use `JINA_API_KEY` environment variable for authenticated requests
- ✅ **Better reliability** - No more DuckDuckGo failures
- ✅ **Clean content extraction** - Markdown format for better parsing
- ✅ **Retry logic** - Exponential backoff for transient errors
- ✅ **DuckDuckGo fallback** - Kept as backup option

### Real Search Integration
- ✅ **Multi-store discovery** - Amazon, Noon, Jumia, B.TECH, 2B
- ✅ **Intelligent parsing** - Regex-based price extraction from search snippets
- ✅ **No more simulated data** - Real search results from actual queries

### Link Validation
- ✅ **Automated validation** - Weekly checks for dead links via GitHub Actions
- ✅ **404 removal** - Automatically removes broken product URLs
- ✅ **Quality assurance** - Only shows valid, working links with timestamps

### Advanced Filters
- ✅ **Comprehensive search** - Filter by brand, price, storage, confidence
- ✅ **Smart sorting** - Price, confidence, brand alphabetically
- ✅ **Instant results** - Client-side filtering for speed
- ✅ **Extensible architecture** - Easy to add new filter types

---

## 🏗️ Architecture

### System Components

```
engine/
  discovery/                # NEW: Real search integration
    jina_search_engine.py   # Jina AI search wrapper (optional authentication)
    search_engine.py        # DuckDuckGo search wrapper (fallback)
    result_parser.py        # Extract prices from search results
  pipelines/                # NEW: Validation pipelines
    validation_pipeline.py  # Link validation and 404 removal
  search_intents.py         # Generates search queries for price discovery
  extractor.py              # Text-based extraction (regex, keywords, heuristics)
  matcher.py                # Semantic + fuzzy matching (RapidFuzz)
  validator.py              # Reject false positives (accessories, refurbs)
  scorer.py                 # Confidence scoring (rule-based, no LLM)
  normalizer.py             # Brand/model normalization
  specs_discovery.py        # Specs inference pipeline
  price_discovery.py        # Price discovery pipeline (now with real search!)
```

---

## 📊 How It Works

### Specs Discovery (Weekly - Sundays 2 AM UTC)

- Uses curated seed list of popular phones in Egyptian market
- Applies heuristic rules and brand-specific patterns
- Generates normalized specs: brand, model, year, chipset, display, battery
- Creates storage/RAM variant combinations
- **Output:** `phones_specs.json`, `phone_variants.json`

### Price Discovery (Every 6 Hours)

**Flow for each phone variant:**

1. **Generate search intents**
   - "Samsung Galaxy S23 256GB price Egypt"
   - "Galaxy S23 سعر مصر"

2. **Extract from text** using regex patterns:
   - Prices (e.g., `\d{4,6}\s*EGP`)
   - Storage/RAM capacities
   - Store names
   - Product conditions

3. **Validate data:**
   - Reject accessories (cases, chargers)
   - Reject refurbished/used items
   - Validate variant matches
   - Check price reasonableness

4. **Calculate confidence scores:**
   ```
   +0.4 if trusted store (Amazon, Noon, Jumia)
   +0.3 if storage variant matches exactly
   +0.2 if price from multiple sources
   +0.1 if "official" or "warranty"
   -0.5 if accessory detected
   -0.3 if refurbished/used
   -0.4 if price outlier
   ```

5. **Output with transparency:**
   - All offers include confidence scores
   - Timestamps for last verification
   - Price ranges, not absolute values

---

## 🎯 Confidence Scoring

All price data includes transparent confidence scores:

- **🟢 High (0.75-1.0):** Trusted store, exact match, multiple sources
- **🟡 Medium (0.50-0.74):** Good match, single source, some uncertainty
- **🔴 Low (0.0-0.49):** Weak match, outlier price, questionable source

**Scoring is rule-based and transparent** - no black-box AI models.

---

## 🚀 Automated Workflows

- **Specs Update:** Weekly (Sundays 2 AM UTC)
- **Price Update:** Every 6 hours
- **Link Validation:** Weekly (Sundays 3 AM UTC) - **NEW!**
- **Deployment:** Automatic to GitHub Pages
- **Fault Tolerance:** Keeps last valid data on failures

---

## 📈 Static Frontend

Live at: `https://[username].github.io/egypt-phone-prices/`

**Features:**
- ✅ Confidence indicators (🟢🟡🔴)
- ✅ "Estimated Market Price" labeling
- ✅ Last verification timestamps
- ✅ Price ranges with transparency
- ✅ Filter by brand, price, store
- ✅ Sort by price, confidence, availability
- ✅ Mobile-responsive, vanilla JS

**UI Principles:**
- Manages user expectations honestly
- Shows data limitations clearly
- Encourages store verification

---

## 🛠️ Local Development

### Prerequisites

```bash
Python 3.11+
pip install -r requirements.txt
```

### Environment Variables (Optional)

```bash
# Optional: Jina AI API key for better search quality
export JINA_API_KEY="your_jina_api_key_here"
```

The system works without an API key (using Jina AI's free tier), but providing an API key can improve search quality and reliability.

To obtain a Jina AI API key:
1. Visit [Jina AI](https://jina.ai/)
2. Sign up for an account
3. Generate an API key from your dashboard
4. Set it as an environment variable or GitHub secret

### Run Specs Discovery

```bash
# Test mode (limited phones)
python -m engine.specs_discovery --test

# Full run
python -m engine.specs_discovery --min-year 2023
```

### Run Price Discovery

```bash
# Test mode (5 variants)
python -m engine.price_discovery --test

# Full run
python -m engine.price_discovery
```

### Test Engine Modules

```python
from engine import (
    generate_search_queries,
    extract_prices_from_text,
    fuzzy_match_phone,
    calculate_confidence_score
)

# Generate search queries
queries = generate_search_queries("Samsung", "Galaxy S23", "256GB")
print(queries)

# Extract prices
text = "Samsung Galaxy S23 256GB costs 32,999 EGP"
prices = extract_prices_from_text(text)
print(prices)

# Fuzzy matching
result = {"title": "Samsung Galaxy S23 256GB", "description": ""}
phone = {"brand": "Samsung", "model": "Galaxy S23", "storage": "256GB"}
score = fuzzy_match_phone(result, phone)
print(f"Match confidence: {score:.2f}")
```

---

## 📦 Dependencies

```txt
# Core (minimal)
requests>=2.31.0
rapidfuzz>=3.6.0
tenacity==8.2.3
python-dateutil==2.8.2
pydantic==2.5.0
# Jina AI API used directly via requests (optional API key for better results)
```

**What's NOT included:**
- ❌ beautifulsoup4 (REMOVED - no DOM parsing)
- ❌ selenium (REMOVED - no browser automation)
- ❌ playwright (REMOVED - no browser automation)
- ❌ openai / anthropic (no LLM APIs)
- ❌ duckduckgo-search (moved to optional fallback)

**What's NEW:**
- ✅ Jina AI Search (free API via requests, no dedicated library needed)
- ✅ Retry logic with tenacity

---

## 🚫 Constraints & Design Decisions

### Forbidden:
- Traditional web scraping with DOM parsers
- Browser automation tools
- Paid APIs or LLM services
- CAPTCHA bypassing

### Allowed:
- `requests` library for text fetching
- Regex and keyword extraction
- RapidFuzz for fuzzy matching
- Local heuristic rules
- GitHub Actions + Pages only

### Why This Approach?

✅ **More resilient** than brittle scrapers  
✅ **More legal** (no ToS violations)  
✅ **More scalable** on free infrastructure  
✅ **More maintainable** (rules over selectors)  
✅ **More honest** (confidence scores)

---

## ⚠️ Limitations & Honest Disclosure

### What This System Does:
- ✅ Provides market intelligence estimates
- ✅ Shows price ranges and trends
- ✅ Offers confidence-scored data
- ✅ Updates automatically

### What This System Does NOT Do:
- ❌ Guarantee real-time accuracy
- ❌ Verify stock availability
- ❌ Confirm seller legitimacy
- ❌ Replace direct verification

**Always verify prices with stores before purchasing.**

---

## 🚀 Deployment

1. Fork this repository
2. Enable GitHub Actions
3. (Optional but recommended) Add `JINA_API_KEY` secret:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `JINA_API_KEY`
   - Value: Your Jina AI API key
4. Enable GitHub Pages (Settings → Pages → /docs folder)
5. Trigger workflows manually or wait for schedule
6. Access at `https://[username].github.io/egypt-phone-prices/`

---

## 🔧 Configuration

### Jina AI API Key (Optional)

The system uses Jina AI for web search. While it works without authentication, providing an API key improves results:

**For Local Development:**
```bash
export JINA_API_KEY="your_api_key_here"
python -m engine.price_discovery
```

**For GitHub Actions:**
Add `JINA_API_KEY` as a repository secret (Settings → Secrets and variables → Actions).

The workflows in `.github/workflows/` are already configured to use this secret.

### Add New Phone

Edit `engine/specs_discovery.py`:

```python
seed_phones = [
    {"brand": "Samsung", "model": "Galaxy S25", "year": 2025},
]
```

### Adjust Scoring

Edit `engine/scorer.py` to modify confidence rules.

### Change Frequency

Edit `.github/workflows/update-prices.yml`:

```yaml
schedule:
  - cron: '0 */12 * * *'  # Every 12 hours
```

---

## 📝 Project Structure

```
egypt-phone-prices/
├── engine/               # AI-assisted search intelligence
│   ├── search_intents.py
│   ├── extractor.py
│   ├── matcher.py
│   ├── validator.py
│   ├── scorer.py
│   ├── normalizer.py
│   ├── specs_discovery.py
│   └── price_discovery.py
├── data/                 # Generated data files
├── docs/                 # GitHub Pages frontend
└── .github/workflows/    # Automated pipelines
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Follow AI-assisted architecture (no scraping)
2. Add confidence scoring for new sources
3. Document limitations honestly

---

## 📜 License

MIT License

---

## ⚠️ Disclaimer

This project is for **educational purposes**.

**Data Accuracy:**
- Prices are estimates based on market intelligence
- Confidence scores indicate reliability
- Always verify with stores before purchase

**Ethical Use:**
- Respects website Terms of Service
- Uses only text-based extraction
- No aggressive scraping
- Rate limiting built-in

Authors not responsible for pricing errors or misuse.

---

## 🎓 Methodology

This is a **search engineer's solution**, not a scraper's hack.

**Built with:**
- Pattern extraction and heuristics
- Fuzzy matching algorithms
- Rule-based validation
- Probabilistic confidence scoring

**Result:** Resilient, maintainable, honest, and free.

---

**Questions?** Open an issue or PR!
