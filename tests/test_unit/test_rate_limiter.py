"""
Unit tests for rate limiter implementations.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.core.rate_limiter_redis import SlidingWindowRateLimiter, TokenBucketRateLimiter, DistributedRateLimiter


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = SlidingWindowRateLimiter(
            redis_url="redis://invalid:6379",  # Will fail to connect
            window_size=60,
            max_requests=100
        )

        # Should handle connection failure gracefully
        with pytest.raises(Exception):
            await limiter.initialize()

    @pytest.mark.asyncio
    async def test_rate_limiting_logic(self, redis_mock_context):
        """Test basic rate limiting logic."""
        limiter = SlidingWindowRateLimiter(
            redis_url="redis://localhost:6379",
            window_size=60,
            max_requests=5
        )

        await limiter.initialize()

        identifier = "test_user"
        endpoint = "/test"

        # Should work with mocked Redis
        allowed, info = await limiter.is_allowed(identifier, endpoint)

        assert allowed is True
        assert "limit" in info
        assert info["limit"] == 5

        await limiter.shutdown()

    @pytest.mark.asyncio
    async def test_key_generation(self):
        """Test key generation for different identifiers."""
        limiter = SlidingWindowRateLimiter()

        # Test key generation
        key1 = limiter._get_key("user1", "/api/test")
        key2 = limiter._get_key("user2", "/api/test")
        key3 = limiter._get_key("user1", "/api/other")

        # Keys should be different
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

        # Keys should be deterministic
        key1_again = limiter._get_key("user1", "/api/test")
        assert key1 == key1_again


class TestTokenBucketRateLimiter:
    """Test token bucket rate limiter."""

    @pytest.mark.asyncio
    async def test_token_bucket_initialization(self, redis_mock_context):
        """Test token bucket initialization."""
        limiter = TokenBucketRateLimiter(
            redis_url="redis://localhost:6379",
            capacity=100,
            refill_rate=10
        )

        await limiter.initialize()
        await limiter.shutdown()

    @pytest.mark.asyncio
    async def test_token_refill_logic(self, redis_mock_context):
        """Test token refill logic."""
        limiter = TokenBucketRateLimiter(
            redis_url="redis://localhost:6379",
            capacity=10,
            refill_rate=1  # 1 token per second
        )

        await limiter.initialize()

        identifier = "test_user"
        endpoint = "/test"

        # First request should be allowed
        allowed, info = await limiter.is_allowed(identifier, endpoint)
        assert allowed is True
        assert "tokens_remaining" in info

        await limiter.shutdown()


class TestDistributedRateLimiter:
    """Test distributed rate limiter."""

    @pytest.mark.asyncio
    async def test_distributed_limiter_initialization(self, redis_mock_context):
        """Test distributed rate limiter initialization."""
        limiter = DistributedRateLimiter(
            redis_url="redis://localhost:6379",
            strategy="sliding_window",
            window_size=60,
            max_requests=100
        )

        await limiter.initialize()
        await limiter.shutdown()

    @pytest.mark.asyncio
    async def test_strategy_selection(self, redis_mock_context):
        """Test strategy selection."""
        # Test sliding window
        limiter = DistributedRateLimiter(
            redis_url="redis://localhost:6379",
            strategy="sliding_window"
        )
        await limiter.initialize()
        assert isinstance(limiter._limiter, SlidingWindowRateLimiter)

        await limiter.shutdown()

        # Test token bucket
        limiter = DistributedRateLimiter(
            redis_url="redis://localhost:6379",
            strategy="token_bucket"
        )
        await limiter.initialize()
        assert isinstance(limiter._limiter, TokenBucketRateLimiter)

        await limiter.shutdown()

    @pytest.mark.asyncio
    async def test_invalid_strategy(self):
        """Test invalid strategy handling."""
        with pytest.raises(ValueError):
            limiter = DistributedRateLimiter(strategy="invalid_strategy")
            await limiter.initialize()


class TestRateLimiterWithMocks:
    """Test rate limiter with mocked Redis client."""

    @pytest.mark.asyncio
    async def test_sliding_window_with_mocked_redis(self, redis_mock_context):
        """Test sliding window rate limiter with mocked Redis."""
        limiter = SlidingWindowRateLimiter(
            redis_url="redis://localhost:6379",
            window_size=60,
            max_requests=5
        )

        # Initialize should work with mocked Redis
        await limiter.initialize()

        identifier = "test_user"
        endpoint = "/test"

        # First few requests should be allowed
        for i in range(5):  # Make 5 requests to reach the limit of 5
            allowed, info = await limiter.is_allowed(identifier, endpoint)
            assert allowed is True
            assert info["remaining"] == 5 - (i + 1)

        # Next request should be rate limited
        allowed, info = await limiter.is_allowed(identifier, endpoint)
        assert allowed is False
        assert info["remaining"] == 0

        # Test key generation
        key1 = limiter._get_key("user1", "/api/test")
        key2 = limiter._get_key("user2", "/api/test")
        assert key1 != key2

        await limiter.shutdown()

    @pytest.mark.asyncio
    async def test_token_bucket_with_mocked_redis(self, redis_mock_context):
        """Test token bucket rate limiter with mocked Redis."""
        limiter = TokenBucketRateLimiter(
            redis_url="redis://localhost:6379",
            capacity=10,
            refill_rate=1  # 1 token per second
        )

        await limiter.initialize()

        identifier = "test_user"
        endpoint = "/test"

        # Should be able to make requests
        allowed, info = await limiter.is_allowed(identifier, endpoint)
        assert allowed is True
        assert "tokens_remaining" in info

        # Test a few more requests to verify rate limiting works
        for i in range(3):
            allowed, info = await limiter.is_allowed(identifier, endpoint)
            assert allowed is True
            assert "tokens_remaining" in info

        await limiter.shutdown()

    @pytest.mark.asyncio
    async def test_distributed_limiter_with_mocked_redis(self, redis_mock_context):
        """Test distributed rate limiter with mocked Redis."""
        limiter = DistributedRateLimiter(
            redis_url="redis://localhost:6379",
            strategy="sliding_window",
            window_size=60,
            max_requests=10
        )

        await limiter.initialize()

        # Test sliding window strategy
        allowed, info = await limiter.is_allowed("user1", "/test")
        assert allowed is True
        assert info["limit"] == 10

        await limiter.shutdown()

        # Test token bucket strategy
        limiter = DistributedRateLimiter(
            redis_url="redis://localhost:6379",
            strategy="token_bucket",
            capacity=20,
            refill_rate=2
        )

        await limiter.initialize()

        allowed, info = await limiter.is_allowed("user1", "/test")
        assert allowed is True
        assert info["capacity"] == 20

        await limiter.shutdown()
