"""
Product Validation Logic
Validates product offers against target phone specifications.
"""

import re
from typing import Tuple, Optional, Dict, Any
from .matcher import extract_storage_from_text, extract_ram_from_text, extract_price_from_text
from .normalizer import normalize_storage, normalize_ram


# Keywords for accessory detection
ACCESSORY_KEYWORDS = [
    "case", "cover", "cable", "charger", "screen protector", 
    "tempered glass", "adapter", "holder", "stand", "mount",
    "earphone", "headphone", "headset", "earbuds", "airpods",
    "power bank", "battery pack", "car charger", "wall charger",
    "usb", "otg", "stylus", "pen", "grip", "ring",
    "skin", "sticker", "protector", "film", "guard",
    # Arabic keywords
    "جراب", "كفر", "واقي", "شاحن", "كابل", "سماعة"
]

# Keywords for refurbished/used detection
REFURBISHED_KEYWORDS = [
    "refurbished", "used", "open box", "pre-owned", "second hand",
    "renewed", "reconditioned", "like new", "pre owned",
    # Arabic keywords
    "مستعمل", "مجدد", "مستورد", "مفتوح"
]


def validate_offer(
    offer: dict, 
    phone_specs: dict, 
    variant: dict,
    allow_refurbished: bool = False
) -> Tuple[bool, str]:
    """
    Validate product offer against phone specifications.
    
    Returns (is_valid, rejection_reason)
    
    Args:
        offer: Product offer with title, description, price
        phone_specs: Target phone specifications
        variant: Target variant (storage, RAM)
        allow_refurbished: Whether to allow refurbished phones
        
    Returns:
        Tuple of (is_valid: bool, rejection_reason: str)
        
    Examples:
        >>> offer = {"title": "Samsung Galaxy S24 256GB", "price": 32000}
        >>> specs = {"brand": "Samsung", "model": "Galaxy S24"}
        >>> variant = {"storage": "256GB"}
        >>> validate_offer(offer, specs, variant)
        (True, '')
    """
    title = offer.get('title', '').lower()
    description = offer.get('description', '').lower()
    price = offer.get('price', 0)
    full_text = f"{title} {description}"
    
    # Check 1: Not an accessory
    if is_accessory(full_text):
        return False, "Product is an accessory, not a phone"
    
    # Check 2: Not refurbished (unless allowed)
    if not allow_refurbished and is_refurbished(full_text):
        return False, "Product is refurbished/used"
    
    # Check 3: Validate storage variant
    target_storage = variant.get('storage')
    if target_storage:
        extracted_storage = extract_storage_from_text(full_text)
        if extracted_storage:
            storage_norm_extracted = normalize_storage(extracted_storage)
            storage_norm_target = normalize_storage(target_storage)
            
            if storage_norm_extracted != storage_norm_target:
                return False, f"Storage mismatch: found {storage_norm_extracted}, expected {storage_norm_target}"
    
    # Check 4: Validate RAM variant (if specified)
    target_ram = variant.get('ram')
    if target_ram:
        extracted_ram = extract_ram_from_text(full_text)
        if extracted_ram:
            ram_norm_extracted = normalize_ram(extracted_ram)
            ram_norm_target = normalize_ram(target_ram)
            
            if ram_norm_extracted != ram_norm_target:
                return False, f"RAM mismatch: found {ram_norm_extracted}, expected {ram_norm_target}"
    
    # Check 5: Price within reasonable range (not outliers)
    if price > 0:
        # Phones typically range from 2,000 EGP to 100,000 EGP
        if price < 2000:
            return False, f"Price too low ({price} EGP) - likely not a phone"
        if price > 100000:
            return False, f"Price too high ({price} EGP) - likely an error"
    else:
        return False, "No valid price found"
    
    # All checks passed
    return True, ""


def is_accessory(text: str) -> bool:
    """
    Detect if product is an accessory, not a phone.
    
    Args:
        text: Product title/description
        
    Returns:
        True if product is an accessory
        
    Examples:
        >>> is_accessory("Samsung Galaxy S24 Case")
        True
        >>> is_accessory("Samsung Galaxy S24 256GB")
        False
    """
    text_lower = text.lower()
    
    # Check for accessory keywords
    for keyword in ACCESSORY_KEYWORDS:
        if keyword in text_lower:
            # Additional check: ensure it's not just mentioning "with case" or "includes charger"
            # Look for patterns that indicate it's ONLY an accessory
            if re.search(rf'\b{re.escape(keyword)}\b', text_lower):
                # Check if phone model is also present
                phone_indicators = ["phone", "smartphone", "mobile", "هاتف", "موبايل"]
                has_phone_indicator = any(indicator in text_lower for indicator in phone_indicators)
                
                # If it's described as a phone AND mentions accessory, it's probably a bundle
                # If it's ONLY accessory, reject it
                if not has_phone_indicator or text_lower.startswith(keyword):
                    return True
    
    return False


def is_refurbished(text: str) -> bool:
    """
    Detect if product is refurbished/used.
    
    Args:
        text: Product title/description
        
    Returns:
        True if product is refurbished/used
        
    Examples:
        >>> is_refurbished("Samsung Galaxy S24 Refurbished")
        True
        >>> is_refurbished("Samsung Galaxy S24 Brand New")
        False
    """
    text_lower = text.lower()
    
    for keyword in REFURBISHED_KEYWORDS:
        if keyword in text_lower:
            return True
    
    return False


def validate_price_range(
    price: float,
    similar_prices: list,
    max_deviation: float = 0.5
) -> Tuple[bool, str]:
    """
    Validate that price is not an outlier compared to similar offers.
    
    Args:
        price: Price to validate
        similar_prices: List of similar product prices
        max_deviation: Maximum allowed deviation from median (0.5 = 50%)
        
    Returns:
        Tuple of (is_valid: bool, reason: str)
        
    Examples:
        >>> validate_price_range(30000, [29000, 31000, 30500])
        (True, '')
        >>> validate_price_range(50000, [29000, 31000, 30500])
        (False, 'Price is outlier: 66.7% above median')
    """
    if not similar_prices or len(similar_prices) < 2:
        # Not enough data to validate
        return True, ""
    
    # Calculate median
    sorted_prices = sorted(similar_prices)
    n = len(sorted_prices)
    if n % 2 == 0:
        median = (sorted_prices[n//2 - 1] + sorted_prices[n//2]) / 2
    else:
        median = sorted_prices[n//2]
    
    # Calculate deviation
    if median > 0:
        deviation = abs(price - median) / median
        
        if deviation > max_deviation:
            direction = "above" if price > median else "below"
            return False, f"Price is outlier: {deviation*100:.1f}% {direction} median"
    
    return True, ""


def extract_seller_info(offer: dict) -> Dict[str, Any]:
    """
    Extract seller information from offer.
    
    Args:
        offer: Product offer
        
    Returns:
        Dictionary with seller info
    """
    return {
        'seller': offer.get('seller', 'Unknown'),
        'rating': offer.get('rating'),
        'reviews': offer.get('reviews'),
        'verified': offer.get('verified', False)
    }


def calculate_offer_quality_score(offer: dict) -> float:
    """
    Calculate overall quality score for an offer.
    
    Considers:
    - Seller rating
    - Number of reviews
    - Verified seller status
    - Availability
    
    Args:
        offer: Product offer
        
    Returns:
        Quality score between 0.0 and 1.0
    """
    score = 0.5  # Base score
    
    # Seller rating (max +0.2)
    rating = offer.get('rating', 0)
    if rating >= 4.5:
        score += 0.2
    elif rating >= 4.0:
        score += 0.15
    elif rating >= 3.5:
        score += 0.1
    
    # Number of reviews (max +0.15)
    reviews = offer.get('reviews', 0)
    if reviews >= 100:
        score += 0.15
    elif reviews >= 50:
        score += 0.10
    elif reviews >= 10:
        score += 0.05
    
    # Verified seller (max +0.1)
    if offer.get('verified'):
        score += 0.1
    
    # In stock (max +0.05)
    if offer.get('availability') == 'in_stock':
        score += 0.05
    
    return min(score, 1.0)
