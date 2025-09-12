import pytest
import hashlib
import secrets
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.core.auth import APIKeyAuth, verify_api_key, get_api_key_auth


class TestAPIKeyAuth:
    """Test APIKeyAuth class"""

    def test_init_with_api_keys(self):
        """Test APIKeyAuth initialization with API keys"""
        api_keys = ["key1", "key2", "key3"]
        auth = APIKeyAuth(api_keys)

        assert len(auth.valid_api_key_hashes) == 3
        # Verify keys are hashed
        expected_hashes = {hashlib.sha256(key.encode()).hexdigest() for key in api_keys}
        assert auth.valid_api_key_hashes == expected_hashes

    def test_init_with_empty_keys(self):
        """Test APIKeyAuth initialization with empty key list"""
        auth = APIKeyAuth([])
        assert auth.valid_api_key_hashes == set()

    def test_init_with_none_keys(self):
        """Test APIKeyAuth initialization with None keys"""
        auth = APIKeyAuth([None, "", "valid_key"])
        # Should only include non-empty keys
        assert len(auth.valid_api_key_hashes) == 1
        expected_hash = hashlib.sha256("valid_key".encode()).hexdigest()
        assert expected_hash in auth.valid_api_key_hashes

    def test_verify_api_key_valid(self):
        """Test verify_api_key with valid key"""
        api_keys = ["test_key_123", "another_key"]
        auth = APIKeyAuth(api_keys)

        assert auth.verify_api_key("test_key_123") is True
        assert auth.verify_api_key("another_key") is True

    def test_verify_api_key_invalid(self):
        """Test verify_api_key with invalid key"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        assert auth.verify_api_key("invalid_key") is False
        assert auth.verify_api_key("") is False
        assert auth.verify_api_key(None) is False

    def test_verify_api_key_empty_list(self):
        """Test verify_api_key when no valid keys configured"""
        auth = APIKeyAuth([])

        assert auth.verify_api_key("any_key") is False
        assert auth.verify_api_key("") is False
        assert auth.verify_api_key(None) is False

    def test_verify_api_key_timing_attack_resistance(self):
        """Test that verify_api_key is resistant to timing attacks"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Test with keys of different lengths to ensure constant time
        import time

        start_time = time.time()
        auth.verify_api_key("short")
        short_time = time.time() - start_time

        start_time = time.time()
        auth.verify_api_key("a_very_long_key_that_should_take_more_time_to_hash_but_does_not_due_to_constant_time")
        long_time = time.time() - start_time

        # Times should be very close (within 10% difference)
        time_diff = abs(short_time - long_time)
        max_time = max(short_time, long_time)
        assert time_diff / max_time < 0.1

    def test_verify_api_key_case_sensitivity(self):
        """Test that verify_api_key is case sensitive"""
        api_keys = ["Test_Key_123"]
        auth = APIKeyAuth(api_keys)

        assert auth.verify_api_key("Test_Key_123") is True
        assert auth.verify_api_key("test_key_123") is False
        assert auth.verify_api_key("TEST_KEY_123") is False

    def test_verify_api_key_special_characters(self):
        """Test verify_api_key with special characters"""
        api_keys = ["key-with_special.chars!@#"]
        auth = APIKeyAuth(api_keys)

        assert auth.verify_api_key("key-with_special.chars!@#") is True
        assert auth.verify_api_key("key-with_special.chars!@# ") is False  # Extra space
        assert auth.verify_api_key("key-with_special.chars!@") is False   # Missing chars

    def test_verify_api_key_unicode(self):
        """Test verify_api_key with unicode characters"""
        api_keys = ["clé_avec_émojis🚀"]
        auth = APIKeyAuth(api_keys)

        assert auth.verify_api_key("clé_avec_émojis🚀") is True
        assert auth.verify_api_key("clé_avec_émojis") is False  # Missing emoji


class TestVerifyAPIKeyDependency:
    """Test verify_api_key FastAPI dependency"""

    @pytest.mark.asyncio
    async def test_verify_api_key_success_custom_header(self):
        """Test verify_api_key with custom header"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request with custom header
        mock_request = Mock()
        mock_request.headers = {"x-api-key": "test_key_123"}
        mock_request.app.state.api_key_auth = auth

        with patch('src.core.auth.config_manager') as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.api_key_header = "x-api-key"
            mock_config_manager.load_config.return_value = mock_config

            result = await verify_api_key(mock_request)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_api_key_success_authorization_header(self):
        """Test verify_api_key with Authorization header"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request with Authorization header
        mock_request = Mock()
        mock_request.headers = {"authorization": "Bearer test_key_123"}
        mock_request.app.state.api_key_auth = auth

        with patch('src.core.auth.config_manager') as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.api_key_header = "x-api-key"  # Different from actual header
            mock_config_manager.load_config.return_value = mock_config

            result = await verify_api_key(mock_request)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_api_key_no_key_provided(self):
        """Test verify_api_key when no API key is provided"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request without API key headers
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.url.path = "/test/endpoint"
        mock_request.app.state.api_key_auth = auth

        with patch('src.core.auth.config_manager') as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.api_key_header = "x-api-key"
            mock_config_manager.load_config.return_value = mock_config

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(mock_request)

            assert exc_info.value.status_code == 401
            assert "API key required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid_key(self):
        """Test verify_api_key with invalid API key"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request with invalid API key
        mock_request = Mock()
        mock_request.headers = {"x-api-key": "invalid_key"}
        mock_request.url.path = "/test/endpoint"
        mock_request.app.state.api_key_auth = auth

        with patch('src.core.auth.config_manager') as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.api_key_header = "x-api-key"
            mock_config_manager.load_config.return_value = mock_config

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(mock_request)

            assert exc_info.value.status_code == 401
            assert "Invalid or unauthorized API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_key_malformed_authorization_header(self):
        """Test verify_api_key with malformed Authorization header"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request with malformed Authorization header
        mock_request = Mock()
        mock_request.headers = {"authorization": "InvalidFormat test_key_123"}
        mock_request.url.path = "/test/endpoint"
        mock_request.app.state.api_key_auth = auth

        with patch('src.core.auth.config_manager') as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.api_key_header = "x-api-key"
            mock_config_manager.load_config.return_value = mock_config

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(mock_request)

            assert exc_info.value.status_code == 401
            assert "API key required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_key_empty_authorization_header(self):
        """Test verify_api_key with empty Authorization header"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request with empty Authorization header
        mock_request = Mock()
        mock_request.headers = {"authorization": ""}
        mock_request.url.path = "/test/endpoint"
        mock_request.app.state.api_key_auth = auth

        with patch('src.core.auth.config_manager') as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.api_key_header = "x-api-key"
            mock_config_manager.load_config.return_value = mock_config

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(mock_request)

            assert exc_info.value.status_code == 401
            assert "API key required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_api_key_case_insensitive_header(self):
        """Test verify_api_key with case insensitive header names"""
        api_keys = ["test_key_123"]
        auth = APIKeyAuth(api_keys)

        # Mock request with uppercase header
        mock_request = Mock()
        mock_request.headers = {"X-API-KEY": "test_key_123"}
        mock_request.app.state.api_key_auth = auth

        with patch('src.core.auth.config_manager') as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.api_key_header = "x-api-key"
            mock_config_manager.load_config.return_value = mock_config

            result = await verify_api_key(mock_request)
            assert result is True


class TestGetAPIKeyAuth:
    """Test get_api_key_auth dependency"""

    def test_get_api_key_auth(self):
        """Test get_api_key_auth dependency"""
        mock_request = Mock()
        mock_auth = Mock()
        mock_request.app.state.api_key_auth = mock_auth

        result = get_api_key_auth(mock_request)

        assert result == mock_auth


class TestAuthIntegration:
    """Integration tests for authentication"""

    @pytest.mark.asyncio
    async def test_auth_integration_with_app(self):
        """Test authentication integration with FastAPI app"""
        # This would require setting up a test app with authentication
        # For now, we'll test the components individually
        pass

    def test_api_key_hashing_consistency(self):
        """Test that API key hashing is consistent"""
        key = "test_key_123"
        hash1 = hashlib.sha256(key.encode()).hexdigest()
        hash2 = hashlib.sha256(key.encode()).hexdigest()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 character hex string

    def test_secrets_compare_digest_usage(self):
        """Test that secrets.compare_digest is used for secure comparison"""
        # This is more of a code review test to ensure secure practices
        with patch('secrets.compare_digest') as mock_compare:
            mock_compare.return_value = True

            auth = APIKeyAuth(["test_key"])
            result = auth.verify_api_key("test_key")

            # Should call compare_digest for each valid hash
            assert mock_compare.call_count == 1
            assert result is True

    def test_multiple_keys_verification(self):
        """Test verification with multiple valid keys"""
        api_keys = ["key1", "key2", "key3", "key4", "key5"]
        auth = APIKeyAuth(api_keys)

        # All keys should work
        for key in api_keys:
            assert auth.verify_api_key(key) is True

        # Invalid key should fail
        assert auth.verify_api_key("invalid") is False

    def test_empty_string_key_handling(self):
        """Test handling of empty string keys in initialization"""
        api_keys = ["", "valid_key", "", "another_valid"]
        auth = APIKeyAuth(api_keys)

        # Should only have 2 valid keys (non-empty ones)
        assert len(auth.valid_api_key_hashes) == 2

        assert auth.verify_api_key("valid_key") is True
        assert auth.verify_api_key("another_valid") is True
        assert auth.verify_api_key("") is False
        assert auth.verify_api_key("invalid") is False