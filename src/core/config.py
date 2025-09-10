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
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    proxy_api_keys: List[str] = []
    
    from pydantic import field_validator
    
    @field_validator('proxy_api_keys', mode='before')
    def parse_proxy_keys(cls, v):
        """Parse proxy_api_keys from string to list if necessary.
        Functionality: If env var is string (comma-separated or JSON), convert to list for validation.
        Potential issues: Assumes comma if str; for JSON, use json.loads. Handles empty.
        Optimizations: Make separator configurable or auto-detect."""
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                import json
                return json.loads(v)
            else:
                return [k.strip() for k in v.split(',') if k.strip()]
        return v

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Timeouts
    client_timeout: int = 60
    provider_timeout: int = 30

    # Resilience
    provider_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60  # seconds

    # Paths
    config_file: Path = BASE_DIR / "config.yaml"
    log_file: Path = BASE_DIR / "logs/proxy_api.log"

    class Config:
        env_prefix = "PROXY_API_"
        case_sensitive = False
        env_file = ".env"

from src.core.app_config import ProviderConfig

# Initialize settings
settings = Settings()

# Fix for env var loading as string instead of list; split comma-separated string if needed.
# Functionality: Ensures proxy_api_keys is always a list by splitting if it's a string from env.
# Potential issue: Assumes comma separator; if JSON or other, fails. Optimization: Use json.loads if starts with [.
if isinstance(settings.proxy_api_keys, str):
    settings.proxy_api_keys = [k.strip() for k in settings.proxy_api_keys.split(',') if k.strip()]

if not settings.proxy_api_keys:
    raise ValueError("Proxy API keys must be configured. At least one key is required for security.")

def load_providers_cfg(path: str) -> List[ProviderConfig]:
    with open(path, 'r') as f:
        raw = yaml.safe_load(f)
    providers_data = raw.get("providers", []) if raw else []
    return [ProviderConfig.model_validate(p) for p in providers_data]
