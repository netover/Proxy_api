"""
Middleware pipeline for request/response processing.

This module provides middleware components for request preprocessing,
response postprocessing, logging, security, and performance monitoring.
"""

import json
import re
import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.core.logging import ContextualLogger

from .request_validator import request_validator
from .response_validator import response_validator

logger = ContextualLogger(__name__)


class MiddlewarePipeline:
    """Centralized middleware pipeline for request/response processing."""

    def __init__(self):
        self.middlewares = []
        self.request_count = 0
        self.error_count = 0

    def add_middleware(self, middleware: Callable) -> None:
        """Add a middleware to the pipeline."""
        self.middlewares.append(middleware)

    async def process_request(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process incoming request through middleware pipeline."""
        start_time = time.time()
        self.request_count += 1

        # Generate request ID
        request_id = f"req_{int(time.time() * 1000)}_{self.request_count}"
        request.state.request_id = request_id

        try:
            # Log request
            await self._log_request(request, request_id)

            # Apply request middlewares
            for middleware in self.middlewares:
                if hasattr(middleware, "process_request"):
                    request = await middleware.process_request(request)

            # Call the actual endpoint
            response = await call_next(request)

            # Apply response middlewares
            for middleware in reversed(self.middlewares):
                if hasattr(middleware, "process_response"):
                    response = await middleware.process_response(
                        request, response
                    )

            # Log response
            await self._log_response(request, response, start_time, request_id)

            return response

        except Exception as e:
            self.error_count += 1
            logger.error(
                f"Request processing error: {e}", request_id=request_id
            )

            # Create error response
            error_response = await self._create_error_response(e, request_id)
            await self._log_response(
                request, error_response, start_time, request_id
            )

            return error_response

    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details."""
        try:
            # Extract basic request info
            request_info = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }

            # Don't log sensitive headers
            sensitive_headers = ["authorization", "x-api-key", "cookie"]
            for header in sensitive_headers:
                if header in request_info["headers"]:
                    request_info["headers"][header] = "[REDACTED]"

            logger.info(
                "Incoming request", request_id=request_id, **request_info
            )

        except Exception as e:
            logger.error(f"Failed to log request: {e}", request_id=request_id)

    async def _log_response(
        self,
        request: Request,
        response: Response,
        start_time: float,
        request_id: str,
    ) -> None:
        """Log outgoing response details."""
        try:
            duration = time.time() - start_time

            response_info = {
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "content_type": response.headers.get(
                    "content-type", "unknown"
                ),
                "content_length": response.headers.get(
                    "content-length", "unknown"
                ),
            }

            if response.status_code >= 400:
                logger.warning(
                    "Error response", request_id=request_id, **response_info
                )
            else:
                logger.info(
                    "Response sent", request_id=request_id, **response_info
                )

        except Exception as e:
            logger.error(f"Failed to log response: {e}", request_id=request_id)

    async def _create_error_response(
        self, exception: Exception, request_id: str
    ) -> JSONResponse:
        """Create standardized error response."""
        from src.core.exceptions import (
            InvalidRequestError,
            ServiceUnavailableError,
        )

        if isinstance(exception, InvalidRequestError):
            status_code = 400
            error_type = "invalid_request"
        elif isinstance(exception, ServiceUnavailableError):
            status_code = 503
            error_type = "service_unavailable"
        else:
            status_code = 500
            error_type = "internal_server_error"

        error_response = {
            "error": {
                "message": str(exception),
                "type": error_type,
                "request_id": request_id,
                "timestamp": int(time.time()),
            }
        }

        return JSONResponse(status_code=status_code, content=error_response)


class ValidationMiddleware:
    """Middleware for request/response validation."""

    async def process_request(self, request: Request) -> Request:
        """Validate incoming request."""
        # Skip validation for certain endpoints
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
        if any(path in str(request.url.path) for path in skip_paths):
            return request

        # Parse request body for validation
        try:
            body = await request.json()
            request.state.validated_body = body

            # Basic validation
            if str(request.url.path).startswith("/v1/chat/completions"):
                validated_body = (
                    await request_validator.validate_chat_completion_request(
                        body
                    )
                )
                request.state.validated_body = validated_body
            elif str(request.url.path).startswith("/v1/completions"):
                validated_body = (
                    await request_validator.validate_text_completion_request(
                        body
                    )
                )
                request.state.validated_body = validated_body
            elif str(request.url.path).startswith("/v1/embeddings"):
                validated_body = (
                    await request_validator.validate_embedding_request(body)
                )
                request.state.validated_body = validated_body

        except Exception as e:
            logger.warning(f"Request validation failed: {e}")
            # Continue with original body if validation fails

        return request

    async def process_response(
        self, request: Request, response: Response
    ) -> Response:
        """Validate outgoing response."""
        if response.status_code >= 400:
            return response  # Don't validate error responses

        try:
            # Only validate JSON responses
            if (
                hasattr(response, "body")
                and response.media_type == "application/json"
            ):
                # Parse response body
                response_data = json.loads(response.body.decode("utf-8"))

                # Apply appropriate validation
                if str(request.url.path).startswith("/v1/chat/completions"):
                    validated_data = await response_validator.validate_chat_completion_response(
                        response_data
                    )
                elif str(request.url.path).startswith("/v1/completions"):
                    validated_data = await response_validator.validate_text_completion_response(
                        response_data
                    )
                elif str(request.url.path).startswith("/v1/embeddings"):
                    validated_data = (
                        await response_validator.validate_embedding_response(
                            response_data
                        )
                    )
                elif str(request.url.path).startswith(
                    "/v1/images/generations"
                ):
                    validated_data = await response_validator.validate_image_generation_response(
                        response_data
                    )
                else:
                    validated_data = (
                        await response_validator.validate_generic_response(
                            response_data
                        )
                    )

                # Create new response with validated data
                response = JSONResponse(
                    status_code=response.status_code,
                    content=validated_data,
                    headers=dict(response.headers),
                )

        except Exception as e:
            logger.warning(f"Response validation failed: {e}")
            # Continue with original response if validation fails

        return response


class SecurityMiddleware:
    """Middleware for security checks."""

    def __init__(self):
        self.suspicious_patterns = [
            r"\.\./",  # Directory traversal
            r"<script",  # XSS attempts
            r"union.*select",  # SQL injection
        ]
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_window = 100

    async def process_request(self, request: Request) -> Request:
        """Perform security checks on incoming request."""
        # Check for suspicious patterns in URL
        url_path = str(request.url.path)
        for pattern in self.suspicious_patterns:
            if re.search(pattern, url_path, re.IGNORECASE):
                logger.warning(
                    f"Suspicious pattern detected in URL: {pattern}"
                )
                # Could add additional security measures here

        # Basic rate limiting check (simplified)
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        if not hasattr(request.app.state, "rate_limit_cache"):
            request.app.state.rate_limit_cache = {}

        cache = request.app.state.rate_limit_cache

        if client_ip not in cache:
            cache[client_ip] = []

        # Clean old entries
        cache[client_ip] = [
            timestamp
            for timestamp in cache[client_ip]
            if current_time - timestamp < self.rate_limit_window
        ]

        if len(cache[client_ip]) >= self.max_requests_per_window:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            # Could return 429 response here

        cache[client_ip].append(current_time)

        return request


# Global middleware instances
validation_middleware = ValidationMiddleware()
security_middleware = SecurityMiddleware()
middleware_pipeline = MiddlewarePipeline()

# Add middlewares to pipeline
middleware_pipeline.add_middleware(validation_middleware)
middleware_pipeline.add_middleware(security_middleware)
