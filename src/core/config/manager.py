import yaml
from pathlib import Path
from functools import lru_cache
from .models import UnifiedConfig

@lru_cache(maxsize=1)
def get_config() -> UnifiedConfig:
    """
    Loads the configuration from config.yaml, parses it using Pydantic models,
    and returns a cached UnifiedConfig object.
    """
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("Configuration file 'config.yaml' not found.")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return UnifiedConfig(**config_data)

# To make it runnable for quick checks
if __name__ == "__main__":
    try:
        config = get_config()
        print("Configuration loaded successfully!")
        print(f"App Version: {config.app.version}")
        print(f"Loaded {len(config.providers)} providers.")
        print(f"API Keys: {config.proxy_api_keys}")
    except Exception as e:
        print(f"Failed to load configuration: {e}")
