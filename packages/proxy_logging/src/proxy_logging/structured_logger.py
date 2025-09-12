"""Structured logging with JSON formatting and contextual information."""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone


class StructuredLogger:
    """Structured logger with JSON formatting and contextual information."""
    
    def __init__(self, name: str, level: Optional[str] = None):
        self.name = name
        self.logger = logging.getLogger(name)

        # Set level from parameter, environment, or default
        if level:
            self.logger.setLevel(getattr(logging, level.upper()))
        else:
            # Check for LOG_LEVEL first, then fall back to INFO
            env_level = os.getenv("LOG_LEVEL", "INFO").upper()
            self.logger.setLevel(getattr(logging, env_level, logging.INFO))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Add JSON formatter handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, extra={"extra_data": kwargs})
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, extra={"extra_data": kwargs})
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, extra={"extra_data": kwargs})
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, extra={"extra_data": kwargs})
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.logger.critical(message, extra={"extra_data": kwargs})
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra={"extra_data": kwargs})


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra data
        if hasattr(record, "extra_data"):
            log_entry["extra_data"] = record.extra_data
        
        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


class MetricsCollector:
    """Metrics collection for monitoring and observability."""
    
    def __init__(self, prefix: str = "proxy_api"):
        self.prefix = prefix
        self.metrics: Dict[str, Any] = {}
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = f"{self.prefix}.{name}"
        if key not in self.metrics:
            self.metrics[key] = {"type": "counter", "value": 0.0, "tags": tags or {}}
        self.metrics[key]["value"] += value
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        key = f"{self.prefix}.{name}"
        self.metrics[key] = {"type": "gauge", "value": value, "tags": tags or {}}
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        key = f"{self.prefix}.{name}"
        if key not in self.metrics:
            self.metrics[key] = {"type": "histogram", "values": [], "tags": tags or {}}
        self.metrics[key]["values"].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics.copy()


def get_metrics_collector(prefix: str = "proxy_api") -> MetricsCollector:
    """Get a metrics collector instance."""
    return MetricsCollector(prefix)