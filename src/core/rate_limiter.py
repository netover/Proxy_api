import asyncio
import time
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket"""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_tokens_remaining(self) -> float:
        """Get the number of tokens remaining"""
        self._refill()
        return self.tokens

    def get_reset_time(self) -> float:
        """Get time until bucket is full (for Retry-After header)"""
        if self.tokens >= self.capacity:
            return 0.0

        tokens_needed = self.capacity - self.tokens
        return tokens_needed / self.refill_rate


class TokenBucketRateLimiter:
    """Token bucket based rate limiter for FastAPI endpoints"""

    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.capacity = requests_per_minute  # Allow burst up to 1 minute worth
        self.refill_rate = requests_per_minute / 60.0  # Tokens per second
        self.buckets: Dict[str, TokenBucket] = {}
        self._cleanup_interval = 300  # Clean up old buckets every 5 minutes
        self._last_cleanup = time.time()

        logger.info(
            "Token bucket rate limiter initialized",
            capacity=self.capacity,
            refill_rate=self.refill_rate,
        )

    def is_allowed(self, key: str) -> tuple[bool, float]:
        """
        Check if request is allowed for the given key

        Returns:
            Tuple of (allowed: bool, reset_time: float)
        """
        # Periodic cleanup of old buckets
        self._cleanup_old_buckets()

        if key not in self.buckets:
            self.buckets[key] = TokenBucket(self.capacity, self.refill_rate)

        bucket = self.buckets[key]
        allowed = bucket.consume(1)

        if allowed:
            logger.debug(
                "Request allowed",
                key=key,
                tokens_remaining=bucket.get_tokens_remaining(),
            )
        else:
            reset_time = bucket.get_reset_time()
            logger.warning(
                "Rate limit exceeded", key=key, reset_in_seconds=reset_time
            )

        return allowed, bucket.get_reset_time()

    def _cleanup_old_buckets(self):
        """Clean up buckets that haven't been used recently"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        keys_to_remove = []
        for key, bucket in self.buckets.items():
            # Remove buckets that are full and haven't been used recently
            if bucket.get_tokens_remaining() >= bucket.capacity:
                # Check if it's been more than 10 minutes since last refill
                if now - bucket.last_refill > 600:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.buckets[key]

        if keys_to_remove:
            logger.debug("Cleaned up old buckets", count=len(keys_to_remove))

        self._last_cleanup = now

    def get_stats(self, key: str = None) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        if key and key in self.buckets:
            bucket = self.buckets[key]
            return {
                "tokens_remaining": bucket.get_tokens_remaining(),
                "capacity": bucket.capacity,
                "reset_in_seconds": bucket.get_reset_time(),
                "last_refill": bucket.last_refill,
            }

        return {
            "total_buckets": len(self.buckets),
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "requests_per_minute": self.requests_per_minute,
            "last_cleanup": self._last_cleanup,
        }

    # TODO: Redis integration - placeholder for future implementation
    # def _redis_get_bucket(self, key: str) -> TokenBucket:
    #     """Get bucket from Redis"""
    #     pass
    #
    # def _redis_store_bucket(self, key: str, bucket: TokenBucket):
    #     """Store bucket in Redis"""
    #     pass
    #
    # async def redis_cleanup_expired_buckets(self):
    #     """Clean up expired buckets from Redis"""
    #     pass


class RateLimiter:
    """Enhanced rate limiter with global, per-provider, and fallback strategies"""

    def __init__(self):
        self.limiter = Limiter(key_func=get_remote_address)
        self._default_limit = "100/minute"
        self._global_limits: Dict[str, str] = {}
        self._provider_limits: Dict[str, str] = {}
        self._route_limits: Dict[str, str] = {}
        self._fallback_strategies: Dict[str, Any] = {}
        self._last_config_update = 0

        # Token bucket rate limiter for sensitive endpoints
        self.token_bucket_limiter = None

    def configure_from_settings(self, settings: "RateLimitSettings"):
        """Configure the rate limiter from a RateLimitSettings object."""
        try:
            self._default_limit = (
                f"{settings.requests_per_window}/{settings.window_seconds}s"
            )
            self._global_limits["default"] = self._default_limit
            self._route_limits = settings.routes

            # Initialize token bucket limiter with config values
            # Convert requests per window to requests per minute for the token bucket
            rpm = int(
                settings.requests_per_window * (60 / settings.window_seconds)
            )
            self.token_bucket_limiter = TokenBucketRateLimiter(
                requests_per_minute=rpm
            )

            self._last_config_update = time.time()
            logger.info(
                "Rate limiter configured successfully",
                default_limit=self._default_limit,
                route_limits=self._route_limits,
            )
        except Exception as e:
            logger.error(f"Failed to configure rate limiter from settings: {e}")

    def get_provider_limit(self, provider_name: str) -> str:
        """Get rate limit for specific provider"""
        return self._provider_limits.get(provider_name, self._default_limit)

    def get_route_limit(self, route_path: str) -> str:
        """Get rate limit for specific route"""
        return self._route_limits.get(route_path, self._default_limit)

    def limit(
        self,
        rate: Optional[str] = None,
        provider: Optional[str] = None,
        route: Optional[str] = None,
    ):
        """Create a rate limit decorator with provider-specific or route-specific limits"""
        if route:
            limit_rate = self.get_route_limit(route)
        elif provider:
            limit_rate = self.get_provider_limit(provider)
        else:
            limit_rate = rate or self._default_limit

        def decorator(func: Callable) -> Callable:
            # Apply the rate limit
            limited_func = self.limiter.limit(limit_rate)(func)

            # Add fallback strategy wrapper
            async def wrapper(*args, **kwargs):
                try:
                    return await limited_func(*args, **kwargs)
                except RateLimitExceeded:
                    return await self._handle_rate_limit_exceeded(
                        func, provider, *args, **kwargs
                    )

            # For sync functions
            def sync_wrapper(*args, **kwargs):
                try:
                    return limited_func(*args, **kwargs)
                except RateLimitExceeded:
                    return self._handle_rate_limit_exceeded_sync(
                        func, provider, *args, **kwargs
                    )

            return (
                wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
            )

        return decorator

    async def _handle_rate_limit_exceeded(
        self, func: Callable, provider: str, *args, **kwargs
    ):
        """Handle rate limit exceeded with fallback strategies"""
        logger.warning(
            "Rate limit exceeded", provider=provider, function=func.__name__
        )

        # Apply fallback strategies
        if "secondary_provider" in self._fallback_strategies:
            logger.info(
                "Applying secondary provider fallback", provider=provider
            )
            # This would need to be implemented based on your provider switching logic

        if "delay" in self._fallback_strategies:
            delay = self._fallback_strategies["delay"]
            logger.info(
                f"Applying delay fallback: {delay}s", provider=provider
            )
            await asyncio.sleep(delay)
            return await func(*args, **kwargs)

        # Default: return rate limit error
        raise RateLimitExceeded("Rate limit exceeded")

    def _handle_rate_limit_exceeded_sync(
        self, func: Callable, provider: str, *args, **kwargs
    ):
        """Handle rate limit exceeded for sync functions"""
        logger.warning(
            "Rate limit exceeded (sync)",
            provider=provider,
            function=func.__name__,
        )

        # For sync functions, just re-raise the exception
        # In a real implementation, you might want to implement sync fallback strategies
        raise RateLimitExceeded("Rate limit exceeded")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        stats = {
            "default_limit": self._default_limit,
            "global_limits": self._global_limits,
            "provider_limits": self._provider_limits,
            "route_limits": self._route_limits,
            "fallback_strategies": list(self._fallback_strategies.keys()),
            "last_config_update": self._last_config_update,
        }

        if self.token_bucket_limiter:
            stats["token_bucket"] = self.token_bucket_limiter.get_stats()

        return stats


# FastAPI dependency for token bucket rate limiting
async def token_bucket_rate_limit(request: Request) -> None:
    """
    FastAPI dependency for token bucket rate limiting.
    Raises HTTP 429 exception when rate limit is exceeded.
    """
    if (
        not hasattr(rate_limiter, "token_bucket_limiter")
        or rate_limiter.token_bucket_limiter is None
    ):
        # If token bucket limiter is not initialized, allow the request
        return

    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    allowed, reset_time = rate_limiter.token_bucket_limiter.is_allowed(
        client_ip
    )

    if not allowed:
        # Return HTTP 429 with Retry-After header
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too Many Requests",
                "message": "Rate limit exceeded. Please try again later.",
                "retry_after": int(reset_time),
            },
            headers={"Retry-After": str(int(reset_time))},
        )


# Global instance
rate_limiter = RateLimiter()
