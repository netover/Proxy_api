import pytest
import json
import yaml
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from pydantic import ValidationError

from src.core.app_config import (
    ProviderConfig,
    CondensationConfig,
    AppConfig,
    get_config_paths,
    create_default_config,
    load_config,
    init_config,
)


class TestProviderConfig:
    """Test ProviderConfig class"""

    def test_valid_provider_config(self):
        """Test creating a valid ProviderConfig"""
        config = ProviderConfig(
            name="openai",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-3.5-turbo", "gpt-4"],
            enabled=True,
            priority=1,
            timeout=30,
            rate_limit=1000,
            retry_attempts=3,
            retry_delay=1.0,
        )
        assert config.name == "openai"
        assert config.type == "openai"
        assert config.enabled is True
        assert config.priority == 1

    def test_provider_config_defaults(self):
        """Test ProviderConfig default values"""
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1"],
        )
        assert config.enabled is True
        assert config.priority == 100
        assert config.timeout == 30
        assert config.rate_limit == 1000
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
        assert config.max_keepalive_connections == 100
        assert config.max_connections == 1000
        assert config.keepalive_expiry == 30.0

    def test_invalid_provider_type(self):
        """Test invalid provider type validation"""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(
                name="test",
                type="invalid_type",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
            )
        assert "Provider type must be one of" in str(exc_info.value)

    def test_empty_models_list(self):
        """Test empty models list validation"""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=[],
            )
        assert "List should have at least 1 item" in str(exc_info.value)

    def test_duplicate_models_removed(self):
        """Test that duplicate models are removed"""
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1", "model1", "model2"],
        )
        assert sorted(config.models) == sorted(["model1", "model2"])

    def test_priority_bounds(self):
        """Test priority field bounds"""
        # Valid priority
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1"],
            priority=50,
        )
        assert config.priority == 50

        # Invalid priority too low
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                priority=0,
            )

        # Invalid priority too high
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                priority=1001,
            )

    def test_timeout_bounds(self):
        """Test timeout field bounds"""
        # Valid timeout
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1"],
            timeout=60,
        )
        assert config.timeout == 60

        # Invalid timeout too low
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                timeout=0,
            )

        # Invalid timeout too high
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                timeout=301,
            )

    def test_rate_limit_bounds(self):
        """Test rate_limit field bounds"""
        # Valid rate limit
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1"],
            rate_limit=500,
        )
        assert config.rate_limit == 500

        # Invalid rate limit too low
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                rate_limit=0,
            )

    def test_retry_attempts_bounds(self):
        """Test retry_attempts field bounds"""
        # Valid retry attempts
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1"],
            retry_attempts=5,
        )
        assert config.retry_attempts == 5

        # Invalid retry attempts negative
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                retry_attempts=-1,
            )

        # Invalid retry attempts too high
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                retry_attempts=11,
            )

    def test_retry_delay_bounds(self):
        """Test retry_delay field bounds"""
        # Valid retry delay
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1"],
            retry_delay=2.5,
        )
        assert config.retry_delay == 2.5

        # Invalid retry delay too low
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                retry_delay=0.05,
            )

        # Invalid retry delay too high
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                retry_delay=61.0,
            )

    def test_connection_pool_bounds(self):
        """Test connection pool configuration bounds"""
        # Valid values
        config = ProviderConfig(
            name="test",
            type="openai",
            base_url="https://api.test.com",
            api_key_env="TEST_KEY",
            models=["model1"],
            max_keepalive_connections=50,
            max_connections=500,
            keepalive_expiry=15.0,
        )
        assert config.max_keepalive_connections == 50
        assert config.max_connections == 500
        assert config.keepalive_expiry == 15.0

        # Invalid max_keepalive_connections too low
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                max_keepalive_connections=0,
            )

        # Invalid max_connections too low
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                max_connections=0,
            )

        # Invalid keepalive_expiry too low
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                keepalive_expiry=0.5,
            )

        # Invalid keepalive_expiry too high
        with pytest.raises(ValidationError):
            ProviderConfig(
                name="test",
                type="openai",
                base_url="https://api.test.com",
                api_key_env="TEST_KEY",
                models=["model1"],
                keepalive_expiry=301.0,
            )


class TestCondensationConfig:
    """Test CondensationConfig class"""

    def test_valid_condensation_config(self):
        """Test creating a valid CondensationConfig"""
        config = CondensationConfig(
            max_tokens_default=256,
            error_keywords=[
                "context_length_exceeded",
                "maximum context length",
            ],
            adaptive_enabled=True,
            adaptive_factor=0.6,
            cache_ttl=200,
        )
        assert config.max_tokens_default == 256
        assert config.adaptive_enabled is True
        assert config.adaptive_factor == 0.6
        assert config.cache_ttl == 200

    def test_condensation_config_defaults(self):
        """Test CondensationConfig default values"""
        config = CondensationConfig()
        assert config.max_tokens_default == 512
        assert config.error_keywords == [
            "context_length_exceeded",
            "maximum context length",
        ]
        assert config.adaptive_enabled is True
        assert config.adaptive_factor == 0.5
        assert config.cache_ttl == 300

    def test_max_tokens_bounds(self):
        """Test max_tokens_default bounds"""
        # Valid value
        config = CondensationConfig(max_tokens_default=1024)
        assert config.max_tokens_default == 1024

        # Invalid too low
        with pytest.raises(ValidationError):
            CondensationConfig(max_tokens_default=0)

        # Invalid too high
        with pytest.raises(ValidationError):
            CondensationConfig(max_tokens_default=4097)

    def test_adaptive_factor_bounds(self):
        """Test adaptive_factor bounds"""
        # Valid value
        config = CondensationConfig(adaptive_factor=0.7)
        assert config.adaptive_factor == 0.7

        # Invalid too low
        with pytest.raises(ValidationError):
            CondensationConfig(adaptive_factor=0.05)

        # Invalid too high
        with pytest.raises(ValidationError):
            CondensationConfig(adaptive_factor=1.1)

    def test_cache_ttl_bounds(self):
        """Test cache_ttl bounds"""
        # Valid value
        config = CondensationConfig(cache_ttl=500)
        assert config.cache_ttl == 500

        # Invalid too low
        with pytest.raises(ValidationError):
            CondensationConfig(cache_ttl=50)

        # Invalid too high
        with pytest.raises(ValidationError):
            CondensationConfig(cache_ttl=3601)


class TestAppConfig:
    """Test AppConfig class"""

    def test_valid_app_config(self):
        """Test creating a valid AppConfig"""
        provider_config = ProviderConfig(
            name="openai",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-3.5-turbo"],
        )
        config = AppConfig(providers=[provider_config])
        assert len(config.providers) == 1
        assert config.providers[0].name == "openai"

    def test_app_config_with_condensation(self):
        """Test AppConfig with custom condensation config"""
        provider_config = ProviderConfig(
            name="openai",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-3.5-turbo"],
        )
        condensation_config = CondensationConfig(max_tokens_default=256)
        config = AppConfig(
            providers=[provider_config], condensation=condensation_config
        )
        assert config.condensation.max_tokens_default == 256

    def test_empty_providers_validation(self):
        """Test validation for empty providers list"""
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(providers=[])
        assert "List should have at least 1 item" in str(exc_info.value)

    def test_duplicate_provider_names(self):
        """Test validation for duplicate provider names"""
        provider1 = ProviderConfig(
            name="openai",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-3.5-turbo"],
        )
        provider2 = ProviderConfig(
            name="openai",  # Duplicate name
            type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_API_KEY",
            models=["claude-3"],
        )
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(providers=[provider1, provider2])
        assert "Provider names must be unique" in str(exc_info.value)

    def test_duplicate_provider_priorities(self):
        """Test validation for duplicate provider priorities"""
        provider1 = ProviderConfig(
            name="openai",
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-3.5-turbo"],
            priority=1,
        )
        provider2 = ProviderConfig(
            name="anthropic",
            type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_API_KEY",
            models=["claude-3"],
            priority=1,  # Duplicate priority
        )
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(providers=[provider1, provider2])
        assert "Provider priorities must be unique" in str(exc_info.value)


class TestConfigFunctions:
    """Test configuration utility functions"""

    @patch("sys.frozen", False, create=True)
    @patch("src.core.app_config.Path")
    def test_get_config_paths_development(self, mock_path_class):
        """Test get_config_paths in development mode"""
        # Configure the mock to simulate path operations
        mock_base_path = mock_path_class.return_value.parent.parent.parent
        mock_base_path.__truediv__.side_effect = lambda x: Path(
            f"/mock/base/{x}"
        )

        paths = get_config_paths()

        expected_yaml_path = Path("/mock/base/config.yaml")
        expected_json_path = Path("/mock/base/config.json")
        assert paths[0] == expected_yaml_path
        assert paths[1] == expected_json_path
        assert paths[2] == expected_yaml_path
        assert paths[3] == expected_json_path

    @patch("sys.frozen", True, create=True)
    @patch("sys._MEIPASS", "/frozen/path", create=True)
    @patch("sys.executable", "/exec/path/app.exe")
    @patch("src.core.app_config.Path")
    def test_get_config_paths_frozen(self, mock_path_class):
        """Test get_config_paths in frozen/executable mode"""
        from unittest.mock import MagicMock

        # Configure the mock to simulate path operations
        def path_side_effect(p):
            if p == "/frozen/path":
                return Path("/frozen/path")
            elif p == "/exec/path/app.exe":
                mock_exe_path = MagicMock()
                mock_exe_path.parent = Path("/exec/path")
                return mock_exe_path
            return Path(p)

        mock_path_class.side_effect = path_side_effect

        paths = get_config_paths()

        # Should use _MEIPASS for bundle and executable parent for external
        assert paths[0] == Path("/frozen/path/config.yaml")
        assert paths[1] == Path("/frozen/path/config.json")
        assert paths[2] == Path("/exec/path/config.yaml")
        assert paths[3] == Path("/exec/path/config.json")

    def test_create_default_config_yaml(self):
        """Test create_default_config with YAML format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"

            result = create_default_config(config_path)

            assert config_path.exists()
            assert "providers" in result
            assert len(result["providers"]) == 1
            assert result["providers"][0]["name"] == "openai"

            # Verify file content
            with open(config_path, "r") as f:
                loaded_config = yaml.safe_load(f)
            assert loaded_config == result

    def test_create_default_config_json(self):
        """Test create_default_config with JSON format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"

            result = create_default_config(config_path)

            assert config_path.exists()
            assert "providers" in result

            # Verify file content
            with open(config_path, "r") as f:
                loaded_config = json.load(f)
            assert loaded_config == result

    @patch("src.core.app_config.logger")
    def test_create_default_config_error(self, mock_logger):
        """Test create_default_config error handling"""
        # Try to create in a directory that doesn't allow writing
        config_path = Path("/nonexistent/directory/config.yaml")

        result = create_default_config(config_path)

        # Should still return default config even if file creation fails
        assert "providers" in result
        mock_logger.error.assert_called_once()

    @patch("src.core.app_config.get_config_paths")
    @patch("src.core.app_config._try_load_config")
    @patch("src.core.app_config.create_default_config")
    def test_load_config_fallback_chain(
        self, mock_create_default, mock_try_load, mock_get_paths
    ):
        """Test load_config fallback chain"""
        # Mock paths
        bundle_yaml = Path("/bundle/config.yaml")
        bundle_json = Path("/bundle/config.json")
        external_yaml = Path("/external/config.yaml")
        external_json = Path("/external/config.json")
        mock_get_paths.return_value = (
            bundle_yaml,
            bundle_json,
            external_yaml,
            external_json,
        )

        # Mock try_load_config to return None for all attempts
        mock_try_load.return_value = None

        # Mock create_default_config
        default_config = {"providers": []}
        mock_create_default.return_value = default_config

        with patch("src.core.app_config.AppConfig") as mock_app_config:
            mock_app_config.return_value = "parsed_config"

            result = load_config()

            # Should try external first, then bundled, then create default
            assert mock_try_load.call_count == 2  # external + bundled
            mock_create_default.assert_called_once()
            mock_app_config.assert_called_once_with(**default_config)
            assert result == "parsed_config"

    @patch("src.core.app_config.load_config")
    def test_init_config(self, mock_load_config):
        """Test init_config function"""
        mock_load_config.return_value = "test_config"

        result = init_config()

        assert result == "test_config"
        mock_load_config.assert_called_once()


class TestConfigLoading:
    """Test configuration loading from files"""

    def test_load_config_from_yaml_file(self):
        """Test loading config from YAML file"""
        config_data = {
            "providers": [
                {
                    "name": "openai",
                    "type": "openai",
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "OPENAI_API_KEY",
                    "models": ["gpt-3.5-turbo"],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_data, f)

            with patch(
                "src.core.app_config.get_config_paths",
                return_value=(config_path, None, config_path, None),
            ):
                with patch(
                    "src.core.app_config._try_load_config"
                ) as mock_try_load:
                    mock_try_load.return_value = AppConfig(**config_data)

                    result = load_config()

                    mock_try_load.assert_called_once_with(
                        config_path, None, "external"
                    )
                    assert isinstance(result, AppConfig)

    def test_load_config_from_json_file(self):
        """Test loading config from JSON file"""
        config_data = {
            "providers": [
                {
                    "name": "anthropic",
                    "type": "anthropic",
                    "base_url": "https://api.anthropic.com",
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "models": ["claude-3"],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            with patch(
                "src.core.app_config.get_config_paths",
                return_value=(None, config_path, None, config_path),
            ):
                with patch(
                    "src.core.app_config._try_load_config"
                ) as mock_try_load:
                    mock_try_load.return_value = AppConfig(**config_data)

                    result = load_config()

                    mock_try_load.assert_called_once_with(
                        None, config_path, "external"
                    )
                    assert isinstance(result, AppConfig)
