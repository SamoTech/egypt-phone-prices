"""
Search Intent Generation
Generates intelligent search queries for phone price discovery.
NO web scraping - only generates search queries for text-based extraction.
"""

from typing import List, Dict, Any


def generate_search_queries(
    brand: str,
    model: str,
    storage: str = None,
    ram: str = None,
    country: str = "Egypt"
) -> List[str]:
    """
    Generate intelligent search queries for a phone variant.
    
    Args:
        brand: Phone brand (e.g., "Samsung")
        model: Phone model (e.g., "Galaxy S23")
        storage: Storage capacity (e.g., "256GB")
        ram: RAM capacity (e.g., "8GB")
        country: Target country for pricing
        
    Returns:
        List of search query strings
        
    Examples:
        >>> generate_search_queries("Samsung", "Galaxy S23", "256GB", "8GB")
        ['Samsung Galaxy S23 256GB price Egypt', 'Galaxy S23 8GB RAM Egypt Amazon', ...]
    """
    queries = []
    
    # Base model variations
    model_variants = [
        f"{brand} {model}",
        f"{model}",  # Without brand
        f"{brand} {model}".replace(" ", ""),  # No spaces
    ]
    
    # Storage/RAM variations
    spec_variants = []
    if storage:
        spec_variants.append(f"{storage}")
        if ram:
            spec_variants.append(f"{ram} {storage}")
            spec_variants.append(f"{ram}/{storage}")
    elif ram:
        spec_variants.append(f"{ram}")
    
    # English queries
    for model_var in model_variants[:2]:  # Limit to 2 model variants
        # Query 1: Basic price query
        if spec_variants:
            for spec in spec_variants[:2]:  # Limit to 2 spec variants
                queries.append(f"{model_var} {spec} price {country}")
        else:
            queries.append(f"{model_var} price {country}")
        
        # Query 2: With "buy" intent
        if storage:
            queries.append(f"buy {model_var} {storage} {country}")
    
    # Store-specific queries (top Egyptian stores)
    stores = ["Amazon", "Noon", "Jumia"]
    if storage:
        for store in stores[:2]:  # Limit to 2 stores
            queries.append(f"{brand} {model} {storage} {country} {store}")
    
    # Arabic queries
    arabic_queries = [
        f"{model} {storage if storage else ''} سعر مصر",
        f"{brand} {model} السعر في مصر",
    ]
    queries.extend(arabic_queries[:2])  # Limit Arabic queries
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean not in seen:
            seen.add(q_clean)
            unique_queries.append(q_clean)
    
    return unique_queries[:10]  # Return max 10 queries


def generate_store_specific_queries(
    brand: str,
    model: str,
    storage: str = None,
    store_domain: str = None
) -> List[str]:
    """
    Generate store-specific search queries.
    
    Args:
        brand: Phone brand
        model: Phone model
        storage: Storage capacity
        store_domain: Store domain (e.g., "amazon.eg")
        
    Returns:
        List of store-specific queries
        
    Examples:
        >>> generate_store_specific_queries("Samsung", "Galaxy S23", "256GB", "amazon.eg")
        ['Samsung Galaxy S23 256GB site:amazon.eg', ...]
    """
    queries = []
    
    base_query = f"{brand} {model}"
    if storage:
        base_query += f" {storage}"
    
    if store_domain:
        # Site-specific search
        queries.append(f"{base_query} site:{store_domain}")
        queries.append(f"{brand} {model} {store_domain}")
    
    return queries


def generate_variant_search_matrix(phone: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate search matrix for all variants of a phone.
    
    Args:
        phone: Phone dictionary with brand, model, and variants
        
    Returns:
        List of search configurations for each variant
        
    Examples:
        >>> phone = {
        ...     "brand": "Samsung",
        ...     "model": "Galaxy S23",
        ...     "variants": [
        ...         {"storage": "128GB", "ram": "8GB"},
        ...         {"storage": "256GB", "ram": "8GB"}
        ...     ]
        ... }
        >>> matrix = generate_variant_search_matrix(phone)
        >>> len(matrix)
        2
    """
    search_matrix = []
    
    brand = phone.get("brand", "")
    model = phone.get("model", "")
    variants = phone.get("variants", [])
    
    # If no variants specified, create a base search
    if not variants:
        variants = [{}]
    
    for variant in variants:
        storage = variant.get("storage")
        ram = variant.get("ram")
        
        queries = generate_search_queries(brand, model, storage, ram)
        
        search_matrix.append({
            "brand": brand,
            "model": model,
            "storage": storage,
            "ram": ram,
            "queries": queries,
            "variant_id": f"{brand}_{model}_{storage or 'base'}_{ram or 'base'}".replace(" ", "_").lower()
        })
    
    return search_matrix


def prioritize_queries(queries: List[str], context: Dict[str, Any] = None) -> List[str]:
    """
    Prioritize search queries based on context and likelihood of success.
    
    Args:
        queries: List of search queries
        context: Optional context for prioritization
        
    Returns:
        Prioritized list of queries
        
    Examples:
        >>> queries = ["Samsung Galaxy S23 price", "S23 سعر"]
        >>> prioritize_queries(queries)
        ['Samsung Galaxy S23 price', 'S23 سعر']
    """
    # Simple prioritization: prefer English, specific, with brand
    priority_scores = []
    
    for query in queries:
        score = 0
        
        # Prefer queries with storage/RAM info
        if any(cap in query for cap in ["GB", "TB"]):
            score += 3
        
        # Prefer queries with "price" or "buy"
        if "price" in query.lower() or "buy" in query.lower():
            score += 2
        
        # Prefer queries with store names
        if any(store in query for store in ["Amazon", "Noon", "Jumia"]):
            score += 1
        
        # English queries slightly preferred for parsing
        if not any(ord(c) > 127 for c in query):  # ASCII only
            score += 1
        
        priority_scores.append((score, query))
    
    # Sort by score (descending) and return queries
    priority_scores.sort(reverse=True, key=lambda x: x[0])
    return [q for _, q in priority_scores]
