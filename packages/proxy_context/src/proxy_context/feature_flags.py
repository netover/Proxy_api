"""
Feature Flag System for Cache Migration and Safe Rollout
Provides toggle mechanisms for switching between cache implementations with gradual rollout support.
"""

import os
import json
import hashlib
import random
import logging
from typing import Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlag:
    """Individual feature flag with rollout capabilities"""

    name: str
    enabled: bool = False
    rollout_percentage: int = 0  # 0-100
    description: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_enabled_for(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if feature is enabled for given context"""
        if not self.enabled:
            return False

        # Check custom conditions first
        if self.conditions:
            if not context:
                return False  # Conditions require context
            for condition_key, expected_value in self.conditions.items():
                if context.get(condition_key) != expected_value:
                    return False

        # Check rollout percentage
        if self.rollout_percentage < 100:
            context = context or {}
            user_id = context.get('user_id', 'anonymous')
            key = f"{self.name}:{user_id}"

            # Use consistent hashing for deterministic rollout
            hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
            user_percentage = (hash_value % 100) + 1

            if user_percentage > self.rollout_percentage:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'rollout_percentage': self.rollout_percentage,
            'description': self.description,
            'conditions': self.conditions,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlag':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            enabled=data.get('enabled', False),
            rollout_percentage=data.get('rollout_percentage', 0),
            description=data.get('description', ''),
            conditions=data.get('conditions', {}),
            metadata=data.get('metadata', {})
        )


class FeatureFlagManager:
    """
    Central feature flag manager with configuration support and persistence.
    Supports environment variables, config files, and runtime updates.
    """

    def __init__(
        self,
        config_file: Optional[Path] = None,
        auto_reload: bool = True,
        reload_interval: int = 60
    ):
        self.config_file = config_file or Path.cwd() / "feature_flags.json"
        self.auto_reload = auto_reload
        self.reload_interval = reload_interval

        self._flags: Dict[str, FeatureFlag] = {}
        self._lock = threading.RLock()
        self._last_reload = 0
        self._reload_task = None

        # Load initial configuration
        self._load_from_config()
        self._load_from_env()

        logger.info(f"FeatureFlagManager initialized with {len(self._flags)} flags")

    def _load_from_config(self):
        """Load flags from configuration file"""
        if not self.config_file.exists():
            logger.debug(f"Config file not found: {self.config_file}")
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._lock:
                for flag_data in data.get('flags', []):
                    flag = FeatureFlag.from_dict(flag_data)
                    self._flags[flag.name] = flag

            logger.info(f"Loaded {len(self._flags)} flags from config file")

        except Exception as e:
            logger.error(f"Error loading config file: {e}")

    def _load_from_env(self):
        """Load flags from environment variables"""
        # Environment variables format: FEATURE_<FLAG_NAME>_ENABLED=true
        # FEATURE_<FLAG_NAME>_ROLLOUT=50
        # FEATURE_<FLAG_NAME>_DESCRIPTION="Description"

        for key, value in os.environ.items():
            if key.startswith('FEATURE_') and key.endswith('_ENABLED'):
                flag_name = key[8:-8].lower()  # Remove FEATURE_ and _ENABLED, convert to lowercase
                enabled = value.lower() in ('true', '1', 'yes', 'on')

                # Get rollout percentage
                rollout_key = f"FEATURE_{flag_name.upper()}_ROLLOUT"
                rollout_percentage = int(os.environ.get(rollout_key, '100'))

                # Get description
                desc_key = f"FEATURE_{flag_name.upper()}_DESCRIPTION"
                description = os.environ.get(desc_key, '')

                with self._lock:
                    if flag_name not in self._flags:
                        self._flags[flag_name] = FeatureFlag(
                            name=flag_name,
                            enabled=enabled,
                            rollout_percentage=rollout_percentage,
                            description=description
                        )
                    else:
                        self._flags[flag_name].enabled = enabled
                        self._flags[flag_name].rollout_percentage = rollout_percentage
                        if description:
                            self._flags[flag_name].description = description

        logger.debug("Loaded flags from environment variables")

    def is_enabled(self, flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a feature flag is enabled"""
        with self._lock:
            flag = self._flags.get(flag_name)
            if not flag:
                return False
            return flag.is_enabled_for(context)

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name"""
        with self._lock:
            return self._flags.get(flag_name)

    def set_flag(
        self,
        name: str,
        enabled: bool = True,
        rollout_percentage: int = 100,
        description: str = "",
        conditions: Optional[Dict[str, Any]] = None
    ):
        """Set or update a feature flag"""
        with self._lock:
            flag = self._flags.get(name, FeatureFlag(name=name))
            flag.enabled = enabled
            flag.rollout_percentage = rollout_percentage
            if description:
                flag.description = description
            if conditions:
                flag.conditions = conditions

            self._flags[name] = flag
            logger.info(f"Updated feature flag: {name} (enabled={enabled}, rollout={rollout_percentage}%)")

    def enable_flag(self, name: str, rollout_percentage: int = 100):
        """Enable a feature flag"""
        self.set_flag(name, enabled=True, rollout_percentage=rollout_percentage)

    def disable_flag(self, name: str):
        """Disable a feature flag"""
        self.set_flag(name, enabled=False, rollout_percentage=0)

    def list_flags(self) -> Dict[str, Dict[str, Any]]:
        """List all feature flags with their status"""
        with self._lock:
            return {
                name: flag.to_dict()
                for name, flag in self._flags.items()
            }

    def save_to_config(self):
        """Save current flags to configuration file"""
        try:
            data = {
                'flags': [flag.to_dict() for flag in self._flags.values()],
                'metadata': {
                    'last_updated': self._last_reload,
                    'version': '1.0'
                }
            }

            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self._flags)} flags to config file")

        except Exception as e:
            logger.error(f"Error saving config file: {e}")

    def reload_config(self):
        """Reload configuration from file and environment"""
        self._load_from_config()
        self._load_from_env()
        self._last_reload = os.path.getmtime(self.config_file) if self.config_file.exists() else 0

    def get_stats(self) -> Dict[str, Any]:
        """Get feature flag statistics"""
        with self._lock:
            enabled_flags = [flag for flag in self._flags.values() if flag.enabled]
            enabled_count = len(enabled_flags)
            total_rollout = sum(flag.rollout_percentage for flag in enabled_flags)

            return {
                'total_flags': len(self._flags),
                'enabled_flags': enabled_count,
                'disabled_flags': len(self._flags) - enabled_count,
                'average_rollout_percentage': round(total_rollout / max(enabled_count, 1), 2),
                'config_file': str(self.config_file),
                'auto_reload': self.auto_reload
            }


# Global feature flag manager instance
_feature_flag_manager: Optional[FeatureFlagManager] = None


def get_feature_flag_manager() -> FeatureFlagManager:
    """Get global feature flag manager instance"""
    global _feature_flag_manager

    if _feature_flag_manager is None:
        _feature_flag_manager = FeatureFlagManager()

    return _feature_flag_manager


def is_feature_enabled(flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to check if a feature is enabled"""
    return get_feature_flag_manager().is_enabled(flag_name, context)


def enable_feature_flag(name: str, rollout_percentage: int = 100):
    """Convenience function to enable a feature flag"""
    get_feature_flag_manager().enable_flag(name, rollout_percentage)


def disable_feature_flag(name: str):
    """Convenience function to disable a feature flag"""
    get_feature_flag_manager().disable_flag(name)


# Cache-specific feature flags
CACHE_FEATURE_FLAGS = {
    'smart_cache_compression': 'Enable compression in SmartCache',
    'smart_cache_memory_optimization': 'Enable advanced memory optimization',
    'model_cache_persistence': 'Enable disk persistence for ModelCache',
    'model_cache_ttl_extension': 'Extend TTL for model cache entries',
    'memory_manager_aggressive_gc': 'Enable aggressive garbage collection',
    'cache_migration_mode': 'Enable migration between cache implementations',
    'cache_performance_monitoring': 'Enable detailed performance monitoring',
    'cache_fallback_mode': 'Enable fallback to simpler cache when needed'
}