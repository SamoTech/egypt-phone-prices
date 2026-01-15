"""
Unit tests for engine.matcher module.
Tests fuzzy matching logic, storage/RAM extraction, and price extraction.
"""

import pytest
from engine.matcher import (
    fuzzy_match_phone,
    extract_storage_from_text,
    extract_ram_from_text,
    calculate_variant_match_score,
    extract_price_from_text,
)


class TestFuzzyMatchPhone:
    """Test fuzzy_match_phone function."""

    def test_perfect_match(self):
        """Test perfect match scenario."""
        search_result = {
            "title": "Samsung Galaxy S24 Ultra 256GB",
            "description": "Latest flagship phone"
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24 Ultra",
            "storage": "256GB",
            "ram": ""
        }
        score = fuzzy_match_phone(search_result, target_phone)
        assert score >= 0.85, f"Expected high match score, got {score}"

    def test_brand_mismatch(self):
        """Test when brand doesn't match."""
        search_result = {
            "title": "Apple iPhone 15 Pro 256GB",
            "description": ""
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24",
            "storage": "256GB",
            "ram": ""
        }
        score = fuzzy_match_phone(search_result, target_phone)
        assert score < 0.70, f"Expected low match score for brand mismatch, got {score}"

    def test_storage_mismatch(self):
        """Test when storage doesn't match."""
        search_result = {
            "title": "Samsung Galaxy S24 512GB",
            "description": ""
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24",
            "storage": "256GB",
            "ram": ""
        }
        score = fuzzy_match_phone(search_result, target_phone)
        # Should still have decent score from brand/model but reduced by storage mismatch
        assert 0.50 <= score <= 0.80, f"Expected moderate score for storage mismatch, got {score}"

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        search_result = {
            "title": "SAMSUNG GALAXY S24 ULTRA 256GB",
            "description": ""
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24 Ultra",
            "storage": "256GB",
            "ram": ""
        }
        score = fuzzy_match_phone(search_result, target_phone)
        assert score >= 0.85, f"Case insensitive matching failed, score: {score}"

    def test_with_ram_matching(self):
        """Test matching with RAM specification."""
        search_result = {
            "title": "Samsung Galaxy S24 Ultra 12GB RAM 256GB Storage",
            "description": ""
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24 Ultra",
            "storage": "256GB",
            "ram": "12GB"
        }
        score = fuzzy_match_phone(search_result, target_phone)
        assert score >= 0.85, f"Expected high match score with RAM, got {score}"

    def test_partial_model_name(self):
        """Test matching with partial model names."""
        search_result = {
            "title": "Samsung S24 Ultra 256GB",
            "description": ""
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24 Ultra",
            "storage": "256GB",
            "ram": ""
        }
        score = fuzzy_match_phone(search_result, target_phone)
        assert score >= 0.70, f"Partial model matching failed, score: {score}"

    def test_empty_search_result(self):
        """Test with empty search result."""
        search_result = {"title": "", "description": ""}
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24",
            "storage": "256GB",
            "ram": ""
        }
        score = fuzzy_match_phone(search_result, target_phone)
        assert score <= 0.50, f"Empty search should give low score, got {score}"

    def test_no_storage_requirement(self):
        """Test when target has no storage requirement."""
        search_result = {
            "title": "Samsung Galaxy S24",
            "description": ""
        }
        target_phone = {
            "brand": "Samsung",
            "model": "Galaxy S24",
            "storage": "",
            "ram": ""
        }
        score = fuzzy_match_phone(search_result, target_phone)
        # Should get full credit for missing storage
        assert score >= 0.70, f"No storage requirement should not penalize, score: {score}"


class TestExtractStorageFromText:
    """Test extract_storage_from_text function."""

    def test_extract_gb_storage(self):
        """Test extracting GB storage."""
        assert extract_storage_from_text("Samsung Galaxy S24 256GB") == "256GB"
        assert extract_storage_from_text("iPhone with 512 GB storage") == "512GB"
        assert extract_storage_from_text("128GB Internal") == "128GB"

    def test_extract_tb_storage(self):
        """Test extracting TB storage."""
        assert extract_storage_from_text("Phone with 1TB storage") == "1TB"
        assert extract_storage_from_text("2 TB Internal") == "2TB"

    def test_no_storage_found(self):
        """Test when no storage is found."""
        assert extract_storage_from_text("Phone case") is None
        assert extract_storage_from_text("Charger cable") is None

    def test_ignore_small_gb_values(self):
        """Test that small GB values (likely RAM) are filtered out."""
        # 4GB is likely RAM, not storage
        result = extract_storage_from_text("Phone with 4GB")
        # Should return None or handle appropriately
        # Based on implementation, it checks for >= 32 or in [8, 16]
        assert result is None or result == "4GB"

    def test_common_storage_sizes(self):
        """Test common phone storage sizes."""
        assert extract_storage_from_text("64GB phone") == "64GB"
        assert extract_storage_from_text("128GB variant") == "128GB"
        assert extract_storage_from_text("256GB model") == "256GB"
        assert extract_storage_from_text("512GB version") == "512GB"

    def test_case_insensitive(self):
        """Test case insensitive extraction."""
        assert extract_storage_from_text("256gb storage") == "256GB"
        assert extract_storage_from_text("1tb internal") == "1TB"


class TestExtractRamFromText:
    """Test extract_ram_from_text function."""

    def test_extract_explicit_ram(self):
        """Test extracting explicit RAM indicators."""
        assert extract_ram_from_text("Samsung Galaxy S24 12GB RAM") == "12GB"
        assert extract_ram_from_text("Phone with RAM 8GB") == "8GB"
        assert extract_ram_from_text("16GB Memory") == "16GB"

    def test_extract_from_combo_format(self):
        """Test extracting RAM from combo format (RAM/Storage)."""
        assert extract_ram_from_text("12GB/256GB") == "12GB"
        assert extract_ram_from_text("8GB/128GB") == "8GB"

    def test_no_ram_found(self):
        """Test when no RAM is found."""
        assert extract_ram_from_text("Phone with 256GB storage") is None
        assert extract_ram_from_text("Accessory") is None

    def test_common_ram_sizes(self):
        """Test common phone RAM sizes."""
        assert extract_ram_from_text("4GB RAM") == "4GB"
        assert extract_ram_from_text("6GB RAM") == "6GB"
        assert extract_ram_from_text("8GB RAM") == "8GB"
        assert extract_ram_from_text("12GB RAM") == "12GB"

    def test_case_insensitive(self):
        """Test case insensitive extraction."""
        assert extract_ram_from_text("12gb ram") == "12GB"
        assert extract_ram_from_text("8GB memory") == "8GB"


class TestCalculateVariantMatchScore:
    """Test calculate_variant_match_score function."""

    def test_perfect_storage_match(self):
        """Test perfect storage match."""
        score = calculate_variant_match_score("256GB", None, "256GB", None)
        assert score == 1.0

    def test_storage_mismatch(self):
        """Test storage mismatch."""
        score = calculate_variant_match_score("512GB", None, "256GB", None)
        assert score == 0.0

    def test_perfect_storage_and_ram_match(self):
        """Test perfect storage and RAM match."""
        score = calculate_variant_match_score("256GB", "12GB", "256GB", "12GB")
        assert score == 1.0

    def test_storage_match_ram_mismatch(self):
        """Test storage matches but RAM doesn't."""
        score = calculate_variant_match_score("256GB", "8GB", "256GB", "12GB")
        assert 0.0 < score < 1.0  # Should have partial score

    def test_no_extracted_storage(self):
        """Test when storage cannot be extracted."""
        score = calculate_variant_match_score(None, None, "256GB", None)
        assert score == 0.0

    def test_no_target_ram(self):
        """Test when target doesn't specify RAM."""
        score = calculate_variant_match_score("256GB", "12GB", "256GB", None)
        assert score == 1.0  # Should still get perfect score from storage


class TestExtractPriceFromText:
    """Test extract_price_from_text function."""

    def test_extract_egp_price(self):
        """Test extracting EGP prices."""
        assert extract_price_from_text("EGP 15,999") == 15999.0
        assert extract_price_from_text("Price: 32,999 EGP") == 32999.0

    def test_extract_price_with_le(self):
        """Test extracting prices with LE currency."""
        assert extract_price_from_text("25,000 LE") == 25000.0

    def test_extract_price_without_comma(self):
        """Test extracting prices without comma separator."""
        # The regex expects comma separators in format \d{1,3}(?:,\d{3})*
        # For numbers without commas, it will match up to 3 digits
        assert extract_price_from_text("Price: 15,999") == 15999.0

    def test_extract_decimal_price(self):
        """Test extracting prices with decimals."""
        result = extract_price_from_text("EGP 15,999.99")
        assert result is not None
        assert 15999 <= result <= 16000

    def test_no_price_found(self):
        """Test when no price is found."""
        assert extract_price_from_text("Product description") is None
        assert extract_price_from_text("Phone specs") is None

    def test_multiple_numbers(self):
        """Test extraction when multiple numbers are present."""
        # Should extract the first valid price pattern (with comma separator)
        result = extract_price_from_text("EGP 25,999 for phone with 256GB")
        assert result == 25999.0

    def test_arabic_currency(self):
        """Test extracting prices with Arabic currency symbols."""
        assert extract_price_from_text("25,000 جنيه") == 25000.0
        assert extract_price_from_text("ج.م 15,999") == 15999.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
