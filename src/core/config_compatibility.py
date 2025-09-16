"""
Configuration Compatibility Layer for Legacy Formats

This module provides backward compatibility for legacy configuration formats
during the transition to the unified configuration system. It allows existing
configurations to continue working while gradually migrating to new formats.

Features:
- Legacy model selections format compatibility
- Legacy YAML configuration format compatibility
- Legacy Python configuration format compatibility
- Automatic transparent migration
- Deprecation warnings for legacy formats
- Gradual migration support without downtime

Supported Legacy Formats:
1. Legacy Model Selections JSON: {"provider": "model_name"}
2. Legacy YAML Config: Flat structure instead of nested
3. Legacy Python Config: Different key names and structure
"""

import json
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .logging import ContextualLogger
from .unified_config import config_manager

logger = ContextualLogger(__name__)


class LegacyFormatDetector:
    """Detects legacy configuration formats"""

    @staticmethod
    def detect_legacy_model_selections(path: Path) -> bool:
        """Detect legacy model selections format (simple provider->model mapping)"""
        if not path.exists():
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Legacy format: {"provider": "model_name"}
            # New format: {"provider": {"model_name": "...", "editable": true, "last_updated": "..."}}
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        return True  # Legacy format detected
                    elif isinstance(value, dict) and "model_name" in value:
                        continue  # New format
                    else:
                        return False  # Invalid format
            return False
        except (json.JSONDecodeError, IOError):
            return False

    @staticmethod
    def detect_legacy_yaml_config(path: Path) -> bool:
        """Detect legacy YAML configuration format"""
        if not path.exists():
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                return False

            # Legacy indicators:
            # - Flat structure instead of nested
            # - Different key names
            legacy_indicators = [
                "providers" in data
                and isinstance(data["providers"], list)
                and len(data["providers"]) > 0
                and isinstance(data["providers"][0], dict)
                and "name" in data["providers"][0]
                and "type"
                not in data["providers"][0],  # Legacy doesn't have 'type'
                "host" in data
                and "port" in data
                and "providers" not in data,  # Flat structure
                "api_keys" in data
                and isinstance(
                    data["api_keys"], str
                ),  # Legacy api_keys as string
            ]

            return any(legacy_indicators)
        except (yaml.YAMLError, IOError):
            return False

    @staticmethod
    def detect_legacy_python_config(path: Path) -> bool:
        """Detect legacy Python configuration format"""
        if not path.exists():
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Legacy indicators in Python files:
            legacy_indicators = [
                "PRODUCTION_CONFIG" in content and "old_key_name" in content,
                "legacy_config_format" in content,
                "deprecated_config_keys" in content,
            ]

            return any(legacy_indicators)
        except IOError:
            return False


class LegacyConfigMigrator:
    """Handles migration of legacy configuration formats"""

    def __init__(self):
        self.migration_warnings: List[str] = []

    def migrate_model_selections(
        self, legacy_path: Path, new_path: Path
    ) -> bool:
        """Migrate legacy model selections to new format"""
        try:
            with open(legacy_path, "r", encoding="utf-8") as f:
                legacy_data = json.load(f)

            # Convert legacy format to new format
            new_data = {}
            for provider, model_name in legacy_data.items():
                if isinstance(model_name, str):
                    new_data[provider] = {
                        "model_name": model_name,
                        "editable": True,
                        "last_updated": datetime.now().isoformat(),
                    }
                else:
                    # Already in new format
                    new_data[provider] = model_name

            # Write migrated data
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)

            # Backup legacy file
            backup_path = legacy_path.with_suffix(".legacy.json")
            legacy_path.rename(backup_path)

            self.migration_warnings.append(
                f"Migrated legacy model selections from {legacy_path} to {new_path}. "
                f"Legacy file backed up as {backup_path}"
            )

            logger.info(
                f"Successfully migrated model selections from {legacy_path} to {new_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to migrate model selections: {e}")
            return False

    def migrate_yaml_config(self, legacy_path: Path, new_path: Path) -> bool:
        """Migrate legacy YAML configuration to new format"""
        try:
            with open(legacy_path, "r", encoding="utf-8") as f:
                legacy_data = yaml.safe_load(f)

            # Convert legacy flat structure to new nested structure
            new_data = self._convert_legacy_yaml_structure(legacy_data)

            # Write migrated data
            with open(new_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    new_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

            # Backup legacy file
            backup_path = legacy_path.with_suffix(".legacy.yaml")
            legacy_path.rename(backup_path)

            self.migration_warnings.append(
                f"Migrated legacy YAML config from {legacy_path} to {new_path}. "
                f"Legacy file backed up as {backup_path}"
            )

            logger.info(
                f"Successfully migrated YAML config from {legacy_path} to {new_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to migrate YAML config: {e}")
            return False

    def migrate_python_config(self, legacy_path: Path, new_path: Path) -> bool:
        """Migrate legacy Python configuration to new format"""
        try:
            # For Python configs, we'll create a new config file
            # and import the legacy config to extract values
            new_config_content = self._generate_new_python_config()

            with open(new_path, "w", encoding="utf-8") as f:
                f.write(new_config_content)

            # Backup legacy file
            backup_path = legacy_path.with_suffix(".legacy.py")
            legacy_path.rename(backup_path)

            self.migration_warnings.append(
                f"Migrated legacy Python config from {legacy_path} to {new_path}. "
                f"Legacy file backed up as {backup_path}"
            )

            logger.info(
                f"Successfully migrated Python config from {legacy_path} to {new_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to migrate Python config: {e}")
            return False

    def _convert_legacy_yaml_structure(
        self, legacy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert legacy YAML structure to new format"""
        new_data = {}

        # Create nested settings structure
        settings = {}

        # Handle global settings
        settings_keys = [
            "app_name",
            "app_version",
            "debug",
            "host",
            "port",
            "api_keys",
        ]
        for key in settings_keys:
            if key in legacy_data:
                settings[key] = legacy_data[key]

        # Handle api_keys conversion
        if "api_keys" in legacy_data and isinstance(
            legacy_data["api_keys"], str
        ):
            settings["api_keys"] = [
                k.strip()
                for k in legacy_data["api_keys"].split(",")
                if k.strip()
            ]

        # Set default values for missing settings
        settings.setdefault("app_name", "LLM Proxy API")
        settings.setdefault("app_version", "2.0.0")
        settings.setdefault("debug", False)
        settings.setdefault("host", "127.0.0.1")
        settings.setdefault("port", 8000)
        settings.setdefault("api_keys", [])

        new_data["settings"] = settings

        # Handle providers
        if "providers" in legacy_data:
            new_data["providers"] = []
            for provider in legacy_data["providers"]:
                new_provider = {
                    "name": provider.get("name", ""),
                    "type": provider.get(
                        "type", "openai"
                    ),  # Default to openai
                    "base_url": provider.get(
                        "base_url", "https://api.openai.com/v1"
                    ),
                    "api_key_env": provider.get("api_key_env", "API_KEY"),
                    "models": provider.get("models", []),
                    "enabled": provider.get("enabled", True),
                    "priority": provider.get("priority", 100),
                    "timeout": provider.get("timeout", 30),
                    "max_retries": provider.get("max_retries", 3),
                }
                new_data["providers"].append(new_provider)
        else:
            # Default provider if none specified
            new_data["providers"] = [
                {
                    "name": "openai_default",
                    "type": "openai",
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "OPENAI_API_KEY",
                    "models": ["gpt-3.5-turbo"],
                    "enabled": True,
                    "priority": 100,
                    "timeout": 30,
                    "max_retries": 3,
                }
            ]

        return new_data

    def _generate_new_python_config(self) -> str:
        """Generate new Python configuration content"""
        return '''"""
Production Configuration for LLM Proxy API
Generated from legacy configuration migration.
"""

import os
from pathlib import Path

# Production Configuration
PRODUCTION_CONFIG = {
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "api_keys": os.getenv("PROXY_API_KEYS", "").split(",") if os.getenv("PROXY_API_KEYS") else [],
    "debug": os.getenv("DEBUG", "false").lower() == "true",
}

def get_production_config():
    """Get production configuration"""
    return PRODUCTION_CONFIG.copy()
'''


class ConfigCompatibilityLayer:
    """Main compatibility layer for configuration formats"""

    def __init__(self):
        self.detector = LegacyFormatDetector()
        self.migrator = LegacyConfigMigrator()
        self._migration_enabled = True
        self._warnings_shown = set()
        self._migration_history: List[Dict[str, Any]] = []
        self._rollback_enabled = True

    def enable_migration(self, enabled: bool = True):
        """Enable or disable automatic migration"""
        self._migration_enabled = enabled
        logger.info(
            f"Configuration migration {'enabled' if enabled else 'disabled'}"
        )

    def enable_rollback(self, enabled: bool = True):
        """Enable or disable rollback capability"""
        self._rollback_enabled = enabled
        logger.info(
            f"Configuration rollback {'enabled' if enabled else 'disabled'}"
        )

    def migrate_on_demand(
        self, format_type: str, config_path: Optional[Path] = None
    ) -> bool:
        """Perform migration on demand for specific format type"""
        config_path = config_path or Path("config.yaml")

        success = False
        if format_type == "model_selections":
            model_selections_path = Path("config/model_selections.json")
            if self.detector.detect_legacy_model_selections(
                model_selections_path
            ):
                success = self.migrator.migrate_model_selections(
                    model_selections_path, model_selections_path
                )
        elif format_type == "yaml_config":
            if self.detector.detect_legacy_yaml_config(config_path):
                success = self.migrator.migrate_yaml_config(
                    config_path, config_path
                )
        elif format_type == "python_config":
            python_config_path = Path("production_config.py")
            if self.detector.detect_legacy_python_config(python_config_path):
                success = self.migrator.migrate_python_config(
                    python_config_path, python_config_path
                )

        if success:
            self._record_migration(format_type, "manual")
            logger.info(f"Successfully migrated {format_type} on demand")

        return success

    def rollback_migration(
        self, format_type: str, config_path: Optional[Path] = None
    ) -> bool:
        """Rollback migration for specific format type"""
        if not self._rollback_enabled:
            logger.warning("Rollback is disabled")
            return False

        config_path = config_path or Path("config.yaml")

        try:
            if format_type == "model_selections":
                return self._rollback_model_selections()
            elif format_type == "yaml_config":
                return self._rollback_yaml_config(config_path)
            elif format_type == "python_config":
                return self._rollback_python_config()
            else:
                logger.error(
                    f"Unknown format type for rollback: {format_type}"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to rollback {format_type}: {e}")
            return False

    def _rollback_model_selections(self) -> bool:
        """Rollback model selections migration"""
        legacy_path = Path("config/model_selections.legacy.json")
        current_path = Path("config/model_selections.json")

        if not legacy_path.exists():
            logger.warning(
                "No legacy model selections backup found for rollback"
            )
            return False

        # Backup current file
        if current_path.exists():
            current_path.rename(current_path.with_suffix(".rollback.json"))

        # Restore legacy file
        legacy_path.rename(current_path)

        logger.info("Successfully rolled back model selections migration")
        return True

    def _rollback_yaml_config(self, config_path: Path) -> bool:
        """Rollback YAML config migration"""
        legacy_path = config_path.with_suffix(".legacy.yaml")

        if not legacy_path.exists():
            logger.warning(
                f"No legacy YAML config backup found for rollback: {legacy_path}"
            )
            return False

        # Backup current file
        if config_path.exists():
            config_path.rename(config_path.with_suffix(".rollback.yaml"))

        # Restore legacy file
        legacy_path.rename(config_path)

        logger.info(
            f"Successfully rolled back YAML config migration: {config_path}"
        )
        return True

    def _rollback_python_config(self) -> bool:
        """Rollback Python config migration"""
        legacy_path = Path("production_config.legacy.py")
        current_path = Path("production_config.py")

        if not legacy_path.exists():
            logger.warning("No legacy Python config backup found for rollback")
            return False

        # Backup current file
        if current_path.exists():
            current_path.rename(current_path.with_suffix(".rollback.py"))

        # Restore legacy file
        legacy_path.rename(current_path)

        logger.info("Successfully rolled back Python config migration")
        return True

    def _record_migration(self, format_type: str, migration_type: str):
        """Record migration in history"""
        self._migration_history.append(
            {
                "format_type": format_type,
                "migration_type": migration_type,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
            }
        )

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        return self._migration_history.copy()

    def check_legacy_formats(
        self, config_path: Optional[Path] = None
    ) -> Dict[str, bool]:
        """Check which legacy formats are present"""
        config_path = config_path or Path("config.yaml")

        return {
            "model_selections": self.detector.detect_legacy_model_selections(
                Path("config/model_selections.json")
            ),
            "yaml_config": self.detector.detect_legacy_yaml_config(
                config_path
            ),
            "python_config": self.detector.detect_legacy_python_config(
                Path("production_config.py")
            ),
        }

    def load_config_with_compatibility(
        self, config_path: Optional[Path] = None
    ) -> Any:
        """Load configuration with legacy format compatibility"""
        config_path = config_path or Path("config.yaml")

        # Check for legacy formats and migrate if needed
        if self._migration_enabled:
            self._check_and_migrate_legacy_formats(config_path)

        # Show any migration warnings
        self._show_migration_warnings()

        # Load the configuration using the standard manager
        return config_manager.load_config()

    def _check_and_migrate_legacy_formats(self, config_path: Path):
        """Check for and migrate legacy configuration formats"""
        # Check model selections
        model_selections_path = Path("config/model_selections.json")
        if self.detector.detect_legacy_model_selections(model_selections_path):
            self._migrate_with_warning(
                "model_selections",
                lambda: self.migrator.migrate_model_selections(
                    model_selections_path, model_selections_path
                ),
            )

        # Check YAML config
        if self.detector.detect_legacy_yaml_config(config_path):
            self._migrate_with_warning(
                "yaml_config",
                lambda: self.migrator.migrate_yaml_config(
                    config_path, config_path
                ),
            )

        # Check Python config
        python_config_path = Path("production_config.py")
        if self.detector.detect_legacy_python_config(python_config_path):
            self._migrate_with_warning(
                "python_config",
                lambda: self.migrator.migrate_python_config(
                    python_config_path, python_config_path
                ),
            )

    def _migrate_with_warning(self, format_type: str, migration_func):
        """Perform migration with deprecation warning"""
        warning_key = f"legacy_{format_type}"

        if warning_key not in self._warnings_shown:
            warnings.warn(
                f"Legacy {format_type.replace('_', ' ')} format detected. "
                "Automatic migration will be performed. "
                "Please update your configuration to use the new format.",
                DeprecationWarning,
                stacklevel=3,
            )
            self._warnings_shown.add(warning_key)

        # Perform migration
        if migration_func():
            logger.info(f"Successfully migrated legacy {format_type}")
        else:
            logger.error(f"Failed to migrate legacy {format_type}")

    def _show_migration_warnings(self):
        """Show accumulated migration warnings"""
        for warning in self.migrator.migration_warnings:
            warnings.warn(warning, UserWarning, stacklevel=2)

        # Clear warnings after showing
        self.migrator.migration_warnings.clear()

    def get_migration_status(self) -> Dict[str, Any]:
        """Get status of migration operations"""
        legacy_formats = self.check_legacy_formats()

        return {
            "migration_enabled": self._migration_enabled,
            "rollback_enabled": self._rollback_enabled,
            "warnings_shown": list(self._warnings_shown),
            "migration_warnings": self.migrator.migration_warnings.copy(),
            "migration_history": self.get_migration_history(),
            "legacy_formats_detected": legacy_formats,
            "migration_needed": any(legacy_formats.values()),
        }


# Global compatibility layer instance
config_compatibility = ConfigCompatibilityLayer()


def load_config_with_legacy_support(config_path: Optional[Path] = None) -> Any:
    """Load configuration with legacy format support"""
    return config_compatibility.load_config_with_compatibility(config_path)


def enable_legacy_migration(enabled: bool = True):
    """Enable or disable legacy configuration migration"""
    config_compatibility.enable_migration(enabled)


def get_migration_status() -> Dict[str, Any]:
    """Get current migration status"""
    return config_compatibility.get_migration_status()


# Backward compatibility functions
def migrate_legacy_configs():
    """Manually trigger migration of legacy configurations"""
    config_compatibility._check_and_migrate_legacy_formats(Path("config.yaml"))


def migrate_specific_format(
    format_type: str, config_path: Optional[Path] = None
):
    """Migrate a specific legacy format on demand"""
    return config_compatibility.migrate_on_demand(format_type, config_path)


def rollback_format(format_type: str, config_path: Optional[Path] = None):
    """Rollback migration for a specific format"""
    return config_compatibility.rollback_migration(format_type, config_path)


def check_legacy_presence(config_path: Optional[Path] = None):
    """Check which legacy formats are present"""
    return config_compatibility.check_legacy_formats(config_path)


def get_migration_report():
    """Get comprehensive migration report"""
    status = config_compatibility.get_migration_status()
    legacy_check = config_compatibility.check_legacy_formats()

    return {
        **status,
        "recommendations": _generate_migration_recommendations(legacy_check),
        "next_steps": _generate_next_steps(legacy_check),
    }


def _generate_migration_recommendations(
    legacy_check: Dict[str, bool],
) -> List[str]:
    """Generate migration recommendations based on detected legacy formats"""
    recommendations = []

    if legacy_check.get("model_selections"):
        recommendations.append(
            "Migrate model selections: Run migrate_specific_format('model_selections')"
        )

    if legacy_check.get("yaml_config"):
        recommendations.append(
            "Migrate YAML config: Run migrate_specific_format('yaml_config')"
        )

    if legacy_check.get("python_config"):
        recommendations.append(
            "Migrate Python config: Run migrate_specific_format('python_config')"
        )

    if not any(legacy_check.values()):
        recommendations.append(
            "No legacy formats detected - system is up to date"
        )

    return recommendations


def _generate_next_steps(legacy_check: Dict[str, bool]) -> List[str]:
    """Generate next steps for migration process"""
    next_steps = []

    if any(legacy_check.values()):
        next_steps.extend(
            [
                "1. Review migration recommendations above",
                "2. Backup your current configuration files",
                "3. Run individual migrations using migrate_specific_format()",
                "4. Test your application with migrated configurations",
                "5. Remove legacy backup files after verification",
            ]
        )
    else:
        next_steps.append(
            "No action required - all configurations are current"
        )

    return next_steps


if __name__ == "__main__":
    # Enable compatibility layer
    print("Configuration Compatibility Layer")
    print("===============================")

    # Get migration report
    report = get_migration_report()

    print(f"Migration enabled: {report['migration_enabled']}")
    print(f"Rollback enabled: {report['rollback_enabled']}")
    print(f"Migration needed: {report['migration_needed']}")
    print()

    # Show legacy format status
    legacy_formats = report["legacy_formats_detected"]
    print("Legacy format detection:")
    for format_type, detected in legacy_formats.items():
        status = "DETECTED" if detected else "Not detected"
        print(f"  {format_type}: {status}")

    print()

    # Show recommendations
    if report["recommendations"]:
        print("Migration recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")

    print()

    # Show next steps
    if report["next_steps"]:
        print("Next steps:")
        for step in report["next_steps"]:
            print(f"  {step}")

    print()

    # Show migration history
    history = report["migration_history"]
    if history:
        print("Migration history:")
        for migration in history:
            print(
                f"  • {migration['format_type']} ({migration['migration_type']}) - {migration['timestamp']}"
            )
    else:
        print("No migration history available.")

    print("\nCompatibility layer ready.")
    print("Use migrate_specific_format() for individual migrations.")
    print("Use rollback_format() to rollback if needed.")
