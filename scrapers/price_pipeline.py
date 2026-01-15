"""
Price Scraping Pipeline Orchestrator
Coordinates scraping prices from multiple Egyptian marketplaces.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.prices.amazon import AmazonEgPriceScraper
from scrapers.prices.jumia import JumiaEgPriceScraper
from scrapers.prices.noon import NoonEgPriceScraper
from engine.matcher import fuzzy_match_phone
from engine.validator import validate_offer
from engine.normalizer import create_slug

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
SPECS_FILE = os.path.join(DATA_DIR, 'phones_specs.json')
VARIANTS_FILE = os.path.join(DATA_DIR, 'phone_variants.json')
PRICES_FILE = os.path.join(DATA_DIR, 'prices.json')
ERRORS_FILE = os.path.join(DATA_DIR, 'scrape_errors.json')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
DOCS_PRICES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'prices.json')


def ensure_directories():
    """Ensure all required directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DOCS_PRICES_FILE), exist_ok=True)


def load_specs() -> List[Dict[str, Any]]:
    """Load phone specifications."""
    if not os.path.exists(SPECS_FILE):
        logger.error(f"Specs file not found: {SPECS_FILE}")
        return []
    
    with open(SPECS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_variants() -> List[Dict[str, Any]]:
    """Load phone variants."""
    if not os.path.exists(VARIANTS_FILE):
        logger.warning(f"Variants file not found: {VARIANTS_FILE}")
        return []
    
    with open(VARIANTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_existing_prices() -> Dict[str, Any]:
    """Load existing prices to retain last known good values."""
    if not os.path.exists(PRICES_FILE):
        return {}
    
    try:
        with open(PRICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load existing prices: {e}")
        return {}


def calculate_price_stats(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate price statistics from offers.
    
    Args:
        offers: List of offer dictionaries
        
    Returns:
        Dictionary with min, max, avg prices and best store
    """
    if not offers:
        return {}
    
    prices = [o['price'] for o in offers if o.get('price', 0) > 0]
    
    if not prices:
        return {}
    
    # Find best offer
    best_offer = min(offers, key=lambda o: o.get('price', float('inf')))
    
    return {
        'best_price': min(prices),
        'best_store': best_offer.get('store', ''),
        'price_range': {
            'min': min(prices),
            'max': max(prices),
            'avg': sum(prices) / len(prices)
        },
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }


def run_price_pipeline(
    test_mode: bool = False,
    max_phones: Optional[int] = None,
    stores: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the complete price scraping pipeline.
    
    Args:
        test_mode: If True, only scrape a few phones
        max_phones: Maximum number of phones to process
        stores: List of stores to scrape (default: all)
        
    Returns:
        Pipeline status dictionary
    """
    start_time = datetime.utcnow()
    execution_id = f"prices_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"Starting price pipeline: {execution_id}")
    logger.info(f"Configuration: test_mode={test_mode}, max_phones={max_phones}")
    
    ensure_directories()
    
    # Initialize status
    status = {
        'execution_id': execution_id,
        'pipeline_type': 'prices',
        'status': 'running',
        'started_at': start_time.isoformat() + 'Z',
        'phones_processed': 0,
        'phones_failed': 0,
        'stores_attempted': 0,
        'stores_failed': 0,
        'errors_count': 0
    }
    
    errors = []
    all_prices = {}
    
    try:
        # Load phone specs and variants
        logger.info("Loading phone specifications and variants...")
        specs_list = load_specs()
        variants_list = load_variants()
        existing_prices = load_existing_prices()
        
        if not specs_list:
            logger.error("No phone specifications found!")
            status['status'] = 'failed'
            return status
        
        logger.info(f"Loaded {len(specs_list)} phones with {len(variants_list)} variants")
        
        # Create lookup dictionaries
        specs_by_slug = {s['slug']: s for s in specs_list}
        variants_by_phone = {}
        for variant in variants_list:
            phone_slug = variant['phone_slug']
            if phone_slug not in variants_by_phone:
                variants_by_phone[phone_slug] = []
            variants_by_phone[phone_slug].append(variant)
        
        # Determine which stores to scrape
        if stores is None:
            stores = ['amazon_eg', 'jumia_eg', 'noon_eg']
        
        status['stores_attempted'] = len(stores)
        
        # Initialize scrapers
        scrapers = []
        if 'amazon_eg' in stores:
            scrapers.append(('amazon_eg', AmazonEgPriceScraper()))
        if 'jumia_eg' in stores:
            scrapers.append(('jumia_eg', JumiaEgPriceScraper()))
        if 'noon_eg' in stores:
            scrapers.append(('noon_eg', NoonEgPriceScraper()))
        
        # Limit phones if needed
        phones_to_process = list(specs_by_slug.values())
        
        if test_mode:
            phones_to_process = phones_to_process[:5]
            logger.info(f"Test mode: limited to {len(phones_to_process)} phones")
        elif max_phones:
            phones_to_process = phones_to_process[:max_phones]
            logger.info(f"Limited to {len(phones_to_process)} phones")
        
        # Process each phone
        for phone_idx, phone_specs in enumerate(phones_to_process, 1):
            phone_slug = phone_specs['slug']
            phone_name = f"{phone_specs['brand']} {phone_specs['model']}"
            
            logger.info(f"\n{'='*60}")
            logger.info(f"[{phone_idx}/{len(phones_to_process)}] Processing: {phone_name}")
            logger.info(f"{'='*60}")
            
            # Get variants for this phone
            phone_variants = variants_by_phone.get(phone_slug, [])
            
            if not phone_variants:
                logger.warning(f"No variants found for {phone_name}, skipping")
                continue
            
            # Process each variant
            for variant in phone_variants:
                variant_slug = variant['variant_slug']
                variant_name = variant['display_name']
                
                logger.info(f"Processing variant: {variant_name}")
                
                # Initialize price entry for this variant
                if variant_slug not in all_prices:
                    all_prices[variant_slug] = {
                        'phone_slug': phone_slug,
                        'variant': f"{variant.get('ram', '')}/{variant.get('storage', '')}".strip('/'),
                        'offers': []
                    }
                
                # Scrape from each store
                for store_name, scraper in scrapers:
                    try:
                        logger.info(f"Scraping {store_name}...")
                        
                        with scraper:
                            offers = scraper.scrape_phone_offers(
                                phone_specs,
                                variant,
                                max_results=5
                            )
                        
                        if offers:
                            logger.info(f"Found {len(offers)} offers from {store_name}")
                            
                            # Validate and score each offer
                            for offer in offers:
                                # Calculate confidence score
                                confidence = fuzzy_match_phone(
                                    {'title': offer.get('title', ''), 'description': ''},
                                    {
                                        'brand': phone_specs['brand'],
                                        'model': phone_specs['model'],
                                        'storage': variant.get('storage'),
                                        'ram': variant.get('ram')
                                    }
                                )
                                
                                offer['confidence'] = round(confidence, 2)
                                
                                # Validate offer
                                is_valid, reason = validate_offer(offer, phone_specs, variant)
                                
                                if is_valid and confidence >= 0.70:
                                    all_prices[variant_slug]['offers'].append(offer)
                                    logger.info(f"✓ Added offer: {offer['price']} EGP (confidence: {confidence:.2f})")
                                else:
                                    logger.debug(f"✗ Rejected offer: {reason} (confidence: {confidence:.2f})")
                        else:
                            logger.warning(f"No offers found from {store_name}")
                        
                    except Exception as e:
                        logger.error(f"Error scraping {store_name}: {e}", exc_info=True)
                        
                        error_entry = {
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'pipeline': 'prices',
                            'store': store_name,
                            'phone': phone_name,
                            'variant': variant_name,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                        errors.append(error_entry)
                        status['errors_count'] += 1
                
                # Calculate price stats for this variant
                if all_prices[variant_slug]['offers']:
                    stats = calculate_price_stats(all_prices[variant_slug]['offers'])
                    all_prices[variant_slug].update(stats)
                    logger.info(f"Best price: {stats['best_price']} EGP from {stats['best_store']}")
                else:
                    # No new offers, try to retain existing
                    if variant_slug in existing_prices:
                        logger.info("No new offers, retaining existing data")
                        all_prices[variant_slug] = existing_prices[variant_slug]
            
            status['phones_processed'] += 1
        
        # Save results
        logger.info(f"\n{'='*60}")
        logger.info("Saving results...")
        logger.info(f"{'='*60}")
        
        # Save prices
        with open(PRICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_prices, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved prices to {PRICES_FILE}")
        
        # Copy to docs
        with open(DOCS_PRICES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_prices, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Copied prices to {DOCS_PRICES_FILE}")
        
        # Save errors
        if errors:
            with open(ERRORS_FILE, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Saved {len(errors)} errors to {ERRORS_FILE}")
        
        # Update status
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        status['completed_at'] = end_time.isoformat() + 'Z'
        status['duration_seconds'] = int(duration)
        status['status'] = 'success'
        
        logger.info(f"\n{'='*60}")
        logger.info("Pipeline completed!")
        logger.info(f"Status: {status['status']}")
        logger.info(f"Phones processed: {status['phones_processed']}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"{'='*60}")
        
        return status
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        
        status['status'] = 'failed'
        status['completed_at'] = datetime.utcnow().isoformat() + 'Z'
        status['error'] = str(e)
        
        return status


def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Egyptian Phone Price Scraper')
    parser.add_argument('--test', action='store_true', help='Test mode (limited scraping)')
    parser.add_argument('--max-phones', type=int, help='Maximum phones to process')
    parser.add_argument('--stores', nargs='+', choices=['amazon_eg', 'jumia_eg', 'noon_eg'],
                       help='Stores to scrape')
    
    args = parser.parse_args()
    
    status = run_price_pipeline(
        test_mode=args.test,
        max_phones=args.max_phones,
        stores=args.stores
    )
    
    # Exit with appropriate code
    if status['status'] == 'success':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
