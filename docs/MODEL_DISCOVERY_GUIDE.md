# Model Discovery Guide

A comprehensive guide to understanding and using the model discovery system in ProxyAPI.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Configuration](#configuration)
- [Using the Web Interface](#using-the-web-interface)
- [Using the API](#using-the-api)
- [Advanced Features](#advanced-features)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Overview

The Model Discovery system automatically discovers and catalogs available AI models from multiple providers including OpenAI, Anthropic, Azure OpenAI, Cohere, and more. It provides:

- **Automatic Discovery**: Automatically fetches available models from configured providers
- **Unified Interface**: Consistent API across all providers
- **Caching**: Intelligent caching to reduce API calls and improve performance
- **Filtering**: Advanced filtering capabilities for finding specific models
- **Real-time Updates**: Refresh capabilities to get the latest models
- **Cost Information**: Pricing data for informed decision-making

## Quick Start

### 1. Basic Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python web_ui.py
```

### 2. Configure Providers

Create or update your `config.yaml`:

```yaml
providers:
  openai:
    api_key: "your-openai-api-key"
    enabled: true
    
  anthropic:
    api_key: "your-anthropic-api-key"
    enabled: true
    
  azure_openai:
    api_key: "your-azure-api-key"
    endpoint: "https://your-resource.openai.azure.com/"
    enabled: true
```

### 3. Discover Models

**Via Web Interface:**
1. Navigate to `http://localhost:8000`
2. Click "Discover Models" to refresh the model list
3. Browse available models with their capabilities and pricing

**Via API:**
```bash
# Get all models
curl http://localhost:8000/api/models

# Search for specific models
curl "http://localhost:8000/api/models/search?q=gpt-4"

# Get provider status
curl http://localhost:8000/api/providers/status
```

## Core Concepts

### Model Information Structure

Each discovered model includes:

```json
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
  "description": "Most capable GPT-4 model"
}
```

### Provider Types

| Provider | Description | Key Features |
|----------|-------------|--------------|
| **OpenAI** | OpenAI GPT models | Chat, completion, embeddings |
| **Anthropic** | Claude models | Advanced reasoning, safety |
| **Azure OpenAI** | Microsoft Azure hosted OpenAI | Enterprise features, regional deployment |
| **Cohere** | Command and Embed models | Multilingual, retrieval |
| **OpenRouter** | Unified API gateway | Access to multiple providers |

## Configuration

### Provider Configuration

Each provider can be configured with specific parameters:

```yaml
providers:
  openai:
    api_key: "sk-..."
    organization: "org-..."  # Optional
    base_url: "https://api.openai.com/v1"  # Optional
    timeout: 30  # Optional
    enabled: true
    
  anthropic:
    api_key: "sk-ant-..."
    base_url: "https://api.anthropic.com"  # Optional
    timeout: 30  # Optional
    enabled: true
    
  azure_openai:
    api_key: "your-azure-key"
    endpoint: "https://your-resource.openai.azure.com/"
    api_version: "2023-12-01-preview"  # Optional
    timeout: 30  # Optional
    enabled: true
```

### Discovery Settings

```yaml
discovery:
  # Cache settings
  cache_ttl: 300  # 5 minutes
  cache_dir: "./cache"
  
  # Discovery settings
  timeout: 30  # seconds
  max_retries: 3
  
  # Filtering
  default_filters:
    min_context_length: 1000
    max_cost_per_token: 0.1
    
  # Update settings
  auto_refresh: true
  refresh_interval: 3600  # 1 hour
```

## Using the Web Interface

### Model Browser

The web interface provides an intuitive model browser:

1. **Model List View**
   - Displays all available models in a table
   - Shows key metrics: name, provider, context length, cost
   - Sortable columns for easy comparison

2. **Model Details**
   - Click any model for detailed information
   - Full capabilities and limitations
   - Pricing calculator for estimated costs
   - Sample usage code

3. **Filtering & Search**
   - Filter by provider, capabilities, or cost range
   - Real-time search across model names and descriptions
   - Save favorite filters for quick access

4. **Refresh & Updates**
   - Manual refresh button for immediate updates
   - Auto-refresh toggle for periodic updates
   - Last updated timestamp display

### Dashboard Features

- **Provider Status**: Real-time status of all configured providers
- **Usage Statistics**: Model usage patterns and trends
- **Cost Tracking**: Estimated costs based on usage
- **Performance Metrics**: Response times and reliability

## Using the API

### REST API Endpoints

#### Get All Models
```http
GET /api/models
```

**Response:**
```json
{
  "models": [...],
  "count": 25,
  "timestamp": "2024-01-15T10:30:00Z",
  "providers": ["openai", "anthropic"]
}
```

#### Search Models
```http
GET /api/models/search?q=gpt-4&provider=openai
```

**Query Parameters:**
- `q`: Search query (searches name, id, description)
- `provider`: Filter by provider
- `supports_chat`: Filter by chat capability
- `supports_completion`: Filter by completion capability
- `min_context`: Minimum context length
- `max_cost`: Maximum cost per token

#### Get Model Details
```http
GET /api/models/{model_id}
```

#### Refresh Models
```http
POST /api/models/refresh
```

#### Get Provider Status
```http
GET /api/providers/status
```

### Python SDK Usage

```python
import asyncio
from src.core.model_discovery import ModelDiscovery
from src.core.cache_manager import CacheManager
from src.core.provider_factory import ProviderFactory

async def discover_models():
    # Initialize discovery service
    cache_manager = CacheManager()
    provider_factory = ProviderFactory()
    discovery = ModelDiscovery(cache_manager, provider_factory)
    
    # Discover all models
    config = {
        "providers": {
            "openai": {"api_key": "your-key", "enabled": True},
            "anthropic": {"api_key": "your-key", "enabled": True}
        }
    }
    
    models = await discovery.discover_all_models(config)
    
    # Filter models
    chat_models = [m for m in models if m.supports_chat]
    cheap_models = [m for m in models if m.input_cost < 0.01]
    
    return models

# Run discovery
models = asyncio.run(discover_models())
```

## Advanced Features

### Custom Providers

You can add custom providers by extending the base discovery class:

```python
from src.providers.base_discovery import BaseDiscovery
from src.models.model_info import ModelInfo

class CustomProviderDiscovery(BaseDiscovery):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.custom.com")
    
    async def get_models(self):
        # Implement your custom discovery logic
        response = await self._make_request("GET", "/models")
        models = []
        
        for model_data in response.json()["models"]:
            model = ModelInfo(
                id=model_data["id"],
                name=model_data["name"],
                provider="custom",
                context_length=model_data.get("max_tokens", 4096),
                max_tokens=model_data.get("max_tokens", 2048),
                supports_chat=model_data.get("supports_chat", True),
                supports_completion=model_data.get("supports_completion", True),
                input_cost=model_data.get("input_cost", 0.01),
                output_cost=model_data.get("output_cost", 0.02)
            )
            models.append(model)
        
        return models
```

### Advanced Filtering

```python
# Complex filtering example
filters = {
    "provider": ["openai", "anthropic"],
    "supports_chat": True,
    "min_context_length": 4000,
    "max_input_cost": 0.05,
    "capabilities": ["function_calling", "vision"]
}

filtered_models = await discovery.discover_all_models(
    config, 
    filters=filters
)
```

### Caching Strategies

#### Memory Cache
- Fast in-memory caching for frequently accessed data
- Configurable TTL (Time To Live)
- Automatic cleanup of expired entries

#### Disk Cache
- Persistent caching across application restarts
- JSON-based storage for easy debugging
- Compression for large datasets

#### Cache Invalidation
```python
# Manual cache invalidation
await discovery.invalidate_cache(provider="openai")

# Invalidate specific models
await discovery.invalidate_cache(model_id="gpt-4")

# Clear all cache
await discovery.clear_cache()
```

## Performance Optimization

### Cache Tuning

```yaml
# Optimized cache settings
discovery:
  cache_ttl: 1800  # 30 minutes for stable providers
  cache_dir: "/tmp/fast_cache"  # Use tmpfs for better performance
  
  # Preload popular models
  preload_models:
    - "gpt-4"
    - "gpt-3.5-turbo"
    - "claude-3-opus"
```

### Connection Pooling

```yaml
# HTTP connection settings
http:
  connection_pool_size: 100
  connection_timeout: 10
  read_timeout: 30
  max_retries: 3
```

### Rate Limiting

```yaml
# Rate limiting per provider
rate_limits:
  openai:
    requests_per_minute: 60
    burst_limit: 10
    
  anthropic:
    requests_per_minute: 40
    burst_limit: 5
```

## Troubleshooting

### Common Issues

#### 1. Provider Authentication Errors

**Symptoms:**
- Empty model lists
- 401/403 errors in logs

**Solutions:**
```bash
# Check API key validity
curl -H "Authorization: Bearer YOUR_KEY" https://api.openai.com/v1/models

# Verify configuration
python -c "from src.core.config import load_config; print(load_config())"
```

#### 2. Timeout Issues

**Symptoms:**
- Discovery taking too long
- Timeout errors

**Solutions:**
```yaml
# Increase timeout settings
discovery:
  timeout: 60  # Increase from default 30
  
# Check network connectivity
ping api.openai.com
```

#### 3. Cache Corruption

**Symptoms:**
- Outdated model information
- Cache errors in logs

**Solutions:**
```bash
# Clear cache
rm -rf ./cache/*

# Or programmatically
python -c "from src.core.cache_manager import CacheManager; CacheManager().clear()"
```

#### 4. Memory Issues

**Symptoms:**
- High memory usage
- Application crashes

**Solutions:**
```yaml
# Reduce cache size
discovery:
  max_cache_size: 100MB
  
# Enable memory monitoring
monitoring:
  memory_limit: 512MB
  gc_frequency: 300  # seconds
```

### Debug Mode

Enable debug logging:

```yaml
logging:
  level: DEBUG
  discovery: true
  cache: true
  http: true
```

### Health Checks

```bash
# Check system health
curl http://localhost:8000/health

# Check provider connectivity
curl http://localhost:8000/api/providers/status
```

## Security Considerations

### API Key Management

#### Environment Variables (Recommended)
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### Secure Configuration Files
```yaml
# config.yaml
providers:
  openai:
    api_key: "${OPENAI_API_KEY}"  # Use environment variable
```

#### Key Rotation
```bash
# Automated key rotation script
python scripts/rotate_api_keys.py --provider openai --new-key sk-new-key
```

### Network Security

#### HTTPS Only
```yaml
# Force HTTPS
security:
  enforce_https: true
  ssl_verify: true
```

#### IP Whitelisting
```yaml
security:
  allowed_ips:
    - "192.168.1.0/24"
    - "10.0.0.0/8"
```

### Data Privacy

#### Sensitive Data Filtering
```python
# Automatically filter sensitive data from logs
logging:
  filters:
    - "api_key"
    - "secret"
    - "password"
```

#### Audit Logging
```yaml
audit:
  enabled: true
  log_file: "./logs/audit.log"
  include:
    - model_access
    - provider_requests
    - configuration_changes
```

### Compliance

#### GDPR Compliance
- Data retention policies
- Right to be forgotten
- Data portability

#### SOC 2 Compliance
- Access controls
- Monitoring and alerting
- Incident response

## Best Practices

### 1. Configuration Management
- Use environment variables for sensitive data
- Version control configuration templates
- Regular configuration audits

### 2. Monitoring
- Set up alerts for provider failures
- Monitor cache hit rates
- Track API usage and costs

### 3. Testing
- Regular provider connectivity tests
- Performance benchmarks
- Security vulnerability scans

### 4. Documentation
- Keep provider documentation updated
- Document custom configurations
- Maintain runbooks for common issues

## Support and Resources

### Getting Help
- **Documentation**: This guide and API reference
- **Issues**: GitHub issue tracker
- **Discussions**: Community forum
- **Email**: support@proxyapi.com

### Contributing
- **Bug Reports**: Use GitHub issues
- **Feature Requests**: Use GitHub discussions
- **Pull Requests**: Follow contribution guidelines

### Updates
- **Release Notes**: Check GitHub releases
- **Migration Guides**: Provided for breaking changes
- **Deprecation Notices**: 3-month advance notice

---

For more detailed API documentation, see [API_REFERENCE.md](API_REFERENCE.md)
For integration examples, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)