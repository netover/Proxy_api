from typing import Optional


class ProviderError(Exception):
    """Base exception for all provider errors"""

    def __init__(self, message: str, provider: str = "", code: str = "provider_error"):
        self.message = message
        self.provider = provider
        self.code = code
        super().__init__(self.message)

    def to_dict(self):
        return {
            "message": self.message,
            "type": self.code,
            "param": None,
            "code": self.code,
        }


class ProviderNotFoundError(ProviderError):
    """Exception raised when a provider is not found in the registry."""

    def __init__(self, provider_name: str, message: str = None):
        self.provider_name = provider_name
        message = message or f"Provider '{provider_name}' not found in registry"
        super().__init__(message, provider=provider_name, code="provider_not_found")


class ProviderUnavailableError(ProviderError):
    """Exception raised when a provider is unavailable (e.g., circuit breaker is open)."""

    def __init__(self, provider_name: str, message: str = None):
        self.provider_name = provider_name
        message = message or f"Provider '{provider_name}' is currently unavailable"
        super().__init__(message, provider=provider_name, code="provider_unavailable")


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
        message: str,
        retry_after: Optional[int] = None,
        code: str = "rate_limit_error",
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


class ValidationError(Exception):
    """Raised for validation errors in data processing"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotFoundError(ProviderError):
    """Raised when a requested resource is not found"""

    def __init__(self, message: str, code: str = "not_found_error"):
        super().__init__(message, code=code)


class TimeoutError(ProviderError):
    """Raised when an operation times out"""

    def __init__(self, message: str, code: str = "timeout_error"):
        super().__init__(message, code=code)


class ConfigurationError(Exception):
    """Raised for configuration-related errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InitializationError(Exception):
    """Raised for initialization-related errors"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
