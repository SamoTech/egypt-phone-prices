# Egyptian Phone Price Comparison

Automated system to scrape phone prices from Amazon.eg, Jumia, and Noon, then display them in a web interface hosted on GitHub Pages.

## How it works

- data/phones.csv contains the list of phones and specs.
- scraper.py updates prices from online stores.
- GitHub Actions runs the scraper every 6 hours and regenerates docs/phones.json.
- docs/index.html reads phones.json and shows search, filters, and comparison.

## How to use

1. Fork or clone this repo.
2. Go to Settings -> Pages.
3. Source: Deploy from branch
4. Branch: main, folder: /docs.
5. Wait a few minutes, then open the GitHub Pages URL.
6. Prices will refresh automatically several times per day.

## Project structure

- data/phones.csv: Phone database with prices
- data/stores.json: Store metadata
- scrapers/: Scraping modules (amazon.py, jumia.py, noon.py, stores.py)
- utils/: Utilities (price_calculator.py, error_handler.py, notifier.py)
- docs/index.html: Website
- .github/workflows/update-prices.yml: GitHub Actions automation
- scraper.py: Main scraping script

## Contributing

To add more phones: edit data/phones.csv and add a new row.

To add more stores: add new columns to data/phones.csv, update data/stores.json, and implement a scraper in scrapers/stores.py.
