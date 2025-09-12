# ProxyAPI Documentation

## Overview

ProxyAPI is a high-performance proxy API for LLM providers with intelligent routing, caching, rate limiting, and circuit breaking capabilities. This documentation provides comprehensive information about all available REST API endpoints.

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Chat Completions](#chat-completions)
  - [Text Completions](#text-completions)
  - [Model Management](#model-management)
  - [Provider Management](#provider-management)
  - [Cache Operations](#cache-operations)
  - [Analytics](#analytics)
  - [Health Checks](#health-checks)
  - [Alerting](#alerting)
  - [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Authentication

ProxyAPI uses API key-based authentication. You can provide your API key in two ways:

### Header Authentication

```http
Authorization: Bearer your-api-key
```

### Custom Header

The API key header can be configured via settings (default: `x-api-key`):

```http
X-API-Key: your-api-key
```

### Configuration

API keys are configured through the `proxy_api_keys` setting in your configuration file. Keys are securely hashed and stored.

## Rate Limiting

ProxyAPI implements multi-level rate limiting to ensure fair usage and prevent abuse:

### Global Rate Limits

- **Default**: 100 requests per minute (configurable via `rate_limit_rpm`)
- **Token Bucket**: Allows burst traffic up to the configured limit

### Endpoint-Specific Limits

| Endpoint | Rate Limit |
|----------|------------|
| `/v1/chat/completions` | 100/minute |
| `/v1/completions` | 100/minute |
| `/v1/models` | 60/minute |
| `/v1/providers/{provider}/models` | 60/minute |
| `/v1/providers/{provider}/model_selection` | 30/minute |
| `/v1/providers/{provider}/models/refresh` | 10/minute |

### Rate Limit Headers

When rate limited, the API returns standard HTTP 429 with these headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "message": "Error description",
    "type": "error_type",
    "code": "error_code",
    "status_code": 400
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `invalid_request_error` | 400 | Invalid request parameters |
| `authentication_error` | 401 | Invalid or missing API key |
| `authorization_error` | 403 | Insufficient permissions |
| `not_found_error` | 404 | Resource not found |
| `rate_limit_error` | 429 | Rate limit exceeded |
| `service_unavailable_error` | 503 | Service temporarily unavailable |
| `provider_error` | 502 | Provider-specific error |
| `internal_error` | 500 | Internal server error |

## Endpoints

### Chat Completions

#### POST `/v1/chat/completions`

Generate chat completions using OpenAI-compatible API.

**Request Body:**

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "stream": false
}
```

**Response (Non-streaming):**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1640995200,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 13,
    "completion_tokens": 12,
    "total_tokens": 25
  }
}
```

**Streaming Response:**

Returns Server-Sent Events (SSE) with incremental updates:

```http
data: {"id": "chatcmpl-abc123", "object": "chat.completion.chunk", "created": 1640995200, "model": "gpt-3.5-turbo", "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": null}]}

data: {"id": "chatcmpl-abc123", "object": "chat.completion.chunk", "created": 1640995200, "model": "gpt-3.5-turbo", "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": null}]}

data: [DONE]
```

### Text Completions

#### POST `/v1/completions`

Generate text completions (legacy OpenAI API).

**Request Body:**

```json
{
  "model": "text-davinci-003",
  "prompt": "Write a haiku about programming:",
  "max_tokens": 50,
  "temperature": 0.7,
  "stream": false
}
```

**Response:**

```json
{
  "id": "cmpl-abc123",
  "object": "text_completion",
  "created": 1640995200,
  "model": "text-davinci-003",
  "choices": [
    {
      "text": "\n\nCode flows like water,\nAlgorithms dance in light,\nBugs hide in shadows.",
      "index": 0,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 23,
    "total_tokens": 31
  }
}
```

### Model Management

#### GET `/v1/models`

List all available models across providers.

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1640995200,
      "owned_by": "openai",
      "provider_type": "openai",
      "status": "available",
      "enabled": true,
      "forced": false
    }
  ]
}
```

#### GET `/v1/providers/{provider_name}/models`

List models for a specific provider.

**Parameters:**
- `provider_name`: Provider name (e.g., "openai", "anthropic")

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-3.5-turbo",
      "created": 1640995200,
      "owned_by": "openai",
      "provider": "openai",
      "status": "active",
      "capabilities": ["text_generation", "chat", "completion"],
      "description": "Model gpt-3.5-turbo from openai"
    }
  ],
  "provider": "openai",
  "total": 1,
  "cached": true,
  "last_refresh": 1640995200
}
```

#### GET `/v1/providers/{provider_name}/models/{model_id}`

Get detailed information about a specific model.

**Response:**

```json
{
  "object": "model",
  "data": {
    "id": "gpt-3.5-turbo",
    "created": 1640995200,
    "owned_by": "openai",
    "provider": "openai",
    "status": "active",
    "capabilities": ["text_generation", "chat", "completion"],
    "description": "Model gpt-3.5-turbo from openai",
    "last_updated": 1640995200
  },
  "provider": "openai",
  "cached": true,
  "last_refresh": 1640995200
}
```

#### PUT `/v1/providers/{provider_name}/model_selection`

Update model selection configuration for a provider.

**Request Body:**

```json
{
  "selected_model": "gpt-4",
  "editable": true,
  "priority": 100,
  "max_tokens": 4096,
  "temperature": 0.7
}
```

**Response:**

```json
{
  "success": true,
  "provider": "openai",
  "selected_model": "gpt-4",
  "updated_at": 1640995200,
  "message": "Model selection updated for provider 'openai'"
}
```

#### POST `/v1/providers/{provider_name}/models/refresh`

Force refresh model cache for a provider.

**Response:**

```json
{
  "success": true,
  "provider": "openai",
  "models_refreshed": 15,
  "cache_cleared": true,
  "duration_ms": 1250.5,
  "timestamp": 1640995200
}
```

### Provider Management

#### GET `/v1/providers`

List all configured providers with detailed information.

**Response:**

```json
{
  "providers": [
    {
      "name": "openai",
      "type": "openai",
      "status": "healthy",
      "models": ["gpt-3.5-turbo", "gpt-4"],
      "priority": 100,
      "enabled": true,
      "forced": false,
      "last_health_check": 1640995200,
      "error_count": 0,
      "success_rate": 99.8,
      "average_latency_ms": 450.2,
      "total_requests": 15420
    }
  ],
  "summary": {
    "total_providers": 3,
    "healthy_providers": 2,
    "total_requests": 45000,
    "average_success_rate": 98.5
  }
}
```

### Cache Operations

#### GET `/v1/cache/stats`

Get comprehensive cache statistics.

**Response:**

```json
{
  "unified_cache": {
    "hit_rate": 85.5,
    "entries": 1250,
    "memory_usage_mb": 45.2,
    "total_requests": 10000,
    "total_hits": 8550,
    "total_misses": 1450
  },
  "model_cache": {
    "hit_rate": 92.3,
    "entries": 150,
    "memory_usage_mb": 8.5
  },
  "provider_cache": {
    "hit_rate": 98.1,
    "entries": 25,
    "memory_usage_mb": 2.1
  },
  "overall_hit_rate": 85.5,
  "total_cache_entries": 1425,
  "cache_memory_usage_mb": 55.8,
  "cache_health": "healthy"
}
```

#### POST `/v1/cache/clear`

Clear cache entries, optionally by category.

**Request Body (optional):**

```json
{
  "category": "responses"
}
```

**Response:**

```json
{
  "message": "Cleared 1250 unified cache entries and 150 model cache entries",
  "unified_cache_cleared": 1250,
  "model_cache_cleared": 150
}
```

#### GET `/v1/cache/health`

Get cache health report.

**Response:**

```json
{
  "status": "healthy",
  "hit_rate": 85.5,
  "memory_usage_percent": 45.2,
  "eviction_rate": 2.1,
  "recommendations": []
}
```

### Analytics

#### GET `/v1/metrics`

Get comprehensive metrics from all providers.

**Response:**

```json
{
  "timestamp": 1640995200,
  "providers": {
    "openai": {
      "total_requests": 15420,
      "successful_requests": 15350,
      "failed_requests": 70,
      "success_rate": 99.5,
      "average_response_time": 450.2,
      "error_rate": 0.5,
      "status": "healthy",
      "models": ["gpt-3.5-turbo", "gpt-4"],
      "priority": 100,
      "enabled": true,
      "forced": false,
      "last_health_check": 1640995200,
      "error_count": 2
    }
  },
  "summary": {
    "total_providers": 3,
    "total_requests": 45000,
    "average_success_rate": 98.5
  }
}
```

#### GET `/v1/metrics/prometheus`

Get Prometheus-compatible metrics.

**Response:**

```
# HELP proxy_api_requests_total Total number of requests
# TYPE proxy_api_requests_total counter
proxy_api_requests_total{provider="openai",status="200"} 15420
proxy_api_requests_total{provider="openai",status="500"} 70

# HELP proxy_api_response_time Response time in seconds
# TYPE proxy_api_response_time histogram
proxy_api_response_time_bucket{provider="openai",le="0.1"} 1200
proxy_api_response_time_bucket{provider="openai",le="0.5"} 14200
```

### Health Checks

#### GET `/v1/health`

Get comprehensive health check information.

**Response:**

```json
{
  "status": "healthy",
  "health_score": 95.0,
  "timestamp": 1640995200,
  "response_time": 0.023,
  "version": "1.0.0",
  "uptime": 3600.5,

  "providers": {
    "total": 3,
    "healthy": 2,
    "degraded": 1,
    "unhealthy": 0,
    "disabled": 0
  },

  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "memory_used_mb": 1024.5,
    "disk_percent": 35.1,
    "network_connections": 45,
    "threads_count": 12
  },

  "alerts": {
    "active": 2,
    "critical": 0,
    "warning": 2,
    "recent": [
      {
        "id": "alert_001",
        "rule_name": "high_error_rate",
        "severity": "warning",
        "message": "Error rate above threshold",
        "timestamp": 1640995100
      }
    ]
  },

  "performance": {
    "total_requests": 15420,
    "successful_requests": 15350,
    "failed_requests": 70,
    "overall_success_rate": 99.5,
    "cache_hit_rate": 85.5,
    "avg_response_time": 0.45
  },

  "details": [
    {
      "name": "openai",
      "type": "openai",
      "status": "healthy",
      "models": 15,
      "enabled": true,
      "forced": false,
      "last_check": 1640995200,
      "error_count": 2
    }
  ]
}
```

#### GET `/health`

Basic health check (root level).

**Response:**

```json
{
  "status": "healthy",
  "service": "proxy-api-gateway",
  "timestamp": 1640995200
}
```

### Alerting

#### GET `/v1/alerts`

Get active alerts with optional filtering.

**Query Parameters:**
- `severity`: Filter by severity (info, warning, error, critical)
- `status`: Filter by status (active, acknowledged, resolved)

**Response:**

```json
{
  "alerts": [
    {
      "id": "alert_001",
      "rule_name": "high_error_rate",
      "severity": "warning",
      "status": "active",
      "message": "Error rate above threshold: 5.2%",
      "value": 5.2,
      "threshold": 2.0,
      "timestamp": 1640995100,
      "acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null
    }
  ],
  "count": 1,
  "timestamp": 1640995200
}
```

#### POST `/v1/alerts/{alert_id}/acknowledge`

Acknowledge an alert.

**Request Body:**

```json
{
  "acknowledged_by": "admin_user"
}
```

**Response:**

```json
{
  "message": "Alert acknowledged successfully"
}
```

#### GET `/v1/alerts/rules`

Get all alert rules.

**Query Parameters:**
- `enabled`: Filter by enabled status (true/false)

**Response:**

```json
{
  "rules": [
    {
      "name": "high_error_rate",
      "description": "Monitor error rate across providers",
      "metric_path": "providers.*.error_rate",
      "condition": ">",
      "threshold": 2.0,
      "severity": "warning",
      "enabled": true,
      "cooldown_minutes": 5,
      "channels": ["log", "email"],
      "custom_message": "Error rate threshold exceeded"
    }
  ],
  "count": 1,
  "timestamp": 1640995200
}
```

#### POST `/v1/alerts/rules`

Create a new alert rule.

**Request Body:**

```json
{
  "name": "cpu_usage_high",
  "description": "High CPU usage alert",
  "metric_path": "system_health.cpu_percent",
  "condition": ">",
  "threshold": 80.0,
  "severity": "warning",
  "enabled": true,
  "cooldown_minutes": 10,
  "channels": ["log", "webhook"],
  "custom_message": "CPU usage is above 80%"
}
```

#### PUT `/v1/alerts/rules/{rule_name}`

Update an existing alert rule.

**Request Body:**

```json
{
  "threshold": 85.0,
  "cooldown_minutes": 15
}
```

#### DELETE `/v1/alerts/rules/{rule_name}`

Delete an alert rule.

**Response:**

```json
{
  "message": "Alert rule deleted successfully"
}
```

### Configuration

#### POST `/v1/config/reload`

Force reload configuration from disk.

**Response:**

```json
{
  "success": true,
  "message": "Configuration reloaded successfully",
  "reload_time_ms": 245.5,
  "config_version": "1.0.0",
  "changes_detected": true
}
```

#### GET `/v1/config/status`

Get current configuration status.

**Response:**

```json
{
  "current_config_path": "/app/config/config.yaml",
  "last_modified": 1640995000,
  "cache_status": {
    "cache_hit_rate": 95.2,
    "cache_misses": 45,
    "memory_usage_mb": 12.5
  },
  "file_watching_enabled": true
}
```

## Usage Examples

### Python

#### Chat Completion

```python
import requests

url = "https://your-proxy-api.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 150
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(result["choices"][0]["message"]["content"])
```

#### Streaming Chat Completion

```python
import requests

url = "https://your-proxy-api.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": True
}

with requests.post(url, headers=headers, json=data, stream=True) as response:
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                if line == 'data: [DONE]':
                    break
                import json
                chunk = json.loads(line[6:])  # Remove 'data: ' prefix
                if chunk['choices'][0]['delta'].get('content'):
                    print(chunk['choices'][0]['delta']['content'], end='')
```

### JavaScript/Node.js

#### Chat Completion

```javascript
const axios = require('axios');

const url = 'https://your-proxy-api.com/v1/chat/completions';
const headers = {
  'Authorization': 'Bearer your-api-key',
  'Content-Type': 'application/json'
};

const data = {
  model: 'gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Hello!' }],
  temperature: 0.7,
  max_tokens: 150
};

axios.post(url, data, { headers })
  .then(response => {
    console.log(response.data.choices[0].message.content);
  })
  .catch(error => {
    console.error('Error:', error.response.data);
  });
```

#### Streaming Chat Completion

```javascript
const axios = require('axios');

const url = 'https://your-proxy-api.com/v1/chat/completions';
const headers = {
  'Authorization': 'Bearer your-api-key',
  'Content-Type': 'application/json'
};

const data = {
  model: 'gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true
};

axios.post(url, data, {
  headers,
  responseType: 'stream'
}).then(response => {
  response.data.on('data', (chunk) => {
    const lines = chunk.toString().split('\n');
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        if (line === 'data: [DONE]') return;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.choices[0].delta.content) {
            process.stdout.write(data.choices[0].delta.content);
          }
        } catch (e) {
          // Ignore parsing errors
        }
      }
    }
  });
});
```

### cURL

#### Chat Completion

```bash
curl -X POST "https://your-proxy-api.com/v1/chat/completions" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

#### Streaming Chat Completion

```bash
curl -X POST "https://your-proxy-api.com/v1/chat/completions" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true
  }'
```

#### List Models

```bash
curl -X GET "https://your-proxy-api.com/v1/models" \
  -H "Authorization: Bearer your-api-key"
```

#### Health Check

```bash
curl -X GET "https://your-proxy-api.com/health"
```

#### Get Metrics

```bash
curl -X GET "https://your-proxy-api.com/v1/metrics" \
  -H "Authorization: Bearer your-api-key"
```

## Best Practices

### Authentication
1. **Secure Key Storage**: Store API keys securely, never in code
2. **Key Rotation**: Regularly rotate API keys
3. **Environment Variables**: Use environment variables for key configuration

### Rate Limiting
1. **Monitor Usage**: Track your API usage patterns
2. **Implement Retries**: Use exponential backoff for rate-limited requests
3. **Batch Requests**: Consider batching multiple requests when possible

### Error Handling
1. **Handle All Error Types**: Implement proper error handling for all HTTP status codes
2. **Retry Logic**: Implement intelligent retry logic for transient failures
3. **Circuit Breaker**: Use circuit breaker pattern for unreliable providers

### Performance
1. **Connection Reuse**: Reuse HTTP connections when possible
2. **Caching**: Leverage response caching for repeated requests
3. **Streaming**: Use streaming for large responses to reduce memory usage

### Monitoring
1. **Health Checks**: Implement regular health checks
2. **Metrics Collection**: Monitor key metrics (latency, error rates, throughput)
3. **Alerting**: Set up alerts for critical issues

## Troubleshooting

### Common Issues

#### Authentication Errors
**Problem**: `401 Unauthorized` or `authentication_error`

**Solutions**:
- Verify API key is correct and not expired
- Check that API key is provided in correct header format
- Ensure API key has necessary permissions

#### Rate Limiting
**Problem**: `429 Too Many Requests`

**Solutions**:
- Check `Retry-After` header for retry timing
- Implement exponential backoff
- Reduce request frequency
- Consider upgrading rate limits

#### Provider Errors
**Problem**: `502 Bad Gateway` or `provider_error`

**Solutions**:
- Check provider status via `/v1/health` endpoint
- Try alternative models or providers
- Wait for provider to recover
- Check provider-specific error messages

#### Timeout Errors
**Problem**: Request timeout

**Solutions**:
- Increase timeout values in configuration
- Reduce request size (fewer tokens, shorter prompts)
- Use streaming for large responses
- Check network connectivity

#### Cache Issues
**Problem**: Stale or missing cached data

**Solutions**:
- Force cache refresh using `/v1/cache/clear`
- Check cache health via `/v1/cache/health`
- Verify cache configuration settings

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
export LOG_LEVEL=DEBUG
```

### Health Check Commands

```bash
# Quick health check
curl -X GET "https://your-api.com/health"

# Detailed health check
curl -X GET "https://your-api.com/v1/health" \
  -H "Authorization: Bearer your-api-key"

# Check provider status
curl -X GET "https://your-api.com/v1/providers" \
  -H "Authorization: Bearer your-api-key"
```

### Performance Monitoring

```bash
# Get metrics
curl -X GET "https://your-api.com/v1/metrics" \
  -H "Authorization: Bearer your-api-key"

# Get cache stats
curl -X GET "https://your-api.com/v1/cache/stats" \
  -H "Authorization: Bearer your-api-key"

# Get latency metrics
curl -X GET "https://your-api.com/analytics/latency" \
  -H "Authorization: Bearer your-api-key"
```

### Configuration Issues

```bash
# Check config status
curl -X GET "https://your-api.com/v1/config/status" \
  -H "Authorization: Bearer your-api-key"

# Reload configuration
curl -X POST "https://your-api.com/v1/config/reload" \
  -H "Authorization: Bearer your-api-key"
```

### Logging and Alerting

```bash
# Get recent logs
curl -X GET "https://your-api.com/analytics/logs?limit=50" \
  -H "Authorization: Bearer your-api-key"

# Get active alerts
curl -X GET "https://your-api.com/alerts" \
  -H "Authorization: Bearer your-api-key"

# Acknowledge alert
curl -X POST "https://your-api.com/alerts/{alert_id}/acknowledge" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"acknowledged_by": "your_name"}'
```

---

This documentation provides comprehensive coverage of the ProxyAPI endpoints and features. For additional support or questions, please refer to the project documentation or contact the development team.