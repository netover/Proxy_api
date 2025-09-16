#!/usr/bin/env python3
"""Test script to validate unified config loaders and schema validation"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_config_schema_validation():
    """Test JSON schema validation"""
    print("Testing JSON schema validation...")

    try:
        from src.core.config_schema import validate_config_at_startup

        config_path = Path("config.yaml")
        config_data = validate_config_at_startup(config_path)
        print("PASS: JSON schema validation passed")
        return True, config_data
    except Exception as e:
        print(f"FAIL: JSON schema validation failed: {e}")
        return False, None


def test_app_config_loading():
    """Test app config loading with Pydantic models"""
    print("Testing app config loading...")

    try:
        from src.core.app_config import load_config

        config = load_config()
        print(
            f"PASS: App config loading passed - {len(config.providers)} providers loaded"
        )
        return True, config
    except Exception as e:
        print(f"FAIL: App config loading failed: {e}")
        return False, None


def test_unified_config_loading():
    """Test unified config loading"""
    print("Testing unified config loading...")

    try:
        from src.core.unified_config import config_manager

        config = config_manager.load_config()
        print(
            f"PASS: Unified config loading passed - {len(config.providers)} providers loaded"
        )
        return True, config
    except Exception as e:
        print(f"FAIL: Unified config loading failed: {e}")
        return False, None


def test_provider_validation():
    """Test provider configuration validation"""
    print("Testing provider configuration validation...")

    try:
        from src.core.app_config import load_config

        config = load_config()

        # Check provider uniqueness
        names = [p.name for p in config.providers]
        if len(names) != len(set(names)):
            print("FAIL: Provider names are not unique")
            return False

        # Check priorities
        priorities = [p.priority for p in config.providers]
        if len(priorities) != len(set(priorities)):
            print("FAIL: Provider priorities are not unique")
            return False

        print("PASS: Provider validation passed")
        return True
    except Exception as e:
        print(f"FAIL: Provider validation failed: {e}")
        return False


def test_rate_limiting_config():
    """Test rate limiting configuration"""
    print("Testing rate limiting configuration...")

    try:
        import yaml

        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)

        rate_limit = config.get("rate_limit", {})
        if not rate_limit:
            print("FAIL: Rate limiting config missing")
            return False

        required_fields = ["requests_per_window", "window_seconds"]
        for field in required_fields:
            if field not in rate_limit:
                print(f"FAIL: Rate limiting config missing field: {field}")
                return False

        print("PASS: Rate limiting config validation passed")
        return True
    except Exception as e:
        print(f"FAIL: Rate limiting config validation failed: {e}")
        return False


def test_caching_config():
    """Test caching configuration"""
    print("Testing caching configuration...")

    try:
        import yaml

        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)

        caching = config.get("caching", {})
        if not caching:
            print("FAIL: Caching config missing")
            return False

        print("PASS: Caching config validation passed")
        return True
    except Exception as e:
        print(f"FAIL: Caching config validation failed: {e}")
        return False


def main():
    """Run all validation tests"""
    print("Starting unified config validation tests...\n")

    results = []

    # Test JSON schema validation
    schema_ok, config_data = test_config_schema_validation()
    results.append(("JSON Schema Validation", schema_ok))

    # Test app config loading
    app_config_ok, app_config = test_app_config_loading()
    results.append(("App Config Loading", app_config_ok))

    # Test unified config loading
    unified_ok, unified_config = test_unified_config_loading()
    results.append(("Unified Config Loading", unified_ok))

    # Test provider validation
    provider_ok = test_provider_validation()
    results.append(("Provider Validation", provider_ok))

    # Test rate limiting
    rate_limit_ok = test_rate_limiting_config()
    results.append(("Rate Limiting Config", rate_limit_ok))

    # Test caching
    caching_ok = test_caching_config()
    results.append(("Caching Config", caching_ok))

    print("\nValidation Results Summary:")
    print("=" * 40)

    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print("<30")
        if not passed:
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("All validation tests passed!")
        return 0
    else:
        print("Some validation tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
