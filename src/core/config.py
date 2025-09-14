from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings

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

    @field_validator('proxy_api_keys', mode='before')
    @classmethod
    def parse_proxy_keys(cls, v):
        """Parse proxy_api_keys from string to list if necessary.

        Handles multiple input formats:
        - Comma-separated string: "key1,key2,key3"
        - JSON array string: "['key1','key2','key3']"
        - List: ['key1', 'key2', 'key3']
        - Empty/None values are filtered out
        """
        if isinstance(v, str):
            v = v.strip()
            if not v:  # Empty string
                return []
            if v.startswith('[') and v.endswith(']'):
                # JSON array format
                import json
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(k).strip() for k in parsed if k and str(k).strip()]
                    else:
                        return [str(parsed).strip()] if parsed else []
                except json.JSONDecodeError:
                    # Fallback to comma-separated if JSON parsing fails
                    return [k.strip() for k in v.split(',') if k.strip()]
            else:
                # Comma-separated format
                return [k.strip() for k in v.split(',') if k.strip()]
        elif isinstance(v, list):
            # Already a list, clean it up
            return [str(k).strip() for k in v if k and str(k).strip()]
        else:
            # Other types, convert to string and process
            return cls.parse_proxy_keys(str(v)) if v else []

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

    # Export Dataset Settings
    export_default_log_file: Path = BASE_DIR / "logs/proxy_api.log"
    export_default_output_dir: Path = BASE_DIR / "exports"
    export_default_output_file: str = "dataset.jsonl"
    export_max_records: Optional[int] = None
    export_successful_only: bool = False
    export_export_all: bool = False
    export_start_date: Optional[str] = None
    export_end_date: Optional[str] = None
    export_model_filter: Optional[str] = None
    export_log_level: str = "INFO"

    model_config = {
        "env_prefix": "PROXY_API_",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "allow",
    }

from src.core.app_config import ProviderConfig

# Initialize settings
settings = Settings()

# Validate that proxy API keys are configured
if not settings.proxy_api_keys:
    raise ValueError("Proxy API keys must be configured. At least one key is required for security.")

def load_providers_cfg(path: str) -> List[ProviderConfig]:
    with open(path, 'r') as f:
        raw = yaml.safe_load(f)
    providers_data = raw.get("providers", []) if raw else []
    return [ProviderConfig.model_validate(p) for p in providers_data]
