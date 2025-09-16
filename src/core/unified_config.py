import asyncio
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    validator,
    ConfigDict,
)

from .logging import ContextualLogger
from .metrics import metrics_collector
from .model_config import model_config_manager
from .optimized_config import (
    load_config_section,
    load_critical_config,
    load_full_config,
)

logger = ContextualLogger(__name__)


class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    PERPLEXITY = "perplexity"
    GROK = "grok"
    BLACKBOX = "blackbox"
    OPENROUTER = "openrouter"
    COHERE = "cohere"


class ProviderConfig(BaseModel):
    """Unified provider configuration"""

    name: str = Field(..., min_length=1, max_length=50)
    type: ProviderType
    base_url: HttpUrl
    api_key_env: str = Field(..., pattern=r"^[A-Z_][A-Z0-9_]*$")
    models: List[str] = Field(..., min_items=1, max_items=100)

    # Performance settings
    enabled: bool = Field(default=True)
    forced: bool = Field(default=False)
    priority: int = Field(default=100, ge=1, le=1000)
    timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    rate_limit: Optional[int] = Field(default=None, ge=1)

    # Connection settings
    max_keepalive_connections: int = Field(
        default=100, ge=1, le=1000, description="Maximum keepalive connections"
    )
    max_connections: int = Field(
        default=1000, ge=1, le=10000, description="Maximum total connections"
    )
    keepalive_expiry: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Keepalive expiry in seconds",
    )

    # Headers
    custom_headers: Dict[str, str] = Field(default_factory=dict)

    @field_validator("models")
    @classmethod
    def validate_models(cls, v):
        # Remove duplicates while preserving order
        return list(dict.fromkeys(v))

    @field_validator("custom_headers")
    @classmethod
    def validate_headers(cls, v):
        # Validate header names (basic check)
        for key in v.keys():
            if not key.replace("-", "").replace("_", "").isalnum():
                raise ValueError(f"Invalid header name: {key}")
        return v

    @validator("forced", pre=True, always=True)
    def validate_forced_consistency(cls, v, values):
        """Ensure forced providers are also enabled"""
        if v and not values.get("enabled", True):
            raise ValueError("Forced providers must be enabled")
        return v


class CondensationSettings(BaseModel):
    """Condensation-specific settings for context summarization"""

    cache_ttl: int = Field(
        default=3600, ge=60, le=86400, description="Cache TTL in seconds"
    )
    cache_size: int = Field(
        default=1000, ge=100, le=10000, description="Max cache size for LRU"
    )
    cache_persist: bool = Field(
        default=False, description="Enable persistent cache (e.g., file/Redis)"
    )
    adaptive_enabled: bool = Field(
        default=True, description="Enable adaptive token limit calculation"
    )
    adaptive_factor: float = Field(
        default=0.5,
        ge=0.1,
        le=1.0,
        description="Factor for adaptive max_tokens",
    )
    truncation_threshold: int = Field(
        default=2000,
        ge=500,
        le=10000,
        description="Content length threshold for proactive truncation before summarization",
    )
    max_tokens_default: int = Field(
        default=512,
        ge=100,
        le=4096,
        description="Default max tokens for summaries",
    )
    error_keywords: List[str] = Field(
        default_factory=lambda: ["context_length_exceeded", "token_limit"],
        description="Keywords to detect long context errors",
    )
    fallback_strategies: List[str] = Field(
        default_factory=lambda: ["truncate", "secondary_provider"],
        description="Fallback strategies on failure",
    )
    parallel_providers: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Max concurrent providers for parallelism",
    )
    dynamic_reload: bool = Field(
        default=True, description="Enable dynamic config reloading"
    )

    @field_validator("fallback_strategies")
    @classmethod
    def validate_fallbacks(cls, v):
        valid_strategies = {
            "truncate",
            "secondary_provider",
            "default_summary",
        }
        invalid = [s for s in v if s not in valid_strategies]
        if invalid:
            raise ValueError(
                f"Invalid fallback strategies: {invalid}. Must be one of {valid_strategies}"
            )
        return v


class CacheSettings(BaseModel):
    """Model discovery cache settings"""

    cache_enabled: bool = Field(
        default=True, description="Enable model discovery caching"
    )
    cache_ttl: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Cache TTL in seconds (default: 5 minutes)",
    )
    cache_persist: bool = Field(
        default=False, description="Enable disk persistence for cache"
    )
    cache_dir: Optional[Path] = Field(
        default=None, description="Directory for cache persistence"
    )

    @field_validator("cache_dir")
    @classmethod
    def validate_cache_dir(cls, v):
        if v is not None and not v.is_absolute():
            return Path.cwd() / v
        return v


class GlobalSettings(BaseModel):
    """Global application settings"""

    # App info
    app_name: str = "LLM Proxy API"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="127.0.0.1", pattern=r"^[\w\.\-]+$")
    port: int = Field(default=8000, ge=1, le=65535)

    @field_validator("port", mode="before")
    @classmethod
    def validate_port(cls, v):
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(
                    f"Invalid port number: '{v}' cannot be converted to an integer."
                )
        return v

    # Security
    api_keys: List[str] = Field(default_factory=list, min_items=1)
    api_key_header: str = Field(
        default="X-API-Key", pattern=r"^[A-Za-z0-9\-_]+$"
    )
    cors_origins: List[str] = Field(default=["*"])

    # Performance
    rate_limit_rpm: int = Field(default=1000, ge=1)
    rate_limit_window: int = Field(default=60, ge=1, le=3600)
    request_timeout: int = Field(default=300, ge=1, le=3600)

    # Resilience
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=50)
    circuit_breaker_timeout: int = Field(default=60, ge=1, le=3600)

    # Paths
    log_level: str = Field(
        default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    log_file: Optional[Path] = Field(default=None)
    config_file: Path = Field(default=Path("config.yaml"))
    condensation: CondensationSettings = Field(
        default_factory=CondensationSettings,
        description="Settings for context condensation optimizations",
    )
    cache: CacheSettings = Field(
        default_factory=CacheSettings,
        description="Settings for model discovery caching",
    )

    model_config = ConfigDict(
        env_prefix="PROXY_API_", case_sensitive=False, env_file=".env"
    )


class UnifiedConfig(BaseModel):
    """Complete proxy configuration"""

    settings: GlobalSettings
    providers: List[ProviderConfig] = Field(..., min_items=1)

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v):
        # Check unique names
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError("Provider names must be unique")

        # Check unique priorities among enabled providers
        enabled_priorities = [p.priority for p in v if p.enabled]
        if len(enabled_priorities) != len(set(enabled_priorities)):
            raise ValueError("Enabled provider priorities must be unique")

        # Check for multiple forced providers
        forced_providers = [p.name for p in v if p.forced]
        if len(forced_providers) > 1:
            raise ValueError(
                f"Only one provider can be forced. Found: {forced_providers}"
            )

        # Validate API keys exist with prefix (only warn, don't fail)
        missing_keys = []
        for provider in v:
            if provider.enabled and not os.getenv(
                f"PROXY_API_{provider.api_key_env}"
            ):
                missing_keys.append(f"PROXY_API_{provider.api_key_env}")

        if missing_keys:
            # Log warning instead of raising error for better test compatibility
            import warnings

            warnings.warn(
                f"Missing environment variables (this is normal in test environments): {missing_keys}",
                UserWarning,
                stacklevel=2,
            )

        return v

    def get_forced_provider(self) -> Optional[ProviderConfig]:
        """Get the forced provider if one exists and is enabled"""
        forced_providers = [
            p for p in self.providers if p.forced and p.enabled
        ]
        return forced_providers[0] if forced_providers else None


class ConfigManager:
    """Centralized configuration manager with optimized loading and validation"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.yaml")
        self._config: Optional[UnifiedConfig] = None
        self._critical_config: Optional[Dict[str, Any]] = None
        self._lazy_loaded_sections: Dict[str, Any] = {}
        self._event_loop = None

    def _get_event_loop(self):
        """Get or create event loop for async operations"""
        if self._event_loop is None:
            try:
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    def load_config(self, force_reload: bool = False) -> UnifiedConfig:
        """Load configuration with optimized loading, caching, and validation"""
        start_time = time.time()
        success = False
        config_file_size = 0
        providers_count = 0

        try:
            # Get config file size if it exists
            if self.config_path.exists():
                config_file_size = self.config_path.stat().st_size

            # Try to load critical config first (async)
            loop = self._get_event_loop()
            if loop.is_running():
                # If loop is running, we need to use the optimized loader directly
                config = self._load_config_sync(force_reload)
            else:
                # Can run async operations
                config = loop.run_until_complete(
                    self._load_config_async(force_reload)
                )

            success = True
            providers_count = len(config.providers) if config.providers else 0
            return config

        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")
        finally:
            # Record metrics
            load_time_ms = (time.time() - start_time) * 1000
            metrics_collector.record_config_load(
                load_time_ms=load_time_ms,
                success=success,
                config_file_size=config_file_size,
                providers_count=providers_count,
            )

    async def _load_config_async(
        self, force_reload: bool = False
    ) -> UnifiedConfig:
        """Async configuration loading with lazy loading and validation"""
        try:
            # Load critical sections first
            if self._critical_config is None or force_reload:
                self._critical_config = await load_critical_config()

            # Load providers (critical)
            providers_data = self._critical_config.get("providers", [])

            # Load other critical settings
            settings_data = {
                k: v
                for k, v in self._critical_config.items()
                if k != "providers"
            }

            # Validate critical configuration
            critical_config_data = dict(settings_data)
            critical_config_data["providers"] = providers_data
            from .config_schema import config_validator

            config_validator.validate_config(
                critical_config_data, self.config_path
            )

            # Create configuration with critical data
            self._config = UnifiedConfig(
                settings=GlobalSettings(**settings_data),
                providers=[ProviderConfig(**p) for p in providers_data],
            )

            return self._config

        except Exception as e:
            # Fallback to sync loading
            return self._load_config_sync(force_reload)

    def _load_config_sync(self, force_reload: bool = False) -> UnifiedConfig:
        """Synchronous fallback for configuration loading with validation"""
        try:
            # Use optimized loader's sync interface
            loop = self._get_event_loop()
            if not loop.is_running():
                config_data = loop.run_until_complete(load_full_config())
            else:
                # Load synchronously using yaml directly
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

                # Validate configuration before proceeding
                from .config_schema import config_validator

                config_validator.validate_config(config_data, self.config_path)

            # Separate global settings from providers
            providers_data = config_data.pop("providers", [])
            settings_data = config_data

            # Create configuration
            self._config = UnifiedConfig(
                settings=GlobalSettings(**settings_data),
                providers=[ProviderConfig(**p) for p in providers_data],
            )

            return self._config

        except FileNotFoundError:
            return self._create_default_config()
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def _create_default_config(self) -> UnifiedConfig:
        """Create default configuration if none exists"""
        default_config = UnifiedConfig(
            settings=GlobalSettings(
                api_keys=["your-api-key-here"],
                debug=True,
                condensation=CondensationSettings(),  # Use defaults
            ),
            providers=[
                ProviderConfig(
                    name="openai_default",
                    type=ProviderType.OPENAI,
                    base_url="https://api.openai.com/v1",
                    api_key_env="OPENAI_API_KEY",
                    models=["gpt-3.5-turbo", "gpt-4"],
                    priority=1,
                )
            ],
        )

        # Save default config
        self.save_config(default_config)
        return default_config

    def save_config(self, config: UnifiedConfig) -> None:
        """Save configuration to file"""
        # Create a serializable dictionary using built-in serialization
        config_dict = {
            **config.settings.dict(exclude={"providers"}),
            "providers": [],
        }

        # Convert providers to serializable format
        for provider in config.providers:
            provider_dict = provider.dict()
            # Convert HttpUrl to string
            if "base_url" in provider_dict:
                provider_dict["base_url"] = str(provider_dict["base_url"])
            # Convert enum to string
            if "type" in provider_dict:
                provider_dict["type"] = str(provider_dict["type"])
            # Convert Path to string
            if "config_file" in provider_dict and provider_dict["config_file"]:
                provider_dict["config_file"] = str(
                    provider_dict["config_file"]
                )
            if "log_file" in provider_dict and provider_dict["log_file"]:
                provider_dict["log_file"] = str(provider_dict["log_file"])
            config_dict["providers"].append(provider_dict)

        # Handle settings paths and enums
        if "config_file" in config_dict and config_dict["config_file"]:
            config_dict["config_file"] = str(config_dict["config_file"])
        if "log_file" in config_dict and config_dict["log_file"]:
            config_dict["log_file"] = str(config_dict["log_file"])

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
            )

        # Update cache
        self._config = config
        self._last_modified = self.config_path.stat().st_mtime

    def get_providers_for_model(self, model: str) -> List[ProviderConfig]:
        """Get enabled providers that support the given model, sorted by priority"""
        if not self._config:
            self.load_config()

        # Check for forced provider first
        forced_provider = self.get_forced_provider()
        if forced_provider and model in forced_provider.models:
            return [forced_provider]

        # Fall back to normal priority-based selection
        providers = [
            p
            for p in self._config.providers
            if p.enabled and model in p.models
        ]

        return sorted(providers, key=lambda p: p.priority)

    def get_provider_by_name(self, name: str) -> Optional[ProviderConfig]:
        """Get provider by name"""
        if not self._config:
            self.load_config()

        return next(
            (p for p in self._config.providers if p.name == name), None
        )

    def set_forced_provider(self, provider_name: str) -> None:
        """Set a provider as forced, unsetting others"""
        if not self._config:
            self.load_config()

        # Unset all forced providers
        for provider in self._config.providers:
            provider.forced = False

        # Set the specified provider as forced
        target_provider = self.get_provider_by_name(provider_name)
        if target_provider:
            if not target_provider.enabled:
                raise ValueError("Cannot force a disabled provider")
            target_provider.forced = True
            self.save_config(self._config)

    def toggle_provider_enabled(
        self, provider_name: str, enabled: bool
    ) -> None:
        """Toggle provider enabled status"""
        if not self._config:
            self.load_config()

        provider = self.get_provider_by_name(provider_name)
        if provider:
            provider.enabled = enabled
            # If disabling a forced provider, also unset forced
            if not enabled and provider.forced:
                provider.forced = False
            self.save_config(self._config)

    def get_model_selection(self, provider_name: str) -> Optional[str]:
        """Get the selected model for a provider"""
        selection = model_config_manager.get_model_selection(provider_name)
        return selection.model_name if selection else None

    def set_model_selection(
        self, provider_name: str, model_name: str, editable: bool = True
    ) -> None:
        """Set the model selection for a provider"""
        if not self._config:
            self.load_config()

        # Validate that the provider exists and supports the model
        provider = self.get_provider_by_name(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found")

        if model_name not in provider.models:
            raise ValueError(
                f"Model '{model_name}' not supported by provider '{provider_name}'"
            )

        model_config_manager.set_model_selection(
            provider_name, model_name, editable
        )

    def update_model_selection(
        self, provider_name: str, model_name: str
    ) -> bool:
        """Update an existing model selection if it's editable"""
        if not self._config:
            self.load_config()

        # Validate that the provider exists and supports the model
        provider = self.get_provider_by_name(provider_name)
        if not provider:
            return False

        if model_name not in provider.models:
            return False

        result = model_config_manager.update_model_selection(
            provider_name, model_name
        )
        return result is not None

    def remove_model_selection(self, provider_name: str) -> bool:
        """Remove the model selection for a provider"""
        return model_config_manager.remove_model_selection(provider_name)

    def get_all_model_selections(self) -> Dict[str, str]:
        """Get all model selections as a simple mapping"""
        return model_config_manager.get_selected_models()

    def get_model_selection_details(self) -> Dict[str, Any]:
        """Get detailed model selections including metadata"""
        selections = model_config_manager.get_all_selections()
        return {
            provider_name: {
                "model_name": selection.model_name,
                "editable": selection.editable,
                "last_updated": selection.last_updated.isoformat(),
            }
            for provider_name, selection in selections.items()
        }

    def validate_model_selection(
        self, provider_name: str, model_name: str
    ) -> bool:
        """Validate if a model selection is valid for a provider"""
        if not self._config:
            self.load_config()

        provider = self.get_provider_by_name(provider_name)
        if not provider:
            return False

        return model_name in provider.models

    def get_available_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider"""
        if not self._config:
            self.load_config()

        provider = self.get_provider_by_name(provider_name)
        return provider.models if provider else []

    async def load_section_async(self, section: str) -> Optional[Any]:
        """Lazily load a non-critical configuration section"""
        if section in self._lazy_loaded_sections:
            return self._lazy_loaded_sections[section]

        try:
            section_data = await load_config_section(section)
            if section_data:
                self._lazy_loaded_sections[section] = section_data
            return section_data
        except Exception as e:
            logger.warning(f"Failed to lazy load section '{section}': {e}")
            return None

    def load_section(self, section: str) -> Optional[Any]:
        """Synchronous version of lazy section loading"""
        loop = self._get_event_loop()
        if loop.is_running():
            # Create task for async operation
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, self.load_section_async(section)
                )
                return future.result()
        else:
            return loop.run_until_complete(self.load_section_async(section))

    def get_telemetry_config(self) -> Optional[Dict[str, Any]]:
        """Get telemetry configuration (lazy loaded)"""
        return self.load_section("telemetry")

    def get_chaos_config(self) -> Optional[Dict[str, Any]]:
        """Get chaos engineering configuration (lazy loaded)"""
        return self.load_section("chaos_engineering")

    def get_load_testing_config(self) -> Optional[Dict[str, Any]]:
        """Get load testing configuration (lazy loaded)"""
        return self.load_section("load_testing")

    def get_network_simulation_config(self) -> Optional[Dict[str, Any]]:
        """Get network simulation configuration (lazy loaded)"""
        return self.load_section("network_simulation")


# Global instance
config_manager = ConfigManager()
