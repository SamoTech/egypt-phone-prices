"""
Matching & Validation Engine for Egypt Phone Prices
Provides fuzzy matching, validation, and normalization functionality.
"""

from .matcher import fuzzy_match_phone, extract_storage_from_text, extract_ram_from_text
from .validator import validate_offer, is_accessory, is_refurbished
from .normalizer import normalize_brand, normalize_model, create_slug

__all__ = [
    'fuzzy_match_phone',
    'extract_storage_from_text',
    'extract_ram_from_text',
    'validate_offer',
    'is_accessory',
    'is_refurbished',
    'normalize_brand',
    'normalize_model',
    'create_slug',
]
