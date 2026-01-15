"""
AI-Assisted Price Discovery Pipeline
Discovers phone prices using search-based intelligence and text extraction.
NO web scraping with BeautifulSoup/Selenium/Playwright.

This is a market intelligence engine, not a scraper.
"""

import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import argparse
import requests

from engine import (
    generate_search_queries,
    extract_prices_from_text,
    extract_storage_capacity,
    extract_ram_capacity,
    extract_store_names,
    extract_product_conditions,
    fuzzy_match_phone,
    validate_offer,
    calculate_confidence_score,
    classify_confidence_level,
    apply_scoring_rules
)


def search_for_phone(
    brand: str,
    model: str,
    storage: str = None,
    ram: str = None
) -> List[Dict[str, Any]]:
    """
    Generate search results for a phone variant.
    
    NOTE: This is a demonstration/prototype implementation that returns
    simulated search results. In a production system, this would:
    1. Use actual search APIs or fetch search result pages
    2. Extract data from real search results
    3. Apply rate limiting and error handling
    
    For the current implementation, it generates realistic sample data
    that demonstrates the confidence scoring and validation pipeline.
    
    Args:
        brand: Phone brand
        model: Phone model
        storage: Storage capacity
        ram: RAM capacity
        
    Returns:
        List of simulated search result snippets
    """
    # Generate search queries (this part is real)
    queries = generate_search_queries(brand, model, storage, ram, country="Egypt")
    
    print(f"  Generated {len(queries)} search queries")
    
    # NOTE: SIMULATION - In production, replace with actual search API calls
    # Example production implementation:
    # for query in queries:
    #     response = requests.get(f"https://search-api.com/?q={query}")
    #     results.extend(parse_search_results(response.text))
    
    simulated_results = []
    
    # Simulate Amazon result
    simulated_results.append({
        "source": "search_result",
        "store_hint": "amazon",
        "text": f"{brand} {model} {storage or ''} {ram or ''} Official warranty - EGP 32999 at Amazon Egypt. In stock. Free delivery.",
        "url": "https://www.amazon.eg/...",
        "confidence": 0.8
    })
    
    # Simulate Noon result
    simulated_results.append({
        "source": "search_result",
        "store_hint": "noon",
        "text": f"Buy {brand} {model} {storage or ''} online in Egypt - Price: 33,499 EGP - Noon.com - Fast shipping",
        "url": "https://www.noon.com/...",
        "confidence": 0.75
    })
    
    # Simulate Jumia result (maybe with different variant)
    if storage == "256GB":
        simulated_results.append({
            "source": "search_result",
            "store_hint": "jumia",
            "text": f"{brand} {model} - 256GB Storage - EGP 33,200 - Jumia Egypt - Official Store",
            "url": "https://www.jumia.com.eg/...",
            "confidence": 0.7
        })
    
    return simulated_results


def process_search_results(
    results: List[Dict[str, Any]],
    target_phone: Dict[str, Any],
    target_variant: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Process search results and extract price offers.
    
    Args:
        results: List of search results
        target_phone: Target phone specs
        target_variant: Target variant (storage/RAM)
        
    Returns:
        List of validated price offers with confidence scores
    """
    offers = []
    
    for result in results:
        text = result.get("text", "")
        
        # Extract prices from text
        prices = extract_prices_from_text(text)
        if not prices:
            continue
        
        # Extract storage and RAM
        extracted_storage = extract_storage_capacity(text)
        extracted_ram = extract_ram_capacity(text)
        
        # Extract stores
        stores = extract_store_names(text)
        store = stores[0] if stores else result.get("store_hint", "unknown")
        
        # Extract conditions
        conditions = extract_product_conditions(text)
        
        # Create offer object
        for price_data in prices:
            offer = {
                "store": store,
                "title": text[:100],  # First 100 chars as title
                "price": price_data["price"],
                "currency": price_data["currency"],
                "url": result.get("url", ""),
                "source_text": text,
                "extracted_storage": extracted_storage,
                "extracted_ram": extracted_ram,
                "conditions": conditions,
                "timestamp": datetime.now().replace(microsecond=0).isoformat() + "Z"
            }
            
            # Validate offer
            is_valid, rejection_reason = validate_offer(
                offer,
                target_phone,
                target_variant,
                allow_refurbished=False
            )
            
            if not is_valid:
                print(f"    ✗ Rejected: {rejection_reason}")
                continue
            
            # Calculate match confidence
            match_result = {
                "title": text,
                "description": ""
            }
            match_confidence = fuzzy_match_phone(match_result, {
                "brand": target_phone["brand"],
                "model": target_phone["model"],
                "storage": target_variant.get("storage"),
                "ram": target_variant.get("ram")
            })
            
            # Calculate overall confidence
            extraction_result = {
                "confidence": price_data.get("confidence", 0.5),
                "extracted": {
                    "prices": [price_data],
                    "best_price": price_data["price"],
                    "storage": extracted_storage,
                    "ram": extracted_ram,
                    "stores": [store],
                    "conditions": conditions
                }
            }
            
            match_result_conf = {"confidence": match_confidence}
            validation_result = {
                "is_valid": True,
                "store": store,
                "storage_match": extracted_storage == target_variant.get("storage")
            }
            
            confidence_score = calculate_confidence_score(
                extraction_result,
                match_result_conf,
                validation_result
            )
            
            # Apply scoring rules
            adjusted_conf, rules = apply_scoring_rules(
                confidence_score["overall_confidence"],
                extraction_result,
                validation_result
            )
            
            offer["confidence"] = adjusted_conf
            offer["confidence_level"] = classify_confidence_level(adjusted_conf)
            offer["scoring_rules"] = rules
            
            offers.append(offer)
    
    return offers


def discover_prices_for_variant(
    phone: Dict[str, Any],
    variant: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Discover prices for a single phone variant.
    
    Args:
        phone: Phone specifications
        variant: Variant configuration
        
    Returns:
        Variant with discovered offers
    """
    brand = phone["brand"]
    model = phone["model"]
    storage = variant.get("storage")
    ram = variant.get("ram")
    
    print(f"  Searching for: {brand} {model} {ram}/{storage}")
    
    # Search for phone
    search_results = search_for_phone(brand, model, storage, ram)
    
    # Process results and extract offers
    offers = process_search_results(search_results, phone, variant)
    
    print(f"    Found {len(offers)} valid offers")
    
    # Calculate best price and statistics
    if offers:
        prices = [o["price"] for o in offers]
        best_price = min(prices)
        best_offer = min(offers, key=lambda x: x["price"])
        
        result = {
            "variant_id": variant["variant_id"],
            "phone_slug": phone["slug"],
            "brand": brand,
            "model": model,
            "ram": ram,
            "storage": storage,
            "variant": f"{ram}/{storage}",
            "offers": offers,
            "best_price": best_price,
            "best_store": best_offer["store"],
            "avg_price": sum(prices) / len(prices),
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices)
            },
            "offer_count": len(offers),
            "high_confidence_count": sum(1 for o in offers if o["confidence"] >= 0.75),
            "last_updated": datetime.now().isoformat() + "Z"
        }
    else:
        result = {
            "variant_id": variant["variant_id"],
            "phone_slug": phone["slug"],
            "brand": brand,
            "model": model,
            "ram": ram,
            "storage": storage,
            "variant": f"{ram}/{storage}",
            "offers": [],
            "best_price": None,
            "best_store": None,
            "avg_price": None,
            "price_range": None,
            "offer_count": 0,
            "high_confidence_count": 0,
            "last_updated": datetime.now().isoformat() + "Z"
        }
    
    return result


def main():
    """Main pipeline execution."""
    parser = argparse.ArgumentParser(description="AI-Assisted Price Discovery Pipeline")
    parser.add_argument("--specs-file", type=str, default="data/phones_specs.json", help="Phone specs file")
    parser.add_argument("--variants-file", type=str, default="data/phone_variants.json", help="Phone variants file")
    parser.add_argument("--output-file", type=str, default="data/prices.json", help="Output prices file")
    parser.add_argument("--test", action="store_true", help="Test mode (limited variants)")
    parser.add_argument("--max-variants", type=int, default=None, help="Max variants to process")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI-ASSISTED PRICE DISCOVERY PIPELINE")
    print("=" * 60)
    print(f"Specs file: {args.specs_file}")
    print(f"Variants file: {args.variants_file}")
    print(f"Output file: {args.output_file}")
    print(f"Test mode: {args.test}")
    print()
    
    # Load phone specs
    specs_file = Path(args.specs_file)
    if not specs_file.exists():
        print(f"Error: Specs file not found: {specs_file}")
        print("Please run specs discovery pipeline first.")
        return
    
    with open(specs_file, "r", encoding="utf-8") as f:
        phones = json.load(f)
    
    print(f"Loaded {len(phones)} phones from specs file")
    
    # Load variants
    variants_file = Path(args.variants_file)
    if not variants_file.exists():
        print(f"Error: Variants file not found: {variants_file}")
        return
    
    with open(variants_file, "r", encoding="utf-8") as f:
        variants = json.load(f)
    
    print(f"Loaded {len(variants)} variants")
    
    # Filter variants for test mode
    if args.test:
        variants = variants[:5]
        print(f"TEST MODE: Processing only {len(variants)} variants")
    elif args.max_variants:
        variants = variants[:args.max_variants]
        print(f"Processing {len(variants)} variants (limited)")
    
    print()
    
    # Create phone lookup
    phone_lookup = {p["slug"]: p for p in phones}
    
    # Discover prices for each variant
    price_data = {}
    
    for i, variant in enumerate(variants, 1):
        phone_slug = variant["phone_slug"]
        variant_id = variant["variant_id"]
        
        if phone_slug not in phone_lookup:
            print(f"[{i}/{len(variants)}] Skipping {variant_id} - phone not found")
            continue
        
        phone = phone_lookup[phone_slug]
        
        print(f"[{i}/{len(variants)}] {phone['brand']} {phone['model']} {variant['variant_label']}")
        
        try:
            result = discover_prices_for_variant(phone, variant)
            price_data[variant_id] = result
            
            # Rate limiting
            time.sleep(1.0)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            # Add empty entry on error
            price_data[variant_id] = {
                "variant_id": variant_id,
                "phone_slug": phone_slug,
                "offers": [],
                "error": str(e),
                "last_updated": datetime.now().isoformat() + "Z"
            }
    
    # Save results
    output_file = Path(args.output_file)
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(price_data, f, indent=2, ensure_ascii=False)
    
    # Copy to docs for GitHub Pages
    docs_dir = Path("docs")
    if docs_dir.exists():
        import shutil
        shutil.copy(output_file, docs_dir / "prices.json")
        print(f"✓ Copied prices to docs/prices.json")
    
    # Calculate statistics
    total_variants = len(price_data)
    variants_with_offers = sum(1 for v in price_data.values() if v.get("offer_count", 0) > 0)
    total_offers = sum(v.get("offer_count", 0) for v in price_data.values())
    high_conf_offers = sum(v.get("high_confidence_count", 0) for v in price_data.values())
    
    print()
    print("=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"✓ Processed {total_variants} variants")
    print(f"✓ Found prices for {variants_with_offers} variants")
    print(f"✓ Total offers: {total_offers}")
    print(f"✓ High confidence offers: {high_conf_offers}")
    print(f"✓ Saved to {output_file}")


if __name__ == "__main__":
    main()
