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

## Supported Providers

The proxy supports 8 LLM providers with unified OpenAI-compatible interfaces. Each provider has specific authentication, payload requirements, and limitations. All use PROXY_API_{PROVIDER}_API_KEY environment variables (e.g., PROXY_API_OPENAI_API_KEY).

### OpenAI
- **Endpoint**: `/v1/chat/completions` (standard OpenAI API)
- **Auth**: `Authorization: Bearer {api_key}`
- **Payload**: Standard OpenAI format: `{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 100, "temperature": 0.7}`
- **Streaming**: Yes (SSE for `stream=true`)
- **Limitations**: Rate limits apply; supports chat, text completions, embeddings
- **Health Check**: GET `/v1/models`

### Anthropic
- **Endpoint**: `/v1/messages` (transformed to OpenAI chat format)
- **Auth**: `x-api-key: {api_key}`, `anthropic-version: 2023-06-01`
- **Payload**: Messages transformed to prompt: `Human: {user msg}\n\nAssistant:`, stop_sequences include "Human:"
- **Example**: `{"model": "claude-3-sonnet-20240229", "messages": [{"role": "user", "content": "Explain AI"}], "max_tokens": 200}`
- **Streaming**: Yes (SSE chunks with text_delta)
- **Limitations**: No embeddings; prompt-based, multi-turn via concatenation
- **Health Check**: Minimal POST `/v1/messages`

### Perplexity
- **Endpoint**: `/v1/ask` (query from last user message)
- **Auth**: `x-perplexity-api-key: {api_key}`
- **Payload**: `{"model": "llama-2-70b-chat", "query": "Last user message", "max_tokens": 100}` (messages extracted)
- **Response**: Includes `perplexity_sources` array with title/url
- **Streaming**: No
- **Limitations**: Search-focused; create_text_completion alias for chat; no embeddings
- **Health Check**: GET `/v1/models`

### Grok (xAI)
- **Endpoint**: `/v1/complete` (prompt from concatenated messages)
- **Auth**: `Authorization: Bearer {api_key}`
- **Payload**: `{"model": "grok-beta", "prompt": "User: Hello\nAssistant: ", "max_tokens": 100}` (role:content concat)
- **Streaming**: No
- **Limitations**: Text-only; no chat streaming or embeddings
- **Health Check**: GET `/v1/models`

### Blackbox
- **Endpoint**: `/v1/chat/completions` for chat, `/v1/images/generations` for images
- **Auth**: `Authorization: Bearer {api_key}`
- **Payload (Chat)**: Standard OpenAI chat format
- **Payload (Image)**: `{"model": "blackbox-alpha", "prompt": "A cat", "n": 1, "size": "1024x1024"}`
- **Example Image Request**:
  ```
  POST /v1/images/generations
  {"model": "blackbox-alpha", "prompt": "A futuristic city", "n": 1, "size": "512x512"}
  ```
  Response: `{"data": [{"url": "https://..."}]}`
- **Streaming**: No for chat; non-streaming for images
- **Limitations**: Supports create_image/create_video; no embeddings
- **Health Check**: GET `/v1/models`

### OpenRouter
- **Endpoint**: `/v1/chat/completions` (OpenAI-compatible)
- **Auth**: `Authorization: Bearer {api_key}`
- **Payload**: Standard OpenAI format; models cached for 5 minutes
- **Streaming**: Yes (proxies provider streaming)
- **Limitations**: Aggregator; supports many models but depends on upstream providers
- **Health Check**: GET `/v1/models`

### Cohere
- **Endpoint**: `/v1/generate` (prompt from multi-line role:content)
- **Auth**: `Authorization: Bearer {api_key}`
- **Payload**: `{"model": "command-xlarge-nightly", "prompt": "User: Hello\n\nAssistant: ", "max_tokens": 100}` (concatenated)
- **Streaming**: No
- **Limitations**: Text generation only; no chat streaming or embeddings; multi-line prompt support
- **Health Check**: Minimal POST `/v1/generate`

### Azure OpenAI
- **Endpoint**: `/openai/deployments/{deployment}/chat/completions?api-version={version}` (OpenAI-compatible)
- **Auth**: `api-key: {api_key}`
- **Payload**: Standard OpenAI format with `model: "{deployment_id}"` (e.g., "gpt-4-deployment")
- **Example**: `{"model": "gpt-4-deployment", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 100}` (api_version=2023-12-01-preview)
- **Streaming**: Yes (SSE for `stream=true`)
- **Limitations**: Requires deployment_id and api_version in config; Azure-specific quotas
- **Health Check**: GET `/openai/deployments`

All providers map errors to standardized ProviderError subclasses (e.g., 400→InvalidRequestError). Unsupported operations raise NotImplementedError (501).

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

### Streaming with SSE

When `stream=True` in the request, the endpoint returns a `StreamingResponse` with `media_type="text/event-stream"`. The response uses Server-Sent Events (SSE) format for real-time delivery of completion chunks.

Each event is a line starting with `data: ` followed by a JSON object containing the partial completion data (similar to non-streaming but with `delta` instead of full `choices`). The stream ends with `data: [DONE]`.

#### Client-Side Handling

To consume the stream:

1. Set `Accept: text/event-stream` header if needed.
2. Read the response as a stream and parse line by line.
3. For lines starting with `data: `, extract the JSON after the prefix and parse it.
4. Accumulate `delta.content` from chunks to build the full response.
5. Handle errors and the `[DONE]` marker to end processing.

#### Example with curl

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "stream": true
  }' \
  --no-buffer
```

This will output lines like:
```
data: {"id": "chatcmpl-abc", "object": "chat.completion.chunk", "choices": [{"delta": {"content": "Quantum computing "}}]}

data: {"id": "chatcmpl-abc", "object": "chat.completion.chunk", "choices": [{"delta": {"content": "is a revolutionary..."}}]}

data: [DONE]
```

#### JavaScript Example

```javascript
const response = await fetch('/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-3.5-turbo',
    messages: [{role: 'user', content: 'Hello'}],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

let fullContent = '';
while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') {
        console.log('Stream complete');
        break;
      }
      try {
        const json = JSON.parse(data);
        if (json.choices && json.choices[0].delta && json.choices[0].delta.content) {
          fullContent += json.choices[0].delta.content;
          console.log('Received:', json.choices[0].delta.content);
        }
      } catch (e) {
        console.error('Parse error:', e);
      }
    }
  }
}
console.log('Full response:', fullContent);
```

This setup ensures efficient streaming with proper error handling and client compatibility.
## Automatic Context Condensation

The LLM Proxy API includes automatic context condensation for non-streaming requests to both `/v1/chat/completions` and `/v1/completions` endpoints. When a provider returns a context length exceeded error (detected by configurable keywords like "context_length_exceeded" or "maximum context length" in the error message), the proxy automatically:

1. Extracts the content from all messages (chat) or the prompt (completions).
2. Uses the top-priority enabled provider to generate a concise summary (with adaptive max_tokens limited to min(input_size * 0.5, 512) by default) that preserves key entities and intents, leveraging in-memory caching to avoid redundant computations.
3. Replaces the full history/prompt with a system message containing the summary followed by the original last message (chat) or "Resumo: {summary}" as the new prompt (completions).
4. Retries the request with the condensed context (streaming is disabled for the retry to ensure compatibility), with fallback to truncating input to half length if condensation times out (10s) or fails.

This feature prevents interruptions from long conversation histories or prompts without requiring client-side handling, with optimizations for performance and reliability. It only applies to non-streaming requests (`stream=false`); streaming requests raise the original error to maintain real-time behavior.

### Optimizations
- **Local Cache**: In-memory cache for summaries using MD5 hash of chunks as key with TTL (default 300s) to avoid redundant condensations for repeated inputs.
- **Adaptive Max Tokens**: Dynamically calculated as min(original_size * adaptive_factor, max_tokens_default) based on input length (approximated by character count) to preserve more context for larger inputs (default factor 0.5, default 512).
- **Fallback Truncation**: If condensation fails due to timeout or error, automatically truncates messages/prompt to half original length and retries without summarization.
- **Non-Blocking Timeout Handling**: Condensation executed with asyncio.wait_for(timeout=10s) for non-blocking operation; triggers fallback on asyncio.TimeoutError.
- **Dynamic Configuration**: All settings configurable via `config.yaml` under `condensation` key for customization (e.g., custom error keywords, lower adaptive factor for aggressive reduction).

### Config Example
```yaml
condensation:
  max_tokens_default: 512
  error_keywords:
    - "context_length_exceeded"
    - "maximum context length"
    - "custom_error"
  adaptive_factor: 0.5
  cache_ttl: 300
```

### Example for Chat Completions

Send a request with an excessively long message to trigger the error:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "'$(printf 'a%.0s' {1..10000})'"}],
    "stream": false,
    "max_tokens": 50
  }'
```

### Example for Text Completions

Similar for `/v1/completions` with a long prompt:

```bash
curl -X POST http://localhost:8000/v1/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo-instruct",
    "prompt": "'$(printf 'a%.0s' {1..10000})'",
    "stream": false,
    "max_tokens": 50
  }'
```

Expected behavior: The response will be a successful completion (200) using the condensed summary/prompt, with the provider's create_completion/create_text_completion called twice (first failure, second success).

### Testing

The feature is tested in `tests/test_endpoints.py` with `test_chat_completions_context_condensation` and `test_text_completions_context_condensation`, mocking a ValueError on the first call and verifying the retry and summary usage.

## Monitoring & Metrics

- **Health Monitoring**: Background health checks every 60 seconds
- **Metrics**: Request success rates, response times, token usage per provider
- **Circuit Breakers**: Per-provider circuit breakers to prevent cascading failures
- **Logging**: Structured JSON logging with request context

Access metrics at `/metrics` and health at `/health`.

#### Health Check Example
```
GET /health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": 1699999999.123,
  "providers": {
    "total": 8,
    "healthy": 7,
    "degraded": 1,
    "unhealthy": 0
  },
  "uptime": "99.95%",
  "last_check": "2023-11-01T12:00:00Z"
}
```

#### Metrics Example
```
GET /metrics
```
Response:
```json
{
  "providers": {
    "openai": {
      "success_rate": 0.98,
      "total_requests": 100,
      "average_response_time": 1.2,
      "total_tokens": 5000,
      "error_count": 2
    },
    "anthropic": {
      "success_rate": 0.95,
      "total_requests": 50,
      "average_response_time": 2.1,
      "total_tokens": 2500,
      "error_count": 3
    }
    // ... other providers
  },
  "summary": {
    "average_success_rate": 0.95,
    "total_requests": 500,
    "average_response_time": 1.5,
    "total_tokens": 20000
  },
  "timestamp": 1699999999.123
}
```

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

### Docker Deployment

The project includes a multistage Dockerfile for production deployment. To build and run:

1. Build the Docker image:
   ```bash
   docker build -t llm-proxy-api .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml llm-proxy-api
   ```

3. Using docker-compose (recommended for multi-container setups):
   ```bash
   docker-compose up -d
   ```

The Dockerfile uses a build stage to compile the application and a runtime stage based on Alpine Linux for minimal size. Customize the `docker-compose.yml` for volumes, environment variables, and networking.

### Cross-Platform Builds

Standalone executables can be built for Windows, Linux, and macOS using the provided build scripts:

1. Configure `build_config.yaml` for your target platform (icon, permissions, etc.).

2. **Windows:**
   ```bash
   python build_windows.py
   ```
   Creates `dist/LLM_Proxy_API.exe` with embedded config.

3. **Linux:**
   ```bash
   python build_linux.py
   ```
   Creates `dist/llm-proxy-api` with executable permissions.

4. **macOS:**
   ```bash
   python build_macos.py
   ```
   Creates `dist/llm-proxy-api` with macOS bundle support.

Each script uses PyInstaller for one-file distribution. Test the executable on the target platform. For cross-compilation, use Docker or virtual machines.

## Error Classification

The API uses standardized JSON error responses with classification for better debugging:

- **4xx Client Errors:**
  - `invalid_request_error` (400): Invalid parameters, e.g., unsupported model.
    ```json
    {
      "error": {
        "message": "Model 'invalid-model' is not supported",
        "type": "invalid_request_error",
        "param": "model",
        "code": "model_not_found"
      }
    }
    ```
  - `authentication_error` (401): Invalid API key.

- **4xx Rate Limits:**
  - `rate_limit_error` (429): Exceeded request rate.

- **5xx Server Errors:**
  - `service_unavailable_error` (503): All providers unavailable, with details on attempts.
    ```json
    {
      "error": {
        "message": "All providers are currently unavailable",
        "type": "service_unavailable_error",
        "code": "providers_unavailable",
        "details": {
          "attempts": 2,
          "providers_tried": ["openai", "anthropic"],
          "errors": [{"provider": "openai", "error_type": "TimeoutError"}]
        }
      }
    }
    ```
  - `not_implemented_error` (501): Operation not supported by providers.

- **5xx Internal:**
  - `server_error` (500): Unexpected errors.

All errors include `type` and `code` for programmatic handling. Check logs for full details.

### Environment Variable Validation

Run the validation script to check required PROXY_API_* variables:

```bash
python validate_env.py
```

This script checks for missing keys and provides setup guidance. Customize as needed.

## License

MIT License
