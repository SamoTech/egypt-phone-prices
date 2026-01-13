"""
Amazon Egypt Price Scraper
Scrapes phone prices and availability from Amazon Egypt (amazon.eg)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Dict, Optional
import json
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmazonEGScraper:
    """Scraper for Amazon Egypt phone prices"""
    
    BASE_URL = "https://www.amazon.eg"
    SEARCH_URL = f"{BASE_URL}/s"
    
    # Headers to mimic a real browser request
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    def __init__(self, timeout: int = 10):
        """Initialize the scraper with configuration"""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def search_phones(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search for phones on Amazon Egypt
        
        Args:
            query: Search query (e.g., "iPhone 15", "Samsung Galaxy S24")
            max_results: Maximum number of results to return
            
        Returns:
            List of phone listings with price and availability info
        """
        try:
            params = {
                'k': query,
                'i': 'electronics'
            }
            
            logger.info(f"Searching Amazon Egypt for: {query}")
            response = self.session.get(
                self.SEARCH_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            phones = self._parse_search_results(soup, max_results)
            
            logger.info(f"Found {len(phones)} phones for query: {query}")
            return phones
            
        except requests.RequestException as e:
            logger.error(f"Error searching phones: {e}")
            return []
    
    def get_phone_details(self, asin: str) -> Optional[Dict]:
        """
        Get detailed information about a specific phone
        
        Args:
            asin: Amazon Standard Identification Number
            
        Returns:
            Dictionary with detailed phone information
        """
        try:
            url = f"{self.BASE_URL}/dp/{asin}"
            logger.info(f"Fetching phone details for ASIN: {asin}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            phone_details = self._parse_product_page(soup, asin)
            
            return phone_details
            
        except requests.RequestException as e:
            logger.error(f"Error fetching phone details for {asin}: {e}")
            return None
    
    def _parse_search_results(self, soup: BeautifulSoup, max_results: int) -> List[Dict]:
        """Parse search results from the soup object"""
        phones = []
        
        # Find all product containers (Amazon uses div with data-component-type="s-search-result")
        product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for container in product_containers[:max_results]:
            try:
                phone = self._extract_product_info(container)
                if phone:
                    phones.append(phone)
            except Exception as e:
                logger.warning(f"Error parsing product container: {e}")
                continue
        
        return phones
    
    def _extract_product_info(self, container) -> Optional[Dict]:
        """Extract product information from a container element"""
        try:
            # Extract product title
            title_elem = container.find('h2', {'class': 'a-size-mini'})
            if not title_elem:
                title_elem = container.find('span', {'class': 'a-size-base-plus'})
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Extract ASIN from the data-asin attribute
            asin = container.get('data-asin')
            
            # Extract price
            price_elem = container.find('span', {'class': 'a-price-whole'})
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Remove currency symbol and extract number
                price = self._extract_price(price_text)
            
            # Extract rating
            rating = None
            stars_elem = container.find('span', {'class': 'a-icon-star-small'})
            if stars_elem:
                rating_text = stars_elem.get_text(strip=True)
                rating = self._extract_rating(rating_text)
            
            # Check availability
            availability_elem = container.find('span', {'class': 'a-size-base'})
            in_stock = True
            if availability_elem:
                availability_text = availability_elem.get_text(strip=True).lower()
                in_stock = 'out of stock' not in availability_text
            
            # Extract product URL
            link_elem = container.find('a', {'class': 'a-link-normal'})
            url = None
            if link_elem:
                url = link_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = self.BASE_URL + url
            
            return {
                'title': title,
                'asin': asin,
                'price_egp': price,
                'rating': rating,
                'in_stock': in_stock,
                'url': url,
                'source': 'Amazon Egypt',
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error extracting product info: {e}")
            return None
    
    def _parse_product_page(self, soup: BeautifulSoup, asin: str) -> Optional[Dict]:
        """Parse detailed product page"""
        try:
            # Extract title
            title_elem = soup.find('h1', {'class': 'product-title'})
            if not title_elem:
                title_elem = soup.find('span', {'id': 'productTitle'})
            
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract price
            price = None
            price_elem = soup.find('span', {'class': 'a-price-whole'})
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._extract_price(price_text)
            
            # Extract rating
            rating = None
            rating_elem = soup.find('span', {'class': 'a-icon-star'})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating = self._extract_rating(rating_text)
            
            # Extract availability
            availability = "Unknown"
            avail_elem = soup.find('span', {'class': 'availability'})
            if avail_elem:
                availability = avail_elem.get_text(strip=True)
            
            # Extract specifications
            specs = {}
            spec_table = soup.find('table', {'class': 'a-keyvalue'})
            if spec_table:
                for row in spec_table.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) == 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(strip=True)
                        specs[key] = value
            
            return {
                'asin': asin,
                'title': title,
                'price_egp': price,
                'rating': rating,
                'availability': availability,
                'specifications': specs,
                'source': 'Amazon Egypt',
                'url': f"{self.BASE_URL}/dp/{asin}",
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing product page: {e}")
            return None
    
    @staticmethod
    def _extract_price(price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        try:
            # Remove currency symbols and whitespace
            price_text = price_text.replace('ج.م', '').replace('EGP', '').strip()
            # Remove commas used in large numbers
            price_text = price_text.replace(',', '')
            return float(price_text)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def _extract_rating(rating_text: str) -> Optional[float]:
        """Extract numeric rating from text"""
        try:
            # Rating is usually in format "4.5 out of 5"
            rating_value = rating_text.split()[0]
            return float(rating_value)
        except (ValueError, IndexError):
            return None
    
    def scrape_top_phones(self, queries: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Scrape prices for popular phone models
        
        Args:
            queries: List of phone models to search for
            
        Returns:
            Dictionary with search queries as keys and phone listings as values
        """
        if queries is None:
            queries = [
                "iPhone 15 Pro Max",
                "Samsung Galaxy S24",
                "Xiaomi 14",
                "OnePlus 12",
                "Google Pixel 8 Pro",
                "Realme 12",
                "Oppo A80",
                "Vivo Y36"
            ]
        
        results = {}
        
        for query in queries:
            phones = self.search_phones(query, max_results=10)
            results[query] = phones
        
        return results
    
    def export_to_json(self, data: Dict, filename: str = "amazon_eg_phones.json") -> bool:
        """Export scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data exported to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False


def main():
    """Example usage of the AmazonEGScraper"""
    scraper = AmazonEGScraper()
    
    # Search for a specific phone
    phones = scraper.search_phones("iPhone 15", max_results=5)
    
    print("\n=== Amazon Egypt Phone Scraper Results ===\n")
    for phone in phones:
        print(f"Title: {phone['title']}")
        print(f"Price: {phone['price_egp']} EGP")
        print(f"Rating: {phone['rating']}")
        print(f"In Stock: {phone['in_stock']}")
        print(f"URL: {phone['url']}")
        print("-" * 50)
    
    # Scrape top phones
    print("\nScraping popular phone models...")
    results = scraper.scrape_top_phones()
    
    # Export results
    scraper.export_to_json(results)
    print("Results exported to amazon_eg_phones.json")


if __name__ == "__main__":
    main()
