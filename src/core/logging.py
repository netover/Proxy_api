import logging
import sys
from typing import Optional

# Using structlog which is in requirements.txt
import structlog

class ContextualLogger:
    """
    A logger that uses structlog to provide contextual logging.
    This is a simplified version based on src/services/logging.py
    """
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

    def span(self, name: str, **kwargs):
        """Placeholder for a tracing span."""
        from contextlib import contextmanager
        @contextmanager
        def dummy_span(*args, **kwargs):
            yield
        return dummy_span()

def setup_logging(log_level: str = "INFO"):
    """
    Configures the logging system for the application.
    This function sets up structlog to format logs as JSON.
    """
    log_level = log_level.upper()
    level = getattr(logging, log_level, logging.INFO)

    # Basic configuration for the standard logging system
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger("logging_setup")
    logger.info(f"Logging configured with level {log_level}")
