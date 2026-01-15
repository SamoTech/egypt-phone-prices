"""
GSMArena Phone Specifications Scraper
Discovers phones and extracts detailed specifications from GSMArena.
"""

from .brands import get_all_brands, get_brand_url
from .phones import get_phones_for_brand, filter_phones_by_year
from .specs import extract_phone_specs, parse_spec_table

__all__ = [
    'get_all_brands',
    'get_brand_url',
    'get_phones_for_brand',
    'filter_phones_by_year',
    'extract_phone_specs',
    'parse_spec_table',
]
