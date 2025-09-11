# Model Management API Documentation

This document describes the RESTful API endpoints for model management in the ProxyAPI system.

## Overview

The Model Management API provides endpoints for discovering, managing, and configuring models across different AI providers. These endpoints are designed to be RESTful and follow OpenAPI standards.

## Base URL
All endpoints are prefixed with: `/v1/providers/{provider_name}`

## Authentication
All endpoints require API key authentication via the `Authorization: Bearer {api_key}` header.

## Endpoints

### 1. List Provider Models
**GET** `/v1/providers/{provider_name}/models`

List all available models for a specific provider.

**Parameters:**
- `provider_name` (path): Name of the provider (e.g., 'openai', 'anthropic')

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
      "max_tokens": 4096,
      "pricing": {"input": 0.03, "output": 0.06},
      "description": "GPT-4 language model",
      "version": "2023-03-15",
      "last_updated": 1709251200
    }
  ],
  "provider": "openai",
  "total": 1,
  "cached": true,
  "last_refresh": 1709251200
}
```

**Rate Limit:** 60 requests per minute

### 2. Get Model Details
**GET** `/v1/providers/{provider_name}/models/{model_id}`

Get detailed information for a specific model.

**Parameters:**
- `provider_name` (path): Name of the provider
- `model_id` (path): Unique model identifier

**Response:**
```json
{
  "object": "model",
  "data": {
    "id": "claude-3-opus-20240229",
    "object": "model",
    "created": 1709251200,
    "owned_by": "anthropic",
    "provider": "anthropic",
    "status": "active",
    "capabilities": ["text_generation", "chat", "vision"],
    "context_window": 200000,
    "max_tokens": 4096,
    "pricing": {"input": 0.015, "output": 0.075},
    "description": "Claude 3 Opus - Most capable model",
    "version": "2024-02-29",
    "last_updated": 1709251200
  },
  "provider": "anthropic",
  "cached": true,
  "last_refresh": 1709251200
}
```

**Rate Limit:** 60 requests per minute

### 3. Update Model Selection
**PUT** `/v1/providers/{provider_name}/model_selection`

Update model selection configuration for a provider.

**Parameters:**
- `provider_name` (path): Name of the provider

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

**Response:**
```json
{
  "success": true,
  "provider": "openai",
  "selected_model": "gpt-4",
  "updated_at": 1709251200,
  "message": "Model selection updated for provider 'openai'"
}
```

**Rate Limit:** 30 requests per minute

### 4. Refresh Model Cache
**POST** `/v1/providers/{provider_name}/models/refresh`

Force refresh the model cache for a provider.

**Parameters:**
- `provider_name` (path): Name of the provider

**Response:**
```json
{
  "success": true,
  "provider": "openai",
  "models_refreshed": 2,
  "cache_cleared": true,
  "duration_ms": 1250.5,
  "timestamp": 1709251200
}
```

**Rate Limit:** 10 requests per minute

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": {
    "message": "Error description",
    "type": "error_type",
    "code": "error_code"
  }
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (Invalid parameters)
- `404` - Not Found (Provider or model not found)
- `429` - Rate Limited
- `500` - Internal Server Error

## Rate Limiting

Each endpoint has specific rate limits:
- List models: 60 requests/minute
- Get model details: 60 requests/minute
- Update model selection: 30 requests/minute
- Refresh models: 10 requests/minute

## Examples

### List OpenAI Models
```bash
curl -X GET "https://api.example.com/v1/providers/openai/models" \
  -H "Authorization: Bearer your-api-key"
```

### Update Model Selection
```bash
curl -X PUT "https://api.example.com/v1/providers/openai/model_selection" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"selected_model": "gpt-4", "editable": true}'
```

### Refresh Model Cache
```bash
curl -X POST "https://api.example.com/v1/providers/anthropic/models/refresh" \
  -H "Authorization: Bearer your-api-key"