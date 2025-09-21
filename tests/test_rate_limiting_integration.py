import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# The app from bootstrap is already configured, we can use it directly
from src.bootstrap import app
from src.core.config.models import UnifiedConfig, RateLimitConfig
from src.middleware.rate_limiter import RateLimitingMiddleware

@pytest.fixture(scope="function")
def client_with_rate_limiting(monkeypatch):
    """
    Provides a TestClient with a specific rate-limiting configuration
    and authentication set up for isolated testing.
    """
    # Set the API key in the environment before the app starts
    monkeypatch.setenv("PROXY_API_KEYS", "test-key-for-rate-limit-tests")

    # Create a mock UnifiedConfig object
    mock_config = UnifiedConfig()

    # Define a specific rate limit configuration for this test
    mock_config.rate_limit = RateLimitConfig(
        routes={
            "/v1/models": "5/minute",
            "/v1/chat/completions": "2/minute",
        },
        default="10/minute"
    )

    # Before the TestClient starts the app, patch the get_config function
    # to return our mock config instead of reading from the file.
    monkeypatch.setattr("src.core.config.manager.get_config", lambda: mock_config)

    # Now, when the TestClient starts the app and the lifespan runs,
    # it will use our mocked config and the API key from the environment.
    try:
        with TestClient(app) as client:
            yield client
    finally:
        # Teardown: find the middleware instance and reset its state
        # to ensure no state leaks between tests.
        for middleware in app.user_middleware:
            if hasattr(middleware.cls, "reset"):
                # The middleware instance is on middleware.options['app']
                # No, that's not right. The instance is middleware.cls
                # Let's check starlette source. The instance is just middleware.cls
                # No, that's the class. The instance is wrapped.
                # Let's try to access the instance via the app's middleware stack
                # The actual instance is not directly exposed in a simple way.
                # Let's find the actual instance on the app object.
                # It's app.middleware_stack which is the app itself after wrapping.
                # This is getting complicated. Let's find a simpler way.
                # The middleware instance is created when app.add_middleware is called.
                # The app object is global. So the middleware is also global.
                # I can find it in app.user_middleware

                # The middleware object in app.user_middleware is a Middleware object
                # which has a `cls` attribute for the class, and `options`.
                # The actual instance is not stored there.
                # This is a problem with how FastAPI/Starlette manages middleware.

                # Let's try another way. The middleware is a global-like instance
                # because the 'app' is global. I can iterate through app.middleware
                # and find the one that is my class.
                # app.middleware is a list of dicts.

                # Let's find the instance on the app object itself.
                # The app is wrapped by the middleware.
                # So app.app is the next middleware, and so on.

                # Let's iterate through the middleware stack
                current_app = app
                while hasattr(current_app, 'app'):
                    if isinstance(current_app, RateLimitingMiddleware):
                        current_app.reset()
                        break
                    # This check is needed for the ErrorMiddleware which is the last one.
                    if not hasattr(current_app.app, 'app'):
                         break
                    current_app = current_app.app

# Let's correct the above logic. Starlette's `app.user_middleware` contains
# `Middleware` objects. The actual instantiated middleware is part of the stack
# but not easily accessible.
# The easiest way is to find the instance in the actual stack.
# The app object is wrapped in middleware layers.
# app -> GZip -> CORSMiddleware -> SecurityHeaders -> RateLimitingMiddleware -> router
# So I need to traverse app.app.app.app ...
# This is fragile.

# A better way: The middleware is added to `app.middleware_stack`.
# The `app.middleware_stack` is the entry point for requests.
# It is the result of wrapping the app in all middleware.
# The instance is `app.middleware_stack`. Let's see its type.
# It's the GzipMiddleware instance. `app.middleware_stack.app` is the CORSMiddleware.
# Let's traverse it.

        # Find the middleware and reset it
        m_app = app.middleware_stack
        while hasattr(m_app, 'app'):
            if isinstance(m_app, RateLimitingMiddleware):
                m_app.reset()
                break
            m_app = m_app.app



class TestRateLimitingMiddleware:
    """
    Integration tests for the new RateLimitingMiddleware.
    """

    def test_endpoint_under_limit(self, client_with_rate_limiting):
        """
        Tests that a request to a rate-limited endpoint is successful
        when the client is under the defined limit.
        """
        headers = {"X-API-Key": "test-key-for-rate-limit-tests"}
        response = client_with_rate_limiting.get("/v1/models", headers=headers)
        assert response.status_code == 200


    def test_endpoint_over_limit(self, client_with_rate_limiting):
        """
        Tests that requests to a rate-limited endpoint are blocked
        once the rate limit has been exceeded.
        """
        headers = {"X-API-Key": "test-key-for-rate-limit-tests"}
        # Provide a valid-enough body to pass Pydantic validation
        valid_body = {"model": "test-model", "messages": [{"role": "user", "content": "hello"}]}

        # The limit for /v1/chat/completions is 2/minute
        for _ in range(2):
            response = client_with_rate_limiting.post("/v1/chat/completions", headers=headers, json=valid_body)
            # This will now fail at the provider_factory level, which is fine for this test
            assert response.status_code != 429

        # The third request should be blocked by the rate limiter
        response = client_with_rate_limiting.post("/v1/chat/completions", headers=headers, json=valid_body)
        assert response.status_code == 429
        data = response.json()
        assert "Rate limit exceeded" in data.get("detail")

    def test_non_limited_route_is_not_affected(self, client_with_rate_limiting):
        """
        Tests that a route without a specific limit is not affected by the
        rate limiter, even when other routes are exhausted.
        """
        headers = {"X-API-Key": "test-key-for-rate-limit-tests"}
        valid_body = {"model": "test-model", "messages": [{"role": "user", "content": "hello"}]}

        # Exhaust the limit for /v1/chat/completions
        for _ in range(2):
            client_with_rate_limiting.post("/v1/chat/completions", headers=headers, json=valid_body)

        response = client_with_rate_limiting.post("/v1/chat/completions", headers=headers, json=valid_body)
        assert response.status_code == 429

        # A request to a non-configured endpoint should still go through
        response = client_with_rate_limiting.get("/health")
        assert response.status_code == 200

    def test_different_clients_have_separate_buckets(self, client_with_rate_limiting, monkeypatch):
        """
        Tests that different clients (identified by IP) have separate rate limits.
        """
        # Mock the key function to simulate different clients.
        # We must patch the function where it's *used* (in the middleware module),
        # not where it's defined (in the slowapi.util module).
        mock_key_func = MagicMock()
        monkeypatch.setattr("src.middleware.rate_limiter.get_remote_address", mock_key_func)

        headers = {"X-API-Key": "test-key-for-rate-limit-tests"}
        valid_body = {"model": "test-model", "messages": [{"role": "user", "content": "hello"}]}

        # Exhaust the limit for client 1
        mock_key_func.return_value = "127.0.0.1"
        for _ in range(2):
            response = client_with_rate_limiting.post("/v1/chat/completions", headers=headers, json=valid_body)
            assert response.status_code != 429, "Client 1's requests should be allowed before exhausting the limit"

        response = client_with_rate_limiting.post("/v1/chat/completions", headers=headers, json=valid_body)
        assert response.status_code == 429, "Client 1's third request should be blocked"

        # Make a request from client 2, it should be successful
        mock_key_func.return_value = "192.168.1.100"
        response_from_other_client = client_with_rate_limiting.post(
            "/v1/chat/completions",
            headers=headers, # No need for X-Forwarded-For since we are mocking the function
            json=valid_body
        )
        assert response_from_other_client.status_code != 429, "Client 2's first request should be successful"

    def test_default_rate_limit_is_applied(self, client_with_rate_limiting):
        """
        Tests that the default rate limit is applied to routes that
        do not have a specific limit defined.
        """
        headers = {"X-API-Key": "test-key-for-rate-limit-tests"}

        # The route /v1/config/status is not in our test config, so it should use default (10/min)
        for i in range(10):
            response = client_with_rate_limiting.get("/v1/config/status", headers=headers)
            assert response.status_code != 429, f"Request {i+1} should have passed"

        # The 11th request should be blocked
        response = client_with_rate_limiting.get("/v1/config/status", headers=headers)
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json().get("detail")
