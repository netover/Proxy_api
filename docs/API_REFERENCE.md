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

## Health API

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

# Get all models
response = requests.get('http://localhost:8000/api/models')
models = response.json()['models']

# Search models
response = requests.get('http://localhost:8000/api/models/search?q=gpt-4')
search_results = response.json()['models']

# Refresh models
response = requests.post('http://localhost:8000/api/models/refresh')
```

### JavaScript
```javascript
// Get all models
fetch('http://localhost:8000/api/models')
  .then(response => response.json())
  .then(data => console.log(data.models));

// Search with filters
const params = new URLSearchParams({
  q: 'claude',
  supports_chat: 'true',
  min_context: '100000'
});

fetch(`/api/models/search?${params}`)
  .then(response => response.json())
  .then(data => console.log(data.models));
```

### cURL Examples
```bash
# Basic discovery
curl http://localhost:8000/api/models

# With filters
curl "http://localhost:8000/api/models?provider=openai&supports_chat=true"

# Force refresh
curl -X POST http://localhost:8000/api/models/refresh

# Provider status
curl http://localhost:8000/api/providers/status