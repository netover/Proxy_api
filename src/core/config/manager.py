import yaml
from pathlib import Path
from functools import lru_cache
from .models import UnifiedConfig

@lru_cache(maxsize=1)
def get_config() -> UnifiedConfig:
    """
    Loads the configuration from config.yaml, parses it using Pydantic models,
    and returns a cached UnifiedConfig object.
    The lru_cache decorator ensures the file is read and parsed only once.
    """
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("Configuration file 'config.yaml' not found.")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return UnifiedConfig(**config_data)

if __name__ == "__main__":
    # Example of how to use the cached config function
    start_time = time.time()
    config1 = get_config()
    duration1 = time.time() - start_time

    start_time_cached = time.time()
    config2 = get_config()
    duration_cached = time.time() - start_time_cached

    print(f"Initial config load time: {duration1:.6f}s")
    print(f"Cached config load time: {duration_cached:.6f}s")
    print(f"Configs are the same object: {config1 is config2}")
