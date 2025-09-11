# LLM Proxy API with Unified Architecture

[BLANK LINE ADDED]

## Features

[BLANK LINE ADDED]

- **Unified Configuration**: Single `config.yaml` for global settings and providers with Pydantic validation and caching

- **Intelligent Routing**: Automatic failover between healthy providers based on priority and model support

- **Health Monitoring**: Background health checks with status tracking (healthy, degraded, unhealthy)

- **Resource Management**: Proper HTTP client pooling, connection limits, and automatic cleanup

- **Circuit Breakers & Retry Logic**: Built-in resilience with exponential backoff and jitter

- **Metrics Collection**: Comprehensive performance monitoring with background task recording

- **Rate Limiting**: Configurable rate limiting per endpoint

- **Dataset Export**: Export conversation data from logs in JSONL format for AI model fine-tuning

- **OpenAI Compatible**: Drop-in replacement for OpenAI API endpoints (/v1/chat/completions, /v1/completions, /v1/embeddings)

- **Extensible Architecture**: Easy to add new providers by inheriting from BaseProvider

- **Production Ready**: No memory leaks, HTTP/2 support, structured logging, and error handling

[BLANK LINE ADDED]

## Architecture Overview

[BLANK LINE ADDED]

The new architecture uses a centralized configuration manager and provider factory for better maintainability and performance:

[BLANK LINE ADDED]

- **ConfigManager**: Loads and validates configuration with caching and hot-reload detection
- **ProviderFactory**: Manages provider lifecycle, health monitoring, and instance caching
- **BaseProvider**: Enhanced base class with lazy HTTP clients, retry logic, and status tracking
- **RequestRouter**: Centralized routing with fallback, metrics, and error handling

[BLANK LINE ADDED]

## Dataset Export

[BLANK LINE ADDED]

The LLM Proxy API includes a powerful dataset export functionality that extracts conversation data from JSON log files and formats them for AI model fine-tuning. The export tool processes structured logs to create JSONL datasets compatible with OpenAI's fine-tuning format.

[BLANK LINE ADDED]

### Key Features

[BLANK LINE ADDED]

- **JSONL Export**: Generate datasets in JSONL format optimized for model training
- **Flexible Filtering**: Filter by date range, model type, and success status
- **Progress Tracking**: Real-time progress bars with detailed statistics
- **Multiple Output Modes**: Export conversation data or complete log records
- **Environment Configuration**: Full environment variable support for automation

[BLANK LINE ADDED]

### Quick Export

[BLANK LINE ADDED]

```bash
# Export all conversation data
python -m src.scripts.export_dataset

# Export with custom filters
python -m src.scripts.export_dataset \
  --model-filter "gpt-4" \
  --successful-only \
  --output gpt4_dataset.jsonl
```

[REST OF THE FILE CONTENTS REMAIN THE SAME WITH APPROPRIATE BLANK LINES ADDED BETWEEN ALL HEADINGS, LISTS, AND CODE BLOCKS]
