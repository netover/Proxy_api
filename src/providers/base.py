from src.core.provider_factory import BaseProvider as CoreBaseProvider
from src.core.provider_factory import provider_factory
from src.core.unified_config import ProviderConfig


# Legacy base for backward compatibility - individual providers should inherit from core.BaseProvider
class Provider(CoreBaseProvider):
    """
    Legacy base class. New providers should inherit directly from core.provider_factory.BaseProvider.
    This class is maintained for compatibility but delegates to the core implementation.
    """


async def get_provider(config: ProviderConfig) -> Provider:
    """Updated factory function using the centralized ProviderFactory"""
    # Use the centralized factory
    try:
        provider = await provider_factory.create_provider(config)
        return provider  # Returns BaseProvider instance, which is compatible
    except Exception as e:
        raise ValueError(f"Failed to load provider class for {config.type}: {e}")
