"""
DuckDuckGo Search Engine Integration (Fallback)
Uses DuckDuckGo Search (no API keys, no rate limits, no cost)

NOTE: This is kept as fallback only.
Primary search engine is JinaSearchEngine.
Requires: pip install duckduckgo-search==4.4.0
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    logger.warning(
        "duckduckgo-search package not installed. "
        "DuckDuckGoSearchEngine will not be available. "
        "Install with: pip install duckduckgo-search==4.4.0"
    )


class DuckDuckGoSearchEngine:
    """
    Fallback search engine using DuckDuckGo.

    NOTE: This is kept as fallback only.
    Primary search engine is JinaSearchEngine.

    NO API keys required.
    NO rate limits.
    NO cost.
    """

    def __init__(self):
        if not DUCKDUCKGO_AVAILABLE:
            raise ImportError(
                "duckduckgo-search package is not installed. "
                "Install with: pip install duckduckgo-search==4.4.0"
            )
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 10, region: str = "eg-en") -> List[Dict[str, Any]]:
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
                results.append(
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                        "position": idx + 1,
                    }
                )

            logger.info(f"Found {len(results)} results for query: {query}")

        except Exception as e:
            # Log detailed error for debugging
            logger.error(f"DuckDuckGo search API failed for query '{query}': {type(e).__name__}: {e}")

        return results

    def search_store_specific(
        self, brand: str, model: str, storage: str = None, store_domain: str = None
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
            query = " ".join(query_parts)

        return self.search(query, max_results=5)
