"""
Brand and Model Normalization
Standardizes brand names, model names, and creates URL-safe slugs.
"""

import re
from typing import Optional


# Comprehensive brand mapping for normalization
BRAND_MAP = {
    "samsung": "Samsung",
    "apple": "Apple",
    "xiaomi": "Xiaomi",
    "oppo": "Oppo",
    "realme": "Realme",
    "oneplus": "OnePlus",
    "one plus": "OnePlus",
    "google": "Google",
    "motorola": "Motorola",
    "moto": "Motorola",
    "nokia": "Nokia",
    "vivo": "Vivo",
    "huawei": "Huawei",
    "honor": "Honor",
    "infinix": "Infinix",
    "tecno": "Tecno",
    "itel": "Itel",
    "lenovo": "Lenovo",
    "asus": "Asus",
    "sony": "Sony",
    "lg": "LG",
    "htc": "HTC",
    "alcatel": "Alcatel",
    "zte": "ZTE",
    "meizu": "Meizu",
    "nothing": "Nothing",
}


def normalize_brand(brand: str) -> str:
    """
    Standardize brand names to consistent format.
    
    Args:
        brand: Raw brand name (e.g., "SAMSUNG", "apple", "One Plus")
        
    Returns:
        Standardized brand name (e.g., "Samsung", "Apple", "OnePlus")
        
    Examples:
        >>> normalize_brand("SAMSUNG")
        'Samsung'
        >>> normalize_brand("one plus")
        'OnePlus'
        >>> normalize_brand("Unknown Brand")
        'Unknown Brand'
    """
    if not brand:
        return ""
    
    # Clean and normalize
    brand_clean = brand.strip().lower()
    
    # Remove extra whitespace
    brand_clean = re.sub(r'\s+', ' ', brand_clean)
    
    # Look up in mapping
    if brand_clean in BRAND_MAP:
        return BRAND_MAP[brand_clean]
    
    # If not found, return title case
    return brand.strip().title()


def normalize_model(model: str) -> str:
    """
    Standardize model names by removing extra spaces and normalizing format.
    
    Args:
        model: Raw model name
        
    Returns:
        Normalized model name
        
    Examples:
        >>> normalize_model("Galaxy  S24   Ultra")
        'Galaxy S24 Ultra'
        >>> normalize_model("  iPhone 15 Pro Max  ")
        'iPhone 15 Pro Max'
    """
    if not model:
        return ""
    
    # Remove extra whitespace
    model_clean = re.sub(r'\s+', ' ', model.strip())
    
    return model_clean


def create_slug(brand: str, model: str) -> str:
    """
    Generate URL-safe slug from brand and model.
    
    Args:
        brand: Phone brand
        model: Phone model
        
    Returns:
        URL-safe slug
        
    Examples:
        >>> create_slug("Samsung", "Galaxy S24 Ultra")
        'samsung_galaxy_s24_ultra'
        >>> create_slug("Apple", "iPhone 15 Pro Max")
        'apple_iphone_15_pro_max'
        >>> create_slug("OnePlus", "12R")
        'oneplus_12r'
    """
    # Combine brand and model
    combined = f"{brand} {model}".lower()
    
    # Remove special characters, keep alphanumeric and spaces
    cleaned = re.sub(r'[^a-z0-9\s]', '', combined)
    
    # Replace spaces with underscores
    slug = re.sub(r'\s+', '_', cleaned.strip())
    
    # Remove consecutive underscores
    slug = re.sub(r'_+', '_', slug)
    
    return slug


def normalize_storage(storage: str) -> Optional[str]:
    """
    Normalize storage capacity to consistent format.
    
    Args:
        storage: Raw storage string (e.g., "256 GB", "512G", "1TB")
        
    Returns:
        Normalized storage (e.g., "256GB", "512GB", "1TB")
        
    Examples:
        >>> normalize_storage("256 GB")
        '256GB'
        >>> normalize_storage("1 TB")
        '1TB'
        >>> normalize_storage("512G")
        '512GB'
    """
    if not storage:
        return None
    
    storage_clean = storage.upper().replace(" ", "")
    
    # Handle various formats
    if "TB" in storage_clean:
        # Already has TB
        return re.sub(r'(\d+).*TB.*', r'\1TB', storage_clean)
    elif "GB" in storage_clean:
        # Already has GB
        return re.sub(r'(\d+).*GB.*', r'\1GB', storage_clean)
    elif "G" in storage_clean:
        # Just "G" without "B"
        return storage_clean.replace("G", "GB")
    
    # Try to extract number and assume GB
    match = re.search(r'(\d+)', storage_clean)
    if match:
        return f"{match.group(1)}GB"
    
    return None


def normalize_ram(ram: str) -> Optional[str]:
    """
    Normalize RAM capacity to consistent format.
    
    Args:
        ram: Raw RAM string (e.g., "12 GB", "8G", "16GB")
        
    Returns:
        Normalized RAM (e.g., "12GB", "8GB", "16GB")
        
    Examples:
        >>> normalize_ram("12 GB")
        '12GB'
        >>> normalize_ram("8G")
        '8GB'
    """
    if not ram:
        return None
    
    ram_clean = ram.upper().replace(" ", "")
    
    # Handle various formats
    if "GB" in ram_clean:
        return re.sub(r'(\d+).*GB.*', r'\1GB', ram_clean)
    elif "G" in ram_clean:
        return ram_clean.replace("G", "GB")
    
    # Try to extract number and assume GB
    match = re.search(r'(\d+)', ram_clean)
    if match:
        return f"{match.group(1)}GB"
    
    return None
