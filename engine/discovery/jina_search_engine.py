"""
Jina AI Search Engine Integration
Uses Jina AI Search API (free, unlimited, no API keys)
"""

import logging
import requests
from typing import List, Dict, Any
from urllib.parse import quote_plus
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class JinaSearchEngine:
    """
    Free web search using Jina AI.

    Features:
    - Unlimited free tier
    - No API keys required
    - Clean content extraction
    - Markdown output
    """

    BASE_SEARCH_URL = "https://s.jina.ai/"
    BASE_READER_URL = "https://r.jina.ai/"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "User-Agent": "Egypt-Phone-Prices/1.0"}
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def search(
        self, query: str, max_results: int = 10, region: str = "eg"
    ) -> List[Dict[str, Any]]:
        """
        Perform free web search using Jina AI.

        Args:
            query: Search query
            max_results: Maximum results to return (Jina returns ~5-10 per search)
            region: Region hint (not strictly enforced by Jina)

        Returns:
            List of search result dictionaries
        """
        results = []

        try:
            # Jina search API endpoint - properly encode query for URL safety
            encoded_query = quote_plus(query)
            url = f"{self.BASE_SEARCH_URL}{encoded_query}"

            response = self.session.get(
                url,
                timeout=self.timeout,
                headers={"X-Retain-Images": "none"},  # Faster response
            )
            response.raise_for_status()

            # Jina returns markdown or JSON depending on Accept header
            data = response.json()

            # Parse Jina's response format
            if isinstance(data, dict) and "data" in data:
                search_results = data["data"]
            elif isinstance(data, list):
                search_results = data
            else:
                logger.warning(f"Unexpected Jina response format: {type(data)}")
                return results

            # Convert to standard format
            for idx, item in enumerate(search_results[:max_results]):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("description", item.get("content", ""))[
                            :500
                        ],
                        "url": item.get("url", ""),
                        "position": idx + 1,
                    }
                )

            logger.info(f"Jina AI found {len(results)} results for query: {query}")

        except requests.exceptions.Timeout:
            logger.error(f"Jina AI search timeout for query: {query}")
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Jina AI search failed for query '{query}': {type(e).__name__}: {e}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Jina search: {type(e).__name__}: {e}")

        return results

    @retry(
        stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8)
    )
    def read_url(self, url: str) -> str:
        """
        Use Jina Reader to extract clean content from a URL.

        Args:
            url: URL to read

        Returns:
            Clean markdown content
        """
        try:
            reader_url = f"{self.BASE_READER_URL}{url}"

            response = self.session.get(reader_url, timeout=self.timeout)
            response.raise_for_status()

            return response.text

        except Exception as e:
            logger.error(f"Jina Reader failed for {url}: {e}")
            return ""

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
