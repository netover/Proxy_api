import asyncio
import importlib
import os
import time
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type

import httpx

from src.core.http_client_v2 import (AdvancedHTTPClient,
                                     get_advanced_http_client)
from src.core.logging import ContextualLogger
from src.core.metrics import metrics_collector
from src.core.unified_config import (ProviderConfig, ProviderType,
                                     config_manager)
from src.models.model_info import ModelInfo

logger = ContextualLogger(__name__)

class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"

class ProviderCapability(Enum):
    """Capabilities supported by providers"""
    CHAT_COMPLETION = "chat_completion"
    TEXT_COMPLETION = "text_completion"
    EMBEDDINGS = "embeddings"
    MODEL_DISCOVERY = "model_discovery"
    STREAMING = "streaming"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    TOOL_CALLING = "tool_calling"

@dataclass
class ProviderInfo:
    """Information about a provider instance"""
    name: str
    type: ProviderType
    status: ProviderStatus
    models: List[str]
    priority: int
    enabled: bool
    forced: bool
    last_health_check: float
    error_count: int
    last_error: Optional[str] = None

class BaseProvider(ABC):
    """Enhanced base provider with better resource management"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self.models = config.models
        self.priority = config.priority
        # Use centralized HTTP client with connection pooling
        self._http_client: Optional[AdvancedHTTPClient] = None

        # Initialize provider capabilities
        self._capabilities = self._get_capabilities()

    @property
    def capabilities(self) -> Set[ProviderCapability]:
        """Get provider capabilities"""
        return self._capabilities

    def _get_capabilities(self) -> set[ProviderCapability]:
        """Get provider capabilities - override in subclasses"""
        capabilities = {
            ProviderCapability.CHAT_COMPLETION,
            ProviderCapability.TEXT_COMPLETION,
            ProviderCapability.EMBEDDINGS
        }

        # Add streaming if supported
        if hasattr(self, 'create_completion') and callable(getattr(self, 'create_completion', None)):
            # Check if create_completion accepts 'stream' parameter
            import inspect
            sig = inspect.signature(self.create_completion)
            if 'stream' in sig.parameters:
                capabilities.add(ProviderCapability.STREAMING)

        # Add model discovery if supported
        if (hasattr(self, 'list_models') and hasattr(self, 'retrieve_model') and
            callable(getattr(self, 'list_models', None)) and callable(getattr(self, 'retrieve_model', None))):
            capabilities.add(ProviderCapability.MODEL_DISCOVERY)

        return capabilities
    
    @property
    async def http_client(self) -> AdvancedHTTPClient:
        """Get centralized HTTP client with connection pooling"""
        if self._http_client is None:
            # Get configuration from config manager
            config = config_manager.load_config()
            http_config = config.get('http_client', {})

            # Use provider-specific settings with fallback to global config
            max_keepalive = getattr(self.config, 'max_keepalive_connections',
                                  http_config.get('pool_limits', {}).get('max_keepalive_connections', 30))
            max_connections = getattr(self.config, 'max_connections',
                                    http_config.get('pool_limits', {}).get('max_connections', 100))
            keepalive_expiry = getattr(self.config, 'keepalive_expiry',
                                     http_config.get('pool_limits', {}).get('keepalive_timeout', 30.0))
            timeout = getattr(self.config, 'timeout', http_config.get('timeout', 30.0))

            self._http_client = get_advanced_http_client(
                provider_name=self.name,
                max_keepalive_connections=max_keepalive,
                max_connections=max_connections,
                keepalive_expiry=keepalive_expiry,
                timeout=timeout
            )

        return self._http_client

    async def close(self) -> None:
        """Close provider resources (HTTP client is managed centrally)"""
        # The centralized HTTP client manages its own lifecycle
        # We don't close it here as it may be shared across providers
        self._http_client = None
        self.logger.info("Provider resources closed")
    
    @property
    def status(self) -> ProviderStatus:
        """Current provider status"""
        return self._status
    
    @property
    def info(self) -> ProviderInfo:
        """Get provider information"""
        return ProviderInfo(
            name=self.name,
            type=self.config.type,
            status=self._status,
            models=self.models,
            priority=self.priority,
            enabled=self.config.enabled,
            forced=self.config.forced,
            last_health_check=self._last_health_check,
            error_count=self._error_count,
            last_error=self._last_error
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check with status tracking"""
        start_time = time.time()
        
        try:
            # Skip if checked recently (within 30 seconds)
            if time.time() - self._last_health_check < 30:
                return {
                    "status": self._status.value,
                    "cached": True,
                    "last_check": self._last_health_check
                }
            
            # Perform actual health check
            result = await self._perform_health_check()
            response_time = time.time() - start_time
            
            # Update status based on result
            if result.get("healthy", False):
                self._status = ProviderStatus.HEALTHY
                self._error_count = max(0, self._error_count - 1)  # Decrease error count on success
                self._last_error = None
            else:
                self._status = ProviderStatus.DEGRADED
                self._error_count += 1
                self._last_error = result.get("error", "Health check failed")
            
            self._last_health_check = time.time()
            
            # Record metrics
            metrics_collector.record_request(
                self.name,
                success=result.get("healthy", False),
                response_time=response_time,
                error_type=None if result.get("healthy") else "health_check_failed"
            )
            
            return {
                "status": self._status.value,
                "healthy": result.get("healthy", False),
                "response_time": response_time,
                "error_count": self._error_count,
                "last_error": self._last_error,
                "details": result.get("details", {})
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self._status = ProviderStatus.UNHEALTHY
            self._error_count += 1
            self._last_error = str(e)
            self._last_health_check = time.time()
            
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            
            self.logger.error(f"Health check failed: {e}")
            
            return {
                "status": self._status.value,
                "healthy": False,
                "response_time": response_time,
                "error": str(e),
                "error_count": self._error_count
            }
    
    @abstractmethod
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Provider-specific health check implementation"""
    
    @abstractmethod
    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion"""
    
    @abstractmethod
    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion"""
    
    @abstractmethod
    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings"""
    
    async def make_request(self,
                          method: str,
                          url: str,
                          **kwargs) -> httpx.Response:
        """Make HTTP request using centralized HTTP client with connection pooling"""
        client = await self.http_client

        # Add authorization header if not present
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        if 'Authorization' not in kwargs['headers'] and hasattr(self, 'api_key'):
            kwargs['headers']['Authorization'] = f"Bearer {self.api_key}"

        # Add User-Agent if not present
        if 'User-Agent' not in kwargs['headers']:
            kwargs['headers']['User-Agent'] = f"LLM-Proxy-API/2.0 ({self.name})"

        # Add custom headers from config
        if hasattr(self.config, 'custom_headers'):
            kwargs['headers'].update(self.config.custom_headers)

        # Use the centralized client's request method which includes retry logic
        return await client.request(method, url, **kwargs)
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def list_models(self) -> List[ModelInfo]:
        """List available models - default implementation raises NotImplementedError"""
        raise NotImplementedError("Model discovery not supported by this provider")

    async def retrieve_model(self, model_id: str) -> Optional[ModelInfo]:
        """Retrieve model information - default implementation raises NotImplementedError"""
        raise NotImplementedError("Model retrieval not supported by this provider")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

class ProviderFactory:
    """Centralized provider factory with caching and lifecycle management"""
    
    # Mapping of provider types to their implementation modules/classes
    PROVIDER_MAPPING = {
        ProviderType.OPENAI: ("src.providers.openai", "OpenAIProvider"),
        ProviderType.ANTHROPIC: ("src.providers.anthropic", "AnthropicProvider"),
        ProviderType.AZURE_OPENAI: ("src.providers.azure_openai", "AzureOpenAIProvider"),
        ProviderType.PERPLEXITY: ("src.providers.perplexity", "PerplexityProvider"),
        ProviderType.GROK: ("src.providers.grok", "GrokProvider"),
        ProviderType.BLACKBOX: ("src.providers.blackbox", "BlackboxProvider"),
        ProviderType.OPENROUTER: ("src.providers.openrouter", "OpenRouterProvider"),
        ProviderType.COHERE: ("src.providers.cohere", "CohereProvider"),
    }
    
    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
        self._provider_classes: Dict[ProviderType, Type[BaseProvider]] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Weak references to track all instances
        self._all_instances: weakref.WeakSet = weakref.WeakSet()
    
    def _load_provider_class(self, provider_type: ProviderType) -> Type[BaseProvider]:
        """Load provider class dynamically with caching"""
        if provider_type in self._provider_classes:
            return self._provider_classes[provider_type]
        
        if provider_type not in self.PROVIDER_MAPPING:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        module_path, class_name = self.PROVIDER_MAPPING[provider_type]
        
        try:
            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)
            
            # Validate that it's actually a BaseProvider subclass
            if not issubclass(provider_class, BaseProvider):
                raise ValueError(f"{class_name} is not a BaseProvider subclass")
            
            # Cache the class
            self._provider_classes[provider_type] = provider_class
            
            logger.info(f"Loaded provider class: {provider_type.value} -> {module_path}.{class_name}")
            return provider_class
            
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load provider {provider_type}: {e}")
    
    async def create_provider(self, config: ProviderConfig) -> BaseProvider:
        """Create a new provider instance with retry logic"""
        if not config.enabled:
            raise ValueError(f"Provider {config.name} is disabled")

        provider_class = self._load_provider_class(config.type)
        last_exception = None
        max_retries = 2  # Or get from config

        for attempt in range(max_retries + 1):
            try:
                provider = provider_class(config)
                self._all_instances.add(provider)

                # Perform initial health check
                health_result = await provider.health_check()

                logger.info(f"Created provider: {config.name} (attempt {attempt + 1})",
                           type=config.type.value,
                           status=health_result.get("status"),
                           models=len(config.models))

                # If provider is unhealthy, we might still return it but log a warning
                if health_result.get("status") == "unhealthy":
                    logger.warning(f"Provider {config.name} created but is initially unhealthy.")

                return provider

            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Failed to create provider {config.name} (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to create provider {config.name} after {max_retries + 1} attempts: {e}")
        
        # All retries failed
        raise last_exception
    
    async def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get cached provider by name"""
        return self._providers.get(name)
    
    async def initialize_providers(self, provider_configs: List[ProviderConfig]) -> Dict[str, BaseProvider]:
        """Initialize all providers from configuration"""
        logger.info(f"Initializing {len(provider_configs)} providers...")
        
        # Clear existing providers
        await self.shutdown()
        self._providers.clear()
        
        # Create new providers
        successful_providers = {}
        failed_providers = []

        for config in provider_configs:
            if not config.enabled:
                logger.info(f"Skipping disabled provider: {config.name}")
                continue

            try:
                provider = await self.create_provider(config)
                successful_providers[config.name] = provider
                self._providers[config.name] = provider

            except Exception as e:
                logger.error(f"Failed to initialize provider {config.name}: {e}")
                failed_providers.append((config.name, str(e)))

        logger.info(f"Initialized {len(successful_providers)} providers successfully")

        if failed_providers:
            logger.warning(f"Failed to initialize {len(failed_providers)} providers: {failed_providers}")

        # Start background health checks
        if successful_providers:
            await self.start_health_monitoring()

        return successful_providers
    
    async def start_health_monitoring(self) -> None:
        """Start background health monitoring for all providers"""
        if self._health_check_task and not self._health_check_task.done():
            return  # Already running
        
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Started health monitoring for providers")
    
    async def _health_check_loop(self) -> None:
        """Background loop for health checks"""
        while not self._shutdown_event.is_set():
            try:
                # Check all providers
                for provider in self._providers.values():
                    try:
                        await provider.health_check()
                    except Exception as e:
                        logger.error(f"Health check failed for {provider.name}: {e}")
                
                # Wait for next check or shutdown
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=60.0)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Continue health checks
                    
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def get_providers_for_model(self, model: str, required_capability: Optional[ProviderCapability] = None) -> List[BaseProvider]:
        """Get providers that support the model and optional capability, with forced provider priority"""
        from src.core.unified_config import config_manager

        config = config_manager.load_config()

        # Check for forced provider first
        forced_provider = config.get_forced_provider()
        if forced_provider:
            forced_instance = self._providers.get(forced_provider.name)
            if forced_instance and model in forced_instance.models:
                # Check capability if required
                if required_capability and required_capability not in forced_instance.capabilities:
                    return []  # Forced provider doesn't support required capability
                # Return only the forced provider
                return [forced_instance]

        # Fall back to normal selection
        providers = []
        for provider in self._providers.values():
            if (model in provider.models and
                provider.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]):
                # Check capability if required
                if required_capability and required_capability not in provider.capabilities:
                    continue  # Skip providers that don't support required capability
                providers.append(provider)

        # Sort by priority (lower number = higher priority)
        return sorted(providers, key=lambda p: p.priority)
    
    async def get_all_provider_info(self) -> List[ProviderInfo]:
        """Get information about all providers"""
        return [provider.info for provider in self._providers.values()]
    
    def is_discovery_enabled(self, provider_name: str) -> bool:
        """
        Check if a provider supports model discovery.
        
        Args:
            provider_name: Name of the provider to check
            
        Returns:
            True if the provider supports discovery, False otherwise
        """
        provider = self._providers.get(provider_name)
        if not provider:
            return False
        
        # Check if provider has discovery methods
        return (
            hasattr(provider, 'list_models') and
            hasattr(provider, 'retrieve_model') and
            callable(getattr(provider, 'list_models', None)) and
            callable(getattr(provider, 'retrieve_model', None))
        )
    
    async def discover_models(self, provider_name: str) -> List[ModelInfo]:
        """
        Discover models for a specific provider.
        
        Args:
            provider_name: Name of the provider to discover models for
            
        Returns:
            List of ModelInfo objects for available models
            
        Raises:
            ValueError: If provider doesn't exist or doesn't support discovery
        """
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found")
        
        if not self.is_discovery_enabled(provider_name):
            raise ValueError(f"Provider '{provider_name}' doesn't support model discovery")
        
        try:
            models = await provider.list_models()
            logger.info(f"Discovered {len(models)} models from {provider_name}")
            return models
        except Exception as e:
            logger.error(f"Failed to discover models for {provider_name}: {e}")
            raise
    
    async def retrieve_model(self, provider_name: str, model_id: str) -> Optional[ModelInfo]:
        """
        Retrieve model information from a specific provider.
        
        Args:
            provider_name: Name of the provider
            model_id: ID of the model to retrieve
            
        Returns:
            ModelInfo object if found, None otherwise
            
        Raises:
            ValueError: If provider doesn't exist or doesn't support discovery
        """
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found")
        
        if not self.is_discovery_enabled(provider_name):
            raise ValueError(f"Provider '{provider_name}' doesn't support model discovery")
        
        try:
            model_info = await provider.retrieve_model(model_id)
            if model_info:
                logger.info(f"Retrieved model '{model_id}' from {provider_name}")
            else:
                logger.warning(f"Model '{model_id}' not found in {provider_name}")
            return model_info
        except Exception as e:
            logger.error(f"Failed to retrieve model {model_id} from {provider_name}: {e}")
            raise
    
    async def get_discovery_enabled_providers(self) -> List[str]:
        """
        Get list of providers that support model discovery.
        
        Returns:
            List of provider names that support discovery
        """
        return [
            name for name, provider in self._providers.items()
            if self.is_discovery_enabled(name)
        ]
    
    async def shutdown(self) -> None:
        """Shutdown all providers and cleanup resources"""
        logger.info("Shutting down provider factory...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all providers
        close_tasks = []
        for provider in self._providers.values():
            close_tasks.append(provider.close())
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Clean up weak references
        for instance in list(self._all_instances):
            try:
                await instance.close()
            except Exception as e:
                logger.warning(f"Error closing provider instance: {e}")
        
        self._providers.clear()
        self._provider_classes.clear()
        
        logger.info("Provider factory shutdown complete")

# Global instance
provider_factory = ProviderFactory()