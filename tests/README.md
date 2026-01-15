# Test Suite Documentation

This directory contains the comprehensive test suite for the Egyptian Phone Price & Specs Comparison Platform.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual modules
│   ├── test_matcher.py      # Fuzzy matching logic (69 tests)
│   ├── test_validator.py    # Offer validation (38 tests)
│   ├── test_normalizer.py   # Brand/model normalization (45 tests)
│   └── test_base_scraper.py # Circuit breaker logic (17 tests)
├── integration/             # Integration tests
│   └── test_matching_validation.py  # End-to-end workflows (10 tests)
└── e2e/                     # End-to-end tests (future)
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Specific Test File
```bash
pytest tests/unit/test_matcher.py -v
```

### With Coverage Report
```bash
pytest tests/ --cov=engine --cov=scrapers --cov=utils --cov-report=html
```

### Run Specific Test
```bash
pytest tests/unit/test_matcher.py::TestFuzzyMatchPhone::test_perfect_match -v
```

## Coverage Targets

- **Overall**: 95%+
- **Engine modules**: 95%+ ✅ (Currently achieved)
- **Scrapers**: 80%+
- **Utils**: 90%+

## Test Categories

### Unit Tests (129 tests)

#### test_matcher.py (69 tests)
Tests fuzzy matching logic for phone products:
- Brand, model, storage, RAM matching
- Storage/RAM extraction from text
- Price extraction from text
- Variant matching scores

**Coverage**: 95%+ for matcher.py

#### test_validator.py (38 tests)
Tests product validation logic:
- Offer validation against specs
- Accessory detection
- Refurbished/used detection
- Price range validation
- Seller info extraction
- Offer quality scoring

**Coverage**: 91%+ for validator.py

#### test_normalizer.py (45 tests)
Tests brand/model normalization:
- Brand name standardization
- Model name cleaning
- Slug creation
- Storage/RAM normalization

**Coverage**: 100% for normalizer.py

#### test_base_scraper.py (17 tests)
Tests circuit breaker pattern:
- State transitions (CLOSED → OPEN → HALF_OPEN)
- Failure threshold handling
- Recovery timeout logic
- Success/failure tracking

**Coverage**: 55%+ for base_scraper.py

### Integration Tests (10 tests)

#### test_matching_validation.py (10 tests)
Tests complete workflows:
- End-to-end matching pipeline
- Variant extraction and matching
- Multiple offers ranking
- Error handling scenarios

## Code Quality Tools

### Linting
```bash
# Flake8
flake8 engine/ scrapers/ utils/ --statistics

# Pylint
pylint engine/ scrapers/ utils/ --score=yes

# MyPy
mypy engine/ scrapers/ utils/
```

### Security Scanning
```bash
# Bandit
bandit -r engine/ scrapers/ utils/
```

## Continuous Integration

Tests run automatically on:
- Push to main, develop, or copilot/** branches
- Pull requests to main or develop
- Manual workflow dispatch

See `.github/workflows/test.yml` for CI configuration.

## Test Markers

Tests can be marked with pytest markers:
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.security
```

Run tests by marker:
```bash
pytest -m unit
pytest -m "not slow"
```

## Writing New Tests

### Unit Test Template
```python
"""
Unit tests for module_name.
"""

import pytest
from module_name import function_to_test


class TestFunctionName:
    """Test function_to_test function."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        result = function_to_test(input_data)
        assert result == expected_output

    def test_edge_case(self):
        """Test edge case."""
        result = function_to_test(edge_input)
        assert result == expected_output
```

### Test Best Practices
1. **One assertion per test** (when possible)
2. **Clear test names** describing what is being tested
3. **Arrange-Act-Assert** pattern
4. **Test both success and failure paths**
5. **Use fixtures for reusable test data**
6. **Mock external dependencies**

## Current Status

- **Total Tests**: 139
- **Passing**: 139 (100%)
- **Overall Coverage**: 10.4%
- **Engine Coverage**: 95%+ ✅
- **CI/CD**: ✅ Implemented

## Future Enhancements

- [ ] Add E2E tests for complete pipeline execution
- [ ] Add performance/benchmark tests
- [ ] Increase coverage for scrapers and utils
- [ ] Add mutation testing
- [ ] Add property-based testing (Hypothesis)
- [ ] Add load testing for pipelines
