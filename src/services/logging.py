"""
Helper functions for log processing and analysis.
Integrates with the existing JSON-based logging system.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
import logging
import structlog

# Define ContextualLogger directly in this file
class ContextualLogger:
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)

    def info(self, message: str, **kwargs):
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **kwargs)


logger = ContextualLogger(__name__)


def iterate_logs(
    log_file: Path, max_lines: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Iterate over log entries from a JSON log file.

    Args:
        log_file: Path to the log file
        max_lines: Maximum number of lines to read (from the end if specified)

    Yields:
        Dict containing parsed log entry
    """
    if not log_file.exists():
        logger.warning(f"Log file does not exist: {log_file}")
        return

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # If max_lines specified, take from the end
        if max_lines:
            lines = lines[-max_lines:]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                log_entry = json.loads(line)
                yield log_entry
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse log line: {e}")
                continue

    except Exception as e:
        logger.error(f"Error reading log file {log_file}: {e}")
        raise


def build_prompt_from_record(record: Dict[str, Any]) -> str:
    """
    Build a human-readable prompt from a log record for analysis or debugging.

    Args:
        record: Log entry dictionary

    Returns:
        Formatted prompt string
    """
    timestamp = record.get("timestamp", "Unknown")
    record.get("level", "UNKNOWN")
    record.get("logger", "Unknown")
    record.get("message", "")
    record.get("module", "Unknown")
    record.get("function", "Unknown")
    record.get("line", "Unknown")

    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Could not parse timestamp '{timestamp}': {e}")

    prompt = """Log Entry Analysis:
Time: {formatted_time}
Level: {level}
Logger: {logger_name}
Module: {module}
Function: {function}
Line: {line}
Message: {message}
"""

    # Add extra data if present
    if "extra_data" in record and record["extra_data"]:
        prompt += "\nExtra Data:\n"
        for key, value in record["extra_data"].items():
            prompt += f"  {key}: {value}\n"

    # Add exception if present
    if "exception" in record:
        prompt += f"\nException:\n{record['exception']}\n"

    return prompt.strip()


def extract_completion(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract completion-related data from a log record.

    Args:
        record: Log entry dictionary

    Returns:
        Dictionary with completion data if found, None otherwise
    """
    message = record.get("message", "").lower()
    extra_data = record.get("extra_data", {})

    # Look for completion-related keywords in message or extra_data
    completion_keywords = [
        "completion",
        "successful",
        "response_time",
        "tokens",
    ]

    if any(keyword in message for keyword in completion_keywords):
        completion_data = {
            "timestamp": record.get("timestamp"),
            "level": record.get("level"),
            "message": record.get("message"),
            "logger": record.get("logger"),
        }

        # Extract relevant metrics from extra_data
        if "response_time" in extra_data:
            completion_data["response_time"] = extra_data["response_time"]
        if "tokens" in extra_data:
            completion_data["tokens"] = extra_data["tokens"]
        if "provider" in extra_data:
            completion_data["provider"] = extra_data["provider"]
        if "model" in extra_data:
            completion_data["model"] = extra_data["model"]

        return completion_data

    return None


def validate_record(record: Dict[str, Any]) -> bool:
    """
    Validate that a log record has all required fields.

    Args:
        record: Log entry dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["timestamp", "level", "message"]

    # Check required fields
    for field in required_fields:
        if field not in record:
            logger.warning(f"Log record missing required field: {field}")
            return False

    # Validate timestamp format
    timestamp = record.get("timestamp")
    if timestamp:
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return False

    # Validate level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if record.get("level") not in valid_levels:
        logger.warning(f"Invalid log level: {record.get('level')}")
        return False

    return True


def filter_successful_records(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Filter log records to return only those indicating successful operations.

    Args:
        records: List of log entry dictionaries

    Returns:
        List of successful log records
    """
    successful_records = []

    success_indicators = [
        "successful",
        "completed",
        "success",
        "ok",
        "200",
        "healthy",
    ]

    for record in records:
        if not validate_record(record):
            continue

        message = record.get("message", "").lower()
        level = record.get("level", "")

        # Check if message contains success indicators
        if any(indicator in message for indicator in success_indicators):
            successful_records.append(record)
            continue

        # Check extra_data for success indicators
        extra_data = record.get("extra_data", {})
        if isinstance(extra_data, dict):
            extra_str = json.dumps(extra_data).lower()
            if any(indicator in extra_str for indicator in success_indicators):
                successful_records.append(record)
                continue

        # INFO level often indicates successful operations
        if level == "INFO" and "error" not in message and "fail" not in message:
            successful_records.append(record)

    return successful_records
