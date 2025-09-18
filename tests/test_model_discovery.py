"""Unit tests for model discovery functionality."""

import pytest
from unittest.mock import AsyncMock, patch
import aiohttp

from src.core.providers.models import ModelInfo
from src.core.routing.model_discovery import ModelDiscoveryService, ProviderConfig
from src.core.routing.exceptions import ProviderError, ValidationError


class TestModelInfo:
    """Test cases for ModelInfo class."""

    def test_model_info_creation(self):
        """Test basic ModelInfo creation."""
        model = ModelInfo(
            id="gpt-4",
            created=1687882411,
            owned_by="openai",
            permissions=[{"id": "perm-123", "object": "model_permission"}],
        )

        assert model.id == "gpt-4"
        assert model.object == "model"
        assert model.created == 1687882411
        assert model.owned_by == "openai"
        assert len(model.permissions) == 1

    def test_model_info_validation(self):
        """Test ModelInfo validation."""
        # Valid model
        model = ModelInfo(
            id="test-model",
            created=1234567890,
            owned_by="test-org",
            permissions=[],
        )
        assert model.object == "model"

        # Invalid object
        with pytest.raises(ValueError, match="object must be 'model'"):
            ModelInfo(
                id="test",
                object="invalid",
                created=1234567890,
                owned_by="test",
                permissions=[],
            )

        # Empty id
        with pytest.raises(ValueError, match="id cannot be empty"):
            ModelInfo(id="", created=1234567890, owned_by="test", permissions=[])

        # Invalid timestamp
        with pytest.raises(
            ValueError, match="created must be a positive Unix timestamp"
        ):
            ModelInfo(id="test", created=-1, owned_by="test", permissions=[])

    def test_model_info_from_dict(self):
        """Test creating ModelInfo from dictionary."""
        data = {
            "id": "claude-3-opus-20240229",
            "object": "model",
            "created": 1707264000,
            "owned_by": "anthropic",
            "permissions": [{"id": "perm-456", "object": "model_permission"}],
            "root": "claude-3-opus-20240229",
            "parent": None,
        }

        model = ModelInfo.from_dict(data)
        assert model.id == "claude-3-opus-20240229"
        assert model.root == "claude-3-opus-20240229"
        assert model.parent is None

    def test_model_info_to_dict(self):
        """Test converting ModelInfo to dictionary."""
        model = ModelInfo(
            id="test-model",
            created=1234567890,
            owned_by="test-org",
            permissions=[{"id": "perm-789"}],
            root="test-model",
            parent=None,
        )

        data = model.to_dict()
        assert data["id"] == "test-model"
        assert data["object"] == "model"
        assert data["root"] == "test-model"
        assert data["parent"] is None

    def test_created_datetime_property(self):
        """Test the created_datetime property."""
        timestamp = 1234567890
        model = ModelInfo(id="test", created=timestamp, owned_by="test", permissions=[])

        dt = model.created_datetime
        assert dt.timestamp() == timestamp


class TestProviderConfig:
    """Test cases for ProviderConfig class."""

    def test_provider_config_creation(self):
        """Test basic ProviderConfig creation."""
        config = ProviderConfig(
            name="test-provider",
            base_url="https://api.test.com",
            api_key="test-key",
        )

        assert config.name == "test-provider"
        assert config.base_url == "https://api.test.com"
        assert config.api_key == "test-key"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_provider_config_with_options(self):
        """Test ProviderConfig with optional parameters."""
        config = ProviderConfig(
            name="test",
            base_url="https://api.test.com/",
            api_key="key",
            organization="org-123",
            timeout=60,
            max_retries=5,
        )

        assert config.base_url == "https://api.test.com"  # Trailing slash removed
        assert config.organization == "org-123"
        assert config.timeout == 60
        assert config.max_retries == 5


class TestModelDiscoveryService:
    """Test cases for ModelDiscoveryService."""

    @pytest.fixture
    def service(self):
        """Create a ModelDiscoveryService instance."""
        return ModelDiscoveryService()

    @pytest.fixture
    def provider_config(self):
        """Create a test ProviderConfig."""
        return ProviderConfig(
            name="test-provider",
            base_url="https://api.test.com",
            api_key="test-key",
        )

    @pytest.mark.asyncio
    async def test_discover_models_success(self, service, provider_config):
        """Test successful model discovery."""
        mock_response = {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4",
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "openai",
                    "permissions": [{"id": "modelperm-abc123"}],
                    "root": "gpt-4",
                    "parent": None,
                },
                {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "openai",
                    "permissions": [{"id": "modelperm-def456"}],
                    "root": "gpt-3.5-turbo",
                    "parent": None,
                },
            ],
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            models = await service.discover_models(provider_config)

            assert len(models) == 2
            assert models[0].id == "gpt-4"
            assert models[1].id == "gpt-3.5-turbo"
            assert models[0].owned_by == "openai"

    @pytest.mark.asyncio
    async def test_discover_models_empty_response(self, service, provider_config):
        """Test handling empty model list."""
        mock_response = {"object": "list", "data": []}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            models = await service.discover_models(provider_config)

            assert len(models) == 0

    @pytest.mark.asyncio
    async def test_discover_models_invalid_response(self, service, provider_config):
        """Test handling invalid response format."""
        mock_response = {"invalid": "format"}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            with pytest.raises(ValidationError, match="Invalid response format"):
                await service.discover_models(provider_config)

    @pytest.mark.asyncio
    async def test_discover_models_auth_error(self, service, provider_config):
        """Test handling authentication errors."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 401
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            with pytest.raises(ProviderError, match="Authentication failed"):
                await service.discover_models(provider_config)

    @pytest.mark.asyncio
    async def test_discover_models_rate_limit(self, service, provider_config):
        """Test handling rate limiting with retries."""
        mock_response = {
            "object": "list",
            "data": [
                {
                    "id": "test-model",
                    "object": "model",
                    "created": 1234567890,
                    "owned_by": "test",
                    "permissions": [],
                }
            ],
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            # First two calls return 429, third succeeds
            mock_get.side_effect = [
                AsyncMock(
                    status=429,
                    __aenter__=AsyncMock(return_value=AsyncMock(status=429)),
                ),
                AsyncMock(
                    status=429,
                    __aenter__=AsyncMock(return_value=AsyncMock(status=429)),
                ),
                AsyncMock(
                    status=200,
                    __aenter__=AsyncMock(
                        return_value=AsyncMock(
                            status=200,
                            json=AsyncMock(return_value=mock_response),
                        )
                    ),
                ),
            ]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                models = await service.discover_models(provider_config)

            assert len(models) == 1
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_validate_model_success(self, service, provider_config):
        """Test successful model validation."""
        mock_response = {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4",
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "openai",
                    "permissions": [],
                },
                {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "openai",
                    "permissions": [],
                },
            ],
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            is_valid = await service.validate_model(provider_config, "gpt-4")
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_model_not_found(self, service, provider_config):
        """Test validating non-existent model."""
        mock_response = {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4",
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "openai",
                    "permissions": [],
                }
            ],
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            is_valid = await service.validate_model(
                provider_config, "non-existent-model"
            )
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_model_provider_error(self, service, provider_config):
        """Test validation when provider is unreachable."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Connection failed")

            is_valid = await service.validate_model(provider_config, "gpt-4")
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_get_model_info_success(self, service, provider_config):
        """Test getting model info for existing model."""
        mock_response = {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4",
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "openai",
                    "permissions": [],
                }
            ],
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            model_info = await service.get_model_info(provider_config, "gpt-4")

            assert model_info is not None
            assert model_info.id == "gpt-4"
            assert model_info.owned_by == "openai"

    @pytest.mark.asyncio
    async def test_get_model_info_not_found(self, service, provider_config):
        """Test getting model info for non-existent model."""
        mock_response = {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4",
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "openai",
                    "permissions": [],
                }
            ],
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            model_info = await service.get_model_info(provider_config, "non-existent")
            assert model_info is None

    @pytest.mark.asyncio
    async def test_context_manager(self, service):
        """Test async context manager functionality."""
        service.close = AsyncMock()

        async with service:
            pass

        service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_invalid_models(self, service, provider_config):
        """Test skipping invalid model data in response."""
        mock_response = {
            "object": "list",
            "data": [
                {
                    "id": "valid-model",
                    "object": "model",
                    "created": 1234567890,
                    "owned_by": "test",
                    "permissions": [],
                },
                {
                    "id": "invalid-model",
                    "object": "invalid",
                    "created": 1234567890,
                    "owned_by": "test",
                    "permissions": [],
                },
                {
                    "id": "another-valid",
                    "object": "model",
                    "created": 1234567890,
                    "owned_by": "test",
                    "permissions": [],
                },
            ],
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj

            models = await service.discover_models(provider_config)

            # Should skip the invalid model
            assert len(models) == 2
            model_ids = [m.id for m in models]
            assert "valid-model" in model_ids
            assert "another-valid" in model_ids
            assert "invalid-model" not in model_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
