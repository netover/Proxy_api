# LLM Proxy API with Unified Architecture

A production-ready LLM proxy with unified configuration, intelligent routing, health monitoring, and fallback capabilities. Supports multiple providers with centralized management and performance optimization.

## Features

- **Unified Configuration**: Single `config.yaml` for global settings and providers with Pydantic validation and caching
- **Intelligent Routing**: Automatic failover between healthy providers based on priority and model support
- **Health Monitoring**: Background health checks with status tracking (healthy, degraded, unhealthy)
- **Resource Management**: Proper HTTP client pooling, connection limits, and automatic cleanup
- **Circuit Breakers & Retry Logic**: Built-in resilience with exponential backoff and jitter
- **Metrics Collection**: Comprehensive performance monitoring with background task recording
- **Rate Limiting**: Configurable rate limiting per endpoint
- **OpenAI Compatible**: Drop-in replacement for OpenAI API endpoints (/v1/chat/completions, /v1/completions, /v1/embeddings)
- **Extensible Architecture**: Easy to add new providers by inheriting from BaseProvider
- **Production Ready**: No memory leaks, HTTP/2 support, structured logging, and error handling

## Architecture Overview

The new architecture uses a centralized configuration manager and provider factory for better maintainability and performance:

- **ConfigManager**: Loads and validates configuration with caching and hot-reload detection
- **ProviderFactory**: Manages provider lifecycle, health monitoring, and instance caching
- **BaseProvider**: Enhanced base class with lazy HTTP clients, retry logic, and status tracking
- **RequestRouter**: Centralized routing with fallback, metrics, and error handling

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your API keys in `.env` or environment variables:
   ```
   PROXY_API_OPENAI_API_KEY=your-openai-key
   PROXY_API_ANTHROPIC_API_KEY=your-anthropic-key
   # ... other provider keys
   ```

3. Edit `config.yaml` to add providers and global settings (example included)

4. Run the server:
   ```bash
   python main_dynamic.py
   ```

## Configuration

### Global Settings

Global settings are configured in the root of `config.yaml`:

```yaml
app_name: "LLM Proxy API"
app_version: "2.0.0"
debug: false
host: "127.0.0.1"
port: 8000
api_keys:
  - "your-api-key-here"
api_key_header: "X-API-Key"
cors_origins:
  - "*"
rate_limit_rpm: 1000
rate_limit_window: 60
request_timeout: 300
circuit_breaker_threshold: 5
circuit_breaker_timeout: 60
log_level: "INFO"
log_file: null
config_file: "config.yaml"
```

### Provider Configuration

Providers are configured under the `providers` key with enhanced fields:

```yaml
providers:
  - name: "openai_default"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "PROXY_API_OPENAI_API_KEY"
    models:
      - "gpt-4"
      - "gpt-3.5-turbo"
    enabled: true
    priority: 1
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    rate_limit: null
    max_connections: 10
    keepalive_timeout: 30
    custom_headers: {}
```

Supported provider types: `openai`, `anthropic`, `perplexity`, `grok`, `blackbox`, `openrouter`, `cohere`

### Adding New Providers

To add a new provider:

1. Create a new class in `src/providers/` that inherits from `BaseProvider`
2. Implement the abstract methods:
   - `_perform_health_check()`
   - `create_completion()`
   - `create_text_completion()`
   - `create_embeddings()`
3. Add the provider to `ProviderFactory.PROVIDER_MAPPING` in `src/core/provider_factory.py`
4. Add the provider configuration to `config.yaml`
5. Set the appropriate environment variable for the API key

Example provider implementation:

```python
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig

class MyNewProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def _perform_health_check(self) -> Dict[str, Any]:
        # Implementation here
        pass
        
    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        pass
        
    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        pass
        
    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        pass
```

## API Endpoints

All endpoints are OpenAI-compatible and include intelligent routing:

- `POST /v1/chat/completions` - Chat completions (rate limited 100/min)
- `POST /v1/completions` - Text completions (rate limited 100/min)
- `POST /v1/embeddings` - Embeddings generation (rate limited 200/min)
- `GET /v1/models` - List available models across all providers
- `GET /providers` - List configured providers with status and capabilities
- `GET /metrics` - Comprehensive performance metrics
- `GET /health` - Health check with provider status summary

### Authentication

All endpoints require an API key in the `X-API-Key` header (configurable).

### Response Format

Responses include `_proxy_info` with routing details:

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [...],
  "_proxy_info": {
    "provider": "openai_default",
    "attempt_number": 1,
    "response_time": 0.85,
    "request_id": "chat_completion_1699999999999"
  }
}
```

## Monitoring & Metrics

- **Health Monitoring**: Background health checks every 60 seconds
- **Metrics**: Request success rates, response times, token usage per provider
- **Circuit Breakers**: Per-provider circuit breakers to prevent cascading failures
- **Logging**: Structured JSON logging with request context

Access metrics at `/metrics` and health at `/health`.

## Testing

Run the test suite:

```bash
pytest tests/test_providers.py
```

The tests cover provider initialization, request routing, retry logic, and error handling.

## Deployment

For production deployment:

1. Set `debug: false` in config.yaml
2. Configure proper API keys and rate limits
3. Use a reverse proxy (nginx) for SSL and load balancing
4. Monitor logs and metrics
5. Set up environment variables for all provider API keys

## License

MIT License
