"""
Base scraper class with circuit breaker pattern, retry logic, and error handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Dict
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for handling service failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Attempting recovery, limited requests allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerException: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerException(
                    f"Circuit breaker is OPEN. Retry after "
                    f"{self.recovery_timeout} seconds."
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful request."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker returning to CLOSED state")
        else:
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker returning to OPEN state")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class BaseScraper(ABC):
    """
    Abstract base class for web scrapers with built-in retry logic,
    circuit breaker pattern, and HTTP error handling.
    """
    
    # Default configuration
    DEFAULT_TIMEOUT = 10
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 1.0
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize base scraper.
        
        Args:
            base_url: Base URL for the scraper
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry delay
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Recovery timeout in seconds
            headers: Custom HTTP headers
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        self.session = self._create_session()
        
        # Initialize headers
        default_headers = {"User-Agent": self.DEFAULT_USER_AGENT}
        if headers:
            default_headers.update(headers)
        self.session.headers.update(default_headers)
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_timeout,
            expected_exception=requests.RequestException
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=self.backoff_factor,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.
        
        Args:
            endpoint: API endpoint or path
            
        Returns:
            Full URL
        """
        if self.base_url:
            return urljoin(self.base_url, endpoint)
        return endpoint
    
    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Perform GET request with error handling and circuit breaker.
        
        Args:
            url: URL to request
            params: Query parameters
            headers: Custom headers
            **kwargs: Additional requests arguments
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails
            CircuitBreakerException: If circuit breaker is open
        """
        full_url = self._build_url(url)
        
        def _request():
            return self.session.get(
                full_url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
        
        return self._execute_with_circuit_breaker(_request, "GET", full_url)
    
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Perform POST request with error handling and circuit breaker.
        
        Args:
            url: URL to request
            data: Form data
            json: JSON data
            headers: Custom headers
            **kwargs: Additional requests arguments
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails
            CircuitBreakerException: If circuit breaker is open
        """
        full_url = self._build_url(url)
        
        def _request():
            return self.session.post(
                full_url,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
        
        return self._execute_with_circuit_breaker(_request, "POST", full_url)
    
    def _execute_with_circuit_breaker(
        self,
        func,
        method: str,
        url: str
    ) -> requests.Response:
        """
        Execute request with circuit breaker protection.
        
        Args:
            func: Request function to execute
            method: HTTP method
            url: Request URL
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails
            CircuitBreakerException: If circuit breaker is open
        """
        try:
            response = self.circuit_breaker.call(func)
            response.raise_for_status()
            
            self.logger.info(f"{method} {url} - Status: {response.status_code}")
            return response
            
        except CircuitBreakerException as e:
            self.logger.error(f"Circuit breaker open for {method} {url}: {str(e)}")
            raise
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout for {method} {url}: {str(e)}")
            raise requests.RequestException(f"Request timeout: {str(e)}") from e
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error for {method} {url}: {str(e)}")
            raise requests.RequestException(f"Connection error: {str(e)}") from e
            
        except requests.exceptions.HTTPError as e:
            response = e.response
            status_code = response.status_code if response is not None else "Unknown"
            error_msg = f"HTTP {status_code} for {method} {url}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise requests.RequestException(error_msg) from e
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed for {method} {url}: {str(e)}")
            raise
    
    @abstractmethod
    def scrape(self) -> Any:
        """
        Abstract method for scraping logic.
        
        Must be implemented by subclasses.
        
        Returns:
            Scraped data
        """
        pass
    
    def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()
            self.logger.info("Session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
