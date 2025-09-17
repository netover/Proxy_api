"""FastAPI application factory and configuration."""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Import from our packages
from proxy_context import (
    SmartCache,
    MemoryManager,
)
from proxy_logging import (
    StructuredLogger,
    MetricsCollector,
    OpenTelemetryConfig,
    PrometheusExporter,
)

from .endpoints import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger = StructuredLogger("proxy_api")
    logger.info("Starting Proxy API...")

    # Initialize components
    app.state.metrics = MetricsCollector()
    app.state.cache = SmartCache()
    app.state.memory_manager = MemoryManager()

    # Start Prometheus metrics server
    prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8000"))
    app.state.prometheus = PrometheusExporter(port=prometheus_port)
    app.state.prometheus.start_server()

    # Configure OpenTelemetry
    otel_config = OpenTelemetryConfig(prometheus_exporter=app.state.prometheus)
    otel_config.configure()
    app.state.otel_config = otel_config

    logger.info("Proxy API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Proxy API...")
    if hasattr(app.state, "cache"):
        await app.state.cache.close()
    if hasattr(app.state, "memory_manager"):
        await app.state.memory_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Proxy API",
        description="A high-performance proxy API for LLM providers with caching, rate limiting, and circuit breaking",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    origins = os.getenv("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add request ID to all requests."""
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Add logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all requests."""
        logger = StructuredLogger("proxy_api")
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

        # Record metrics
        if hasattr(request.app.state, "prometheus"):
            request.app.state.prometheus.record_request(
                request.method,
                request.url.path,
                response.status_code,
                duration,
            )

        return response

    # Add error handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger = StructuredLogger("proxy_api")
        logger.error(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "http_exception",
                    "status_code": exc.status_code,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger = StructuredLogger("proxy_api")
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "error": str(exc),
                "error_type": type(exc).__name__,
                "request_id": getattr(request.state, "request_id", None),
            },
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "Internal server error",
                    "type": "internal_error",
                    "status_code": 500,
                }
            },
        )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Include analytics routes
    from .analytics import router as analytics_router

    app.include_router(analytics_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": int(time.time()),
            "version": "1.0.0",
            "uptime": time.time() - getattr(app.state, "start_time", time.time()),
        }

    # Telemetry configuration endpoint
    @app.get("/telemetry/config")
    async def telemetry_config():
        """Get current telemetry configuration."""
        if hasattr(app.state, "otel_config"):
            return app.state.otel_config.get_telemetry_config()
        return {"error": "Telemetry not configured"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Proxy API is running",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return app


# Create the application instance
app = create_app()
