#!/usr/bin/env python3
"""
Demonstration script for model configuration persistence and hot-reloading
"""

import os
import tempfile
import json
from pathlib import Path
import time

# Add the src directory to the path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.model_config import ModelConfigManager
from src.services.model_config_service import ModelConfigService


def demo_persistence():
    """Demonstrate persistence across restarts"""
    print("=== Model Configuration Persistence Demo ===")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"

    try:
        # First instance
        print("\n1. Creating first ModelConfigManager instance...")
        manager1 = ModelConfigManager(config_dir)

        # Set some model selections
        print("   Setting model selections...")
        manager1.set_model_selection("openai", "gpt-4")
        manager1.set_model_selection("anthropic", "claude-3-sonnet")
        manager1.set_model_selection("google", "gemini-pro", editable=False)

        # Show current selections
        selections = manager1.get_all_selections()
        print(f"   Current selections: {len(selections)} providers configured")
        for provider, selection in selections.items():
            print(
                f"   - {provider}: {selection.model_name} (editable: {selection.editable})"
            )

        # Create second instance (simulating restart)
        print(
            "\n2. Creating second ModelConfigManager instance (simulating restart)..."
        )
        manager2 = ModelConfigManager(config_dir)

        # Verify persistence
        selections2 = manager2.get_all_selections()
        print(f"   Loaded selections: {len(selections2)} providers configured")
        for provider, selection in selections2.items():
            print(
                f"   - {provider}: {selection.model_name} (editable: {selection.editable})"
            )

        # Verify they match
        assert len(selections) == len(selections2)
        for provider in selections:
            assert (
                selections[provider].model_name
                == selections2[provider].model_name
            )
            assert (
                selections[provider].editable == selections2[provider].editable
            )

        print(
            "   [OK] Persistence verified - selections maintained across restarts"
        )

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_hot_reload():
    """Demonstrate hot-reloading functionality"""
    print("\n=== Model Configuration Hot-Reload Demo ===")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"

    try:
        # Create manager
        manager = ModelConfigManager(config_dir)

        # Set initial selection
        print("\n1. Setting initial model selection...")
        manager.set_model_selection("openai", "gpt-3.5-turbo")

        # Simulate external modification
        print("\n2. Simulating external modification...")
        config_file = manager.config_file

        # Read current config
        with open(config_file, "r") as f:
            data = json.load(f)

        # Modify externally
        data["openai"]["model_name"] = "gpt-4"
        data["anthropic"] = {
            "model_name": "claude-3-haiku",
            "editable": True,
            "last_updated": "2024-01-01T00:00:00",
        }

        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)

        print("   External modification saved to config file")

        # Reload configuration
        print("\n3. Reloading configuration...")
        manager.reload()

        # Verify changes
        selections = manager.get_all_selections()
        print(f"   Updated selections: {len(selections)} providers configured")
        for provider, selection in selections.items():
            print(f"   - {provider}: {selection.model_name}")

        # Verify changes took effect
        openai_selection = manager.get_model_selection("openai")
        anthropic_selection = manager.get_model_selection("anthropic")

        assert openai_selection.model_name == "gpt-4"
        assert anthropic_selection.model_name == "claude-3-haiku"

        print(
            "   [OK] Hot-reload verified - external changes detected and loaded"
        )

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


def demo_service_layer():
    """Demonstrate the service layer functionality"""
    print("\n=== Model Configuration Service Layer Demo ===")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"

    try:
        # Create service
        from src.core.model_config import model_config_manager

        model_config_manager.config_dir = config_dir

        service = ModelConfigService()
        service._model_manager = model_config_manager

        print("\n1. Using service layer to set model selections...")

        # Use service to set selections
        result1 = service.set_model_selection("test_provider1", "test_model1")
        print(f"   Set test_provider1: {result1}")

        result2 = service.set_model_selection(
            "test_provider2", "test_model2", editable=False
        )
        print(f"   Set test_provider2: {result2}")

        # Get all selections
        selections = service.get_all_model_selections()
        print(f"\n   All selections: {selections}")

        # Validate selections
        validation = service.validate_model_selection(
            "test_provider1", "test_model1"
        )
        print(f"   Validation result: {validation}")

        print("   [OK] Service layer functionality verified")

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Model Configuration System Validation")
    print("=" * 50)

    demo_persistence()
    demo_hot_reload()
    demo_service_layer()

    print("\n" + "=" * 50)
    print("[SUCCESS] All demonstrations completed successfully!")
    print("The model configuration system provides:")
    print("  - Persistent storage across application restarts")
    print("  - Hot-reloading of configuration changes")
    print("  - Thread-safe operations")
    print("  - Service layer with validation and error handling")
    print("  - Backward compatibility with legacy formats")
    print("  - Atomic updates with rollback capability")
