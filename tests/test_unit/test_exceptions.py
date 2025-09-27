"""
Unit tests for exception handling and error management.
"""

import pytest
from src.core.exceptions import (
    ProviderNotFoundError,
    ProviderUnavailableError,
    InvalidRequestError,
    ServiceUnavailableError,
    APIException,
    ProviderError
)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_provider_not_found_error(self):
        """Test ProviderNotFoundError."""
        error = ProviderNotFoundError("Provider 'test' not found")

        assert str(error) == "Provider 'test' not found"
        assert error.code == "provider_not_found_error"

    def test_provider_unavailable_error(self):
        """Test ProviderUnavailableError."""
        error = ProviderUnavailableError("Provider 'test' is unavailable")

        assert str(error) == "Provider 'test' is unavailable"
        assert error.code == "provider_unavailable_error"

    def test_invalid_request_error(self):
        """Test InvalidRequestError."""
        error = InvalidRequestError("Invalid model parameter", param="model", code="invalid_model")

        assert str(error) == "Invalid model parameter"
        assert error.param == "model"
        assert error.code == "invalid_model"

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError."""
        error = ServiceUnavailableError("Service is temporarily unavailable", code="service_down")

        assert str(error) == "Service is temporarily unavailable"
        assert error.code == "service_down"

    def test_api_exception(self):
        """Test APIException base class."""
        error = APIException("API error", status_code=400, error_code="api_error")

        assert str(error) == "API error"
        assert error.status_code == 400
        assert error.error_code == "api_error"


class TestExceptionInheritance:
    """Test exception inheritance and relationships."""

    def test_exception_hierarchy(self):
        """Test that custom exceptions inherit from appropriate base classes."""

        # Provider exceptions should inherit from ProviderError
        provider_error = ProviderNotFoundError("test")
        assert isinstance(provider_error, ProviderError)

        # API exceptions should inherit from APIException
        api_error = APIException("API error")
        assert isinstance(api_error, APIException)

        # Provider exceptions inherit from ProviderError, not APIException
        unavailable_error = ProviderUnavailableError("test")
        assert isinstance(unavailable_error, ProviderError)

        # Request exceptions should inherit from ProviderError
        request_error = InvalidRequestError("test")
        assert isinstance(request_error, ProviderError)

        service_error = ServiceUnavailableError("test")
        assert isinstance(service_error, ProviderError)

    def test_exception_attributes(self):
        """Test exception attributes."""
        error = InvalidRequestError("Test error", param="test_param", code="test_code")

        assert hasattr(error, 'param')
        assert hasattr(error, 'code')
        assert error.param == "test_param"
        assert error.code == "test_code"

    def test_exception_serialization(self):
        """Test exception serialization for API responses."""
        error = InvalidRequestError("Test error", param="model", code="invalid_model")

        # Should be serializable to dict
        error_dict = {
            "detail": str(error),
            "param": error.param,
            "code": error.code
        }

        assert error_dict["detail"] == "Test error"
        assert error_dict["param"] == "model"
        assert error_dict["code"] == "invalid_model"
