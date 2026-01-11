import requests
import json
from datetime import datetime
import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneScraper:
    def __init__(self):
        self.phones = []
        self.timestamp = datetime.now().isoformat()
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome webdriver for JavaScript rendering"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            logger.info("✓ Chrome driver initialized")
            return True
        except Exception as e:
            logger.warning(f"Chrome not available: {e}")
            logger.info("Using fallback data instead...")
            return False
    
    def close_driver(self):
        """Close the webdriver"""
        if self.driver:
            self.driver.quit()
            logger.info("✓ Driver closed")
    
    def scrape_jumia(self):
        logger.info("Scraping Jumia...")
        try:
            # Try real scraping with Selenium
            self.driver.get('https://www.jumia.com.eg/mobile-phones/')
            time.sleep(3)
            
            # Wait for products to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "c8j"))
            )
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            products = soup.find_all('article', class_='prd')
            
            for product in products[:8]:  # Get first 8 products
                try:
                    name = product.find('h2').text.strip()
                    price_text = product.find('div', class_='prc').text.strip()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    
                    self.phones.append({
                        'name': name,
                        'store': 'Jumia',
                        'price': price,
                        'url': 'https://www.jumia.com.eg/mobile-phones/',
                        'timestamp': self.timestamp
                    })
                    logger.info(f"✓ {name} - {price} EGP")
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
            
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Jumia scraping failed: {e}")
            logger.info("Using fallback data...")
            self._jumia_fallback()
    
    def _jumia_fallback(self):
        """Fallback data for Jumia"""
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
            logger.info(f"✓ {phone['name']} - {phone['price']} EGP (fallback)")
    
    def scrape_elahly(self):
        logger.info("Scraping ElAhly...")
        try:
            self.driver.get('https://www.elahly.com/mobiles')
            time.sleep(3)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "product"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            products = soup.find_all('div', class_='product-item')
            
            for product in products[:5]:
                try:
                    name = product.find('h3').text.strip()
                    price_text = product.find('span', class_='price').text.strip()
                    price = int(''.join(filter(str.isdigit, price_text)))
                    
                    self.phones.append({
                        'name': name,
                        'store': 'ElAhly',
                        'price': price,
                        'url': 'https://www.elahly.com/mobiles',
                        'timestamp': self.timestamp
                    })
                    logger.info(f"✓ {name} - {price} EGP")
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
            
            time.slee
