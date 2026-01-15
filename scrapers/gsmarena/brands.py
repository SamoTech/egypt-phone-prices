"""
GSMArena Brand Discovery
Scrapes the list of phone brands from GSMArena.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)

BASE_URL = "https://www.gsmarena.com"
MAKERS_URL = f"{BASE_URL}/makers.php3"

# Top 15 most popular smartphone brands globally (especially for Egyptian market)
PRIORITY_BRANDS = [
    "Samsung",      # #1 Market leader globally
    "Apple",        # #2 Premium segment leader
    "Xiaomi",       # #3 Best value, huge in Egypt
    "Oppo",         # #4 Strong presence in Egypt
    "Vivo",         # #5 Expanding rapidly
    "Realme",       # #6 Growing fast, great value
    "OnePlus",      # #7 Premium flagship killer
    "Huawei",       # #8 Still has strong presence
    "Honor",        # #9 Spin-off from Huawei, growing
    "Motorola",     # #10 Trusted brand
    "Google",       # #11 Pixel phones, pure Android
    "Nokia",        # #12 Classic brand, reliable
    "Infinix",      # #13 Very popular budget brand in Egypt
    "Tecno",        # #14 Popular budget brand in Egypt/Africa
    "Nothing",      # #15 New innovative brand
]

def get_all_brands(priority_only: bool = False) -> List[Dict[str, str]]:
    """
    Fetch all phone brands from GSMArena.
    
    Args:
        priority_only: If True, only return priority brands
        
    Returns:
        List of brand dictionaries with keys: name, url, slug
        
    Example:
        >>> brands = get_all_brands()
        >>> len(brands) > 0
        True
        >>> brands[0]['name']
        'Samsung'
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        logger.info(f"Fetching brands from {MAKERS_URL}")
        response = requests.get(MAKERS_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        brands = []
        
        # Find brand table
        brand_table = soup.find('div', class_='st-text')
        if not brand_table:
            logger.error("Could not find brand table")
            return []
        
        # Find all brand links
        brand_links = brand_table.find_all('a')
        
        for link in brand_links:
            brand_name = link.get_text(strip=True)
            brand_url = link.get('href', '')
            
            if brand_url:
                full_url = f"{BASE_URL}/{brand_url}"
                slug = brand_url.replace('.php', '').replace('-', '_')
                
                brand_dict = {
                    'name': brand_name,
                    'url': full_url,
                    'slug': slug
                }
                
                # Check if priority brand
                if priority_only:
                    if brand_name in PRIORITY_BRANDS:
                        brands.append(brand_dict)
                else:
                    brands.append(brand_dict)
        
        # Sort priority brands first
        if not priority_only:
            brands.sort(key=lambda x: (
                x['name'] not in PRIORITY_BRANDS,
                PRIORITY_BRANDS.index(x['name']) if x['name'] in PRIORITY_BRANDS else 999,
                x['name']
            ))
        else:
            # Sort by priority order
            brands.sort(key=lambda x: PRIORITY_BRANDS.index(x['name']) if x['name'] in PRIORITY_BRANDS else 999)
        
        logger.info(f"Found {len(brands)} brands")
        return brands
        
    except requests.RequestException as e:
        logger.error(f"Error fetching brands: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def get_brand_url(brand_name: str) -> Optional[str]:
    """
    Get the URL for a specific brand.
    
    Args:
        brand_name: Name of the brand
        
    Returns:
        URL for the brand's phone listing page
        
    Example:
        >>> url = get_brand_url("Samsung")
        >>> "samsung" in url.lower()
        True
    """
    brands = get_all_brands()
    
    for brand in brands:
        if brand['name'].lower() == brand_name.lower():
            return brand['url']
    
    return None


def filter_priority_brands(brands: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter to only priority brands.
    
    Args:
        brands: List of all brands
        
    Returns:
        Filtered list of priority brands
    """
    return [b for b in brands if b['name'] in PRIORITY_BRANDS]