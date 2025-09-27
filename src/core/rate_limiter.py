"""
Main rate limiter interface that delegates to the distributed implementation.
"""

import logging
from typing import Dict, Optional, Tuple, Any

from src.core.rate_limiter_redis import get_distributed_limiter
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class DistributedRateLimiter:
    """
    Main rate limiter interface that uses Redis-backed distributed rate limiting.
    """

    def __init__(self):
        self._limiter = None
        self._initialized = False

    async def initialize(self, config):
        """Initialize the distributed rate limiter with configuration."""
        if self._initialized:
            return

        try:
            redis_url = getattr(config, 'redis_url', 'redis://localhost:6379')
            strategy = getattr(config, 'strategy', 'sliding_window')
            window_size = getattr(config, 'window_seconds', 60)
            max_requests = getattr(config, 'requests_per_window', 100)

            self._limiter = get_distributed_limiter(
                strategy=strategy,
                redis_url=redis_url,
                window_size=window_size,
                max_requests=max_requests
            )

            await self._limiter.initialize()
            self._initialized = True
            logger.info(f"Distributed rate limiter initialized with {strategy} strategy")

        except Exception as e:
            logger.error(f"Failed to initialize distributed rate limiter: {e}")
            # Fall back to dummy behavior
            self._limiter = None

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
    ) -> Tuple[bool, Dict[str, Any]]:
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
            # If not initialized, allow all requests
            return True, {
                "allowed": True,
                "remaining": 999999,
                "reset_time": 0,
                "limit": 999999
            }

        return await self._limiter.is_allowed(
            identifier=identifier,
            endpoint=endpoint,
            user_id=user_id,
            api_key=api_key
        )

    def get_stats(self, identifier: str = None, endpoint: str = None) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "status": "Distributed rate limiter active",
            "strategy": "sliding_window",
            "redis_configured": self._limiter is not None,
            "initialized": self._initialized
        }


class DummyRateLimiter:
    """
    Fallback dummy rate limiter for when distributed rate limiting is not available.
    """

    def __init__(self):
        logger.warning("Using dummy rate_limiter object. This should not be called for actual rate limiting.")

    def get_stats(self, *args, **kwargs):
        """Placeholder for get_stats."""
        return {"status": "Rate limiting is handled by middleware."}

    def is_allowed(self, *args, **kwargs):
        """Placeholder for is_allowed."""
        return True


# Global instance to be imported
rate_limiter = DistributedRateLimiter()
