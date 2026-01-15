"""
Dubai Phone Egypt Price Scraper
Scrapes phone prices from dubaiphone.com.eg
"""

import logging
import re
from typing import Dict, List, Any, Optional
from .base import BasePriceScraper

logger = logging.getLogger(__name__)


class DubaiPhoneScraper(BasePriceScraper):
    """
    Scraper for Dubai Phone Egypt (dubaiphone.com.eg).
    Popular electronics retailer in Egypt.
    """
    
    STORE_NAME = "dubaiphone"
    BASE_URL = "https://www.dubaiphone.com.eg"
    SEARCH_URL = f"{BASE_URL}/catalogsearch/result/"
    
    def __init__(self):
        super().__init__()
        self.store_display_name = "Dubai Phone"
    
    def build_search_url(self, phone_specs: Dict[str, Any], variant: Dict[str, Any]) -> str:
        """Build search URL for Dubai Phone."""
        brand = phone_specs.get('brand', '')
        model = phone_specs.get('model', '')
        storage = variant.get('storage', '')
        
        # Build search query
        query_parts = [brand, model]
        if storage:
            query_parts.append(storage)
        
        query = '+'.join(query_parts)
        return f"{self.SEARCH_URL}?q={query}"
    
    def extract_products_from_page(self, page) -> List[Dict[str, Any]]:
        """Extract product data from search results page."""
        products = []
        
        try:
            # Wait for products to load
            page.wait_for_selector('.product-item, .product-items, .products-grid', timeout=10000)
            
            # Get all product containers
            product_elements = page.query_selector_all('.product-item')
            
            for element in product_elements[:10]:  # Limit to first 10
                try:
                    product = self._extract_single_product(element)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Error extracting product: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error extracting products: {e}")
        
        return products
    
    def _extract_single_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract data from a single product element."""
        try:
            # Extract title
            title_el = element.query_selector('.product-item-name a, .product-name a, .product-item-link')
            title = title_el.inner_text().strip() if title_el else None
            
            if not title:
                return None
            
            # Extract URL
            url = title_el.get_attribute('href') if title_el else None
            
            # Extract price
            price_el = element.query_selector('.price, .special-price .price, .regular-price .price')
            price_text = price_el.inner_text().strip() if price_el else None
            price = self._parse_price(price_text) if price_text else None
            
            if not price or price <= 0:
                return None
            
            # Check availability
            availability = "in_stock"
            out_of_stock_el = element.query_selector('.out-of-stock, .unavailable')
            if out_of_stock_el:
                availability = "out_of_stock"
            
            return {
                'store': self.STORE_NAME,
                'title': title,
                'price': price,
                'currency': 'EGP',
                'url': url or self.BASE_URL,
                'seller': self.store_display_name,
                'availability': availability,
                'scraped_at': self._get_timestamp()
            }
            
        except Exception as e:
            logger.debug(f"Error parsing product: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text."""
        if not price_text:
            return None
        
        # Remove currency symbols and text
        price_text = price_text.replace('EGP', '').replace('LE', '').replace('E£', '')
        price_text = price_text.replace('جنيه', '').replace('ج.م', '').replace(',', '')
        
        # Extract number
        match = re.search(r'[\d.]+', price_text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None