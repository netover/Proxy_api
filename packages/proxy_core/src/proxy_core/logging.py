"""Logging utilities for proxy_core package."""

import logging
from typing import Any, Dict, Optional


class ContextualLogger:
    """Enhanced logger with context support."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _add_context(self, message: str, **kwargs: Any) -> str:
        """Add context to log message."""
        if kwargs:
            context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} [{context_str}]"
        return message
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self.logger.debug(self._add_context(message, **kwargs))
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self.logger.info(self._add_context(message, **kwargs))
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self.logger.warning(self._add_context(message, **kwargs))
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self.logger.error(self._add_context(message, **kwargs))
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with context."""
        self.logger.critical(self._add_context(message, **kwargs))