# LLM Proxy API

A high-performance, production-ready proxy server for Large Language Models (LLMs) with intelligent routing, fallback mechanisms, and comprehensive monitoring.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, and extensible architecture for additional providers
- **Intelligent Routing**: Automatic provider selection with priority-based fallback and circuit breaker protection
- **Rate Limiting**: Built-in rate limiting with configurable thresholds using slowapi
- **Comprehensive Monitoring**: Real-time metrics collection, health checks, and provider statistics
- **Circuit Breaker**: Prevents cascading failures with configurable failure thresholds and recovery
- **Security**: API key authentication, CORS support, and input validation
- **Performance**: Asynchronous processing with HTTP connection pooling and retry logic
- **Deployment Flexibility**: Standalone executable build for Windows and cross-platform support

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  LLM Proxy API   │───▶│  LLM Provider   │
└─────────────────┘    │                  │    │ (OpenAI, etc.)  │
                       │ ├── Provider      │    └─────────────────┘
                       │ │   Routing      │    ┌─────────────────┐
                       │ ├── Health        │───▶│  LLM Provider   │
                       │ │   Monitoring   │    │ (Fallback)      │
                       │ ├── Rate          │    └─────────────────┘
                       │ │   Limiting     │
                       │ └── Metrics       │
                       └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd llm-proxy-api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

4. Start the server:
   ```bash
   python main.py
   ```

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t llm-proxy-api .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env llm-proxy-api
   ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Server Settings
PROXY_API_HOST=0.0.0.0
PROXY_API_PORT=8000
PROXY_API_DEBUG=false

# Rate Limiting
PROXY_API_RATE_LIMIT_REQUESTS=100
PROXY_API_RATE_LIMIT_WINDOW=60
```

### Provider Configuration

Edit `config.yaml` to configure providers:

```yaml
providers:
  - name: "openai"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    models:
      - "gpt-4"
      - "gpt-3.5-turbo"
    enabled: true
    priority: 1  # Lower number = higher priority
```

## API Endpoints

### Chat Completions (OpenAI Compatible)

```http
POST /v1/chat/completions
Content-Type: application/json
X-API-Key: YOUR_API_KEY

{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ]
}
```

Or using Bearer token authentication:

```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN

{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ]
}
```

### Health Check

```http
GET /health
```

### Provider Metrics

```http
GET /metrics
```

### List Models

```http
GET /v1/models
```

### List Providers

```http
GET /providers
```

## Building Executables

To build a standalone executable:

```bash
python build.py
```

This creates a single executable file in the `dist/` directory.

## Monitoring

The proxy provides real-time metrics through the `/metrics` endpoint:

```json
{
  "openai": {
    "total_requests": 1250,
    "success_rate": 0.98,
    "avg_response_time": 0.45,
    "error_counts": {
      "http_429": 5,
      "timeout": 2
    }
  }
}
```

## Security

- All API requests require authentication via API key or JWT token
- CORS policy can be configured in environment variables
- Rate limiting prevents abuse
- Secure headers are automatically added to responses
- Input validation and sanitization protect against malicious payloads


## Extending Providers

To add a new provider:

1. Create a new file in `src/providers/` (e.g., `new_provider.py`)
2. Implement the `Provider` base class
3. Add configuration to `config.yaml`

```python
from src.providers.base import Provider

class NewProvider(Provider):
    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
