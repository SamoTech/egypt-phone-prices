"""
Noon Egypt Price Scraper
"""

import logging
from typing import List, Dict, Optional, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

from .base import BasePriceScraper

logger = logging.getLogger(__name__)


class NoonEgPriceScraper(BasePriceScraper):
    """Noon Egypt marketplace price scraper."""
    
    def get_store_name(self) -> str:
        """Return store identifier."""
        return 'noon_eg'
    
    def search_product(
        self,
        page: Page,
        brand: str,
        model: str,
        variant: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Noon Egypt for a product.
        
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
            search_url = f"https://www.noon.com/egypt-en/search?q={query}"
            
            logger.info(f"Searching Noon EG: {search_url}")
            
            # Navigate to search page
            page.goto(search_url, wait_until='networkidle')
            
            # Wait for search results - Noon uses React, so wait longer
            try:
                page.wait_for_selector('[data-qa="product-name"], .productContainer', timeout=15000)
            except PlaywrightTimeout:
                logger.warning("Search results not loaded - trying alternative selector")
                try:
                    page.wait_for_selector('article, [class*="Product"]', timeout=5000)
                except PlaywrightTimeout:
                    logger.error("No search results found")
                    return results
            
            # Random delay for rate limiting
            self.wait_random(2.0, 4.0)
            
            # Extract product cards - Noon uses various selectors
            product_cards = page.query_selector_all('.productContainer')
            
            if not product_cards:
                product_cards = page.query_selector_all('[data-qa="product-container"]')
            
            if not product_cards:
                product_cards = page.query_selector_all('article[class*="Product"]')
            
            if not product_cards:
                product_cards = page.query_selector_all('div[class*="Grid"] > div')
            
            logger.info(f"Found {len(product_cards)} product cards")
            
            # Process each product card
            for card in product_cards[:10]:
                try:
                    # Extract product title
                    title = None
                    title_elem = card.query_selector('[data-qa="product-name"]')
                    if not title_elem:
                        title_elem = card.query_selector('[class*="productTitle"]')
                    if not title_elem:
                        title_elem = card.query_selector('h2, h3')
                    
                    if title_elem:
                        title = title_elem.text_content().strip()
                    
                    if not title:
                        # Try extracting from link title attribute
                        link = card.query_selector('a[title]')
                        if link:
                            title = link.get_attribute('title')
                    
                    if not title:
                        continue
                    
                    # Extract product URL
                    link_elem = card.query_selector('a[href*="/product/"]')
                    if not link_elem:
                        link_elem = card.query_selector('a[href]')
                    
                    if not link_elem:
                        continue
                    
                    product_url = link_elem.get_attribute('href')
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.noon.com{product_url}"
                    
                    # Extract price
                    price = None
                    
                    # Try data attribute first
                    price_elem = card.query_selector('[data-qa="product-price"]')
                    if not price_elem:
                        price_elem = card.query_selector('[class*="price"]')
                    if not price_elem:
                        price_elem = card.query_selector('strong, [class*="Price"]')
                    
                    if price_elem:
                        price_text = price_elem.text_content()
                        price = self.extract_price(price_text)
                    
                    # Skip if no price found
                    if not price:
                        continue
                    
                    # Check availability
                    availability = 'in_stock'
                    
                    # Check for out of stock indicators
                    out_of_stock_elem = card.query_selector('[class*="outOfStock"], [class*="OutOfStock"]')
                    if out_of_stock_elem:
                        availability = 'out_of_stock'
                    else:
                        # Check text content
                        card_text = card.text_content().lower()
                        if 'out of stock' in card_text or 'currently unavailable' in card_text:
                            availability = 'out_of_stock'
                    
                    # Extract seller info
                    seller = 'Noon'
                    seller_elem = card.query_selector('[data-qa="seller-name"], [class*="seller"]')
                    if seller_elem:
                        seller_text = seller_elem.text_content().strip()
                        if seller_text and len(seller_text) > 0:
                            seller = seller_text
                    
                    # Check for "Sold by Noon" badge
                    noon_badge = card.query_selector('[class*="ExpressBadge"], [class*="noon"]')
                    if noon_badge:
                        badge_text = noon_badge.text_content().lower()
                        if 'noon' in badge_text or 'express' in badge_text:
                            seller = 'Noon'
                    
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
            
            logger.info(f"Successfully extracted {len(results)} products from Noon EG")
            
        except PlaywrightTimeout:
            logger.error("Timeout while loading Noon EG search page")
        except Exception as e:
            logger.error(f"Error searching Noon EG: {e}", exc_info=True)
        
        return results
