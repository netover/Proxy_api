"""Model discovery service for OpenAI-compatible providers."""

import asyncio
import hashlib
from typing import List, Optional

import aiohttp

from ..models.model_info import ModelInfo
from .exceptions import ProviderError, ValidationError
from .http_client import HTTPClient
from .logging import ContextualLogger
from .unified_cache import get_unified_cache

logger = ContextualLogger(__name__)


class ProviderConfig:
    """
    Configuration for a model provider.

    This class encapsulates all necessary configuration for connecting to
    an OpenAI-compatible API endpoint.

    Attributes:
        name: Human-readable name for the provider
        base_url: Base URL for the API endpoint
        api_key: API key for authentication
        organization: Optional organization ID
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 3)
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        organization: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize provider configuration."""
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.organization = organization
        self.timeout = timeout
        self.max_retries = max_retries

    def __str__(self) -> str:
        """String representation of the provider config."""
        return f"ProviderConfig(name='{self.name}', base_url='{self.base_url}')"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            "ProviderConfig("
            f"name='{self.name}', "
            f"base_url='{self.base_url}', "
            "api_key='***masked***', "
            f"organization={self.organization}, "
            f"timeout={self.timeout}, "
            f"max_retries={self.max_retries}"
            ")"
        )


class ModelDiscoveryService:
    """
    Service for discovering and validating models from OpenAI-compatible providers.

    This service provides methods to:
    - Discover available models from a provider
    - Validate if a specific model exists and is accessible
    - Handle provider-specific quirks and variations

    The service is designed to be provider-agnostic and works with any
    OpenAI-compatible API endpoint.

    Features:
    - Intelligent caching with TTL support
    - LRU eviction for memory efficiency
    - Background cache management
    """

    def __init__(self, http_client: Optional[HTTPClient] = None):
        """
        Initialize the model discovery service.

        Args:
            http_client: Optional HTTP client instance. If not provided,
                        a new instance will be created.
        """
        self.http_client = http_client or HTTPClient()
        self._cache = None
        logger.info("ModelDiscoveryService initialized", service_type="model_discovery")

    async def _get_cache(self):
        """Get or initialize the unified cache instance"""
        if self._cache is None:
            self._cache = await get_unified_cache()
        return self._cache

    def _generate_model_cache_key(self, provider_config: ProviderConfig) -> str:
        """Generate a unique cache key for provider models"""
        key_string = f"models:{provider_config.name}:{provider_config.base_url}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def invalidate_model_cache(self, provider_config: ProviderConfig) -> bool:
        """
        Invalidate cached model data for a specific provider.

        Args:
            provider_config: Configuration for the provider to invalidate

        Returns:
            True if cache was invalidated, False if not found
        """
        cache = await self._get_cache()
        cache_key = self._generate_model_cache_key(provider_config)
        result = await cache.delete(cache_key)
        if result:
            logger.info(
                "Invalidated model cache",
                provider=provider_config.name,
                cache_key=cache_key,
            )
        else:
            logger.debug(
                "No cache entry to invalidate",
                provider=provider_config.name,
                cache_key=cache_key,
            )
        return result

    async def clear_all_model_cache(self) -> int:
        """
        Clear all cached model data.

        Returns:
            Number of cache entries cleared
        """
        cache = await self._get_cache()
        count = await cache.clear(category="models")
        logger.info(
            "Cleared model cache entries",
            entries_cleared=count,
            category="models",
        )
        return count

    async def get_cache_stats(self):
        """
        Get cache statistics for model discovery.

        Returns:
            Dictionary with cache statistics
        """
        cache = await self._get_cache()
        stats = await cache.get_stats()

        # Filter stats for model-related entries
        model_entries = 0
        for category, count in stats.get("categories", {}).items():
            if category == "models":
                model_entries = count
                break

        return {
            "model_cache_entries": model_entries,
            "total_cache_entries": stats.get("entries", 0),
            "cache_hit_rate": stats.get("hit_rate", 0),
            "cache_memory_usage_mb": stats.get("memory_usage_mb", 0),
            "cache_max_memory_mb": stats.get("max_memory_mb", 0),
        }

    async def discover_models(self, provider_config: ProviderConfig) -> List[ModelInfo]:
        """
        Discover all available models from a provider with intelligent caching.

        This method queries the provider's /v1/models endpoint and returns
        a list of ModelInfo objects for all available models. Results are cached
        for 15 minutes to reduce API calls and improve performance.

        Args:
            provider_config: Configuration for the provider to query

        Returns:
            List of ModelInfo objects for all available models

        Raises:
            ProviderError: If the provider is unreachable or returns an error
            ValidationError: If the response format is invalid

        Example:
            >>> config = ProviderConfig("openai", "https://api.openai.com", "sk-...")
            >>> service = ModelDiscoveryService()
            >>> models = await service.discover_models(config)
            >>> print(f"Found {len(models)} models")
        """
        cache = await self._get_cache()
        cache_key = self._generate_model_cache_key(provider_config)

        # Try to get from cache first
        cached_models = await cache.get(cache_key, category="models")
        if cached_models is not None:
            logger.debug(
                "Cache hit for models",
                provider=provider_config.name,
                model_count=len(cached_models),
                cache_key=cache_key,
            )
            return cached_models

        # Cache miss - fetch from provider
        logger.info(
            "Cache miss - discovering models from provider",
            provider=provider_config.name,
            cache_key=cache_key,
        )

        url = f"{provider_config.base_url}/v1/models"
        headers = {
            "Authorization": f"Bearer {provider_config.api_key}",
            "Content-Type": "application/json",
        }

        if provider_config.organization:
            headers["OpenAI-Organization"] = provider_config.organization

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=provider_config.timeout)
            ) as session:
                for attempt in range(provider_config.max_retries + 1):
                    try:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                break
                            elif response.status == 401:
                                raise ProviderError(
                                    f"Authentication failed for {provider_config.name}. "
                                    "Check your API key."
                                )
                            elif response.status == 403:
                                raise ProviderError(
                                    f"Access forbidden for {provider_config.name}. "
                                    "Check your permissions."
                                )
                            elif response.status == 429:
                                if attempt < provider_config.max_retries:
                                    wait_time = 2**attempt
                                    logger.warning(
                                        f"Rate limited, waiting {wait_time}s before retry"
                                    )
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise ProviderError(
                                        f"Rate limit exceeded for {provider_config.name}"
                                    )
                            else:
                                raise ProviderError(
                                    f"HTTP {response.status} from {provider_config.name}"
                                )
                    except aiohttp.ClientError as e:
                        if attempt < provider_config.max_retries:
                            wait_time = 2**attempt
                            logger.warning(
                                f"Request failed: {e}. Retrying in {wait_time}s"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise ProviderError(
                                f"Failed to connect to {provider_config.name}: {e}"
                            )

                # Parse response
                if not isinstance(data, dict) or "data" not in data:
                    raise ValidationError(
                        f"Invalid response format from {provider_config.name}"
                    )

                models = []
                for model_data in data["data"]:
                    try:
                        model_info = ModelInfo.from_dict(model_data)
                        models.append(model_info)
                    except (KeyError, ValueError) as e:
                        logger.warning(
                            f"Skipping invalid model data: {e}. Data: {model_data}"
                        )
                        continue

                # Cache the results (15 minutes TTL for model data)
                await cache.set(
                    cache_key, models, ttl=900, category="models", priority=3
                )

                logger.info(
                    "Discovered and cached models",
                    provider=provider_config.name,
                    model_count=len(models),
                    cache_key=cache_key,
                    ttl_seconds=900,
                )
                return models

        except asyncio.TimeoutError:
            raise ProviderError(
                f"Timeout connecting to {provider_config.name} "
                f"after {provider_config.timeout}s"
            )

    async def validate_model(
        self, provider_config: ProviderConfig, model_id: str
    ) -> bool:
        """
        Validate if a specific model exists and is accessible.

        This method checks if a model with the given ID is available from
        the provider. Uses cached model data when available for better performance.

        Args:
            provider_config: Configuration for the provider to query
            model_id: The model ID to validate

        Returns:
            True if the model exists and is accessible, False otherwise

        Example:
            >>> config = ProviderConfig("openai", "https://api.openai.com", "sk-...")
            >>> service = ModelDiscoveryService()
            >>> is_valid = await service.validate_model(config, "gpt-4")
            >>> print(f"Model exists: {is_valid}")
        """
        logger.debug(
            f"Validating model '{model_id}' from provider: {provider_config.name}"
        )

        try:
            models = await self.discover_models(provider_config)
            exists = any(model.id == model_id for model in models)

            if exists:
                logger.debug(f"Model '{model_id}' is valid")
            else:
                logger.debug(
                    f"Model '{model_id}' not found in {len(models)} available models"
                )

            return exists

        except ProviderError as e:
            logger.error(f"Failed to validate model: {e}")
            return False

    async def get_model_info(
        self, provider_config: ProviderConfig, model_id: str
    ) -> Optional[ModelInfo]:
        """
        Get detailed information for a specific model.

        Args:
            provider_config: Configuration for the provider to query
            model_id: The model ID to retrieve information for

        Returns:
            ModelInfo object if the model exists, None otherwise

        Example:
            >>> config = ProviderConfig("openai", "https://api.openai.com", "sk-...")
            >>> service = ModelDiscoveryService()
            >>> model_info = await service.get_model_info(config, "gpt-4")
            >>> if model_info:
            ...     print(f"Model owned by: {model_info.owned_by}")
        """
        logger.info(
            f"Getting model info for '{model_id}' from provider: {provider_config.name}"
        )

        try:
            models = await self.discover_models(provider_config)
            for model in models:
                if model.id == model_id:
                    return model
            return None

        except ProviderError as e:
            logger.error(f"Failed to get model info: {e}")
            return None

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self.http_client:
            await self.http_client.close()
        logger.info("ModelDiscoveryService closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
