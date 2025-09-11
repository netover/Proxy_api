# Dataset Export Scripts

This directory contains scripts for exporting and processing LLM Proxy API data.

## export_dataset.py

A comprehensive tool for extracting conversation data from JSON log files and formatting them for AI model fine-tuning.

### Features

- **JSONL Export**: Generate datasets in JSONL format for fine-tuning
- **Flexible Filtering**: Filter by date, model, and success status
- **Progress Tracking**: Real-time progress bars with statistics
- **Environment Configuration**: Full environment variable support
- **Multiple Output Modes**: Conversation data or complete log records

### Quick Usage

```bash
# Basic export
python -m src.scripts.export_dataset

# Export with filters
python -m src.scripts.export_dataset \
  --model-filter "gpt-4" \
  --successful-only \
  --output gpt4_dataset.jsonl

# Export date range
python -m src.scripts.export_dataset \
  --start-date "2024-01-01T00:00:00" \
  --end-date "2024-01-31T23:59:59"
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--log-file` | Path to log file (default: logs/proxy_api.log) |
| `--output` | Output file path (default: exports/dataset.jsonl) |
| `--max-records` | Maximum records to export |
| `--successful-only` | Export only successful records |
| `--export-all` | Export all log records (not just conversations) |
| `--start-date` | Start date filter (ISO format) |
| `--end-date` | End date filter (ISO format) |
| `--model-filter` | Filter by model name |
| `--verbose` | Enable verbose logging |

### Environment Variables

All options can be configured via `PROXY_API_EXPORT_*` environment variables:

```bash
export PROXY_API_EXPORT_DEFAULT_LOG_FILE="logs/proxy_api.log"
export PROXY_API_EXPORT_SUCCESSFUL_ONLY="true"
export PROXY_API_EXPORT_MAX_RECORDS="1000"
```

### Output Format

#### Conversation Data (Default)

```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "model": "gpt-4",
    "provider": "openai_default"
  }
}
```

#### Complete Log Records (`--export-all`)

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Request completed successfully",
  "extra_data": {
    "messages": [...],
    "response": "...",
    "model": "gpt-4"
  }
}
```

### Examples

#### Daily Export Script

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
python -m src.scripts.export_dataset \
  --start-date "${DATE}T00:00:00" \
  --end-date "${DATE}T23:59:59" \
  --output "exports/dataset_${DATE}.jsonl"
  ```
  
#### Model-Specific Export
  
  ```bash
python -m src.scripts.export_dataset \
  --model-filter "claude" \
  --successful-only \
  --output claude_dataset.jsonl
```

### Documentation

For comprehensive documentation including configuration options, API reference, and advanced usage examples, see [`docs/export_dataset.md`](../../docs/export_dataset.md).
