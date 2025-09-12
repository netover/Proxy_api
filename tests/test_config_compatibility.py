"""
Unit tests for Configuration Compatibility Layer
"""

import json
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.core.config_compatibility import (
    ConfigCompatibilityLayer,
    LegacyFormatDetector,
    LegacyConfigMigrator,
    check_legacy_presence,
    get_migration_report,
    migrate_specific_format,
    rollback_format
)


class TestLegacyFormatDetector:
    """Test legacy format detection"""

    def test_detect_legacy_model_selections(self):
        """Test detection of legacy model selections format"""
        detector = LegacyFormatDetector()

        # Test with legacy format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"openai": "gpt-3.5-turbo", "anthropic": "claude-3"}, f)
            legacy_path = Path(f.name)

        try:
            assert detector.detect_legacy_model_selections(legacy_path) == True
        finally:
            legacy_path.unlink()

        # Test with new format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "openai": {"model_name": "gpt-3.5-turbo", "editable": True},
                "anthropic": {"model_name": "claude-3", "editable": True}
            }, f)
            new_path = Path(f.name)

        try:
            assert detector.detect_legacy_model_selections(new_path) == False
        finally:
            new_path.unlink()

    def test_detect_legacy_yaml_config(self):
        """Test detection of legacy YAML configuration format"""
        detector = LegacyFormatDetector()

        # Test with legacy flat format
        legacy_config = {
            "host": "127.0.0.1",
            "port": 8000,
            "api_keys": "key1,key2",
            "providers": [
                {"name": "openai", "base_url": "https://api.openai.com/v1"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(legacy_config, f)
            legacy_path = Path(f.name)

        try:
            assert detector.detect_legacy_yaml_config(legacy_path) == True
        finally:
            legacy_path.unlink()

    def test_detect_legacy_python_config(self):
        """Test detection of legacy Python configuration format"""
        detector = LegacyFormatDetector()

        # Test with legacy indicators
        legacy_content = '''
PRODUCTION_CONFIG = {
    "old_key_name": "value",
    "legacy_config_format": True
}

def old_function():
    pass
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(legacy_content)
            legacy_path = Path(f.name)

        try:
            assert detector.detect_legacy_python_config(legacy_path) == True
        finally:
            legacy_path.unlink()


class TestLegacyConfigMigrator:
    """Test legacy configuration migration"""

    def test_migrate_model_selections(self):
        """Test migration of legacy model selections"""
        migrator = LegacyConfigMigrator()

        # Create legacy format
        legacy_data = {"openai": "gpt-3.5-turbo", "anthropic": "claude-3"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(legacy_data, f)
            legacy_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{}")  # Empty new file
            new_path = Path(f.name)

        try:
            success = migrator.migrate_model_selections(legacy_path, new_path)
            assert success == True

            # Check migrated content
            with open(new_path, 'r') as f:
                migrated_data = json.load(f)

            assert "openai" in migrated_data
            assert migrated_data["openai"]["model_name"] == "gpt-3.5-turbo"
            assert migrated_data["openai"]["editable"] == True
            assert "last_updated" in migrated_data["openai"]

        finally:
            # Cleanup
            for path in [legacy_path, new_path]:
                if path.exists():
                    path.unlink()
                backup_path = path.with_suffix('.legacy.json')
                if backup_path.exists():
                    backup_path.unlink()

    def test_migrate_yaml_config(self):
        """Test migration of legacy YAML configuration"""
        migrator = LegacyConfigMigrator()

        # Create legacy format
        legacy_data = {
            "host": "127.0.0.1",
            "port": 8000,
            "api_keys": "key1,key2",
            "providers": [
                {"name": "openai", "base_url": "https://api.openai.com/v1"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(legacy_data, f)
            legacy_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty new file
            new_path = Path(f.name)

        try:
            success = migrator.migrate_yaml_config(legacy_path, new_path)
            assert success == True

            # Check migrated content
            with open(new_path, 'r') as f:
                migrated_data = yaml.safe_load(f)

            assert "settings" in migrated_data
            assert migrated_data["settings"]["host"] == "127.0.0.1"
            assert migrated_data["settings"]["port"] == 8000
            assert "providers" in migrated_data

        finally:
            # Cleanup
            for path in [legacy_path, new_path]:
                if path.exists():
                    path.unlink()
                backup_path = path.with_suffix('.legacy.yaml')
                if backup_path.exists():
                    backup_path.unlink()


class TestConfigCompatibilityLayer:
    """Test main compatibility layer"""

    def test_enable_migration(self):
        """Test enabling/disabling migration"""
        layer = ConfigCompatibilityLayer()

        layer.enable_migration(False)
        assert layer._migration_enabled == False

        layer.enable_migration(True)
        assert layer._migration_enabled == True

    def test_enable_rollback(self):
        """Test enabling/disabling rollback"""
        layer = ConfigCompatibilityLayer()

        layer.enable_rollback(False)
        assert layer._rollback_enabled == False

        layer.enable_rollback(True)
        assert layer._rollback_enabled == True

    def test_check_legacy_formats(self):
        """Test checking legacy formats"""
        layer = ConfigCompatibilityLayer()

        # Test with non-existent files
        result = layer.check_legacy_formats()
        assert isinstance(result, dict)
        assert "model_selections" in result
        assert "yaml_config" in result
        assert "python_config" in result

    def test_get_migration_status(self):
        """Test getting migration status"""
        layer = ConfigCompatibilityLayer()

        status = layer.get_migration_status()
        assert isinstance(status, dict)
        assert "migration_enabled" in status
        assert "rollback_enabled" in status
        assert "legacy_formats_detected" in status
        assert "migration_needed" in status

    @patch('src.core.config_compatibility.warnings.warn')
    def test_migrate_on_demand(self, mock_warn):
        """Test on-demand migration"""
        layer = ConfigCompatibilityLayer()

        # Test with invalid format type
        result = layer.migrate_on_demand("invalid_format")
        assert result == False

    def test_migration_history(self):
        """Test migration history tracking"""
        layer = ConfigCompatibilityLayer()

        # Initially empty
        assert layer.get_migration_history() == []

        # Add a migration record
        layer._record_migration("test_format", "manual")

        history = layer.get_migration_history()
        assert len(history) == 1
        assert history[0]["format_type"] == "test_format"
        assert history[0]["migration_type"] == "manual"


class TestCompatibilityFunctions:
    """Test compatibility utility functions"""

    def test_check_legacy_presence(self):
        """Test checking legacy presence function"""
        result = check_legacy_presence()
        assert isinstance(result, dict)
        assert "model_selections" in result

    def test_get_migration_report(self):
        """Test getting migration report"""
        report = get_migration_report()
        assert isinstance(report, dict)
        assert "recommendations" in report
        assert "next_steps" in report
        assert "migration_enabled" in report

    def test_migrate_specific_format_invalid(self):
        """Test migrating invalid format type"""
        result = migrate_specific_format("invalid_format")
        assert result == False

    def test_rollback_format_invalid(self):
        """Test rolling back invalid format type"""
        result = rollback_format("invalid_format")
        assert result == False


if __name__ == "__main__":
    pytest.main([__file__])