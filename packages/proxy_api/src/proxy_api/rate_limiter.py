"""Rate limiting for proxy_api package."""

from proxy_core import RateLimiter

# Global instance
rate_limiter = RateLimiter()
