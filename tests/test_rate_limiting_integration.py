import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from src.core.rate_limiter import TokenBucketRateLimiter, rate_limiter
from src.core.unified_config import RateLimitSettings




@pytest.fixture
def low_rate_limiter():
    """Rate limiter with low limit for testing"""
    limiter = TokenBucketRateLimiter(5)  # 5 requests per minute
    rate_limiter.token_bucket_limiter = limiter
    return limiter


class TestRateLimitingIntegration:
    """Integration tests for rate limiting on actual endpoints"""

    def test_models_endpoint_under_limit(self, client, low_rate_limiter):
        """Test GET /models allows requests under rate limit"""
        response = client.get("/v1/models")

        assert response.status_code == 200
        assert "data" in response.json()

    def test_models_endpoint_over_limit(self, client, low_rate_limiter):
        """Test GET /models blocks requests over rate limit"""
        # Mock client IP to ensure same bucket
        with patch("fastapi.Request") as mock_request_class:
            mock_request = mock_request_class.return_value
            mock_request.client = type("Client", (), {"host": "127.0.0.1"})()

            # Use up all tokens
            for _ in range(5):
                low_rate_limiter.is_allowed("127.0.0.1")

            # Next request should be blocked
            response = client.get("/v1/models")
            assert response.status_code == 429
            assert "Too Many Requests" in response.json()["detail"]["message"]
            assert "Retry-After" in response.headers

    def test_non_rate_limited_endpoints_not_affected(self, client, low_rate_limiter):
        """Test endpoints without rate limiting are not affected"""
        # This endpoint doesn't have rate limiting applied in the router
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_different_ips_have_separate_limits(self, client, low_rate_limiter):
        """Test different IP addresses have separate rate limits"""
        # This test would require mocking different client IPs
        # For now, just verify the rate limiter logic works
        assert low_rate_limiter.is_allowed("192.168.1.1")[0] == True
        assert low_rate_limiter.is_allowed("192.168.1.2")[0] == True

    def test_retry_after_header_format(self, client, low_rate_limiter):
        """Test Retry-After header is properly formatted"""
        # Use up all tokens
        for _ in range(5):
            low_rate_limiter.is_allowed("127.0.0.1")

        # Next request should be blocked with Retry-After header
        response = client.get("/v1/models")

        assert response.status_code == 429
        assert "Retry-After" in response.headers

        # Retry-After should be a number
        retry_after = response.headers["Retry-After"]
        assert retry_after.isdigit()
        assert int(retry_after) > 0

    def test_rate_limit_resets_over_time(self, client, low_rate_limiter):
        """Test rate limits reset over time (simplified test)"""
        # Use up all tokens
        for _ in range(5):
            assert low_rate_limiter.is_allowed("127.0.0.1")[0] == True

        # Next request should be blocked
        assert low_rate_limiter.is_allowed("127.0.0.1")[0] == False

        # Simulate time passage
        bucket = low_rate_limiter.buckets["127.0.0.1"]
        initial_tokens = bucket.tokens

        # Manually refill some tokens by advancing time
        bucket.last_refill = bucket.last_refill - 10  # 10 seconds ago
        bucket._refill()

        # Should have more tokens now
        assert bucket.tokens > initial_tokens


class TestRateLimiterConfiguration:
    """Test rate limiter configuration from config"""

    def test_configuration_from_settings(self):
        """Test rate limiter configures from a RateLimitSettings object."""
        # Create a mock settings object
        settings = RateLimitSettings(
            requests_per_window=120,
            window_seconds=60,
            burst_limit=20,
            routes={
                "/v1/models": "10/minute",
                "/v1/providers": "20/minute",
            },
        )

        # Configure rate limiter
        rate_limiter.configure_from_settings(settings)

        # Check that the token bucket was initialized correctly (120 reqs/60s = 120 rpm)
        assert rate_limiter.token_bucket_limiter is not None
        assert rate_limiter.token_bucket_limiter.requests_per_minute == 120

        # Check that routes were configured
        assert rate_limiter.get_route_limit("/v1/models") == "10/minute"
        assert rate_limiter.get_route_limit("/v1/providers") == "20/minute"
        # Check fallback to default
        assert rate_limiter.get_route_limit("/v1/unknown") == "120/60s"


class TestRateLimitStats:
    """Test rate limiter statistics"""

    def test_token_bucket_stats(self, low_rate_limiter):
        """Test token bucket provides useful statistics"""
        # Make some requests
        low_rate_limiter.is_allowed("127.0.0.1")

        stats = low_rate_limiter.get_stats()

        assert "total_buckets" in stats
        assert "capacity" in stats
        assert "refill_rate" in stats
        assert stats["capacity"] == 5

    def test_bucket_specific_stats(self, low_rate_limiter):
        """Test getting stats for specific bucket"""
        low_rate_limiter.is_allowed("127.0.0.1")

        stats = low_rate_limiter.get_stats("127.0.0.1")

        assert "tokens_remaining" in stats
        assert "capacity" in stats
        assert "reset_in_seconds" in stats


if __name__ == "__main__":
    pytest.main([__file__])
