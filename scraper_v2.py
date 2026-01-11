import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.phones = []
        self.timestamp = datetime.now().isoformat()
        
    def scrape_jumia(self):
        logger.info("Scraping Jumia...")
        try:
            url = "https://www.jumia.com.eg/mlp/electronics/phones/"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('article', {'data-sku': True})
            logger.info(f"Found {len(products)} products on Jumia")
            
            for product in products[:20]:
                try:
                    name = product.find('h2')
                    price = product.find('div', class_='prc')
                    
                    if name and price:
                        phone_data = {
                            'timestamp': self.timestamp,
                            'store': 'Jumia',
                            'model': name.get_text(strip=True),
                            'price_egp': float(price.get_text(strip=True).replace('EGP', '').replace(',', '').strip()),
                            'url': product.find('a')['href'] if product.find('a') else ''
                        }
                        self.phones.append(phone_data)
                        logger.info(f"✓ {phone_data['model']} - {phone_data['price_egp']} EGP")
                except Exception as e:
                    continue
                    
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error scraping Jumia: {e}")
    
    def scrape_noon(self):
        logger.info("Scraping Noon...")
        try:
            url = "https://www.noon.com/egypt-en/electronics/mobile-phones/"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('div', {'data-productid': True})
            logger.info(f"Found {len(products)} products on Noon")
            
            for product in products[:20]:
                try:
                    name = product.find('span', class_='productName')
                    price = product.find('span', class_='priceText')
                    
                    if name and price:
                        phone_data = {
                            'timestamp': self.timestamp,
                            'store': 'Noon',
                            'model': name.get_text(strip=True),
                            'price_egp': float(price.get_text(strip=True).replace('E£', '').replace(',', '').strip()),
                            'url': product.find('a')['href'] if product.find('a') else ''
                        }
                        self.phones.append(phone_data)
                        logger.info(f"✓ {phone_data['model']} - {phone_data['price_egp']} EGP")
                except Exception as e:
                    continue
                    
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error scraping Noon: {e}")
    
    def run_all_scrapers(self):
        logger.info("="*50)
        logger.info("Starting multi-store scrape...")
        logger.info("="*50)
        
        self.scrape_jumia()
        self.scrape_noon()
        
        logger.info("="*50)
        logger.info(f"✓ Collected {len(self.phones)} total phones")
        logger.info("="*50)
        return self.phones
    
    def save_to_json(self, filename='data/phones_data.json'):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.phones, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Saved {len(self.phones)} records to {filename}")
        except Exception as e:
            logger.error(f"Error saving: {e}")
    
    def generate_report(self, filename='docs/price_report.md'):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            report = f"# Egypt Phone Prices Report\n"
            report += f"**Generated:** {self.timestamp}\n\n"
            report += f"## Summary\n"
            report += f"- **Total Records:** {len(self.phones)}\n"
            report += f"- **Stores:** {len(set(p['store'] for p in self.phones))}\n\n"
            
            for store in set(p['store'] for p in self.phones):
                count = len([p for p in self.phones if p['store'] == store])
                report += f"### {store}\n**Phones Listed:** {count}\n\n"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"✓ Report saved to {filename}")
        except Exception as e:
            logger.error(f"Error generating report: {e}")

if __name__ == '__main__':
    scraper = PhoneScraper()
    scraper.run_all_scrapers()
    scraper.save_to_json()
    scraper.generate_report()
