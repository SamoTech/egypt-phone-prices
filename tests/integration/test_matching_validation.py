"""
Integration tests for the matching and validation workflow.
Tests the complete flow from search results to validated offers.
"""

import pytest
from engine.matcher import fuzzy_match_phone, extract_storage_from_text, extract_ram_from_text
from engine.validator import validate_offer, is_accessory
from engine.normalizer import normalize_brand, normalize_model, create_slug


class TestMatchingWorkflow:
    """Test complete matching workflow."""

    def test_complete_phone_matching_flow(self):
        """Test complete workflow from search result to match score."""
        # Step 1: Normalize brand and model
        brand = normalize_brand("SAMSUNG")
        model = normalize_model("Galaxy  S24  Ultra")
        
        assert brand == "Samsung"
        assert model == "Galaxy S24 Ultra"
        
        # Step 2: Create slug for identification
        slug = create_slug(brand, model)
        assert slug == "samsung_galaxy_s24_ultra"
        
        # Step 3: Match against search result
        search_result = {
            "title": "Samsung Galaxy S24 Ultra 12GB RAM 256GB",
            "description": "Latest flagship smartphone"
        }
        
        target_phone = {
            "brand": brand,
            "model": model,
            "storage": "256GB",
            "ram": "12GB"
        }
        
        match_score = fuzzy_match_phone(search_result, target_phone)
        assert match_score >= 0.85  # High confidence match

    def test_variant_extraction_and_matching(self):
        """Test extracting variant info and matching."""
        # Search result with variant info
        search_result = {
            "title": "iPhone 15 Pro 256GB Storage 8GB RAM",
            "description": "Apple flagship phone"
        }
        
        # Extract storage and RAM
        text = search_result["title"] + " " + search_result["description"]
        extracted_storage = extract_storage_from_text(text)
        extracted_ram = extract_ram_from_text(text)
        
        assert extracted_storage == "256GB"
        assert extracted_ram == "8GB"
        
        # Match against target
        target_phone = {
            "brand": "Apple",
            "model": "iPhone 15 Pro",
            "storage": "256GB",
            "ram": "8GB"
        }
        
        match_score = fuzzy_match_phone(search_result, target_phone)
        assert match_score >= 0.85

    def test_accessory_filtering_workflow(self):
        """Test that accessories are properly filtered."""
        # Phone should pass
        phone_result = {
            "title": "Samsung Galaxy S24 256GB",
            "description": "Brand new smartphone"
        }
        assert is_accessory(phone_result["title"] + " " + phone_result["description"]) is False
        
        # Accessory should be caught
        accessory_result = {
            "title": "Samsung Galaxy S24 Case",
            "description": "Protective case"
        }
        assert is_accessory(accessory_result["title"] + " " + accessory_result["description"]) is True


class TestValidationWorkflow:
    """Test complete validation workflow."""

    def test_valid_offer_complete_flow(self):
        """Test complete validation flow for valid offer."""
        # Step 1: Create offer
        offer = {
            "title": "Samsung Galaxy S24 Ultra 256GB",
            "description": "Brand new, sealed box",
            "price": 32000,
            "seller": "TechStore",
            "rating": 4.5,
            "reviews": 100,
            "verified": True
        }
        
        # Step 2: Define target phone
        specs = {
            "brand": "Samsung",
            "model": "Galaxy S24 Ultra"
        }
        
        variant = {
            "storage": "256GB"
        }
        
        # Step 3: Validate offer
        is_valid, reason = validate_offer(offer, specs, variant)
        
        assert is_valid is True
        assert reason == ""

    def test_invalid_offer_rejection_flow(self):
        """Test rejection of invalid offers."""
        # Test 1: Accessory rejection
        accessory_offer = {
            "title": "Samsung Galaxy S24 Case",
            "description": "Protective case",
            "price": 200
        }
        
        specs = {"brand": "Samsung", "model": "Galaxy S24"}
        variant = {"storage": "256GB"}
        
        is_valid, reason = validate_offer(accessory_offer, specs, variant)
        assert is_valid is False
        assert "accessory" in reason.lower()
        
        # Test 2: Price too low
        low_price_offer = {
            "title": "Samsung Galaxy S24 256GB",
            "description": "Brand new",
            "price": 500
        }
        
        is_valid, reason = validate_offer(low_price_offer, specs, variant)
        assert is_valid is False
        assert "price" in reason.lower()
        
        # Test 3: Storage mismatch
        wrong_storage_offer = {
            "title": "Samsung Galaxy S24 512GB",
            "description": "High capacity",
            "price": 35000
        }
        
        is_valid, reason = validate_offer(wrong_storage_offer, specs, variant)
        assert is_valid is False
        assert "storage" in reason.lower()


class TestEndToEndPipeline:
    """Test end-to-end pipeline scenarios."""

    def test_multiple_offers_ranking(self):
        """Test processing multiple offers and ranking them."""
        offers = [
            {
                "title": "Samsung Galaxy S24 256GB - Official",
                "price": 31000,
                "rating": 4.8,
                "reviews": 200
            },
            {
                "title": "Samsung Galaxy S24 256GB",
                "price": 30500,
                "rating": 4.2,
                "reviews": 50
            },
            {
                "title": "Samsung Galaxy S24 512GB",  # Wrong storage
                "price": 35000,
                "rating": 4.5,
                "reviews": 100
            },
            {
                "title": "Samsung S24 Case",  # Accessory
                "price": 200,
                "rating": 4.0,
                "reviews": 30
            }
        ]
        
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24",
            "storage": "256GB"
        }
        
        specs = {"brand": "Samsung", "model": "Galaxy S24"}
        variant = {"storage": "256GB"}
        
        valid_offers = []
        for offer in offers:
            # Check match score
            match_score = fuzzy_match_phone(offer, target_phone)
            
            # Validate offer
            is_valid, reason = validate_offer(offer, specs, variant)
            
            if is_valid and match_score >= 0.70:
                valid_offers.append({
                    "offer": offer,
                    "match_score": match_score
                })
        
        # Should have 2 valid offers (first two)
        assert len(valid_offers) == 2
        
        # Offers should have high match scores
        for item in valid_offers:
            assert item["match_score"] >= 0.70

    def test_brand_normalization_consistency(self):
        """Test that brand normalization is consistent across pipeline."""
        brand_variations = [
            "SAMSUNG", "samsung", "Samsung", "SaMsUnG"
        ]
        
        for variation in brand_variations:
            normalized = normalize_brand(variation)
            assert normalized == "Samsung"
            
            slug = create_slug(normalized, "Galaxy S24")
            assert slug == "samsung_galaxy_s24"


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_empty_search_results(self):
        """Test handling of empty search results."""
        search_result = {"title": "", "description": ""}
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24",
            "storage": "256GB"
        }
        
        score = fuzzy_match_phone(search_result, target_phone)
        assert 0.0 <= score <= 1.0  # Should not crash

    def test_missing_variant_info(self):
        """Test handling of missing variant information."""
        offer = {
            "title": "Samsung Phone",  # No storage info
            "description": "Good condition",
            "price": 25000
        }
        
        specs = {"brand": "Samsung", "model": "Galaxy S24"}
        variant = {"storage": "256GB"}
        
        # Should handle gracefully
        is_valid, reason = validate_offer(offer, specs, variant)
        # May fail validation due to missing storage
        assert isinstance(is_valid, bool)
        assert isinstance(reason, str)

    def test_extreme_prices(self):
        """Test handling of extreme price values."""
        specs = {"brand": "Samsung", "model": "Galaxy S24"}
        variant = {"storage": "256GB"}
        
        # Test very low price
        low_offer = {
            "title": "Samsung Galaxy S24 256GB",
            "description": "Brand new",
            "price": 100
        }
        is_valid, _ = validate_offer(low_offer, specs, variant)
        assert is_valid is False
        
        # Test very high price
        high_offer = {
            "title": "Samsung Galaxy S24 256GB",
            "description": "Brand new",
            "price": 200000
        }
        is_valid, _ = validate_offer(high_offer, specs, variant)
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
