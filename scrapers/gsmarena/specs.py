"""
GSMArena Detailed Specifications Extractor
Extracts comprehensive phone specifications from individual phone pages.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_URL = "https://www.gsmarena.com"


def extract_phone_specs(phone_url: str, delay: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Extract detailed specifications from a phone's detail page.
    
    Args:
        phone_url: URL of the phone's detail page
        delay: Delay before making request (for rate limiting)
        
    Returns:
        Dictionary with normalized phone specifications
        
    Example:
        >>> specs = extract_phone_specs("https://www.gsmarena.com/samsung_galaxy_s24_ultra-12771.php")
        >>> specs['brand']
        'Samsung'
    """
    import time
    time.sleep(delay)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        logger.info(f"Extracting specs from {phone_url}")
        response = requests.get(phone_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract phone name and brand
        title_element = soup.find('h1', class_='specs-phone-name-title')
        if not title_element:
            logger.error("Could not find phone title")
            return None
        
        phone_name = title_element.get_text(strip=True)
        brand, model = parse_phone_name(phone_name)
        
        # Extract slug from URL
        slug = phone_url.split('/')[-1].replace('.php', '').replace('-', '_')
        
        # Initialize specs dictionary
        specs = {
            'brand': brand,
            'model': model,
            'slug': slug,
            'release_year': None,
            'release_date': None,
            'display': {},
            'chipset': None,
            'ram_options': [],
            'storage_options': [],
            'battery': None,
            'camera_main': None,
            'camera_front': None,
            'os': None,
            '5g': False,
            'gsmarena_url': phone_url,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Extract specifications from table
        spec_table = soup.find('div', id='specs-list')
        if spec_table:
            specs_dict = parse_spec_table(spec_table)
            
            # Parse release date and year
            launch_info = specs_dict.get('Launch', {})
            announced = launch_info.get('Announced', '')
            status = launch_info.get('Status', '')
            
            release_year = extract_year(announced or status)
            if release_year:
                specs['release_year'] = release_year
            
            # Try to extract full date
            release_date = extract_date(announced or status)
            if release_date:
                specs['release_date'] = release_date
            
            # Parse display information
            display_info = specs_dict.get('Display', {})
            if display_info:
                specs['display'] = parse_display_specs(display_info)
            
            # Parse platform (chipset, OS)
            platform_info = specs_dict.get('Platform', {})
            if platform_info:
                specs['chipset'] = platform_info.get('Chipset', '').strip()
                specs['os'] = platform_info.get('OS', '').strip()
            
            # Parse memory
            memory_info = specs_dict.get('Memory', {})
            if memory_info:
                ram_storage = parse_memory_specs(memory_info)
                specs['ram_options'] = ram_storage.get('ram_options', [])
                specs['storage_options'] = ram_storage.get('storage_options', [])
            
            # Parse battery
            battery_info = specs_dict.get('Battery', {})
            if battery_info:
                battery_capacity = extract_battery_capacity(battery_info)
                if battery_capacity:
                    specs['battery'] = battery_capacity
            
            # Parse camera
            main_camera_info = specs_dict.get('Main Camera', {})
            if main_camera_info:
                specs['camera_main'] = parse_camera_specs(main_camera_info)
            
            selfie_camera_info = specs_dict.get('Selfie camera', {})
            if selfie_camera_info:
                specs['camera_front'] = parse_camera_specs(selfie_camera_info)
            
            # Check for 5G support
            network_info = specs_dict.get('Network', {})
            if network_info:
                specs['5g'] = check_5g_support(network_info)
        
        logger.info(f"Successfully extracted specs for {phone_name}")
        return specs
        
    except requests.RequestException as e:
        logger.error(f"Error fetching specs: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting specs: {e}", exc_info=True)
        return None


def parse_spec_table(spec_table_element) -> Dict[str, Dict[str, str]]:
    """
    Parse GSMArena specification table into structured dictionary.
    
    Args:
        spec_table_element: BeautifulSoup element containing specs
        
    Returns:
        Nested dictionary: {category: {attribute: value}}
    """
    specs = {}
    
    # Find all specification categories
    tables = spec_table_element.find_all('table')
    
    for table in tables:
        # Get category name
        category_header = table.find_previous('th')
        if not category_header:
            continue
        
        category_name = category_header.get_text(strip=True)
        category_specs = {}
        
        # Parse rows in this category
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                attr_name = cells[0].get_text(strip=True)
                attr_value = cells[1].get_text(strip=True)
                category_specs[attr_name] = attr_value
        
        if category_specs:
            specs[category_name] = category_specs
    
    return specs


def parse_phone_name(full_name: str) -> tuple:
    """
    Split phone name into brand and model.
    
    Args:
        full_name: Full phone name (e.g., "Samsung Galaxy S24 Ultra")
        
    Returns:
        Tuple of (brand, model)
    """
    parts = full_name.split(None, 1)
    if len(parts) >= 2:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], parts[0]
    else:
        return "Unknown", full_name


def parse_display_specs(display_info: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse display specifications.
    
    Args:
        display_info: Dictionary with display attributes
        
    Returns:
        Normalized display specs
    """
    display = {}
    
    # Extract size
    size_text = display_info.get('Size', '')
    size_match = re.search(r'(\d+\.?\d*)\s*inches', size_text)
    if size_match:
        display['size'] = float(size_match.group(1))
    
    # Extract type
    type_text = display_info.get('Type', '')
    if type_text:
        display['type'] = type_text.split(',')[0].strip()
    
    # Extract refresh rate
    refresh_match = re.search(r'(\d+)Hz', type_text + ' ' + size_text)
    if refresh_match:
        display['refresh_rate'] = int(refresh_match.group(1))
    
    # Extract resolution
    resolution_text = display_info.get('Resolution', '')
    resolution_match = re.search(r'(\d+)x(\d+)', resolution_text)
    if resolution_match:
        display['resolution'] = f"{resolution_match.group(1)}x{resolution_match.group(2)}"
    
    return display


def parse_memory_specs(memory_info: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Parse memory (RAM and storage) specifications.
    
    Args:
        memory_info: Dictionary with memory attributes
        
    Returns:
        Dictionary with ram_options and storage_options
    """
    result = {
        'ram_options': [],
        'storage_options': []
    }
    
    # Look for internal memory specification
    internal = memory_info.get('Internal', '')
    card_slot = memory_info.get('Card slot', '')
    
    # Common formats:
    # "128GB 6GB RAM, 256GB 8GB RAM"
    # "256GB 8GB RAM"
    # "12GB RAM"
    
    ram_set = set()
    storage_set = set()
    
    # Find all RAM values
    ram_matches = re.findall(r'(\d+)GB\s+RAM', internal)
    for ram in ram_matches:
        ram_set.add(f"{ram}GB")
    
    # Find all storage values
    storage_matches = re.findall(r'(\d+)GB\s+\d+GB\s+RAM', internal)
    for storage in storage_matches:
        storage_set.add(f"{storage}GB")
    
    # Also check for TB
    storage_tb_matches = re.findall(r'(\d+)TB', internal)
    for storage in storage_tb_matches:
        storage_set.add(f"{storage}TB")
    
    result['ram_options'] = sorted(list(ram_set))
    result['storage_options'] = sorted(list(storage_set))
    
    return result


def extract_battery_capacity(battery_info: Dict[str, str]) -> Optional[int]:
    """
    Extract battery capacity in mAh.
    
    Args:
        battery_info: Dictionary with battery attributes
        
    Returns:
        Battery capacity in mAh
    """
    battery_text = battery_info.get('Type', '') or battery_info.get('', '')
    
    # Look for mAh value
    match = re.search(r'(\d+)\s*mAh', battery_text)
    if match:
        return int(match.group(1))
    
    return None


def parse_camera_specs(camera_info: Dict[str, str]) -> Optional[str]:
    """
    Parse camera specifications to extract main sensor info.
    
    Args:
        camera_info: Dictionary with camera attributes
        
    Returns:
        Main camera spec (e.g., "200MP" or "12MP + 10MP + 10MP")
    """
    # Look for camera details in various fields
    for key in ['Single', 'Dual', 'Triple', 'Quad', 'Multiple', '']:
        if key in camera_info:
            camera_text = camera_info[key]
            # Extract megapixels
            mp_match = re.search(r'(\d+)\s*MP', camera_text)
            if mp_match:
                return f"{mp_match.group(1)}MP"
    
    return None


def check_5g_support(network_info: Dict[str, str]) -> bool:
    """
    Check if phone supports 5G.
    
    Args:
        network_info: Dictionary with network attributes
        
    Returns:
        True if 5G is supported
    """
    for key, value in network_info.items():
        if '5G' in value.upper():
            return True
    
    return False


def extract_year(text: str) -> Optional[int]:
    """
    Extract year from text.
    
    Args:
        text: Text containing year
        
    Returns:
        Year as integer
    """
    match = re.search(r'20\d{2}', text)
    if match:
        return int(match.group())
    
    return None


def extract_date(text: str) -> Optional[str]:
    """
    Extract date from text and normalize to YYYY-MM-DD format.
    
    Args:
        text: Text containing date
        
    Returns:
        Date in YYYY-MM-DD format
    """
    # Common formats: "2024, January 25", "Released 2023, September"
    
    # Try full date
    match = re.search(r'(\d{4}),?\s+([A-Za-z]+)\s+(\d{1,2})', text)
    if match:
        year = match.group(1)
        month_name = match.group(2)
        day = match.group(3).zfill(2)
        
        # Convert month name to number
        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        
        month = month_map.get(month_name, '01')
        return f"{year}-{month}-{day}"
    
    # Try year and month only
    match = re.search(r'(\d{4}),?\s+([A-Za-z]+)', text)
    if match:
        year = match.group(1)
        month_name = match.group(2)
        
        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        
        month = month_map.get(month_name, '01')
        return f"{year}-{month}-01"
    
    return None
