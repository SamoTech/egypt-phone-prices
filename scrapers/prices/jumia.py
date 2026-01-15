"""
Jumia Egypt Price Scraper
"""

import logging
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from .base import BasePriceScraper

logger = logging.getLogger(__name__)


class JumiaEgPriceScraper(BasePriceScraper):
    """Jumia Egypt marketplace price scraper."""
    
    def get_store_name(self) -> str:
        """Return store identifier."""
        return 'jumia_eg'
    
    def search_product(
        self,
        page: Page,
        brand: str,
        model: str,
        variant: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Jumia Egypt for a product.
        
        Args:
            page: Playwright page
            brand: Phone brand
            model: Phone model
            variant: Variant info (storage, RAM)
            
        Returns:
            List of product result dictionaries
        """
        results = []
        
        try:
            # Build search query
            query = self.build_search_query(brand, model, variant)
            search_url = f"https://www.jumia.com.eg/catalog/?q={quote_plus(query)}"
            
            logger.info(f"Searching Jumia EG: {search_url}")
            
            # Navigate to search page
            page.goto(search_url, wait_until='networkidle')
            
            # Wait for search results
            try:
                page.wait_for_selector('article.core, .core', timeout=10000)
            except PlaywrightTimeout:
                logger.warning("Search results not loaded - trying alternative selector")
                try:
                    page.wait_for_selector('[data-catalog-grid-item]', timeout=5000)
                except PlaywrightTimeout:
                    logger.error("No search results found")
                    return results
            
            # Random delay for rate limiting
            self.wait_random(1.5, 3.0)
            
            # Extract product cards
            product_cards = page.query_selector_all('article.core')
            
            if not product_cards:
                product_cards = page.query_selector_all('.core')
            
            if not product_cards:
                product_cards = page.query_selector_all('[data-catalog-grid-item]')
            
            logger.info(f"Found {len(product_cards)} product cards")
            
            # Process each product card
            for card in product_cards[:10]:
                try:
                    # Extract product title
                    title_elem = card.query_selector('h3.name')
                    if not title_elem:
                        title_elem = card.query_selector('.name')
                    if not title_elem:
                        title_elem = card.query_selector('a[title]')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_attribute('title')
                    if not title:
                        title = title_elem.text_content().strip()
                    
                    if not title:
                        continue
                    
                    # Extract product URL
                    link_elem = card.query_selector('a[href]')
                    if not link_elem:
                        continue
                    
                    product_url = link_elem.get_attribute('href')
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.jumia.com.eg{product_url}"
                    
                    # Extract price
                    price = None
                    price_elem = card.query_selector('.prc')
                    
                    if not price_elem:
                        price_elem = card.query_selector('[data-price]')
                    
                    if price_elem:
                        # Try data attribute first
                        price_attr = price_elem.get_attribute('data-price')
                        if price_attr:
                            try:
                                price = float(price_attr)
                            except ValueError:
                                pass
                        
                        # If not found, extract from text
                        if not price:
                            price_text = price_elem.text_content()
                            price = self.extract_price(price_text)
                    
                    # Skip if no price found
                    if not price:
                        continue
                    
                    # Check availability
                    availability = 'in_stock'
                    out_of_stock_elem = card.query_selector('.tag._dsbl, .-fs0')
                    if out_of_stock_elem:
                        text = out_of_stock_elem.text_content().lower()
                        if 'out of stock' in text or 'unavailable' in text or 'currently unavailable' in text:
                            availability = 'out_of_stock'
                    
                    # Extract seller info
                    seller = 'Jumia'
                    seller_elem = card.query_selector('.store-name, .bdg._mall')
                    if seller_elem:
                        seller_text = seller_elem.text_content().strip()
                        if seller_text:
                            seller = seller_text
                    
                    result = {
                        'title': title,
                        'price': price,
                        'url': product_url,
                        'availability': availability,
                        'seller': seller
                    }
                    
                    results.append(result)
                    logger.debug(f"Extracted: {title} - {price} EGP")
                    
                except Exception as e:
                    logger.debug(f"Error processing product card: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(results)} products from Jumia EG")
            
        except PlaywrightTimeout:
            logger.error("Timeout while loading Jumia EG search page")
        except Exception as e:
            logger.error(f"Error searching Jumia EG: {e}", exc_info=True)
        
        return results
