import os
from threading import Lock
from typing import Any, Dict, Optional

import yaml

from .config.models import UnifiedConfig

class ConfigManager:
    _instance: Optional["ConfigManager"] = None
    _lock = Lock()

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.unified_config: Optional[UnifiedConfig] = None
        self.config_path: Optional[str] = None
        self._initialized = True

    def load_config(self, config_path: str) -> None:
        if self.unified_config and self.config_path == config_path:
            return

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        self.unified_config = UnifiedConfig(**config_data)
        self.config_path = config_path

    def get_config(self) -> UnifiedConfig:
        if not self.unified_config:
            raise RuntimeError(
                "Configuration not loaded. Call load_config() first."
            )
        return self.unified_config

    def reset(self) -> None:
        self.unified_config = None
        self.config_path = None

config_manager = ConfigManager()
