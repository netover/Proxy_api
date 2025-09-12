"""
JSON Schema validation for config.yaml
Provides fast failure validation at startup with detailed error reporting
"""

from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema
from jsonschema import SchemaError

from .logging import ContextualLogger

logger = ContextualLogger(__name__)

# JSON Schema for config.yaml validation
CONFIG_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        # App configuration
        "app": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
                "environment": {"type": "string", "enum": ["development", "staging", "production"]}
            },
            "required": ["name", "version"]
        },

        # Server configuration
        "server": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "format": "hostname"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "debug": {"type": "boolean"},
                "reload": {"type": "boolean"}
            },
            "required": ["host", "port"]
        },

        # Telemetry configuration
        "telemetry": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "service_name": {"type": "string", "minLength": 1},
                "service_version": {"type": "string"},
                "jaeger": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "endpoint": {"type": "string", "format": "uri"}
                    }
                },
                "zipkin": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "endpoint": {"type": "string", "format": "uri"}
                    }
                },
                "sampling": {
                    "type": "object",
                    "properties": {
                        "probability": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                    }
                }
            }
        },

        # Templates configuration
        "templates": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "directory": {"type": "string"},
                "cache_size": {"type": "integer", "minimum": 1},
                "auto_reload": {"type": "boolean"}
            }
        },

        # Chaos engineering configuration
        "chaos_engineering": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "faults": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["delay", "error", "rate_limit", "timeout", "network_failure"]},
                            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                            "probability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "duration_ms": {"type": "integer", "minimum": 1},
                            "error_code": {"type": "integer"},
                            "error_message": {"type": "string"}
                        },
                        "required": ["type", "severity", "probability"]
                    }
                }
            }
        },

        # Rate limiting
        "rate_limit": {
            "type": "object",
            "properties": {
                "requests_per_window": {"type": "integer", "minimum": 1},
                "window_seconds": {"type": "integer", "minimum": 1},
                "burst_limit": {"type": "integer", "minimum": 1}
            }
        },

        # Authentication
        "auth": {
            "type": "object",
            "properties": {
                "api_keys": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "minItems": 1
                }
            },
            "required": ["api_keys"]
        },

        # Providers configuration - most critical section
        "providers": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 50},
                    "type": {"type": "string", "enum": ["openai", "anthropic", "azure_openai", "cohere", "perplexity", "grok", "blackbox", "openrouter"]},
                    "api_key_env": {"type": "string", "pattern": r"^[A-Z_][A-Z0-9_]*$"},
                    "base_url": {"type": "string", "format": "uri"},
                    "models": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "minItems": 1,
                        "maxItems": 100
                    },
                    "enabled": {"type": "boolean"},
                    "forced": {"type": "boolean"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 1000},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 300},
                    "max_retries": {"type": "integer", "minimum": 0, "maximum": 10},
                    "max_connections": {"type": "integer", "minimum": 1, "maximum": 1000},
                    "max_keepalive_connections": {"type": "integer", "minimum": 1, "maximum": 1000},
                    "keepalive_expiry": {"type": "number", "minimum": 1.0, "maximum": 300.0},
                    "retry_delay": {"type": "number", "minimum": 0.1, "maximum": 60.0},
                    "custom_headers": {
                        "type": "object",
                        "patternProperties": {
                            "^[a-zA-Z0-9_-]+$": {"type": "string"}
                        },
                        "additionalProperties": False
                    }
                },
                "required": ["name", "type", "api_key_env", "base_url", "models"]
            }
        },

        # Circuit breaker
        "circuit_breaker": {
            "type": "object",
            "properties": {
                "failure_threshold": {"type": "integer", "minimum": 1},
                "recovery_timeout": {"type": "integer", "minimum": 1},
                "half_open_max_calls": {"type": "integer", "minimum": 1},
                "expected_exception": {"type": "string"}
            }
        },

        # Context condensation
        "condensation": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "truncation_threshold": {"type": "integer", "minimum": 500},
                "summary_max_tokens": {"type": "integer", "minimum": 100},
                "cache_size": {"type": "integer", "minimum": 100},
                "cache_ttl": {"type": "integer", "minimum": 60},
                "cache_persist": {"type": "boolean"},
                "cache_redis_url": {"type": "string"},
                "error_patterns": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },

        # Caching
        "caching": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "response_cache": {
                    "type": "object",
                    "properties": {
                        "max_size_mb": {"type": "integer", "minimum": 1},
                        "ttl": {"type": "integer", "minimum": 1},
                        "compression": {"type": "boolean"}
                    }
                },
                "summary_cache": {
                    "type": "object",
                    "properties": {
                        "max_size_mb": {"type": "integer", "minimum": 1},
                        "ttl": {"type": "integer", "minimum": 1},
                        "compression": {"type": "boolean"}
                    }
                }
            }
        },

        # Memory management
        "memory": {
            "type": "object",
            "properties": {
                "max_usage_percent": {"type": "integer", "minimum": 1, "maximum": 100},
                "gc_threshold_percent": {"type": "integer", "minimum": 1, "maximum": 100},
                "monitoring_interval": {"type": "integer", "minimum": 1},
                "cache_cleanup_interval": {"type": "integer", "minimum": 1}
            }
        },

        # HTTP client
        "http_client": {
            "type": "object",
            "properties": {
                "timeout": {"type": "integer", "minimum": 1},
                "connect_timeout": {"type": "integer", "minimum": 1},
                "read_timeout": {"type": "integer", "minimum": 1},
                "pool_limits": {
                    "type": "object",
                    "properties": {
                        "max_connections": {"type": "integer", "minimum": 1},
                        "max_keepalive_connections": {"type": "integer", "minimum": 1},
                        "keepalive_timeout": {"type": "integer", "minimum": 1}
                    }
                }
            }
        },

        # Logging
        "logging": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "format": {"type": "string", "enum": ["json", "text"]},
                "file": {"type": "string"},
                "rotation": {
                    "type": "object",
                    "properties": {
                        "max_size_mb": {"type": "integer", "minimum": 1},
                        "max_files": {"type": "integer", "minimum": 1}
                    }
                }
            }
        },

        # Health check
        "health_check": {
            "type": "object",
            "properties": {
                "interval": {"type": "integer", "minimum": 1},
                "timeout": {"type": "integer", "minimum": 1},
                "providers": {"type": "boolean"},
                "context_service": {"type": "boolean"},
                "memory": {"type": "boolean"},
                "cache": {"type": "boolean"}
            }
        },

        # Load testing
        "load_testing": {
            "type": "object",
            "properties": {
                "tiers": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                            "type": "object",
                            "properties": {
                                "users": {"type": "integer", "minimum": 1},
                                "duration": {"type": "string"},
                                "ramp_up": {"type": "string"},
                                "expected_rps": {"type": "integer", "minimum": 1}
                            },
                            "required": ["users", "duration", "ramp_up", "expected_rps"]
                        }
                    }
                }
            }
        },

        # Network simulation
        "network_simulation": {
            "type": "object",
            "properties": {
                "profiles": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                            "type": "object",
                            "properties": {
                                "min_delay": {"type": "integer", "minimum": 0},
                                "max_delay": {"type": "integer", "minimum": 0},
                                "jitter": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                            },
                            "required": ["min_delay", "max_delay", "jitter"]
                        }
                    }
                }
            }
        }
    },

    # Critical sections that must be present
    "required": ["app", "server", "auth", "providers"]
}

class ConfigValidator:
    """Configuration validator with fast failure and detailed error reporting"""

    def __init__(self, schema: Dict[str, Any] = None):
        self.schema = schema or CONFIG_SCHEMA
        self._validator = jsonschema.Draft202012Validator(self.schema)

    def validate_config(self, config_data: Dict[str, Any], config_path: Optional[Path] = None) -> None:
        """
        Validate configuration data against schema

        Args:
            config_data: Configuration dictionary to validate
            config_path: Path to config file for error reporting

        Raises:
            ValueError: If validation fails with detailed error message
        """
        try:
            # Validate against schema
            errors = list(self._validator.iter_errors(config_data))

            if errors:
                error_messages = []
                for error in errors:
                    path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                    error_messages.append(f"  {path}: {error.message}")

                config_file = str(config_path) if config_path else "config"
                error_summary = f"Configuration validation failed for {config_file}:\n" + "\n".join(error_messages)

                logger.error("Configuration validation failed", errors=len(errors))
                raise ValueError(error_summary)

            logger.info("Configuration validation successful")

        except SchemaError as e:
            logger.error("Configuration schema error", error=str(e))
            raise ValueError(f"Configuration schema is invalid: {e}")

    def validate_config_file(self, config_path: Path) -> Dict[str, Any]:
        """
        Load and validate configuration from file

        Args:
            config_path: Path to configuration file

        Returns:
            Validated configuration dictionary

        Raises:
            ValueError: If file doesn't exist or validation fails
        """
        if not config_path.exists():
            raise ValueError(f"Configuration file not found: {config_path}")

        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                config_data = {}

            # Validate the loaded configuration
            self.validate_config(config_data, config_path)

            return config_data

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file {config_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")

    def get_schema_summary(self) -> Dict[str, Any]:
        """Get summary of schema requirements for documentation"""
        required_sections = self.schema.get("required", [])
        optional_sections = []

        for prop in self.schema.get("properties", {}):
            if prop not in required_sections:
                optional_sections.append(prop)

        return {
            "required_sections": required_sections,
            "optional_sections": optional_sections,
            "schema_version": "Draft 2020-12"
        }

# Global validator instance
config_validator = ConfigValidator()

def validate_config_at_startup(config_path: Path) -> Dict[str, Any]:
    """
    Validate configuration at application startup with fast failure

    Args:
        config_path: Path to configuration file

    Returns:
        Validated configuration dictionary

    Raises:
        SystemExit: If validation fails (fast failure)
    """
    try:
        logger.info("Validating configuration at startup", config_path=str(config_path))
        config_data = config_validator.validate_config_file(config_path)
        logger.info("Configuration validation passed")
        return config_data

    except ValueError as e:
        logger.error("Configuration validation failed at startup", error=str(e))
        print(f"\n❌ CONFIGURATION ERROR:")
        print(f"{e}")
        print("\n🔧 Please fix the configuration file and restart the application.\n")
        exit(1)

    except Exception as e:
        logger.error("Unexpected error during configuration validation", error=str(e))
        print(f"\n❌ UNEXPECTED CONFIGURATION ERROR:")
        print(f"{e}")
        print("\n🔧 Please check the configuration file and try again.\n")
        exit(1)