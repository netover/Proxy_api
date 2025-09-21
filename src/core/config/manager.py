import yaml
from pathlib import Path
from .models import UnifiedConfig

CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"

_config_instance: UnifiedConfig = None

def get_config() -> UnifiedConfig:
    """
    Parses the config.yaml file and returns a UnifiedConfig object.
    Caches the result for subsequent calls.
    """
    global _config_instance
    if _config_instance is not None:
        return _config_instance

    if not CONFIG_FILE_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_FILE_PATH}")

    with open(CONFIG_FILE_PATH, 'r') as f:
        config_data = yaml.safe_load(f)

    if not config_data:
        raise ValueError("Configuration file is empty or invalid.")

    # Pydantic will automatically validate and map the data to the models
    _config_instance = UnifiedConfig(**config_data)

    return _config_instance
