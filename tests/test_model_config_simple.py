import pytest
import json
import tempfile
import os
from pathlib import Path

# Import the modules to test
from src.core.model_config import ModelSelection, ModelConfigManager

class TestModelConfigSimple:
    """Simple tests for model configuration without complex dependencies"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.manager = ModelConfigManager(self.config_dir)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_model_selection_creation(self):
        """Test basic ModelSelection creation"""
        selection = ModelSelection(
            provider_name="test_provider",
            model_name="test_model",
            editable=True
        )
        
        assert selection.provider_name == "test_provider"
        assert selection.model_name == "test_model"
        assert selection.editable is True
    
    def test_set_and_get_model_selection(self):
        """Test setting and getting model selections"""
        selection = self.manager.set_model_selection("provider1", "model1")
        
        assert selection.provider_name == "provider1"
        assert selection.model_name == "model1"
        
        retrieved = self.manager.get_model_selection("provider1")
        assert retrieved is not None
        assert retrieved.model_name == "model1"
    
    def test_persistence(self):
        """Test that selections persist across instances"""
        self.manager.set_model_selection("provider1", "model1")
        
        # Create new manager instance
        new_manager = ModelConfigManager(self.config_dir)
        retrieved = new_manager.get_model_selection("provider1")
        
        assert retrieved is not None
        assert retrieved.model_name == "model1"
    
    def test_clear_all_selections(self):
        """Test clearing all model selections"""
        self.manager.set_model_selection("provider1", "model1", editable=True)
        self.manager.set_model_selection("provider2", "model2", editable=False)
        
        # Clear only editable
        cleared = self.manager.clear_all_selections(force=False)
        assert cleared == 1
        
        remaining = self.manager.get_all_selections()
        assert len(remaining) == 1
        assert "provider2" in remaining
    
    def test_legacy_format_compatibility(self):
        """Test compatibility with legacy JSON format"""
        # Create legacy format file
        legacy_data = {
            "provider1": "model1",
            "provider2": "model2"
        }
        
        with open(self.manager.config_file, 'w') as f:
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
        with open(self.manager.config_file, 'w') as f:
            f.write("invalid json")
        
        # Should handle gracefully and start fresh
        new_manager = ModelConfigManager(self.config_dir)
        selections = new_manager.get_all_selections()
        assert len(selections) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])