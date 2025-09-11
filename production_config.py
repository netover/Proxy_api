"""
Production Configuration for LLM Proxy API
High-performance, scalable deployment configuration.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
import logging

# Production environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_STAGING = ENVIRONMENT == "staging"

# Base paths
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"
METRICS_DIR = BASE_DIR / "metrics"

# Ensure directories exist
for directory in [LOGS_DIR, CACHE_DIR, METRICS_DIR]:
    directory.mkdir(exist_ok=True)

# Production Configuration
PRODUCTION_CONFIG = {
    # Server Configuration
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "workers": int(os.getenv("WORKERS", "4")),  # Gunicorn workers
    "worker_class": "uvicorn.workers.UvicornWorker",
    "worker_connections": 1000,
    "max_requests": 1000,  # Restart worker after this many requests
    "max_requests_jitter": 50,

    # Performance Tuning
    "http_client": {
        "max_keepalive_connections": int(os.getenv("HTTP_MAX_KEEPALIVE", "200")),
        "max_connections": int(os.getenv("HTTP_MAX_CONNECTIONS", "2000")),
        "keepalive_expiry": float(os.getenv("HTTP_KEEPALIVE_EXPIRY", "30.0")),
        "timeout": float(os.getenv("HTTP_TIMEOUT", "30.0")),
        "connect_timeout": float(os.getenv("HTTP_CONNECT_TIMEOUT", "10.0")),
        "retry_attempts": int(os.getenv("HTTP_RETRY_ATTEMPTS", "3")),
    },

    "cache": {
        "response_cache_size": int(os.getenv("RESPONSE_CACHE_SIZE", "10000")),
        "response_cache_ttl": int(os.getenv("RESPONSE_CACHE_TTL", "1800")),  # 30 min
        "summary_cache_size": int(os.getenv("SUMMARY_CACHE_SIZE", "2000")),
        "summary_cache_ttl": int(os.getenv("SUMMARY_CACHE_TTL", "3600")),  # 1 hour
        "max_memory_mb": int(os.getenv("CACHE_MAX_MEMORY_MB", "512")),
    },

    "memory_manager": {
        "memory_threshold_mb": int(os.getenv("MEMORY_THRESHOLD_MB", "1024")),
        "emergency_threshold_mb": int(os.getenv("EMERGENCY_MEMORY_MB", "1536")),
        "cleanup_interval": int(os.getenv("CLEANUP_INTERVAL", "300")),
        "enable_gc_tuning": os.getenv("ENABLE_GC_TUNING", "true").lower() == "true",
        "leak_detection_enabled": os.getenv("LEAK_DETECTION", "true").lower() == "true",
    },

    "circuit_breaker": {
        "failure_threshold": int(os.getenv("CB_FAILURE_THRESHOLD", "5")),
        "recovery_timeout": int(os.getenv("CB_RECOVERY_TIMEOUT", "60")),
        "success_threshold": int(os.getenv("CB_SUCCESS_THRESHOLD", "3")),
        "adaptive_thresholds": os.getenv("CB_ADAPTIVE", "true").lower() == "true",
    },

    # Security Configuration
    "security": {
        "api_keys_required": os.getenv("API_KEYS_REQUIRED", "true").lower() == "true",
        "rate_limit_requests": int(os.getenv("RATE_LIMIT_REQUESTS", "1000")),
        "rate_limit_window": int(os.getenv("RATE_LIMIT_WINDOW", "60")),
        "cors_origins": os.getenv("CORS_ORIGINS", "https://yourdomain.com").split(","),
        "trusted_proxies": os.getenv("TRUSTED_PROXIES", "").split(",") if os.getenv("TRUSTED_PROXIES") else [],
        "ssl_certfile": os.getenv("SSL_CERTFILE"),
        "ssl_keyfile": os.getenv("SSL_KEYFILE"),
    },

    # Logging Configuration
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": LOGS_DIR / "app.log",
        "max_file_size": int(os.getenv("LOG_MAX_SIZE", "100")),  # MB
        "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "10")),
        "json_format": os.getenv("LOG_JSON_FORMAT", "true").lower() == "true",
    },

    # Monitoring Configuration
    "monitoring": {
        "metrics_enabled": os.getenv("METRICS_ENABLED", "true").lower() == "true",
        "metrics_port": int(os.getenv("METRICS_PORT", "9090")),
        "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
        "alert_webhook_url": os.getenv("ALERT_WEBHOOK_URL"),
        "alert_threshold_cpu": float(os.getenv("ALERT_CPU_THRESHOLD", "80.0")),
        "alert_threshold_memory": float(os.getenv("ALERT_MEMORY_THRESHOLD", "85.0")),
    },

    # Database Configuration (if needed)
    "database": {
        "url": os.getenv("DATABASE_URL"),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    },

    # External Services
    "external": {
        "redis_url": os.getenv("REDIS_URL"),
        "prometheus_url": os.getenv("PROMETHEUS_URL"),
        "grafana_url": os.getenv("GRAFANA_URL"),
        "alertmanager_url": os.getenv("ALERTMANAGER_URL"),
    }
}

# Environment-specific overrides
if IS_PRODUCTION:
    PRODUCTION_CONFIG.update({
        "logging": {
            **PRODUCTION_CONFIG["logging"],
            "level": "WARNING",
            "json_format": True,
        },
        "cache": {
            **PRODUCTION_CONFIG["cache"],
            "max_memory_mb": 1024,  # 1GB for production
        },
        "http_client": {
            **PRODUCTION_CONFIG["http_client"],
            "max_connections": 5000,
            "max_keepalive_connections": 500,
        }
    })

elif IS_STAGING:
    PRODUCTION_CONFIG.update({
        "logging": {
            **PRODUCTION_CONFIG["logging"],
            "level": "INFO",
            "json_format": True,
        }
    })

def get_production_config() -> Dict[str, Any]:
    """Get production configuration with environment overrides"""
    return PRODUCTION_CONFIG.copy()

def setup_production_logging():
    """Setup production logging configuration"""
    config = PRODUCTION_CONFIG["logging"]

    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set log level
    root_logger.setLevel(getattr(logging, config["level"]))

    # Create formatters
    if config["json_format"]:
        try:
            import pythonjsonlogger.jsonlogger
            formatter = pythonjsonlogger.jsonlogger.JsonFormatter(
                fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
            )
        except ImportError:
            formatter = logging.Formatter(config["format"])
    else:
        formatter = logging.Formatter(config["format"])

    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        config["file"],
        maxBytes=config["max_file_size"] * 1024 * 1024,
        backupCount=config["backup_count"]
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler for development
    if not IS_PRODUCTION:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

def validate_production_config() -> List[str]:
    """Validate production configuration and return issues"""
    issues = []

    config = get_production_config()

    # Check required API keys
    if config["security"]["api_keys_required"]:
        api_keys = os.getenv("PROXY_API_KEYS", "")
        if not api_keys or len(api_keys.split(",")) < 1:
            issues.append("PROXY_API_KEYS must be configured with at least one key")

    # Check SSL configuration for production
    if IS_PRODUCTION:
        if not config["security"]["ssl_certfile"] or not config["security"]["ssl_keyfile"]:
            issues.append("SSL certificates must be configured for production")

    # Check external services
    if config["monitoring"]["metrics_enabled"]:
        if not config["external"]["prometheus_url"]:
            issues.append("Prometheus URL must be configured when metrics are enabled")

    # Check database configuration
    if config["database"]["url"]:
        # Validate database URL format
        pass

    return issues

# Production startup validation
def validate_production_readiness() -> bool:
    """Validate that the system is ready for production"""
    issues = validate_production_config()

    if issues:
        print("🚨 Production Configuration Issues:")
        for issue in issues:
            print(f"  ❌ {issue}")
        return False

    print("✅ Production configuration validated successfully")
    return True

if __name__ == "__main__":
    # Validate configuration when run directly
    if validate_production_readiness():
        print("\n🚀 System is ready for production deployment!")
        print(f"Environment: {ENVIRONMENT}")
        print(f"Workers: {PRODUCTION_CONFIG['workers']}")
        print(f"Host: {PRODUCTION_CONFIG['host']}:{PRODUCTION_CONFIG['port']}")
    else:
        print("\n❌ System is NOT ready for production deployment!")
        exit(1)