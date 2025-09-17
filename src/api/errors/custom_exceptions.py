"""
Custom exceptions for API layer.

This module defines domain-specific exceptions for the API layer,
extending the core exceptions with API-specific context and error codes.
"""

from src.core.exceptions import AuthenticationError as CoreAuthenticationError
from src.core.exceptions import AuthorizationError as CoreAuthorizationError
from src.core.exceptions import InvalidRequestError as CoreInvalidRequestError
from src.core.exceptions import NotFoundError as CoreNotFoundError
from src.core.exceptions import RateLimitError as CoreRateLimitError
from src.core.exceptions import (
    ServiceUnavailableError as CoreServiceUnavailableError,
)


class APIException(Exception):
    """Base exception for API layer errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = None,
        details: dict = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or self.__class__.__name__.lower()
        self.details = details or {}


class ValidationError(APIException):
    """Exception raised for request validation failures."""

    def __init__(self, message: str, field: str = None, value: str = None, **kwargs):
        super().__init__(message, status_code=400, code="validation_error", **kwargs)
        self.field = field
        self.value = value

    def __str__(self):
        if self.field:
            return f"Validation error for field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class ModelNotFoundError(APIException):
    """Exception raised when requested model is not found."""

    def __init__(self, model_name: str, provider: str = None, **kwargs):
        message = f"Model '{model_name}' not found"
        if provider:
            message += f" for provider '{provider}'"
        super().__init__(message, status_code=404, code="model_not_found", **kwargs)
        self.model_name = model_name
        self.provider = provider


class ProviderUnavailableError(APIException):
    """Exception raised when provider is temporarily unavailable."""

    def __init__(
        self,
        provider_name: str,
        reason: str = None,
        retry_after: int = None,
        **kwargs,
    ):
        message = f"Provider '{provider_name}' is currently unavailable"
        if reason:
            message += f": {reason}"
        super().__init__(
            message, status_code=503, code="provider_unavailable", **kwargs
        )
        self.provider_name = provider_name
        self.reason = reason
        self.retry_after = retry_after


class QuotaExceededError(APIException):
    """Exception raised when API quota is exceeded."""

    def __init__(
        self,
        quota_type: str,
        limit: int = None,
        reset_time: str = None,
        **kwargs,
    ):
        message = f"{quota_type} quota exceeded"
        if limit:
            message += f" (limit: {limit})"
        if reset_time:
            message += f". Resets at {reset_time}"
        super().__init__(message, status_code=429, code="quota_exceeded", **kwargs)
        self.quota_type = quota_type
        self.limit = limit
        self.reset_time = reset_time


class UnsupportedOperationError(APIException):
    """Exception raised when operation is not supported."""

    def __init__(
        self, operation: str, model: str = None, provider: str = None, **kwargs
    ):
        message = f"Operation '{operation}' is not supported"
        if model:
            message += f" for model '{model}'"
        if provider:
            message += f" by provider '{provider}'"
        super().__init__(
            message, status_code=501, code="unsupported_operation", **kwargs
        )
        self.operation = operation
        self.model = model
        self.provider = provider


class ConfigurationError(APIException):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, status_code=500, code="configuration_error", **kwargs)
        self.config_key = config_key


class StreamingError(APIException):
    """Exception raised for streaming-related errors."""

    def __init__(self, message: str, stream_id: str = None, **kwargs):
        super().__init__(message, status_code=500, code="streaming_error", **kwargs)
        self.stream_id = stream_id


class TimeoutError(APIException):
    """Exception raised when operation times out."""

    def __init__(self, operation: str, timeout_seconds: int = None, **kwargs):
        message = f"Operation '{operation}' timed out"
        if timeout_seconds:
            message += f" after {timeout_seconds} seconds"
        super().__init__(message, status_code=504, code="timeout_error", **kwargs)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class PayloadTooLargeError(APIException):
    """Exception raised when request payload is too large."""

    def __init__(self, actual_size: int, max_size: int, **kwargs):
        message = f"Payload too large: {actual_size} bytes (max: {max_size} bytes)"
        super().__init__(message, status_code=413, code="payload_too_large", **kwargs)
        self.actual_size = actual_size
        self.max_size = max_size


class ConcurrentRequestError(APIException):
    """Exception raised when too many concurrent requests."""

    def __init__(self, current_requests: int, max_concurrent: int, **kwargs):
        message = f"Too many concurrent requests: {current_requests}/{max_concurrent}"
        super().__init__(
            message, status_code=429, code="concurrent_request_limit", **kwargs
        )
        self.current_requests = current_requests
        self.max_concurrent = max_concurrent


# Wrapper exceptions that extend core exceptions with API-specific context
class APIValidationError(CoreInvalidRequestError):
    """API-specific validation error extending core InvalidRequestError."""

    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field = field


class APINotFoundError(CoreNotFoundError):
    """API-specific not found error extending core NotFoundError."""

    def __init__(self, resource: str, resource_id: str = None, **kwargs):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, **kwargs)
        self.resource = resource
        self.resource_id = resource_id


class APIAuthenticationError(CoreAuthenticationError):
    """API-specific authentication error."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class APIAuthorizationError(CoreAuthorizationError):
    """API-specific authorization error."""

    def __init__(self, message: str = "Authorization failed", **kwargs):
        super().__init__(message, **kwargs)


class APIRateLimitError(CoreRateLimitError):
    """API-specific rate limit error."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class APIUnavailableError(CoreServiceUnavailableError):
    """API-specific service unavailable error."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


# Exception mapping for backwards compatibility
InvalidRequestError = APIValidationError
NotFoundError = APINotFoundError
AuthenticationError = APIAuthenticationError
AuthorizationError = APIAuthorizationError
RateLimitError = APIRateLimitError
ServiceUnavailableError = APIUnavailableError
