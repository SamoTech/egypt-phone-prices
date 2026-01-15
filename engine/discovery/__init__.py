"""
Search-Based Discovery Module
Uses free search APIs to discover phones and prices
"""

from .search_engine import FreeSearchEngine
from .result_parser import SearchResultParser

__all__ = ['FreeSearchEngine', 'SearchResultParser']
