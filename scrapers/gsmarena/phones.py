"""
GSMArena Phone Listing Scraper
Scrapes phone lists for each brand with year filtering.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import logging
import time
import re
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://www.gsmarena.com"


def get_phones_for_brand(
    brand_url: str,
    min_year: int = 2023,
    delay: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Fetch all phones for a given brand, filtered by release year.
    
    Args:
        brand_url: URL of the brand's phone listing page
        min_year: Minimum release year (default: 2023)
        delay: Delay between requests in seconds
        
    Returns:
        List of phone dictionaries with keys: name, url, slug, release_year
        
    Example:
        >>> phones = get_phones_for_brand("https://www.gsmarena.com/samsung-phones-9.php")
        >>> len(phones) > 0
        True
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    all_phones = []
    page = 1
    
    try:
        while True:
            # Build URL for pagination
            if page == 1:
                url = brand_url
            else:
                # GSMArena uses format: samsung-phones-f-9-0-p2.php
                base_url = brand_url.replace('.php', '')
                url = f"{base_url}-f-9-0-p{page}.php"
            
            logger.info(f"Fetching page {page} from {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find phone listings
            phone_section = soup.find('div', class_='section-body')
            if not phone_section:
                logger.warning("No phone section found")
                break
            
            phone_list = phone_section.find_all('li')
            
            if not phone_list:
                logger.info(f"No more phones found on page {page}")
                break
            
            page_phones = []
            for phone_item in phone_list:
                try:
                    link = phone_item.find('a')
                    if not link:
                        continue
                    
                    phone_name = link.find('strong')
                    if phone_name:
                        phone_name = phone_name.get_text(strip=True)
                    else:
                        # Fallback to span with class "preview-name"
                        phone_name_span = link.find('span')
                        if phone_name_span:
                            phone_name = phone_name_span.get_text(strip=True)
                        else:
                            continue
                    
                    phone_url = link.get('href', '')
                    if not phone_url:
                        continue
                    
                    full_url = f"{BASE_URL}/{phone_url}"
                    slug = phone_url.replace('.php', '').replace('-', '_')
                    
                    # Extract year from page if available
                    # GSMArena doesn't show year on listing, so we'll extract from detail page later
                    phone_dict = {
                        'name': phone_name,
                        'url': full_url,
                        'slug': slug,
                        'release_year': None  # Will be filled by specs extraction
                    }
                    
                    page_phones.append(phone_dict)
                    logger.debug(f"Found phone: {phone_name}")
                    
                except Exception as e:
                    logger.debug(f"Error parsing phone item: {e}")
                    continue
            
            if not page_phones:
                logger.info("No phones found on this page, stopping")
                break
            
            all_phones.extend(page_phones)
            logger.info(f"Found {len(page_phones)} phones on page {page}")
            
            # Check if there's a next page
            nav_pages = soup.find('div', class_='nav-pages')
            if nav_pages:
                next_link = nav_pages.find('a', class_='prevnextbutton', string='Next page »')
                if not next_link:
                    logger.info("No next page link found")
                    break
            else:
                logger.info("No navigation found, assuming single page")
                break
            
            page += 1
            
            # Rate limiting
            time.sleep(delay)
            
            # Safety limit to avoid infinite loops
            if page > 20:
                logger.warning("Reached maximum page limit (20)")
                break
        
        logger.info(f"Total phones found: {len(all_phones)}")
        return all_phones
        
    except requests.RequestException as e:
        logger.error(f"Error fetching phones: {e}")
        return all_phones
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return all_phones


def filter_phones_by_year(
    phones: List[Dict[str, Any]],
    min_year: int = 2023
) -> List[Dict[str, Any]]:
    """
    Filter phones by minimum release year.
    
    Args:
        phones: List of phone dictionaries
        min_year: Minimum release year
        
    Returns:
        Filtered list of phones
        
    Example:
        >>> phones = [{"name": "Phone A", "release_year": 2024}, {"name": "Phone B", "release_year": 2022}]
        >>> filtered = filter_phones_by_year(phones, 2023)
        >>> len(filtered)
        1
    """
    filtered = []
    
    for phone in phones:
        release_year = phone.get('release_year')
        
        if release_year is None:
            # If year is not set, include it (will be filtered later after specs extraction)
            filtered.append(phone)
        elif isinstance(release_year, int) and release_year >= min_year:
            filtered.append(phone)
        elif isinstance(release_year, str):
            try:
                year_int = int(release_year)
                if year_int >= min_year:
                    filtered.append(phone)
            except ValueError:
                # Can't parse year, include it for now
                filtered.append(phone)
    
    logger.info(f"Filtered {len(filtered)} phones from {len(phones)} (>= {min_year})")
    return filtered


def extract_year_from_name(phone_name: str) -> Optional[int]:
    """
    Try to extract year from phone name.
    
    Args:
        phone_name: Phone name
        
    Returns:
        Year as integer or None
        
    Examples:
        >>> extract_year_from_name("Samsung Galaxy S24")
        2024
        >>> extract_year_from_name("iPhone 15 Pro")
        2023
    """
    # Look for 4-digit years
    year_match = re.search(r'20\d{2}', phone_name)
    if year_match:
        return int(year_match.group())
    
    # Map common model numbers to years (heuristic)
    current_year = datetime.now().year
    
    # Samsung Galaxy S series (S24 = 2024, S23 = 2023, etc.)
    s_series_match = re.search(r'S(\d{2})', phone_name)
    if s_series_match:
        model_num = int(s_series_match.group(1))
        return 2000 + model_num
    
    # iPhone series (15 = 2023, 16 = 2024)
    iphone_match = re.search(r'iPhone (\d{2})', phone_name)
    if iphone_match:
        model_num = int(iphone_match.group(1))
        # iPhone 15 released in 2023
        return 2023 + (model_num - 15)
    
    return None
