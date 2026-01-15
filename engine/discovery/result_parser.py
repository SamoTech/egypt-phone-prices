"""
Search Result Parser
Extracts structured data from search results using heuristics
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SearchResultParser:
    """Parse search results to extract product information."""
    
    # Egyptian store domains
    TRUSTED_STORES = {
        'amazon.eg': 'Amazon Egypt',
        'noon.com': 'Noon',
        'jumia.com.eg': 'Jumia Egypt',
        'btech.com': 'B.TECH',
        '2b.com.eg': '2B Egypt'
    }
    
    def parse_results(
        self,
        results: List[Dict[str, Any]],
        target_phone: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse search results to extract offers.
        
        Args:
            results: Raw search results
            target_phone: Target phone specifications
            
        Returns:
            List of parsed offers
        """
        offers = []
        
        for result in results:
            offer = self._parse_single_result(result, target_phone)
            if offer:
                offers.append(offer)
        
        return offers
    
    def _parse_single_result(
        self,
        result: Dict[str, Any],
        target_phone: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Parse a single search result."""
        try:
            url = result.get('url', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Extract store from URL
            store = self._extract_store(url)
            if not store:
                return None
            
            # Extract price from snippet
            price = self._extract_price(snippet)
            if not price:
                return None
            
            # Build offer
            offer = {
                'store': store,
                'title': title,
                'price': price,
                'currency': 'EGP',
                'url': url,
                'snippet': snippet,
                'confidence': 0.7  # Base confidence
            }
            
            # Boost confidence for trusted stores
            if any(domain in url.lower() for domain in self.TRUSTED_STORES.keys()):
                offer['confidence'] = min(offer['confidence'] + 0.2, 1.0)
            
            return offer
            
        except Exception as e:
            logger.debug(f"Error parsing result: {e}")
            return None
    
    def _extract_store(self, url: str) -> Optional[str]:
        """Extract store name from URL."""
        url_lower = url.lower()
        
        for domain, name in self.TRUSTED_STORES.items():
            if domain in url_lower:
                return name
        
        # Generic extraction from domain
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text."""
        # Pattern 1: "EGP 32,999" or "32,999 EGP"
        pattern1 = r'(?:EGP|LE|ج\.م)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        pattern2 = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:EGP|LE|ج\.م)'
        
        for pattern in [pattern1, pattern2]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if 2000 <= price <= 100000:  # Reasonable phone price range
                        return price
                except ValueError:
                    continue
        
        return None
