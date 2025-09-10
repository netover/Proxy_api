# LLM Proxy API with Dynamic Provider Loading

A high-performance LLM proxy with intelligent routing and fallback capabilities that supports dynamic provider loading through configuration.

## Features

- **Dynamic Provider Loading**: Add, remove, or reorder providers by simply editing the `config.yaml` file
- **Intelligent Routing**: Automatic failover between providers
- **Rate Limiting**: Built-in rate limiting protection
- **Metrics Collection**: Performance monitoring and statistics
- **OpenAI Compatible**: Drop-in replacement for OpenAI API endpoints
- **Extensible Architecture**: Easy to add new provider implementations

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your API keys in environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   # ... other provider keys
   ```

3. Run the server:
   ```bash
   python main_dynamic.py
   ```

## Dynamic Provider Configuration

Providers are configured in `config.yaml` with the following structure:

```yaml
providers:
  - name: "openai"
    module: "src.providers.dynamic_openai"
    class: "DynamicOpenAIProvider"
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    models:
      - "gpt-4"
      - "gpt-3.5-turbo"
    priority: 1
```

To add a new provider:
1. Create a new provider implementation that inherits from `DynamicProvider`
2. Add the provider configuration to `config.yaml`
3. Set the required environment variable for the API key
4. Restart the server (no code changes needed)

## API Endpoints

- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions
- `POST /v1/embeddings` - Embeddings generation
- `GET /v1/models` - List available models
- `GET /providers` - List configured providers
- `GET /metrics` - View performance metrics
- `GET /health` - Health check

## Web UI

The project includes two separate user interfaces:

- **FastAPI API (main.py)**: The core proxy API for LLM requests. Run with `python main.py`
- **Flask Configuration UI (web_ui.py)**: A simple web interface for viewing and editing configuration. Run with `python web_ui.py`

To use both, run them on different ports (default: FastAPI on 8000, Flask on 5000). No integration is required; they serve different purposes: API for programmatic access, Flask for configuration management.

## Adding New Providers

To add a new provider:

1. Create a new provider class in `src/providers/` that inherits from `DynamicProvider`
2. Implement the required methods:
   - `_health_check()`
   - `create_completion()`
   - `create_text_completion()`
   - `create_embeddings()`
3. Add the provider configuration to `config.yaml`
4. Set the appropriate environment variable for the API key

Example provider implementation:

```python
from src.providers.dynamic_base import DynamicProvider

class MyNewProvider(DynamicProvider):
    async def _health_check(self):
        # Implementation here
        pass
        
    async def create_completion(self, request):
        # Implementation here
        pass
        
    async def create_text_completion(self, request):
        # Implementation here
        pass
        
    async def create_embeddings(self, request):
        # Implementation here
        pass
```

## Testing

Run the dynamic loading test:

```bash
python test_dynamic_loading.py
```

## License

MIT
