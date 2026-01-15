"""
GSMArena Specs Pipeline Orchestrator
Main entry point for scraping phone specifications from GSMArena.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.gsmarena.brands import get_all_brands, filter_priority_brands
from scrapers.gsmarena.phones import get_phones_for_brand, filter_phones_by_year
from scrapers.gsmarena.specs import extract_phone_specs
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
ERRORS_FILE = os.path.join(DATA_DIR, 'scrape_errors.json')
DOCS_SPECS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'specs.json')


def ensure_directories():
    """Ensure all required directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DOCS_SPECS_FILE), exist_ok=True)


def log_error(error_entry: Dict[str, Any]):
    """
    Log an error to the scrape_errors.json file.
    
    Args:
        error_entry: Dictionary with error details
    """
    try:
        # Load existing errors
        errors = []
        if os.path.exists(ERRORS_FILE):
            with open(ERRORS_FILE, 'r', encoding='utf-8') as f:
                errors = json.load(f)
        
        # Append new error
        errors.append(error_entry)
        
        # Save back
        with open(ERRORS_FILE, 'w', encoding='utf-8') as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Failed to log error: {e}")


def generate_variants(specs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate all RAM/storage variant combinations for a phone.
    
    Args:
        specs: Phone specifications
        
    Returns:
        List of variant dictionaries
    """
    variants = []
    
    ram_options = specs.get('ram_options', [])
    storage_options = specs.get('storage_options', [])
    
    # If no options specified, create a default variant
    if not ram_options and not storage_options:
        return []
    
    # If only storage, no RAM
    if storage_options and not ram_options:
        for storage in storage_options:
            variant_slug = f"{specs['slug']}_{storage.lower().replace('gb', '').replace('tb', 't')}"
            variants.append({
                'phone_slug': specs['slug'],
                'variant_slug': variant_slug,
                'storage': storage,
                'ram': None,
                'display_name': f"{specs['brand']} {specs['model']} ({storage})"
            })
    
    # If only RAM, no storage (rare)
    elif ram_options and not storage_options:
        for ram in ram_options:
            variant_slug = f"{specs['slug']}_{ram.lower().replace('gb', '')}"
            variants.append({
                'phone_slug': specs['slug'],
                'variant_slug': variant_slug,
                'storage': None,
                'ram': ram,
                'display_name': f"{specs['brand']} {specs['model']} ({ram} RAM)"
            })
    
    # Both RAM and storage
    else:
        for ram in ram_options:
            for storage in storage_options:
                ram_num = ram.lower().replace('gb', '')
                storage_num = storage.lower().replace('gb', '').replace('tb', 't')
                variant_slug = f"{specs['slug']}_{ram_num}_{storage_num}"
                
                variants.append({
                    'phone_slug': specs['slug'],
                    'variant_slug': variant_slug,
                    'storage': storage,
                    'ram': ram,
                    'display_name': f"{specs['brand']} {specs['model']} ({ram}/{storage})"
                })
    
    return variants


def run_specs_pipeline(
    min_year: int = 2023,
    priority_only: bool = True,
    max_phones_per_brand: Optional[int] = None,
    test_mode: bool = False
) -> Dict[str, Any]:
    """
    Run the complete specs scraping pipeline.
    
    Args:
        min_year: Minimum release year to include
        priority_only: Only scrape priority brands
        max_phones_per_brand: Limit phones per brand (for testing)
        test_mode: If True, only scrape a few phones
        
    Returns:
        Pipeline status dictionary
    """
    start_time = datetime.utcnow()
    execution_id = f"specs_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"Starting specs pipeline: {execution_id}")
    logger.info(f"Configuration: min_year={min_year}, priority_only={priority_only}, test_mode={test_mode}")
    
    ensure_directories()
    
    # Initialize status
    status = {
        'execution_id': execution_id,
        'pipeline_type': 'specs',
        'status': 'running',
        'started_at': start_time.isoformat() + 'Z',
        'phones_processed': 0,
        'phones_failed': 0,
        'brands_processed': 0,
        'errors_count': 0
    }
    
    all_specs = []
    all_variants = []
    errors = []
    
    try:
        # Step 1: Get all brands
        logger.info("Fetching brands from GSMArena...")
        brands = get_all_brands(priority_only=priority_only)
        
        if not brands:
            logger.error("No brands found!")
            status['status'] = 'failed'
            return status
        
        logger.info(f"Found {len(brands)} brands to process")
        
        if test_mode:
            brands = brands[:2]  # Only first 2 brands in test mode
            logger.info(f"Test mode: limiting to {len(brands)} brands")
        
        # Step 2: Process each brand
        for brand in brands:
            brand_name = brand['name']
            brand_url = brand['url']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing brand: {brand_name}")
            logger.info(f"{'='*60}")
            
            try:
                # Get phones for this brand
                phones = get_phones_for_brand(brand_url, min_year=min_year, delay=2.5)
                
                if not phones:
                    logger.warning(f"No phones found for {brand_name}")
                    continue
                
                logger.info(f"Found {len(phones)} phones for {brand_name}")
                
                # Limit phones if specified
                if max_phones_per_brand:
                    phones = phones[:max_phones_per_brand]
                    logger.info(f"Limited to {len(phones)} phones")
                
                if test_mode:
                    phones = phones[:3]  # Only 3 phones per brand in test mode
                    logger.info(f"Test mode: limited to {len(phones)} phones")
                
                # Step 3: Extract specs for each phone
                for phone in phones:
                    try:
                        logger.info(f"Extracting specs: {phone['name']}")
                        
                        specs = extract_phone_specs(phone['url'], delay=2.5)
                        
                        if specs:
                            # Filter by year if release year was extracted
                            if specs.get('release_year'):
                                if specs['release_year'] < min_year:
                                    logger.info(f"Skipping {phone['name']} - too old ({specs['release_year']})")
                                    continue
                            
                            all_specs.append(specs)
                            status['phones_processed'] += 1
                            
                            # Generate variants
                            variants = generate_variants(specs)
                            all_variants.extend(variants)
                            
                            logger.info(f"✓ Successfully extracted specs for {phone['name']} ({len(variants)} variants)")
                        else:
                            logger.warning(f"Failed to extract specs for {phone['name']}")
                            status['phones_failed'] += 1
                            
                            # Log error
                            error_entry = {
                                'timestamp': datetime.utcnow().isoformat() + 'Z',
                                'pipeline': 'specs',
                                'brand': brand_name,
                                'phone': phone['name'],
                                'error_type': 'ExtractionFailed',
                                'error_message': 'Failed to extract specifications',
                                'url': phone['url']
                            }
                            errors.append(error_entry)
                            status['errors_count'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing {phone['name']}: {e}", exc_info=True)
                        status['phones_failed'] += 1
                        
                        # Log error
                        error_entry = {
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'pipeline': 'specs',
                            'brand': brand_name,
                            'phone': phone.get('name', 'Unknown'),
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'url': phone.get('url', '')
                        }
                        errors.append(error_entry)
                        status['errors_count'] += 1
                
                status['brands_processed'] += 1
                logger.info(f"Completed brand: {brand_name} ({status['phones_processed']} phones total)")
                
            except Exception as e:
                logger.error(f"Error processing brand {brand_name}: {e}", exc_info=True)
                
                error_entry = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'pipeline': 'specs',
                    'brand': brand_name,
                    'phone': None,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'url': brand_url
                }
                errors.append(error_entry)
                status['errors_count'] += 1
        
        # Step 4: Save results
        logger.info(f"\n{'='*60}")
        logger.info("Saving results...")
        logger.info(f"{'='*60}")
        
        # Save specs
        with open(SPECS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_specs, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved {len(all_specs)} phone specs to {SPECS_FILE}")
        
        # Save variants
        with open(VARIANTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_variants, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved {len(all_variants)} variants to {VARIANTS_FILE}")
        
        # Copy to docs
        with open(DOCS_SPECS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_specs, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Copied specs to {DOCS_SPECS_FILE}")
        
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
        
        if status['phones_processed'] > 0:
            if status['phones_failed'] / (status['phones_processed'] + status['phones_failed']) > 0.5:
                status['status'] = 'partial_success'
            else:
                status['status'] = 'success'
        else:
            status['status'] = 'failed'
        
        logger.info(f"\n{'='*60}")
        logger.info("Pipeline completed!")
        logger.info(f"Status: {status['status']}")
        logger.info(f"Phones processed: {status['phones_processed']}")
        logger.info(f"Phones failed: {status['phones_failed']}")
        logger.info(f"Brands processed: {status['brands_processed']}")
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
    
    parser = argparse.ArgumentParser(description='GSMArena Phone Specs Scraper')
    parser.add_argument('--min-year', type=int, default=2023, help='Minimum release year')
    parser.add_argument('--all-brands', action='store_true', help='Scrape all brands (not just priority)')
    parser.add_argument('--max-phones', type=int, help='Maximum phones per brand')
    parser.add_argument('--test', action='store_true', help='Test mode (limited scraping)')
    
    args = parser.parse_args()
    
    status = run_specs_pipeline(
        min_year=args.min_year,
        priority_only=not args.all_brands,
        max_phones_per_brand=args.max_phones,
        test_mode=args.test
    )
    
    # Exit with appropriate code
    if status['status'] == 'success':
        sys.exit(0)
    elif status['status'] == 'partial_success':
        sys.exit(0)  # Don't fail workflow on partial success
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
