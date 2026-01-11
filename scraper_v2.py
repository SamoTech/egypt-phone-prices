
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.phones = []
        self.timestamp = datetime.now().isoformat()
        
    def scrape_jumia(self):
        """Scrape phones from Jumia Egypt"""
        logger.info("Scraping Jumia...")
        try:
            # Page 1
            url = "https://www.jumia.com.eg/mlp/electronics/phones/"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('article', class_='prd')
            logger.info(f"Found {len(products)} products on Jumia")
            
            for product in products[:30]:
                try:
                    name_tag = product.find('h2')
                    price_tag = product.find('div', class_='prc')
                    link_tag = product.find('a')
                    
                    if name_tag and price_tag and link_tag:
                        name = name_tag.get_text(strip=True)
                        price_text = price_tag.get_text(strip=True)
                        link = link_tag.get('href', '')
                        
                        price = self._extract_price(price_text)
                        
                        if price > 0 and name:
                            phone_data = {
                                'timestamp': self.timestamp,
                                'store': 'Jumia',
                                'model': name,
                                'price_egp': price,
                                'url': link
                            }
                            self.phones.append(phone_data)
                            logger.info(f"✓ Jumia: {name} - {price} EGP")
                except Exception as e:
                    logger.debug(f"Error parsing Jumia product: {e}")
                    continue
                    
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error scraping Jumia: {e}")
    
    def scrape_noon(self):
        """Scrape phones from Noon Egypt"""
        logger.info("Scraping Noon...")
        try:
            url = "https://www.noon.com/egypt-en/electronics/mobile-phones-1/"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Noon uses different structure - adjust selector as needed
            products = soup.find_all('div', attrs={'class': 'productCard'})
            logger.info(f"Found {len(products)} products on Noon")
            
            for product in products[:30]:
                try:
                    name_tag = product.find('span', class_='productName')
                    price_tag = product.find('span', class_='priceText')
                    link_tag = product.find('a')
                    
                    if name_tag and price_tag:
                        name = name_tag.get_text(strip=True)
                        price_text = price_tag.get_text(strip=True)
                        link = link_tag.get('href', '') if link_tag else ''
                        
                        price = self._extract_price(price_text)
                        
                        if price > 0 and name:
                            phone_data = {
                                'timestamp': self.timestamp,
                                'store': 'Noon',
                                'model': name,
                                'price_egp': price,
                                'url': link
                            }
                            self.phones.append(phone_data)
                            logger.info(f"✓ Noon: {name} - {price} EGP")
                except Exception as e:
                    logger.debug(f"Error parsing Noon product: {e}")
                    continue
                    
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error scraping Noon: {e}")
    
    def scrape_elahly(self):
        """Scrape phones from ElAhly Stores"""
        logger.info("Scraping ElAhly...")
        try:
            url = "https://www.elahly.com/en/mobile-phones/"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('div', class_='product-item')
            logger.info(f"Found {len(products)} products on ElAhly")
            
            for product in products[:30]:
                try:
                    name_tag = product.find('h2', class_='product-name')
                    price_tag = product.find('span', class_='product-price')
                    link_tag = product.find('a')
                    
                    if name_tag and price_tag:
                        name = name_tag.get_text(strip=True)
                        price_text = price_tag.get_text(strip=True)
                        link = link_tag.get('href', '') if link_tag else ''
                        
                        price = self._extract_price(price_text)
                        
                        if price > 0 and name:
                            phone_data = {
                                'timestamp': self.timestamp,
                                'store': 'ElAhly',
                                'model': name,
                                'price_egp': price,
                                'url': link
                            }
                            self.phones.append(phone_data)
                            logger.info(f"✓ ElAhly: {name} - {price} EGP")
                except Exception as e:
                    logger.debug(f"Error parsing ElAhly product: {e}")
                    continue
                    
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error scraping ElAhly: {e}")
    
    def scrape_carrefour(self):
        """Scrape phones from Carrefour Egypt"""
        logger.info("Scraping Carrefour...")
        try:
            url = "https://www.carrefouregypt.com/mafegy/en/c/ELECTRONICS-L19/MOBILE-PHONES-L2113"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('div', class_='product-grid-item')
            logger.info(f"Found {len(products)} products on Carrefour")
            
            for product in products[:30]:
                try:
                    name_tag = product.find('h3')
                    price_tag = product.find('span', class_='price')
                    link_tag = product.find('a')
                    
                    if name_tag and price_tag:
                        name = name_tag.get_text(strip=True)
                        price_text = price_tag.get_text(strip=True)
                        link = link_tag.get('href', '') if link_tag else ''
                        
                        price = self._extract_price(price_text)
                        
                        if price > 0 and name:
                            phone_data = {
                                'timestamp': self.timestamp,
                                'store': 'Carrefour',
                                'model': name,
                                'price_egp': price,
                                'url': link
                            }
                            self.phones.append(phone_data)
                            logger.info(f"✓ Carrefour: {name} - {price} EGP")
                except Exception as e:
                    logger.debug(f"Error parsing Carrefour product: {e}")
                    continue
                    
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error scraping Carrefour: {e}")
    
    def scrape_sharawy(self):
        """Scrape phones from Sharawy"""
        logger.info("Scraping Sharawy...")
        try:
            url = "https://www.sharawy.com/en/phones"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            products = soup.find_all('div', class_='product')
            logger.info(f"Found {len(products)} products on Sharawy")
            
            for product in products[:30]:
                try:
                    name_tag = product.find('h4')
                    price_tag = product.find('span', class_='price')
                    link_tag = product.find('a')
                    
                    if name_tag and price_tag:
                        name = name_tag.get_text(strip=True)
                        price_text = price_tag.get_text(strip=True)
                        link = link_tag.get('href', '') if link_tag else ''
                        
                        price = self._extract_price(price_text)
                        
                        if price > 0 and name:
                            phone_data = {
                                'timestamp': self.timestamp,
                                'store': 'Sharawy',
                                'model': name,
                                'price_egp': price,
                                'url': link
                            }
                            self.phones.append(phone_data)
                            logger.info(f"✓ Sharawy: {name} - {price} EGP")
                except Exception as e:
                    logger.debug(f"Error parsing Sharawy product: {e}")
                    continue
                    
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error scraping Sharawy: {e}")
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        import re
        # Remove common currency symbols and text
        cleaned = price_text.replace('EGP', '').replace('LE', '').replace('E£', '').strip()
        # Find number pattern
        match = re.search(r'[\d,]+(?:\.\d+)?', cleaned.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except:
                return 0
        return 0
    
    def run_all_scrapers(self):
        """Run all scrapers"""
        logger.info("="*50)
        logger.info("Starting multi-store scrape...")
        logger.info("="*50)
        
        self.scrape_jumia()
        self.scrape_noon()
        self.scrape_elahly()
        self.scrape_carrefour()
        self.scrape_sharawy()
        
        logger.info("="*50)
        logger.info(f"✓ Collected {len(self.phones)} total phones from all stores")
        logger.info("="*50)
        return self.phones
    
    def save_to_json(self, filename: str = 'data/phones_data.json'):
        """Save collected data to JSON"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.phones, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Saved {len(self.phones)} records to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def generate_report(self, filename: str = 'docs/price_report.md'):
        """Generate markdown report"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            report = f"""# Egypt Phone Prices Report
**Generated:** {self.timestamp}

## Summary
- **Total Records:** {len(self.phones)}
- **Stores Covered:** {len(set(p['store'] for p in self.phones))}
- **Unique Models:** {len(set(p['model'] for p in self.phones))}

## Store Breakdown
"""
            for store in sorted(set(p['store'] for p in self.phones)):
                count = len([p for p in self.phones if p['store'] == store])
                avg_price = sum(p.get('price_egp', 0) for p in self.phones if p['store'] == store) / count if count > 0 else 0
                report += f"\n### {store}\n- **Phones Listed:** {count}\n- **Avg Price:** {avg_price:,.0f} EGP\n"
            
            report += f"\n## Top 10 Lowest Prices\n\n"
            sorted_phones = sorted(self.phones, key=lambda x: x.get('price_egp', float('inf')))
            
            for idx, phone in enumerate(sorted_phones[:10], 1):
                report += f"{idx}. **{phone['model']}** ({phone['store']}) - **EGP {phone.get('price_egp', 'N/A'):,.0f}**\n"
            
            report += f"\n## Top 10 Highest Prices\n\n"
            for idx, phone in enumerate(sorted_phones[-10:], 1):
                report += f"{idx}. **{phone['model']}** ({phone['store']}) - **EGP {phone.get('price_egp', 'N/A'):,.0f}**\n"
            
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
