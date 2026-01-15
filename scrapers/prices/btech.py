import requests
from bs4 import BeautifulSoup

class BTechPriceScraper:
    def __init__(self):
        self.base_url = 'https://www.btech.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    def fetch_product_page(self, product_id):
        url = f'{self.base_url}/product/{product_id}'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text

    def parse_product_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        product_name = soup.find('h1', class_='product-title').text.strip()
        product_price = soup.find('span', class_='price').text.strip()
        return {
            'name': product_name,
            'price': product_price
        }

    def get_price(self, product_id):
        html = self.fetch_product_page(product_id)
        return self.parse_product_data(html)

# Example usage
if __name__ == '__main__':
    scraper = BTechPriceScraper()
    product_data = scraper.get_price('example-product-id')
    print(product_data)