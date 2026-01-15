import requests
from bs4 import BeautifulSoup
from base_price_scraper import BasePriceScraper

class BtechEgPriceScraper(BasePriceScraper):
    def __init__(self, url):
        super().__init__()
        self.url = url

    def fetch_data(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            return response.text
        else:
            return None

    def parse_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        prices = []
        for item in soup.select('.price-item'):
            price = item.get_text(strip=True)
            prices.append(price)
        return prices

    def scrape(self):
        html_content = self.fetch_data()
        if html_content:
            return self.parse_data(html_content)
        else:
            return []

# Example usage
if __name__ == "__main__":
    scraper = BtechEgPriceScraper("http://example.com/btech-prices")
    print(scraper.scrape())
