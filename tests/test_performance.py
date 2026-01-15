"""
Performance tests for critical code paths.
Ensures that key operations meet performance targets.
"""

import time
import pytest
from engine.matcher import fuzzy_match_phone, extract_storage_from_text, extract_ram_from_text
from engine.validator import validate_offer, is_accessory
from engine.normalizer import normalize_brand, normalize_model, create_slug


@pytest.mark.performance
class TestMatcherPerformance:
    """Performance tests for matcher module."""

    def test_fuzzy_match_performance(self, benchmark=None):
        """Test that fuzzy matching is fast enough."""
        search_result = {
            "title": "Samsung Galaxy S24 Ultra 256GB 12GB RAM",
            "description": "Latest flagship smartphone"
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24 Ultra",
            "storage": "256GB",
            "ram": "12GB"
        }
        
        # Run multiple times to get average
        start_time = time.perf_counter()
        iterations = 1000
        
        for _ in range(iterations):
            score = fuzzy_match_phone(search_result, target_phone)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000
        
        print(f"\n⚡ Fuzzy match average time: {avg_time_ms:.2f} ms")
        
        # Target: < 35ms per phone (from requirements)
        assert avg_time_ms < 35, f"Fuzzy matching too slow: {avg_time_ms:.2f} ms"

    def test_extraction_performance(self):
        """Test storage/RAM extraction performance."""
        text = "Samsung Galaxy S24 Ultra 12GB RAM 256GB Storage"
        
        start_time = time.perf_counter()
        iterations = 10000
        
        for _ in range(iterations):
            extract_storage_from_text(text)
            extract_ram_from_text(text)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000
        
        print(f"\n⚡ Extraction average time: {avg_time_ms:.2f} ms")
        
        # Should be very fast (< 1ms)
        assert avg_time_ms < 1.0, f"Extraction too slow: {avg_time_ms:.2f} ms"


@pytest.mark.performance
class TestValidatorPerformance:
    """Performance tests for validator module."""

    def test_validate_offer_performance(self):
        """Test offer validation performance."""
        offer = {
            "title": "Samsung Galaxy S24 Ultra 256GB",
            "description": "Brand new smartphone",
            "price": 32000
        }
        specs = {"brand": "Samsung", "model": "Galaxy S24 Ultra"}
        variant = {"storage": "256GB"}
        
        start_time = time.perf_counter()
        iterations = 5000
        
        for _ in range(iterations):
            validate_offer(offer, specs, variant)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000
        
        print(f"\n⚡ Validation average time: {avg_time_ms:.2f} ms")
        
        # Should be fast (< 5ms)
        assert avg_time_ms < 5.0, f"Validation too slow: {avg_time_ms:.2f} ms"

    def test_accessory_detection_performance(self):
        """Test accessory detection performance."""
        texts = [
            "Samsung Galaxy S24 256GB",
            "Samsung Galaxy S24 Case",
            "iPhone 15 Pro Max",
            "USB Charging Cable",
            "Xiaomi Redmi Note 12"
        ]
        
        start_time = time.perf_counter()
        iterations = 10000
        
        for _ in range(iterations):
            for text in texts:
                is_accessory(text)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / (iterations * len(texts))) * 1000
        
        print(f"\n⚡ Accessory detection average time: {avg_time_ms:.2f} ms")
        
        # Should be very fast (< 0.5ms)
        assert avg_time_ms < 0.5, f"Accessory detection too slow: {avg_time_ms:.2f} ms"


@pytest.mark.performance
class TestNormalizerPerformance:
    """Performance tests for normalizer module."""

    def test_normalization_performance(self):
        """Test brand/model normalization performance."""
        brands = ["SAMSUNG", "apple", "Xiaomi", "OPPO", "realme"]
        models = ["Galaxy S24 Ultra", "iPhone 15 Pro", "Redmi Note 12", "A78", "12 Pro"]
        
        start_time = time.perf_counter()
        iterations = 10000
        
        for _ in range(iterations):
            for brand in brands:
                normalize_brand(brand)
            for model in models:
                normalize_model(model)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / (iterations * (len(brands) + len(models)))) * 1000
        
        print(f"\n⚡ Normalization average time: {avg_time_ms:.2f} ms")
        
        # Should be very fast (< 0.1ms)
        assert avg_time_ms < 0.1, f"Normalization too slow: {avg_time_ms:.2f} ms"

    def test_slug_creation_performance(self):
        """Test slug creation performance."""
        brand_model_pairs = [
            ("Samsung", "Galaxy S24 Ultra"),
            ("Apple", "iPhone 15 Pro Max"),
            ("Xiaomi", "Redmi Note 12 Pro"),
            ("OnePlus", "12R"),
            ("Google", "Pixel 8 Pro")
        ]
        
        start_time = time.perf_counter()
        iterations = 10000
        
        for _ in range(iterations):
            for brand, model in brand_model_pairs:
                create_slug(brand, model)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / (iterations * len(brand_model_pairs))) * 1000
        
        print(f"\n⚡ Slug creation average time: {avg_time_ms:.2f} ms")
        
        # Should be very fast (< 0.1ms)
        assert avg_time_ms < 0.1, f"Slug creation too slow: {avg_time_ms:.2f} ms"


@pytest.mark.performance
class TestIntegrationPerformance:
    """Performance tests for integrated workflows."""

    def test_complete_matching_workflow_performance(self):
        """Test complete matching workflow performance."""
        offers = [
            {
                "title": "Samsung Galaxy S24 256GB",
                "price": 30000,
                "description": "Brand new"
            },
            {
                "title": "Apple iPhone 15 Pro 256GB",
                "price": 45000,
                "description": "Latest model"
            },
            {
                "title": "Xiaomi Redmi Note 12 128GB",
                "price": 8000,
                "description": "Budget phone"
            }
        ]
        
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24",
            "storage": "256GB"
        }
        
        specs = {"brand": "Samsung", "model": "Galaxy S24"}
        variant = {"storage": "256GB"}
        
        start_time = time.perf_counter()
        iterations = 1000
        
        for _ in range(iterations):
            for offer in offers:
                # Normalize
                brand = normalize_brand(specs["brand"])
                model = normalize_model(specs["model"])
                
                # Match
                score = fuzzy_match_phone(offer, target_phone)
                
                # Validate
                if score >= 0.70:
                    validate_offer(offer, specs, variant)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / (iterations * len(offers))) * 1000
        
        print(f"\n⚡ Complete workflow average time: {avg_time_ms:.2f} ms")
        
        # Target: < 40ms per offer (allowing for matching target of 35ms + validation)
        assert avg_time_ms < 40, f"Complete workflow too slow: {avg_time_ms:.2f} ms"


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage tests."""

    def test_matcher_memory_efficiency(self):
        """Test that matcher doesn't leak memory."""
        import gc
        import tracemalloc
        
        tracemalloc.start()
        
        # Create many match operations
        for _ in range(10000):
            search_result = {
                "title": "Samsung Galaxy S24 Ultra 256GB",
                "description": "Latest phone"
            }
            target_phone = {
                "brand": "Samsung",
                "model": "Galaxy S24 Ultra",
                "storage": "256GB"
            }
            fuzzy_match_phone(search_result, target_phone)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / (1024 * 1024)
        print(f"\n💾 Peak memory usage: {peak_mb:.2f} MB")
        
        # Should use reasonable memory (< 50MB for 10k operations)
        assert peak_mb < 50, f"Memory usage too high: {peak_mb:.2f} MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "performance"])
