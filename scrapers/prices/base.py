"""
Base Price Scraper using Playwright
Provides common functionality for all marketplace price scrapers.
"""

import logging
import random
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class BasePriceScraper(ABC):
    """
    Abstract base class for price scrapers using Playwright.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the scraper.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.user_agent = UserAgent()
        self.playwright = None
        self.browser = None
        self.context = None
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def start(self):
        """Start Playwright browser."""
        if self.playwright is None:
            logger.info("Starting Playwright...")
            self.playwright = sync_playwright().start()
            
            # Launch browser
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            
            # Create context with random user agent
            self.context = self.browser.new_context(
                user_agent=self.user_agent.random,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Set default timeout
            self.context.set_default_timeout(self.timeout)
            
            logger.info("Playwright started successfully")
    
    def stop(self):
        """Stop Playwright browser."""
        if self.context:
            self.context.close()
            self.context = None
        
        if self.browser:
            self.browser.close()
            self.browser = None
        
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        
        logger.info("Playwright stopped")
    
    def new_page(self) -> Page:
        """
        Create a new page with random user agent.
        
        Returns:
            Playwright Page object
        """
        if not self.context:
            self.start()
        
        page = self.context.new_page()
        return page
    
    @abstractmethod
    def get_store_name(self) -> str:
        """
        Get the name identifier for this store.
        
        Returns:
            Store name (e.g., 'amazon_eg', 'jumia_eg')
        """
        pass
    
    @abstractmethod
    def search_product(
        self,
        page: Page,
        brand: str,
        model: str,
        variant: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for a product and return search results.
        
        Args:
            page: Playwright page
            brand: Phone brand
            model: Phone model
            variant: Variant info (storage, RAM)
            
        Returns:
            List of search result dictionaries
        """
        pass
    
    def build_search_query(
        self,
        brand: str,
        model: str,
        variant: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build search query string.
        
        Args:
            brand: Phone brand
            model: Phone model
            variant: Variant info
            
        Returns:
            Search query string
        """
        query_parts = [brand, model]
        
        if variant:
            if variant.get('storage'):
                query_parts.append(variant['storage'])
            if variant.get('ram'):
                query_parts.append(variant['ram'])
        
        return ' '.join(query_parts)
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """
        Extract numeric price from text.
        
        Args:
            price_text: Price text (e.g., "EGP 15,999")
            
        Returns:
            Price as float or None
        """
        import re
        
        # Remove currency symbols and common text
        cleaned = price_text.replace('EGP', '').replace('LE', '').replace('E£', '')
        cleaned = cleaned.replace('جنيه', '').replace('ج.م', '')
        cleaned = cleaned.strip()
        
        # Find numbers with optional comma separators
        match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', cleaned)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                pass
        
        return None
    
    def safe_get_text(self, element, selector: str, default: str = '') -> str:
        """
        Safely get text from an element using selector.
        
        Args:
            element: Parent element
            selector: CSS selector
            default: Default value if not found
            
        Returns:
            Text content or default
        """
        try:
            elem = element.query_selector(selector)
            if elem:
                return elem.text_content().strip()
        except Exception as e:
            logger.debug(f"Error getting text for {selector}: {e}")
        
        return default
    
    def safe_get_attribute(self, element, selector: str, attribute: str, default: str = '') -> str:
        """
        Safely get attribute from an element.
        
        Args:
            element: Parent element
            selector: CSS selector
            attribute: Attribute name
            default: Default value if not found
            
        Returns:
            Attribute value or default
        """
        try:
            elem = element.query_selector(selector)
            if elem:
                value = elem.get_attribute(attribute)
                if value:
                    return value.strip()
        except Exception as e:
            logger.debug(f"Error getting attribute {attribute} for {selector}: {e}")
        
        return default
    
    def wait_random(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """
        Wait for a random duration (rate limiting).
        
        Args:
            min_seconds: Minimum wait time
            max_seconds: Maximum wait time
        """
        import time
        duration = random.uniform(min_seconds, max_seconds)
        time.sleep(duration)
    
    def scrape_phone_offers(
        self,
        phone_specs: Dict[str, Any],
        variant: Dict[str, Any],
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scrape offers for a specific phone variant.
        
        Args:
            phone_specs: Phone specifications
            variant: Variant information
            max_results: Maximum number of offers to return
            
        Returns:
            List of offer dictionaries
        """
        offers = []
        
        try:
            page = self.new_page()
            
            brand = phone_specs.get('brand', '')
            model = phone_specs.get('model', '')
            
            logger.info(f"Searching {self.get_store_name()} for {brand} {model}")
            
            # Search for product
            results = self.search_product(page, brand, model, variant)
            
            if not results:
                logger.warning(f"No results found for {brand} {model}")
                page.close()
                return offers
            
            logger.info(f"Found {len(results)} results")
            
            # Process top results
            for result in results[:max_results]:
                try:
                    offer = {
                        'store': self.get_store_name(),
                        'title': result.get('title', ''),
                        'price': result.get('price', 0),
                        'currency': 'EGP',
                        'url': result.get('url', ''),
                        'seller': result.get('seller', self.get_store_name()),
                        'availability': result.get('availability', 'unknown'),
                        'scraped_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.error(f"Error processing result: {e}")
                    continue
            
            page.close()
            
        except Exception as e:
            logger.error(f"Error scraping {self.get_store_name()}: {e}", exc_info=True)
        
        return offers
