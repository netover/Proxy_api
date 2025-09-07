import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
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
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with JSON format
    if log_file:
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

class ContextualLogger:
    """Logger with request context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        self.context.update(kwargs)
    
    def _log_with_context(self, level: int, msg: str, extra_data: Dict[str, Any] = None):
        extra = {"extra_data": {**self.context, **(extra_data or {})}}
        self.logger.log(level, msg, extra=extra)
    
    def info(self, msg: str, **kwargs):
        self._log_with_context(logging.INFO, msg, kwargs)
    
    def error(self, msg: str, **kwargs):
        self._log_with_context(logging.ERROR, msg, kwargs)
    
    def warning(self, msg: str, **kwargs):
        self._log_with_context(logging.WARNING, msg, kwargs)
