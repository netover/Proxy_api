from slowapi import Limiter
from slowapi.util import get_remote_address
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

class RateLimiter:
    """Custom rate limiter using slowapi with unified config"""
    
    def __init__(self):
        self.limiter = Limiter(key_func=get_remote_address)
        self.limiter.storage = self.limiter.storage_class()
        self._default_limit = "100/minute"  # Default fallback
    
    def configure_limits(self, rpm: int):
        """Configure default limits from config"""
        self._default_limit = f"{rpm}/minute"
        logger.info(f"Rate limiter configured with {rpm} RPM")
    
    def limit(self, rate: str):
        """Create a rate limit decorator"""
        def decorator(func):
            return self.limiter.limit(rate or self._default_limit)(func)
        return decorator

# Global instance
rate_limiter = RateLimiter()