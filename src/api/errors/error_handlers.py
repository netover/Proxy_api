"""
Centralized error handling framework for API endpoints.

This module provides standardized error handling, logging, and response
formatting for all API errors.
"""

import traceback
import time
from typing import Any, Dict

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
)
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class ErrorHandler:
    """Centralized error handler for API responses."""

    def __init__(self):
        self.error_counts = {}
        self.max_error_details_length = 500

    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle any exception and return standardized JSON response."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Log the error
        await self._log_error(request, exc, request_id)

        # Increment error count
        error_type = type(exc).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Create standardized error response
        error_response = self._create_error_response(exc, request_id)

        # Determine HTTP status code
        status_code = self._get_status_code(exc)

        return JSONResponse(status_code=status_code, content=error_response)

    async def _log_error(
        self, request: Request, exc: Exception, request_id: str
    ) -> None:
        """Log error details with context."""
        try:
            error_details = {
                "request_id": request_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "url": str(request.url),
                "method": request.method,
                "client_ip": (request.client.host if request.client else "unknown"),
                "user_agent": request.headers.get("user-agent", "unknown"),
            }

            # Add traceback for server errors
            if isinstance(exc, (ValueError, TypeError, KeyError, AttributeError)):
                error_details["traceback"] = traceback.format_exc()

            # Log at appropriate level
            if isinstance(exc, (HTTPException, InvalidRequestError)):
                logger.warning("Client error", **error_details)
            else:
                logger.error("Server error", **error_details)

        except Exception as log_exc:
            logger.error(f"Failed to log error: {log_exc}")

    def _create_error_response(self, exc: Exception, request_id: str) -> Dict[str, Any]:
        """Create standardized error response structure."""
        base_response = {
            "error": {
                "request_id": request_id,
                "timestamp": int(time.time()),
                "type": self._get_error_type(exc),
                "message": self._sanitize_error_message(str(exc)),
            }
        }

        # Add additional context for specific error types
        if isinstance(exc, InvalidRequestError):
            base_response["error"]["param"] = getattr(exc, "param", None)
            base_response["error"]["code"] = getattr(
                exc, "code", "invalid_request_error"
            )

        elif isinstance(exc, NotFoundError):
            base_response["error"]["code"] = "resource_not_found"

        elif isinstance(exc, ServiceUnavailableError):
            base_response["error"]["code"] = "service_unavailable"
            base_response["error"]["retry_after"] = 30  # seconds

        elif isinstance(exc, AuthenticationError):
            base_response["error"]["code"] = "authentication_failed"

        elif isinstance(exc, AuthorizationError):
            base_response["error"]["code"] = "authorization_failed"

        elif isinstance(exc, RateLimitError):
            base_response["error"]["code"] = "rate_limit_exceeded"
            base_response["error"]["retry_after"] = getattr(exc, "retry_after", 60)

        return base_response

    def _get_error_type(self, exc: Exception) -> str:
        """Map exception type to standardized error type."""
        error_type_mapping = {
            InvalidRequestError: "invalid_request",
            NotFoundError: "not_found",
            ServiceUnavailableError: "service_unavailable",
            AuthenticationError: "authentication_error",
            AuthorizationError: "authorization_error",
            RateLimitError: "rate_limit_error",
            RequestValidationError: "validation_error",
            HTTPException: "http_error",
            ValueError: "value_error",
            TypeError: "type_error",
            KeyError: "key_error",
            AttributeError: "attribute_error",
        }

        return error_type_mapping.get(type(exc), "internal_server_error")

    def _get_status_code(self, exc: Exception) -> int:
        """Map exception type to HTTP status code."""
        status_code_mapping = {
            InvalidRequestError: 400,
            NotFoundError: 404,
            ServiceUnavailableError: 503,
            AuthenticationError: 401,
            AuthorizationError: 403,
            RateLimitError: 429,
            RequestValidationError: 422,
            HTTPException: getattr(exc, "status_code", 500),
            ValueError: 400,
            TypeError: 400,
            KeyError: 400,
            AttributeError: 500,
        }

        return status_code_mapping.get(type(exc), 500)

    def _sanitize_error_message(self, message: str) -> str:
        """Sanitize error message to prevent information leakage."""
        if not message:
            return "An error occurred"

        # Truncate very long messages
        if len(message) > self.max_error_details_length:
            message = message[: self.max_error_details_length] + "..."

        # Remove sensitive information
        sensitive_patterns = [
            r"api[_-]?key[=:]\s*[^\s]+",
            r"password[=:]\s*[^\s]+",
            r"token[=:]\s*[^\s]+",
            r"secret[=:]\s*[^\s]+",
            r"authorization[=:]\s*[^\s]+",
            r"bearer\s+[^\s]+",
            r"x-api-key[=:]\s*[^\s]+",
        ]

        import re

        for pattern in sensitive_patterns:
            message = re.sub(pattern, "[REDACTED]", message, flags=re.IGNORECASE)

        return message

    def sanitize_provider_error_response(self, error_response: str) -> str:
        """Sanitize provider error responses to prevent information leakage."""
        if not error_response:
            return "Provider error occurred"

        # Parse JSON if possible and sanitize fields that might contain sensitive info
        try:
            import json

            if isinstance(error_response, str):
                parsed = json.loads(error_response)
            else:
                parsed = error_response

            # Sanitize common fields that might contain sensitive information
            if isinstance(parsed, dict):
                for key in ["message", "error", "detail", "description"]:
                    if key in parsed and isinstance(parsed[key], str):
                        parsed[key] = self._sanitize_error_message(parsed[key])

                # Remove potentially sensitive fields
                sensitive_fields = ["trace", "stack", "debug", "internal"]
                for field in sensitive_fields:
                    if field in parsed:
                        parsed[field] = "[REDACTED]"

                return json.dumps(parsed)
            else:
                return self._sanitize_error_message(str(parsed))
        except (json.JSONDecodeError, TypeError):
            # If not JSON, just sanitize as string
            return self._sanitize_error_message(str(error_response))

    async def handle_validation_error(
        self, request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors specifically."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Extract validation details
        validation_errors = []
        for error in exc.errors():
            validation_error = {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            validation_errors.append(validation_error)

        error_response = {
            "error": {
                "request_id": request_id,
                "timestamp": int(time.time()),
                "type": "validation_error",
                "message": "Request validation failed",
                "details": validation_errors,
            }
        }

        logger.warning(
            "Validation error",
            request_id=request_id,
            validation_errors=validation_errors,
        )

        return JSONResponse(status_code=422, content=error_response)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        import time

        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "timestamp": int(time.time()),
        }


# Global error handler instance
error_handler = ErrorHandler()


# FastAPI exception handlers
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for FastAPI."""
    return await error_handler.handle_exception(request, exc)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Validation exception handler for FastAPI."""
    return await error_handler.handle_validation_error(request, exc)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP exception handler for FastAPI."""
    return await error_handler.handle_exception(request, exc)
