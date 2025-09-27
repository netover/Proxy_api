import pytest
import time
from starlette.testclient import TestClient
from src.bootstrap import create_app
from unittest.mock import patch
from src.core.config.models import UnifiedConfig
from src.core.security.auth import APIKeyAuth

# This fixture builds on the `test_config` fixture from conftest.py.
@pytest.fixture(scope="function")
def client_with_rate_limiting(test_config: UnifiedConfig, monkeypatch):
    """
    Provides a client where the rate limit is explicitly configured
    for testing. It uses the app factory pattern to create an isolated
    app instance with a modified and authenticated configuration.
    """
    api_key = "test-key-for-rate-limit-tests"

    # Modify the configuration object in memory for this specific test suite.
    test_config.rate_limit.default = "5/minute"
    test_config.proxy_api_keys = [api_key]

    # Create a new, isolated app instance using the modified config.
    app = create_app(test_config)

    with TestClient(app) as c:
        # The API key is now managed by the app's auth system,
        # so we just need to provide it in the headers.
        c.headers["X-API-Key"] = api_key
        yield c

class TestRateLimitingMiddleware:
    """Integration tests for the RateLimitingMiddleware."""

    def test_endpoint_under_limit(self, client_with_rate_limiting: TestClient):
        """
        Tests that a request to a rate-limited endpoint is successful
        when the client is under the defined limit.
        """
        response = client_with_rate_limiting.get("/v1/models")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "4"

    def test_endpoint_over_limit(self, client_with_rate_limiting: TestClient):
        """
        Tests that requests to a rate-limited endpoint are denied
        once the client exceeds the defined limit.
        """
        # Consume the limit
        for _ in range(5):
            response = client_with_rate_limiting.get("/v1/models")
            assert response.status_code == 200

        # The next request should be denied
        response_denied = client_with_rate_limiting.get("/v1/models")
        assert response_denied.status_code == 429
        assert "Too Many Requests" in response_denied.text
        assert "Retry-After" in response_denied.headers

    def test_limit_resets_after_window(self, client_with_rate_limiting: TestClient):
        """
        Tests that the rate limit resets after the window expires.
        """
        # Consume the limit
        for _ in range(5):
            client_with_rate_limiting.get("/v1/models")

        # Wait for the window to reset (using a mock for time.time)
        with patch('time.time', return_value=time.time() + 61):
            response = client_with_rate_limiting.get("/v1/models")
            assert response.status_code == 200
            assert response.headers["X-RateLimit-Remaining"] == "4"

    def test_unlimited_route_not_affected(self, client_with_rate_limiting: TestClient):
        """
        Tests that a route not under the rate limiter is not affected
        even if another route is over limit.
        """
        pytest.skip("Requires a more complex fixture setup to modify routes.")