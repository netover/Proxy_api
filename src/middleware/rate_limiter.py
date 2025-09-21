import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from typing import Callable, Awaitable
from starlette.responses import Response
from limits import parse as parse_limit

import logging

# Set up a logger for this middleware
logger = logging.getLogger(__name__)

class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # We will initialize the limiter later, after the config is loaded
        self.limiter: Limiter = None
        self.limiter_mapping = {}
        self.default_limit = None

    def reset(self):
        """Resets the limiter state. Used for testing purposes."""
        self.limiter = None

    def _initialize_limiter(self, request: Request):
        """
        Initializes the limiter and route mappings from the application config.
        This is done on the first request to ensure app_state is initialized.
        """
        if self.limiter is None:
            self.limiter = Limiter(key_func=get_remote_address)
            # Load rate limits from the application state config
            if hasattr(request.app.state, 'config') and request.app.state.config and hasattr(request.app.state.config, 'rate_limit'):
                rate_limit_config = request.app.state.config.rate_limit
                if rate_limit_config:
                    self.limiter_mapping = rate_limit_config.routes or {}
                    self.default_limit = getattr(rate_limit_config, 'default', None)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        if self.limiter is None:
            self._initialize_limiter(request)

        current_path = request.url.path
        limit_str = self.limiter_mapping.get(current_path, self.default_limit)

        if limit_str and self.limiter:
            limit_item = parse_limit(limit_str)
            identifier = self.limiter._key_func(request)

            if not self.limiter.limiter.hit(limit_item, identifier):
                logger.warning(f"Rate limit exceeded for {identifier} on path {current_path}. Blocking request.")
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded for {limit_str}",
                        "error": "Too Many Requests",
                    },
                )

        response = await call_next(request)
        return response
