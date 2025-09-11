from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.core.logging import ContextualLogger
from typing import Dict, Any, Optional, Callable
import time
import asyncio

logger = ContextualLogger(__name__)

class RateLimiter:
    """Enhanced rate limiter with global, per-provider, and fallback strategies"""

    def __init__(self):
        self.limiter = Limiter(key_func=get_remote_address)
        self._default_limit = "100/minute"
        self._global_limits: Dict[str, str] = {}
        self._provider_limits: Dict[str, str] = {}
        self._fallback_strategies: Dict[str, Any] = {}
        self._last_config_update = 0

    def configure_from_config(self, config: Any):
        """Configure rate limiter from unified config"""
        try:
            settings = config.settings if hasattr(config, 'settings') else config

            # Global rate limits
            if hasattr(settings, 'rate_limit_rpm'):
                self._default_limit = f"{settings.rate_limit_rpm}/minute"
                self._global_limits['default'] = self._default_limit

            # Provider-specific limits
            if hasattr(config, 'providers'):
                for provider in config.providers:
                    if hasattr(provider, 'rate_limit') and provider.rate_limit:
                        self._provider_limits[provider.name] = f"{provider.rate_limit}/hour"

            # Fallback strategies
            if hasattr(settings, 'fallback_strategies'):
                self._fallback_strategies = settings.fallback_strategies

            self._last_config_update = time.time()
            logger.info("Rate limiter configured", global_limits=self._global_limits, provider_limits=self._provider_limits)

        except Exception as e:
            logger.error(f"Failed to configure rate limiter: {e}")

    def get_provider_limit(self, provider_name: str) -> str:
        """Get rate limit for specific provider"""
        return self._provider_limits.get(provider_name, self._default_limit)

    def limit(self, rate: Optional[str] = None, provider: Optional[str] = None):
        """Create a rate limit decorator with provider-specific limits"""
        if provider:
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
                    return await self._handle_rate_limit_exceeded(func, provider, *args, **kwargs)

            # For sync functions
            def sync_wrapper(*args, **kwargs):
                try:
                    return limited_func(*args, **kwargs)
                except RateLimitExceeded:
                    return self._handle_rate_limit_exceeded_sync(func, provider, *args, **kwargs)

            return wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    async def _handle_rate_limit_exceeded(self, func: Callable, provider: str, *args, **kwargs):
        """Handle rate limit exceeded with fallback strategies"""
        logger.warning("Rate limit exceeded", provider=provider, function=func.__name__)

        # Apply fallback strategies
        if "secondary_provider" in self._fallback_strategies:
            logger.info("Applying secondary provider fallback", provider=provider)
            # This would need to be implemented based on your provider switching logic
            pass

        if "delay" in self._fallback_strategies:
            delay = self._fallback_strategies["delay"]
            logger.info(f"Applying delay fallback: {delay}s", provider=provider)
            await asyncio.sleep(delay)
            return await func(*args, **kwargs)

        # Default: return rate limit error
        raise RateLimitExceeded("Rate limit exceeded")

    def _handle_rate_limit_exceeded_sync(self, func: Callable, provider: str, *args, **kwargs):
        """Handle rate limit exceeded for sync functions"""
        logger.warning("Rate limit exceeded (sync)", provider=provider, function=func.__name__)

        # For sync functions, just re-raise the exception
        # In a real implementation, you might want to implement sync fallback strategies
        raise RateLimitExceeded("Rate limit exceeded")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            'default_limit': self._default_limit,
            'global_limits': self._global_limits,
            'provider_limits': self._provider_limits,
            'fallback_strategies': list(self._fallback_strategies.keys()),
            'last_config_update': self._last_config_update
        }

# Global instance
rate_limiter = RateLimiter()