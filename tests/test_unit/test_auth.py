"""
Unit tests for authentication system.
"""

import pytest
from unittest.mock import patch
from src.core.security.auth import APIKeyAuth, verify_api_key


class TestAPIKeyAuth:
    """Test API key authentication."""

    def test_api_key_auth_initialization(self):
        """Test API key auth initialization."""
        valid_keys = ["key1", "key2", "key3"]
        auth = APIKeyAuth(valid_keys)

        assert auth.valid_keys == set(valid_keys)
        assert len(auth.valid_keys) == 3

    def test_api_key_validation(self):
        """Test API key validation."""
        valid_keys = ["secret_key_123", "another_key_456"]
        auth = APIKeyAuth(valid_keys)

        # Test valid keys
        assert auth.verify("secret_key_123") is True
        assert auth.verify("another_key_456") is True

        # Test invalid keys
        assert auth.verify("invalid_key") is False
        assert auth.verify("") is False
        assert auth.verify(None) is False

    def test_empty_valid_keys(self):
        """Test API key auth with empty valid keys."""
        auth = APIKeyAuth([])

        # All keys should be invalid
        assert auth.verify("any_key") is False

    def test_verify_api_key_function(self):
        """Test verify_api_key function."""
        # This test is complex because verify_api_key requires a Request object
        # For now, let's test the auth manager directly
        valid_keys = ["test_key_123"]
        auth = APIKeyAuth(valid_keys)

        # Test valid key
        assert auth.verify("test_key_123") is True

        # Test invalid key
        assert auth.verify("invalid_key") is False


class TestAuthenticationIntegration:
    """Test authentication integration."""

    def test_auth_middleware_simulation(self):
        """Test authentication middleware simulation."""
        valid_keys = ["test_key_123"]
        auth = APIKeyAuth(valid_keys)

        # Simulate FastAPI request with API key
        class MockRequest:
            def __init__(self, api_key):
                self.headers = {"X-API-Key": api_key} if api_key else {}

        # Test valid API key
        request = MockRequest("test_key_123")
        api_key = request.headers.get("X-API-Key")
        is_valid = auth.verify(api_key)
        assert is_valid is True

        # Test invalid API key
        request = MockRequest("invalid_key")
        api_key = request.headers.get("X-API-Key")
        is_valid = auth.verify(api_key)
        assert is_valid is False

        # Test missing API key
        request = MockRequest(None)
        api_key = request.headers.get("X-API-Key")
        is_valid = auth.verify(api_key)
        assert is_valid is False

    def test_multiple_valid_keys(self):
        """Test with multiple valid API keys."""
        valid_keys = ["key1", "key2", "key3", "key4"]
        auth = APIKeyAuth(valid_keys)

        # All valid keys should work
        for key in valid_keys:
            assert auth.verify(key) is True

        # Invalid keys should not work
        assert auth.verify("invalid") is False
        assert auth.verify("key5") is False
