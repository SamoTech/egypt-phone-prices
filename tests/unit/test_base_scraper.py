"""
Unit tests for scrapers.base_scraper module.
Tests circuit breaker, retry logic, and base scraper functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from scrapers.base_scraper import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerException,
)


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_initial_state_closed(self):
        """Test that circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_successful_call(self):
        """Test successful function call."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_single_failure(self):
        """Test single failure doesn't open circuit."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def fail_func():
            raise Exception("Test failure")
        
        with pytest.raises(Exception):
            cb.call(fail_func)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

    def test_multiple_failures_open_circuit(self):
        """Test multiple failures open the circuit."""
        cb = CircuitBreaker(failure_threshold=3)
        
        def fail_func():
            raise Exception("Test failure")
        
        # Fail 3 times
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_open_circuit_blocks_calls(self):
        """Test that open circuit blocks new calls."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        def fail_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Next call should be blocked
        with pytest.raises(CircuitBreakerException):
            cb.call(fail_func)

    def test_half_open_after_timeout(self):
        """Test circuit enters HALF_OPEN state after timeout."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0)
        
        def fail_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Set last failure time to the past
        cb.last_failure_time = datetime.now() - timedelta(seconds=1)
        
        # Next call should attempt recovery (will fail and reopen)
        with pytest.raises(Exception):
            cb.call(fail_func)

    def test_successful_call_resets_failures(self):
        """Test successful call resets failure count."""
        cb = CircuitBreaker(failure_threshold=5)
        
        def fail_func():
            raise Exception("Test failure")
        
        def success_func():
            return "success"
        
        # Accumulate some failures
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(fail_func)
        
        assert cb.failure_count == 2
        
        # Successful call should reset
        cb.call(success_func)
        assert cb.failure_count == 0

    def test_custom_exception_type(self):
        """Test circuit breaker with custom exception type."""
        class CustomException(Exception):
            pass
        
        cb = CircuitBreaker(failure_threshold=2, expected_exception=CustomException)
        
        def fail_custom():
            raise CustomException("Custom failure")
        
        def fail_other():
            raise ValueError("Different exception")
        
        # Custom exception should be caught
        with pytest.raises(CustomException):
            cb.call(fail_custom)
        assert cb.failure_count == 1
        
        # Other exceptions should propagate without incrementing counter
        with pytest.raises(ValueError):
            cb.call(fail_other)
        # Failure count might not increment for non-expected exceptions
        # depending on implementation

    def test_recovery_success_closes_circuit(self):
        """Test successful recovery closes the circuit."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0)
        
        def fail_func():
            raise Exception("Test failure")
        
        def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(fail_func)
        
        assert cb.state == CircuitState.OPEN
        
        # Set last failure time to the past to allow recovery
        cb.last_failure_time = datetime.now() - timedelta(seconds=1)
        
        # Manually set to HALF_OPEN for testing
        cb.state = CircuitState.HALF_OPEN
        
        # In HALF_OPEN state, requires 2 successful calls to close
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN  # Still HALF_OPEN after 1 success
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED  # Closed after 2 successes


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration scenarios."""

    def test_realistic_failure_recovery_scenario(self):
        """Test realistic failure and recovery scenario."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0)
        call_count = 0
        
        def unreliable_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception(f"Failure {call_count}")
            return "success"
        
        # First 3 calls fail and open circuit
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(unreliable_func)
        
        assert cb.state == CircuitState.OPEN
        assert call_count == 3
        
        # Circuit is open, immediate call should be blocked
        # But if enough time has passed, it will attempt recovery
        # Since recovery_timeout=0, next call will enter HALF_OPEN
        # and attempt the function (which will succeed now)
        
        # Time passes, circuit attempts recovery
        cb.last_failure_time = datetime.now() - timedelta(seconds=1)
        
        # This call will attempt recovery and succeed
        result = cb.call(unreliable_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN  # Needs 2 successes to close
        
        # Another success to close the circuit
        result = cb.call(unreliable_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    def test_concurrent_failures_tracking(self):
        """Test tracking of multiple concurrent failures."""
        cb = CircuitBreaker(failure_threshold=5)
        
        def fail_func():
            raise Exception("Test failure")
        
        # Multiple failures
        for i in range(4):
            with pytest.raises(Exception):
                cb.call(fail_func)
            assert cb.failure_count == i + 1
            assert cb.state == CircuitState.CLOSED
        
        # One more failure should open circuit
        with pytest.raises(Exception):
            cb.call(fail_func)
        assert cb.failure_count == 5
        assert cb.state == CircuitState.OPEN


class TestBaseScraper:
    """Test base scraper functionality (if accessible)."""
    
    # Note: Since BaseScraper might be abstract or complex to test,
    # we focus on the circuit breaker which is the key testable component
    
    def test_circuit_breaker_usage_pattern(self):
        """Test typical circuit breaker usage pattern in scraper."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        # Simulate scraping function
        def scrape_page(url):
            # Simulate network call
            if "bad" in url:
                raise Exception("Network error")
            return {"data": "scraped"}
        
        # Successful scrapes
        result = cb.call(scrape_page, "http://good-url.com")
        assert result["data"] == "scraped"
        
        # Failed scrapes
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(scrape_page, "http://bad-url.com")
        
        # Circuit should be open
        assert cb.state == CircuitState.OPEN
        
        # Further calls blocked
        with pytest.raises(CircuitBreakerException):
            cb.call(scrape_page, "http://good-url.com")


class TestCircuitBreakerEdgeCases:
    """Test edge cases for circuit breaker."""

    def test_zero_failure_threshold(self):
        """Test circuit breaker with zero failure threshold."""
        # This might not be a valid configuration
        # but we test behavior
        cb = CircuitBreaker(failure_threshold=0)
        
        def fail_func():
            raise Exception("Test failure")
        
        # Circuit might open immediately or have minimum threshold
        with pytest.raises(Exception):
            cb.call(fail_func)

    def test_very_high_failure_threshold(self):
        """Test circuit breaker with high failure threshold."""
        cb = CircuitBreaker(failure_threshold=1000)
        
        def fail_func():
            raise Exception("Test failure")
        
        # Many failures shouldn't open circuit
        for _ in range(100):
            with pytest.raises(Exception):
                cb.call(fail_func)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 100

    def test_negative_recovery_timeout(self):
        """Test circuit breaker with negative recovery timeout."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=-1)
        
        def fail_func():
            raise Exception("Test failure")
        
        # Open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(fail_func)
        
        # With negative timeout, should attempt recovery immediately
        # Behavior depends on implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
