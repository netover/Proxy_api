"""
Tests for the Feature Flag System
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from proxy_context.feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    get_feature_flag_manager,
    is_feature_enabled,
    enable_feature_flag,
    disable_feature_flag,
    CACHE_FEATURE_FLAGS,
)


class TestFeatureFlag:
    """Test individual feature flag functionality"""

    def test_flag_creation(self):
        """Test creating a feature flag"""
        flag = FeatureFlag(
            name="test_flag",
            enabled=True,
            rollout_percentage=50,
            description="Test flag",
        )

        assert flag.name == "test_flag"
        assert flag.enabled is True
        assert flag.rollout_percentage == 50
        assert flag.description == "Test flag"

    def test_flag_serialization(self):
        """Test flag serialization to/from dict"""
        flag = FeatureFlag(
            name="test_flag",
            enabled=True,
            rollout_percentage=75,
            description="Test flag",
            conditions={"env": "test"},
        )

        data = flag.to_dict()
        restored_flag = FeatureFlag.from_dict(data)

        assert restored_flag.name == flag.name
        assert restored_flag.enabled == flag.enabled
        assert restored_flag.rollout_percentage == flag.rollout_percentage
        assert restored_flag.description == flag.description
        assert restored_flag.conditions == flag.conditions

    def test_rollout_percentage_full(self):
        """Test 100% rollout"""
        flag = FeatureFlag(
            name="test_flag", enabled=True, rollout_percentage=100
        )

        # Should always be enabled regardless of context
        assert flag.is_enabled_for() is True
        assert flag.is_enabled_for({"user_id": "user1"}) is True

    def test_rollout_percentage_zero(self):
        """Test 0% rollout"""
        flag = FeatureFlag(
            name="test_flag", enabled=True, rollout_percentage=0
        )

        # Should never be enabled
        assert flag.is_enabled_for() is False
        assert flag.is_enabled_for({"user_id": "user1"}) is False

    def test_rollout_percentage_partial(self):
        """Test partial rollout with deterministic hashing"""
        flag = FeatureFlag(
            name="test_flag", enabled=True, rollout_percentage=50
        )

        # Test with known user IDs to verify deterministic behavior
        # These specific user IDs are chosen to fall within/outside the 50% rollout
        assert flag.is_enabled_for({"user_id": "user_in_rollout"}) is True
        assert flag.is_enabled_for({"user_id": "user_not_in_rollout"}) is False

    def test_conditions(self):
        """Test conditional flag evaluation"""
        flag = FeatureFlag(
            name="test_flag",
            enabled=True,
            rollout_percentage=100,
            conditions={"env": "production"},
        )

        # Should be enabled only when condition matches
        assert flag.is_enabled_for({"env": "production"}) is True
        assert flag.is_enabled_for({"env": "staging"}) is False
        assert flag.is_enabled_for() is False  # No context

    def test_disabled_flag(self):
        """Test disabled flag"""
        flag = FeatureFlag(
            name="test_flag", enabled=False, rollout_percentage=100
        )

        assert flag.is_enabled_for() is False
        assert flag.is_enabled_for({"user_id": "user1"}) is False


class TestFeatureFlagManager:
    """Test feature flag manager functionality"""

    def test_manager_creation(self):
        """Test creating a feature flag manager"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "feature_flags.json"
            manager = FeatureFlagManager(config_file=config_file)

            assert manager.config_file == config_file
            assert len(manager._flags) == 0

    def test_flag_management(self):
        """Test basic flag management operations"""
        manager = FeatureFlagManager()

        # Set a flag
        manager.set_flag(
            "test_flag",
            enabled=True,
            rollout_percentage=100,
            description="Test",
        )

        # Check if it exists
        flag = manager.get_flag("test_flag")
        assert flag is not None
        assert flag.enabled is True
        assert flag.rollout_percentage == 100

        # Check if enabled
        assert manager.is_enabled("test_flag") is True

        # Disable flag
        manager.disable_flag("test_flag")
        assert manager.is_enabled("test_flag") is False

        # Enable flag with rollout
        manager.enable_flag("test_flag", 75)
        assert manager.is_enabled("test_flag") is True
        flag = manager.get_flag("test_flag")
        assert flag.rollout_percentage == 75

    def test_config_file_loading(self):
        """Test loading flags from config file"""
        config_data = {
            "flags": [
                {
                    "name": "flag1",
                    "enabled": True,
                    "rollout_percentage": 100,
                    "description": "Flag 1",
                },
                {
                    "name": "flag2",
                    "enabled": False,
                    "rollout_percentage": 50,
                    "description": "Flag 2",
                },
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "feature_flags.json"

            # Write config file
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Create manager
            manager = FeatureFlagManager(config_file=config_file)

            # Check flags were loaded
            assert len(manager._flags) == 2
            assert manager.is_enabled("flag1") is True
            assert manager.is_enabled("flag2") is False

    def test_environment_variables(self):
        """Test loading flags from environment variables"""
        env_vars = {
            "FEATURE_TEST_ENABLED": "true",
            "FEATURE_TEST_ROLLOUT": "100",
            "FEATURE_TEST_DESCRIPTION": "Test flag from env",
        }

        with patch.dict(os.environ, env_vars):
            # Create a fresh manager without loading existing config
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as temp_dir:
                config_file = Path(temp_dir) / "test_flags.json"
                manager = FeatureFlagManager(config_file=config_file)
                # Clear any existing flags
                manager._flags.clear()
                # Load from environment
                manager._load_from_env()

                # Check flag was loaded from env
                assert (
                    "test" in manager._flags
                ), f"Flag 'test' not found in {list(manager._flags.keys())}"
                flag = manager.get_flag("test")

                # Test with context that should be enabled
                context = {"user_id": "test_user_123"}
                assert manager.is_enabled("test", context) is True
                assert flag.rollout_percentage == 100
                assert flag.description == "Test flag from env"

    def test_save_to_config(self):
        """Test saving flags to config file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "feature_flags.json"
            manager = FeatureFlagManager(config_file=config_file)

            # Add some flags
            manager.set_flag("flag1", enabled=True, rollout_percentage=100)
            manager.set_flag("flag2", enabled=False, rollout_percentage=50)

            # Save to config
            manager.save_to_config()

            # Verify file was created and contains correct data
            assert config_file.exists()

            with open(config_file, "r") as f:
                data = json.load(f)

            assert len(data["flags"]) == 2
            flag_names = [flag["name"] for flag in data["flags"]]
            assert "flag1" in flag_names
            assert "flag2" in flag_names

    def test_stats(self):
        """Test getting manager statistics"""
        manager = FeatureFlagManager()

        # Add some flags
        manager.set_flag("enabled_flag", enabled=True, rollout_percentage=100)
        manager.set_flag("disabled_flag", enabled=False, rollout_percentage=50)
        manager.set_flag("partial_flag", enabled=True, rollout_percentage=25)

        stats = manager.get_stats()

        assert stats["total_flags"] == 3
        assert stats["enabled_flags"] == 2
        assert stats["disabled_flags"] == 1
        assert stats["average_rollout_percentage"] == 62.5  # (100 + 25) / 2

    def test_list_flags(self):
        """Test listing all flags"""
        manager = FeatureFlagManager()

        manager.set_flag(
            "flag1", enabled=True, rollout_percentage=100, description="Flag 1"
        )
        manager.set_flag(
            "flag2", enabled=False, rollout_percentage=50, description="Flag 2"
        )

        flags = manager.list_flags()

        assert len(flags) == 2
        assert "flag1" in flags
        assert "flag2" in flags
        assert flags["flag1"]["enabled"] is True
        assert flags["flag2"]["enabled"] is False


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_convenience_functions(self):
        """Test the global convenience functions"""
        # Reset the global manager
        import proxy_context.feature_flags

        proxy_context.feature_flags._feature_flag_manager = None

        # Enable a flag
        enable_feature_flag("test_flag", 100)
        assert is_feature_enabled("test_flag") is True

        # Disable a flag
        disable_feature_flag("test_flag")
        assert is_feature_enabled("test_flag") is False

    def test_get_feature_flag_manager(self):
        """Test getting the global feature flag manager"""
        manager = get_feature_flag_manager()
        assert isinstance(manager, FeatureFlagManager)

        # Should return the same instance
        manager2 = get_feature_flag_manager()
        assert manager is manager2


class TestCacheFeatureFlags:
    """Test cache-specific feature flags"""

    def test_cache_feature_flags_exist(self):
        """Test that predefined cache feature flags exist"""
        assert "smart_cache_compression" in CACHE_FEATURE_FLAGS
        assert "smart_cache_memory_optimization" in CACHE_FEATURE_FLAGS
        assert "model_cache_persistence" in CACHE_FEATURE_FLAGS
        assert "model_cache_ttl_extension" in CACHE_FEATURE_FLAGS
        assert "memory_manager_aggressive_gc" in CACHE_FEATURE_FLAGS
        assert "cache_migration_mode" in CACHE_FEATURE_FLAGS
        assert "cache_performance_monitoring" in CACHE_FEATURE_FLAGS
        assert "cache_fallback_mode" in CACHE_FEATURE_FLAGS

    def test_cache_feature_flag_descriptions(self):
        """Test that cache feature flags have descriptions"""
        for flag_name, description in CACHE_FEATURE_FLAGS.items():
            assert isinstance(description, str)
            assert len(description) > 0


if __name__ == "__main__":
    pytest.main([__file__])
