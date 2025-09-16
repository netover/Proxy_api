import asyncio
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field, HttpUrl, field_validator

from .logging import ContextualLogger
from .optimized_config import config_loader, load_full_config

logger = ContextualLogger(__name__)


def get_config_paths() -> Tuple[Path, Path, Path, Path]:
    """Returns paths for bundled and external config files (YAML and JSON)"""
    if getattr(sys, "frozen", False):
        # Executable: config bundled (read-only) + config external (writable)
        bundle_yaml = Path(sys._MEIPASS) / "config.yaml"
        bundle_json = Path(sys._MEIPASS) / "config.json"
        external_yaml = Path(sys.executable).parent / "config.yaml"
        external_json = Path(sys.executable).parent / "config.json"
    else:
        # Development: both point to the same files
        base_path = Path(__file__).parent.parent.parent
        bundle_yaml = external_yaml = base_path / "config.yaml"
        bundle_json = external_json = base_path / "config.json"

    return bundle_yaml, bundle_json, external_yaml, external_json


def create_default_config(config_path: Path) -> Dict[str, Any]:
    """Create and return default configuration in appropriate format"""
    default_config = {
        "providers": [
            {
                "name": "openai",
                "type": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
                "models": ["gpt-3.5-turbo", "gpt-4"],
                "enabled": True,
                "priority": 1,
                "timeout": 30,
                "rate_limit": 1000,
                "retry_attempts": 3,
                "retry_delay": 1.0,
            }
        ],
        "condensation": {
            "max_tokens_default": 512,
            "error_keywords": [
                "context_length_exceeded",
                "maximum context length",
            ],
            "adaptive_factor": 0.5,
            "cache_ttl": 300,
        },
    }

    try:
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the config file in appropriate format
        with open(config_path, "w", encoding="utf-8") as f:
            if config_path.suffix.lower() == ".json":
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            else:
                yaml.safe_dump(
                    default_config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )

        logger.info(
            "Created default config file", config_path=str(config_path)
        )
    except Exception as e:
        logger.error(
            "Failed to create default config file",
            error=str(e),
            config_path=str(config_path),
        )

    return default_config


class ProviderConfig(BaseModel):
    """Configuration for a single provider"""

    name: str = Field(..., description="Unique name for the provider")
    type: str = Field(
        ..., description="Provider type (openai, anthropic, etc.)"
    )
    base_url: HttpUrl = Field(..., description="Base URL for the provider API")
    api_key_env: str = Field(
        ..., description="Environment variable name for API key"
    )
    models: List[str] = Field(
        ..., min_length=1, description="List of supported models"
    )
    enabled: bool = Field(True, description="Whether this provider is enabled")
    priority: int = Field(
        100,
        ge=1,
        le=1000,
        description="Provider priority (lower = higher priority)",
    )
    timeout: int = Field(
        30, ge=1, le=300, description="Request timeout in seconds"
    )
    rate_limit: int = Field(
        1000, ge=1, description="Rate limit requests per hour"
    )
    retry_attempts: int = Field(
        3, ge=0, le=10, description="Number of retry attempts"
    )
    retry_delay: float = Field(
        1.0, ge=0.1, le=60.0, description="Delay between retries in seconds"
    )
    headers: Optional[Dict[str, str]] = Field(
        None, description="Additional headers to send"
    )

    # HTTP Connection Pool Configuration
    max_keepalive_connections: int = Field(
        100, ge=1, le=1000, description="Maximum keepalive connections"
    )
    max_connections: int = Field(
        1000, ge=1, le=10000, description="Maximum total connections"
    )
    keepalive_expiry: float = Field(
        30.0, ge=1.0, le=300.0, description="Keepalive expiry in seconds"
    )

    @field_validator("type")
    @classmethod
    def validate_provider_type(cls, v):
        supported_types = [
            "openai",
            "anthropic",
            "azure_openai",
            "cohere",
            "perplexity",
            "grok",
            "blackbox",
            "openrouter",
        ]
        if v.lower() not in supported_types:
            raise ValueError(
                f"Provider type must be one of: {supported_types}"
            )
        return v.lower()

    @field_validator("models")
    @classmethod
    def validate_models(cls, v):
        if not v:
            raise ValueError("At least one model must be specified")
        return list(set(v))  # Remove duplicates


class CondensationConfig(BaseModel):
    """Configuration for context condensation feature"""

    max_tokens_default: int = Field(
        512, ge=1, le=4096, description="Default max tokens for condensation"
    )
    error_keywords: List[str] = Field(
        default_factory=lambda: [
            "context_length_exceeded",
            "maximum context length",
        ],
        description="Keywords to detect context length errors",
    )
    adaptive_enabled: bool = Field(
        True, description="Enable adaptive max_tokens calculation"
    )
    adaptive_factor: float = Field(
        0.5,
        ge=0.1,
        le=1.0,
        description="Factor for adaptive max_tokens calculation",
    )
    cache_ttl: int = Field(
        300, ge=60, le=3600, description="Cache TTL in seconds for summaries"
    )


class AppConfig(BaseModel):
    """Main application configuration"""

    providers: List[ProviderConfig] = Field(..., min_length=1)
    condensation: CondensationConfig = Field(
        default_factory=CondensationConfig
    )

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v):
        if not v:
            raise ValueError("At least one provider must be configured")

        # Check for duplicate names
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError("Provider names must be unique")

        # Check for duplicate priorities
        priorities = [p.priority for p in v]
        if len(priorities) != len(set(priorities)):
            raise ValueError("Provider priorities must be unique")

        return v


def _try_load_config(
    yaml_path: Path, json_path: Path, description: str
) -> Optional[AppConfig]:
    """Helper function to try loading a config file with both YAML and JSON"""
    # Try YAML first
    if yaml_path.exists():
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            logger.info(
                f"Loaded {description} config (YAML)",
                config_path=str(yaml_path),
            )
            return AppConfig(**config_data)
        except Exception as e:
            logger.warning(
                f"Error reading {description} YAML config",
                error=str(e),
                config_path=str(yaml_path),
            )

    # Try JSON as fallback
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            logger.info(
                f"Loaded {description} config (JSON)",
                config_path=str(json_path),
            )
            return AppConfig(**config_data)
        except Exception as e:
            logger.warning(
                f"Error reading {description} JSON config",
                error=str(e),
                config_path=str(json_path),
            )

    return None


def load_config() -> AppConfig:
    """Load config with optimized loading and fallback: external -> bundled -> default"""
    bundle_yaml, bundle_json, external_yaml, external_json = get_config_paths()

    async def _load_optimized():
        """Try to load using optimized loader first"""
        try:
            # Use optimized loader for external config
            if external_yaml.exists():
                config_loader.config_path = external_yaml
                config_data = await load_full_config()
                logger.info(
                    "Loaded external config (optimized)",
                    config_path=str(external_yaml),
                )
                return AppConfig(**config_data)
            elif external_json.exists():
                config_loader.config_path = external_json
                config_data = await load_full_config()
                logger.info(
                    "Loaded external config (optimized)",
                    config_path=str(external_json),
                )
                return AppConfig(**config_data)
        except Exception as e:
            logger.warning(
                "Optimized loader failed for external config", error=str(e)
            )

        return None

    # Try optimized loading first
    try:
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            # If we get here, there's a running loop, so we can't use run_until_complete
            # Fall back to sync loading
            logger.warning("Event loop already running, using sync fallback")
            raise RuntimeError("Event loop already running")
        except RuntimeError:
            # No running loop, we can create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            optimized_config = loop.run_until_complete(_load_optimized())
            if optimized_config:
                return optimized_config
    except Exception as e:
        logger.warning("Async optimized loading failed", error=str(e))

    # Fallback to original synchronous loading
    # 1st: Try external config (editable by user) - YAML preferred, JSON fallback
    external_config = _try_load_config(
        external_yaml, external_json, "external"
    )
    if external_config:
        return external_config

    # 2nd: Try bundled config (read-only) - YAML preferred, JSON fallback
    bundled_config = _try_load_config(bundle_yaml, bundle_json, "bundled")
    if bundled_config:
        # Copy bundled config to external for future editing (try both formats)
        try:
            if bundle_yaml.exists():
                shutil.copy2(bundle_yaml, external_yaml)
                logger.info(
                    "Copied bundled config to external location",
                    source=str(bundle_yaml),
                    destination=str(external_yaml),
                )
            elif bundle_json.exists():
                # Convert JSON to YAML for external editing
                with open(bundle_json, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                with open(external_yaml, "w", encoding="utf-8") as f:
                    yaml.safe_dump(
                        config_data,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                    )
                logger.info(
                    "Converted and copied bundled config to external location",
                    source=str(bundle_json),
                    destination=str(external_yaml),
                )
        except Exception as e:
            logger.warning(
                "Failed to copy config to external location", error=str(e)
            )

        return bundled_config

    # 3rd: Create default config (YAML format)
    logger.info("Creating default config", config_path=str(external_yaml))
    config_data = create_default_config(external_yaml)
    return AppConfig(**config_data)


def init_config():
    """Initialize config"""
    return load_config()
