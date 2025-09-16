"""
Proxy Logging - Structured logging and observability components for LLM Proxy.

This package provides:
- Structured JSON logging with context
- OpenTelemetry integration
- Prometheus metrics collection
- Log aggregation support
"""

__version__ = "1.0.0"
__author__ = "ProxyAPI Team"
__email__ = "team@proxyapi.dev"

from .structured_logger import StructuredLogger, get_logger
from .metrics_collector import MetricsCollector, get_metrics_collector
from .opentelemetry_config import OpenTelemetryConfig
from .prometheus_exporter import PrometheusExporter

__all__ = [
    "StructuredLogger",
    "get_logger",
    "MetricsCollector",
    "get_metrics_collector",
    "OpenTelemetryConfig",
    "PrometheusExporter",
]
