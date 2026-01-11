import random
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118 Safari/537.36",
]


def _session():
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        }
    )
    return s


def scrape_noon_prices(brand, model):
    session = _session()
    query = f"{brand} {model}"
    q = urllib.parse.quote_plus(query)
    url = f"https://www.noon.com/egypt-en/search/?q={q}"

    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            return {}

        soup = BeautifulSoup(resp.text, "html.parser")
        result = soup.select_one("div.productContainer, div.product")
        if not result:
            return {}

        price_el = result.select_one("[data-qa='productPrice'], .price")
        link = result.select_one("a")

        if not price_el or not link:
            return {}

        price_text = price_el.get_text(strip=True).replace("EGP", "").replace(",", "")
        try:
            price = float(price_text)
        except ValueError:
            price = price_text

        product_url = "https://www.noon.com" + link.get("href")

        time.sleep(1.5)

        return {
            "noon_eg": price,
            "noon_eg_url": product_url,
        }
    except Exception as e:
        print(f"Noon scrape error: {e}")
        return {}
