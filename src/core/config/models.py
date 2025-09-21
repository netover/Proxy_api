from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class AppConfig(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None

class ServerConfig(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    debug: Optional[bool] = None
    reload: Optional[bool] = None

class JaegerConfig(BaseModel):
    enabled: Optional[bool] = None
    endpoint: Optional[str] = None

class ZipkinConfig(BaseModel):
    enabled: Optional[bool] = None
    endpoint: Optional[str] = None

class SamplingConfig(BaseModel):
    probability: Optional[float] = None

class TelemetryConfig(BaseModel):
    enabled: Optional[bool] = None
    service_name: Optional[str] = None
    service_version: Optional[str] = None
    jaeger: Optional[JaegerConfig] = None
    zipkin: Optional[ZipkinConfig] = None
    sampling: Optional[SamplingConfig] = None

class TemplatesConfig(BaseModel):
    enabled: Optional[bool] = None
    directory: Optional[str] = None
    cache_size: Optional[int] = None
    auto_reload: Optional[bool] = None

class FaultConfig(BaseModel):
    type: Optional[str] = None
    severity: Optional[str] = None
    probability: Optional[float] = None
    duration_ms: Optional[int] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None

class ChaosEngineeringConfig(BaseModel):
    enabled: Optional[bool] = None
    faults: Optional[List[FaultConfig]] = []

class RateLimitConfig(BaseModel):
    requests_per_window: Optional[int] = None
    window_seconds: Optional[int] = None
    burst_limit: Optional[int] = None
    routes: Optional[Dict[str, str]] = {}
    default: Optional[str] = None

class ProviderConfig(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[List[str]] = []
    enabled: Optional[bool] = None
    forced: Optional[bool] = None
    priority: Optional[int] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    max_connections: Optional[int] = None
    max_keepalive_connections: Optional[int] = None
    keepalive_expiry: Optional[float] = None
    retry_delay: Optional[float] = None
    custom_headers: Optional[Dict[str, str]] = {}

class CircuitBreakerConfig(BaseModel):
    failure_threshold: Optional[int] = None
    recovery_timeout: Optional[int] = None
    half_open_max_calls: Optional[int] = None
    expected_exception: Optional[str] = None

class CondensationConfig(BaseModel):
    enabled: Optional[bool] = None
    truncation_threshold: Optional[int] = None
    summary_max_tokens: Optional[int] = None
    cache_size: Optional[int] = None
    cache_ttl: Optional[int] = None
    cache_persist: Optional[bool] = None
    cache_redis_url: Optional[str] = None
    error_patterns: Optional[List[str]] = []

class CacheSubConfig(BaseModel):
    max_size_mb: Optional[int] = None
    ttl: Optional[int] = None
    compression: Optional[bool] = None

class CachingConfig(BaseModel):
    enabled: Optional[bool] = None
    response_cache: Optional[CacheSubConfig] = None
    summary_cache: Optional[CacheSubConfig] = None

class MemoryConfig(BaseModel):
    max_usage_percent: Optional[int] = None
    gc_threshold_percent: Optional[int] = None
    monitoring_interval: Optional[int] = None
    cache_cleanup_interval: Optional[int] = None

class PoolLimitsConfig(BaseModel):
    max_connections: Optional[int] = None
    max_keepalive_connections: Optional[int] = None
    keepalive_timeout: Optional[int] = None

class HTTPClientConfig(BaseModel):
    timeout: Optional[int] = None
    connect_timeout: Optional[int] = None
    read_timeout: Optional[int] = None
    pool_limits: Optional[PoolLimitsConfig] = None

class LoggingRotationConfig(BaseModel):
    max_size_mb: Optional[int] = None
    max_files: Optional[int] = None

class LoggingConfig(BaseModel):
    level: Optional[str] = None
    format: Optional[str] = None
    file: Optional[str] = None
    rotation: Optional[LoggingRotationConfig] = None

class HealthCheckConfig(BaseModel):
    interval: Optional[int] = None

class ServicesConfig(BaseModel):
    context_service_url: Optional[str] = None
    timeout: Optional[int] = None
    providers: Optional[bool] = None
    context_service: Optional[bool] = None
    memory: Optional[bool] = None
    cache: Optional[bool] = None

class TierConfig(BaseModel):
    users: Optional[int] = None
    duration: Optional[str] = None
    ramp_up: Optional[str] = None
    expected_rps: Optional[int] = None

class LoadTestingConfig(BaseModel):
    tiers: Optional[Dict[str, TierConfig]] = {}

class ProfileConfig(BaseModel):
    min_delay: Optional[int] = None
    max_delay: Optional[int] = None
    jitter: Optional[float] = None

class NetworkSimulationConfig(BaseModel):
    profiles: Optional[Dict[str, ProfileConfig]] = {}

class UnifiedConfig(BaseModel):
    app: Optional[AppConfig] = None
    server: Optional[ServerConfig] = None
    telemetry: Optional[TelemetryConfig] = None
    templates: Optional[TemplatesConfig] = None
    chaos_engineering: Optional[ChaosEngineeringConfig] = Field(None, alias='chaos_engineering')
    rate_limit: Optional[RateLimitConfig] = Field(None, alias='rate_limit')
    providers: Optional[List[ProviderConfig]] = []
    circuit_breaker: Optional[CircuitBreakerConfig] = Field(None, alias='circuit_breaker')
    condensation: Optional[CondensationConfig] = None
    caching: Optional[CachingConfig] = None
    memory: Optional[MemoryConfig] = None
    http_client: Optional[HTTPClientConfig] = Field(None, alias='http_client')
    logging: Optional[LoggingConfig] = None
    health_check: Optional[HealthCheckConfig] = Field(None, alias='health_check')
    services: Optional[ServicesConfig] = None
    load_testing: Optional[LoadTestingConfig] = Field(None, alias='load_testing')
    network_simulation: Optional[NetworkSimulationConfig] = Field(None, alias='network_simulation')

    # This is where we would have loaded the keys if we didn't do it from env
    proxy_api_keys: List[str] = []

    class Config:
        populate_by_name = True
        extra = 'ignore' # Ignore extra fields in the yaml
