from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# ==============================================================================
# Refactored Models with Sensible Defaults
# ==============================================================================
# The previous implementation used Optional[T] = None extensively, which led to
# brittle code that required constant `if obj is not None:` checks. This also
# caused a critical bug where a missing `http_client` section in config.yaml
# would crash the application on startup.
#
# By providing default values and using default_factory for mutable types,
# we make the configuration robust and the application more stable. The code
# consuming this configuration can now safely access attributes without
# fearing a NoneType error.
# ==============================================================================

class AppConfig(BaseModel):
    name: str = "LLM Proxy API"
    version: str = "2.0.0"
    environment: str = "production"

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    reload: bool = False

class JaegerConfig(BaseModel):
    enabled: bool = False
    endpoint: str = "http://localhost:16686"

class ZipkinConfig(BaseModel):
    enabled: bool = False
    endpoint: str = "http://localhost:9411"

class SamplingConfig(BaseModel):
    probability: float = 0.1

class TelemetryConfig(BaseModel):
    enabled: bool = True
    service_name: str = "llm_proxy"
    service_version: str = "2.0.0"
    jaeger: JaegerConfig = Field(default_factory=JaegerConfig)
    zipkin: ZipkinConfig = Field(default_factory=ZipkinConfig)
    sampling: SamplingConfig = Field(default_factory=SamplingConfig)

class TemplatesConfig(BaseModel):
    enabled: bool = True
    directory: str = "templates"
    cache_size: int = 128
    auto_reload: bool = False

class FaultConfig(BaseModel):
    type: str = "latency"
    severity: str = "medium"
    probability: float = 0.01
    duration_ms: int = 100
    error_code: int = 500
    error_message: str = "Chaos monkey error"

class ChaosEngineeringConfig(BaseModel):
    enabled: bool = False
    faults: List[FaultConfig] = Field(default_factory=list)

class RateLimitConfig(BaseModel):
    requests_per_window: int = 100
    window_seconds: int = 60
    burst_limit: int = 120
    routes: Dict[str, str] = Field(default_factory=dict)
    default: str = "100/minute"
    redis_url: str = "redis://localhost:6379"
    strategy: str = "sliding_window"  # sliding_window, token_bucket
    enabled: bool = True

class ProviderConfig(BaseModel):
    name: str
    type: str
    api_key_env: str
    base_url: Optional[str] = None
    models: List[str] = Field(default_factory=list)
    enabled: bool = True
    forced: bool = False
    priority: int = 10
    timeout: int = 120
    max_retries: int = 2
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 60.0
    retry_delay: float = 1.0
    custom_headers: Dict[str, str] = Field(default_factory=dict)

class CircuitBreakerConfig(BaseModel):
    failure_threshold: int = 5
    recovery_timeout: int = 30
    half_open_max_calls: int = 10
    expected_exception: Optional[str] = None

class CondensationConfig(BaseModel):
    enabled: bool = False
    truncation_threshold: int = 4096
    summary_max_tokens: int = 512
    cache_size: int = 100
    cache_ttl: int = 3600
    cache_persist: bool = False
    cache_redis_url: Optional[str] = None
    error_patterns: List[str] = Field(default_factory=list)

class CacheSubConfig(BaseModel):
    max_size_mb: int = 100
    ttl: int = 300
    compression: bool = True

class CachingConfig(BaseModel):
    enabled: bool = True
    response_cache: CacheSubConfig = Field(default_factory=CacheSubConfig)
    summary_cache: CacheSubConfig = Field(default_factory=CacheSubConfig)

class MemoryConfig(BaseModel):
    max_usage_percent: int = 90
    gc_threshold_percent: int = 70
    monitoring_interval: int = 10
    cache_cleanup_interval: int = 60

class PoolLimitsConfig(BaseModel):
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_timeout: int = 60

class HTTPClientConfig(BaseModel):
    timeout: int = 30
    connect_timeout: int = 10
    read_timeout: int = 30
    pool_limits: PoolLimitsConfig = Field(default_factory=PoolLimitsConfig)

class LoggingRotationConfig(BaseModel):
    max_size_mb: int = 100
    max_files: int = 10

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    rotation: LoggingRotationConfig = Field(default_factory=LoggingRotationConfig)

class HealthCheckConfig(BaseModel):
    interval: int = 30

class ServicesConfig(BaseModel):
    context_service_url: Optional[str] = None
    timeout: int = 10
    providers: bool = True
    context_service: bool = True
    memory: bool = True
    cache: bool = True

class TierConfig(BaseModel):
    users: int = 1
    duration: str = "1m"
    ramp_up: str = "10s"
    expected_rps: int = 10

class LoadTestingConfig(BaseModel):
    tiers: Dict[str, TierConfig] = Field(default_factory=dict)

class ProfileConfig(BaseModel):
    min_delay: int = 50
    max_delay: int = 150
    jitter: float = 0.1

class NetworkSimulationConfig(BaseModel):
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict)

class CorsConfig(BaseModel):
    enabled: bool = True
    allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    allow_headers: List[str] = Field(default_factory=lambda: ["*"])

class UnifiedConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    templates: TemplatesConfig = Field(default_factory=TemplatesConfig)
    chaos_engineering: ChaosEngineeringConfig = Field(default_factory=ChaosEngineeringConfig, alias='chaos_engineering')
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig, alias='rate_limit')
    providers: List[ProviderConfig] = Field(default_factory=list)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig, alias='circuit_breaker')
    condensation: CondensationConfig = Field(default_factory=CondensationConfig)
    caching: CachingConfig = Field(default_factory=CachingConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    http_client: HTTPClientConfig = Field(default_factory=HTTPClientConfig, alias='http_client')
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    services: ServicesConfig = Field(default_factory=ServicesConfig)
    load_testing: LoadTestingConfig = Field(default_factory=LoadTestingConfig, alias='load_testing')
    network_simulation: NetworkSimulationConfig = Field(default_factory=NetworkSimulationConfig)

    proxy_api_keys: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        extra = 'ignore'