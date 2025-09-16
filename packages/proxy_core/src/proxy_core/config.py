"""Configuration management for proxy_core package."""

from typing import List, Optional, Dict, Any
from .models import ProviderConfig, ProviderType


class ConfigManager:
    """Simple configuration manager for proxy_core."""

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None

    def load_config(self) -> Any:
        """Load configuration (placeholder implementation)."""
        # This is a placeholder - in a real implementation, this would load from file/env
        return self

    def get_forced_provider(self) -> Optional[ProviderConfig]:
        """Get forced provider configuration."""
        return None


# Global instance
config_manager = ConfigManager()
