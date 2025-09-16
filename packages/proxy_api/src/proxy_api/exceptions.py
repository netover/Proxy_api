"""Exception classes for proxy_api package."""

# Import core exceptions to maintain consistency
from src.core.exceptions import (
    AuthenticationError as CoreAuthenticationError,
    InvalidRequestError as CoreInvalidRequestError,
    NotFoundError as CoreNotFoundError,
    RateLimitError as CoreRateLimitError,
    ServiceUnavailableError as CoreServiceUnavailableError,
)

# Use core exceptions for consistency
AuthenticationError = CoreAuthenticationError
InvalidRequestError = CoreInvalidRequestError
NotFoundError = CoreNotFoundError
RateLimitError = CoreRateLimitError
ServiceUnavailableError = CoreServiceUnavailableError
