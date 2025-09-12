# API Reference

Complete API documentation for the Model Discovery system.

## Base URL
```
http://localhost:8000
```

## Authentication
Most endpoints don't require authentication. Provider-specific endpoints use API keys configured in `config.yaml`.

## Content Types
- **Request**: `application/json`
- **Response**: `application/json`

## API Versions
- **v1**: Stable API for chat completions, models, etc.
- **v2**: Enhanced API with performance optimizations (recommended)

## Rate Limiting
All endpoints are subject to rate limiting:
- **Default**: 1000 requests per minute
- **Burst**: 50 requests
- Rate limit headers are included in responses

---

## Models API

### Get All Models
Retrieve all discovered models from all configured providers.

```http
GET /api/models
```

#### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `provider` | string | Filter by provider name | `openai` |
| `supports_chat` | boolean | Filter models that support chat | `true` |
| `supports_completion` | boolean | Filter models that support completion | `true` |
| `min_context` | integer | Minimum context length | `4000` |
| `max_cost` | float | Maximum cost per 1K tokens | `0.05` |
| `refresh` | boolean | Force refresh from providers | `true` |

#### Example Request
```bash
curl "http://localhost:8000/api/models?provider=openai&supports_chat=true"
```

#### Example Response
```json
{
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "openai",
      "context_length": 8192,
      "max_tokens": 4096,
      "supports_chat": true,
      "supports_completion": true,
      "input_cost": 0.03,
      "output_cost": 0.06,
      "description": "Most capable GPT-4 model",
      "capabilities": ["function_calling", "vision", "json_mode"],
      "created_at": "2023-03-14T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "gpt-3.5-turbo",
      "name": "GPT-3.5 Turbo",
      "provider": "openai",
      "context_length": 4096,
      "max_tokens": 2048,
      "supports_chat": true,
      "supports_completion": true,
      "input_cost": 0.0015,
      "output_cost": 0.002,
      "description": "Fast and cost-effective GPT-3.5 model",
      "capabilities": ["function_calling"],
      "created_at": "2022-11-30T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 2,
  "providers": ["openai"],
  "timestamp": "2024-01-15T10:30:00Z",
  "cache_hit": true
}
```

#### Response Schema
| Field | Type | Description |
|-------|------|-------------|
| `models` | array | List of model objects |
| `count` | integer | Total number of models |
| `providers` | array | List of active providers |
| `timestamp` | string | ISO 8601 timestamp of last update |
| `cache_hit` | boolean | Whether response came from cache |

---

### Search Models
Search for models using various criteria.

```http
GET /api/models/search
```

#### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query (searches name, id, description) | `gpt-4` |
| `provider` | string | Filter by provider | `anthropic` |
| `supports_chat` | boolean | Chat capability filter | `true` |
| `supports_completion` | boolean | Completion capability filter | `true` |
| `min_context` | integer | Minimum context length | `8000` |
| `max_input_cost` | float | Maximum input cost per 1K tokens | `0.05` |
| `max_output_cost` | float | Maximum output cost per 1K tokens | `0.1` |
| `capabilities` | array | Required capabilities | `["vision","function_calling"]` |

#### Example Request
```bash
curl "http://localhost:8000/api/models/search?q=claude&supports_chat=true&min_context=100000"
```

#### Example Response
```json
{
  "models": [
    {
      "id": "claude-3-opus-20240229",
      "name": "Claude 3 Opus",
      "provider": "anthropic",
      "context_length": 200000,
      "max_tokens": 4096,
      "supports_chat": true,
      "supports_completion": false,
      "input_cost": 0.015,
      "output_cost": 0.075,
      "description": "Most powerful Claude model for complex reasoning",
      "capabilities": ["vision", "tool_use", "json_mode"],
      "created_at": "2024-02-29T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1,
  "query": "claude",
  "filters_applied": {
    "supports_chat": true,
    "min_context": 100000
  }
}
```

---

### Get Model Details
Get detailed information about a specific model.

```http
GET /api/models/{model_id}
```

#### Path Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `model_id` | string | The model identifier | `gpt-4` |

#### Example Request
```bash
curl "http://localhost:8000/api/models/gpt-4"
```

#### Example Response
```json
{
  "model": {
    "id": "gpt-4",
    "name": "GPT-4",
    "provider": "openai",
    "context_length": 8192,
    "max_tokens": 4096,
    "supports_chat": true,
    "supports_completion": true,
    "input_cost": 0.03,
    "output_cost": 0.06,
    "description": "Most capable GPT-4 model",
    "capabilities": ["function_calling", "vision", "json_mode"],
    "training_data": "Up to Apr 2023",
    "knowledge_cutoff": "2023-04",
    "created_at": "2023-03-14T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "provider_info": {
    "name": "openai",
    "status": "active",
    "last_check": "2024-01-15T10:30:00Z"
  }
}
```

---

### Refresh Models
Force a refresh of models from all providers.

```http
POST /api/models/refresh
```

#### Request Body (Optional)
```json
{
  "providers": ["openai", "anthropic"],
  "force": true
}
```

#### Example Request
```bash
curl -X POST "http://localhost:8000/api/models/refresh" \
  -H "Content-Type: application/json" \
  -d '{"providers": ["openai"], "force": true}'
```

#### Example Response
```json
{
  "status": "success",
  "message": "Models refreshed successfully",
  "models_discovered": 25,
  "providers_updated": ["openai"],
  "duration_ms": 1250,
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

## Providers API

### Get Provider Status
Get the status of all configured providers.

```http
GET /api/providers/status
```

#### Example Request
```bash
curl "http://localhost:8000/api/providers/status"
```

#### Example Response
```json
{
  "providers": {
    "openai": {
      "status": "active",
      "last_check": "2024-01-15T10:30:00Z",
      "models_count": 15,
      "error": null,
      "response_time_ms": 245
    },
    "anthropic": {
      "status": "active",
      "last_check": "2024-01-15T10:30:00Z",
      "models_count": 8,
      "error": null,
      "response_time_ms": 189
    },
    "cohere": {
      "status": "error",
      "last_check": "2024-01-15T10:30:00Z",
      "models_count": 0,
      "error": "Authentication failed",
      "response_time_ms": 120
    }
  },
  "summary": {
    "total_providers": 3,
    "active_providers": 2,
    "total_models": 23,
    "last_update": "2024-01-15T10:30:00Z"
  }
}
```

---

### Get Provider Models
Get models from a specific provider.

```http
GET /api/providers/{provider_name}/models
```

#### Path Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `provider_name` | string | Provider name | `openai` |

#### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `refresh` | boolean | Force refresh from provider | `true` |

#### Example Request
```bash
curl "http://localhost:8000/api/providers/openai/models?refresh=true"
```

#### Example Response
```json
{
  "provider": "openai",
  "models": [...],
  "count": 15,
  "last_updated": "2024-01-15T10:30:00Z",
  "cache_hit": false
}
```

---

## Cache API

### Get Cache Statistics
Get cache performance statistics.

```http
GET /api/cache/stats
```

#### Example Request
```bash
curl "http://localhost:8000/api/cache/stats"
```

#### Example Response
```json
{
  "cache_stats": {
    "hits": 1250,
    "misses": 45,
    "hit_rate": 96.5,
    "total_entries": 23,
    "memory_usage_mb": 2.3,
    "oldest_entry": "2024-01-15T09:00:00Z",
    "newest_entry": "2024-01-15T10:30:00Z"
  },
  "provider_stats": {
    "openai": {
      "hits": 450,
      "misses": 15,
      "hit_rate": 96.8
    },
    "anthropic": {
      "hits": 320,
      "misses": 10,
      "hit_rate": 97.0
    }
  }
}
```

---

### Clear Cache
Clear the model discovery cache.

```http
DELETE /api/cache
```

#### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `provider` | string | Clear cache for specific provider | `openai` |

#### Example Request
```bash
curl -X DELETE "http://localhost:8000/api/cache?provider=openai"
```

#### Example Response
```json
{
  "status": "success",
  "message": "Cache cleared for provider: openai",
  "cleared_entries": 15
}
```

---

## Performance Monitoring API

### Get Performance Metrics
Get comprehensive performance metrics for all providers and system components.

```http
GET /metrics
```

#### Example Request
```bash
curl "http://localhost:8000/metrics"
```

#### Example Response
```json
{
  "providers": {
    "openai": {
      "total_requests": 1250,
      "successful_requests": 1225,
      "failed_requests": 25,
      "success_rate": 0.98,
      "avg_response_time": 245.8,
      "total_tokens": 50000,
      "models": {
        "gpt-4": {
          "total_requests": 450,
          "successful_requests": 445,
          "avg_response_time": 320.5,
          "total_tokens": 25000
        }
      }
    }
  },
  "summarization": {
    "total_summaries": 150,
    "cache_hits": 120,
    "cache_misses": 30,
    "avg_latency": 45.2
  },
  "cache_performance": {
    "hit_rate": 0.85,
    "total_requests": 2000,
    "cache_hits": 1700,
    "entries": 500,
    "memory_usage_mb": 45.2
  },
  "connection_pool": {
    "active_connections": 25,
    "max_connections": 100,
    "pending_requests": 2,
    "error_count": 0
  },
  "system_health": {
    "cpu_percent": 45.2,
    "memory_percent": 68.5,
    "memory_used_mb": 552.3,
    "disk_percent": 32.1
  },
  "uptime": 3600.5
}
```

---

### Get Prometheus Metrics
Get metrics in Prometheus format for integration with monitoring systems.

```http
GET /metrics/prometheus
```

#### Example Request
```bash
curl "http://localhost:8000/metrics/prometheus"
```

#### Example Response
```bash
# HELP proxy_api_requests_total Total number of requests
# TYPE proxy_api_requests_total counter
proxy_api_requests_total{provider="openai"} 1250
proxy_api_requests_total{provider="anthropic"} 890

# HELP proxy_api_response_time_avg Average response time in seconds
# TYPE proxy_api_response_time_avg gauge
proxy_api_response_time_avg{provider="openai"} 0.246
proxy_api_response_time_avg{provider="anthropic"} 0.189
```

---

## Enhanced Health API

### Health Check
Check the health of the model discovery system.

```http
GET /health
```

#### Example Request
```bash
curl "http://localhost:8000/health"
```

#### Example Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "discovery": "ok",
    "cache": "ok",
    "providers": {
      "openai": "ok",
      "anthropic": "ok",
      "cohere": "error"
    }
  },
  "metrics": {
    "uptime_seconds": 3600,
    "memory_usage_mb": 45.2,
    "cache_hit_rate": 96.5
  }
}
```

---

## Context Condensation API

### Summarize Context
Request intelligent summarization of long conversation contexts to reduce token usage and improve performance.

```http
POST /api/condense
```

#### Request Body
```json
{
  "messages": [
    {"role": "user", "content": "Long conversation text..."},
    {"role": "assistant", "content": "Response..."}
  ],
  "max_tokens": 512,
  "model": "gpt-3.5-turbo",
  "strategy": "truncate"
}
```

#### Query Parameters
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `async` | boolean | Process asynchronously | `false` |
| `priority` | string | Processing priority (low, medium, high) | `medium` |

#### Example Request
```bash
curl -X POST "http://localhost:8000/api/condense" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Very long conversation..."},
      {"role": "assistant", "content": "Detailed response..."}
    ],
    "max_tokens": 512
  }'
```

#### Example Response
```json
{
  "status": "success",
  "summary": "Condensed version of the conversation...",
  "original_tokens": 2500,
  "condensed_tokens": 450,
  "compression_ratio": 0.18,
  "processing_time_ms": 245,
  "cache_hit": false
}
```

---

### Asynchronous Summarization
For long contexts, request asynchronous processing to avoid blocking.

```http
POST /api/condense/async
```

#### Example Response
```json
{
  "request_id": "req_1234567890",
  "status": "processing",
  "estimated_time_ms": 2000,
  "message": "Summarization request queued for processing"
}
```

---

### Get Summarization Status
Check the status of an asynchronous summarization request.

```http
GET /api/condense/status/{request_id}
```

#### Example Response
```json
{
  "request_id": "req_1234567890",
  "status": "completed",
  "result": {
    "summary": "Condensed conversation...",
    "original_tokens": 2500,
    "condensed_tokens": 450,
    "compression_ratio": 0.18
  },
  "processing_time_ms": 1845,
  "completed_at": "2024-01-15T10:35:00Z"
}
```

---

## Load Testing API

### Start Load Test
Initiate a load test with specified parameters.

```http
POST /api/load-test/start
```

#### Request Body
```json
{
  "tier": "medium",
  "duration_minutes": 5,
  "target_rps": 20,
  "providers": ["openai", "anthropic"],
  "models": ["gpt-3.5-turbo", "claude-3-haiku"],
  "scenarios": ["chat_completion", "model_discovery"]
}
```

#### Example Response
```json
{
  "test_id": "load_test_123",
  "status": "running",
  "configuration": {
    "tier": "medium",
    "users": 100,
    "duration": "5m",
    "target_rps": 20
  },
  "started_at": "2024-01-15T10:30:00Z"
}
```

---

### Get Load Test Results
Retrieve results from a completed load test.

```http
GET /api/load-test/results/{test_id}
```

#### Example Response
```json
{
  "test_id": "load_test_123",
  "status": "completed",
  "duration_seconds": 300,
  "results": {
    "total_requests": 6000,
    "successful_requests": 5985,
    "failed_requests": 15,
    "average_response_time_ms": 245,
    "p95_response_time_ms": 450,
    "p99_response_time_ms": 890,
    "requests_per_second": 20.1,
    "error_rate": 0.0025
  },
  "provider_breakdown": {
    "openai": {
      "requests": 3000,
      "success_rate": 0.995,
      "avg_response_time_ms": 280
    },
    "anthropic": {
      "requests": 3000,
      "success_rate": 0.997,
      "avg_response_time_ms": 210
    }
  }
}
```

---

## Chaos Engineering API

### Start Chaos Experiment
Initiate chaos engineering experiments to test system resilience.

```http
POST /api/chaos/start
```

#### Request Body
```json
{
  "experiment_name": "network_degradation_test",
  "duration_minutes": 10,
  "faults": [
    {
      "type": "delay",
      "target": "openai",
      "severity": "medium",
      "probability": 0.1,
      "duration_ms": 500
    },
    {
      "type": "error",
      "target": "anthropic",
      "severity": "low",
      "probability": 0.05,
      "error_code": 503
    }
  ]
}
```

#### Example Response
```json
{
  "experiment_id": "chaos_exp_456",
  "status": "running",
  "configuration": {
    "name": "network_degradation_test",
    "duration": "10m",
    "faults": 2
  },
  "started_at": "2024-01-15T10:30:00Z"
}
```

---

### Stop Chaos Experiment
Stop a running chaos engineering experiment.

```http
POST /api/chaos/stop/{experiment_id}
```

#### Example Response
```json
{
  "experiment_id": "chaos_exp_456",
  "status": "stopped",
  "duration_seconds": 450,
  "results": {
    "total_faults_injected": 45,
    "system_degradation_detected": false,
    "recovery_time_seconds": 12
  }
}
```

---

## Configuration Management API

### Get Configuration Status
Get the current configuration status and validation results.

```http
GET /api/config/status
```

#### Example Response
```json
{
  "status": "valid",
  "last_loaded": "2024-01-15T10:30:00Z",
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

---

### Reload Configuration
Trigger a hot reload of the configuration file.

```http
POST /api/config/reload
```

#### Example Response
```json
{
  "status": "success",
  "message": "Configuration reloaded successfully",
  "changes_detected": true,
  "providers_updated": ["openai"],
  "reload_time_ms": 67
}
```

---

## Error Handling

### Error Response Format
All errors follow a consistent format:

```json
{
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "Model 'gpt-5' not found",
    "details": {
      "model_id": "gpt-5",
      "available_models": ["gpt-4", "gpt-3.5-turbo"]
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Codes
| Code | Description | HTTP Status |
|------|-------------|-------------|
| `MODEL_NOT_FOUND` | Requested model doesn't exist | 404 |
| `PROVIDER_ERROR` | Provider API error | 502 |
| `INVALID_FILTER` | Invalid filter parameter | 400 |
| `CACHE_ERROR` | Cache operation failed | 500 |
| `RATE_LIMITED` | Rate limit exceeded | 429 |
| `UNAUTHORIZED` | Invalid or missing API key | 401 |

---

## Rate Limiting

### Rate Limit Headers
All API responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

### Rate Limit Response
When rate limit is exceeded:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Pagination

### Pagination Parameters
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `limit` | integer | Number of results per page | 50 |
| `offset` | integer | Number of results to skip | 0 |
| `cursor` | string | Cursor for pagination | - |

### Pagination Response
```json
{
  "models": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 125,
    "has_next": true,
    "next_offset": 50,
    "next_cursor": "eyJpZCI6Im1vZGVsLTUwIn0="
  }
}
```

---

## WebSocket API

### Real-time Model Updates
Subscribe to real-time model updates via WebSocket.

```http
GET /ws/models
```

#### Example JavaScript Client
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/models');

ws.onmessage = function(event) {
  const update = JSON.parse(event.data);
  console.log('Model update:', update);
};

ws.onopen = function() {
  console.log('Connected to model updates');
};
```

#### Update Message Format
```json
{
  "type": "model_added",
  "model": {
    "id": "new-model",
    "name": "New Model",
    "provider": "openai"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## SDK Examples

### Python
```python
import requests
import asyncio
import aiohttp

# Synchronous examples
def sync_examples():
    # Get all models
    response = requests.get('http://localhost:8000/api/models')
    models = response.json()['models']

    # Search models
    response = requests.get('http://localhost:8000/api/models/search?q=gpt-4')
    search_results = response.json()['models']

    # Refresh models
    response = requests.post('http://localhost:8000/api/models/refresh')

    # Get performance metrics
    metrics = requests.get('http://localhost:8000/metrics').json()

    # Health check
    health = requests.get('http://localhost:8000/health').json()

    # Context condensation
    condense_response = requests.post('http://localhost:8000/api/condense', json={
        "messages": [{"role": "user", "content": "Long text to summarize..."}],
        "max_tokens": 512
    })

# Asynchronous examples
async def async_examples():
    async with aiohttp.ClientSession() as session:
        # Get models asynchronously
        async with session.get('http://localhost:8000/api/models') as response:
            models = await response.json()

        # Performance metrics
        async with session.get('http://localhost:8000/metrics') as response:
            metrics = await response.json()

        # Context condensation
        async with session.post('http://localhost:8000/api/condense', json={
            "messages": [{"role": "user", "content": "Long conversation..."}],
            "max_tokens": 512
        }) as response:
            summary = await response.json()
```

### JavaScript
```javascript
// Modern async/await examples
async function apiExamples() {
  const baseUrl = 'http://localhost:8000';

  try {
    // Get all models
    const modelsResponse = await fetch(`${baseUrl}/api/models`);
    const modelsData = await modelsResponse.json();
    console.log('Models:', modelsData.models);

    // Search with filters
    const searchParams = new URLSearchParams({
      q: 'claude',
      supports_chat: 'true',
      min_context: '100000'
    });
    const searchResponse = await fetch(`${baseUrl}/api/models/search?${searchParams}`);
    const searchData = await searchResponse.json();
    console.log('Search results:', searchData.models);

    // Get performance metrics
    const metricsResponse = await fetch(`${baseUrl}/metrics`);
    const metrics = await metricsResponse.json();
    console.log('Performance metrics:', metrics);

    // Health check
    const healthResponse = await fetch(`${baseUrl}/health`);
    const health = await healthResponse.json();
    console.log('Health status:', health.status);

    // Context condensation
    const condenseResponse = await fetch(`${baseUrl}/api/condense`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: 'Long conversation to summarize...' }],
        max_tokens: 512
      })
    });
    const summary = await condenseResponse.json();
    console.log('Summary:', summary);

  } catch (error) {
    console.error('API call failed:', error);
  }
}

// WebSocket example for real-time updates
function setupWebSocket() {
  const ws = new WebSocket('ws://localhost:8000/ws/models');

  ws.onopen = () => {
    console.log('Connected to model updates');
  };

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log('Model update:', update);

    // Handle different update types
    switch (update.type) {
      case 'model_added':
        console.log('New model added:', update.model);
        break;
      case 'model_updated':
        console.log('Model updated:', update.model);
        break;
      case 'provider_status_changed':
        console.log('Provider status changed:', update.provider);
        break;
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  return ws;
}
```

### cURL Examples
```bash
# === Model Discovery ===
# Basic discovery
curl http://localhost:8000/api/models

# With filters
curl "http://localhost:8000/api/models?provider=openai&supports_chat=true"

# Search models
curl "http://localhost:8000/api/models/search?q=gpt-4&min_context=8000"

# Force refresh
curl -X POST http://localhost:8000/api/models/refresh

# Provider status
curl http://localhost:8000/api/providers/status

# === Performance & Monitoring ===
# Get performance metrics
curl http://localhost:8000/metrics

# Get Prometheus metrics
curl http://localhost:8000/metrics/prometheus

# Health check
curl http://localhost:8000/health

# Detailed health check
curl "http://localhost:8000/health?detailed=true"

# Provider health
curl http://localhost:8000/health/providers

# System health
curl http://localhost:8000/health/system

# === Cache Management ===
# Cache statistics
curl http://localhost:8000/api/cache/stats

# Clear cache
curl -X DELETE http://localhost:8000/api/cache

# Clear specific provider cache
curl -X DELETE "http://localhost:8000/api/cache?provider=openai"

# === Context Condensation ===
# Synchronous summarization
curl -X POST http://localhost:8000/api/condense \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Very long conversation..."}],
    "max_tokens": 512
  }'

# Asynchronous summarization
curl -X POST http://localhost:8000/api/condense/async \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Very long conversation..."}],
    "max_tokens": 512
  }'

# Check summarization status
curl http://localhost:8000/api/condense/status/req_1234567890

# === Load Testing ===
# Start load test
curl -X POST http://localhost:8000/api/load-test/start \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "medium",
    "duration_minutes": 5,
    "target_rps": 20
  }'

# Get load test results
curl http://localhost:8000/api/load-test/results/load_test_123

# === Chaos Engineering ===
# Start chaos experiment
curl -X POST http://localhost:8000/api/chaos/start \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_name": "network_test",
    "duration_minutes": 10,
    "faults": [{
      "type": "delay",
      "target": "openai",
      "severity": "medium",
      "probability": 0.1
    }]
  }'

# Stop chaos experiment
curl -X POST http://localhost:8000/api/chaos/stop/chaos_exp_456

# === Configuration Management ===
# Configuration status
curl http://localhost:8000/api/config/status

# Reload configuration
curl -X POST http://localhost:8000/api/config/reload