import yaml
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List
from .models import ProviderConfig

class Settings(BaseSettings):
    config_file: str = "config.yaml"

@lru_cache
def get_settings() -> Settings:
    return Settings()

def load_providers_cfg(path: str) -> List[ProviderConfig]:
    with open(path, 'r') as f:
        raw = yaml.safe_load(f)
    return [ProviderConfig.model_validate(p) for p in raw["providers"]]
