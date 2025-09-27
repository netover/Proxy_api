import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.app_state import app_state
from src.core.logging import setup_logging, ContextualLogger
from src.api.router import root_router, main_router
from src.middleware.security_headers import SecurityHeadersMiddleware
from src.middleware.rate_limiter import RateLimitingMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.core.config.manager import get_config
from src.core.config.models import UnifiedConfig

# Setup logging based on the initial config load. This is fine for module-level.
log_level = (get_config().logging.level or "INFO").upper()
setup_logging(log_level=log_level)
logger = ContextualLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting LLM Proxy API")
    try:
        # The config is now passed to the app factory and attached to app.state
        # so we can use it here directly.
        await asyncio.wait_for(app_state.initialize(app.state.config), timeout=60.0)
        app.state.app_state = app_state
        logger.info("Application state initialized successfully.")
        logger.info("LLM Proxy API started successfully.")
    except asyncio.TimeoutError:
        logger.error("Application initialization timed out.")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    logger.info("Shutting down LLM Proxy API...")
    await app_state.shutdown()
    logger.info("LLM Proxy API shutdown complete.")

def create_app(config: UnifiedConfig) -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    app = FastAPI(
        title=config.app.name,
        version=config.app.version,
        description="High-performance LLM proxy with intelligent routing and fallback",
        lifespan=lifespan,
    )

    # Attach the config to the app state so the lifespan and other parts can use it.
    app.state.config = config

    # Add middleware in the correct order.
    if config.cors.enabled:
        logger.info(f"CORS enabled. Allowed origins: {config.cors.allow_origins}")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors.allow_origins,
            allow_credentials=config.cors.allow_credentials,
            allow_methods=config.cors.allow_methods,
            allow_headers=config.cors.allow_headers,
        )
    else:
        logger.info("CORS is disabled by configuration.")

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RateLimitingMiddleware)

    # Include API routers.
    app.include_router(root_router)
    app.include_router(main_router)

    return app

# Create the global app instance for the production entrypoint (e.g., uvicorn src.bootstrap:app)
app = create_app(get_config())