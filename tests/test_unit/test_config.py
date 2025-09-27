"""
Unit tests for configuration management.
"""

import pytest
import tempfile
import yaml
import os
from src.core.config.models import UnifiedConfig, ProviderConfig


class TestUnifiedConfig:
    """Test UnifiedConfig model."""

    def test_config_creation(self):
        """Test basic config creation."""
        config = UnifiedConfig(
            app={"name": "Test API", "version": "1.0.0"},
            providers=[
                ProviderConfig(
                    name="test_openai",
                    type="openai",
                    api_key_env="TEST_KEY",
                    models=["gpt-3.5-turbo"]
                )
            ]
        )

        assert config.app.name == "Test API"
        assert config.app.version == "1.0.0"
        assert len(config.providers) == 1
        assert config.providers[0].name == "test_openai"

    def test_config_validation(self):
        """Test config validation."""
        # Test that ProviderConfig accepts valid data
        config = ProviderConfig(
            name="test_provider",
            type="openai",
            api_key_env="TEST_KEY",
            models=["gpt-3.5-turbo"]
        )
        assert config.name == "test_provider"
        assert config.type == "openai"

    def test_config_defaults(self):
        """Test default values."""
        config = UnifiedConfig()

        assert config.app.name == "LLM Proxy API"
        assert config.app.version == "2.0.0"
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000
        assert config.caching.enabled is True


class TestConfigManager:
    """Test configuration manager."""

    def test_config_loading(self, temp_config_file):
        """Test loading config from file."""
        from src.core.unified_config import config_manager

        config_manager.load_config(temp_config_file)
        config = config_manager.get_config()

        assert config.app.name == "Test API"
        assert len(config.providers) == 1

    def test_config_file_not_found(self):
        """Test loading non-existent config file."""
        from src.core.unified_config import config_manager

        with pytest.raises(FileNotFoundError):
            config_manager.load_config("nonexistent.yaml")
