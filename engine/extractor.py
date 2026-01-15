"""
Text-Based Extraction Engine
Extracts prices, specifications, and product information from raw text.
Uses regex patterns, keyword matching, and heuristic rules.
NO DOM parsing or HTML manipulation.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime


def extract_prices_from_text(text: str, currency: str = "EGP") -> List[Dict[str, Any]]:
    """
    Extract price mentions from raw text using regex patterns.
    
    Args:
        text: Raw text content
        currency: Expected currency (default: "EGP")
        
    Returns:
        List of price mentions with context
        
    Examples:
        >>> extract_prices_from_text("Samsung Galaxy S23 costs 32,999 EGP at Amazon")
        [{'price': 32999.0, 'currency': 'EGP', 'context': '...', 'position': 25}]
    """
    prices = []
    
    # Currency patterns (Egyptian Pound variations)
    currency_patterns = [
        r'EGP',
        r'LE',
        r'E£',
        r'جنيه',
        r'ج\.م',
        r'pound',
    ]
    
    # Build regex pattern for prices
    # Matches: 32,999 EGP, EGP 32999, LE 32,999.00, etc.
    currency_regex = '|'.join(currency_patterns)
    
    # Pattern 1: Currency followed by number
    pattern1 = rf'(?:{currency_regex})\s*(\d{{1,3}}(?:,\d{{3}})*(?:\.\d{{2}})?)'
    
    # Pattern 2: Number followed by currency
    pattern2 = rf'(\d{{1,3}}(?:,\d{{3}})*(?:\.\d{{2}})?)\s*(?:{currency_regex})'
    
    # Pattern 3: Standalone numbers that look like prices (4-6 digits, with optional commas)
    pattern3 = r'\b(\d{4,6})\b'
    
    # Find all matches
    for pattern in [pattern1, pattern2]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            price_str = match.group(1).replace(',', '')
            try:
                price = float(price_str)
                
                # Filter reasonable phone prices (2,000 to 100,000 EGP)
                if 2000 <= price <= 100000:
                    # Extract context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    prices.append({
                        'price': price,
                        'currency': currency,
                        'context': context,
                        'position': match.start(),
                        'confidence': 0.8  # High confidence with explicit currency
                    })
            except ValueError:
                continue
    
    # Pattern 3: Look for standalone numbers in price-like contexts
    price_context_keywords = ['price', 'cost', 'costs', 'سعر', 'buy', 'sale', 'offer']
    for match in re.finditer(pattern3, text, re.IGNORECASE):
        price_str = match.group(1)
        try:
            price = float(price_str)
            
            if 2000 <= price <= 100000:
                # Check if there's a price keyword nearby
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].lower()
                
                if any(keyword in context for keyword in price_context_keywords):
                    prices.append({
                        'price': price,
                        'currency': currency,
                        'context': text[start:end].strip(),
                        'position': match.start(),
                        'confidence': 0.5  # Lower confidence without explicit currency
                    })
        except ValueError:
            continue
    
    # Remove duplicates (same price at similar positions)
    unique_prices = []
    for p in prices:
        is_duplicate = False
        for existing in unique_prices:
            if abs(p['price'] - existing['price']) < 10 and abs(p['position'] - existing['position']) < 100:
                is_duplicate = True
                # Keep the one with higher confidence
                if p['confidence'] > existing['confidence']:
                    unique_prices.remove(existing)
                    unique_prices.append(p)
                break
        if not is_duplicate:
            unique_prices.append(p)
    
    # Sort by position in text
    unique_prices.sort(key=lambda x: x['position'])
    
    return unique_prices


def extract_storage_capacity(text: str) -> Optional[str]:
    """
    Extract storage capacity from text.
    
    Args:
        text: Text to search
        
    Returns:
        Normalized storage string or None
        
    Examples:
        >>> extract_storage_capacity("Samsung Galaxy S23 256GB")
        '256GB'
    """
    text = text.upper()
    
    # Pattern for TB
    tb_match = re.search(r'(\d+)\s*TB\b', text)
    if tb_match:
        return f"{tb_match.group(1)}TB"
    
    # Pattern for GB (more common)
    gb_match = re.search(r'(\d+)\s*GB\b', text)
    if gb_match:
        capacity = int(gb_match.group(1))
        # Filter out likely RAM values
        # Storage is usually 32GB and above (or 8GB, 16GB for older devices)
        if capacity >= 32 or capacity in [8, 16]:
            return f"{capacity}GB"
    
    return None


def extract_ram_capacity(text: str) -> Optional[str]:
    """
    Extract RAM capacity from text.
    
    Args:
        text: Text to search
        
    Returns:
        Normalized RAM string or None
        
    Examples:
        >>> extract_ram_capacity("Samsung Galaxy S23 8GB RAM")
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
            ram_value = int(match.group(1))
            if ram_value <= 24:  # RAM typically 1-24GB
                return f"{ram_value}GB"
    
    # Look for format like "12GB/256GB" where first is likely RAM
    combo_match = re.search(r'(\d+)\s*GB?\s*/\s*(\d+)\s*GB?', text)
    if combo_match:
        ram_value = int(combo_match.group(1))
        storage_value = int(combo_match.group(2))
        # RAM is typically smaller than storage
        if ram_value < storage_value and ram_value <= 24:
            return f"{ram_value}GB"
    
    return None


def extract_phone_mentions(text: str, target_brand: str = None, target_model: str = None) -> List[Dict[str, Any]]:
    """
    Extract phone model mentions from text.
    
    Args:
        text: Raw text to search
        target_brand: Optional brand to focus on
        target_model: Optional model to focus on
        
    Returns:
        List of phone mentions with context
        
    Examples:
        >>> extract_phone_mentions("Samsung Galaxy S23 is available", "Samsung", "Galaxy S23")
        [{'brand': 'Samsung', 'model': 'Galaxy S23', 'context': '...', 'position': 0}]
    """
    mentions = []
    
    # Common brand patterns
    brands = [
        "Samsung", "Apple", "Xiaomi", "Oppo", "Realme", "OnePlus",
        "Google", "Motorola", "Nokia", "Vivo", "Infinix", "Tecno"
    ]
    
    # If target brand specified, prioritize it
    if target_brand:
        brands = [target_brand] + [b for b in brands if b != target_brand]
    
    for brand in brands[:5]:  # Check top 5 brands
        # Look for brand mentions
        pattern = rf'\b{re.escape(brand)}\b'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Extract surrounding context
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            # Try to extract model name (next few words after brand)
            model_text = text[match.end():match.end() + 50]
            model_match = re.search(r'([A-Z]\w+(?:\s+[A-Z0-9]\w*)*)', model_text)
            
            model = model_match.group(1).strip() if model_match else ""
            
            mentions.append({
                'brand': brand,
                'model': model,
                'context': context.strip(),
                'position': match.start(),
                'confidence': 0.7
            })
    
    return mentions


def extract_store_names(text: str) -> List[str]:
    """
    Extract store/seller names from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of store names found
        
    Examples:
        >>> extract_store_names("Available at Amazon Egypt and Noon")
        ['Amazon', 'Noon']
    """
    stores = []
    
    # Egyptian store patterns
    store_patterns = {
        'amazon': r'\b(Amazon|amazon\.eg)\b',
        'noon': r'\b(Noon|noon\.com)\b',
        'jumia': r'\b(Jumia|jumia\.com\.eg)\b',
        'btech': r'\b(B\.?Tech|btech\.com)\b',
        'souq': r'\b(Souq)\b',
        '2b': r'\b(2B|twob)\b',
    }
    
    for store_key, pattern in store_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            stores.append(store_key.title())
    
    return stores


def extract_product_conditions(text: str) -> Dict[str, bool]:
    """
    Extract product condition indicators from text.
    
    Args:
        text: Text to search
        
    Returns:
        Dictionary with condition flags
        
    Examples:
        >>> extract_product_conditions("Brand new Samsung phone with warranty")
        {'is_new': True, 'has_warranty': True, 'is_refurbished': False, 'is_used': False}
    """
    text_lower = text.lower()
    
    return {
        'is_new': any(k in text_lower for k in ['new', 'brand new', 'جديد']),
        'has_warranty': any(k in text_lower for k in ['warranty', 'ضمان', 'guarantee']),
        'is_refurbished': any(k in text_lower for k in ['refurbished', 'renewed', 'مجدد']),
        'is_used': any(k in text_lower for k in ['used', 'second hand', 'مستعمل', 'pre-owned']),
        'is_official': any(k in text_lower for k in ['official', 'authorized', 'رسمي']),
    }


def extract_structured_data(text: str) -> Dict[str, Any]:
    """
    Attempt to extract structured data patterns from text.
    Looks for JSON-LD, microdata, or structured text patterns.
    
    Args:
        text: Raw text that might contain structured data
        
    Returns:
        Extracted structured data
        
    Examples:
        >>> extract_structured_data('{"price": 32999, "name": "Samsung Galaxy S23"}')
        {'price': 32999, 'name': 'Samsung Galaxy S23'}
    """
    import json
    
    structured = {}
    
    # Try to find JSON-LD blocks
    json_pattern = r'\{[^{}]*"@type"\s*:\s*"Product"[^{}]*\}'
    matches = re.finditer(json_pattern, text, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        try:
            data = json.loads(match.group(0))
            if 'price' in data or 'offers' in data:
                structured['json_ld'] = data
                break
        except json.JSONDecodeError:
            continue
    
    # Look for key-value patterns
    kv_patterns = {
        'price': r'(?:price|سعر)\s*:?\s*(\d{4,6})',
        'model': r'(?:model|موديل)\s*:?\s*([A-Z][A-Za-z0-9\s]+)',
        'storage': r'(?:storage|ذاكرة)\s*:?\s*(\d+\s*GB)',
    }
    
    for key, pattern in kv_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            structured[key] = match.group(1).strip()
    
    return structured


def calculate_extraction_confidence(
    text: str,
    price_found: bool,
    model_found: bool,
    storage_found: bool,
    store_found: bool
) -> float:
    """
    Calculate confidence score for extracted data.
    
    Args:
        text: Source text
        price_found: Whether price was found
        model_found: Whether model was found
        storage_found: Whether storage was found
        store_found: Whether store was found
        
    Returns:
        Confidence score (0.0 to 1.0)
        
    Examples:
        >>> calculate_extraction_confidence("text", True, True, True, True)
        1.0
    """
    score = 0.0
    
    # Base score for having text
    if text and len(text) > 50:
        score += 0.2
    
    # Price found (most important)
    if price_found:
        score += 0.4
    
    # Model found
    if model_found:
        score += 0.2
    
    # Storage variant found
    if storage_found:
        score += 0.1
    
    # Store/source found
    if store_found:
        score += 0.1
    
    return min(score, 1.0)


def create_extraction_result(
    text: str,
    target_phone: Dict[str, Any],
    target_variant: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Perform complete extraction on text for a target phone/variant.
    
    Args:
        text: Raw text to extract from
        target_phone: Target phone information
        target_variant: Optional target variant
        
    Returns:
        Complete extraction result with confidence scores
    """
    result = {
        'timestamp': datetime.now().isoformat() + 'Z',
        'source_text_length': len(text),
        'extracted': {},
        'confidence': 0.0
    }
    
    # Extract prices
    prices = extract_prices_from_text(text)
    if prices:
        result['extracted']['prices'] = prices
        result['extracted']['best_price'] = min(p['price'] for p in prices)
    
    # Extract storage and RAM
    storage = extract_storage_capacity(text)
    ram = extract_ram_capacity(text)
    
    if storage:
        result['extracted']['storage'] = storage
    if ram:
        result['extracted']['ram'] = ram
    
    # Extract stores
    stores = extract_store_names(text)
    if stores:
        result['extracted']['stores'] = stores
    
    # Extract conditions
    conditions = extract_product_conditions(text)
    result['extracted']['conditions'] = conditions
    
    # Extract phone mentions
    mentions = extract_phone_mentions(
        text,
        target_phone.get('brand'),
        target_phone.get('model')
    )
    if mentions:
        result['extracted']['mentions'] = mentions[:3]  # Top 3 mentions
    
    # Calculate overall confidence
    result['confidence'] = calculate_extraction_confidence(
        text,
        price_found=bool(prices),
        model_found=bool(mentions),
        storage_found=bool(storage),
        store_found=bool(stores)
    )
    
    return result
