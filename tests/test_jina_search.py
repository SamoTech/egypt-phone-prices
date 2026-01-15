"""
Tests for Jina AI Search Engine
"""

import os
import requests
from engine.discovery.jina_search_engine import JinaSearchEngine


def test_jina_search_engine_init():
    """Test JinaSearchEngine initialization."""
    engine = JinaSearchEngine()
    assert engine is not None
    assert engine.timeout == 15
    assert engine.BASE_SEARCH_URL == "https://s.jina.ai/"
    assert engine.BASE_READER_URL == "https://r.jina.ai/"


def test_jina_search_engine_custom_timeout():
    """Test JinaSearchEngine initialization with custom timeout."""
    engine = JinaSearchEngine(timeout=30)
    assert engine.timeout == 30


def test_jina_search_engine_with_api_key():
    """Test JinaSearchEngine initialization with API key."""
    api_key = "test_api_key_123"
    engine = JinaSearchEngine(api_key=api_key)

    assert engine.api_key == api_key
    assert "Authorization" in engine.session.headers
    assert engine.session.headers["Authorization"] == f"Bearer {api_key}"


def test_jina_search_engine_with_env_api_key(monkeypatch):
    """Test JinaSearchEngine reads API key from environment variable."""
    api_key = "env_api_key_456"
    monkeypatch.setenv("JINA_API_KEY", api_key)

    engine = JinaSearchEngine()

    assert engine.api_key == api_key
    assert "Authorization" in engine.session.headers
    assert engine.session.headers["Authorization"] == f"Bearer {api_key}"


def test_jina_search_engine_no_api_key():
    """Test JinaSearchEngine works without API key (backward compatibility)."""
    # Clear any environment variable
    old_env = os.environ.pop("JINA_API_KEY", None)

    try:
        engine = JinaSearchEngine()

        assert engine.api_key is None
        assert "Authorization" not in engine.session.headers
    finally:
        # Restore environment variable if it existed
        if old_env:
            os.environ["JINA_API_KEY"] = old_env


def test_jina_search_engine_api_key_priority():
    """Test that explicit API key takes priority over environment variable."""
    explicit_key = "explicit_key"
    env_key = "env_key"

    # Set environment variable
    old_env = os.environ.get("JINA_API_KEY")
    os.environ["JINA_API_KEY"] = env_key

    try:
        engine = JinaSearchEngine(api_key=explicit_key)

        # Explicit key should take priority
        assert engine.api_key == explicit_key
        assert engine.session.headers["Authorization"] == f"Bearer {explicit_key}"
    finally:
        # Restore environment variable
        if old_env:
            os.environ["JINA_API_KEY"] = old_env
        else:
            os.environ.pop("JINA_API_KEY", None)


def test_jina_search_basic(monkeypatch):
    """Test basic search functionality."""
    engine = JinaSearchEngine()

    # Mock response
    mock_response_data = {
        "data": [
            {
                "title": "iPhone 15 Pro Max - Amazon Egypt",
                "description": "Buy iPhone 15 Pro Max 256GB for EGP 45,999",
                "url": "https://amazon.eg/iphone-15-pro-max",
            }
        ]
    }

    class MockResponse:
        def json(self):
            return mock_response_data

        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    results = engine.search("iPhone 15 Pro Max Egypt")

    assert len(results) > 0
    assert "title" in results[0]
    assert "url" in results[0]
    assert "snippet" in results[0]
    assert "position" in results[0]
    assert results[0]["title"] == "iPhone 15 Pro Max - Amazon Egypt"
    assert results[0]["url"] == "https://amazon.eg/iphone-15-pro-max"


def test_jina_search_list_format(monkeypatch):
    """Test search with list format response."""
    engine = JinaSearchEngine()

    # Mock response as list
    mock_response_data = [
        {
            "title": "Samsung Galaxy S24",
            "content": "Latest Samsung flagship",
            "url": "https://example.com/s24",
        }
    ]

    class MockResponse:
        def json(self):
            return mock_response_data

        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    results = engine.search("Samsung Galaxy S24")

    assert len(results) > 0
    assert results[0]["title"] == "Samsung Galaxy S24"
    assert "Latest Samsung flagship" in results[0]["snippet"]


def test_jina_search_max_results(monkeypatch):
    """Test search with max_results parameter."""
    engine = JinaSearchEngine()

    # Mock response with many items
    mock_response_data = {
        "data": [
            {
                "title": f"Result {i}",
                "description": f"Desc {i}",
                "url": f"https://example.com/{i}",
            }
            for i in range(20)
        ]
    }

    class MockResponse:
        def json(self):
            return mock_response_data

        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    results = engine.search("test query", max_results=5)

    assert len(results) == 5


def test_jina_search_timeout(monkeypatch):
    """Test search timeout handling."""
    engine = JinaSearchEngine()

    def mock_get(*args, **kwargs):
        raise requests.exceptions.Timeout("Request timed out")

    monkeypatch.setattr(engine.session, "get", mock_get)

    results = engine.search("test query")

    # Should return empty list on timeout
    assert results == []


def test_jina_search_request_exception(monkeypatch):
    """Test search request exception handling."""
    engine = JinaSearchEngine()

    def mock_get(*args, **kwargs):
        raise requests.exceptions.RequestException("Connection error")

    monkeypatch.setattr(engine.session, "get", mock_get)

    results = engine.search("test query")

    # Should return empty list on error
    assert results == []


def test_jina_search_unexpected_format(monkeypatch):
    """Test search with unexpected response format."""
    engine = JinaSearchEngine()

    class MockResponse:
        def json(self):
            return "unexpected string response"

        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    results = engine.search("test query")

    # Should return empty list on unexpected format
    assert results == []


def test_jina_store_specific_search(monkeypatch):
    """Test store-specific search."""
    engine = JinaSearchEngine()

    captured_url = []

    class MockResponse:
        def json(self):
            return {"data": []}

        def raise_for_status(self):
            pass

    def mock_get(url, *args, **kwargs):
        captured_url.append(url)
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    engine.search_store_specific("Samsung", "Galaxy S24", "256GB", "noon.com")

    # Verify query includes site: parameter (will be URL-encoded)
    assert len(captured_url) > 0
    assert "Samsung" in captured_url[0]
    assert "Galaxy" in captured_url[0]
    assert "256GB" in captured_url[0]
    # site:noon.com will be encoded as site%3Anoon.com
    assert ("site:noon.com" in captured_url[0] or "site%3Anoon.com" in captured_url[0])


def test_jina_store_specific_search_no_storage(monkeypatch):
    """Test store-specific search without storage."""
    engine = JinaSearchEngine()

    captured_url = []

    class MockResponse:
        def json(self):
            return {"data": []}

        def raise_for_status(self):
            pass

    def mock_get(url, *args, **kwargs):
        captured_url.append(url)
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    engine.search_store_specific("Apple", "iPhone 15", store_domain="amazon.eg")

    # Verify query (site:amazon.eg will be encoded as site%3Aamazon.eg)
    assert len(captured_url) > 0
    assert "Apple" in captured_url[0]
    assert "iPhone" in captured_url[0]
    assert ("site:amazon.eg" in captured_url[0] or "site%3Aamazon.eg" in captured_url[0])


def test_jina_read_url(monkeypatch):
    """Test Jina Reader functionality."""
    engine = JinaSearchEngine()

    class MockResponse:
        text = "# Sample Markdown Content\n\nThis is a test."

        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    content = engine.read_url("https://example.com/page")

    assert content == "# Sample Markdown Content\n\nThis is a test."


def test_jina_read_url_error(monkeypatch):
    """Test Jina Reader error handling."""
    engine = JinaSearchEngine()

    def mock_get(*args, **kwargs):
        raise requests.exceptions.RequestException("Error")

    monkeypatch.setattr(engine.session, "get", mock_get)

    content = engine.read_url("https://example.com/page")

    # Should return empty string on error
    assert content == ""


def test_jina_search_snippet_truncation(monkeypatch):
    """Test that snippets are truncated to 500 characters."""
    engine = JinaSearchEngine()

    long_description = "x" * 1000
    mock_response_data = {
        "data": [
            {
                "title": "Test",
                "description": long_description,
                "url": "https://example.com",
            }
        ]
    }

    class MockResponse:
        def json(self):
            return mock_response_data

        def raise_for_status(self):
            pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(engine.session, "get", mock_get)

    results = engine.search("test")

    assert len(results) > 0
    assert len(results[0]["snippet"]) == 500
