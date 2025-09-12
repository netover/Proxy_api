"""Exception classes for proxy_api package."""


class ProxyAPIException(Exception):
    """Base exception for proxy API."""
    pass


class InvalidRequestError(ProxyAPIException):
    """Invalid request error."""
    def __init__(self, message: str, code: str = "invalid_request_error"):
        super().__init__(message)
        self.code = code


class NotFoundError(ProxyAPIException):
    """Resource not found error."""
    def __init__(self, message: str, code: str = "resource_not_found"):
        super().__init__(message)
        self.code = code


class AuthenticationError(ProxyAPIException):
    """Authentication error."""
    def __init__(self, message: str, code: str = "authentication_error"):
        super().__init__(message)
        self.code = code


class RateLimitError(ProxyAPIException):
    """Rate limit exceeded error."""
    def __init__(self, message: str, code: str = "rate_limit_exceeded"):
        super().__init__(message)
        self.code = code