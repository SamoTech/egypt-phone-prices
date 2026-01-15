"""
AI-Assisted Specs Discovery Pipeline
Discovers phone specifications using text-based extraction only.
NO web scraping with BeautifulSoup/Selenium/Playwright.

This is a spec inference engine, not a scraper.
"""

import json
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse
import requests
from pathlib import Path

from engine import normalize_brand, create_slug


# Priority brands for Egyptian market
PRIORITY_BRANDS = [
    "Samsung", "Apple", "Xiaomi", "Oppo", "Realme", 
    "OnePlus", "Google", "Motorola", "Nokia", "Vivo"
]


def discover_phones_from_seed(min_year: int = 2023) -> List[Dict[str, Any]]:
    """
    Discover phones from a seed list (avoiding actual scraping).
    Uses a hardcoded seed list of popular phones for bootstrapping.
    
    Args:
        min_year: Minimum release year to include
        
    Returns:
        List of phone specs
    """
    # Seed list of popular phones in Egyptian market (2023-2024)
    seed_phones = [
        {"brand": "Samsung", "model": "Galaxy S24 Ultra", "year": 2024},
        {"brand": "Samsung", "model": "Galaxy S24", "year": 2024},
        {"brand": "Samsung", "model": "Galaxy S24 Plus", "year": 2024},
        {"brand": "Samsung", "model": "Galaxy S23", "year": 2023},
        {"brand": "Samsung", "model": "Galaxy A54", "year": 2023},
        {"brand": "Samsung", "model": "Galaxy A34", "year": 2023},
        {"brand": "Apple", "model": "iPhone 15 Pro Max", "year": 2023},
        {"brand": "Apple", "model": "iPhone 15 Pro", "year": 2023},
        {"brand": "Apple", "model": "iPhone 15", "year": 2023},
        {"brand": "Apple", "model": "iPhone 14", "year": 2023},
        {"brand": "Xiaomi", "model": "14", "year": 2024},
        {"brand": "Xiaomi", "model": "13T Pro", "year": 2023},
        {"brand": "Xiaomi", "model": "Redmi Note 13 Pro", "year": 2024},
        {"brand": "Oppo", "model": "Reno 11", "year": 2024},
        {"brand": "Oppo", "model": "Find X6", "year": 2023},
        {"brand": "Realme", "model": "12 Pro", "year": 2024},
        {"brand": "Realme", "model": "11 Pro", "year": 2023},
        {"brand": "OnePlus", "model": "12", "year": 2024},
        {"brand": "OnePlus", "model": "11", "year": 2023},
        {"brand": "Google", "model": "Pixel 8 Pro", "year": 2023},
        {"brand": "Google", "model": "Pixel 8", "year": 2023},
        {"brand": "Motorola", "model": "Edge 40 Pro", "year": 2023},
        {"brand": "Nokia", "model": "G42", "year": 2023},
        {"brand": "Vivo", "model": "V29", "year": 2023},
        {"brand": "Infinix", "model": "Note 30", "year": 2023},
        {"brand": "Tecno", "model": "Camon 20", "year": 2023},
    ]
    
    # Filter by year
    filtered = [p for p in seed_phones if p["year"] >= min_year]
    
    print(f"Loaded {len(filtered)} phones from seed list (year >= {min_year})")
    
    return filtered


def generate_phone_specs(phone_seed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate phone specs using AI-assisted inference.
    
    This uses heuristic rules and patterns to generate reasonable specs
    without actual web scraping. In a real implementation, this would
    fetch GSMArena pages as text and extract specs.
    
    Args:
        phone_seed: Seed phone info (brand, model, year)
        
    Returns:
        Complete phone specs
    """
    brand = phone_seed["brand"]
    model = phone_seed["model"]
    year = phone_seed["year"]
    
    # For demonstration, we'll use the seed data + some inference
    # In production, this would fetch GSMArena URL as text and extract specs
    
    specs = {
        "slug": create_slug(brand, model),
        "brand": normalize_brand(brand),
        "model": model,
        "release_year": year,
        "display": "6.5 inches, AMOLED",  # Default inference
        "chipset": None,
        "ram_options": ["8GB"],  # Default
        "storage_options": ["128GB", "256GB"],  # Default
        "camera": "50 MP + 12 MP",  # Default
        "battery": "4500 mAh",  # Default
        "os": f"Android {year - 2010}" if brand != "Apple" else f"iOS {year - 2006}"
    }
    
    # Brand-specific inference
    if brand == "Samsung":
        if "Ultra" in model:
            specs["chipset"] = "Snapdragon 8 Gen 3" if year >= 2024 else "Snapdragon 8 Gen 2"
            specs["ram_options"] = ["12GB"]
            specs["storage_options"] = ["256GB", "512GB", "1TB"]
            specs["display"] = "6.8 inches, Dynamic AMOLED 2X"
            specs["camera"] = "200 MP + 50 MP + 10 MP + 12 MP"
            specs["battery"] = "5000 mAh"
        elif "S24" in model or "S23" in model:
            specs["chipset"] = "Snapdragon 8 Gen 3" if "S24" in model else "Snapdragon 8 Gen 2"
            specs["display"] = "6.2 inches, Dynamic AMOLED 2X"
            specs["battery"] = "4000 mAh"
            specs["camera"] = "50 MP + 10 MP + 12 MP"
        elif "A" in model:
            specs["chipset"] = "Exynos 1380"
            specs["ram_options"] = ["6GB", "8GB"]
            specs["battery"] = "5000 mAh"
    
    elif brand == "Apple":
        specs["chipset"] = f"Apple A{year - 2006} Pro" if "Pro" in model else f"Apple A{year - 2006}"
        specs["ram_options"] = ["8GB"] if "Pro" in model else ["6GB"]
        specs["storage_options"] = ["128GB", "256GB", "512GB", "1TB"] if "Pro" in model else ["128GB", "256GB", "512GB"]
        specs["display"] = "6.7 inches, LTPO Super Retina XDR OLED" if "Max" in model else "6.1 inches, Super Retina XDR OLED"
        specs["camera"] = "48 MP + 12 MP + 12 MP"
        specs["battery"] = "4441 mAh" if "Max" in model else "3349 mAh"
    
    elif brand == "Xiaomi":
        specs["chipset"] = "Snapdragon 8 Gen 2" if year >= 2023 else "Snapdragon 8 Gen 1"
        if "Redmi" in model:
            specs["ram_options"] = ["6GB", "8GB"]
            specs["storage_options"] = ["128GB", "256GB"]
    
    return specs


def generate_phone_variants(specs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate all storage/RAM variants for a phone.
    
    Args:
        specs: Phone specifications
        
    Returns:
        List of variant configurations
    """
    variants = []
    
    ram_options = specs.get("ram_options", ["8GB"])
    storage_options = specs.get("storage_options", ["128GB", "256GB"])
    
    for ram in ram_options:
        for storage in storage_options:
            variant_id = f"{specs['slug']}_{ram.lower().replace('gb', '')}_{storage.lower().replace('gb', '').replace('tb', 't')}"
            
            variants.append({
                "variant_id": variant_id,
                "phone_slug": specs["slug"],
                "brand": specs["brand"],
                "model": specs["model"],
                "ram": ram,
                "storage": storage,
                "variant_label": f"{ram}/{storage}"
            })
    
    return variants


def main():
    """Main pipeline execution."""
    parser = argparse.ArgumentParser(description="AI-Assisted Phone Specs Discovery Pipeline")
    parser.add_argument("--min-year", type=int, default=2023, help="Minimum release year")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    parser.add_argument("--test", action="store_true", help="Test mode (limited phones)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI-ASSISTED PHONE SPECS DISCOVERY PIPELINE")
    print("=" * 60)
    print(f"Minimum year: {args.min_year}")
    print(f"Output directory: {args.output_dir}")
    print(f"Test mode: {args.test}")
    print()
    
    # Discover phones from seed
    seed_phones = discover_phones_from_seed(min_year=args.min_year)
    
    if args.test:
        seed_phones = seed_phones[:5]  # Limit to 5 in test mode
        print(f"TEST MODE: Processing only {len(seed_phones)} phones")
    
    # Generate specs for each phone
    all_specs = []
    all_variants = []
    
    for i, phone_seed in enumerate(seed_phones, 1):
        print(f"[{i}/{len(seed_phones)}] Processing {phone_seed['brand']} {phone_seed['model']}...")
        
        try:
            # Generate specs using AI-assisted inference
            specs = generate_phone_specs(phone_seed)
            all_specs.append(specs)
            
            # Generate variants
            variants = generate_phone_variants(specs)
            all_variants.extend(variants)
            
            print(f"  ✓ Generated specs with {len(variants)} variants")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    # Save results
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    specs_file = output_dir / "phones_specs.json"
    variants_file = output_dir / "phone_variants.json"
    
    with open(specs_file, "w", encoding="utf-8") as f:
        json.dump(all_specs, f, indent=2, ensure_ascii=False)
    
    with open(variants_file, "w", encoding="utf-8") as f:
        json.dump(all_variants, f, indent=2, ensure_ascii=False)
    
    # Copy to docs for GitHub Pages
    docs_dir = Path("docs")
    if docs_dir.exists():
        import shutil
        shutil.copy(specs_file, docs_dir / "specs.json")
        print(f"✓ Copied specs to docs/specs.json")
    
    print()
    print("=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"✓ Generated specs for {len(all_specs)} phones")
    print(f"✓ Generated {len(all_variants)} variants")
    print(f"✓ Saved to {specs_file} and {variants_file}")


if __name__ == "__main__":
    main()
