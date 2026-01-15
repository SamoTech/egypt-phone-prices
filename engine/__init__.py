"""
AI-Assisted Search Intelligence Engine for Egypt Phone Prices
Provides search intent generation, text extraction, fuzzy matching, 
validation, normalization, and confidence scoring.
NO web scraping - only search-based discovery and text analysis.
"""

from .search_intents import generate_search_queries, generate_variant_search_matrix
from .extractor import (
    extract_prices_from_text,
    extract_storage_capacity,
    extract_ram_capacity,
    extract_phone_mentions,
    extract_store_names,
    create_extraction_result
)
from .matcher import fuzzy_match_phone, extract_storage_from_text, extract_ram_from_text
from .validator import validate_offer, is_accessory, is_refurbished
from .normalizer import normalize_brand, normalize_model, create_slug
from .scorer import (
    calculate_confidence_score,
    classify_confidence_level,
    get_confidence_emoji,
    apply_scoring_rules,
    generate_confidence_report
)

__all__ = [
    # Search intents
    'generate_search_queries',
    'generate_variant_search_matrix',
    # Extraction
    'extract_prices_from_text',
    'extract_storage_capacity',
    'extract_ram_capacity',
    'extract_phone_mentions',
    'extract_store_names',
    'create_extraction_result',
    # Matching
    'fuzzy_match_phone',
    'extract_storage_from_text',
    'extract_ram_from_text',
    # Validation
    'validate_offer',
    'is_accessory',
    'is_refurbished',
    # Normalization
    'normalize_brand',
    'normalize_model',
    'create_slug',
    # Scoring
    'calculate_confidence_score',
    'classify_confidence_level',
    'get_confidence_emoji',
    'apply_scoring_rules',
    'generate_confidence_report',
]
