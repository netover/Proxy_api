"""
This module provides a robust, structured, and telemetry-aware logging system.
It integrates Python's standard logging with `structlog` and OpenTelemetry to
ensure that all log messages are structured (as JSON) and automatically correlated
with the current request's trace and span IDs.
"""

import logging
import sys
from contextlib import contextmanager

import structlog
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode

# --- Structlog Configuration ---

def setup_logging(log_level: str = "INFO"):
    """
    Configures the logging system to use structlog with OpenTelemetry integration.
    All logs will be processed by structlog and output as JSON.
    """
    # Define shared processors for all logs
    shared_processors = [
        # Add OpenTelemetry context (trace_id, span_id)
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Configure structlog to wrap the standard logging library
    structlog.configure(
        processors=shared_processors + [
            # Prepare event dict for the renderer.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure the standard logging formatter for JSON output
    formatter = structlog.stdlib.ProcessorFormatter(
        # These processors are applied only at render time
        processor=structlog.processors.JSONRenderer(),
        # foreign_pre_chain is for logs not originating from structlog
        foreign_pre_chain=shared_processors,
    )

    # Get the root logger and remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # Add a new stream handler with our JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info(f"Structured logging configured with level {log_level}")


class StructuredLogger:
    """
    A telemetry-aware logger that creates structured logs and integrates with OpenTelemetry spans.
    """
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
        self.tracer = trace.get_tracer(name)

    @contextmanager
    def span(self, name: str, attributes: dict = None):
        """
        Creates an OpenTelemetry span and binds its context to the logger.
        All logs within this context will automatically have trace_id and span_id.

        Args:
            name: The name of the span (e.g., "proxy_request").
            attributes: A dictionary of attributes to add to the span.
        """
        with self.tracer.start_as_current_span(name, attributes=attributes) as span:
            span_context = span.get_span_context()
            context = {
                "trace_id": f"0x{span_context.trace_id:032x}",
                "span_id": f"0x{span_context.span_id:016x}",
            }
            # Bind the context to structlog's contextvars for the duration of the span
            with structlog.contextvars.bind_contextvars(**context):
                try:
                    yield span
                    span.set_status(Status(StatusCode.OK))
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    self.error("Request failed within span", error=str(e))
                    raise

    def info(self, message: str, **kwargs):
        """Logs an informational message."""
        self.logger.info(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Logs an error message."""
        self.logger.error(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Logs a warning message."""
        self.logger.warning(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Logs a debug message."""
        self.logger.debug(message, **kwargs)

# For backward compatibility, provide a logger instance.
# In a real app, this would be instantiated per-module.
logger = StructuredLogger(__name__)
