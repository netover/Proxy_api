# ProxyAPI - AI Model Proxy & Discovery Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

A comprehensive AI model proxy and discovery platform that provides unified access to multiple AI providers including OpenAI, Anthropic, Azure OpenAI, Cohere, and more.

## ✨ Key Features

- **🔍 Automatic Model Discovery**: Real-time discovery and cataloging of AI models from all configured providers
- **🚀 High-Performance Proxy**: Intelligent routing with circuit breakers, caching, and connection pooling
- **📊 Comprehensive Monitoring**: Prometheus metrics, health checks, and detailed analytics
- **🧪 Chaos Engineering**: Fault injection and resilience testing
- **💰 Cost Optimization**: Context condensation and smart caching to reduce API costs
- **🔒 Enterprise Security**: Rate limiting, authentication, and audit logging

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/proxyapi.git
cd proxyapi

# Start with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:8000
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-key"
export API_KEY="your-proxy-key"

# Start the application
python main.py
```

**That's it!** Your proxy API is now running at `http://localhost:8000`.

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- 2GB RAM minimum, 4GB recommended

### Option 1: Docker Installation (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/proxyapi.git
cd proxyapi

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d
```

### Option 2: Manual Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# For enhanced performance (optional)
pip install httpx[http2] aiofiles watchdog psutil

# Configure providers
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys

# Start application
python main_dynamic.py
```

### Configuration

Create a `config.yaml` file with your provider configurations:

```yaml
providers:
  - name: "openai"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    models:
      - "gpt-3.5-turbo"
      - "gpt-4"
    enabled: true

  - name: "anthropic"
    type: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      - "claude-3-haiku"
      - "claude-3-sonnet"
    enabled: true
```

## 💻 Basic Usage

### Chat Completions

```python
import requests

# Make a chat completion request
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-proxy-key"
    },
    json={
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ]
    }
)

print(response.json())
```

### Model Discovery

```python
# Get all available models
response = requests.get("http://localhost:8000/v1/models")
models = response.json()

for model in models["data"]:
    print(f"{model['id']}: {model['description']}")
```

### Health Check

```bash
# Quick health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/v1/health
```

### Running the Web UI

The web UI is a separate application that provides a dashboard for monitoring and interacting with the proxy. For stability, it should be run as a separate process.

```bash
# Run the web UI (from the project root directory)
python web_ui.py
```

The UI will be available at `http://localhost:10000`.

## 📖 Documentation

### For New Users

- **[Getting Started Guide](docs/GETTING_STARTED.md)** - Step-by-step tutorial for first-time users
- **[Quick Start Guide](QUICK_START.md)** - Rapid setup and basic usage
- **[Installation Guide](docs/INSTALLATION_GUIDE.md)** - Detailed installation instructions

### For Developers

- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - Integration patterns and best practices
- **[Configuration Guide](docs/CONFIGURATION_GUIDE.md)** - Advanced configuration options

### Advanced Topics

- **[Model Discovery Guide](docs/MODEL_DISCOVERY_GUIDE.md)** - Using the model discovery system
- **[Performance Guide](docs/PERFORMANCE_GUIDE.md)** - Optimization and performance tuning
- **[Monitoring Guide](docs/MONITORING_GUIDE.md)** - Metrics, logging, and observability
- **[Security Guide](docs/SECURITY_GUIDE.md)** - Security features and best practices

### Deployment & Operations

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment strategies
- **[Load Testing Guide](docs/LOAD_TESTING_GUIDE.md)** - Performance testing and chaos engineering
- **[Troubleshooting Guide](docs/TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions

### Development

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project
- **[Architecture Overview](docs/ARCHITECTURE_AND_SYSTEM_DESIGN.md)** - System architecture and design
- **[Testing Guide](docs/TESTING_GUIDE_COMPREHENSIVE.md)** - Testing strategies and practices

## 🔧 Advanced Features

### Model Discovery System

Automatically discovers and catalogs available AI models from all configured providers with real-time pricing and capabilities.

```bash
# Refresh model cache
curl -X POST http://localhost:8000/v1/models/refresh

# Search models by capabilities
curl "http://localhost:8000/v1/models/search?supports_vision=true&max_cost=0.01"
```

### Context Condensation

Automatically summarizes long contexts to reduce API costs and improve performance.

```python
# Long context is automatically handled
messages = [{"role": "user", "content": "Very long text..." * 1000}]

# API automatically condenses if needed
response = requests.post("http://localhost:8000/v1/chat/completions", json={
    "model": "gpt-4",
    "messages": messages
})
```

### Monitoring & Metrics

Comprehensive monitoring with Prometheus metrics and health checks.

```bash
# Get metrics
curl http://localhost:8000/metrics

# Prometheus format
curl http://localhost:8000/metrics/prometheus
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/proxyapi.git
cd proxyapi

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
flake8 src/
black src/
mypy src/
```

## 📞 Support

### Getting Help

- **📖 Documentation**: Comprehensive docs in the `docs/` directory
- **🐛 Issues**: [GitHub Issues](https://github.com/your-org/proxyapi/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-org/proxyapi/discussions)
- **📧 Email**: support@proxyapi.com

### Community

- **Discord**: [Join our Discord](https://discord.gg/proxyapi)
- **Twitter**: [@ProxyAPI](https://twitter.com/proxyapi)
- **Blog**: [proxyapi.com/blog](https://proxyapi.com/blog)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and API
- **Anthropic** for Claude models
- **Microsoft** for Azure OpenAI
- **FastAPI** for the excellent web framework
- **All contributors** who helped make this possible

---

**⭐ Star this repository if you find it useful!**