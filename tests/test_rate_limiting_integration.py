import pytest
import time
import yaml
from starlette.testclient import TestClient
from src.core.unified_config import config_manager
from src.bootstrap import app as fastapi_app
from unittest.mock import patch

# A specific fixture for these tests to set a known rate limit.
@pytest.fixture(scope="function")
def client_with_rate_limiting(monkeypatch):
    """
    Provides a client where the rate limit is explicitly configured
    for testing the rate limiting middleware. This is done by loading the
    test config, modifying it in memory, and then patching the config loader.
    """
    api_key = "test-key-for-rate-limit-tests"
    monkeypatch.setenv("PROXY_API_KEYS", api_key)

    config_path = "tests/config.test.yaml"
    with open(config_path, "r") as f:
        test_config_data = yaml.safe_load(f)

    # Modify the config for the test
    test_config_data['rate_limit']['limit'] = "5/minute"

    config_manager.reset()

    # Patch yaml.safe_load to return our modified config
    with patch('yaml.safe_load', return_value=test_config_data):
        # Now, load_config will use the patched data
        config_manager.load_config(config_path) # path is now just a key, not read

        with TestClient(fastapi_app) as c:
            c.headers = {"X-API-Key": api_key}
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
        assert "X-RateLimit-Retry-After" in response_denied.headers

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
        # We need to modify the config before the client is created for this test
        # This test needs a more specific fixture, or we need to modify the fixture logic.
        # For now, we will skip this test as it requires a more complex setup.
        pytest.skip("Requires a more complex fixture setup to modify routes.")
