"""
Discovery module - Search and price discovery engines
"""

from .jina_search_engine import JinaSearchEngine
from .search_engine import DuckDuckGoSearchEngine
from .result_parser import SearchResultParser

# Use Jina as default (DuckDuckGo kept as fallback)
FreeSearchEngine = JinaSearchEngine

__all__ = [
    'JinaSearchEngine',
    'DuckDuckGoSearchEngine',
    'FreeSearchEngine',
    'SearchResultParser'
]
