"""
B.Tech Egypt Price Scraper
Scrapes phone prices from btech.com (largest electronics retailer in Egypt)
"""

import logging
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
from datetime import datetime
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from .base import BasePriceScraper

logger = logging.getLogger(__name__)


class BTechScraper(BasePriceScraper):
    """
    Scraper for B.Tech Egypt (btech.com).
    Largest electronics retailer in Egypt with 100+ branches.
    """
    
    def get_store_name(self) -> str:
        return 'btech'
    
    def search_product(
        self,
        page: Page,
        brand: str,
        model: str,
        variant: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for a product on B.Tech."""
        results = []
        
        try:
            # Build search query
            query = self.build_search_query(brand, model, variant)
            search_url = f"https://btech.com/en/catalogsearch/result/?q={quote_plus(query)}"
            
            logger.info(f"Searching B.Tech: {search_url}")
            
            # Navigate to search page
            page.goto(search_url, wait_until='networkidle', timeout=30000)
            self.wait_random(2, 4)
            
            # Wait for products to load
            try:
                page.wait_for_selector('.product-item, .product-items .item, .products-grid', timeout=10000)
            except PlaywrightTimeout:
                logger.warning("No products found on B.Tech")
                return results
            
            # Extract products
            product_elements = page.query_selector_all('.product-item, .product-items .item')
            
            for element in product_elements[:10]:
                try:
                    product = self._extract_product(element)
                    if product:
                        results.append(product)
                except Exception as e:
                    logger.debug(f"Error extracting product: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error searching B.Tech: {e}")
        
        return results
    
    def _extract_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract product data from element."""
        try:
            # Title
            title = self.safe_get_text(element, '.product-item-name a, .product-name a, .product-item-link')
            if not title:
                return None
            
            # URL
            url = self.safe_get_attribute(element, '.product-item-name a, .product-name a, .product-item-link', 'href')
            if url and not url.startswith('http'):
                url = f"https://btech.com{url}"
            
            # Price
            price_text = self.safe_get_text(element, '.price, .special-price .price, .price-box .price')
            price = self.extract_price(price_text) if price_text else None
            
            if not price:
                return None
            
            # Availability
            availability = "in_stock"
            if element.query_selector('.out-of-stock, .unavailable, .outofstock'):
                availability = "out_of_stock"
            
            return {
                'title': title,
                'price': price,
                'url': url or 'https://btech.com',
                'seller': 'B.Tech',
                'availability': availability
            }
            
        except Exception as e:
            logger.debug(f"Error parsing B.Tech product: {e}")
            return None