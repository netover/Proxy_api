"""Tests for provider discovery functionality."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Optional

from src.models.model_info import ModelInfo
from src.providers.openai import OpenAIProvider
from src.core.provider_factory import ProviderFactory, ProviderConfig, ProviderType
from src.core.model_cache import ModelCache
from src.core.model_discovery import ModelDiscoveryService
from src.core.exceptions import APIConnectionError


class TestOpenAIProviderDiscovery:
    """Test OpenAI provider discovery methods."""
    
    @pytest.fixture
    def openai_config(self):
        """Create test OpenAI provider config."""
        return ProviderConfig(
            name="test-openai",
            type=ProviderType.OPENAI,
            base_url="https://api.openai.com",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-4", "gpt-3.5-turbo"],
            priority=1,
            enabled=True
        )
    
    @pytest.fixture
    def mock_model_response(self):
        """Mock response for models endpoint."""
        return {
            "object": "list",
            "data": [
                {
                    "id": "gpt-4",
                    "object": "model",
                    "created": 1687882411,
                    "owned_by": "openai",
                    "permissions": [{"id": "modelperm-abc123", "object": "model_permission"}],
                    "root": "gpt-4",
                    "parent": None
                },
                {
                    "id": "gpt-3.5-turbo",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "openai",
                    "permissions": [{"id": "modelperm-def456", "object": "model_permission"}],
                    "root": "gpt-3.5-turbo",
                    "parent": None
                }
            ]
        }
    
    @pytest.fixture
    def mock_single_model_response(self):
        """Mock response for single model endpoint."""
        return {
            "id": "gpt-4",
            "object": "model",
            "created": 1687882411,
            "owned_by": "openai",
            "permissions": [{"id": "modelperm-abc123", "object": "model_permission"}],
            "root": "gpt-4",
            "parent": None
        }
    
    @pytest.mark.asyncio
    async def test_list_models_success(self, openai_config, mock_model_response):
        """Test successful model discovery."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(openai_config)
            
            # Mock the HTTP response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_model_response
            
            with patch.object(provider, 'make_request', return_value=mock_response):
                models = await provider.list_models()
                
                assert len(models) == 2
                assert models[0].id == "gpt-4"
                assert models[0].owned_by == "openai"
                assert models[1].id == "gpt-3.5-turbo"
                assert models[1].owned_by == "openai"
    
    @pytest.mark.asyncio
    async def test_list_models_with_cache(self, openai_config, mock_model_response):
        """Test model discovery with caching."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(openai_config)
            
            # Mock the HTTP response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_model_response
            
            with patch.object(provider, 'make_request', return_value=mock_response):
                # First call - should hit API
                models1 = await provider.list_models()
                assert len(models1) == 2
                
                # Second call - should use cache
                models2 = await provider.list_models()
                assert len(models2) == 2
                assert models1 == models2
    
    @pytest.mark.asyncio
    async def test_retrieve_model_success(self, openai_config, mock_single_model_response):
        """Test successful model retrieval."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(openai_config)
            
            # Mock the HTTP response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_single_model_response
            
            with patch.object(provider, 'make_request', return_value=mock_response):
                model = await provider.retrieve_model("gpt-4")
                
                assert model is not None
                assert model.id == "gpt-4"
                assert model.owned_by == "openai"
                assert model.created == 1687882411
    
    @pytest.mark.asyncio
    async def test_retrieve_model_not_found(self, openai_config):
        """Test model retrieval for non-existent model."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(openai_config)
            
            # Mock 404 response
            mock_response = AsyncMock()
            mock_response.status_code = 404
            
            with patch.object(provider, 'make_request', return_value=mock_response):
                model = await provider.retrieve_model("non-existent-model")
                assert model is None
    
    @pytest.mark.asyncio
    async def test_list_models_api_error(self, openai_config):
        """Test model discovery with API error."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(openai_config)
            
            # Mock error response
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = Exception("API Error")
            
            with patch.object(provider, 'make_request', return_value=mock_response):
                with pytest.raises(APIConnectionError):
                    await provider.list_models()
    
    @pytest.mark.asyncio
    async def test_retrieve_model_from_list_fallback(self, openai_config, mock_model_response):
        """Test retrieve_model using list_models as fallback."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(openai_config)
            
            # Mock list_models response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_model_response
            
            with patch.object(provider, 'make_request', return_value=mock_response):
                model = await provider.retrieve_model("gpt-4")
                
                assert model is not None
                assert model.id == "gpt-4"
                assert model.owned_by == "openai"


class TestProviderFactoryDiscovery:
    """Test provider factory discovery support."""
    
    @pytest.fixture
    def factory(self):
        """Create test provider factory."""
        return ProviderFactory()
    
    @pytest.fixture
    def openai_config(self):
        """Create test OpenAI provider config."""
        return ProviderConfig(
            name="test-openai",
            type=ProviderType.OPENAI,
            base_url="https://api.openai.com",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-4", "gpt-3.5-turbo"],
            priority=1,
            enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_is_discovery_enabled(self, factory, openai_config):
        """Test discovery capability detection."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = await factory.create_provider(openai_config)
            factory._providers[openai_config.name] = provider
            
            assert factory.is_discovery_enabled("test-openai") is True
            assert factory.is_discovery_enabled("non-existent") is False
    
    @pytest.mark.asyncio
    async def test_discover_models(self, factory, openai_config):
        """Test factory model discovery."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = await factory.create_provider(openai_config)
            factory._providers[openai_config.name] = provider
            
            mock_models = [
                ModelInfo(
                    id="gpt-4",
                    created=1687882411,
                    owned_by="openai"
                ),
                ModelInfo(
                    id="gpt-3.5-turbo",
                    created=1677610602,
                    owned_by="openai"
                )
            ]
            
            with patch.object(provider, 'list_models', return_value=mock_models):
                models = await factory.discover_models("test-openai")
                
                assert len(models) == 2
                assert models[0].id == "gpt-4"
                assert models[1].id == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_retrieve_model(self, factory, openai_config):
        """Test factory model retrieval."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = await factory.create_provider(openai_config)
            factory._providers[openai_config.name] = provider
            
            mock_model = ModelInfo(
                id="gpt-4",
                created=1687882411,
                owned_by="openai"
            )
            
            with patch.object(provider, 'retrieve_model', return_value=mock_model):
                model = await factory.retrieve_model("test-openai", "gpt-4")
                
                assert model is not None
                assert model.id == "gpt-4"
                assert model.owned_by == "openai"
    
    @pytest.mark.asyncio
    async def test_get_discovery_enabled_providers(self, factory, openai_config):
        """Test getting discovery-enabled providers."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = await factory.create_provider(openai_config)
            factory._providers[openai_config.name] = provider
            
            enabled_providers = await factory.get_discovery_enabled_providers()
            
            assert "test-openai" in enabled_providers
    
    @pytest.mark.asyncio
    async def test_discover_models_provider_not_found(self, factory):
        """Test discovery with non-existent provider."""
        with pytest.raises(ValueError, match="Provider 'non-existent' not found"):
            await factory.discover_models("non-existent")
    
    @pytest.mark.asyncio
    async def test_discover_models_not_supported(self, factory):
        """Test discovery with provider that doesn't support it."""
        # Create a mock provider without discovery methods
        mock_provider = MagicMock()
        mock_provider.__class__.__name__ = "MockProvider"
        factory._providers["mock-provider"] = mock_provider
        
        assert factory.is_discovery_enabled("mock-provider") is False
        
        with pytest.raises(ValueError, match="doesn't support model discovery"):
            await factory.discover_models("mock-provider")


class TestModelCacheIntegration:
    """Test model cache integration with discovery."""
    
    @pytest.fixture
    def model_cache(self):
        """Create test model cache."""
        return ModelCache(ttl=60, max_size=100, persist=False)
    
    @pytest.mark.asyncio
    async def test_cache_model_storage(self, model_cache):
        """Test storing and retrieving models from cache."""
        models = [
            ModelInfo(
                id="test-model-1",
                created=1234567890,
                owned_by="test-org"
            ),
            ModelInfo(
                id="test-model-2",
                created=1234567891,
                owned_by="test-org"
            )
        ]
        
        # Store models
        model_cache.set_models("test-provider", "https://api.test.com", models)
        
        # Retrieve models
        cached_models = model_cache.get_models("test-provider", "https://api.test.com")
        
        assert cached_models is not None
        assert len(cached_models) == 2
        assert cached_models[0].id == "test-model-1"
        assert cached_models[1].id == "test-model-2"
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, model_cache):
        """Test cache invalidation."""
        models = [
            ModelInfo(
                id="test-model",
                created=1234567890,
                owned_by="test-org"
            )
        ]
        
        # Store models
        model_cache.set_models("test-provider", "https://api.test.com", models)
        
        # Verify cache exists
        assert model_cache.is_valid("test-provider", "https://api.test.com") is True
        
        # Invalidate cache
        invalidated = model_cache.invalidate("test-provider", "https://api.test.com")
        assert invalidated is True
        
        # Verify cache is gone
        assert model_cache.is_valid("test-provider", "https://api.test.com") is False
        assert model_cache.get_models("test-provider", "https://api.test.com") is None


class TestBackwardCompatibility:
    """Test backward compatibility with existing providers."""
    
    @pytest.fixture
    def legacy_provider_class(self):
        """Create a mock legacy provider without discovery."""
        class LegacyProvider:
            def __init__(self, config):
                self.config = config
                self.name = config.name
            
            async def create_completion(self, request):
                return {"choices": [{"message": {"content": "test"}}]}
            
            async def create_text_completion(self, request):
                return {"choices": [{"text": "test"}]}
            
            async def create_embeddings(self, request):
                return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        
        return LegacyProvider
    
    @pytest.mark.asyncio
    async def test_legacy_provider_compatibility(self, legacy_provider_class):
        """Test that legacy providers still work without discovery."""
        config = ProviderConfig(
            name="legacy-provider",
            type=ProviderType.OPENAI,
            base_url="https://api.test.com",
            api_key_env="TEST_API_KEY",
            models=["test-model"],
            priority=1,
            enabled=True
        )
        
        with patch.dict('os.environ', {'TEST_API_KEY': 'test-key'}):
            provider = legacy_provider_class(config)
            
            # Legacy providers should not have discovery methods
            assert not hasattr(provider, 'list_models')
            assert not hasattr(provider, 'retrieve_model')
            
            # But should still work for basic operations
            result = await provider.create_completion({"messages": [{"role": "user", "content": "test"}]})
            assert "choices" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])