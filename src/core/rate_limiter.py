from slowapi import Limiter
from slowapi.util import get_remote_address
from src.core.unified_config import config_manager
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

class RateLimiter:
    """Custom rate limiter using slowapi with unified config"""
    
    def __init__(self):
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{config_manager.load_config().settings.rate_limit_rpm}/minute"]
        )
        self.limiter.storage = self.limiter.storage_class()
    
    def limit(self, rate: str):
        """Create a rate limit decorator"""
        def decorator(func):
            return self.limiter.limit(rate)(func)
        return decorator

# Global instance
rate_limiter = RateLimiter()