import asyncio
from src.services.logging import ContextualLogger
from src.core.config.manager import get_config
from src.core.config.models import UnifiedConfig
from src.core.telemetry.telemetry import telemetry, TracedSpan
from src.core.http.client_v2 import get_advanced_http_client
from src.core.cache.smart import get_response_cache, get_summary_cache, shutdown_caches
from src.core.memory.manager import get_memory_manager, shutdown_memory_manager
from src.core.security.auth import APIKeyAuth
from src.core.routing.rate_limiter import rate_limiter
from src.core.chaos.monkey import chaos_monkey
from src.core.alerting.manager import alert_manager
from src.core.providers.factory import provider_factory

logger = ContextualLogger(__name__)

class AppState:
    """A singleton-like class to hold the application's state."""

    def __init__(self):
        self.config: UnifiedConfig = None
        self.http_client = None
        self.response_cache = None
        self.summary_cache = None
        self.memory_manager = None
        self.api_key_auth = None

    async def initialize(self):
        """Initializes all the application components."""
        logger.info("AppState: Initializing all application components...")
        self.config = get_config()

        # Configure OpenTelemetry
        telemetry.configure(self.config.telemetry)
        logger.info("AppState: OpenTelemetry configured.")

        # Initialize HTTP client
        with TracedSpan("http_client.initialize"):
            self.http_client = get_advanced_http_client(**self.config.http_client)
            await self.http_client.initialize()
            logger.info("AppState: HTTP client initialized.")

        # Initialize caches
        with TracedSpan("cache.initialize"):
            self.response_cache = await get_response_cache(self.config.caching)
            self.summary_cache = await get_summary_cache(self.config.caching)
            logger.info("AppState: Smart caches initialized.")

        # Initialize memory manager
        with TracedSpan("memory_manager.initialize"):
            self.memory_manager = await get_memory_manager(self.config.memory)
            logger.info("AppState: Memory manager initialized.")

        # Initialize authentication
        self.api_key_auth = APIKeyAuth(self.config.proxy_api_keys)
        logger.info(f"AppState: Authentication initialized with {len(self.config.proxy_api_keys)} API key(s).")

        # Configure rate limiter
        rate_limiter.configure_from_settings(self.config.rate_limit)
        logger.info("AppState: Per-route rate limiting configured.")

        # Configure chaos engineering
        chaos_monkey.configure(self.config.chaos_engineering)
        logger.info("AppState: Chaos engineering configured.")

        # Start alerting system
        with TracedSpan("alerting.initialize"):
            await alert_manager.start_monitoring()
            logger.info("AppState: Alerting system initialized and monitoring started.")

        # Initialize provider factory
        with TracedSpan("provider_factory.initialize"):
            await provider_factory.initialize(self.config)
            logger.info("AppState: Provider factory initialized.")

        logger.info("AppState: All components initialized successfully.")

    async def shutdown(self):
        """Shuts down all the application components."""
        logger.info("AppState: Shutting down all application components...")
        try:
            shutdown_tasks = [
                shutdown_memory_manager(),
                shutdown_caches(),
                alert_manager.stop_monitoring(),
            ]
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
            logger.info("AppState: All primary systems shutdown successfully.")
        except Exception as e:
            logger.error(f"Error during AppState shutdown: {e}", exc_info=True)

# Create a single global instance of the AppState
app_state = AppState()
