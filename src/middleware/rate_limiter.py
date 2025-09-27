import logging
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from typing import Callable, Awaitable
from starlette.responses import Response
from limits import parse as parse_limit

from src.core.rate_limiter_redis import get_distributed_limiter
from src.core.logging import ContextualLogger

# Set up a logger for this middleware
logger = ContextualLogger(__name__)

class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # We will initialize the distributed limiter later, after the config is loaded
        self.distributed_limiter = None
        self.limiter_mapping = {}
        self.default_limit = None
        self.redis_configured = False

    def reset(self):
        """Resets the limiter state. Used for testing purposes."""
        self.distributed_limiter = None
        self.redis_configured = False

    def _initialize_distributed_limiter(self, request: Request):
        """
        Initializes the distributed rate limiter from the application config.
        This is done on the first request to ensure app_state is initialized.
        """
        if self.distributed_limiter is None:
            try:
                # Load rate limits from the application state config
                if hasattr(request.app.state, 'config') and request.app.state.config:
                    rate_limit_config = request.app.state.config.rate_limit
                    if rate_limit_config:
                        self.limiter_mapping = rate_limit_config.routes or {}
                        self.default_limit = getattr(rate_limit_config, 'default', None)

                        # Get Redis URL from config if available
                        redis_url = getattr(rate_limit_config, 'redis_url', 'redis://localhost:6379')

                        # Initialize distributed rate limiter
                        self.distributed_limiter = get_distributed_limiter(
                            strategy="sliding_window",
                            redis_url=redis_url,
                            window_size=getattr(rate_limit_config, 'window_seconds', 60),
                            max_requests=getattr(rate_limit_config, 'requests_per_window', 100)
                        )

                        self.redis_configured = True
                        logger.info(f"Distributed rate limiter initialized with Redis: {redis_url}")

            except Exception as e:
                logger.error(f"Failed to initialize distributed rate limiter: {e}")
                # Fall back to in-memory limiter
                self.distributed_limiter = None
                self.redis_configured = False

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        # Initialize distributed limiter if needed
        if self.distributed_limiter is None:
            self._initialize_distributed_limiter(request)

        current_path = request.url.path
        limit_str = self.limiter_mapping.get(current_path, self.default_limit)

        # If no rate limit configured for this path, continue
        if not limit_str:
            return await call_next(request)

        # If distributed limiter is not available, fall back to in-memory
        if not self.redis_configured or self.distributed_limiter is None:
            return await call_next(request)

        # Get identifier (IP address by default)
        identifier = get_remote_address(request)

        # Check rate limit
        allowed, info = await self.distributed_limiter.is_allowed(
            identifier=identifier,
            endpoint=current_path
        )

        if not allowed:
            retry_after = max(0, info.get("reset_time", 0) - int(time.time()))

            headers = {
                "X-RateLimit-Limit": str(info.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(info.get("reset_time", 0)),
                "Retry-After": str(retry_after),
            }

            logger.warning(
                f"Distributed rate limit exceeded for {identifier} on path {current_path}. "
                f"Blocking request. Reset in {retry_after}s"
            )
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded for {limit_str}",
                    "error": "Too Many Requests",
                    "retry_after": retry_after,
                    "limit": info.get("limit", 0),
                    "reset_time": info.get("reset_time", 0)
                },
                headers=headers,
            )

        # Execute the request
        response = await call_next(request)

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(info.get("limit", 0)),
            "X-RateLimit-Remaining": str(info.get("remaining", 0)),
            "X-RateLimit-Reset": str(info.get("reset_time", 0)),
        }
        response.headers.update(headers)
        return response