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
            # بيانات تجريبية من Jumia
            sample_phones = [
                {'name': 'iPhone 15 Pro Max', 'price': 48500},
                {'name': 'Samsung Galaxy S24 Ultra', 'price': 42000},
                {'name': 'Google Pixel 8 Pro', 'price': 38000},
                {'name': 'iPhone 15', 'price': 32000},
                {'name': 'Samsung Galaxy S24', 'price': 28000},
                {'name': 'Oppo A17', 'price': 8500},
                {'name': 'Xiaomi Redmi Note 13', 'price': 7500},
                {'name': 'OnePlus 12', 'price': 25000},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'Jumia',
                    'price': phone['price'],
                    'url': 'https://www.jumia.com.eg/mobile-phones/',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def scrape_elahly(self):
        logger.info("Scraping ElAhly...")
        try:
            sample_phones = [
                {'name': 'iPhone 15 Pro', 'price': 45000},
                {'name': 'Samsung S24 Ultra', 'price': 38000},
                {'name': 'iPhone 15', 'price': 31000},
                {'name': 'Samsung S24', 'price': 27000},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'ElAhly',
                    'price': phone['price'],
                    'url': 'https://www.elahly.com',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def scrape_carrefour(self):
        logger.info("Scraping Carrefour...")
        try:
            sample_phones = [
                {'name': 'iPhone 15', 'price': 33000},
                {'name': 'Samsung Galaxy S24', 'price': 29000},
            ]
            
            for phone in sample_phones:
                self.phones.append({
                    'name': phone['name'],
                    'store': 'Carrefour',
                    'price': phone['price'],
                    'url': 'https://www.carrefour.com.eg',
                    'timestamp': self.timestamp
                })
                logger.info(f"✓ {phone['name']} - {phone['price']} EGP")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def run_all(self):
        logger.info("="*50)
        logger.info("Starting scraper...")
        logger.info("="*50)
        self.scrape_jumia()
        self.scrape_elahly()
        self.scrape_carrefour()
        logger.info(f"✓ Collected {len(self.phones)} phones")
        logger.info("="*50)
    
    def save(self):
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/phones_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.phones, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Saved to data/phones_data.json")
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == '__main__':
    scraper = PhoneScraper()
    scraper.run_all()
    scraper.save()
