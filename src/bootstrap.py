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

# Initial, basic logging setup before config is loaded
setup_logging(log_level="INFO")
logger = ContextualLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting LLM Proxy API")

    try:
        # Initialize the application state, which handles all component setup
        await asyncio.wait_for(app_state.initialize(), timeout=60.0)
        app.state.app_state = app_state
        app.state.config = app_state.config
        logger.info("Application state initialized successfully.")

        # Re-configure logging based on the loaded configuration
        if app.state.config and app.state.config.logging:
            log_level = (app.state.config.logging.level or "INFO").upper()
            setup_logging(log_level=log_level)
        else:
            logger.warning("Logging configuration not found, continuing with default setup.")

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

# FastAPI app setup
app = FastAPI(
    title="LLM Proxy API",
    version="2.0.0",
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimitingMiddleware)

# Include API routers
app.include_router(root_router)
app.include_router(main_router)
