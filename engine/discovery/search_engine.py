"""
Free Search Engine Integration
Uses DuckDuckGo Search (no API keys, no rate limits, no cost)
"""

import logging
import time
from typing import List, Dict, Any
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class FreeSearchEngine:
    """
    Free web search integration using DuckDuckGo.
    
    NO API keys required.
    NO rate limits.
    NO cost.
    """
    
    def __init__(self):
        self.ddgs = DDGS()
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        region: str = "eg-en"
    ) -> List[Dict[str, Any]]:
        """
        Perform free web search.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            region: Region code (eg-en for Egypt English)
            
        Returns:
            List of search result dictionaries
        """
        results = []
        
        try:
            for idx, r in enumerate(self.ddgs.text(query, region=region, max_results=max_results)):
                results.append({
                    'title': r.get('title', ''),
                    'snippet': r.get('body', ''),
                    'url': r.get('href', ''),
                    'position': idx + 1
                })
            
            logger.info(f"Found {len(results)} results for query: {query}")
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
        
        return results
    
    def search_store_specific(
        self,
        brand: str,
        model: str,
        storage: str = None,
        store_domain: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search for a phone on a specific store.
        
        Args:
            brand: Phone brand
            model: Phone model
            storage: Storage capacity (optional)
            store_domain: Store domain (e.g., 'amazon.eg', 'noon.com')
            
        Returns:
            List of search results
        """
        # Build query
        query_parts = [brand, model]
        if storage:
            query_parts.append(storage)
        
        if store_domain:
            query = f"{' '.join(query_parts)} site:{store_domain}"
        else:
            query = ' '.join(query_parts)
        
        return self.search(query, max_results=5)
