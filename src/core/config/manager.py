import yaml
import os
import threading
from pathlib import Path
from .models import UnifiedConfig

# Use an environment variable for the config path, with a default.
# This makes the application more flexible for different environments.
CONFIG_FILE_PATH = Path(os.getenv("PROXY_CONFIG_PATH", "config.yaml"))

_config_instance: UnifiedConfig = None
_config_lock = threading.Lock()

def get_config() -> UnifiedConfig:
    """
    Parses the config.yaml file and returns a UnifiedConfig object.
    This function is thread-safe and caches the result for subsequent calls.
    """
    global _config_instance
    # First check without a lock for performance.
    if _config_instance is not None:
        return _config_instance

    # If the instance is not created, acquire a lock.
    with _config_lock:
        # Double-check if another thread created the instance while waiting for the lock.
        if _config_instance is not None:
            return _config_instance

        if not CONFIG_FILE_PATH.is_file():
            # If the default config file is not found, we can proceed with default models.
            # This makes the app runnable out-of-the-box without a config file.
            print(f"INFO: Configuration file not found at {CONFIG_FILE_PATH}. "
                  "Proceeding with default configuration models.")
            config_data = {}
        else:
            with open(CONFIG_FILE_PATH, 'r') as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                # Handle empty config file by using defaults.
                print(f"WARNING: Configuration file at {CONFIG_FILE_PATH} is empty. "
                      "Using default configuration.")
                config_data = {}

        # Pydantic will automatically validate and map the data to the models.
        # Missing sections will be populated by the default_factory in the models.
        _config_instance = UnifiedConfig(**(config_data or {}))

        return _config_instance
