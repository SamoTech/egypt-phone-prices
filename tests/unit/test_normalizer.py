"""
Unit tests for engine.normalizer module.
Tests brand/model normalization, slug creation, and storage/RAM normalization.
"""

import pytest
from engine.normalizer import (
    normalize_brand,
    normalize_model,
    create_slug,
    normalize_storage,
    normalize_ram,
)


class TestNormalizeBrand:
    """Test normalize_brand function."""

    def test_uppercase_samsung(self):
        """Test normalizing uppercase Samsung."""
        assert normalize_brand("SAMSUNG") == "Samsung"

    def test_lowercase_apple(self):
        """Test normalizing lowercase Apple."""
        assert normalize_brand("apple") == "Apple"

    def test_mixed_case_xiaomi(self):
        """Test normalizing mixed case Xiaomi."""
        assert normalize_brand("XiAoMi") == "Xiaomi"

    def test_oneplus_variations(self):
        """Test OnePlus brand variations."""
        assert normalize_brand("oneplus") == "OnePlus"
        assert normalize_brand("one plus") == "OnePlus"
        assert normalize_brand("ONE PLUS") == "OnePlus"

    def test_motorola_moto(self):
        """Test Motorola/Moto normalization."""
        assert normalize_brand("motorola") == "Motorola"
        assert normalize_brand("moto") == "Motorola"

    def test_common_brands(self):
        """Test common brand normalizations."""
        assert normalize_brand("oppo") == "Oppo"
        assert normalize_brand("realme") == "Realme"
        assert normalize_brand("google") == "Google"
        assert normalize_brand("nokia") == "Nokia"
        assert normalize_brand("vivo") == "Vivo"
        assert normalize_brand("infinix") == "Infinix"
        assert normalize_brand("tecno") == "Tecno"

    def test_unknown_brand(self):
        """Test unknown brand normalization."""
        result = normalize_brand("UnknownBrand")
        # Should return title case for unknown brands
        assert result == "Unknownbrand"

    def test_empty_brand(self):
        """Test empty brand string."""
        assert normalize_brand("") == ""

    def test_whitespace_handling(self):
        """Test handling of extra whitespace."""
        assert normalize_brand("  samsung  ") == "Samsung"
        assert normalize_brand("one  plus") == "OnePlus"


class TestNormalizeModel:
    """Test normalize_model function."""

    def test_remove_extra_spaces(self):
        """Test removing extra spaces from model name."""
        assert normalize_model("Galaxy  S24   Ultra") == "Galaxy S24 Ultra"

    def test_trim_whitespace(self):
        """Test trimming leading/trailing whitespace."""
        assert normalize_model("  iPhone 15 Pro Max  ") == "iPhone 15 Pro Max"

    def test_single_word_model(self):
        """Test single word model name."""
        assert normalize_model("12R") == "12R"

    def test_empty_model(self):
        """Test empty model string."""
        assert normalize_model("") == ""

    def test_complex_model_name(self):
        """Test complex model name with numbers and text."""
        assert normalize_model("Redmi Note 12 Pro 5G") == "Redmi Note 12 Pro 5G"


class TestCreateSlug:
    """Test create_slug function."""

    def test_samsung_galaxy(self):
        """Test slug creation for Samsung Galaxy."""
        assert create_slug("Samsung", "Galaxy S24 Ultra") == "samsung_galaxy_s24_ultra"

    def test_apple_iphone(self):
        """Test slug creation for Apple iPhone."""
        assert create_slug("Apple", "iPhone 15 Pro Max") == "apple_iphone_15_pro_max"

    def test_oneplus_model(self):
        """Test slug creation for OnePlus."""
        assert create_slug("OnePlus", "12R") == "oneplus_12r"

    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        assert create_slug("Samsung", "Galaxy S24+") == "samsung_galaxy_s24"
        assert create_slug("Apple", "iPhone 15 Pro Max (256GB)") == "apple_iphone_15_pro_max_256gb"

    def test_consecutive_underscores(self):
        """Test that consecutive underscores are collapsed."""
        slug = create_slug("Brand", "Model  Name")
        assert "__" not in slug  # No double underscores

    def test_lowercase_output(self):
        """Test that output is lowercase."""
        slug = create_slug("SAMSUNG", "GALAXY S24 ULTRA")
        assert slug == slug.lower()

    def test_alphanumeric_only(self):
        """Test that only alphanumeric and underscores remain."""
        slug = create_slug("Brand!", "Model@123#")
        assert slug == "brand_model123"


class TestNormalizeStorage:
    """Test normalize_storage function."""

    def test_normalize_gb_with_space(self):
        """Test normalizing GB with space."""
        assert normalize_storage("256 GB") == "256GB"

    def test_normalize_tb_with_space(self):
        """Test normalizing TB with space."""
        assert normalize_storage("1 TB") == "1TB"

    def test_normalize_gb_without_b(self):
        """Test normalizing storage with just G."""
        assert normalize_storage("512G") == "512GB"

    def test_already_normalized(self):
        """Test already normalized storage."""
        assert normalize_storage("256GB") == "256GB"
        assert normalize_storage("1TB") == "1TB"

    def test_common_storage_sizes(self):
        """Test common phone storage sizes."""
        assert normalize_storage("64GB") == "64GB"
        assert normalize_storage("128 GB") == "128GB"
        assert normalize_storage("256G") == "256GB"
        assert normalize_storage("512 GB") == "512GB"
        assert normalize_storage("1TB") == "1TB"

    def test_empty_storage(self):
        """Test empty storage string."""
        assert normalize_storage("") is None
        assert normalize_storage(None) is None

    def test_invalid_storage(self):
        """Test invalid storage format."""
        result = normalize_storage("invalid")
        # Should return None for invalid format
        assert result is None

    def test_just_number(self):
        """Test just a number without unit."""
        result = normalize_storage("256")
        assert result == "256GB"  # Should assume GB

    def test_case_insensitive(self):
        """Test case insensitive normalization."""
        assert normalize_storage("256gb") == "256GB"
        assert normalize_storage("1tb") == "1TB"


class TestNormalizeRam:
    """Test normalize_ram function."""

    def test_normalize_ram_with_space(self):
        """Test normalizing RAM with space."""
        assert normalize_ram("12 GB") == "12GB"

    def test_normalize_ram_without_b(self):
        """Test normalizing RAM with just G."""
        assert normalize_ram("8G") == "8GB"

    def test_already_normalized_ram(self):
        """Test already normalized RAM."""
        assert normalize_ram("12GB") == "12GB"
        assert normalize_ram("8GB") == "8GB"

    def test_common_ram_sizes(self):
        """Test common phone RAM sizes."""
        assert normalize_ram("4GB") == "4GB"
        assert normalize_ram("6 GB") == "6GB"
        assert normalize_ram("8G") == "8GB"
        assert normalize_ram("12 GB") == "12GB"
        assert normalize_ram("16GB") == "16GB"

    def test_empty_ram(self):
        """Test empty RAM string."""
        assert normalize_ram("") is None
        assert normalize_ram(None) is None

    def test_invalid_ram(self):
        """Test invalid RAM format."""
        result = normalize_ram("invalid")
        assert result is None

    def test_just_number(self):
        """Test just a number without unit."""
        result = normalize_ram("12")
        assert result == "12GB"  # Should assume GB

    def test_case_insensitive(self):
        """Test case insensitive normalization."""
        assert normalize_ram("12gb") == "12GB"
        assert normalize_ram("8Gb") == "8GB"


class TestEdgeCases:
    """Test edge cases across all normalizer functions."""

    def test_none_inputs(self):
        """Test None inputs are handled gracefully."""
        assert normalize_storage(None) is None
        assert normalize_ram(None) is None

    def test_whitespace_only(self):
        """Test whitespace-only inputs."""
        assert normalize_brand("   ") == ""
        assert normalize_model("   ") == ""

    def test_very_long_strings(self):
        """Test handling of very long strings."""
        long_brand = "A" * 100
        result = normalize_brand(long_brand)
        assert len(result) > 0

        long_model = "Model " * 50
        result = normalize_model(long_model)
        assert len(result) > 0

    def test_unicode_characters(self):
        """Test handling of Unicode characters."""
        # Arabic brand name
        result = normalize_brand("سامسونج")
        assert len(result) > 0

    def test_numbers_only(self):
        """Test brand/model with numbers only."""
        assert normalize_brand("123") == "123"
        assert normalize_model("456") == "456"


class TestIntegration:
    """Test integration between normalizer functions."""

    def test_brand_model_slug_workflow(self):
        """Test typical workflow from brand/model to slug."""
        # Normalize brand and model
        brand = normalize_brand("SAMSUNG")
        model = normalize_model("Galaxy  S24  Ultra")
        
        assert brand == "Samsung"
        assert model == "Galaxy S24 Ultra"
        
        # Create slug
        slug = create_slug(brand, model)
        assert slug == "samsung_galaxy_s24_ultra"

    def test_storage_ram_workflow(self):
        """Test typical storage/RAM normalization workflow."""
        storage = normalize_storage("256 GB")
        ram = normalize_ram("12 GB")
        
        assert storage == "256GB"
        assert ram == "12GB"
        
        # Both should be in consistent format
        assert storage.endswith("GB")
        assert ram.endswith("GB")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
