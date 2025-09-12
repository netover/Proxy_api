from pathlib import Path
from typing import Optional

from src.core.logging import ContextualLogger
from src.core.provider_factory import ProviderFactory
from src.core.rate_limiter import rate_limiter
from src.core.unified_config import ConfigManager

logger = ContextualLogger(__name__)

class AppState:
    """Centralized application state to break circular dependencies"""
    
    def __init__(self):
        self.config_manager: Optional[ConfigManager] = None
        self.provider_factory: Optional[ProviderFactory] = None
        self.initialized = False
    
    async def initialize(self, config_path: Optional[Path] = None):
        """Initialize all components in correct order"""
        if self.initialized:
            logger.info("AppState already initialized")
            return
            
        try:
            logger.info("Initializing AppState components")
            
            # 1. Config manager first
            self.config_manager = ConfigManager(config_path)
            
            # 2. Provider factory with config
            self.provider_factory = ProviderFactory()
            
            # 3. Load configuration
            config = self.config_manager.load_config()
            logger.info(f"Loaded config with {len(config.providers)} providers")
            
            # 4. Initialize providers
            await self.provider_factory.initialize_providers(config.providers)
            logger.info("Providers initialized successfully")
            
            # 5. Configure rate limiter
            rate_limiter.configure_limits(config.settings.rate_limit_rpm)
            
            self.initialized = True
            logger.info("AppState initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize AppState: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup all resources"""
        if not self.initialized:
            return
            
        logger.info("Shutting down AppState")
        try:
            if self.provider_factory:
                await self.provider_factory.shutdown()
            self.initialized = False
            logger.info("AppState shutdown complete")
        except Exception as e:
            logger.error(f"Error during AppState shutdown: {e}")

# Global app state instance
app_state = AppState()