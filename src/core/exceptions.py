from typing import Optional


class ProviderError(Exception):
    """Base exception for all provider errors"""

    def __init__(self, message: str, provider: str = "", code: str = "provider_error"):
        self.message = message
        self.provider_name = provider  # Changed to provider_name to match test expectations
        self.code = code
        super().__init__(self.message)

    def to_dict(self):
        return {
            "message": self.message,
            "type": self.code,
            "param": None,
            "code": self.code,
        }


class InvalidRequestError(ProviderError):
    """Raised for invalid request parameters"""

    def __init__(
        self,
        message: str,
        param: str = "unknown",
        code: str = "invalid_request_error",
    ):
        super().__init__(message, code=code)
        self.param = param


class RateLimitError(ProviderError):
    """Raised for rate limiting errors"""

    def __init__(
        self,
        retry_after: Optional[int] = None,
        code: str = "rate_limit_error",
        message: str = "Rate limit exceeded"
    ):
        super().__init__(message, code=code)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Raised for authentication failures"""

    def __init__(self, message: str, code: str = "authentication_error"):
        super().__init__(message, code=code)

class AuthorizationError(ProviderError):
    """Raised for authorization failures"""

    def __init__(self, message: str, code: str = "authorization_error"):
        super().__init__(message, code=code)


class ServiceUnavailableError(ProviderError):
    """Raised when service is unavailable"""

    def __init__(self, message: str, code: str = "service_unavailable_error"):
        super().__init__(message, code=code)


class NotImplementedError(ProviderError):
    """Raised when operation is not implemented by provider"""

    def __init__(self, message: str, code: str = "not_implemented_error"):
        super().__init__(message, code=code)


class APIConnectionError(ProviderError):
    """Raised for API connection errors"""

    def __init__(self, message: str, code: str = "api_connection_error"):
        super().__init__(message, code=code)

class ProviderNotFoundError(ProviderError):
    """Raised when a provider is not found"""

    def __init__(self, message: str, code: str = "provider_not_found_error"):
        super().__init__(message, code=code)

class ProviderUnavailableError(ProviderError):
    """Raised when a provider is unavailable"""

    def __init__(self, message: str, code: str = "provider_unavailable_error"):
        super().__init__(message, code=code)

class NotFoundError(ProviderError):
    """Raised when a resource is not found"""

    def __init__(self, message: str, code: str = "not_found_error"):
        super().__init__(message, code=code)


class APIException(Exception):
    """Base exception for API-related errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        details: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "message": self.message,
                "type": self.error_code,
                "code": self.error_code,
                **self.details
            }
        }


class ValidationError(Exception):
    """Raised for validation errors in data processing"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(Exception):
    """Raised for configuration-related errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
