import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": getattr(record, 'process', None),
            "thread": getattr(record, 'thread', None)
        }
        
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
            
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """Setup comprehensive logging configuration"""
    
    # Create logs directory
    if log_file:
        log_file.parent.mkdir(exist_ok=True, parents=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler with colors - add only if not exists
    console_handler = None
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    else:
        # Find existing console handler
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                console_handler = handler
                break

    # Handle encoding issues on Windows
    if sys.platform == "win32" and console_handler:
        import io
        console_handler.stream = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding='utf-8',
            errors='replace'
        )
    
    # File handler with JSON format - add only if not exists
    if log_file and not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    # Specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return root_logger


def mask_secrets(text: str) -> str:
    """Mask sensitive information in log messages"""
    if not isinstance(text, str):
        return text

    # Common API key patterns to mask
    patterns = [
        # OpenAI API keys: sk-... (keep first 3 and last 3 chars)
        (r'\b(sk-[a-zA-Z0-9]{3})[a-zA-Z0-9]{30,}([a-zA-Z0-9]{3})\b', r'\1***\2'),
        # Generic API keys with prefixes
        (r'\b(api[_-]?key[_-]?[:=]\s*)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        (r'\b(token[_-]?[:=]\s*)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        (r'\b(secret[_-]?[:=]\s*)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        # Authorization headers
        (r'\b(Bearer\s+)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        (r'\b(Authorization:\s*Bearer\s+)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        # Password patterns
        (r'\b(password[_-]?[:=]\s*)[^\s]{3,}\b', r'\1***MASKED***'),
        # Email addresses (mask username)
        (r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', r'***@\2'),
    ]

    masked_text = text
    for pattern, replacement in patterns:
        masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)

    return masked_text


class ContextualLogger:
    """Logger with request context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        self.context.update(kwargs)
    
    def _log_with_context(self, level: int, msg: str, extra_data: Dict[str, Any] = None):
        # Mask sensitive information in the message
        masked_msg = mask_secrets(msg)

        # Also mask sensitive information in extra_data values
        masked_extra_data = extra_data or {}
        if masked_extra_data:
            masked_extra_data = {}
            for key, value in (extra_data or {}).items():
                if isinstance(value, str):
                    masked_extra_data[key] = mask_secrets(value)
                else:
                    masked_extra_data[key] = value

        extra = {"extra_data": {**self.context, **masked_extra_data}}
        self.logger.log(level, masked_msg, extra=extra)
    
    def info(self, msg: str, **kwargs):
        self._log_with_context(logging.INFO, msg, kwargs)
    
    def error(self, msg: str, **kwargs):
        self._log_with_context(logging.ERROR, msg, kwargs)
    
    def warning(self, msg: str, **kwargs):
        self._log_with_context(logging.WARNING, msg, kwargs)

    def debug(self, msg: str, **kwargs):
        self._log_with_context(logging.DEBUG, msg, kwargs)

    def critical(self, msg: str, **kwargs):
        self._log_with_context(logging.CRITICAL, msg, kwargs)
