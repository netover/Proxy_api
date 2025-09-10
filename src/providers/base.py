from src.core.provider_factory import BaseProvider as CoreBaseProvider, provider_factory
import asyncio
import asyncio

# Legacy base for backward compatibility - individual providers should inherit from core.BaseProvider
class Provider(CoreBaseProvider):
    """
    Legacy base class. New providers should inherit directly from core.provider_factory.BaseProvider.
    This class is maintained for compatibility but delegates to the core implementation.
    """
    pass

async def get_provider(config: ProviderConfig) -> Provider:
    """Updated factory function using the centralized ProviderFactory"""
    from src.core.unified_config import ProviderConfig  # Ensure import
    import importlib  # Now included
    
    # Use the centralized factory
    try:
        provider = await provider_factory.create_provider(config)
        return provider  # Returns BaseProvider instance, which is compatible
    except Exception as e:
        raise ValueError(f"Failed to load provider class for {config.type}: {e}")
