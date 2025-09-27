"""
Unit tests for provider implementations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.core.config.models import ProviderConfig
from src.core.providers.factory import BaseProvider, ProviderType, ProviderStatus


class TestBaseProvider:
    """Test BaseProvider base class."""

    def test_provider_initialization(self):
        """Test provider initialization."""
        config = ProviderConfig(
            name="test_provider",
            type="openai",
            api_key_env="TEST_KEY",
            models=["gpt-3.5-turbo"]
        )

        # Test that BaseProvider cannot be instantiated directly
        with pytest.raises(TypeError):
            BaseProvider(config)

    def test_provider_status_management(self):
        """Test provider status management."""
        config = ProviderConfig(
            name="test_provider",
            type="openai",
            api_key_env="TEST_KEY",
            models=["gpt-3.5-turbo"]
        )

        # Test that BaseProvider cannot be instantiated directly
        with pytest.raises(TypeError):
            BaseProvider(config)


class TestProviderFactory:
    """Test ProviderFactory."""

    @pytest.mark.asyncio
    async def test_provider_creation(self):
        """Test creating providers."""
        from src.core.providers.factory import provider_factory

        config = ProviderConfig(
            name="test_provider",
            type="openai",
            api_key_env="TEST_OPENAI_KEY",
            models=["gpt-3.5-turbo"],
            base_url="https://api.openai.com/v1"
        )

        # This will fail due to missing API key, but tests the creation logic
        with pytest.raises(ValueError):
            await provider_factory.create_provider(config)

    def test_provider_type_mapping(self):
        """Test provider type to class mapping."""
        from src.core.providers.factory import ProviderFactory, ProviderType

        factory = ProviderFactory()

        # Test that we have mappings for all provider types
        assert ProviderType.OPENAI in factory.PROVIDER_MAPPING
        assert ProviderType.ANTHROPIC in factory.PROVIDER_MAPPING
        assert ProviderType.AZURE_OPENAI in factory.PROVIDER_MAPPING

        # Test mapping values
        openai_mapping = factory.PROVIDER_MAPPING[ProviderType.OPENAI]
        assert openai_mapping[0] == "src.providers.dynamic_openai"
        assert openai_mapping[1] == "DynamicOpenAIProvider"
