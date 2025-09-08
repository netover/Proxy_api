import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
import yaml

# Define the project's base directory (the parent of the 'src' directory)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """Application settings with validation and environment support"""

    # App Configuration
    app_name: str = "LLM Proxy API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000

    # Security
    api_key_header: str = "X-API-Key"
    allowed_origins: List[str] = ["*"]
    proxy_api_keys: List[str] = []

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Timeouts
    client_timeout: int = 60
    provider_timeout: int = 30

    # API Keys (not required in settings, loaded by auth module)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Paths
    config_file: Path = BASE_DIR / "config.yaml"
    log_file: Path = BASE_DIR / "logs/proxy_api.log"

    class Config:
        env_prefix = "PROXY_API_"
        case_sensitive = False
        env_file = ".env"

from src.config.models import ProviderConfig

# Initialize settings
settings = Settings()

def load_providers_cfg(path: str) -> List[ProviderConfig]:
    with open(path, 'r') as f:
        raw = yaml.safe_load(f)
    return [ProviderConfig.model_validate(p) for p in raw["providers"]]
