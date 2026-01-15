"""
2B Egypt Price Scraper
Scrapes phone prices from 2b.com.eg (major electronics retailer)
"""

import logging
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
from datetime import datetime
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from .base import BasePriceScraper

logger = logging.getLogger(__name__)


class TwoBScraper(BasePriceScraper):
    """
    Scraper for 2B Egypt (2b.com.eg).
    Major electronics retailer in Egypt.
    """
    
    def get_store_name(self) -> str:
        return 'twob'
    
    def search_product(
        self,
        page: Page,
        brand: str,
        model: str,
        variant: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for a product on 2B."""
        results = []
        
        try:
            query = self.build_search_query(brand, model, variant)
            search_url = f"https://www.2b.com.eg/en/catalogsearch/result/?q={quote_plus(query)}"
            
            logger.info(f"Searching 2B: {search_url}")
            
            page.goto(search_url, wait_until='networkidle', timeout=30000)
            self.wait_random(2, 4)
            
            try:
                page.wait_for_selector('.product-item, .products-grid .item', timeout=10000)
            except PlaywrightTimeout:
                logger.warning("No products found on 2B")
                return results
            
            product_elements = page.query_selector_all('.product-item, .products-grid .item')
            
            for element in product_elements[:10]:
                try:
                    product = self._extract_product(element)
                    if product:
                        results.append(product)
                except Exception as e:
                    logger.debug(f"Error extracting product: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error searching 2B: {e}")
        
        return results
    
    def _extract_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract product data from element."""
        try:
            title = self.safe_get_text(element, '.product-item-name a, .product-name a')
            if not title:
                return None
            
            url = self.safe_get_attribute(element, '.product-item-name a, .product-name a', 'href')
            if url and not url.startswith('http'):
                url = f"https://www.2b.com.eg{url}"
            
            price_text = self.safe_get_text(element, '.price, .special-price .price')
            price = self.extract_price(price_text) if price_text else None
            
            if not price:
                return None
            
            availability = "in_stock"
            if element.query_selector('.out-of-stock, .unavailable'):
                availability = "out_of_stock"
            
            return {
                'title': title,
                'price': price,
                'url': url or 'https://www.2b.com.eg',
                'seller': '2B',
                'availability': availability
            }
            
        except Exception as e:
            logger.debug(f"Error parsing 2B product: {e}")
            return None