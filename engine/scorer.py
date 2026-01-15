"""
Confidence Scoring Engine
Rule-based confidence scoring for extracted data.
NO LLM or external API calls - purely local logic.
"""

from typing import Dict, List, Any, Optional, Tuple


# Trusted Egyptian stores with quality scores
TRUSTED_STORES = {
    'amazon': 0.9,
    'noon': 0.85,
    'jumia': 0.8,
    'btech': 0.75,
    'souq': 0.7,
    '2b': 0.65,
    'unknown': 0.3
}


def calculate_confidence_score(
    extraction_result: Dict[str, Any],
    match_result: Dict[str, Any],
    validation_result: Dict[str, Any],
    similar_prices: List[float] = None
) -> Dict[str, Any]:
    """
    Calculate overall confidence score combining multiple factors.
    
    Scoring components:
    - Extraction quality (0.3 weight)
    - Match confidence (0.3 weight)
    - Source trust (0.2 weight)
    - Price consistency (0.2 weight)
    
    Args:
        extraction_result: Result from extractor
        match_result: Result from matcher
        validation_result: Result from validator
        similar_prices: List of similar product prices for comparison
        
    Returns:
        Dictionary with overall confidence score and breakdown
        
    Examples:
        >>> extraction = {'confidence': 0.8}
        >>> match = {'confidence': 0.9}
        >>> validation = {'is_valid': True, 'store': 'amazon'}
        >>> result = calculate_confidence_score(extraction, match, validation)
        >>> result['overall_confidence'] > 0.7
        True
    """
    scores = {
        'extraction_score': 0.0,
        'match_score': 0.0,
        'trust_score': 0.0,
        'consistency_score': 0.0,
        'overall_confidence': 0.0,
        'breakdown': {}
    }
    
    # 1. Extraction Quality Score (30%)
    extraction_conf = extraction_result.get('confidence', 0.0)
    scores['extraction_score'] = extraction_conf
    scores['breakdown']['extraction'] = {
        'score': extraction_conf,
        'weight': 0.3,
        'contribution': extraction_conf * 0.3
    }
    
    # 2. Match Confidence Score (30%)
    match_conf = match_result.get('confidence', 0.0)
    scores['match_score'] = match_conf
    scores['breakdown']['match'] = {
        'score': match_conf,
        'weight': 0.3,
        'contribution': match_conf * 0.3
    }
    
    # 3. Source Trust Score (20%)
    store = validation_result.get('store', 'unknown')
    if isinstance(store, str):
        store = store.lower()
    trust_score = TRUSTED_STORES.get(store, TRUSTED_STORES['unknown'])
    
    # Boost trust if conditions are favorable
    conditions = extraction_result.get('extracted', {}).get('conditions', {})
    if conditions.get('is_new'):
        trust_score = min(trust_score + 0.05, 1.0)
    if conditions.get('has_warranty'):
        trust_score = min(trust_score + 0.05, 1.0)
    if conditions.get('is_official'):
        trust_score = min(trust_score + 0.05, 1.0)
    
    scores['trust_score'] = trust_score
    scores['breakdown']['trust'] = {
        'score': trust_score,
        'weight': 0.2,
        'contribution': trust_score * 0.2
    }
    
    # 4. Price Consistency Score (20%)
    consistency_score = 0.5  # Default neutral score
    
    if similar_prices and len(similar_prices) >= 2:
        extracted_price = extraction_result.get('extracted', {}).get('best_price')
        if extracted_price:
            consistency_score = calculate_price_consistency(extracted_price, similar_prices)
    
    scores['consistency_score'] = consistency_score
    scores['breakdown']['consistency'] = {
        'score': consistency_score,
        'weight': 0.2,
        'contribution': consistency_score * 0.2
    }
    
    # Calculate overall confidence
    overall = (
        extraction_conf * 0.3 +
        match_conf * 0.3 +
        trust_score * 0.2 +
        consistency_score * 0.2
    )
    
    scores['overall_confidence'] = min(overall, 1.0)
    
    return scores


def calculate_price_consistency(price: float, similar_prices: List[float], max_deviation: float = 0.3) -> float:
    """
    Calculate price consistency score against similar prices.
    
    Args:
        price: Price to check
        similar_prices: List of similar product prices
        max_deviation: Maximum acceptable deviation (default 30%)
        
    Returns:
        Consistency score (0.0 to 1.0)
        
    Examples:
        >>> calculate_price_consistency(30000, [29000, 31000, 30500])
        0.95
        >>> calculate_price_consistency(50000, [29000, 31000, 30500])
        0.0
    """
    if not similar_prices or len(similar_prices) < 2:
        return 0.5  # Neutral score when not enough data
    
    # Calculate median
    sorted_prices = sorted(similar_prices)
    n = len(sorted_prices)
    if n % 2 == 0:
        median = (sorted_prices[n//2 - 1] + sorted_prices[n//2]) / 2
    else:
        median = sorted_prices[n//2]
    
    if median == 0:
        return 0.5
    
    # Calculate deviation from median
    deviation = abs(price - median) / median
    
    if deviation <= 0.05:  # Within 5%
        return 1.0
    elif deviation <= 0.10:  # Within 10%
        return 0.9
    elif deviation <= 0.20:  # Within 20%
        return 0.7
    elif deviation <= max_deviation:  # Within threshold
        return 0.5
    else:
        # Too far from median
        return max(0.0, 1.0 - (deviation / max_deviation))


def apply_scoring_rules(
    base_confidence: float,
    extraction_result: Dict[str, Any],
    validation_result: Dict[str, Any]
) -> Tuple[float, List[str]]:
    """
    Apply rule-based adjustments to confidence score.
    
    Scoring rules:
    +0.4 if trusted store keyword found
    +0.3 if storage variant matches exactly
    +0.2 if price repeated across 2+ sources
    +0.1 if "official" or "warranty" in context
    -0.5 if accessory keyword detected
    -0.3 if "refurbished" or "used" found
    -0.4 if price is outlier (>30% deviation)
    
    Args:
        base_confidence: Starting confidence score
        extraction_result: Extraction result with context
        validation_result: Validation result
        
    Returns:
        Tuple of (adjusted_confidence, list of applied rules)
        
    Examples:
        >>> result = apply_scoring_rules(0.5, {'extracted': {'stores': ['Amazon']}}, {})
        >>> result[0] > 0.5  # Should be boosted
        True
    """
    confidence = base_confidence
    applied_rules = []
    
    extracted = extraction_result.get('extracted', {})
    conditions = extracted.get('conditions', {})
    stores = extracted.get('stores', [])
    
    # Rule 1: Trusted store (+0.4)
    trusted_found = any(store.lower() in TRUSTED_STORES for store in stores)
    if trusted_found and any(TRUSTED_STORES.get(s.lower(), 0) >= 0.8 for s in stores):
        confidence = min(confidence + 0.4, 1.0)
        applied_rules.append("+0.4: Trusted store found")
    
    # Rule 2: Storage variant matches (+0.3)
    if validation_result.get('storage_match'):
        confidence = min(confidence + 0.3, 1.0)
        applied_rules.append("+0.3: Storage variant matches exactly")
    
    # Rule 3: Multiple price sources (+0.2)
    prices = extracted.get('prices', [])
    if len(prices) >= 2:
        confidence = min(confidence + 0.2, 1.0)
        applied_rules.append("+0.2: Price from multiple sources")
    
    # Rule 4: Official or warranty (+0.1)
    if conditions.get('is_official') or conditions.get('has_warranty'):
        confidence = min(confidence + 0.1, 1.0)
        applied_rules.append("+0.1: Official or warranty mentioned")
    
    # Rule 5: Accessory detected (-0.5)
    if validation_result.get('is_accessory'):
        confidence = max(confidence - 0.5, 0.0)
        applied_rules.append("-0.5: Accessory detected")
    
    # Rule 6: Refurbished/used (-0.3)
    if conditions.get('is_refurbished') or conditions.get('is_used'):
        confidence = max(confidence - 0.3, 0.0)
        applied_rules.append("-0.3: Refurbished or used")
    
    # Rule 7: Price outlier (-0.4)
    if validation_result.get('is_outlier'):
        confidence = max(confidence - 0.4, 0.0)
        applied_rules.append("-0.4: Price is outlier")
    
    return confidence, applied_rules


def classify_confidence_level(confidence: float) -> str:
    """
    Classify confidence score into levels.
    
    Args:
        confidence: Confidence score (0.0 to 1.0)
        
    Returns:
        Confidence level: "high", "medium", or "low"
        
    Examples:
        >>> classify_confidence_level(0.85)
        'high'
        >>> classify_confidence_level(0.65)
        'medium'
        >>> classify_confidence_level(0.45)
        'low'
    """
    if confidence >= 0.75:
        return "high"
    elif confidence >= 0.50:
        return "medium"
    else:
        return "low"


def get_confidence_emoji(confidence: float) -> str:
    """
    Get emoji representation of confidence level.
    
    Args:
        confidence: Confidence score (0.0 to 1.0)
        
    Returns:
        Emoji string
        
    Examples:
        >>> get_confidence_emoji(0.85)
        '🟢'
        >>> get_confidence_emoji(0.65)
        '🟡'
        >>> get_confidence_emoji(0.45)
        '🔴'
    """
    level = classify_confidence_level(confidence)
    return {
        'high': '🟢',
        'medium': '🟡',
        'low': '🔴'
    }[level]


def aggregate_offer_scores(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate confidence scores across multiple offers.
    
    Args:
        offers: List of offers with confidence scores
        
    Returns:
        Aggregated statistics
        
    Examples:
        >>> offers = [
        ...     {'confidence': 0.8, 'price': 30000},
        ...     {'confidence': 0.7, 'price': 31000}
        ... ]
        >>> result = aggregate_offer_scores(offers)
        >>> result['avg_confidence']
        0.75
    """
    if not offers:
        return {
            'avg_confidence': 0.0,
            'max_confidence': 0.0,
            'min_confidence': 0.0,
            'high_confidence_count': 0,
            'total_offers': 0
        }
    
    confidences = [o.get('confidence', 0.0) for o in offers]
    
    return {
        'avg_confidence': sum(confidences) / len(confidences),
        'max_confidence': max(confidences),
        'min_confidence': min(confidences),
        'high_confidence_count': sum(1 for c in confidences if c >= 0.75),
        'total_offers': len(offers),
        'distribution': {
            'high': sum(1 for c in confidences if c >= 0.75),
            'medium': sum(1 for c in confidences if 0.50 <= c < 0.75),
            'low': sum(1 for c in confidences if c < 0.50)
        }
    }


def calculate_best_offer_score(offers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Select best offer based on confidence and price.
    
    Scoring: (confidence * 0.6) + (price_score * 0.4)
    where price_score = 1.0 - ((price - min_price) / (max_price - min_price))
    
    Args:
        offers: List of offers with confidence and price
        
    Returns:
        Best offer or None
        
    Examples:
        >>> offers = [
        ...     {'confidence': 0.8, 'price': 30000, 'store': 'amazon'},
        ...     {'confidence': 0.7, 'price': 29000, 'store': 'noon'}
        ... ]
        >>> best = calculate_best_offer_score(offers)
        >>> best['store']
        'noon'
    """
    if not offers:
        return None
    
    if len(offers) == 1:
        return offers[0]
    
    # Get price range
    prices = [o['price'] for o in offers]
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    # Calculate composite scores
    scored_offers = []
    for offer in offers:
        confidence_score = offer.get('confidence', 0.5)
        
        # Price score (lower is better)
        if price_range > 0:
            price_score = 1.0 - ((offer['price'] - min_price) / price_range)
        else:
            price_score = 1.0
        
        # Composite score
        composite = (confidence_score * 0.6) + (price_score * 0.4)
        
        scored_offers.append({
            **offer,
            'composite_score': composite
        })
    
    # Sort by composite score (descending)
    scored_offers.sort(key=lambda x: x['composite_score'], reverse=True)
    
    return scored_offers[0]


def generate_confidence_report(
    phone: Dict[str, Any],
    offers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate comprehensive confidence report for a phone's price data.
    
    Args:
        phone: Phone information
        offers: List of price offers with confidence scores
        
    Returns:
        Detailed confidence report
    """
    report = {
        'phone': {
            'brand': phone.get('brand'),
            'model': phone.get('model'),
            'variant': f"{phone.get('storage', 'N/A')} / {phone.get('ram', 'N/A')}"
        },
        'offers_summary': aggregate_offer_scores(offers),
        'best_offer': calculate_best_offer_score(offers),
        'recommendations': []
    }
    
    # Generate recommendations
    avg_conf = report['offers_summary']['avg_confidence']
    high_count = report['offers_summary']['high_confidence_count']
    
    if avg_conf >= 0.75:
        report['recommendations'].append("Data quality is excellent. Prices are reliable.")
    elif avg_conf >= 0.50:
        report['recommendations'].append("Data quality is good. Verify with stores before purchase.")
    else:
        report['recommendations'].append("Data quality is low. Manual verification strongly recommended.")
    
    if high_count >= 2:
        report['recommendations'].append(f"Found {high_count} high-confidence offers from trusted sources.")
    elif high_count == 0:
        report['recommendations'].append("No high-confidence offers found. Proceed with caution.")
    
    return report
