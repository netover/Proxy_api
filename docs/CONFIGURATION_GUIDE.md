# ProxyAPI Configuration and Environment Setup Guide

Complete guide to configuring ProxyAPI, including YAML configuration files, environment variables, provider setups, monitoring, and deployment procedures.

## Table of Contents

- [Configuration Files Overview](#configuration-files-overview)
- [Environment Variables](#environment-variables)
- [Provider Configuration](#provider-configuration)
- [Rate Limiting Configuration](#rate-limiting-configuration)
- [Cache Settings Configuration](#cache-settings-configuration)
- [Logging Configuration](#logging-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Configuration Validation](#configuration-validation)
- [Hot Reloading Capabilities](#hot-reloading-capabilities)
- [Setup Guides](#setup-guides)
- [Deployment Scenarios](#deployment-scenarios)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Configuration Files Overview

ProxyAPI uses multiple configuration files and sources to provide flexible configuration management:

### Primary Configuration Files

#### 1. YAML Configuration (`config.yaml`)
The main configuration file for providers, caching, and system settings. Supports both external (user-editable) and bundled (read-only) versions.

**Location Priority:**
1. `./config.yaml` (external, editable)
2. `./config.json` (external, JSON format)
3. Bundled `config.yaml` (in executable, read-only)
4. Auto-generated default configuration

#### 2. Environment Variables (`.env`)
Environment-specific variables loaded via python-dotenv.

**Default location:** `.env` in project root
**Prefix:** `PROXY_API_` for application settings

#### 3. Model Selections (`config/model_selections.json`)
Persistent storage for user-selected default models per provider.

```json
{
  "openai": {
    "model_name": "gpt-3.5-turbo",
    "editable": true,
    "last_updated": "2025-09-12T03:54:29.931051"
  }
}
```

#### 4. Production Configuration (`production_config.py`)
Python-based configuration for production deployments with environment overrides.

### Configuration Loading Order

1. **Environment Variables** (highest priority)
2. **External YAML/JSON** (user-editable)
3. **Bundled Configuration** (fallback)
4. **Default Configuration** (auto-generated)

### Legacy Configuration Compatibility

ProxyAPI includes a comprehensive compatibility layer for handling legacy configuration formats during migration and upgrades. The compatibility layer automatically detects and migrates old configuration schemas to the current format.

#### Supported Legacy Formats

1. **Legacy Model Selections JSON**
   - **Old Format**: `{"provider": "model_name"}`
   - **New Format**: `{"provider": {"model_name": "...", "editable": true, "last_updated": "..."}}`

2. **Legacy YAML Configuration**
   - **Old Format**: Flat structure with different key names
   - **New Format**: Nested structure with standardized schema

3. **Legacy Python Configuration**
   - **Old Format**: Different key names and structure
   - **New Format**: Standardized Python configuration

#### Automatic Migration Features

- **Transparent Migration**: Legacy configurations are automatically detected and migrated
- **Backup Creation**: Original files are backed up with `.legacy` suffix
- **Deprecation Warnings**: Clear warnings when legacy formats are detected
- **Rollback Support**: Ability to rollback migrations if needed
- **Migration History**: Tracking of all migration operations
- **Zero Downtime**: Migration occurs without service interruption

#### Migration Commands

```python
from src.core.config_compatibility import (
    migrate_specific_format,
    rollback_format,
    check_legacy_presence,
    get_migration_report
)

# Check for legacy formats
legacy_status = check_legacy_presence()
print(legacy_status)

# Migrate specific format
success = migrate_specific_format('model_selections')

# Rollback if needed
rollback_format('model_selections')

# Get comprehensive report
report = get_migration_report()
print(report)
```

#### Migration Best Practices

1. **Backup First**: Always backup configurations before migration
2. **Test Migration**: Test migrated configurations in staging environment
3. **Gradual Rollout**: Migrate configurations gradually across environments
4. **Monitor Closely**: Monitor application behavior after migration
5. **Document Changes**: Keep records of migration operations
6. **Plan Rollback**: Have rollback procedures ready

#### Migration Status Monitoring

The compatibility layer provides comprehensive status monitoring:

```python
# Get migration status
status = get_migration_status()
print(f"Migration enabled: {status['migration_enabled']}")
print(f"Legacy formats detected: {status['legacy_formats_detected']}")
print(f"Migration needed: {status['migration_needed']}")
```

#### Configuration Compatibility Integration

The compatibility layer integrates seamlessly with the main configuration system:

```python
from src.core.config_compatibility import load_config_with_legacy_support

# Load configuration with legacy support
config = load_config_with_legacy_support()
```

This ensures that existing deployments continue to work while providing a smooth migration path to the new configuration format.

### Quick Start Configuration

#### Minimal Development Setup

```yaml
# config.yaml
providers:
  - name: "openai"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo", "gpt-4"]
    enabled: true
    priority: 1
    timeout: 30

condensation:
  max_tokens_default: 512
```

```bash
# .env
OPENAI_API_KEY=sk-your-key-here
PROXY_API_HOST=127.0.0.1
PROXY_API_PORT=8000
```

#### Production Setup

```yaml
# config.yaml
providers:
  - name: "openai"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    enabled: true
    priority: 1
    timeout: 30
    rate_limit: 1000
    retry_attempts: 3
    max_connections: 100
    max_keepalive_connections: 50
    keepalive_expiry: 30.0

  - name: "anthropic"
    type: "anthropic"
    base_url: "https://api.anthropic.com"
    api_key_env: "ANTHROPIC_API_KEY"
    models: ["claude-3-haiku", "claude-3-sonnet"]
    enabled: true
    priority: 2
    timeout: 30
    rate_limit: 50
    retry_attempts: 3

condensation:
  max_tokens_default: 512
  error_keywords: ["context_length_exceeded", "maximum context length"]
  adaptive_factor: 0.5
  cache_ttl: 300
```

## Exemplo de Configuração Abrangente

Este exemplo demonstra uma configuração mais complexa e realista, com múltiplos provedores, overrides de modelo e configurações de fallback.

```yaml
# config.yaml

app:
  name: "ProxyAPI Enterprise"
  version: "2.1.0"

server:
  host: "0.0.0.0"
  port: 8000

auth:
  api_keys:
    - "prod-key-12345"
    - "dev-key-67890"

providers:
  - name: "openai-gpt4"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    models:
      - "gpt-4-turbo"
      - "gpt-4"
    enabled: true
    priority: 1
    timeout: 45
    max_retries: 3
    fallback_provider: "anthropic-claude3"

  - name: "anthropic-claude3"
    type: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      - "claude-3-opus-20240229"
      - "claude-3-sonnet-20240229"
    enabled: true
    priority: 2
    timeout: 60

  - name: "google-gemini"
    type: "google"
    api_key_env: "GOOGLE_API_KEY"
    models:
      - "gemini-1.5-pro-latest"
    enabled: false # Temporarily disabled
    priority: 3

model_overrides:
  "gpt-4-turbo":
    max_tokens: 8192
    temperature: 0.8
    presence_penalty: 0.1

caching:
  enabled: true
  response_cache:
    max_size_mb: 256
    ttl: 3600 # 1 hour
  summary_cache:
    max_size_mb: 128
    ttl: 86400 # 24 hours

rate_limit:
  requests_per_window: 2000
  window_seconds: 60
  routes:
    "/v1/chat/completions": "500/minute"
    "/v1/embeddings": "1000/minute"

```

## Core Application Settings

### Application Configuration

```yaml
app:
  name: "LLM Proxy API"          # Application name
  version: "2.0.0"               # Application version
  environment: "production"      # Environment (development/staging/production)
  debug: false                   # Enable debug mode
```

### Server Configuration

```yaml
server:
  host: "0.0.0.0"               # Server bind address
  port: 8000                     # Server port
  debug: false                   # Enable debug mode
  reload: false                  # Auto-reload on code changes
  workers: 4                     # Number of worker processes
  worker_class: "uvicorn.workers.UvicornWorker"  # Worker class
  max_requests: 1000             # Max requests per worker
  max_requests_jitter: 50        # Jitter for max requests
```

### Authentication Configuration

```yaml
auth:
  # API Key authentication
  api_keys:
    - "key1"                     # Static API keys
    - "key2"
    - "${API_KEY_ENV}"           # Environment variable

  # JWT authentication (optional)
  jwt:
    enabled: false
    secret_key: "${JWT_SECRET}"
    algorithm: "HS256"
    expiration_hours: 24

  # OAuth2 (optional)
  oauth2:
    enabled: false
    provider: "google"
    client_id: "${OAUTH_CLIENT_ID}"
    client_secret: "${OAUTH_CLIENT_SECRET}"
```

## Provider Configuration

ProxyAPI supports multiple LLM providers with unified configuration. Provider configurations are defined in the YAML config file and validated against the `ProviderConfig` Pydantic model.

### Supported Providers

- `openai` - OpenAI API
- `anthropic` - Anthropic API
- `azure_openai` - Azure OpenAI Service
- `cohere` - Cohere API
- `perplexity` - Perplexity API
- `grok` - Grok API
- `blackbox` - Blackbox AI
- `openrouter` - OpenRouter API

### Provider Configuration Schema

Each provider requires these fields:
- `name`: Unique provider identifier
- `type`: Provider type (from supported list above)
- `api_key_env`: Environment variable containing API key
- `base_url`: Provider API base URL
- `models`: List of supported models

Optional fields:
- `enabled`: Enable/disable provider (default: true)
- `priority`: Provider priority (1-1000, lower = higher priority)
- `timeout`: Request timeout in seconds (default: 30)
- `rate_limit`: Requests per hour (default: 1000)
- `retry_attempts`: Number of retries (default: 3)
- `retry_delay`: Delay between retries in seconds (default: 1.0)
- `headers`: Additional HTTP headers
- `max_connections`: Maximum connections (default: 100)
- `max_keepalive_connections`: Maximum keep-alive connections (default: 100)
- `keepalive_expiry`: Keep-alive expiry in seconds (default: 30.0)

### Provider Examples

#### OpenAI Provider

```yaml
providers:
  - name: "openai"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models:
      - "gpt-3.5-turbo"
      - "gpt-4"
      - "gpt-4-turbo"
      - "gpt-4o"
    enabled: true
    priority: 1
    timeout: 30
    rate_limit: 1000
    retry_attempts: 3
    retry_delay: 1.0
    max_connections: 100
    max_keepalive_connections: 50
    keepalive_expiry: 30.0
    headers:
      "X-Client-Type": "llm-proxy"
```

#### Anthropic Provider

```yaml
providers:
  - name: "anthropic"
    type: "anthropic"
    base_url: "https://api.anthropic.com"
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      - "claude-3-haiku"
      - "claude-3-sonnet"
      - "claude-3-opus"
      - "claude-3-5-sonnet"
    enabled: true
    priority: 2
    timeout: 30
    rate_limit: 50
    retry_attempts: 3
    max_connections: 50
    max_keepalive_connections: 25
    keepalive_expiry: 30.0
```

#### Azure OpenAI Provider

```yaml
providers:
  - name: "azure"
    type: "azure_openai"
    base_url: "https://your-resource.openai.azure.com/"
    api_key_env: "AZURE_OPENAI_KEY"
    models:
      - "gpt-35-turbo"
      - "gpt-4"
      - "gpt-4-turbo"
    enabled: true
    priority: 3
    timeout: 30
    rate_limit: 1000
    retry_attempts: 3
    headers:
      "api-version": "2023-12-01-preview"
```

#### Grok Provider

```yaml
providers:
  - name: "grok"
    type: "grok"
    base_url: "https://api.x.ai/v1"
    api_key_env: "GROK_API_KEY"
    models:
      - "grok-beta"
    enabled: true
    priority: 4
    timeout: 30
    rate_limit: 100
    retry_attempts: 3
```

### Provider Priority and Fallback

Providers are selected based on priority (lower number = higher priority). The system automatically falls back to lower-priority providers if higher-priority ones fail.

```yaml
providers:
  - name: "openai-primary"
    type: "openai"
    priority: 1        # Highest priority
    enabled: true

  - name: "anthropic-fallback"
    type: "anthropic"
    priority: 2        # Fallback provider
    enabled: true

  - name: "openai-secondary"
    type: "openai"
    priority: 3        # Last resort
    enabled: true
```

### Provider-Specific Settings

#### Connection Pool Configuration

```yaml
providers:
  - name: "high-throughput-provider"
    type: "openai"
    max_connections: 500
    max_keepalive_connections: 200
    keepalive_expiry: 60.0
    timeout: 60
```

#### Custom Headers

```yaml
providers:
  - name: "custom-provider"
    type: "openai"
    headers:
      "X-Organization": "your-org-id"
      "X-Client-Version": "1.0.0"
      "X-Environment": "production"
```

### Provider Validation

The configuration validates:
- Unique provider names
- Unique priorities
- Supported provider types
- Valid model lists (at least one model)
- Valid URL formats
- Environment variable naming conventions

At startup, the system validates provider credentials and connectivity if configured to do so.

## Rate Limiting Configuration

ProxyAPI implements rate limiting at multiple levels to protect against abuse and ensure fair usage.

### Global Rate Limiting

Configured via environment variables in `src/core/config.py`:

```python
# Rate Limiting
rate_limit_requests: int = 100        # Requests per window
rate_limit_window: int = 60           # Time window in seconds
```

Environment variables:
```bash
PROXY_API_RATE_LIMIT_REQUESTS=100     # Requests per window
PROXY_API_RATE_LIMIT_WINDOW=60        # Window in seconds
```

### Provider-Specific Rate Limiting

Configured per provider in YAML configuration:

```yaml
providers:
  - name: "openai"
    type: "openai"
    rate_limit: 1000                  # Requests per hour
    # ... other config

  - name: "anthropic"
    type: "anthropic"
    rate_limit: 50                    # Requests per hour (Anthropic limit)
```

### Rate Limiting Implementation

Rate limiting is enforced by the `rate_limiter.py` module using in-memory storage. The system tracks requests per user/API key and enforces limits globally and per-provider.

## Cache Settings Configuration

ProxyAPI implements multi-level caching for performance optimization.

### Response Cache

Configured in `production_config.py`:

```python
"cache": {
    "response_cache_size": int(os.getenv("RESPONSE_CACHE_SIZE", "10000")),
    "response_cache_ttl": int(os.getenv("RESPONSE_CACHE_TTL", "1800")),
    "summary_cache_size": int(os.getenv("SUMMARY_CACHE_SIZE", "2000")),
    "summary_cache_ttl": int(os.getenv("SUMMARY_CACHE_TTL", "3600")),
    "max_memory_mb": int(os.getenv("CACHE_MAX_MEMORY_MB", "512")),
}
```

### Context Condensation Cache

Configured in YAML:

```yaml
condensation:
  max_tokens_default: 512             # Default max tokens
  error_keywords:                     # Keywords to detect errors
    - "context_length_exceeded"
    - "maximum context length"
  adaptive_factor: 0.5                # Adaptive adjustment factor
  cache_ttl: 300                      # Cache TTL in seconds
```

### Cache Implementation

ProxyAPI uses multiple cache systems:
- **Response Cache**: Caches API responses
- **Summary Cache**: Caches context summaries
- **Model Cache**: Caches model information
- **Memory Manager**: Manages memory usage across caches

### Cache Warming

The system supports cache warming for popular models and responses to improve cold start performance.

## Logging Configuration

ProxyAPI supports structured logging with multiple output formats and levels.

### Logging Configuration

From `production_config.py`:

```python
"logging": {
    "level": os.getenv("LOG_LEVEL", "WARNING" if IS_PRODUCTION else "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "app.log",
    "max_file_size": int(os.getenv("LOG_MAX_SIZE", "100")),
    "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "10")),
    "json_format": os.getenv("LOG_JSON_FORMAT", "true").lower() == "true",
}
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Structured Logging

When `LOG_JSON_FORMAT=true`, logs are output in JSON format for better parsing by log aggregation systems.

### Log Rotation

Logs are automatically rotated based on size:
- Max file size: 100MB (configurable)
- Backup count: 10 files (configurable)

## Monitoring Setup

ProxyAPI integrates with Prometheus, Grafana, and systemd for comprehensive monitoring.

### Prometheus Metrics

The system exposes metrics at `/metrics` endpoint. Available metrics include:

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration histogram
- `llm_requests_total`: Total LLM API calls
- `llm_tokens_total`: Total tokens processed
- `cache_hits_total`: Cache hit counter
- `cache_misses_total`: Cache miss counter
- `context_condensations_total`: Total condensation operations
- `health_checks_total`: Total health checks performed
- `provider_status`: Current provider status (0=unhealthy, 1=healthy)

### Grafana Dashboard

A pre-configured dashboard is available in `monitoring/grafana-dashboard.json` with:
- Request rate and latency graphs
- Cache hit/miss ratios
- Provider health status
- System resource usage
- Error rate monitoring

### Monitoring Setup

From `monitoring/README.md`:

```bash
# Install Prometheus
sudo apt-get install prometheus

# Install Grafana
sudo apt-get install grafana

# Install Node Exporter for system metrics
sudo apt-get install prometheus-node-exporter

# Copy configuration files
sudo cp monitoring/prometheus.yml /etc/prometheus/prometheus.yml
sudo cp monitoring/grafana-dashboard.json /var/lib/grafana/dashboards/

# Start services
sudo systemctl start prometheus grafana-server prometheus-node-exporter
```

### Alerting

Prometheus alerting rules are configured in `/etc/prometheus/alert_rules.yml`:

```yaml
groups:
  - name: llm_proxy_alerts
    rules:
      - alert: LLMProxyDown
        expr: up{job="llm-proxy"} == 0
        for: 5m
        labels:
          severity: critical

      - alert: HighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 90
        for: 5m
        labels:
          severity: warning
```

### Health Checks

Health checks are performed automatically and available at `/health` endpoints:
- `/health/live`: Liveness probe
- `/health/ready`: Readiness probe
- `/health`: Detailed health status

### Memory Management

```yaml
memory:
  # Memory limits
  max_usage_percent: 85               # Maximum memory usage percentage
  gc_threshold_percent: 80            # GC threshold percentage
  emergency_threshold_percent: 95     # Emergency cleanup threshold

  # Monitoring
  monitoring_interval: 30             # Memory check interval
  cache_cleanup_interval: 300         # Cache cleanup interval

  # GC tuning
  gc_tuning:
    enabled: true                     # Enable GC tuning
    generation0_threshold: 700        # Generation 0 threshold
    generation1_threshold: 10         # Generation 1 threshold
    generation2_threshold: 10         # Generation 2 threshold

  # Memory profiling
  profiling:
    enabled: false                    # Enable memory profiling
    dump_on_high_usage: true          # Dump memory on high usage
    profile_interval: 300             # Profiling interval
```

## Monitoring & Observability

### OpenTelemetry Configuration

```yaml
telemetry:
  enabled: true                       # Enable OpenTelemetry
  service_name: "llm-proxy"           # Service name
  service_version: "2.0.0"            # Service version

  # Jaeger exporter
  jaeger:
    enabled: true
    endpoint: "http://localhost:14268/api/traces"
    username: "${JAEGER_USER}"        # Optional
    password: "${JAEGER_PASS}"        # Optional

  # Zipkin exporter
  zipkin:
    enabled: true
    endpoint: "http://localhost:9411/api/v2/spans"

  # OTLP exporter
  otlp:
    enabled: false
    endpoint: "http://localhost:4317"
    headers:
      authorization: "Bearer ${OTLP_TOKEN}"

  # Sampling
  sampling:
    probability: 1.0                  # Sampling probability (0.0-1.0)
    parent_based: true                # Parent-based sampling
    rules:                            # Custom sampling rules
      - service: "llm-proxy"
        probability: 0.1

  # Resource attributes
  resource:
    environment: "${ENVIRONMENT}"
    region: "${REGION}"
    cluster: "${CLUSTER}"
```

### Logging Configuration

```yaml
logging:
  # Basic settings
  level: "INFO"                       # Log level (DEBUG, INFO, WARNING, ERROR)
  format: "json"                      # Log format (json, text)
  file: "logs/app.log"                # Log file path
  max_file_size: "100MB"              # Maximum file size
  max_files: 5                        # Maximum number of files

  # Advanced settings
  rotation: "daily"                   # Rotation policy (daily, size, time)
  compression: "gzip"                 # Log compression
  encoding: "utf-8"                   # Log encoding

  # Structured logging
  structured:
    enabled: true                     # Enable structured logging
    include_trace_id: true            # Include trace ID
    include_span_id: true             # Include span ID
    include_request_id: true          # Include request ID

  # Log filtering
  filters:
    - type: "level"                   # Filter by level
      level: "WARNING"
    - type: "module"                  # Filter by module
      modules: ["src.core.http_client"]
    - type: "message"                 # Filter by message content
      patterns: ["error", "timeout"]

  # External logging
  external:
    # Loki configuration
    loki:
      enabled: false
      url: "http://localhost:3100/loki/api/v1/push"
      labels:
        app: "llm-proxy"
        environment: "${ENVIRONMENT}"

    # Elasticsearch configuration
    elasticsearch:
      enabled: false
      hosts: ["localhost:9200"]
      index: "llm-proxy-logs"
      username: "${ES_USER}"
      password: "${ES_PASS}"
```

### Metrics Configuration

```yaml
metrics:
  enabled: true                       # Enable metrics collection

  # Prometheus configuration
  prometheus:
    enabled: true
    port: 9090                        # Prometheus port
    path: "/metrics"                  # Metrics path
    registry: "default"               # Metrics registry

  # Custom metrics
  custom:
    enabled: true
    prefix: "llm_proxy"               # Metric prefix
    labels:
      environment: "${ENVIRONMENT}"
      region: "${REGION}"

  # Metrics collection
  collection:
    interval: 30                      # Collection interval in seconds
    timeout: 10                       # Collection timeout in seconds

  # Alerting
  alerting:
    enabled: true
    rules:
      - name: "high_error_rate"
        condition: "error_rate > 0.05"
        severity: "warning"
        description: "Error rate is above 5%"
      - name: "high_latency"
        condition: "avg_response_time > 5000"
        severity: "critical"
        description: "Average response time is above 5 seconds"
```

### Health Check Configuration

```yaml
health_check:
  enabled: true                       # Enable health checks
  interval: 30                        # Check interval in seconds
  timeout: 5                          # Check timeout in seconds
  unhealthy_threshold: 3              # Failures before marking unhealthy

  # Component checks
  checks:
    providers: true                   # Check provider connectivity
    cache: true                       # Check cache health
    database: false                   # Check database connectivity
    external_services: true           # Check external service health

  # Detailed checks
  detailed:
    enabled: true                     # Enable detailed health checks
    include_metrics: true             # Include metrics in health response
    include_config: false             # Include config validation

  # Health endpoints
  endpoints:
    liveness: "/health/live"          # Liveness probe endpoint
    readiness: "/health/ready"        # Readiness probe endpoint
    detailed: "/health"               # Detailed health endpoint
```

## Security Configuration

### Rate Limiting

```yaml
rate_limit:
  enabled: true                       # Enable rate limiting

  # Global limits
  requests_per_window: 1000           # Requests per time window
  window_seconds: 60                  # Time window in seconds
  burst_limit: 50                     # Burst limit

  # Provider-specific limits
  providers:
    openai:
      requests_per_minute: 60         # OpenAI rate limit
      burst_limit: 10
    anthropic:
      requests_per_minute: 40         # Anthropic rate limit
      burst_limit: 5

  # IP-based limits
  ip_limits:
    enabled: true
    requests_per_minute: 100          # Per IP limit
    whitelist:
      - "192.168.1.0/24"              # Whitelisted IP ranges
    blacklist:
      - "10.0.0.0/8"                  # Blacklisted IP ranges

  # User-based limits
  user_limits:
    enabled: true
    requests_per_minute: 500          # Per user limit
    burst_limit: 20

  # Response headers
  headers:
    enabled: true                     # Include rate limit headers
    remaining: "X-RateLimit-Remaining"
    reset: "X-RateLimit-Reset"
    retry_after: "Retry-After"
```

### Circuit Breaker

```yaml
circuit_breaker:
  enabled: true                       # Enable circuit breaker

  # Global settings
  failure_threshold: 5                # Failures before opening
  recovery_timeout: 60                # Recovery timeout in seconds
  half_open_max_calls: 3              # Max calls in half-open state
  expected_exception: "ProviderError" # Expected exception type

  # Provider-specific settings
  providers:
    openai:
      failure_threshold: 3
      recovery_timeout: 30
    anthropic:
      failure_threshold: 5
      recovery_timeout: 60

  # Monitoring
  monitoring:
    enabled: true
    metrics: true                     # Export circuit breaker metrics
    alerts: true                      # Enable circuit breaker alerts
```

### Input Validation

```yaml
validation:
  enabled: true                       # Enable input validation

  # Request validation
  request:
    max_body_size: "10MB"             # Maximum request body size
    allowed_content_types:            # Allowed content types
      - "application/json"
      - "application/x-www-form-urlencoded"
    required_headers:                 # Required headers
      - "Content-Type"
      - "Authorization"

  # Response validation
  response:
    validate_schema: true             # Validate response schema
    sanitize_output: true             # Sanitize output data
    max_response_size: "50MB"         # Maximum response size

  # Content filtering
  content_filter:
    enabled: true
    rules:
      - type: "keyword"               # Keyword filtering
        keywords: ["password", "secret", "key"]
      - type: "regex"                 # Regex filtering
        patterns: ["\\b\\d{16}\\b"]   # Credit card numbers
```

## Load Testing & Chaos Engineering

### Load Testing Configuration

```yaml
load_testing:
  enabled: true                       # Enable load testing

  # Test tiers
  tiers:
    light:
      users: 30                       # Number of virtual users
      duration: "5m"                  # Test duration
      ramp_up: "30s"                  # Ramp-up time
      expected_rps: 5                 # Expected requests per second
      scenarios: ["chat_completion"]  # Test scenarios

    medium:
      users: 100
      duration: "5m"
      ramp_up: "1m"
      expected_rps: 20
      scenarios: ["chat_completion", "model_discovery"]

    heavy:
      users: 400
      duration: "15m"
      ramp_up: "5m"
      expected_rps: 80
      scenarios: ["chat_completion", "model_discovery", "summarization"]

    extreme:
      users: 1000
      duration: "20m"
      ramp_up: "10m"
      expected_rps: 200
      scenarios: ["all"]

  # Test scenarios
  scenarios:
    chat_completion:
      weight: 70                      # Scenario weight (percentage)
      model: "gpt-3.5-turbo"
      max_tokens: 100
      temperature: 0.7

    model_discovery:
      weight: 20
      filters:
        provider: "openai"
        supports_chat: true

    summarization:
      weight: 10
      input_length: 4000
      max_tokens: 512

  # Test configuration
  config:
    timeout: 30                       # Request timeout
    think_time: "1s"                  # Think time between requests
    random_seed: 12345                # Random seed for reproducibility

  # Reporting
  reporting:
    enabled: true
    format: ["json", "html", "csv"]   # Report formats
    output_dir: "reports/load_tests"  # Output directory
    include_charts: true              # Include performance charts
    include_raw_data: true            # Include raw test data
```

### Chaos Engineering Configuration

```yaml
chaos_engineering:
  enabled: false                      # Enable chaos engineering (use carefully!)

  # Fault types
  faults:
    - type: "delay"                   # Network delay
      severity: "medium"
      probability: 0.1                # 10% chance
      duration_ms: 500                # 500ms delay
      target: "all"                   # Target all providers

    - type: "error"                   # HTTP error injection
      severity: "low"
      probability: 0.05               # 5% chance
      error_code: 503                 # Service unavailable
      error_message: "Service temporarily unavailable"
      target: "openai"

    - type: "rate_limit"              # Rate limit injection
      severity: "low"
      probability: 0.03               # 3% chance
      target: "anthropic"

    - type: "timeout"                 # Request timeout
      severity: "medium"
      probability: 0.08               # 8% chance
      duration_ms: 5000               # 5 second timeout
      target: "all"

    - type: "network_failure"         # Network failure simulation
      severity: "high"
      probability: 0.02               # 2% chance
      target: "all"

  # Chaos scheduling
  schedule:
    enabled: true
    timezone: "UTC"
    rules:
      - name: "business_hours_only"
        condition: "hour >= 9 and hour <= 17"
        enabled: true
      - name: "weekdays_only"
        condition: "weekday >= 1 and weekday <= 5"
        enabled: true
      - name: "low_traffic_periods"
        condition: "hour >= 2 and hour <= 6"
        enabled: false

  # Monitoring and safety
  monitoring:
    enabled: true
    alert_on_failure: true            # Alert when chaos causes failures
    max_failure_rate: 0.1             # Maximum allowed failure rate
    auto_stop: true                   # Auto-stop on high failure rate

  safety:
    enabled: true
    max_duration: "1h"                # Maximum chaos duration
    rollback_on_failure: true         # Rollback changes on failure
    excluded_endpoints:               # Endpoints to exclude
      - "/health"
      - "/metrics"
```

## Advanced Features

### Context Condensation

```yaml
condensation:
  enabled: true                       # Enable context condensation

  # Basic settings
  truncation_threshold: 8000          # Truncate if over this length
  summary_max_tokens: 512             # Maximum summary tokens
  cache_size: 1000                    # Summary cache size
  cache_ttl: 3600                     # Cache TTL in seconds
  cache_persist: true                 # Persist cache to disk

  # Advanced settings
  adaptive_enabled: true              # Enable adaptive summarization
  adaptive_factor: 0.5                # Adaptive adjustment factor
  quality_threshold: 0.8              # Minimum quality threshold

  # Error handling
  error_patterns:                     # Patterns to detect summarization errors
    - "context length"
    - "maximum context"
    - "too long"
    - "exceeds maximum"

  fallback_strategies:                # Fallback strategies
    - "truncate"
    - "secondary_provider"
    - "skip_summarization"

  # Performance tuning
  batch_size: 10                      # Batch processing size
  concurrency_limit: 5                # Maximum concurrent summarizations
  timeout: 30                         # Summarization timeout

  # Monitoring
  monitoring:
    enabled: true
    metrics: true                     # Export summarization metrics
    alerts: true                      # Enable summarization alerts
    alert_threshold: 0.9              # Alert when success rate below threshold
```

### Template Configuration

```yaml
templates:
  enabled: true                       # Enable Jinja2 templates
  directory: "templates"              # Template directory
  cache_size: 1000                    # Template cache size
  auto_reload: false                  # Auto-reload templates in development

  # Template variables
  variables:
    app_name: "${APP_NAME}"
    version: "${APP_VERSION}"
    environment: "${ENVIRONMENT}"

  # Custom filters
  filters:
    json_encode: true                 # Enable JSON encoding filter
    base64_encode: true               # Enable base64 encoding filter
    hash: true                        # Enable hashing filter

  # Template functions
  functions:
    now: true                         # Enable current time function
    uuid: true                        # Enable UUID generation
    random: true                      # Enable random value generation
```

## Environment Variables

ProxyAPI uses environment variables for sensitive data and runtime configuration. Variables are loaded via python-dotenv with `PROXY_API_` prefix for application settings.

### Core Application Variables

```bash
# Server Configuration (PROXY_API_ prefix)
PROXY_API_HOST=127.0.0.1              # Server bind address
PROXY_API_PORT=8000                   # Server port
PROXY_API_DEBUG=false                 # Enable debug mode

# Security
PROXY_API_API_KEY_HEADER=X-API-Key    # API key header name
PROXY_API_PROXY_API_KEYS=key1,key2    # Comma-separated API keys (required)

# Rate Limiting
PROXY_API_RATE_LIMIT_REQUESTS=100     # Requests per window
PROXY_API_RATE_LIMIT_WINDOW=60        # Time window in seconds

# Timeouts
PROXY_API_CLIENT_TIMEOUT=60           # Client timeout
PROXY_API_PROVIDER_TIMEOUT=30         # Provider timeout

# Resilience
PROXY_API_PROVIDER_RETRIES=3          # Retry attempts
PROXY_API_CIRCUIT_BREAKER_THRESHOLD=5 # Circuit breaker threshold
PROXY_API_CIRCUIT_BREAKER_TIMEOUT=60  # Circuit breaker timeout

# Paths
PROXY_API_CONFIG_FILE=config.yaml     # Configuration file path
PROXY_API_LOG_FILE=logs/proxy_api.log # Log file path
```

### Provider API Keys

```bash
# Required API Keys (no prefix)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
AZURE_OPENAI_KEY=your-azure-key
COHERE_API_KEY=your-cohere-key
GROK_API_KEY=your-grok-key
BLACKBOX_API_KEY=your-blackbox-key
OPENROUTER_API_KEY=your-openrouter-key
PERPLEXITY_API_KEY=your-perplexity-key
```

### Context Service Variables (from systemd-services/.env.example)

```bash
# Context Service Configuration
CACHE_SIZE=1000                      # Cache size for context condensation
CACHE_TTL=3600                       # Cache TTL in seconds
CACHE_PERSIST=false                  # Persist cache to disk
ADAPTIVE_ENABLED=true                # Enable adaptive condensation
ADAPTIVE_FACTOR=0.5                  # Adaptive factor
MAX_TOKENS_DEFAULT=512               # Default max tokens
TRUNCATION_THRESHOLD=10000           # Truncation threshold
PARALLEL_PROVIDERS=1                 # Parallel provider processing
ERROR_PATTERNS=context.*exceeded,token.*limit  # Error patterns
FALLBACK_STRATEGIES=truncate,secondary_provider  # Fallback strategies

# Service URLs
CONTEXT_SERVICE_URL=http://localhost:8001
HEALTH_WORKER_URL=http://localhost:8002
```

### Production Variables (from production_config.py)

```bash
# Environment Detection
ENVIRONMENT=production               # Environment: development/staging/production
IS_PRODUCTION=true                   # Auto-detected

# Server Performance
HOST=0.0.0.0                        # Production bind address
PORT=8000                           # Production port
WORKERS=4                           # Gunicorn workers
WORKER_CLASS=uvicorn.workers.UvicornWorker
MAX_REQUESTS=1000                   # Restart after requests
MAX_REQUESTS_JITTER=50

# HTTP Client Performance
HTTP_MAX_KEEPALIVE=200              # Max keepalive connections
HTTP_MAX_CONNECTIONS=2000           # Max total connections
HTTP_KEEPALIVE_EXPIRY=30.0          # Keepalive expiry
HTTP_TIMEOUT=30.0                   # Request timeout
HTTP_CONNECT_TIMEOUT=10.0           # Connection timeout
HTTP_RETRY_ATTEMPTS=3               # Retry attempts

# Caching
RESPONSE_CACHE_SIZE=10000           # Response cache size
RESPONSE_CACHE_TTL=1800             # Response cache TTL
SUMMARY_CACHE_SIZE=2000             # Summary cache size
SUMMARY_CACHE_TTL=3600              # Summary cache TTL
CACHE_MAX_MEMORY_MB=512             # Max memory for cache

# Memory Management
MEMORY_THRESHOLD_MB=1024            # Memory threshold
EMERGENCY_MEMORY_MB=1536            # Emergency threshold
CLEANUP_INTERVAL=300                # Cleanup interval
ENABLE_GC_TUNING=true               # Enable GC tuning
LEAK_DETECTION=true                 # Enable leak detection

# Security
API_KEYS_REQUIRED=true              # Require API keys
RATE_LIMIT_REQUESTS=1000            # Global rate limit
RATE_LIMIT_WINDOW=60                # Rate limit window
CORS_ORIGINS=https://yourdomain.com
TRUSTED_PROXIES=10.0.0.0/8          # Trusted proxy ranges
SSL_CERTFILE=/path/to/cert.pem      # SSL certificate
SSL_KEYFILE=/path/to/key.pem        # SSL key

# Logging
LOG_LEVEL=WARNING                   # Production log level
LOG_MAX_SIZE=100                    # Max log size (MB)
LOG_BACKUP_COUNT=10                 # Backup count
LOG_JSON_FORMAT=true                # JSON log format

# Monitoring
METRICS_ENABLED=true                # Enable metrics
METRICS_PORT=9090                   # Metrics port
HEALTH_CHECK_INTERVAL=30            # Health check interval
ALERT_WEBHOOK_URL=https://hooks.slack.com/...  # Alert webhook
ALERT_CPU_THRESHOLD=80.0            # CPU alert threshold
ALERT_MEMORY_THRESHOLD=85.0         # Memory alert threshold

# External Services
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
ALERTMANAGER_URL=http://localhost:9093
```

### Variable Parsing

The application supports flexible API key parsing:

```bash
# Comma-separated
PROXY_API_PROXY_API_KEYS=key1,key2,key3

# JSON array
PROXY_API_PROXY_API_KEYS="['key1','key2','key3']"

# Single key
PROXY_API_PROXY_API_KEYS=key1
```

### Environment File Example

```bash
# .env - Development environment
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
PROXY_API_HOST=127.0.0.1
PROXY_API_PORT=8000
PROXY_API_DEBUG=true
PROXY_API_PROXY_API_KEYS=dev-key-123,test-key-456
PROXY_API_LOG_LEVEL=INFO
```

## Configuration Validation

ProxyAPI validates configuration at startup using JSON Schema validation with detailed error reporting.

### Validation Implementation

Configuration validation is handled by `src/core/config_schema.py` which defines a comprehensive JSON Schema and provides fast failure validation.

**Key Features:**
- JSON Schema validation (Draft 2020-12)
- Fast failure at startup
- Detailed error messages with path information
- Required vs optional section validation

### Schema Structure

The validation schema includes these critical sections:

**Required Sections:**
- `app`: Application configuration
- `server`: Server settings
- `auth`: Authentication configuration
- `providers`: Provider configurations

**Optional Sections:**
- `telemetry`, `templates`, `chaos_engineering`, `rate_limit`, `circuit_breaker`, `condensation`, `caching`, `memory`, `http_client`, `logging`, `health_check`, `load_testing`, `network_simulation`

### Provider Validation

Each provider is validated for:
- Supported provider types: `openai`, `anthropic`, `azure_openai`, `cohere`, `perplexity`, `grok`, `blackbox`, `openrouter`
- Unique names and priorities
- Valid environment variable names (UPPER_CASE with underscores)
- Proper URL formats
- At least one model specified
- Valid connection pool settings

### Validation at Startup

The `validate_config_at_startup()` function:
1. Loads configuration file
2. Validates against schema
3. Provides detailed error messages
4. Exits with code 1 on validation failure

**Example Error Output:**
```
❌ CONFIGURATION ERROR:
Configuration validation failed for config.yaml:
  providers[0].type: 'invalid_provider' is not one of ['openai', 'anthropic', 'azure_openai', 'cohere', 'perplexity', 'grok', 'blackbox', 'openrouter']
  providers[1].name: Provider names must be unique

🔧 Please fix the configuration file and restart the application.
```

### Runtime Validation

In addition to startup validation, runtime validation occurs for:
- API key presence and format
- Provider connectivity (optional)
- Memory limits
- Connection pool settings

### Validation Commands

```bash
# Validate configuration file
python -c "from src.core.config_schema import validate_config_at_startup; validate_config_at_startup('config.yaml')"

# Check production readiness
python production_config.py
```

## Hot Reloading Capabilities

ProxyAPI supports hot reloading for certain configuration changes without restarting the application.

### Supported Hot Reload Features

#### Model Selections Reload

The model selection configuration (`config/model_selections.json`) supports hot reloading:

```python
from src.core.model_config import ModelConfig

# Force reload from disk
config = ModelConfig()
config.reload()  # Hot reload model selections
```

#### Configuration File Watching

The system supports file watching for configuration changes (implementation in `src/core/optimized_config.py`):

- Automatic detection of config file changes
- Optimized loading with caching
- Performance timing measurements
- File watching for hot reload triggers

#### Provider Configuration Reload

Provider configurations can be reloaded via API endpoints:

```python
# POST /api/config/reload
# Triggers provider configuration reload
```

### Hot Reload Implementation

Hot reloading is implemented through:
1. **File watchers** that monitor configuration files
2. **In-memory cache invalidation** for changed settings
3. **Graceful provider switching** without dropping active connections
4. **Metrics and logging** for reload events

### Limitations

Hot reloading does **not** support:
- Server configuration changes (host, port, workers)
- Authentication settings
- Schema changes requiring restart

For these changes, a full application restart is required.

### Monitoring Hot Reloads

Hot reload events are logged and can be monitored:

```bash
# View reload logs
tail -f logs/proxy_api.log | grep "reload"

# Check metrics
curl http://localhost:9090/metrics | grep reload
```

## Setup Guides

### Development Environment Setup

#### 1. Clone and Install

```bash
git clone <repository>
cd proxyapi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Create `.env` file:

```bash
# API Keys
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Development settings
PROXY_API_HOST=127.0.0.1
PROXY_API_PORT=8000
PROXY_API_DEBUG=true
PROXY_API_PROXY_API_KEYS=dev-key-123
PROXY_API_LOG_LEVEL=INFO
```

#### 3. Create Basic Configuration

Create `config.yaml`:

```yaml
providers:
  - name: "openai"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo"]
    enabled: true
    priority: 1

condensation:
  max_tokens_default: 512
```

#### 4. Start Development Server

```bash
python main.py
# Or with auto-reload
uvicorn src.api:app --reload --host 127.0.0.1 --port 8000
```

#### 5. Verify Setup

```bash
# Check health endpoint
curl http://localhost:8000/health

# Test API
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Staging Environment Setup

#### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv

# Create application user
sudo useradd --system --shell /bin/bash --home /opt/proxyapi proxyapi
sudo mkdir -p /opt/proxyapi
sudo chown proxyapi:proxyapi /opt/proxyapi
```

#### 2. Application Deployment

```bash
# Switch to application user
sudo -u proxyapi bash

# Clone repository
cd /opt/proxyapi
git clone <repository> .
git checkout staging

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Staging Configuration

Create `/opt/proxyapi/.env`:

```bash
# Staging environment
ENVIRONMENT=staging

# API Keys (use staging keys)
OPENAI_API_KEY=sk-staging-key
ANTHROPIC_API_KEY=sk-ant-staging-key

# Server configuration
PROXY_API_HOST=0.0.0.0
PROXY_API_PORT=8000
PROXY_API_DEBUG=false
PROXY_API_PROXY_API_KEYS=staging-key-1,staging-key-2

# Enhanced logging
PROXY_API_LOG_LEVEL=INFO

# Monitoring
METRICS_ENABLED=true
```

Create `/opt/proxyapi/config.yaml`:

```yaml
providers:
  - name: "openai"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo", "gpt-4"]
    enabled: true
    priority: 1
    rate_limit: 500

  - name: "anthropic"
    type: "anthropic"
    base_url: "https://api.anthropic.com"
    api_key_env: "ANTHROPIC_API_KEY"
    models: ["claude-3-sonnet"]
    enabled: true
    priority: 2
    rate_limit: 25

condensation:
  max_tokens_default: 512
  cache_ttl: 600
```

#### 4. Systemd Service Setup

Create `/etc/systemd/system/llm-proxy.service`:

```ini
[Unit]
Description=LLM Proxy API (Staging)
After=network.target

[Service]
Type=simple
User=proxyapi
Group=proxyapi
WorkingDirectory=/opt/proxyapi
Environment=PATH=/opt/proxyapi/venv/bin
ExecStart=/opt/proxyapi/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 5. Start and Monitor

```bash
sudo systemctl daemon-reload
sudo systemctl start llm-proxy
sudo systemctl enable llm-proxy
sudo systemctl status llm-proxy

# View logs
sudo journalctl -u llm-proxy -f
```

### Production Environment Setup

#### 1. Production Server Setup

```bash
# Security hardening
sudo apt install ufw fail2ban
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp

# Install monitoring stack
sudo apt install prometheus grafana prometheus-node-exporter

# SSL certificate setup (using Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

#### 2. Production Configuration

Create `/opt/proxyapi/.env`:

```bash
# Production environment
ENVIRONMENT=production
IS_PRODUCTION=true

# API Keys (production keys)
OPENAI_API_KEY=sk-production-key
ANTHROPIC_API_KEY=sk-ant-production-key
AZURE_OPENAI_KEY=production-azure-key

# Server configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
MAX_REQUESTS=1000

# Security
PROXY_API_PROXY_API_KEYS=prod-key-1,prod-key-2,prod-key-3
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60

# Performance
HTTP_MAX_CONNECTIONS=2000
HTTP_MAX_KEEPALIVE=500
CACHE_MAX_MEMORY_MB=1024
MEMORY_THRESHOLD_MB=2048

# Logging
LOG_LEVEL=WARNING
LOG_JSON_FORMAT=true
LOG_MAX_SIZE=500
LOG_BACKUP_COUNT=30

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# SSL
SSL_CERTFILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEYFILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### 3. Production YAML Configuration

Create `/opt/proxyapi/config.yaml`:

```yaml
providers:
  - name: "openai-primary"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    enabled: true
    priority: 1
    timeout: 30
    rate_limit: 2000
    retry_attempts: 3
    max_connections: 200
    max_keepalive_connections: 100

  - name: "anthropic-fallback"
    type: "anthropic"
    base_url: "https://api.anthropic.com"
    api_key_env: "ANTHROPIC_API_KEY"
    models: ["claude-3-sonnet", "claude-3-opus"]
    enabled: true
    priority: 2
    timeout: 30
    rate_limit: 100
    retry_attempts: 3

condensation:
  max_tokens_default: 512
  error_keywords: ["context_length_exceeded", "maximum context length"]
  adaptive_factor: 0.5
  cache_ttl: 1800
```

#### 4. Gunicorn Setup for Production

Create `/opt/proxyapi/gunicorn.conf.py`:

```python
# Gunicorn configuration for production
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "warning"
accesslog = "/opt/proxyapi/logs/access.log"
errorlog = "/opt/proxyapi/logs/error.log"

# Process naming
proc_name = "llm-proxy"

# SSL (if using direct SSL)
# keyfile = "/etc/letsencrypt/live/yourdomain.com/privkey.pem"
# certfile = "/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
```

#### 5. Production Deployment

Update systemd service for production:

```ini
[Unit]
Description=LLM Proxy API (Production)
After=network.target
Requires=network.target

[Service]
Type=exec
User=proxyapi
Group=proxyapi
WorkingDirectory=/opt/proxyapi
Environment=PATH=/opt/proxyapi/venv/bin
Environment=PYTHONPATH=/opt/proxyapi
ExecStart=/opt/proxyapi/venv/bin/gunicorn -c gunicorn.conf.py src.api:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=30

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/opt/proxyapi /var/log/proxyapi

[Install]
WantedBy=multi-user.target
```

#### 6. Reverse Proxy Setup (Nginx)

Create `/etc/nginx/sites-available/llm-proxy`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Rate limiting
    limit_req zone=api burst=100 nodelay;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Metrics endpoint (internal only)
    location /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:9090;
    }
}
```

#### 7. Monitoring Setup

```bash
# Configure Prometheus
sudo cp monitoring/prometheus.yml /etc/prometheus/prometheus.yml
sudo systemctl restart prometheus

# Import Grafana dashboard
# Access Grafana at http://your-server:3000
# Import monitoring/grafana-dashboard.json

# Setup log rotation
sudo cp systemd-services/logrotate.conf /etc/logrotate.d/proxyapi
```

#### 8. Backup and Recovery

```bash
# Create backup script
cat > /opt/proxyapi/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/proxyapi/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config.yaml .env

# Backup logs (last 7 days)
find logs/ -name "*.log" -mtime -7 -exec tar -rf $BACKUP_DIR/logs_$DATE.tar logs/ {} +

# Cleanup old backups (keep last 30)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/proxyapi/backup.sh

# Add to cron
echo "0 2 * * * /opt/proxyapi/backup.sh" | sudo crontab -u proxyapi -
```

## Deployment Scenarios

### Docker Container Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs cache metrics && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "main.py"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  proxyapi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - PROXY_API_HOST=0.0.0.0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

### Kubernetes Deployment

#### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-proxy
  labels:
    app: llm-proxy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-proxy
  template:
    metadata:
      labels:
        app: llm-proxy
    spec:
      containers:
      - name: llm-proxy
        image: your-registry/llm-proxy:latest
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: PROXY_API_HOST
          value: "0.0.0.0"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-proxy-secrets
              key: openai-api-key
        - name: WORKERS
          value: "2"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
          readOnly: true
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: config
        configMap:
          name: llm-proxy-config
      - name: logs
        emptyDir: {}
```

#### Service Manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-proxy
  labels:
    app: llm-proxy
spec:
  selector:
    app: llm-proxy
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP
```

#### Ingress Manifest

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-proxy
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: llm-proxy-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: llm-proxy
            port:
              number: 80
```

### Cloud Platform Deployments

#### AWS ECS Fargate

```yaml
# Task Definition
{
  "family": "llm-proxy",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "llm-proxy",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-proxy:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "WORKERS", "value": "2"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/llm-proxy",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

## Troubleshooting

### Configuration Issues

#### Configuration Validation Fails

**Symptoms:**
- Application fails to start
- Error message: "CONFIGURATION ERROR"

**Solutions:**
1. Check YAML syntax: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
2. Validate against schema: Use the validation command
3. Check required fields are present
4. Verify provider types are supported
5. Ensure environment variables are set

#### Provider Connection Issues

**Symptoms:**
- Provider requests fail
- "Connection timeout" errors

**Solutions:**
1. Verify API keys are correct
2. Check network connectivity to provider endpoints
3. Validate base_url configuration
4. Check rate limits haven't been exceeded
5. Review timeout settings

#### Memory Issues

**Symptoms:**
- Out of memory errors
- High memory usage

**Solutions:**
1. Reduce cache sizes in configuration
2. Increase memory limits
3. Enable memory monitoring
4. Check for memory leaks
5. Adjust garbage collection settings

#### Rate Limiting Problems

**Symptoms:**
- Requests being rejected
- "Rate limit exceeded" errors

**Solutions:**
1. Check rate limit configuration
2. Verify API key configuration
3. Review rate limit headers in responses
4. Adjust rate limits if too restrictive

### Performance Issues

#### High Latency

**Symptoms:**
- Slow response times
- Timeout errors

**Solutions:**
1. Check provider response times
2. Review connection pool settings
3. Enable caching for frequent requests
4. Adjust timeout values
5. Monitor system resources

#### Cache Issues

**Symptoms:**
- Cache not working
- High cache miss rates

**Solutions:**
1. Verify cache configuration
2. Check cache size limits
3. Monitor cache hit/miss ratios
4. Adjust TTL values
5. Clear cache if corrupted

### Monitoring Issues

#### Metrics Not Appearing

**Symptoms:**
- No metrics in Prometheus
- Grafana dashboards empty

**Solutions:**
1. Check metrics endpoint is accessible: `curl http://localhost:9090/metrics`
2. Verify Prometheus configuration
3. Check firewall settings
4. Review scraping configuration
5. Validate metric names

#### Alerting Not Working

**Symptoms:**
- Alerts not triggered
- No notifications received

**Solutions:**
1. Check Prometheus alerting rules
2. Verify alertmanager configuration
3. Test webhook endpoints
4. Review alert thresholds
5. Check notification channels

### Logging Issues

#### Logs Not Appearing

**Symptoms:**
- No log output
- Logs not written to files

**Solutions:**
1. Check log level configuration
2. Verify log file permissions
3. Review log format settings
4. Check disk space
5. Validate logging configuration

#### Log Rotation Not Working

**Symptoms:**
- Log files growing too large
- Old logs not cleaned up

**Solutions:**
1. Check logrotate configuration
2. Verify log rotation settings
3. Review file permissions
4. Test log rotation manually

### Deployment Issues

#### Application Won't Start

**Symptoms:**
- Service fails to start
- Error in systemd logs

**Solutions:**
1. Check systemd service configuration
2. Review application logs
3. Verify dependencies are installed
4. Check file permissions
5. Validate configuration

#### Container Issues

**Symptoms:**
- Container crashes
- Health checks failing

**Solutions:**
1. Check container logs: `docker logs <container>`
2. Verify environment variables
3. Review resource limits
4. Check health check configuration
5. Validate networking

### Common Error Messages

#### "Proxy API keys must be configured"

**Cause:** Missing PROXY_API_PROXY_API_KEYS environment variable
**Solution:** Set API keys in environment or .env file

#### "Provider type must be one of [list]"

**Cause:** Invalid provider type in configuration
**Solution:** Use supported provider types only

#### "Provider names must be unique"

**Cause:** Duplicate provider names
**Solution:** Ensure all provider names are unique

#### "Environment variable 'X' not found"

**Cause:** Required environment variable not set
**Solution:** Set the environment variable or check spelling

#### Legacy Configuration Migration Issues

**Symptoms:**
- Deprecation warnings about legacy configuration formats
- Migration failures during startup
- Configuration not loading properly

**Solutions:**
1. Check migration status: `python -c "from src.core.config_compatibility import get_migration_report; print(get_migration_report())"`
2. Manually migrate formats: `migrate_specific_format('format_type')`
3. Check legacy file backups in case rollback is needed
4. Review migration logs for specific error details
5. Ensure write permissions for configuration directory

#### Migration Rollback Problems

**Symptoms:**
- Unable to rollback migrated configurations
- Missing legacy backup files

**Solutions:**
1. Check file permissions on configuration directory
2. Verify legacy backup files exist (`.legacy` suffix)
3. Manually restore from backup if automatic rollback fails
4. Review migration history for correct format type
5. Contact support if rollback fails unexpectedly

## Best Practices

### Configuration Management

#### Version Control

1. **Store configurations in Git**: Keep all configuration files under version control
2. **Use branches for environments**: Separate branches for dev/staging/production
3. **Document changes**: Include configuration changes in commit messages
4. **Review configuration changes**: Require code review for config changes

#### Environment Separation

1. **Separate configurations**: Use different config files per environment
2. **Environment variables**: Override sensitive data with environment variables
3. **Naming conventions**: Use consistent naming across environments
4. **Configuration validation**: Validate configs in CI/CD pipelines

#### Security

1. **Never commit secrets**: Use environment variables for sensitive data
2. **Restrict permissions**: Limit access to configuration files
3. **Regular rotation**: Rotate API keys and credentials regularly
4. **Audit logging**: Enable audit logging for configuration changes

### Performance Optimization

#### Connection Management

1. **Tune connection pools**: Adjust pool sizes based on load
2. **Enable keep-alive**: Use persistent connections
3. **Set appropriate timeouts**: Balance responsiveness and reliability
4. **Monitor connection usage**: Track connection pool metrics

#### Caching Strategy

1. **Configure cache sizes**: Set appropriate cache limits
2. **Set proper TTL**: Balance freshness and performance
3. **Enable compression**: Reduce memory usage
4. **Monitor cache effectiveness**: Track hit/miss ratios

#### Memory Management

1. **Set memory limits**: Prevent resource exhaustion
2. **Enable GC tuning**: Optimize garbage collection
3. **Monitor memory usage**: Track memory patterns
4. **Configure emergency cleanup**: Handle memory pressure

### Monitoring and Observability

#### Metrics Collection

1. **Enable comprehensive metrics**: Collect all relevant metrics
2. **Set up dashboards**: Create useful monitoring dashboards
3. **Configure alerts**: Set up meaningful alerts
4. **Monitor trends**: Track performance over time

#### Logging Strategy

1. **Use structured logging**: Enable JSON log format
2. **Set appropriate levels**: Balance verbosity and performance
3. **Configure log rotation**: Manage log file sizes
4. **Centralize logs**: Use log aggregation systems

#### Health Checks

1. **Implement liveness probes**: Detect crashed instances
2. **Implement readiness probes**: Detect unready instances
3. **Check dependencies**: Verify external service health
4. **Monitor resource usage**: Track system resource health

### Deployment Practices

#### Infrastructure as Code

1. **Use IaC tools**: Terraform, CloudFormation, etc.
2. **Version infrastructure**: Keep infrastructure changes versioned
3. **Automate deployments**: Use CI/CD pipelines
4. **Test deployments**: Test infrastructure changes

#### Containerization

1. **Use multi-stage builds**: Optimize image sizes
2. **Implement health checks**: Container health verification
3. **Configure resource limits**: Set appropriate CPU/memory limits
4. **Use security scanning**: Scan images for vulnerabilities

#### Orchestration

1. **Use Kubernetes**: For complex deployments
2. **Configure resource requests/limits**: Proper resource allocation
3. **Implement rolling updates**: Zero-downtime deployments
4. **Set up network policies**: Secure pod communication

### Security Best Practices

#### Authentication and Authorization

1. **Use strong API keys**: Generate secure, random keys
2. **Implement rate limiting**: Protect against abuse
3. **Enable audit logging**: Track all API access
4. **Regular key rotation**: Rotate keys periodically

#### Network Security

1. **Use HTTPS**: Encrypt all communications
2. **Configure firewalls**: Restrict network access
3. **Use VPC/security groups**: Network isolation
4. **Implement WAF**: Web application firewall

#### Data Protection

1. **Encrypt sensitive data**: Encrypt API keys and secrets
2. **Use secure protocols**: Prefer HTTPS over HTTP
3. **Implement input validation**: Validate all inputs
4. **Sanitize outputs**: Cleanse response data

### Operational Excellence

#### Backup and Recovery

1. **Regular backups**: Backup configurations and data
2. **Test restores**: Verify backup integrity
3. **Document procedures**: Recovery runbooks
4. **Automate backups**: Scheduled backup scripts

#### Incident Response

1. **Define incident procedures**: Incident response plans
2. **Set up alerting**: Critical alert notifications
3. **Maintain runbooks**: Operational documentation
4. **Conduct post-mortems**: Learn from incidents

#### Capacity Planning

1. **Monitor resource usage**: Track system utilization
2. **Plan for growth**: Scale infrastructure proactively
3. **Load testing**: Regular performance testing
4. **Resource optimization**: Right-size infrastructure

This comprehensive guide covers all aspects of ProxyAPI configuration and deployment. For additional support, refer to the API documentation or contact the development team.

## Best Practices

### Production Configuration

1. **Use Environment Variables**: Never hardcode sensitive data
2. **Enable Monitoring**: Configure comprehensive monitoring and alerting
3. **Set Resource Limits**: Configure appropriate memory and connection limits
4. **Enable Security**: Configure authentication, rate limiting, and validation
5. **Use HTTPS**: Always use HTTPS in production
6. **Configure Backups**: Set up configuration backups and versioning

### Performance Optimization

1. **Tune Connection Pools**: Adjust HTTP connection pool settings based on load
2. **Configure Caching**: Enable appropriate caching with proper TTL values
3. **Set Memory Limits**: Configure memory limits to prevent resource exhaustion
4. **Enable Compression**: Use compression for large responses and cached data
5. **Monitor Performance**: Regularly monitor and tune performance metrics

### Security Best Practices

1. **Use Strong Authentication**: Implement proper API key management
2. **Enable Rate Limiting**: Protect against abuse with rate limiting
3. **Validate Input**: Always validate and sanitize input data
4. **Use HTTPS**: Encrypt all communications
5. **Regular Updates**: Keep dependencies and configurations up to date
6. **Audit Logging**: Enable comprehensive audit logging

### Monitoring and Alerting

1. **Set Up Dashboards**: Create dashboards for key metrics
2. **Configure Alerts**: Set up alerts for critical issues
3. **Monitor Trends**: Track performance trends over time
4. **Log Analysis**: Regularly analyze logs for issues and patterns
5. **Performance Testing**: Regularly run performance tests

### Configuration Management

1. **Version Control**: Keep configuration files in version control
2. **Environment Separation**: Use different configurations for each environment
3. **Documentation**: Document all configuration options and their purposes
4. **Validation**: Always validate configuration before deployment
5. **Backup**: Regularly backup working configurations

This configuration guide provides comprehensive coverage of all available options. For specific use cases or advanced configurations, refer to the API documentation or contact the development team.