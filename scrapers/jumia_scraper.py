"""
Jumia Egypt Price Scraper

This module provides functionality to scrape phone prices and product information
from Jumia Egypt's website. It handles product discovery, price extraction,
availability checking, and data persistence.

Author: SamoTech
Date: 2026-01-13
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class JumiaPhoneProduct:
    """Data class representing a phone product from Jumia Egypt."""
    
    product_id: str
    name: str
    price: float
    currency: str
    original_price: Optional[float]
    discount_percentage: Optional[int]
    rating: Optional[float]
    review_count: int
    availability: str
    url: str
    image_url: Optional[str]
    seller: Optional[str]
    storage: Optional[str]
    color: Optional[str]
    brand: str
    specifications: Dict[str, str]
    scraped_at: str
    
    def to_dict(self) -> Dict:
        """Convert product to dictionary."""
        return asdict(self)


class JumiaEgyptScraper:
    """
    Web scraper for Jumia Egypt phone prices and product information.
    
    This scraper uses both requests and Selenium for comprehensive data extraction,
    handling dynamic content and JavaScript-rendered elements.
    """
    
    BASE_URL = "https://www.jumia.com.eg"
    PHONES_CATEGORY_URL = f"{BASE_URL}/catalog/?q=phones"
    
    # Request headers to mimic browser behavior
    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    def __init__(self, use_selenium: bool = False, headless: bool = True):
        """
        Initialize the Jumia Egypt scraper.
        
        Args:
            use_selenium: Whether to use Selenium for JavaScript rendering
            headless: Whether to run Selenium in headless mode
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.driver = None
        
        if self.use_selenium:
            self._initialize_selenium()
    
    def _initialize_selenium(self):
        """Initialize Selenium WebDriver."""
        try:
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--user-agent=' + self.HEADERS['User-Agent'])
            
            self.driver = webdriver.Chrome(options=options)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
    
    def scrape_phones(self, max_pages: int = 5) -> List[JumiaPhoneProduct]:
        """
        Scrape phones from Jumia Egypt.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of JumiaPhoneProduct objects
        """
        products = []
        
        for page_num in range(1, max_pages + 1):
            logger.info(f"Scraping page {page_num}...")
            
            try:
                page_products = self._scrape_page(page_num)
                products.extend(page_products)
                logger.info(f"Found {len(page_products)} products on page {page_num}")
            except Exception as e:
                logger.error(f"Error scraping page {page_num}: {e}")
                continue
        
        return products
    
    def _scrape_page(self, page_num: int) -> List[JumiaPhoneProduct]:
        """
        Scrape a single page of products.
        
        Args:
            page_num: Page number to scrape
            
        Returns:
            List of products from the page
        """
        url = f"{self.PHONES_CATEGORY_URL}?page={page_num}"
        html_content = self._fetch_page(url)
        
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Find all product containers
        product_containers = soup.find_all('div', {'class': re.compile(r'c-product-card')})
        
        for container in product_containers:
            try:
                product = self._extract_product_info(container)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error extracting product information: {e}")
                continue
        
        return products
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page's HTML content.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if fetch failed
        """
        try:
            if self.use_selenium:
                return self._fetch_with_selenium(url)
            else:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
    
    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """
        Fetch a page using Selenium for JavaScript rendering.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if fetch failed
        """
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "c-product-card"))
            )
            return self.driver.page_source
        except TimeoutException:
            logger.warning(f"Timeout waiting for products to load on {url}")
            return self.driver.page_source
    
    def _extract_product_info(self, container) -> Optional[JumiaPhoneProduct]:
        """
        Extract product information from a product container.
        
        Args:
            container: BeautifulSoup element containing product info
            
        Returns:
            JumiaPhoneProduct object or None if extraction failed
        """
        try:
            # Extract basic information
            product_id = container.get('data-product-id', '')
            
            # Extract name
            name_elem = container.find('h3', {'class': 'c-product-card__name'})
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown'
            
            # Extract price
            price_elem = container.find('span', {'class': re.compile(r'c-price')})
            price_text = price_elem.get_text(strip=True) if price_elem else '0'
            price = self._parse_price(price_text)
            
            # Extract original price and discount
            original_price_elem = container.find('span', {'class': 'c-price--before-discount'})
            original_price = None
            discount_percentage = None
            
            if original_price_elem:
                original_price = self._parse_price(original_price_elem.get_text(strip=True))
                if original_price and price:
                    discount_percentage = int(((original_price - price) / original_price) * 100)
            
            # Extract rating
            rating = None
            review_count = 0
            rating_elem = container.find('div', {'class': re.compile(r'c-rating')})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
                
                review_elem = container.find('span', {'class': 'c-product-card__review-count'})
                if review_elem:
                    review_text = review_elem.get_text(strip=True)
                    review_match = re.search(r'(\d+)', review_text)
                    if review_match:
                        review_count = int(review_match.group(1))
            
            # Extract availability
            availability = self._extract_availability(container)
            
            # Extract URL
            link_elem = container.find('a', {'class': 'c-product-card__link'})
            product_url = ''
            if link_elem and link_elem.get('href'):
                product_url = urljoin(self.BASE_URL, link_elem['href'])
            
            # Extract image URL
            image_url = None
            img_elem = container.find('img', {'class': re.compile(r'c-product-card__image')})
            if img_elem and img_elem.get('src'):
                image_url = img_elem['src']
            
            # Extract seller
            seller_elem = container.find('span', {'class': 'c-product-card__seller'})
            seller = seller_elem.get_text(strip=True) if seller_elem else None
            
            # Extract specifications from name
            storage, color, brand = self._extract_specs_from_name(name)
            
            # Build specifications dictionary
            specifications = {
                'storage': storage or 'Unknown',
                'color': color or 'Unknown',
            }
            
            return JumiaPhoneProduct(
                product_id=product_id,
                name=name,
                price=price,
                currency='EGP',
                original_price=original_price,
                discount_percentage=discount_percentage,
                rating=rating,
                review_count=review_count,
                availability=availability,
                url=product_url,
                image_url=image_url,
                seller=seller,
                storage=storage,
                color=color,
                brand=brand,
                specifications=specifications,
                scraped_at=datetime.utcnow().isoformat()
            )
        
        except Exception as e:
            logger.warning(f"Error extracting product: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> float:
        """
        Parse price text to float value.
        
        Args:
            price_text: Price text (e.g., "1,234.99 EGP")
            
        Returns:
            Price as float
        """
        try:
            # Remove currency and non-numeric characters (except decimal point)
            price_cleaned = re.sub(r'[^\d.]', '', price_text)
            return float(price_cleaned)
        except ValueError:
            logger.warning(f"Could not parse price: {price_text}")
            return 0.0
    
    def _extract_availability(self, container) -> str:
        """
        Extract availability status from product container.
        
        Args:
            container: BeautifulSoup element containing product info
            
        Returns:
            Availability status string
        """
        try:
            availability_elem = container.find('span', {'class': re.compile(r'availability|in-stock')})
            if availability_elem:
                text = availability_elem.get_text(strip=True).lower()
                if 'in stock' in text or 'متوفر' in text:
                    return 'In Stock'
                elif 'out of stock' in text or 'غير متوفر' in text:
                    return 'Out of Stock'
            
            # Check for "Add to Cart" button as indicator of availability
            add_to_cart = container.find('button', {'class': re.compile(r'add-to-cart')})
            if add_to_cart and not add_to_cart.get('disabled'):
                return 'In Stock'
            
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _extract_specs_from_name(self, name: str) -> Tuple[Optional[str], Optional[str], str]:
        """
        Extract storage, color, and brand from product name.
        
        Args:
            name: Product name
            
        Returns:
            Tuple of (storage, color, brand)
        """
        try:
            storage = None
            color = None
            brand = 'Unknown'
            
            # Extract brand
            brand_patterns = [
                r'^(Samsung|iPhone|Xiaomi|OPPO|Realme|Motorola|Nokia|OnePlus|Vivo)',
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    brand = match.group(1)
                    break
            
            # Extract storage
            storage_match = re.search(r'(\d+)\s*(GB|GB RAM)', name, re.IGNORECASE)
            if storage_match:
                storage = storage_match.group(0)
            
            # Extract color
            colors = ['Black', 'White', 'Silver', 'Gold', 'Blue', 'Red', 'Green', 'Purple', 'Gray']
            for color_name in colors:
                if color_name.lower() in name.lower():
                    color = color_name
                    break
            
            return storage, color, brand
        except Exception as e:
            logger.warning(f"Error extracting specs from name: {e}")
            return None, None, 'Unknown'
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """
        Scrape detailed information for a specific product.
        
        Args:
            product_url: URL of the product
            
        Returns:
            Dictionary with detailed product information
        """
        try:
            html_content = self._fetch_page(product_url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            details = {
                'url': product_url,
                'description': '',
                'specifications': {},
                'reviews': [],
                'images': [],
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            # Extract description
            desc_elem = soup.find('div', {'class': re.compile(r'product-description|description')})
            if desc_elem:
                details['description'] = desc_elem.get_text(strip=True)
            
            # Extract specifications table
            spec_table = soup.find('table', {'class': re.compile(r'specifications|specs')})
            if spec_table:
                rows = spec_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(strip=True)
                        details['specifications'][key] = value
            
            # Extract images
            images = soup.find_all('img', {'class': re.compile(r'product-image')})
            details['images'] = [img.get('src', '') for img in images if img.get('src')]
            
            return details
        except Exception as e:
            logger.error(f"Error scraping product details from {product_url}: {e}")
            return None
    
    def save_products_to_json(self, products: List[JumiaPhoneProduct], filename: str):
        """
        Save products to JSON file.
        
        Args:
            products: List of JumiaPhoneProduct objects
            filename: Output filename
        """
        try:
            data = [product.to_dict() for product in products]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(products)} products to {filename}")
        except Exception as e:
            logger.error(f"Error saving products to JSON: {e}")
    
    def save_products_to_csv(self, products: List[JumiaPhoneProduct], filename: str):
        """
        Save products to CSV file.
        
        Args:
            products: List of JumiaPhoneProduct objects
            filename: Output filename
        """
        try:
            import csv
            
            if not products:
                logger.warning("No products to save")
                return
            
            fieldnames = [
                'product_id', 'name', 'brand', 'price', 'currency', 'original_price',
                'discount_percentage', 'rating', 'review_count', 'availability',
                'storage', 'color', 'seller', 'url', 'image_url', 'scraped_at'
            ]
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in products:
                    row = {
                        'product_id': product.product_id,
                        'name': product.name,
                        'brand': product.brand,
                        'price': product.price,
                        'currency': product.currency,
                        'original_price': product.original_price,
                        'discount_percentage': product.discount_percentage,
                        'rating': product.rating,
                        'review_count': product.review_count,
                        'availability': product.availability,
                        'storage': product.storage,
                        'color': product.color,
                        'seller': product.seller,
                        'url': product.url,
                        'image_url': product.image_url,
                        'scraped_at': product.scraped_at
                    }
                    writer.writerow(row)
            
            logger.info(f"Saved {len(products)} products to {filename}")
        except Exception as e:
            logger.error(f"Error saving products to CSV: {e}")
    
    def close(self):
        """Close Selenium WebDriver if initialized."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")


# Example usage and testing
if __name__ == '__main__':
    # Initialize scraper
    scraper = JumiaEgyptScraper(use_selenium=False)
    
    try:
        # Scrape phones
        print("Starting Jumia Egypt phone scraper...")
        products = scraper.scrape_phones(max_pages=2)
        
        # Display results
        print(f"\nFound {len(products)} products")
        for product in products[:5]:  # Display first 5 products
            print(f"\n{product.name}")
            print(f"  Price: {product.price} {product.currency}")
            print(f"  Brand: {product.brand}")
            print(f"  Rating: {product.rating}")
            print(f"  Availability: {product.availability}")
        
        # Save results
        scraper.save_products_to_json(products, 'jumia_products.json')
        scraper.save_products_to_csv(products, 'jumia_products.csv')
        
    finally:
        scraper.close()
