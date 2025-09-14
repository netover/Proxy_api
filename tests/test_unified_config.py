import pytest
import os
from unittest.mock import patch
from pathlib import Path
import yaml
import asyncio

from src.core.optimized_config import OptimizedConfigLoader

@pytest.fixture
def config_loader():
    """Fixture to create an instance of OptimizedConfigLoader for tests."""
    # Using a dummy path, as we will mock the file reading
    return OptimizedConfigLoader(config_path=Path("dummy_config.yaml"), enable_watching=False)

class TestConfigSubstitution:
    """Tests for environment variable substitution in configuration."""

    def test_simple_substitution(self, config_loader):
        """Test basic substitution of an environment variable."""
        test_data = {"key": "value", "url": "${TEST_URL}"}
        expected_data = {"key": "value", "url": "https://example.com"}

        with patch.dict(os.environ, {"TEST_URL": "https://example.com"}):
            result = config_loader._substitute_env_vars(test_data)
            assert result == expected_data

    def test_nested_substitution(self, config_loader):
        """Test substitution in a nested dictionary."""
        test_data = {
            "level1": {
                "level2": {
                    "token": "Bearer ${API_TOKEN}"
                }
            }
        }
        expected_data = {
            "level1": {
                "level2": {
                    "token": "Bearer my-secret-token"
                }
            }
        }

        with patch.dict(os.environ, {"API_TOKEN": "my-secret-token"}):
            result = config_loader._substitute_env_vars(test_data)
            assert result == expected_data

    def test_list_substitution(self, config_loader):
        """Test substitution in a list."""
        test_data = ["${VAR1}", "static_value", "${VAR2}"]
        expected_data = ["value1", "static_value", "value2"]

        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}):
            result = config_loader._substitute_env_vars(test_data)
            assert result == expected_data

    def test_missing_env_var(self, config_loader):
        """Test that a missing environment variable is replaced with an empty string."""
        test_data = {"key": "${MISSING_VAR}"}
        expected_data = {"key": ""}

        # Ensure the variable is not set
        if "MISSING_VAR" in os.environ:
            del os.environ["MISSING_VAR"]

        result = config_loader._substitute_env_vars(test_data)
        assert result == expected_data

    def test_no_substitution(self, config_loader):
        """Test that strings without the placeholder pattern are not modified."""
        test_data = {"key": "this is a normal string", "another_key": "value"}

        result = config_loader._substitute_env_vars(test_data)
        assert result == test_data

    def test_mixed_string_substitution(self, config_loader):
        """Test substitution in a string with other text."""
        test_data = {"connection_string": "user=${DB_USER};password=${DB_PASS};"}
        expected_data = {"connection_string": "user=admin;password=secret;"}

        with patch.dict(os.environ, {"DB_USER": "admin", "DB_PASS": "secret"}):
            result = config_loader._substitute_env_vars(test_data)
            assert result == expected_data

    def test_integration_with_sync_load(self, tmp_path):
        """Test that the substitution is correctly applied during the file loading process."""
        config_content = """
        database:
          url: "postgresql://${DB_HOST}:${DB_PORT}/mydb"
        api_key: "${API_KEY}"
        endpoints:
          - "/api/v1"
          - "/api/${API_VERSION}"
        """
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        loader = OptimizedConfigLoader(config_path=config_file, enable_watching=False)

        env_vars = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "API_KEY": "my-api-key",
            "API_VERSION": "v2"
        }

        with patch.dict(os.environ, env_vars):
            # _sync_load is not directly async, it's called within an executor
            # We can access the internal data after calling the async wrapper
            loop = asyncio.get_event_loop()
            loaded_config = loop.run_until_complete(loader._load_file_async(config_file))

        assert loaded_config["database"]["url"] == "postgresql://localhost:5432/mydb"
        assert loaded_config["api_key"] == "my-api-key"
        assert loaded_config["endpoints"] == ["/api/v1", "/api/v2"]
