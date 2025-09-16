import asyncio
import os
import re
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    validator,
    ConfigDict,
)

from .logging import ContextualLogger

logger = ContextualLogger(__name__)

# --- Environment Variable Handling ---

ENV_VAR_MATCHER = re.compile(r"\$\{(\w+)\}")

def env_var_constructor(loader, node):
    """Constructor for PyYAML to substitute environment variables."""
    value = loader.construct_scalar(node)
    match = ENV_VAR_MATCHER.match(value)
    if match:
        env_var = match.group(1)
        # Return the value of the environment variable, or None if not set.
        return os.getenv(env_var)
    return value

# Add the constructor to the default PyYAML loader
yaml.add_constructor("!env", env_var_constructor, Loader=yaml.FullLoader)
yaml.add_implicit_resolver("!env", ENV_VAR_MATCHER, first="$", Loader=yaml.FullLoader)


# --- Pydantic Models for Configuration ---

class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    PERPLEXITY = "perplexity"
    GROK = "grok"
    BLACKBOX = "blackbox"
    OPENROUTER = "openrouter"
    COHERE = "cohere"


class ProviderConfig(BaseModel):
    name: str
    type: ProviderType
    api_key_env: str
    base_url: Optional[str] = None
    models: List[str]
    enabled: bool = True
    forced: bool = False
    priority: int = 10
    timeout: int = 30
    max_retries: int = 3
    max_connections: int = 50
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0
    retry_delay: float = 1.0
    custom_headers: Dict[str, str] = Field(default_factory=dict)

class RateLimitSettings(BaseModel):
    requests_per_window: int
    window_seconds: int
    burst_limit: int
    routes: Dict[str, str]

class AuthSettings(BaseModel):
    api_keys: List[str]

class CondensationSettings(BaseModel):
    enabled: bool = True
    truncation_threshold: int = 8000
    summary_max_tokens: int = 512
    cache_size: int = 1000
    cache_ttl: int = 3600
    cache_persist: bool = True
    cache_redis_url: Optional[str] = None
    error_patterns: List[str] = Field(default_factory=list)

class CachingSettings(BaseModel):
    enabled: bool = True
    response_cache: Dict[str, Any]
    summary_cache: Dict[str, Any]

class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False

class GlobalSettings(BaseModel):
    name: str = "LLM Proxy API"
    version: str = "2.0.0"
    environment: str = "production"
    cors_origins: List[str] = Field(default=["*"], alias="allowed_origins")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class UnifiedConfig(BaseModel):
    app: GlobalSettings
    server: ServerSettings
    telemetry: Dict[str, Any]
    templates: Dict[str, Any]
    chaos_engineering: Dict[str, Any]
    rate_limit: RateLimitSettings
    auth: AuthSettings
    providers: List[ProviderConfig]
    circuit_breaker: Dict[str, Any]
    condensation: CondensationSettings
    caching: CachingSettings
    memory: Dict[str, Any]
    http_client: Dict[str, Any]
    logging: Dict[str, Any]
    health_check: Dict[str, Any]
    services: Dict[str, Any]

    @property
    def proxy_api_keys(self) -> List[str]:
        """Convenience property to access API keys directly."""
        return self.auth.api_keys


class ConfigManager:
    """Simplified configuration manager as the single source of truth."""

    def __init__(self, config_path: Union[str, Path]):
        self.config_path = Path(config_path)
        self._config: Optional[UnifiedConfig] = None
        self._last_modified: float = 0

    def load_config(self, force_reload: bool = False) -> UnifiedConfig:
        """Loads the config from YAML, handling env vars and validation."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")

        # Check if file has been modified
        mtime = self.config_path.stat().st_mtime
        if self._config and not force_reload and mtime <= self._last_modified:
            return self._config

        logger.info(f"Loading configuration from {self.config_path}")
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_config = yaml.load(f, Loader=yaml.FullLoader)

            self._config = UnifiedConfig.model_validate(raw_config)
            self._last_modified = mtime
            logger.info("Configuration loaded and validated successfully.")
            return self._config
        except (yaml.YAMLError, ValueError) as e:
            logger.error(f"Failed to load or validate configuration: {e}")
            raise

# Global instance, to be initialized in the application
config_manager: Optional[ConfigManager] = None

def get_config() -> UnifiedConfig:
    """Global accessor for the config."""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager(config_path="config.yaml")
    return config_manager.load_config()
