import os
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

class AppConfig(BaseModel):
    name: str
    version: str
    environment: str

class ServerConfig(BaseModel):
    host: str
    port: int
    debug: bool
    reload: bool

class TelemetryConfig(BaseModel):
    enabled: bool
    service_name: str
    service_version: str
    jaeger: Dict[str, Any]
    zipkin: Dict[str, Any]
    sampling: Dict[str, Any]

class AuthConfig(BaseModel):
    api_keys: List[str] = Field(default_factory=list)
    api_keys_env: Optional[str] = None

class ProviderModel(BaseModel):
    name: str
    type: str
    api_key_env: str
    base_url: str
    models: List[str]
    enabled: bool
    forced: bool
    priority: int
    timeout: int
    max_retries: int
    max_connections: int
    max_keepalive_connections: int
    keepalive_expiry: float
    retry_delay: float
    custom_headers: Dict[str, str]

class UnifiedConfig(BaseModel):
    app: AppConfig
    server: ServerConfig
    telemetry: TelemetryConfig
    auth: AuthConfig
    providers: List[ProviderModel]
    rate_limit: Dict[str, Any]
    circuit_breaker: Dict[str, Any]
    condensation: Dict[str, Any]
    caching: Dict[str, Any]
    memory: Dict[str, Any]
    http_client: Dict[str, Any]
    logging: Dict[str, Any]
    health_check: Dict[str, Any]
    services: Dict[str, Any]
    load_testing: Dict[str, Any]
    network_simulation: Dict[str, Any]
    templates: Dict[str, Any]
    chaos_engineering: Dict[str, Any]

    @property
    def proxy_api_keys(self) -> List[str]:
        """
        Provides a unified way to get API keys, prioritizing environment variables
        over hardcoded keys in the config file.
        """
        if self.auth.api_keys_env:
            keys_from_env = os.getenv(self.auth.api_keys_env)
            if keys_from_env:
                # Split comma-separated keys and strip whitespace
                return [key.strip() for key in keys_from_env.split(',')]

        # Fallback to the list defined directly in the YAML
        return self.auth.api_keys
