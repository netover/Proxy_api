import logging

logger = logging.getLogger(__name__)

class DummyRateLimiter:
    """
    A placeholder for a rate limiter object to satisfy a broken import
    in the config_controller. The actual rate limiting is handled by
    the RateLimitingMiddleware.
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
rate_limiter = DummyRateLimiter()
