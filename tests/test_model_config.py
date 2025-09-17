import pytest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

# Import the modules to test
from src.core.model_config import (
    ModelSelection,
    ModelConfigManager,
)
from src.services.model_config_service import (
    ModelConfigService,
)
from src.core.exceptions import ValidationError


class TestModelSelection:
    """Test the ModelSelection class"""

    def test_model_selection_creation(self):
        """Test basic ModelSelection creation"""
        selection = ModelSelection(
            provider_name="test_provider",
            model_name="test_model",
            editable=True,
        )

        assert selection.provider_name == "test_provider"
        assert selection.model_name == "test_model"
        assert selection.editable is True
        assert isinstance(selection.last_updated, datetime)

    def test_model_selection_serialization(self):
        """Test ModelSelection JSON serialization"""
        selection = ModelSelection(
            provider_name="test_provider",
            model_name="test_model",
            editable=False,
        )

        # Test JSON serialization
        json_str = selection.json()
        assert "test_provider" in json_str
        assert "test_model" in json_str
        assert "editable" in json_str


class TestModelConfigManager:
    """Test the ModelConfigManager class"""

    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.manager = ModelConfigManager(self.config_dir)

    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test manager initialization"""
        assert self.manager.config_dir.exists()
        assert self.manager.config_file.exists() is False  # Should not exist initially

    def test_set_and_get_model_selection(self):
        """Test setting and getting model selections"""
        selection = self.manager.set_model_selection("provider1", "model1")

        assert selection.provider_name == "provider1"
        assert selection.model_name == "model1"
        assert selection.editable is True

        retrieved = self.manager.get_model_selection("provider1")
        assert retrieved is not None
        assert retrieved.model_name == "model1"

    def test_update_model_selection(self):
        """Test updating existing model selections"""
        # Set initial selection
        self.manager.set_model_selection("provider1", "model1")

        # Update the selection
        updated = self.manager.update_model_selection("provider1", "model2")
        assert updated is not None
        assert updated.model_name == "model2"

        # Verify update
        retrieved = self.manager.get_model_selection("provider1")
        assert retrieved.model_name == "model2"

    def test_update_non_editable_selection(self):
        """Test updating non-editable selections"""
        # Set non-editable selection
        self.manager.set_model_selection("provider1", "model1", editable=False)

        # Attempt to update
        updated = self.manager.update_model_selection("provider1", "model2")
        assert updated is None

        # Verify original selection remains
        retrieved = self.manager.get_model_selection("provider1")
        assert retrieved.model_name == "model1"

    def test_remove_model_selection(self):
        """Test removing model selections"""
        self.manager.set_model_selection("provider1", "model1")

        # Remove selection
        success = self.manager.remove_model_selection("provider1")
        assert success is True

        # Verify removal
        retrieved = self.manager.get_model_selection("provider1")
        assert retrieved is None

    def test_remove_non_editable_selection(self):
        """Test removing non-editable selections"""
        self.manager.set_model_selection("provider1", "model1", editable=False)

        # Attempt to remove
        success = self.manager.remove_model_selection("provider1")
        assert success is False

    def test_get_all_selections(self):
        """Test getting all model selections"""
        self.manager.set_model_selection("provider1", "model1")
        self.manager.set_model_selection("provider2", "model2")

        selections = self.manager.get_all_selections()
        assert len(selections) == 2
        assert selections["provider1"].model_name == "model1"
        assert selections["provider2"].model_name == "model2"

    def test_get_editable_selections(self):
        """Test getting only editable selections"""
        self.manager.set_model_selection("provider1", "model1", editable=True)
        self.manager.set_model_selection("provider2", "model2", editable=False)

        editable = self.manager.get_editable_selections()
        assert len(editable) == 1
        assert "provider1" in editable
        assert "provider2" not in editable

    def test_clear_all_selections(self):
        """Test clearing all selections"""
        self.manager.set_model_selection("provider1", "model1", editable=True)
        self.manager.set_model_selection("provider2", "model2", editable=False)

        # Clear only editable
        cleared = self.manager.clear_all_selections(force=False)
        assert cleared == 1

        remaining = self.manager.get_all_selections()
        assert len(remaining) == 1
        assert "provider2" in remaining

    def test_clear_all_selections_force(self):
        """Test force clearing all selections"""
        self.manager.set_model_selection("provider1", "model1", editable=True)
        self.manager.set_model_selection("provider2", "model2", editable=False)

        # Clear all including non-editable
        cleared = self.manager.clear_all_selections(force=True)
        assert cleared == 2

        remaining = self.manager.get_all_selections()
        assert len(remaining) == 0

    def test_persistence(self):
        """Test that selections persist across instances"""
        self.manager.set_model_selection("provider1", "model1")

        # Create new manager instance
        new_manager = ModelConfigManager(self.config_dir)
        retrieved = new_manager.get_model_selection("provider1")

        assert retrieved is not None
        assert retrieved.model_name == "model1"

    def test_legacy_format_compatibility(self):
        """Test compatibility with legacy JSON format"""
        # Create legacy format file
        legacy_data = {"provider1": "model1", "provider2": "model2"}

        with open(self.manager.config_file, "w") as f:
            json.dump(legacy_data, f)

        # Create new manager to load legacy format
        new_manager = ModelConfigManager(self.config_dir)
        selections = new_manager.get_all_selections()

        assert len(selections) == 2
        assert selections["provider1"].model_name == "model1"
        assert selections["provider1"].editable is True

    def test_corrupted_file_handling(self):
        """Test handling of corrupted configuration files"""
        # Create corrupted file
        with open(self.manager.config_file, "w") as f:
            f.write("invalid json")

        # Should handle gracefully and start fresh
        new_manager = ModelConfigManager(self.config_dir)
        selections = new_manager.get_all_selections()
        assert len(selections) == 0

    def test_atomic_update_context_manager(self):
        """Test atomic updates using context manager"""
        self.manager.set_model_selection("provider1", "model1")

        try:
            with self.manager.atomic_update() as mgr:
                mgr.set_model_selection("provider1", "model2")
                mgr.set_model_selection("provider2", "model3")
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Verify no changes were made due to exception
        selections = self.manager.get_all_selections()
        assert len(selections) == 1
        assert selections["provider1"].model_name == "model1"


class TestModelConfigService:
    """Test the ModelConfigService class"""

    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"

        # Create mock config
        self.mock_config = MagicMock()
        self.mock_provider = MagicMock()
        self.mock_provider.name = "test_provider"
        self.mock_provider.models = ["model1", "model2", "model3"]

        self.mock_config.providers = [self.mock_provider]
        self.mock_config_manager = MagicMock()
        self.mock_config_manager.load_config.return_value = self.mock_config
        self.mock_config_manager.get_provider_by_name.return_value = self.mock_provider
        self.mock_config_manager.get_available_models.return_value = [
            "model1",
            "model2",
            "model3",
        ]
        self.mock_config_manager.get_model_selection.return_value = (
            "model1"  # Mock return value
        )

        # Create service with mocked dependencies
        self.service = ModelConfigService()
        self.service._config_manager = self.mock_config_manager

        # Create fresh model manager
        self.model_manager = ModelConfigManager(self.config_dir)
        self.service._model_manager = self.model_manager

    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_model_selection(self):
        """Test getting model selection"""
        self.model_manager.set_model_selection("test_provider", "model1")

        result = self.service.get_model_selection("test_provider")
        assert result == "model1"

    def test_get_model_selection_nonexistent_provider(self):
        """Test getting model selection for non-existent provider"""
        self.mock_config_manager.get_provider_by_name.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            self.service.get_model_selection("nonexistent")
        assert "not found" in str(exc_info.value)

    def test_set_model_selection(self):
        """Test setting model selection"""
        result = self.service.set_model_selection("test_provider", "model1")

        assert result["success"] is True
        assert result["provider"] == "test_provider"
        assert result["model"] == "model1"

    def test_set_model_selection_invalid_provider(self):
        """Test setting model selection for invalid provider"""
        self.mock_config_manager.get_provider_by_name.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            self.service.set_model_selection("invalid", "model1")
        assert "not found" in str(exc_info.value)

    def test_set_model_selection_invalid_model(self):
        """Test setting model selection for invalid model"""
        with pytest.raises(ValidationError) as exc_info:
            self.service.set_model_selection("test_provider", "invalid_model")
        assert "not supported" in str(exc_info.value)

    def test_update_model_selection(self):
        """Test updating model selection"""
        self.model_manager.set_model_selection("test_provider", "model1")

        result = self.service.update_model_selection("test_provider", "model2")
        assert result["success"] is True
        assert result["model"] == "model2"

    def test_update_nonexistent_selection(self):
        """Test updating non-existent selection"""
        with pytest.raises(ValidationError) as exc_info:
            self.service.update_model_selection("test_provider", "model1")
        assert "No model selection exists" in str(exc_info.value)

    def test_update_non_editable_selection(self):
        """Test updating non-editable selection"""
        self.model_manager.set_model_selection(
            "test_provider", "model1", editable=False
        )

        with pytest.raises(ValidationError) as exc_info:
            self.service.update_model_selection("test_provider", "model2")
        assert "not editable" in str(exc_info.value)

    def test_remove_model_selection(self):
        """Test removing model selection"""
        self.model_manager.set_model_selection("test_provider", "model1")

        result = self.service.remove_model_selection("test_provider")
        assert result["success"] is True

    def test_remove_nonexistent_selection(self):
        """Test removing non-existent selection"""
        result = self.service.remove_model_selection("test_provider")
        assert result["success"] is False

    def test_get_provider_model_info(self):
        """Test getting provider model information"""
        self.model_manager.set_model_selection("test_provider", "model1")

        info = self.service.get_provider_model_info("test_provider")

        assert info["provider"] == "test_provider"
        assert info["selected_model"] == "model1"
        assert info["available_models"] == ["model1", "model2", "model3"]
        assert info["has_selection"] is True
        assert info["model_count"] == 3

    def test_get_all_providers_model_info(self):
        """Test getting model info for all providers"""
        info_list = self.service.get_all_providers_model_info()

        assert len(info_list) == 1
        assert info_list[0]["provider"] == "test_provider"

    def test_validate_model_selection(self):
        """Test model selection validation"""
        result = self.service.validate_model_selection("test_provider", "model1")

        assert result["valid"] is True
        assert result["provider_exists"] is True
        assert result["model_supported"] is True
        assert len(result["errors"]) == 0

    def test_validate_invalid_model_selection(self):
        """Test validation of invalid model selection"""
        result = self.service.validate_model_selection("test_provider", "invalid_model")

        assert result["valid"] is False
        assert result["provider_exists"] is True
        assert result["model_supported"] is False
        assert len(result["errors"]) > 0

    def test_bulk_set_model_selections(self):
        """Test bulk setting model selections"""
        selections = {"test_provider": "model1"}

        result = self.service.bulk_set_model_selections(selections)

        assert result["success"] is True
        assert result["total"] == 1
        assert result["successful"] == 1
        assert result["failed"] == 0

    def test_bulk_set_with_invalid_selections(self):
        """Test bulk setting with some invalid selections"""
        # Mock the config manager to return None for invalid provider
        self.mock_config_manager.get_provider_by_name.side_effect = lambda name: (
            self.mock_provider if name == "test_provider" else None
        )

        selections = {"test_provider": "model1", "invalid_provider": "model1"}

        result = self.service.bulk_set_model_selections(selections)

        assert result["success"] is False
        assert result["total"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1

    def test_clear_all_model_selections(self):
        """Test clearing all model selections"""
        self.model_manager.set_model_selection("test_provider", "model1")

        result = self.service.clear_all_model_selections()
        assert result["success"] is True
        assert result["cleared_count"] == 1

    def test_reload_model_selections(self):
        """Test reloading model selections"""
        self.model_manager.set_model_selection("test_provider", "model1")

        result = self.service.reload_model_selections()
        assert result["success"] is True
        assert result["loaded_count"] == 1


class TestIntegration:
    """Integration tests with real configuration"""

    def setup_method(self):
        """Setup for integration tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"

        # Create a real config file with required sections
        config_content = """
app:
  name: "Test Proxy API"
  version: "1.0.0"
  environment: "test"

server:
  host: "127.0.0.1"
  port: 8000
  debug: true

auth:
  api_keys:
    - "test-key"

settings:
  api_keys: ["test-key"]
  debug: true

providers:
  - name: openai_test
    type: openai
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY
    models:
      - gpt-3.5-turbo
      - gpt-4
    priority: 1
  - name: anthropic_test
    type: anthropic
    base_url: https://api.anthropic.com/v1
    api_key_env: ANTHROPIC_API_KEY
    models:
      - claude-3-haiku
      - claude-3-sonnet
    priority: 2
"""

        config_file = Path(self.temp_dir) / "config.yaml"
        with open(config_file, "w") as f:
            f.write(config_content)

        # Set environment variables
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        # Initialize with test config
        from src.core.unified_config import ConfigManager

        self.config_manager = ConfigManager(config_file)
        # Load the config explicitly
        config = self.config_manager.load_config()
        print(f"DEBUG: Loaded config with {len(config.providers)} providers")
        for provider in config.providers:
            print(f"DEBUG: Provider: {provider.name}")
        self.model_manager = ModelConfigManager(self.config_dir)
        self.service = ModelConfigService()
        # Override the service's config manager with our test instance
        self.service._config_manager = self.config_manager
        # Override the service's model manager with our test instance
        self.service._model_manager = self.model_manager

        # Update the test to use the correct provider names
        self.openai_provider = config.providers[0].name
        self.anthropic_provider = config.providers[1].name

    def teardown_method(self):
        """Cleanup after integration tests"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

    def test_end_to_end_model_selection(self):
        """Test complete end-to-end model selection workflow"""
        # Set model selections using the actual provider names from config
        result1 = self.service.set_model_selection(self.openai_provider, "gpt-4")
        assert result1["success"] is True

        result2 = self.service.set_model_selection(
            self.anthropic_provider, "claude-3-sonnet"
        )
        assert result2["success"] is True

        # Verify selections
        selections = self.service.get_all_model_selections()
        assert selections[self.openai_provider]["model_name"] == "gpt-4"
        assert selections[self.anthropic_provider]["model_name"] == "claude-3-sonnet"

        # Test persistence
        new_service = ModelConfigService()
        new_service._config_manager = self.config_manager
        new_service._model_manager = ModelConfigManager(self.config_dir)

        persisted_selections = new_service.get_all_model_selections()
        assert persisted_selections[self.openai_provider]["model_name"] == "gpt-4"
        assert (
            persisted_selections[self.anthropic_provider]["model_name"]
            == "claude-3-sonnet"
        )

    def test_hot_reload(self):
        """Test hot-reloading of model selections"""
        # Set initial selection
        self.service.set_model_selection(self.openai_provider, "gpt-3.5-turbo")

        # Verify initial selection
        selection = self.service.get_model_selection(self.openai_provider)
        assert selection == "gpt-3.5-turbo"

        # Reload (should maintain the same selection since no external changes)
        result = self.service.reload_model_selections()
        assert result["success"] is True

        # Verify selection is maintained after reload
        selection = self.service.get_model_selection(self.openai_provider)
        assert selection == "gpt-3.5-turbo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
