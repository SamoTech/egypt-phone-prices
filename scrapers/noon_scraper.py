"""
Noon Egypt Price Scraper

This module provides functionality to scrape phone prices from Noon Egypt.
It includes canonical URL validation for product links to ensure data consistency.
"""

import logging
import re
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NoonScraperError(Exception):
    """Base exception for Noon scraper errors."""
    pass


class CanonicalURLError(NoonScraperError):
    """Exception raised for canonical URL validation errors."""
    pass


class NoonScraper:
    """Scraper for Noon Egypt phone prices with canonical URL validation."""

    BASE_URL = "https://www.noon.com/egypt"
    PHONES_ENDPOINT = "/category/mobiles-and-phones"
    
    # Request headers to mimic browser behavior
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                 "image/webp,*/*;q=0.8",
        "Referer": "https://www.noon.com/egypt",
    }

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the Noon scraper.

        Args:
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def __del__(self):
        """Clean up session on destruction."""
        if hasattr(self, 'session'):
            self.session.close()

    @staticmethod
    def validate_canonical_url(url: str) -> bool:
        """
        Validate that a URL follows Noon's canonical format.

        Noon's canonical product URLs typically follow patterns like:
        - https://www.noon.com/egypt/p/{product-id}/{product-slug}

        Args:
            url: The URL to validate

        Returns:
            bool: True if URL matches canonical format, False otherwise
        """
        if not url:
            return False

        parsed = urlparse(url)
        
        # Check domain
        if "noon.com" not in parsed.netloc:
            return False

        # Check path pattern - canonical URLs should have /p/{id}/{slug}
        path_pattern = r'^/egypt/p/\d+/[a-z0-9\-]+/?$'
        if not re.match(path_pattern, parsed.path):
            return False

        return True

    @staticmethod
    def extract_canonical_url(soup: BeautifulSoup, page_url: str) -> Optional[str]:
        """
        Extract canonical URL from HTML document.

        Args:
            soup: BeautifulSoup object of the page
            page_url: The page URL for reference

        Returns:
            Canonical URL if found, None otherwise
        """
        canonical_link = soup.find('link', {'rel': 'canonical'})
        if canonical_link and canonical_link.get('href'):
            return canonical_link['href']
        return None

    def _make_request(self, url: str) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic.

        Args:
            url: URL to request

        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        return None

    def scrape_product_link(self, product_url: str) -> Optional[str]:
        """
        Scrape a product link and validate its canonical URL.

        Args:
            product_url: The product URL to scrape

        Returns:
            Canonical URL if valid, None otherwise

        Raises:
            CanonicalURLError: If canonical URL validation fails
        """
        response = self._make_request(product_url)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        canonical_url = self.extract_canonical_url(soup, product_url)

        if not canonical_url:
            logger.warning(f"No canonical URL found for {product_url}")
            return None

        # Normalize URL
        if not canonical_url.startswith('http'):
            canonical_url = urljoin(self.BASE_URL, canonical_url)

        # Validate canonical URL format
        if not self.validate_canonical_url(canonical_url):
            raise CanonicalURLError(
                f"Invalid canonical URL format: {canonical_url}"
            )

        return canonical_url

    def extract_price(self, price_text: str) -> Optional[float]:
        """
        Extract numerical price from text.

        Args:
            price_text: Text containing price information

        Returns:
            Float price value or None if extraction fails
        """
        if not price_text:
            return None

        # Remove currency symbols and whitespace, extract numbers and decimals
        match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    def scrape_phones(self, page: int = 1, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape phone listings from Noon Egypt.

        Args:
            page: Page number to scrape (default: 1)
            limit: Maximum number of products to return (None for all)

        Returns:
            List of phone product dictionaries with price and link information
        """
        phones = []
        url = f"{self.BASE_URL}{self.PHONES_ENDPOINT}?page={page}"

        response = self._make_request(url)
        if not response:
            logger.error(f"Failed to fetch phones page {page}")
            return phones

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find product containers - adjust selector based on Noon's HTML structure
        product_containers = soup.find_all('div', {'class': re.compile('product')})

        for container in product_containers:
            if limit and len(phones) >= limit:
                break

            try:
                # Extract product link
                link_elem = container.find('a', href=True)
                if not link_elem or not link_elem['href']:
                    continue

                product_url = link_elem['href']
                if not product_url.startswith('http'):
                    product_url = urljoin(self.BASE_URL, product_url)

                # Validate canonical URL
                try:
                    canonical_url = self.scrape_product_link(product_url)
                    if not canonical_url:
                        logger.warning(
                            f"Skipping product with invalid canonical URL: {product_url}"
                        )
                        continue
                except CanonicalURLError as e:
                    logger.warning(f"Canonical URL error: {e}")
                    continue

                # Extract product name
                name_elem = container.find('h2') or container.find('a')
                product_name = name_elem.get_text(strip=True) if name_elem else "Unknown"

                # Extract price
                price_elem = container.find('span', {'class': re.compile('price')})
                price_text = price_elem.get_text(strip=True) if price_elem else None
                price = self.extract_price(price_text)

                # Extract product ID from canonical URL
                product_id = None
                if canonical_url:
                    match = re.search(r'/p/(\d+)/', canonical_url)
                    if match:
                        product_id = match.group(1)

                phone = {
                    'name': product_name,
                    'price': price,
                    'price_raw': price_text,
                    'url': canonical_url,
                    'product_id': product_id,
                    'source': 'noon_egypt',
                }

                phones.append(phone)
                logger.info(
                    f"Scraped: {product_name} - EGP {price} "
                    f"(ID: {product_id})"
                )

            except Exception as e:
                logger.error(f"Error processing product container: {e}")
                continue

        logger.info(f"Successfully scraped {len(phones)} phones from page {page}")
        return phones

    def scrape_product_details(self, canonical_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed information for a specific product.

        Args:
            canonical_url: Canonical URL of the product

        Returns:
            Dictionary containing product details or None if scraping fails
        """
        if not self.validate_canonical_url(canonical_url):
            logger.error(f"Invalid canonical URL: {canonical_url}")
            return None

        response = self._make_request(canonical_url)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        try:
            # Extract product ID from URL
            product_id = re.search(r'/p/(\d+)/', canonical_url)
            product_id = product_id.group(1) if product_id else None

            # Extract product name
            name_elem = soup.find('h1')
            product_name = name_elem.get_text(strip=True) if name_elem else None

            # Extract price
            price_elem = soup.find('span', {'class': re.compile('price')})
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self.extract_price(price_text)

            # Extract rating (if available)
            rating_elem = soup.find('span', {'class': re.compile('rating')})
            rating = rating_elem.get_text(strip=True) if rating_elem else None

            # Extract product description
            description_elem = soup.find('div', {'class': re.compile('description')})
            description = description_elem.get_text(strip=True) if description_elem else None

            product_details = {
                'product_id': product_id,
                'name': product_name,
                'price': price,
                'price_raw': price_text,
                'rating': rating,
                'description': description,
                'url': canonical_url,
                'source': 'noon_egypt',
            }

            return product_details

        except Exception as e:
            logger.error(f"Error scraping product details from {canonical_url}: {e}")
            return None

    def close(self):
        """Close the session."""
        if hasattr(self, 'session'):
            self.session.close()


def main():
    """Example usage of the Noon scraper."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scraper = NoonScraper()
    try:
        # Scrape phones from page 1
        phones = scraper.scrape_phones(page=1, limit=10)
        
        for phone in phones:
            print(f"\n{phone['name']}")
            print(f"  Price: EGP {phone['price']}")
            print(f"  URL: {phone['url']}")
            print(f"  Product ID: {phone['product_id']}")

    except Exception as e:
        logger.error(f"Error during scraping: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
