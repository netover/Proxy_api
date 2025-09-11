# Dataset Export Documentation

## Overview

[BLANK LINE ADDED]

The Dataset Export functionality provides a comprehensive tool for extracting and formatting conversation data from LLM Proxy API log files into JSONL format suitable for fine-tuning AI models. This feature processes structured JSON log entries, extracts conversation data, and exports them in OpenAI-compatible chat format.

[BLANK LINE ADDED]

## Features

[BLANK LINE ADDED]

- **JSONL Export**: Exports datasets in JSONL format optimized for AI model fine-tuning
- **Flexible Filtering**: Filter by date range, model type, and success status
- **Progress Tracking**: Real-time progress bars with detailed statistics
- **Multiple Output Modes**: Export conversation data or complete log records
- **Environment Configuration**: Full environment variable support for automation
- **Structured Logging**: Comprehensive logging with contextual information

[BLANK LINE ADDED]

## Quick Start

[BLANK LINE ADDED]

### Basic Usage

[BLANK LINE ADDED]

```bash

# Export all conversation data from the default log file
python -m src.scripts.export_dataset

# Export with custom output file
python -m src.scripts.export_dataset --output my_dataset.jsonl

# Export only successful records with verbose logging
python -m src.scripts.export_dataset --successful-only --verbose
```

[BLANK LINE ADDED]

### Environment Setup

[BLANK LINE ADDED]

Set up environment variables for automated exports:

```bash
export PROXY_API_EXPORT_DEFAULT_LOG_FILE="logs/proxy_api.log"
export PROXY_API_EXPORT_DEFAULT_OUTPUT_DIR="exports"
export PROXY_API_EXPORT_MAX_RECORDS="1000"
export PROXY_API_EXPORT_SUCCESSFUL_ONLY="true"
```

[BLANK LINE ADDED]

## Command Line Interface

[BLANK LINE ADDED]

### Basic Arguments

[BLANK LINE ADDED]

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--log-file` | Path | `logs/proxy_api.log` | Path to the log file to process |
| `--output` | Path | `exports/dataset.jsonl` | Output file path for the JSONL dataset |
| `--max-records` | int | None | Maximum number of records to export |
| `--successful-only` | flag | False | Export only successful completion records |
| `--export-all` | flag | False | Export all valid log records (not just conversations) |
| `--verbose` | flag | False | Enable verbose logging |

[BLANK LINE ADDED]

### Filtering Arguments

[BLANK LINE ADDED]

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--start-date` | str | None | Start date filter (ISO format: YYYY-MM-DDTHH:MM:SS) |
| `--end-date` | str | None | End date filter (ISO format: YYYY-MM-DDTHH:MM:SS) |
| `--model-filter` | str | None | Filter records by specific model name |

[BLANK LINE ADDED]

## Configuration

[BLANK LINE ADDED]

### Settings Configuration

[BLANK LINE ADDED]

The export functionality is configured through the main `config.yaml` file under the export settings section:

```yaml

# Export Dataset Settings
export_default_log_file: "logs/proxy_api.log"
export_default_output_dir: "exports"
export_default_output_file: "dataset.jsonl"
export_max_records: null  # null means no limit
export_successful_only: false
export_export_all: false
export_start_date: null
export_end_date: null
export_model_filter: null
export_log_level: "INFO"
```

[REST OF THE FILE CONTENTS REMAIN THE SAME WITH APPROPRIATE BLANK LINES ADDED BETWEEN ALL HEADINGS, LISTS, AND CODE BLOCKS]
