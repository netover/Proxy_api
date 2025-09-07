import pytest
from pathlib import Path
from src.core.app_config import ProviderConfig, AppConfig, load_config


class TestProviderConfig:
    """Test ProviderConfig validation"""

    def test_valid_config(self):
        """Test valid provider configuration"""
        config = ProviderConfig(
            name="test_provider",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_API_KEY",
            models=["gpt-4", "gpt-3.5-turbo"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000
        )
        assert config.name == "test_provider"
        assert config.type == "openai"

    def test_invalid_priority(self):
        """Test invalid priority validation"""
        with pytest.raises(ValueError):
            ProviderConfig(
                name="test_provider",
                type="openai",
                base_url="https://api.openai.com/v1",
                api_key_env="TEST_API_KEY",
                models=["gpt-4"],
                priority=0  # Invalid: must be >= 1
            )

    def test_invalid_provider_type(self):
        """Test invalid provider type validation"""
        with pytest.raises(ValueError):
            ProviderConfig(
                name="test_provider",
                type="invalid_type",
                base_url="https://api.example.com",
                api_key_env="TEST_API_KEY",
                models=["model1"]
            )

    def test_empty_models(self):
        """Test empty models list validation"""
        with pytest.raises(ValueError):
            ProviderConfig(
                name="test_provider",
                type="openai",
                base_url="https://api.openai.com/v1",
                api_key_env="TEST_API_KEY",
                models=[]  # Invalid: must have at least one model
            )


class TestAppConfig:
    """Test AppConfig validation"""

    def test_valid_app_config(self):
        """Test valid application configuration"""
        provider = ProviderConfig(
            name="test_provider",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"]
        )

        app_config = AppConfig(providers=[provider])
        assert len(app_config.providers) == 1
        assert app_config.providers[0].name == "test_provider"

    def test_duplicate_provider_names(self):
        """Test duplicate provider names validation"""
        provider1 = ProviderConfig(
            name="duplicate_name",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"]
        )
        provider2 = ProviderConfig(
            name="duplicate_name",  # Duplicate name
            type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="TEST_API_KEY2",
            models=["claude-3"]
        )

        with pytest.raises(ValueError):
            AppConfig(providers=[provider1, provider2])

    def test_duplicate_priorities(self):
        """Test duplicate priorities validation"""
        provider1 = ProviderConfig(
            name="provider1",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="TEST_API_KEY",
            models=["gpt-4"],
            priority=1
        )
        provider2 = ProviderConfig(
            name="provider2",
            type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="TEST_API_KEY2",
            models=["claude-3"],
            priority=1  # Duplicate priority
        )

        with pytest.raises(ValueError):
            AppConfig(providers=[provider1, provider2])

    def test_empty_providers(self):
        """Test empty providers list validation"""
        with pytest.raises(ValueError):
            AppConfig(providers=[])


class TestConfigLoading:
    """Test configuration file loading"""

    def test_load_valid_config(self, tmp_path):
        """Test loading valid configuration file"""
        config_content = """
providers:
  - name: "test_openai"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    models:
      - "gpt-4"
      - "gpt-3.5-turbo"
    enabled: true
    priority: 1
    timeout: 30
    rate_limit: 1000
"""

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)

        config = load_config(config_file)
        assert len(config.providers) == 1
        assert config.providers[0].name == "test_openai"
        assert config.providers[0].type == "openai"

    def test_load_missing_config_file(self):
        """Test loading missing configuration file"""
        with pytest.raises(FileNotFoundError):
            load_config(Path("nonexistent_config.yaml"))
