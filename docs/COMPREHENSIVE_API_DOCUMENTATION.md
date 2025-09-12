# Comprehensive API Documentation - LLM Proxy API

## Overview

The LLM Proxy API is a unified gateway for accessing multiple AI providers (OpenAI, Anthropic, Grok, etc.) through a single, consistent interface. This documentation covers all API endpoints, authentication, configuration options, and best practices.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Core API Endpoints](#core-api-endpoints)
4. [Model Management API](#model-management-api)
5. [Monitoring & Analytics](#monitoring--analytics)
6. [Alerting System](#alerting-system)
7. [Configuration Management](#configuration-management)
8. [Request/Response Formats](#requestresponse-formats)
9. [Rate Limiting](#rate-limiting)
10. [Error Handling](#error-handling)
11. [Configuration Guide](#configuration-guide)
12. [Best Practices](#best-practices)
13. [Examples](#examples)

## Quick Start

### Basic Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Create config.yaml:**
   ```yaml
   app:
     name: "LLM Proxy API"
     version: "2.0.0"
   server:
     host: "127.0.0.1"
     port: 8000
   auth:
     api_keys:
       - "your-api-key-here"
   providers:
     - name: "openai"
       type: "openai"
       base_url: "https://api.openai.com/v1"
       api_key_env: "OPENAI_API_KEY"
       models: ["gpt-3.5-turbo", "gpt-4"]
       enabled: true
   ```

4. **Start the server:**
   ```bash
   python main_dynamic.py
   ```

5. **Test the API:**
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]}'
   ```

## Authentication

### API Key Authentication

All API endpoints require authentication via API key. The key can be provided in two ways:

1. **Authorization Header (Recommended):**
   ```
   Authorization: Bearer your-api-key-here
   ```

2. **Custom Header (Configurable):**
   ```
   X-API-Key: your-api-key-here
   ```

### Configuration

API keys are configured in `config.yaml`:

```yaml
auth:
  api_keys:
    - "your-primary-api-key"
    - "your-backup-api-key"
  api_key_header: "X-API-Key"  # Optional, defaults to X-API-Key
```

### Security Features

- API keys are hashed using SHA-256 before storage
- Timing attack protection using `secrets.compare_digest()`
- Sensitive data is redacted from logs
- Request sanitization removes potential XSS/SQL injection patterns

## Core API Endpoints

### Chat Completions

**Endpoint:** `POST /v1/chat/completions`

OpenAI-compatible chat completions endpoint with intelligent provider routing and fallback.

**Request Body:**
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, world!"}
  ],
  "max_tokens": 100,
  "temperature": 0.7,
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 13,
    "completion_tokens": 7,
    "total_tokens": 20
  },
  "_proxy_info": {
    "provider": "openai",
    "attempt_number": 1,
    "response_time": 0.85,
    "request_id": "chat_completion_1703123456789"
  }
}
```

**Rate Limit:** 100 requests/minute

### Text Completions

**Endpoint:** `POST /v1/completions`

Legacy text completions endpoint.

**Request Body:**
```json
{
  "model": "text-davinci-003",
  "prompt": "Once upon a time",
  "max_tokens": 100,
  "temperature": 0.8
}
```

### Embeddings

**Endpoint:** `POST /v1/embeddings`

Generate embeddings for text.

**Request Body:**
```json
{
  "model": "text-embedding-ada-002",
  "input": "The quick brown fox jumps over the lazy dog",
  "user": "optional-user-id"
}
```

### Image Generation

**Endpoint:** `POST /v1/images/generations`

Generate images (supported by Blackbox provider).

**Request Body:**
```json
{
  "model": "dall-e-3",
  "prompt": "A beautiful sunset over mountains",
  "n": 1,
  "size": "1024x1024"
}
```

### List Models

**Endpoint:** `GET /v1/models`

List all available models across providers.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1677649200,
      "owned_by": "openai",
      "provider_type": "openai",
      "status": "healthy",
      "enabled": true,
      "forced": false
    }
  ]
}
```

## Model Management API

### List Provider Models

**Endpoint:** `GET /v1/providers/{provider_name}/models`

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1677649200,
      "owned_by": "openai",
      "provider": "openai",
      "status": "active",
      "capabilities": ["text_generation", "chat"],
      "context_window": 8192,
      "max_tokens": 4096
    }
  ],
  "provider": "openai",
  "total": 15,
  "cached": true,
  "last_refresh": 1709251200
}
```

### Get Model Details

**Endpoint:** `GET /v1/providers/{provider_name}/models/{model_id}`

### Update Model Selection

**Endpoint:** `PUT /v1/providers/{provider_name}/model_selection`

**Request Body:**
```json
{
  "selected_model": "gpt-4",
  "editable": true,
  "priority": 5,
  "max_tokens": 2000,
  "temperature": 0.7
}
```

### Refresh Model Cache

**Endpoint:** `POST /v1/providers/{provider_name}/models/refresh`

## Monitoring & Analytics

### Health Check

**Endpoint:** `GET /health`

Comprehensive health check with provider status.

**Response:**
```json
{
  "status": "healthy",
  "health_score": 95.2,
  "timestamp": 1709251200,
  "response_time": 0.023,
  "providers": {
    "total": 3,
    "healthy": 2,
    "degraded": 1,
    "unhealthy": 0,
    "disabled": 0
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 68.5,
    "memory_used_mb": 552.3,
    "disk_percent": 32.1
  },
  "alerts": {
    "active": 2,
    "critical": 0,
    "warning": 2
  }
}
```

### Metrics

**Endpoint:** `GET /metrics`

Detailed performance metrics.

**Response:**
```json
{
  "timestamp": 1709251200,
  "providers": {
    "openai": {
      "total_requests": 1250,
      "successful_requests": 1225,
      "failed_requests": 25,
      "success_rate": 0.98,
      "avg_response_time": 0.245,
      "total_tokens": 50000
    }
  },
  "summary": {
    "total_providers": 3,
    "total_requests": 3750,
    "average_success_rate": 0.967
  }
}
```

### Prometheus Metrics

**Endpoint:** `GET /metrics/prometheus`

Metrics in Prometheus format for monitoring systems.

## Alerting System

### Get Active Alerts

**Endpoint:** `GET /v1/alerts`

**Query Parameters:**
- `severity`: Filter by severity (info, warning, error, critical)
- `status`: Filter by status (active, acknowledged)

### Create Alert Rule

**Endpoint:** `POST /v1/rules`

**Request Body:**
```json
{
  "name": "high_error_rate",
  "description": "Alert when error rate exceeds threshold",
  "metric_path": "providers.openai.error_rate",
  "condition": ">",
  "threshold": 0.05,
  "severity": "warning",
  "enabled": true,
  "cooldown_minutes": 5,
  "channels": ["log", "email"]
}
```

### Update Alert Rule

**Endpoint:** `PUT /v1/rules/{rule_name}`

### Delete Alert Rule

**Endpoint:** `DELETE /v1/rules/{rule_name}`

### Acknowledge Alert

**Endpoint:** `POST /v1/alerts/{alert_id}/acknowledge`

## Configuration Management

### Reload Configuration

**Endpoint:** `POST /v1/config/reload`

Hot reload configuration without restarting the service.

**Response:**
```json
{
  "success": true,
  "message": "Configuration reloaded successfully",
  "reload_time_ms": 67.2,
  "config_version": "2.0.0",
  "changes_detected": true
}
```

### Get Configuration Status

**Endpoint:** `GET /v1/config/status`

**Response:**
```json
{
  "status": "valid",
  "last_loaded": 1709251200,
  "load_time_ms": 45,
  "file_size_bytes": 2456,
  "providers_configured": 3,
  "validation_errors": [],
  "cache_status": {
    "enabled": true,
    "hit_rate": 0.85,
    "entries": 500
  }
}
```

## Request/Response Formats

### Chat Completion Request

```python
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    parallel_tool_calls: Optional[bool] = False
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None
```

### Validation Rules

- **Model names:** Alphanumeric, hyphens, underscores, dots only (max 100 chars)
- **Messages:** Must contain 'role' and 'content' fields
- **Temperature:** 0.0 to 2.0
- **Max tokens:** Positive integer
- **Logit bias:** Values between -100 and 100

### Response Metadata

All responses include `_proxy_info` with:
- `provider`: Which provider handled the request
- `attempt_number`: How many attempts were made
- `response_time`: Time taken in seconds
- `request_id`: Unique request identifier

## Rate Limiting

### Global Limits

- **Default:** 1000 requests per minute
- **Burst:** 50 requests
- Headers included in responses:
  ```
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 950
  X-RateLimit-Reset: 1709251800
  ```

### Endpoint-Specific Limits

| Endpoint | Limit |
|----------|-------|
| `/v1/chat/completions` | 100/minute |
| `/v1/completions` | 100/minute |
| `/v1/embeddings` | 100/minute |
| `/v1/models` | 60/minute |
| `/health` | 60/minute |
| `/metrics` | 30/minute |

### Rate Limit Response

```json
{
  "error": {
    "code": "rate_limited",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Model 'gpt-5' is not supported by any available provider",
    "type": "invalid_request",
    "param": "model",
    "code": "model_not_found"
  },
  "timestamp": 1709251200
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Invalid request parameters |
| `model_not_found` | 404 | Requested model not available |
| `provider_unavailable` | 503 | All providers are down |
| `rate_limited` | 429 | Rate limit exceeded |
| `unauthorized` | 401 | Invalid API key |
| `insufficient_permissions` | 403 | API key lacks permissions |

### Provider Fallback

When a provider fails, the system automatically tries the next available provider based on priority. Failed attempts are logged with detailed error information.

## Configuration Guide

### Complete config.yaml Example

```yaml
# Application Configuration
app:
  name: "LLM Proxy API"
  version: "2.0.0"
  environment: "production"

# Server Configuration
server:
  host: "0.0.0.0"
  port: 8000
  debug: false
  reload: false

# Authentication
auth:
  api_keys:
    - "your-primary-api-key"
    - "your-backup-api-key"
  api_key_header: "X-API-Key"

# Providers Configuration
providers:
  - name: "openai"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models:
      - "gpt-3.5-turbo"
      - "gpt-4"
      - "gpt-4-turbo-preview"
    enabled: true
    forced: false
    priority: 1
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    max_connections: 100
    max_keepalive_connections: 20
    keepalive_expiry: 30.0
    custom_headers: {}

  - name: "anthropic"
    type: "anthropic"
    base_url: "https://api.anthropic.com"
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      - "claude-3-opus-20240229"
      - "claude-3-sonnet-20240229"
    enabled: true
    priority: 2

# Circuit Breaker
circuit_breaker:
  failure_threshold: 5
  recovery_timeout: 60
  half_open_max_calls: 3
  expected_exception: "ConnectionError"

# Context Condensation
condensation:
  enabled: true
  truncation_threshold: 2000
  summary_max_tokens: 512
  cache_size: 1000
  cache_ttl: 3600
  cache_persist: false
  error_patterns:
    - "context_length_exceeded"
    - "token_limit_exceeded"

# Caching
caching:
  enabled: true
  response_cache:
    max_size_mb: 512
    ttl: 300
    compression: true
  summary_cache:
    max_size_mb: 256
    ttl: 3600
    compression: true

# Memory Management
memory:
  max_usage_percent: 85
  gc_threshold_percent: 75
  monitoring_interval: 30
  cache_cleanup_interval: 300

# HTTP Client
http_client:
  timeout: 30
  connect_timeout: 10
  read_timeout: 30
  pool_limits:
    max_connections: 100
    max_keepalive_connections: 20
    keepalive_timeout: 30

# Logging
logging:
  level: "INFO"
  format: "json"
  file: "logs/proxy_api.log"
  rotation:
    max_size_mb: 100
    max_files: 5

# Health Check
health_check:
  interval: 30
  timeout: 10
  providers: true
  context_service: true
  memory: true
  cache: true

# Telemetry
telemetry:
  enabled: true
  service_name: "llm-proxy-api"
  service_version: "2.0.0"
  jaeger:
    enabled: false
    endpoint: "http://localhost:14268/api/traces"
  zipkin:
    enabled: false
    endpoint: "http://localhost:9411/api/v2/spans"
  sampling:
    probability: 0.1

# Chaos Engineering
chaos_engineering:
  enabled: false
  faults:
    - type: "delay"
      severity: "medium"
      probability: 0.1
      duration_ms: 500
    - type: "error"
      severity: "low"
      probability: 0.05
      error_code: 503
      error_message: "Simulated provider error"

# Rate Limiting
rate_limit:
  requests_per_window: 1000
  window_seconds: 60
  burst_limit: 50

# Templates
templates:
  enabled: true
  directory: "templates"
  cache_size: 50
  auto_reload: true
```

## Best Practices

### API Usage

1. **Use Streaming:** Enable streaming for better user experience with long responses
2. **Handle Rate Limits:** Implement exponential backoff for rate limit errors
3. **Monitor Health:** Regularly check `/health` endpoint for system status
4. **Use Appropriate Models:** Choose models based on your use case and cost requirements

### Configuration

1. **Environment Variables:** Store API keys in environment variables, not config files
2. **Multiple Providers:** Configure multiple providers for redundancy
3. **Monitoring:** Enable telemetry and alerting for production deployments
4. **Security:** Use strong, unique API keys and rotate them regularly

### Performance

1. **Caching:** Enable response caching for frequently used requests
2. **Connection Pooling:** Configure appropriate connection pool limits
3. **Load Balancing:** Use multiple provider instances for high availability
4. **Monitoring:** Set up comprehensive monitoring and alerting

### Error Handling

1. **Graceful Degradation:** Handle provider failures gracefully
2. **Retry Logic:** Implement appropriate retry strategies
3. **Fallback Providers:** Configure fallback providers for critical operations
4. **Logging:** Log errors with sufficient context for debugging

## Examples

### Python Client

```python
import requests
from typing import List, Dict, Any

class LLMProxyClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def chat_completion(self, model: str, messages: List[Dict[str, Any]],
                       **kwargs) -> Dict[str, Any]:
        """Send a chat completion request"""
        data = {
            'model': model,
            'messages': messages,
            **kwargs
        }

        response = requests.post(
            f'{self.base_url}/v1/chat/completions',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def list_models(self) -> Dict[str, Any]:
        """List all available models"""
        response = requests.get(
            f'{self.base_url}/v1/models',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        response = requests.get(f'{self.base_url}/health')
        response.raise_for_status()
        return response.json()

# Usage example
client = LLMProxyClient('http://localhost:8000', 'your-api-key')

# Chat completion
response = client.chat_completion(
    model='gpt-3.5-turbo',
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'What is the capital of France?'}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response['choices'][0]['message']['content'])

# Health check
health = client.health_check()
print(f"System status: {health['status']}")
```

### JavaScript/Node.js Client

```javascript
class LLMProxyClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async chatCompletion(model, messages, options = {}) {
        const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                model,
                messages,
                ...options
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    async listModels() {
        const response = await fetch(`${this.baseUrl}/v1/models`, {
            headers: this.headers
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }
}

// Usage
const client = new LLMProxyClient('http://localhost:8000', 'your-api-key');

async function example() {
    try {
        // Chat completion
        const response = await client.chatCompletion(
            'gpt-3.5-turbo',
            [
                { role: 'system', content: 'You are a helpful assistant.' },
                { role: 'user', content: 'Explain quantum computing simply.' }
            ],
            { max_tokens: 200, temperature: 0.7 }
        );

        console.log(response.choices[0].message.content);

        // Health check
        const health = await client.healthCheck();
        console.log(`Status: ${health.status}`);

    } catch (error) {
        console.error('Error:', error.message);
    }
}

example();
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# List models
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/v1/models

# Chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [{"role": "user", "content": "Hello!"}],
       "max_tokens": 50
     }'

# Streaming chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [{"role": "user", "content": "Tell me a story"}],
       "stream": true
     }'

# Get metrics
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/metrics

# Provider status
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/providers

# Model management - list provider models
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/v1/providers/openai/models

# Refresh model cache
curl -X POST \
     -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/v1/providers/openai/models/refresh

# Configuration reload
curl -X POST \
     -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/v1/config/reload

# Get active alerts
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/v1/alerts

# Create alert rule
curl -X POST http://localhost:8000/v1/rules \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "high_error_rate",
       "description": "Alert on high error rates",
       "metric_path": "providers.openai.error_rate",
       "condition": ">",
       "threshold": 0.05,
       "severity": "warning",
       "channels": ["log"]
     }'
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  llm-proxy:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

This comprehensive documentation covers all aspects of the LLM Proxy API. For additional support, please refer to the project documentation or create an issue in the repository.