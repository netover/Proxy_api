import asyncio
import time
import pytest
from unittest.mock import MagicMock

from src.core.rate_limiter import TokenBucket, TokenBucketRateLimiter, token_bucket_rate_limit, rate_limiter
from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestTokenBucket:
    """Test cases for TokenBucket class"""

    def test_token_bucket_initialization(self):
        """Test token bucket initialization"""
        capacity = 100
        refill_rate = 10.0  # tokens per second
        bucket = TokenBucket(capacity, refill_rate)

        assert bucket.capacity == capacity
        assert bucket.refill_rate == refill_rate
        assert bucket.tokens == capacity
        assert bucket.last_refill <= time.time()

    def test_consume_success(self):
        """Test successful token consumption"""
        bucket = TokenBucket(100, 10.0)

        # Should allow consumption
        assert bucket.consume(1) == True
        assert bucket.tokens == 99

    def test_consume_failure_insufficient_tokens(self):
        """Test token consumption failure when insufficient tokens"""
        bucket = TokenBucket(5, 10.0)

        # Consume all tokens
        for _ in range(5):
            assert bucket.consume(1) == True

        # Should fail when no tokens left
        assert bucket.consume(1) == False
        assert bucket.tokens == 0

    def test_token_refill(self):
        """Test token refill over time"""
        bucket = TokenBucket(10, 2.0)  # 2 tokens per second

        # Consume some tokens
        bucket.consume(5)
        assert bucket.tokens == 5

        # Simulate time passage (3 seconds)
        initial_time = bucket.last_refill
        bucket.last_refill = initial_time - 3

        # Should refill tokens
        bucket._refill()
        expected_tokens = min(10, 5 + (3 * 2.0))  # 5 + 6 = 11, capped at 10
        assert bucket.tokens == expected_tokens

    def test_get_reset_time_full_bucket(self):
        """Test reset time when bucket is full"""
        bucket = TokenBucket(10, 2.0)
        assert bucket.get_reset_time() == 0.0

    def test_get_reset_time_partial_bucket(self):
        """Test reset time when bucket has tokens but not full"""
        bucket = TokenBucket(10, 2.0)

        # Consume some tokens
        bucket.consume(7)
        assert bucket.tokens == 3

        # Reset time should be (10-3) / 2.0 = 3.5 seconds
        reset_time = bucket.get_reset_time()
        assert abs(reset_time - 3.5) < 0.1

    def test_get_tokens_remaining(self):
        """Test getting remaining tokens"""
        bucket = TokenBucket(10, 2.0)

        bucket.consume(3)
        assert bucket.get_tokens_remaining() == 7


class TestTokenBucketRateLimiter:
    """Test cases for TokenBucketRateLimiter class"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        rpm = 60
        limiter = TokenBucketRateLimiter(rpm)

        assert limiter.requests_per_minute == rpm
        assert limiter.capacity == rpm
        assert limiter.refill_rate == rpm / 60.0
        assert isinstance(limiter.buckets, dict)

    def test_is_allowed_first_request(self):
        """Test first request is allowed"""
        limiter = TokenBucketRateLimiter(60)

        allowed, reset_time = limiter.is_allowed("192.168.1.1")

        assert allowed == True
        assert reset_time == 0.0
        assert "192.168.1.1" in limiter.buckets

    def test_is_allowed_under_limit(self):
        """Test requests under limit are allowed"""
        limiter = TokenBucketRateLimiter(10)  # 10 requests per minute

        # Should allow all requests within capacity
        for i in range(10):
            allowed, reset_time = limiter.is_allowed("192.168.1.1")
            assert allowed == True

    def test_is_allowed_over_limit(self):
        """Test requests over limit are blocked"""
        limiter = TokenBucketRateLimiter(5)  # 5 requests per minute

        # Use up all tokens
        for i in range(5):
            allowed, _ = limiter.is_allowed("192.168.1.1")
            assert allowed == True

        # Next request should be blocked
        allowed, reset_time = limiter.is_allowed("192.168.1.1")
        assert allowed == False
        assert reset_time > 0

    def test_different_ips_isolated(self):
        """Test that different IPs have separate buckets"""
        limiter = TokenBucketRateLimiter(5)

        # Use up tokens for first IP
        for i in range(5):
            limiter.is_allowed("192.168.1.1")

        # Second IP should still have tokens
        allowed, _ = limiter.is_allowed("192.168.1.2")
        assert allowed == True

    def test_cleanup_old_buckets(self):
        """Test cleanup of old buckets"""
        limiter = TokenBucketRateLimiter(10)

        # Create some buckets
        limiter.is_allowed("192.168.1.1")
        limiter.is_allowed("192.168.1.2")

        initial_count = len(limiter.buckets)

        # Simulate old buckets by setting last_refill to old time
        for bucket in limiter.buckets.values():
            bucket.last_refill = time.time() - 700  # 11+ minutes ago
            bucket.tokens = bucket.capacity  # Full bucket

        # Force cleanup
        limiter._cleanup_old_buckets()

        # Buckets should be removed
        assert len(limiter.buckets) < initial_count

    def test_get_stats_no_key(self):
        """Test getting stats without specific key"""
        limiter = TokenBucketRateLimiter(60)

        stats = limiter.get_stats()

        assert "total_buckets" in stats
        assert "capacity" in stats
        assert "refill_rate" in stats
        assert stats["capacity"] == 60

    def test_get_stats_with_key(self):
        """Test getting stats for specific key"""
        limiter = TokenBucketRateLimiter(60)

        limiter.is_allowed("192.168.1.1")

        stats = limiter.get_stats("192.168.1.1")

        assert "tokens_remaining" in stats
        assert "capacity" in stats
        assert "reset_in_seconds" in stats


class TestTokenBucketRateLimitDependency:
    """Test cases for FastAPI dependency"""

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request object"""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "192.168.1.1"
        return request

    def test_dependency_allows_request_under_limit(self, mock_request):
        """Test dependency allows requests under rate limit"""
        # Initialize rate limiter with high limit for testing
        rate_limiter.token_bucket_limiter = TokenBucketRateLimiter(100)

        # Should not raise exception
        result = asyncio.run(token_bucket_rate_limit(mock_request))
        assert result is None

    def test_dependency_blocks_request_over_limit(self, mock_request):
        """Test dependency blocks requests over rate limit"""
        # Initialize rate limiter with low limit for testing
        rate_limiter.token_bucket_limiter = TokenBucketRateLimiter(1)

        # Use up the token
        rate_limiter.token_bucket_limiter.is_allowed("192.168.1.1")

        # Next request should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(token_bucket_rate_limit(mock_request))

        assert exc_info.value.status_code == 429
        assert "Too Many Requests" in str(exc_info.value.detail)
        assert "Retry-After" in exc_info.value.headers

    def test_dependency_handles_no_client_ip(self):
        """Test dependency handles requests without client IP"""
        request = MagicMock()
        request.client = None

        rate_limiter.token_bucket_limiter = TokenBucketRateLimiter(100)

        # Should not raise exception and use "unknown" as key
        result = asyncio.run(token_bucket_rate_limit(request))
        assert result is None


class TestIntegrationWithConfig:
    """Integration tests with configuration"""

    def test_rate_limiter_configures_from_config(self):
        """Test rate limiter configures from unified config"""
        # Mock config object
        mock_config = MagicMock()
        mock_config.settings = MagicMock()
        mock_config.settings.rate_limit_rpm = 50

        rate_limiter.configure_from_config(mock_config)

        assert rate_limiter.token_bucket_limiter is not None
        assert rate_limiter.token_bucket_limiter.requests_per_minute == 50
        assert rate_limiter.token_bucket_limiter.capacity == 50

    def test_rate_limiter_handles_missing_config(self):
        """Test rate limiter handles missing configuration gracefully"""
        # Config without rate_limit_rpm
        mock_config = MagicMock()
        mock_config.settings = MagicMock()
        del mock_config.settings.rate_limit_rpm  # Remove the attribute

        # Should not raise exception
        rate_limiter.configure_from_config(mock_config)


if __name__ == "__main__":
    pytest.main([__file__])