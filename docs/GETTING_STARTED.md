# Getting Started with ProxyAPI

Welcome to ProxyAPI! This guide will walk you through your first steps with the AI model proxy and discovery platform. Whether you're a developer integrating AI into your application or just exploring the capabilities, this tutorial will get you up and running quickly.

## Prerequisites

Before we begin, make sure you have:

- Python 3.11 or later installed
- At least one API key from a supported AI provider (OpenAI, Anthropic, etc.)
- Basic familiarity with command line tools

## Step 1: Installation

Let's start by installing ProxyAPI. We'll use Docker for the easiest setup.

### Option A: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/proxyapi.git
cd proxyapi

# 2. Copy the environment template
cp .env.example .env

# 3. Start the services
docker-compose up -d

# 4. Check that everything is running
docker-compose ps
```

You should see output showing that the services are running:

```
NAME                COMMAND                  SERVICE             STATUS              PORTS
proxyapi-proxy      "python main.py"         proxy               running             0.0.0.0:8000->8000/tcp
proxyapi-context    "python -m context_se…"   context-service     running             0.0.0.0:8001->8001/tcp
```

### Option B: Manual Installation

If you prefer to install manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp config.yaml.example config.yaml
```

## Step 2: Configuration

Now we need to configure ProxyAPI with your AI provider credentials.

### Setting up API Keys

Edit your `.env` file (or create one) with your API keys:

```bash
# OpenAI (optional but recommended for examples)
OPENAI_API_KEY=[YOUR_OPENAI_API_KEY]

# Anthropic (optional)
ANTHROPIC_API_KEY=[YOUR_ANTHROPIC_API_KEY]

# Proxy API Key (for authentication)
API_KEY=[YOUR_PROXY_API_KEY]

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379
```

### Basic Configuration

Create or edit `config.yaml` with your provider setup:

```yaml
app:
  name: "My ProxyAPI"
  environment: "development"

providers:
  - name: "openai"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    models:
      - "gpt-3.5-turbo"
      - "gpt-4"
    enabled: true
    priority: 1

  - name: "anthropic"
    type: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
    models:
      - "claude-3-haiku-20240307"
      - "claude-3-sonnet-20240229"
    enabled: true
    priority: 2

# Rate limiting
rate_limit:
  requests_per_window: 1000
  window_seconds: 60
```

## Step 3: First API Call

Let's test that everything is working by making your first API call.

### Health Check

First, let's verify the API is running:

```bash
curl http://localhost:8000/health
```

You should see:

```json
{
  "status": "healthy",
  "service": "proxy-api-gateway",
  "timestamp": 1703123456
}
```

### Discover Available Models

Now let's see what models are available:

```bash
curl http://localhost:8000/v1/models
```

This will show you all discoverable models from your configured providers:

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai",
      "permission": [...],
      "root": "gpt-3.5-turbo",
      "parent": null
    },
    {
      "id": "claude-3-haiku-20240307",
      "object": "model",
      "created": 1703123456,
      "owned_by": "anthropic",
      "context_length": 200000,
      "supports_chat": true
    }
  ]
}
```

### Make Your First Chat Completion

Now for the exciting part - let's make your first AI request:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: [YOUR_PROXY_API_KEY]" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Hello! Can you tell me what ProxyAPI is?"
      }
    ]
  }'
```

You should receive a response like:

```json
{
  "id": "chatcmpl-1234567890",
  "object": "chat.completion",
  "created": 1703123456,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "ProxyAPI is a comprehensive AI model proxy and discovery platform that provides unified access to multiple AI providers..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 16,
    "completion_tokens": 45,
    "total_tokens": 61
  }
}
```

🎉 **Congratulations!** You've just made your first API call through ProxyAPI!

## Step 4: Using ProxyAPI in Code

Now let's create a simple Python script to interact with the API programmatically.

### Basic Python Example

Create a file called `test_proxy.py`:

```python
import requests

# Configuration
API_BASE_URL = "http://localhost:8000/v1"
API_KEY = "[YOUR_PROXY_API_KEY]"

def chat_completion(model, messages):
    """Make a chat completion request"""
    response = requests.post(
        f"{API_BASE_URL}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.7
        }
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def list_models():
    """List available models"""
    response = requests.get(f"{API_BASE_URL}/models")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

if __name__ == "__main__":
    # Test the connection
    print("Testing ProxyAPI connection...")

    # List available models
    models = list_models()
    if models:
        print(f"Available models: {len(models['data'])}")
        for model in models['data'][:5]:  # Show first 5
            print(f"  - {model['id']}")

    # Make a test chat completion
    messages = [
        {"role": "user", "content": "What are the main benefits of using ProxyAPI?"}
    ]

    result = chat_completion("gpt-3.5-turbo", messages)
    if result:
        content = result['choices'][0]['message']['content']
        print(f"\nResponse: {content}")
        print(f"Tokens used: {result['usage']['total_tokens']}")
```

Run the script:

```bash
python test_proxy.py
```

## Step 5: Explore Advanced Features

Now that you have the basics working, let's explore some advanced features.

### Model Discovery with Filtering

```bash
# Search for models with specific capabilities
curl "http://localhost:8000/v1/models/search?q=gpt-4&supports_chat=true"

# Get models from a specific provider
curl "http://localhost:8000/v1/models?provider=openai"

# Find cost-effective models
curl "http://localhost:8000/v1/models/search?max_cost=0.01"
```

### Streaming Responses

For real-time responses, use streaming:

```python
import requests
import json

def stream_chat_completion(model, messages):
    """Stream a chat completion response"""
    response = requests.post(
        f"{API_BASE_URL}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json={
            "model": model,
            "messages": messages,
            "stream": True
        },
        stream=True
    )

    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk['choices']:
                            content = chunk['choices'][0]['delta'].get('content', '')
                            print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        continue
        print()  # New line at end
    else:
        print(f"Error: {response.status_code}")

# Test streaming
messages = [{"role": "user", "content": "Write a short poem about AI."}]
stream_chat_completion("gpt-3.5-turbo", messages)
```

### Monitoring and Health Checks

```bash
# Get detailed health information
curl http://localhost:8000/v1/health

# Check provider status
curl http://localhost:8000/v1/health/providers

# Get performance metrics
curl http://localhost:8000/metrics

# View the monitoring dashboard
open http://localhost:8000/monitoring
```

## Step 6: Production Considerations

Before using ProxyAPI in production, consider these best practices:

### Security

1. **Use HTTPS**: Always use HTTPS in production
2. **Secure API Keys**: Store keys securely, never in code
3. **Rate Limiting**: Configure appropriate rate limits
4. **Authentication**: Use strong API keys

### Performance

1. **Caching**: Enable response caching for better performance
2. **Connection Pooling**: Configure appropriate connection limits
3. **Monitoring**: Set up monitoring and alerts

### Scaling

1. **Load Balancing**: Use multiple instances behind a load balancer
2. **Database**: Consider using Redis for shared caching
3. **Auto-scaling**: Set up auto-scaling based on load

## Troubleshooting

### Common Issues

**API returns 401 Unauthorized**
- Check that your `X-API-Key` header is correct
- Verify the API key is set in your `.env` file

**API returns 503 Service Unavailable**
- Check if your provider API keys are valid
- Verify the provider services are running

**Models not showing up**
- Run: `curl -X POST http://localhost:8000/v1/models/refresh`
- Check your provider configurations

**Slow responses**
- Enable caching in your configuration
- Check your internet connection
- Monitor the `/health` endpoint for issues

### Getting Help

If you run into issues:

1. Check the logs: `docker-compose logs -f`
2. Visit the troubleshooting guide: [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
3. Open an issue: [GitHub Issues](https://github.com/your-org/proxyapi/issues)

## Next Steps

Now that you have ProxyAPI running, here are some things you can explore next:

- **[Integration Guide](INTEGRATION_GUIDE.md)** - Learn how to integrate ProxyAPI into your applications
- **[Configuration Guide](CONFIGURATION_GUIDE.md)** - Deep dive into configuration options
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Performance Guide](PERFORMANCE_GUIDE.md)** - Optimize for high-throughput scenarios

Happy coding with ProxyAPI! 🚀