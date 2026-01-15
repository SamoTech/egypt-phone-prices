"""
Dream 2000 Egypt Price Scraper
Scrapes phone prices from dream2000.com.eg
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from playwright.sync_api import Page
from .base import BasePriceScraper

logger = logging.getLogger(__name__)


class Dream2000Scraper(BasePriceScraper):
    """
    Scraper for Dream 2000 Egypt (dream2000.com.eg).
    Major electronics retailer in Egypt with multiple branches.
    """
    
    STORE_NAME = "dream2000"
    BASE_URL = "https://www.dream2000.com.eg"
    SEARCH_URL = f"{BASE_URL}/search"
    
    def get_store_name(self) -> str:
        return self.STORE_NAME
    
    def search_product(
        self,
        page: Page,
        brand: str,
        model: str,
        variant: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for a product on Dream 2000."""
        results = []
        
        try:
            # Build search query
            query = self.build_search_query(brand, model, variant)
            search_url = f"{self.SEARCH_URL}?q={query.replace(' ', '+')}"
            
            logger.info(f"Searching Dream 2000: {search_url}")
            
            # Navigate to search page
            page.goto(search_url, wait_until='networkidle', timeout=30000)
            self.wait_random(2, 4)
            
            # Wait for products to load
            try:
                page.wait_for_selector('.product-item, .product-card, .products-grid .item', timeout=10000)
            except:
                logger.warning("No products found on Dream 2000")
                return results
            
            # Extract products
            product_elements = page.query_selector_all('.product-item, .product-card, .products-grid .item')
            
            for element in product_elements[:10]:
                try:
                    product = self._extract_product(element)
                    if product:
                        results.append(product)
                except Exception as e:
                    logger.debug(f"Error extracting product: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error searching Dream 2000: {e}")
        
        return results
    
    def _extract_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract product data from element."""
        try:
            # Title
            title = self.safe_get_text(element, '.product-name, .product-title, .name a, h2 a, h3 a')
            if not title:
                return None
            
            # URL
            url = self.safe_get_attribute(element, '.product-name a, .product-title a, .name a, h2 a, h3 a', 'href')
            if url and not url.startswith('http'):
                url = f"{self.BASE_URL}{url}"
            
            # Price
            price_text = self.safe_get_text(element, '.price, .special-price, .product-price, .current-price')
            price = self.extract_price(price_text) if price_text else None
            
            if not price:
                return None
            
            # Availability
            availability = "in_stock"
            if element.query_selector('.out-of-stock, .unavailable, .sold-out'):
                availability = "out_of_stock"
            
            return {
                'title': title,
                'price': price,
                'url': url or self.BASE_URL,
                'seller': 'Dream 2000',
                'availability': availability
            }
            
        except Exception as e:
            logger.debug(f"Error parsing Dream 2000 product: {e}")
            return None