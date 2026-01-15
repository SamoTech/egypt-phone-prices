"""
Fuzzy Matching Logic for Phone Products
Provides intelligent matching between search results and target phones.
"""

import re
from typing import Dict, Optional, Tuple
from rapidfuzz import fuzz
from .normalizer import normalize_brand, normalize_model, normalize_storage, normalize_ram


def fuzzy_match_phone(search_result: dict, target_phone: dict) -> float:
    """
    Calculate confidence score (0.0 - 1.0) for match quality.
    
    Scoring weights:
    - Brand match: 30%
    - Model match: 40%
    - Storage match: 20%
    - RAM match: 10%
    
    Args:
        search_result: Dictionary with keys: title, description, etc.
        target_phone: Dictionary with keys: brand, model, storage, ram
        
    Returns:
        Confidence score between 0.0 and 1.0
        
    Examples:
        >>> result = {"title": "Samsung Galaxy S24 Ultra 256GB"}
        >>> phone = {"brand": "Samsung", "model": "Galaxy S24 Ultra", "storage": "256GB"}
        >>> score = fuzzy_match_phone(result, phone)
        >>> score > 0.85
        True
    """
    score = 0.0
    
    # Extract search result text
    search_text = search_result.get('title', '') + ' ' + search_result.get('description', '')
    search_text = search_text.lower()
    
    # Extract target phone details
    target_brand = normalize_brand(target_phone.get('brand', '')).lower()
    target_model = normalize_model(target_phone.get('model', '')).lower()
    target_storage = target_phone.get('storage', '')
    target_ram = target_phone.get('ram', '')
    
    # 1. Brand match (30%)
    if target_brand:
        brand_score = fuzz.partial_ratio(target_brand, search_text) / 100.0
        score += brand_score * 0.30
    
    # 2. Model match (40%) - Most important
    if target_model:
        # Try exact match first
        if target_model in search_text:
            model_score = 1.0
        else:
            # Use fuzzy matching
            model_score = fuzz.token_set_ratio(target_model, search_text) / 100.0
        score += model_score * 0.40
    
    # 3. Storage match (20%)
    if target_storage:
        storage_normalized = normalize_storage(target_storage)
        if storage_normalized:
            extracted_storage = extract_storage_from_text(search_text)
            if extracted_storage:
                if storage_normalized.lower() == extracted_storage.lower():
                    storage_score = 1.0
                else:
                    storage_score = 0.0
            else:
                # Storage not found in text, partial credit
                storage_score = 0.5
            score += storage_score * 0.20
    else:
        # No storage requirement, give full credit
        score += 0.20
    
    # 4. RAM match (10%)
    if target_ram:
        ram_normalized = normalize_ram(target_ram)
        if ram_normalized:
            extracted_ram = extract_ram_from_text(search_text)
            if extracted_ram:
                if ram_normalized.lower() == extracted_ram.lower():
                    ram_score = 1.0
                else:
                    ram_score = 0.0
            else:
                # RAM not found in text, partial credit
                ram_score = 0.5
            score += ram_score * 0.10
    else:
        # No RAM requirement, give full credit
        score += 0.10
    
    return min(score, 1.0)


def extract_storage_from_text(text: str) -> Optional[str]:
    """
    Extract storage capacity from product title/description.
    
    Args:
        text: Product text to search
        
    Returns:
        Normalized storage string (e.g., "256GB") or None
        
    Examples:
        >>> extract_storage_from_text("Samsung Galaxy S24 256GB")
        '256GB'
        >>> extract_storage_from_text("iPhone with 1TB storage")
        '1TB'
        >>> extract_storage_from_text("Phone case")
        None
    """
    text = text.upper()
    
    # Pattern for TB
    tb_match = re.search(r'(\d+)\s*TB', text)
    if tb_match:
        return f"{tb_match.group(1)}TB"
    
    # Pattern for GB (more common)
    gb_match = re.search(r'(\d+)\s*GB?\b', text)
    if gb_match:
        capacity = int(gb_match.group(1))
        # Filter out likely RAM values (typically 2-24 GB)
        # Storage is usually 32GB and above
        if capacity >= 32 or capacity in [8, 16]:  # Include 8GB and 16GB as possible storage
            return f"{capacity}GB"
    
    return None


def extract_ram_from_text(text: str) -> Optional[str]:
    """
    Extract RAM capacity from product title/description.
    
    Args:
        text: Product text to search
        
    Returns:
        Normalized RAM string (e.g., "12GB") or None
        
    Examples:
        >>> extract_ram_from_text("Samsung Galaxy S24 12GB RAM")
        '12GB'
        >>> extract_ram_from_text("iPhone 15 with 8GB memory")
        '8GB'
    """
    text = text.upper()
    
    # Look for explicit RAM indicators
    ram_patterns = [
        r'(\d+)\s*GB\s+RAM',
        r'RAM\s+(\d+)\s*GB',
        r'(\d+)\s*GB\s+MEMORY',
        r'MEMORY\s+(\d+)\s*GB',
    ]
    
    for pattern in ram_patterns:
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}GB"
    
    # Look for format like "12GB/256GB" where first is likely RAM
    combo_match = re.search(r'(\d+)\s*GB?\s*/\s*(\d+)\s*GB?', text)
    if combo_match:
        ram_value = int(combo_match.group(1))
        storage_value = int(combo_match.group(2))
        # RAM is typically smaller than storage
        if ram_value < storage_value and ram_value <= 24:
            return f"{ram_value}GB"
    
    return None


def calculate_variant_match_score(
    extracted_storage: Optional[str],
    extracted_ram: Optional[str],
    target_storage: str,
    target_ram: Optional[str] = None
) -> float:
    """
    Calculate how well extracted specs match target variant.
    
    Args:
        extracted_storage: Storage found in product text
        extracted_ram: RAM found in product text
        target_storage: Expected storage
        target_ram: Expected RAM (optional)
        
    Returns:
        Match score between 0.0 and 1.0
    """
    score = 0.0
    weights_used = 0.0
    
    # Storage match (weight: 0.7)
    storage_weight = 0.7
    weights_used += storage_weight
    
    if extracted_storage and target_storage:
        storage_norm_extracted = normalize_storage(extracted_storage)
        storage_norm_target = normalize_storage(target_storage)
        
        if storage_norm_extracted == storage_norm_target:
            score += storage_weight
    
    # RAM match (weight: 0.3)
    if target_ram:
        ram_weight = 0.3
        weights_used += ram_weight
        
        if extracted_ram:
            ram_norm_extracted = normalize_ram(extracted_ram)
            ram_norm_target = normalize_ram(target_ram)
            
            if ram_norm_extracted == ram_norm_target:
                score += ram_weight
    
    # Normalize score
    if weights_used > 0:
        return score / weights_used
    
    return 0.0


def extract_price_from_text(text: str) -> Optional[float]:
    """
    Extract price from text string.
    
    Args:
        text: Text containing price
        
    Returns:
        Price as float or None
        
    Examples:
        >>> extract_price_from_text("EGP 15,999")
        15999.0
        >>> extract_price_from_text("Price: 32999 EGP")
        32999.0
    """
    # Remove common currency symbols and text
    text = text.replace('EGP', '').replace('LE', '').replace('E£', '')
    text = text.replace('جنيه', '').replace('ج.م', '')
    
    # Find numbers with optional comma separators
    match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
    if match:
        price_str = match.group(1).replace(',', '')
        try:
            return float(price_str)
        except ValueError:
            pass
    
    return None
