"""
Redis-backed Distributed Rate Limiter

This module provides a distributed rate limiter that works across multiple instances
using Redis as the backend storage.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, Optional, Tuple, Union
import redis.asyncio as redis

from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class SlidingWindowRateLimiter:
    """
    Redis-backed sliding window rate limiter.

    This implementation uses Redis sorted sets to maintain a sliding window
    of request timestamps, allowing for precise rate limiting across multiple instances.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        window_size: int = 60,  # seconds
        max_requests: int = 100,
        cleanup_interval: int = 300,  # 5 minutes
    ):
        self.redis_url = redis_url
        self.window_size = window_size
        self.max_requests = max_requests
        self.cleanup_interval = cleanup_interval
        self.redis_client: Optional[redis.Redis] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize Redis connection and start cleanup task."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info(f"Redis rate limiter initialized: {self.redis_url}")

            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Rate limiter cleanup task started")

        except Exception as e:
            logger.error(f"Failed to initialize Redis rate limiter: {e}")
            raise

    async def shutdown(self):
        """Shutdown the rate limiter and cleanup resources."""
        self._shutdown_event.set()

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis rate limiter shutdown complete")

    async def _cleanup_loop(self):
        """Background task to clean up expired entries."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")

    async def _cleanup_expired_entries(self):
        """Remove expired entries from Redis."""
        if not self.redis_client:
            return

        try:
            # Get all keys matching our pattern
            pattern = "rate_limit:*"
            keys = await self.redis_client.keys(pattern)

            for key in keys:
                # Remove entries older than window_size + buffer
                cutoff_time = time.time() - (self.window_size + 60)
                await self.redis_client.zremrangebyscore(key, 0, cutoff_time)

                # If the set is empty, delete the key
                count = await self.redis_client.zcard(key)
                if count == 0:
                    await self.redis_client.delete(key)

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate a unique key for the identifier and endpoint."""
        # Use hash to avoid very long keys
        key_data = f"{identifier}:{endpoint}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"rate_limit:{key_hash}"

    async def is_allowed(self, identifier: str, endpoint: str = "") -> Tuple[bool, Dict]:
        """
        Check if the request is allowed under the rate limit.

        Args:
            identifier: Unique identifier (IP, user ID, API key, etc.)
            endpoint: Specific endpoint path (optional)

        Returns:
            Tuple of (allowed: bool, info: dict)
            info contains: remaining, reset_time, limit
        """
        if not self.redis_client:
            await self.initialize()

        current_time = time.time()
        window_start = current_time - self.window_size
        key = self._get_key(identifier, endpoint)

        try:
            # Add current request timestamp
            await self.redis_client.zadd(key, {str(current_time): current_time})

            # Count requests in the current window
            count = await self.redis_client.zcount(key, window_start, current_time)

            # Check if within limit
            allowed = count <= self.max_requests

            # Calculate remaining time until window resets
            reset_time = current_time + self.window_size
            remaining = max(0, self.max_requests - count)

            info = {
                "allowed": allowed,
                "remaining": remaining,
                "reset_time": int(reset_time),
                "limit": self.max_requests,
                "current_count": count,
                "window_size": self.window_size
            }

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {endpoint}: "
                    f"{count}/{self.max_requests} requests in {self.window_size}s window"
                )

            return allowed, info

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open in case of Redis issues
            return True, {
                "allowed": True,
                "remaining": self.max_requests,
                "reset_time": int(current_time + self.window_size),
                "limit": self.max_requests,
                "error": "Redis unavailable"
            }


class TokenBucketRateLimiter:
    """
    Redis-backed token bucket rate limiter.

    This implementation uses Redis to maintain token buckets across multiple instances.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        capacity: int = 100,  # Maximum tokens
        refill_rate: float = 10,  # Tokens per second
    ):
        self.redis_url = redis_url
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info(f"Redis token bucket rate limiter initialized: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis token bucket rate limiter: {e}")
            raise

    async def shutdown(self):
        """Shutdown the rate limiter."""
        if self.redis_client:
            await self.redis_client.close()

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate a unique key for the identifier and endpoint."""
        key_data = f"{identifier}:{endpoint}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"token_bucket:{key_hash}"

    async def is_allowed(self, identifier: str, endpoint: str = "") -> Tuple[bool, Dict]:
        """
        Check if the request is allowed under the token bucket rate limit.

        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        if not self.redis_client:
            await self.initialize()

        current_time = time.time()
        key = self._get_key(identifier, endpoint)

        try:
            # Get current bucket state
            bucket_data = await self.redis_client.get(key)

            if bucket_data:
                bucket = json.loads(bucket_data)
                tokens = bucket["tokens"]
                last_refill = bucket["last_refill"]
            else:
                # Initialize new bucket
                tokens = self.capacity
                last_refill = current_time
                bucket = {"tokens": tokens, "last_refill": last_refill}

            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            tokens = min(self.capacity, tokens + tokens_to_add)

            # Check if we have tokens
            if tokens >= 1:
                tokens -= 1
                allowed = True
            else:
                allowed = False

            # Update bucket
            bucket["tokens"] = tokens
            bucket["last_refill"] = current_time
            await self.redis_client.set(key, json.dumps(bucket), ex=3600)  # 1 hour expiry

            # Calculate next refill time
            next_refill = current_time + (1 - tokens) / self.refill_rate if tokens < self.capacity else current_time

            info = {
                "allowed": allowed,
                "tokens_remaining": tokens,
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "next_refill": int(next_refill)
            }

            if not allowed:
                logger.warning(
                    f"Token bucket rate limit exceeded for {identifier} on {endpoint}: "
                    f"{tokens:.1f} tokens remaining"
                )

            return allowed, info

        except Exception as e:
            logger.error(f"Token bucket rate limit check failed: {e}")
            # Fail open in case of Redis issues
            return True, {
                "allowed": True,
                "tokens_remaining": self.capacity,
                "capacity": self.capacity,
                "error": "Redis unavailable"
            }


class DistributedRateLimiter:
    """
    Main distributed rate limiter that supports multiple strategies.

    This class provides a unified interface for different rate limiting strategies
    while maintaining distributed state using Redis.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        strategy: str = "sliding_window",
        **strategy_kwargs
    ):
        self.redis_url = redis_url
        self.strategy = strategy.lower()
        self.strategy_kwargs = strategy_kwargs
        self._limiter = None

    async def initialize(self):
        """Initialize the appropriate rate limiter strategy."""
        if self.strategy == "sliding_window":
            self._limiter = SlidingWindowRateLimiter(
                redis_url=self.redis_url,
                **self.strategy_kwargs
            )
        elif self.strategy == "token_bucket":
            self._limiter = TokenBucketRateLimiter(
                redis_url=self.redis_url,
                **self.strategy_kwargs
            )
        else:
            raise ValueError(f"Unknown rate limiting strategy: {self.strategy}")

        await self._limiter.initialize()
        logger.info(f"Distributed rate limiter initialized with {self.strategy} strategy")

    async def shutdown(self):
        """Shutdown the rate limiter."""
        if self._limiter:
            await self._limiter.shutdown()

    async def is_allowed(
        self,
        identifier: str,
        endpoint: str = "",
        user_id: str = None,
        api_key: str = None
    ) -> Tuple[bool, Dict]:
        """
        Check if the request is allowed under the rate limit.

        Args:
            identifier: Primary identifier (IP address)
            endpoint: Endpoint path
            user_id: User ID (optional)
            api_key: API key (optional)

        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        if not self._limiter:
            await self.initialize()

        # Create composite identifier based on available information
        composite_id = identifier
        if user_id:
            composite_id = f"{user_id}:{identifier}"
        if api_key:
            composite_id = f"{api_key}:{identifier}"

        return await self._limiter.is_allowed(composite_id, endpoint)


# Global instances
sliding_window_limiter = None
token_bucket_limiter = None
distributed_limiter = None


def get_sliding_window_limiter(**kwargs) -> SlidingWindowRateLimiter:
    """Get or create a sliding window rate limiter instance."""
    global sliding_window_limiter
    if sliding_window_limiter is None:
        sliding_window_limiter = SlidingWindowRateLimiter(**kwargs)
    return sliding_window_limiter


def get_token_bucket_limiter(**kwargs) -> TokenBucketRateLimiter:
    """Get or create a token bucket rate limiter instance."""
    global token_bucket_limiter
    if token_bucket_limiter is None:
        token_bucket_limiter = TokenBucketRateLimiter(**kwargs)
    return token_bucket_limiter


def get_distributed_limiter(strategy: str = "sliding_window", **kwargs) -> DistributedRateLimiter:
    """Get or create a distributed rate limiter instance."""
    global distributed_limiter
    if distributed_limiter is None:
        distributed_limiter = DistributedRateLimiter(strategy=strategy, **kwargs)
    return distributed_limiter
