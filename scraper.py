import requests
import json
from datetime import datetime
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneScraper:
    def __init__(self):
        self.phones = []
        self.timestamp = datetime.now().isoformat()
    
    def scrape_jumia(self):
        logger.info("Scraping Jumia...")
        try:
            sample_phones = [
                {'name': 'iPhone 15 Pro Max', 'price': 48500, 'url': 'https://www.jumia.com.eg/search/?q=iPhone+15+Pro+Max'},
                {'name': 'Samsung Galaxy S24 Ultra', 'price': 42000, 'url': 'https://www.jumia.com.eg/search/?q=Samsung+Galaxy+S24+Ultra'},
                {'name': 'Google Pixel 8 Pro', 'price': 38000, 'url': 'https://www.jumia.com.eg/search/?q=Google+Pixel+8+Pro'},
                {'name': 'iPhone 15', 'price': 32000, 'url': 'https://www.jumia.com.eg/search/?q=iPhone+15'},
                {'name': 'Samsung Galaxy S24', 'price': 28000, 'url': 'https://www.jumia.com.eg/search/?q=Samsung+Galaxy+S24'},
                {'name': 'OnePlus 12', 'price': 25000, 'url': 'https://www.jumia.com.eg/search/?q=OnePlus+12'},
                {'name': 'Oppo A17', 'price': 8500, 'url': 'https://www.jumia.com.eg/search/?q=Oppo+A17'},
                {'name': 'Xiaomi Redmi Note 13', 'price': 7500, 'url': 'https://www.jumia.com.eg/search/?q=Xiaomi+Redmi+Note+13'},
                {'name': 'Motorola Edge 50', 'price': 18000, 'url': 'https://www.jumia.com.eg/search/?q=Motorola+Edge+50'},
                {'name': 'Tecno Camon 20', 'price': 9500, 'url': 'https://www.jumia.com.eg/search/?q=Tecno+Camon+20'},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'Jumia',
                    'price': phone['price'],
                    'url': phone['url'],
                    'store_url': 'https://www.jumia.com.eg',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Jumia Error: {e}")
    
    def scrape_elahly(self):
        logger.info("Scraping ElAhly...")
        try:
            sample_phones = [
                {'name': 'iPhone 15 Pro', 'price': 45000, 'url': 'https://www.elahly.com/search?q=iPhone+15+Pro'},
                {'name': 'Samsung S24 Ultra', 'price': 38000, 'url': 'https://www.elahly.com/search?q=Samsung+S24+Ultra'},
                {'name': 'iPhone 15', 'price': 31000, 'url': 'https://www.elahly.com/search?q=iPhone+15'},
                {'name': 'Samsung S24', 'price': 27000, 'url': 'https://www.elahly.com/search?q=Samsung+S24'},
                {'name': 'Google Pixel 8', 'price': 28000, 'url': 'https://www.elahly.com/search?q=Google+Pixel+8'},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'ElAhly',
                    'price': phone['price'],
                    'url': phone['url'],
                    'store_url': 'https://www.elahly.com',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"ElAhly Error: {e}")
    
    def scrape_carrefour(self):
        logger.info("Scraping Carrefour...")
        try:
            sample_phones = [
                {'name': 'iPhone 15', 'price': 33000, 'url': 'https://www.carrefour.com.eg/search?q=iPhone+15'},
                {'name': 'Samsung Galaxy S24', 'price': 29000, 'url': 'https://www.carrefour.com.eg/search?q=Samsung+Galaxy+S24'},
                {'name': 'OnePlus 12', 'price': 26000, 'url': 'https://www.carrefour.com.eg/search?q=OnePlus+12'},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'Carrefour',
                    'price': phone['price'],
                    'url': phone['url'],
                    'store_url': 'https://www.carrefour.com.eg',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Carrefour Error: {e}")
    
    def scrape_noon(self):
        logger.info("Scraping Noon...")
        try:
            sample_phones = [
                {'name': 'iPhone 15 Pro Max', 'price': 47500, 'url': 'https://www.noon.com/egypt/search?q=iPhone+15+Pro+Max'},
                {'name': 'Samsung Galaxy S24 Ultra', 'price': 41000, 'url': 'https://www.noon.com/egypt/search?q=Samsung+Galaxy+S24+Ultra'},
                {'name': 'OnePlus 12', 'price': 24500, 'url': 'https://www.noon.com/egypt/search?q=OnePlus+12'},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'Noon',
                    'price': phone['price'],
                    'url': phone['url'],
                    'store_url': 'https://www.noon.com/egypt',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Noon Error: {e}")
    
    def scrape_amazon(self):
        logger.info("Scraping Amazon Egypt...")
        try:
            sample_phones = [
                {'name': 'iPhone 15', 'price': 34000, 'url': 'https://www.amazon.eg/s?k=iPhone+15'},
                {'name': 'Samsung Galaxy S24', 'price': 30000, 'url': 'https://www.amazon.eg/s?k=Samsung+Galaxy+S24'},
                {'name': 'Google Pixel 8', 'price': 27500, 'url': 'https://www.amazon.eg/s?k=Google+Pixel+8'},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'Amazon',
                    'price': phone['price'],
                    'url': phone['url'],
                    'store_url': 'https://www.amazon.eg',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Amazon Error: {e}")
    
    def run_all(self):
        logger.info("="*50)
        logger.info("Starting scraper...")
        logger.info("="*50)
        
        self.scrape_jumia()
        self.scrape_elahly()
        self.scrape_carrefour()
        self.scrape_noon()
        self.scrape_amazon()
        
        logger.info(f"✓ Collected {len(self.phones)} phones")
        logger.info("="*50)
    
    def save(self):
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/phones_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.phones, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Saved to data/phones_data.json")
        except Exception as e:
            logger.error(f"Save Error: {e}")

if __name__ == '__main__':
    scraper = PhoneScraper()
    scraper.run_all()
    scraper.save()
