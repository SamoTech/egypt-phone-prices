import random
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118 Safari/537.36",
]


def _make_session():
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        }
    )
    return s


def scrape_amazon_prices(brand, model):
    session = _make_session()
    query = f"{brand} {model} smartphone"
    q = urllib.parse.quote_plus(query)
    url = f"https://www.amazon.eg/s?k={q}"

    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            return {}

        soup = BeautifulSoup(resp.text, "html.parser")
        result = soup.select_one("div.s-main-slot div[data-component-type='s-search-result']")
        if not result:
            return {}

        price_whole = result.select_one("span.a-price-whole")
        price_fraction = result.select_one("span.a-price-fraction")
        link = result.select_one("a.a-link-normal.s-no-outline, a.a-link-normal.a-text-normal")

        if not price_whole or not link:
            return {}

        price_str = price_whole.get_text(strip=True).replace(",", "")
        if price_fraction:
            price_str += "." + price_fraction.get_text(strip=True)

        try:
            price = float(price_str)
        except ValueError:
            price = price_str

        product_url = "https://www.amazon.eg" + link.get("href")

        time.sleep(1.5)

        return {
            "amazon_eg": price,
            "amazon_eg_url": product_url,
        }
    except Exception as e:
        print(f"Amazon scrape error: {e}")
        return {}
