"""
Comprehensive tests for model discovery external service calls
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

import aiohttp
from src.core.model_discovery import ModelDiscoveryService, ProviderConfig
from src.models.model_info import ModelInfo
from src.core.exceptions import ProviderError, ValidationError


class TestModelDiscoveryExternalCalls:
    """Test external service calls in ModelDiscoveryService"""

    @pytest.fixture
    def provider_config(self):
        """Create a test provider configuration"""
        return ProviderConfig(
            name="test_provider",
            base_url="https://api.test-provider.com",
            api_key="test-api-key",
            organization="test-org",
            timeout=30,
            max_retries=2,
        )

    @pytest.fixture
    def discovery_service(self):
        """Create a model discovery service for testing"""
        return ModelDiscoveryService()

    @pytest.fixture
    def mock_model_data(self):
        """Create mock model data"""
        return {
            "data": [
                {
                    "id": "gpt-4",
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "openai",
                    "permission": [],
                    "root": "gpt-4",
                    "parent": None,
                },
                {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "openai",
                    "permission": [],
                    "root": "gpt-3.5-turbo",
                    "parent": None,
                },
            ]
        }

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache"""
        cache = AsyncMock()
        cache.get.return_value = None  # Cache miss by default
        cache.set.return_value = True
        cache.delete.return_value = True
        cache.clear.return_value = 5
        cache.get_stats.return_value = {
            "entries": 10,
            "categories": {"models": 3},
            "hit_rate": 0.85,
            "memory_usage_mb": 50,
            "max_memory_mb": 100,
        }
        return cache

    @pytest.mark.asyncio
    async def test_successful_model_discovery(
        self, discovery_service, provider_config, mock_model_data, mock_cache
    ):
        """Test successful model discovery from external API"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock successful response
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = mock_model_data
                mock_session.get.return_value.__aenter__.return_value = mock_response

                models = await discovery_service.discover_models(provider_config)

                assert len(models) == 2
                assert models[0].id == "gpt-4"
                assert models[1].id == "gpt-3.5-turbo"

                # Verify HTTP call
                mock_session.get.assert_called_once()
                call_args = mock_session.get.call_args
                assert call_args[0][0] == "https://api.test-provider.com/v1/models"
                assert call_args[1]["headers"]["Authorization"] == "Bearer test-api-key"
                assert call_args[1]["headers"]["OpenAI-Organization"] == "test-org"

                # Verify cache was set
                mock_cache.set.assert_called_once()
                cache_call_args = mock_cache.set.call_args
                assert cache_call_args[1]["ttl"] == 900  # 15 minutes
                assert cache_call_args[1]["category"] == "models"

    @pytest.mark.asyncio
    async def test_model_discovery_cache_hit(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test model discovery cache hit"""
        cached_models = [
            ModelInfo(
                id="gpt-4",
                object="model",
                created=1687882411,
                owned_by="openai",
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                object="model",
                created=1677610602,
                owned_by="openai",
            ),
        ]
        mock_cache.get.return_value = cached_models

        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            models = await discovery_service.discover_models(provider_config)

            assert models == cached_models
            # Cache should not be set again
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_model_discovery_authentication_error(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test authentication error handling"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock 401 response
                mock_response = AsyncMock()
                mock_response.status = 401
                mock_session.get.return_value.__aenter__.return_value = mock_response

                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(provider_config)

                assert "Authentication failed" in str(exc_info.value)
                assert "test_provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_model_discovery_forbidden_error(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test forbidden error handling"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock 403 response
                mock_response = AsyncMock()
                mock_response.status = 403
                mock_session.get.return_value.__aenter__.return_value = mock_response

                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(provider_config)

                assert "Access forbidden" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_model_discovery_rate_limit_with_retry(
        self, discovery_service, provider_config, mock_model_data, mock_cache
    ):
        """Test rate limit handling with retry"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock rate limit then success
                mock_rate_limit_response = AsyncMock()
                mock_rate_limit_response.status = 429

                mock_success_response = AsyncMock()
                mock_success_response.status = 200
                mock_success_response.json.return_value = mock_model_data

                mock_session.get.side_effect = [
                    mock_rate_limit_response,  # First call - rate limited
                    mock_success_response,  # Second call - success
                ]

                with patch("asyncio.sleep") as mock_sleep:
                    models = await discovery_service.discover_models(provider_config)

                    assert len(models) == 2
                    # Should have waited for retry
                    mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second

    @pytest.mark.asyncio
    async def test_model_discovery_rate_limit_exhausted(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test rate limit retry exhaustion"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock persistent rate limit
                mock_response = AsyncMock()
                mock_response.status = 429
                mock_session.get.return_value.__aenter__.return_value = mock_response

                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(provider_config)

                assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_model_discovery_network_error_with_retry(
        self, discovery_service, provider_config, mock_model_data, mock_cache
    ):
        """Test network error handling with retry"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                mock_success_response = AsyncMock()
                mock_success_response.status = 200
                mock_success_response.json.return_value = mock_model_data

                # First two calls fail with network error, third succeeds
                mock_session.get.side_effect = [
                    aiohttp.ClientError("Network error"),
                    aiohttp.ClientError("Network error"),
                    mock_success_response,
                ]

                with patch("asyncio.sleep") as mock_sleep:
                    models = await discovery_service.discover_models(provider_config)

                    assert len(models) == 2
                    # Should have waited twice
                    assert mock_sleep.call_count == 2
                    mock_sleep.assert_any_call(1)  # 2^0
                    mock_sleep.assert_any_call(2)  # 2^1

    @pytest.mark.asyncio
    async def test_model_discovery_network_error_exhausted(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test network error retry exhaustion"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Persistent network error
                mock_session.get.side_effect = aiohttp.ClientError(
                    "Persistent network error"
                )

                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(provider_config)

                assert "Failed to connect to test_provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_model_discovery_timeout_error(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test timeout error handling"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Timeout error
                mock_session.get.side_effect = asyncio.TimeoutError("Request timed out")

                with pytest.raises(ProviderError) as exc_info:
                    await discovery_service.discover_models(provider_config)

                assert "Timeout connecting to test_provider" in str(exc_info.value)
                assert "30s" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_model_discovery_invalid_response_format(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test invalid response format handling"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock response with invalid format
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "invalid": "format"
                }  # Missing 'data' key
                mock_session.get.return_value.__aenter__.return_value = mock_response

                with pytest.raises(ValidationError) as exc_info:
                    await discovery_service.discover_models(provider_config)

                assert "Invalid response format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_model_discovery_invalid_model_data(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test handling of invalid model data in response"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock response with invalid model data
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "data": [
                        {
                            "id": "valid-model",
                            "object": "model",
                            "created": 1234567890,
                            "owned_by": "test",
                        },
                        {"invalid": "data"},  # Missing required fields
                        {
                            "id": "another-valid",
                            "object": "model",
                            "created": 1234567891,
                            "owned_by": "test",
                        },
                    ]
                }
                mock_session.get.return_value.__aenter__.return_value = mock_response

                models = await discovery_service.discover_models(provider_config)

                # Should skip invalid model and return valid ones
                assert len(models) == 2
                assert models[0].id == "valid-model"
                assert models[1].id == "another-valid"

    @pytest.mark.asyncio
    async def test_model_discovery_empty_response(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test handling of empty model list"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                # Mock response with empty data
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"data": []}
                mock_session.get.return_value.__aenter__.return_value = mock_response

                models = await discovery_service.discover_models(provider_config)

                assert len(models) == 0
                # Should still cache empty result
                mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_model_success(
        self, discovery_service, provider_config, mock_model_data, mock_cache
    ):
        """Test successful model validation"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = mock_model_data
                mock_session.get.return_value.__aenter__.return_value = mock_response

                is_valid = await discovery_service.validate_model(
                    provider_config, "gpt-4"
                )

                assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_model_not_found(
        self, discovery_service, provider_config, mock_model_data, mock_cache
    ):
        """Test model validation for non-existent model"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = mock_model_data
                mock_session.get.return_value.__aenter__.return_value = mock_response

                is_valid = await discovery_service.validate_model(
                    provider_config, "non-existent-model"
                )

                assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_model_provider_error(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test model validation with provider error"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                mock_response = AsyncMock()
                mock_response.status = 500
                mock_session.get.return_value.__aenter__.return_value = mock_response

                is_valid = await discovery_service.validate_model(
                    provider_config, "gpt-4"
                )

                assert is_valid is False

    @pytest.mark.asyncio
    async def test_get_model_info_success(
        self, discovery_service, provider_config, mock_model_data, mock_cache
    ):
        """Test successful model info retrieval"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = mock_model_data
                mock_session.get.return_value.__aenter__.return_value = mock_response

                model_info = await discovery_service.get_model_info(
                    provider_config, "gpt-4"
                )

                assert model_info is not None
                assert model_info.id == "gpt-4"
                assert model_info.owned_by == "openai"

    @pytest.mark.asyncio
    async def test_get_model_info_not_found(
        self, discovery_service, provider_config, mock_model_data, mock_cache
    ):
        """Test model info retrieval for non-existent model"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = mock_model_data
                mock_session.get.return_value.__aenter__.return_value = mock_response

                model_info = await discovery_service.get_model_info(
                    provider_config, "non-existent"
                )

                assert model_info is None

    @pytest.mark.asyncio
    async def test_cache_invalidation(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test cache invalidation"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            result = await discovery_service.invalidate_model_cache(provider_config)

            assert result is True
            mock_cache.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_invalidation_not_found(
        self, discovery_service, provider_config, mock_cache
    ):
        """Test cache invalidation when entry not found"""
        mock_cache.delete.return_value = False

        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            result = await discovery_service.invalidate_model_cache(provider_config)

            assert result is False

    @pytest.mark.asyncio
    async def test_clear_all_cache(self, discovery_service, mock_cache):
        """Test clearing all model cache"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            count = await discovery_service.clear_all_model_cache()

            assert count == 5
            mock_cache.clear.assert_called_once_with(category="models")

    @pytest.mark.asyncio
    async def test_cache_stats(self, discovery_service, mock_cache):
        """Test cache statistics retrieval"""
        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            stats = await discovery_service.get_cache_stats()

            assert stats["model_cache_entries"] == 3
            assert stats["total_cache_entries"] == 10
            assert stats["cache_hit_rate"] == 0.85

    @pytest.mark.asyncio
    async def test_provider_config_without_organization(
        self, discovery_service, mock_model_data, mock_cache
    ):
        """Test provider config without organization header"""
        config = ProviderConfig(
            name="test_provider",
            base_url="https://api.test-provider.com",
            api_key="test-api-key",
            organization=None,  # No organization
        )

        with patch(
            "src.core.model_discovery.get_unified_cache",
            return_value=mock_cache,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session

                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = mock_model_data
                mock_session.get.return_value.__aenter__.return_value = mock_response

                await discovery_service.discover_models(config)

                # Verify organization header is not included
                call_args = mock_session.get.call_args
                headers = call_args[1]["headers"]
                assert "OpenAI-Organization" not in headers

    @pytest.mark.asyncio
    async def test_service_context_manager(self, discovery_service):
        """Test async context manager"""
        with patch.object(discovery_service, "close") as mock_close:
            async with discovery_service:
                pass

            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_close(self, discovery_service):
        """Test service close method"""
        mock_client = AsyncMock()
        discovery_service.http_client = mock_client

        await discovery_service.close()

        mock_client.close.assert_called_once()


class TestModelDiscoveryIntegrationScenarios:
    """Integration tests for complex model discovery scenarios"""

    @pytest.fixture
    def discovery_service(self):
        """Create discovery service for integration tests"""
        return ModelDiscoveryService()

    @pytest.mark.asyncio
    async def test_multiple_providers_different_responses(self, discovery_service):
        """Test handling multiple providers with different response formats"""
        providers = [
            ProviderConfig("provider1", "https://api1.com", "key1"),
            ProviderConfig("provider2", "https://api2.com", "key2"),
        ]

        responses = [
            {
                "data": [
                    {
                        "id": "model1",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "prov1",
                    }
                ]
            },
            {
                "data": [
                    {
                        "id": "model2",
                        "object": "model",
                        "created": 1234567891,
                        "owned_by": "prov2",
                    },
                    {
                        "id": "model3",
                        "object": "model",
                        "created": 1234567892,
                        "owned_by": "prov2",
                    },
                ]
            },
        ]

        call_count = 0

        async def mock_get(url, headers=None):
            nonlocal call_count
            response = AsyncMock()
            response.status = 200
            response.json.return_value = responses[call_count]
            call_count += 1
            return response

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.side_effect = mock_get
            mock_session_class.return_value.__aenter__.return_value = mock_session

            with patch("src.core.model_discovery.get_unified_cache") as mock_cache_func:
                mock_cache = AsyncMock()
                mock_cache.get.return_value = None
                mock_cache.set.return_value = True
                mock_cache_func.return_value = mock_cache

                # Test first provider
                models1 = await discovery_service.discover_models(providers[0])
                assert len(models1) == 1
                assert models1[0].id == "model1"

                # Test second provider
                models2 = await discovery_service.discover_models(providers[1])
                assert len(models2) == 2
                assert models2[0].id == "model2"
                assert models2[1].id == "model3"

    @pytest.mark.asyncio
    async def test_concurrent_model_discovery(self, discovery_service):
        """Test concurrent model discovery calls"""
        provider = ProviderConfig("test", "https://api.test.com", "key")

        async def mock_get(url, headers=None):
            await asyncio.sleep(0.01)  # Simulate network delay
            response = AsyncMock()
            response.status = 200
            response.json.return_value = {
                "data": [
                    {
                        "id": "model1",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "test",
                    }
                ]
            }
            return response

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.side_effect = mock_get
            mock_session_class.return_value.__aenter__.return_value = mock_session

            with patch("src.core.model_discovery.get_unified_cache") as mock_cache_func:
                mock_cache = AsyncMock()
                mock_cache.get.return_value = None
                mock_cache.set.return_value = True
                mock_cache_func.return_value = mock_cache

                # Make concurrent calls
                tasks = [discovery_service.discover_models(provider) for _ in range(5)]

                results = await asyncio.gather(*tasks)

                # All should return the same result
                for result in results:
                    assert len(result) == 1
                    assert result[0].id == "model1"


if __name__ == "__main__":
    pytest.main([__file__])
