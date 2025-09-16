"""
Standardized error response formats for API endpoints.

This module provides consistent error response structures and utilities
for formatting different types of API errors.
"""

import time
from typing import Any, Dict, List

from fastapi.responses import JSONResponse


class ErrorResponse:
    """Standardized error response structure."""

    def __init__(
        self,
        message: str,
        error_type: str,
        status_code: int = 500,
        code: str = None,
        details: Dict[str, Any] = None,
        request_id: str = None,
    ):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.code = code or error_type.lower().replace("_", "_")
        self.details = details or {}
        self.request_id = request_id
        self.timestamp = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        response = {
            "error": {
                "message": self.message,
                "type": self.error_type,
                "code": self.code,
                "timestamp": self.timestamp,
            }
        }

        if self.request_id:
            response["error"]["request_id"] = self.request_id

        if self.details:
            response["error"]["details"] = self.details

        return response

    def to_json_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse."""
        return JSONResponse(
            status_code=self.status_code, content=self.to_dict()
        )


class ValidationErrorResponse(ErrorResponse):
    """Error response for validation failures."""

    def __init__(
        self,
        message: str,
        field: str = None,
        value: Any = None,
        validation_errors: List[Dict] = None,
        **kwargs,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if validation_errors:
            details["validation_errors"] = validation_errors

        super().__init__(
            message=message,
            error_type="validation_error",
            status_code=400,
            code="validation_failed",
            details=details,
            **kwargs,
        )


class AuthenticationErrorResponse(ErrorResponse):
    """Error response for authentication failures."""

    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            message=message,
            error_type="authentication_error",
            status_code=401,
            code="authentication_required",
            **kwargs,
        )


class AuthorizationErrorResponse(ErrorResponse):
    """Error response for authorization failures."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permissions: List[str] = None,
        **kwargs,
    ):
        details = {}
        if required_permissions:
            details["required_permissions"] = required_permissions

        super().__init__(
            message=message,
            error_type="authorization_error",
            status_code=403,
            code="insufficient_permissions",
            details=details,
            **kwargs,
        )


class NotFoundErrorResponse(ErrorResponse):
    """Error response for resource not found."""

    def __init__(self, resource: str, resource_id: str = None, **kwargs):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"

        details = {"resource": resource}
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_type="not_found_error",
            status_code=404,
            code="resource_not_found",
            details=details,
            **kwargs,
        )


class RateLimitErrorResponse(ErrorResponse):
    """Error response for rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = None,
        limit: int = None,
        **kwargs,
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        if limit:
            details["limit"] = limit

        super().__init__(
            message=message,
            error_type="rate_limit_error",
            status_code=429,
            code="rate_limit_exceeded",
            details=details,
            **kwargs,
        )


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Error response for service unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int = None,
        reason: str = None,
        **kwargs,
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            error_type="service_unavailable",
            status_code=503,
            code="service_unavailable",
            details=details,
            **kwargs,
        )


class InternalServerErrorResponse(ErrorResponse):
    """Error response for internal server errors."""

    def __init__(
        self,
        message: str = "Internal server error",
        show_details: bool = False,
        **kwargs,
    ):
        # Don't expose internal details in production
        if not show_details and "internal" in message.lower():
            message = "An unexpected error occurred"

        super().__init__(
            message=message,
            error_type="internal_server_error",
            status_code=500,
            code="internal_error",
            **kwargs,
        )


class BadRequestErrorResponse(ErrorResponse):
    """Error response for bad requests."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_type="bad_request",
            status_code=400,
            code="bad_request",
            **kwargs,
        )


class PayloadTooLargeErrorResponse(ErrorResponse):
    """Error response for payload too large."""

    def __init__(self, actual_size: int, max_size: int, **kwargs):
        message = f"Payload too large: {actual_size} bytes (maximum allowed: {max_size} bytes)"
        details = {"actual_size": actual_size, "max_size": max_size}

        super().__init__(
            message=message,
            error_type="payload_too_large",
            status_code=413,
            code="payload_too_large",
            details=details,
            **kwargs,
        )


class UnsupportedMediaTypeErrorResponse(ErrorResponse):
    """Error response for unsupported media type."""

    def __init__(
        self, content_type: str, supported_types: List[str] = None, **kwargs
    ):
        message = f"Unsupported media type: {content_type}"
        details = {"content_type": content_type}
        if supported_types:
            details["supported_types"] = supported_types

        super().__init__(
            message=message,
            error_type="unsupported_media_type",
            status_code=415,
            code="unsupported_media_type",
            details=details,
            **kwargs,
        )


class MethodNotAllowedErrorResponse(ErrorResponse):
    """Error response for method not allowed."""

    def __init__(
        self, method: str, allowed_methods: List[str] = None, **kwargs
    ):
        message = f"Method {method} not allowed"
        details = {"method": method}
        if allowed_methods:
            details["allowed_methods"] = allowed_methods

        super().__init__(
            message=message,
            error_type="method_not_allowed",
            status_code=405,
            code="method_not_allowed",
            details=details,
            **kwargs,
        )


def create_error_response_from_exception(
    exc: Exception, request_id: str = None
) -> ErrorResponse:
    """Create appropriate error response from exception type."""
    from .custom_exceptions import (
        APIAuthenticationError,
        APIAuthorizationError,
        APINotFoundError,
        APIRateLimitError,
        APIUnavailableError,
        APIValidationError,
        ConcurrentRequestError,
        ConfigurationError,
        ModelNotFoundError,
        PayloadTooLargeError,
        ProviderUnavailableError,
        QuotaExceededError,
        StreamingError,
        TimeoutError,
        UnsupportedOperationError,
        ValidationError,
    )

    # Map exception types to response classes
    exception_mapping = {
        ValidationError: ValidationErrorResponse,
        APIValidationError: ValidationErrorResponse,
        ModelNotFoundError: NotFoundErrorResponse,
        APINotFoundError: NotFoundErrorResponse,
        ProviderUnavailableError: ServiceUnavailableErrorResponse,
        APIUnavailableError: ServiceUnavailableErrorResponse,
        QuotaExceededError: lambda msg, **kwargs: RateLimitErrorResponse(
            msg, **kwargs
        ),
        UnsupportedOperationError: lambda msg, **kwargs: InternalServerErrorResponse(
            msg, **kwargs
        ),
        ConfigurationError: InternalServerErrorResponse,
        StreamingError: InternalServerErrorResponse,
        TimeoutError: lambda msg, **kwargs: ServiceUnavailableErrorResponse(
            msg, **kwargs
        ),
        PayloadTooLargeError: PayloadTooLargeErrorResponse,
        ConcurrentRequestError: lambda msg, **kwargs: RateLimitErrorResponse(
            msg, **kwargs
        ),
        APIAuthenticationError: AuthenticationErrorResponse,
        APIAuthorizationError: AuthorizationErrorResponse,
        APIRateLimitError: RateLimitErrorResponse,
    }

    response_class = exception_mapping.get(
        type(exc), InternalServerErrorResponse
    )

    # Create response instance
    if hasattr(exc, "field"):
        response = response_class(
            str(exc), field=getattr(exc, "field", None), request_id=request_id
        )
    elif hasattr(exc, "resource"):
        response = response_class(
            str(exc),
            resource=getattr(exc, "resource", None),
            resource_id=getattr(exc, "resource_id", None),
            request_id=request_id,
        )
    elif hasattr(exc, "retry_after"):
        response = response_class(
            str(exc),
            retry_after=getattr(exc, "retry_after", None),
            request_id=request_id,
        )
    else:
        response = response_class(str(exc), request_id=request_id)

    return response


# Utility functions for common error responses
def bad_request(
    message: str, request_id: str = None
) -> BadRequestErrorResponse:
    """Create bad request error response."""
    return BadRequestErrorResponse(message, request_id=request_id)


def not_found(
    resource: str, resource_id: str = None, request_id: str = None
) -> NotFoundErrorResponse:
    """Create not found error response."""
    return NotFoundErrorResponse(resource, resource_id, request_id=request_id)


def unauthorized(
    message: str = "Authentication required", request_id: str = None
) -> AuthenticationErrorResponse:
    """Create unauthorized error response."""
    return AuthenticationErrorResponse(message, request_id=request_id)


def forbidden(
    message: str = "Access denied", request_id: str = None
) -> AuthorizationErrorResponse:
    """Create forbidden error response."""
    return AuthorizationErrorResponse(message, request_id=request_id)


def rate_limited(
    retry_after: int = None, request_id: str = None
) -> RateLimitErrorResponse:
    """Create rate limit error response."""
    return RateLimitErrorResponse(
        "Rate limit exceeded", retry_after=retry_after, request_id=request_id
    )


def service_unavailable(
    reason: str = None, retry_after: int = None, request_id: str = None
) -> ServiceUnavailableErrorResponse:
    """Create service unavailable error response."""
    message = "Service temporarily unavailable"
    if reason:
        message += f": {reason}"
    return ServiceUnavailableErrorResponse(
        message, retry_after=retry_after, request_id=request_id
    )


def internal_error(
    message: str = "Internal server error", request_id: str = None
) -> InternalServerErrorResponse:
    """Create internal server error response."""
    return InternalServerErrorResponse(message, request_id=request_id)
