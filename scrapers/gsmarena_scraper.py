"""
GSMArena Phone Specifications Scraper

This module provides functionality to scrape phone specifications from GSMArena.
It extracts detailed information about phones including hardware specs, camera details,
battery information, and other technical specifications.
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, quote
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GSMArenaScraperError(Exception):
    """Custom exception for GSMArena scraper errors"""
    pass


class GSMArenaScraperRateLimitError(GSMArenaScraperError):
    """Exception raised when rate limit is hit"""
    pass


class GSMArenaScraperPhoneNotFoundError(GSMArenaScraperError):
    """Exception raised when phone is not found"""
    pass


class GSMArenaScraperTimeout(GSMArenaScraperError):
    """Exception raised when request times out"""
    pass


class GSMArenaScrapers:
    """Scraper for GSMArena phone specifications"""

    BASE_URL = "https://www.gsmarena.com"
    SEARCH_URL = f"{BASE_URL}/results.php"
    
    def __init__(self, timeout: int = 10, retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the GSMArena scraper.
        
        Args:
            timeout: Request timeout in seconds
            retries: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: URL to request
            params: Query parameters
            
        Returns:
            Response object if successful, None otherwise
            
        Raises:
            GSMArenaScraperRateLimitError: If rate limited
            GSMArenaScraperTimeout: If request times out
        """
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 429:
                    raise GSMArenaScraperRateLimitError("Rate limited by GSMArena")
                
                response.raise_for_status()
                return response
                
            except requests.Timeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.retries}: {e}")
                if attempt == self.retries - 1:
                    raise GSMArenaScraperTimeout(f"Request timed out after {self.retries} attempts")
                time.sleep(self.retry_delay)
                
            except requests.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}/{self.retries}: {e}")
                if attempt == self.retries - 1:
                    raise GSMArenaScraperError(f"Request failed after {self.retries} attempts: {e}")
                time.sleep(self.retry_delay)
        
        return None

    def search_phones(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for phones on GSMArena.
        
        Args:
            query: Phone name or model to search for
            limit: Maximum number of results to return
            
        Returns:
            List of phone search results with basic info
        """
        try:
            params = {'sSearch': query}
            response = self._make_request(self.SEARCH_URL, params=params)
            
            if not response:
                logger.error(f"Failed to search for phones: {query}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find phone result rows
            phone_rows = soup.select('div.general-specs > table > tbody > tr')
            
            for idx, row in enumerate(phone_rows[:limit]):
                try:
                    link = row.select_one('a')
                    if link:
                        phone_name = link.get_text(strip=True)
                        phone_url = urljoin(self.BASE_URL, link.get('href'))
                        phone_id = phone_url.split('/')[-1].replace('.php', '')
                        
                        results.append({
                            'name': phone_name,
                            'url': phone_url,
                            'phone_id': phone_id
                        })
                        logger.debug(f"Found phone: {phone_name}")
                except Exception as e:
                    logger.debug(f"Error parsing phone row: {e}")
                    continue
            
            logger.info(f"Found {len(results)} phones for query: {query}")
            return results
            
        except GSMArenaScraperError as e:
            logger.error(f"Scraper error during search: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise GSMArenaScraperError(f"Search failed: {e}")

    def get_phone_specs(self, phone_url: str) -> Dict[str, Any]:
        """
        Scrape detailed specifications for a phone.
        
        Args:
            phone_url: Full URL to the phone's GSMArena page
            
        Returns:
            Dictionary containing phone specifications
            
        Raises:
            GSMArenaScraperPhoneNotFoundError: If phone page not found
        """
        try:
            response = self._make_request(phone_url)
            
            if not response or response.status_code == 404:
                raise GSMArenaScraperPhoneNotFoundError(f"Phone not found: {phone_url}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            specs = self._parse_phone_page(soup, phone_url)
            
            logger.info(f"Successfully scraped specs for: {specs.get('name', 'Unknown')}")
            return specs
            
        except GSMArenaScraperPhoneNotFoundError:
            raise
        except GSMArenaScraperError as e:
            logger.error(f"Scraper error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error scraping phone specs: {e}")
            raise GSMArenaScraperError(f"Failed to scrape phone specs: {e}")

    def _parse_phone_page(self, soup: BeautifulSoup, phone_url: str) -> Dict[str, Any]:
        """
        Parse phone specifications from the HTML page.
        
        Args:
            soup: BeautifulSoup object of the phone page
            phone_url: URL of the phone page
            
        Returns:
            Dictionary with extracted specifications
        """
        specs = {
            'url': phone_url,
            'name': None,
            'brand': None,
            'release_date': None,
            'body': {},
            'display': {},
            'performance': {},
            'camera': {},
            'battery': {},
            'software': {},
            'connectivity': {},
            'features': {},
            'misc': {}
        }
        
        # Extract phone name
        title_elem = soup.select_one('h1.specs-phone-name-title')
        if title_elem:
            specs['name'] = title_elem.get_text(strip=True)
        
        # Extract brand and model
        model_info = soup.select_one('div.data')
        if model_info:
            specs['brand'] = model_info.get_text(strip=True).split()[0] if model_info.get_text() else None
        
        # Parse all specification sections
        spec_tables = soup.select('table.table.table-condensed.table-hover')
        
        for table in spec_tables:
            section_title = table.select_one('th.ttl')
            if not section_title:
                continue
            
            section_name = section_title.get_text(strip=True).lower()
            section_data = self._parse_spec_section(table)
            
            # Categorize specs
            if 'body' in section_name or 'design' in section_name:
                specs['body'].update(section_data)
            elif 'display' in section_name or 'screen' in section_name:
                specs['display'].update(section_data)
            elif 'performance' in section_name or 'processor' in section_name:
                specs['performance'].update(section_data)
            elif 'camera' in section_name:
                specs['camera'].update(section_data)
            elif 'battery' in section_name:
                specs['battery'].update(section_data)
            elif 'software' in section_name or 'os' in section_name:
                specs['software'].update(section_data)
            elif 'network' in section_name or 'connectivity' in section_name or '2g' in section_name or '3g' in section_name or '4g' in section_name or '5g' in section_name:
                specs['connectivity'].update(section_data)
            elif 'features' in section_name:
                specs['features'].update(section_data)
            else:
                specs['misc'].update(section_data)
        
        return specs

    def _parse_spec_section(self, table: BeautifulSoup) -> Dict[str, str]:
        """
        Parse a single specification section table.
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            Dictionary of specification key-value pairs
        """
        section_data = {}
        
        rows = table.select('tr')
        for row in rows:
            # Skip header rows
            if row.select_one('th.ttl'):
                continue
            
            cells = row.select('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                if key and value:
                    section_data[key] = value
        
        return section_data

    def scrape_phone(self, phone_name: str, get_all_variants: bool = False) -> Dict[str, Any]:
        """
        Complete pipeline to search and scrape a phone.
        
        Args:
            phone_name: Name of the phone to scrape
            get_all_variants: If True, scrape all variants found
            
        Returns:
            Dictionary with phone specifications
        """
        try:
            search_results = self.search_phones(phone_name)
            
            if not search_results:
                raise GSMArenaScraperPhoneNotFoundError(f"No phones found matching: {phone_name}")
            
            if get_all_variants:
                all_specs = []
                for phone in search_results:
                    try:
                        specs = self.get_phone_specs(phone['url'])
                        all_specs.append(specs)
                    except Exception as e:
                        logger.warning(f"Failed to scrape {phone['name']}: {e}")
                        continue
                
                return {
                    'query': phone_name,
                    'variants_found': len(all_specs),
                    'phones': all_specs
                }
            else:
                # Scrape only the first result
                first_phone = search_results[0]
                specs = self.get_phone_specs(first_phone['url'])
                return specs
                
        except GSMArenaScraperError:
            raise
        except Exception as e:
            logger.error(f"Error in scrape_phone: {e}")
            raise GSMArenaScraperError(f"Failed to scrape phone: {e}")

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def main():
    """Example usage of the GSMArena scraper"""
    try:
        scraper = GSMArenaScrapers()
        
        # Example: Search for an iPhone
        phone_name = "iPhone 15"
        print(f"\nSearching for: {phone_name}")
        
        specs = scraper.scrape_phone(phone_name)
        print(f"\nPhone: {specs.get('name')}")
        print(f"URL: {specs.get('url')}")
        print(f"\nDisplay Specs:")
        for key, value in specs.get('display', {}).items():
            print(f"  {key}: {value}")
        
        print(f"\nCamera Specs:")
        for key, value in specs.get('camera', {}).items():
            print(f"  {key}: {value}")
        
        scraper.close()
        
    except GSMArenaScraperError as e:
        logger.error(f"Scraper error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
