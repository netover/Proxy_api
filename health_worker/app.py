from fastapi import FastAPI, Response, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
logging.info("BaseHTTPMiddleware imported successfully")
import asyncio
import httpx
import logging
import os
import time
import random
import uuid
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from enum import Enum
import contextvars
import signal
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configuration management
def load_provider_config() -> List[Dict[str, Any]]:
    """Load provider configuration from file or environment"""
    config_file = os.getenv("PROVIDER_CONFIG_FILE", "health_worker_providers.json")

    # Try to load from file first
    if Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                validate_provider_config(config)
                logger.info(f"Loaded provider configuration from {config_file}")
                return config.get("providers", [])
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load config from {config_file}: {e}")

    # Fallback to environment variable
    env_config = os.getenv("PROVIDER_CONFIG")
    if env_config:
        try:
            config = json.loads(env_config)
            validate_provider_config(config)
            logger.info("Loaded provider configuration from environment")
            return config.get("providers", [])
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse provider config from environment: {e}")

    # Final fallback to hardcoded config
    logger.warning("Using hardcoded provider configuration as fallback")
    return [
        {"name": "openai", "base_url": "https://api.openai.com", "models": ["gpt-3.5-turbo", "gpt-4"]},
        {"name": "anthropic", "base_url": "https://api.anthropic.com", "models": ["claude-3-sonnet"]},
        {"name": "google", "base_url": "https://generativelanguage.googleapis.com", "models": ["gemini-pro"]},
    ]

def validate_provider_config(config: Dict[str, Any]) -> None:
    """Validate provider configuration structure"""
    if not isinstance(config, dict):
        raise ProviderConfigError("Configuration must be a dictionary")

    providers = config.get("providers", [])
    if not isinstance(providers, list):
        raise ProviderConfigError("Providers must be a list")

    required_fields = ["name", "base_url", "models"]
    for provider in providers:
        if not isinstance(provider, dict):
            raise ProviderConfigError("Each provider must be a dictionary")

        for field in required_fields:
            if field not in provider:
                raise ProviderConfigError(f"Provider missing required field: {field}")

        if not isinstance(provider["models"], list):
            raise ProviderConfigError("Models must be a list")

async def discover_providers() -> List[Dict[str, Any]]:
    """Auto-discover providers from various sources"""
    discovered_providers = []

    # Try to discover from environment-based registry
    registry_url = os.getenv("PROVIDER_REGISTRY_URL")
    if registry_url and shared_client:
        try:
            response = await shared_client.get(f"{registry_url}/providers", timeout=5.0)
            if response.status_code == 200:
                registry_data = response.json()
                discovered_providers.extend(registry_data.get("providers", []))
                logger.info(f"Discovered {len(discovered_providers)} providers from registry")
        except Exception as e:
            logger.warning(f"Failed to discover providers from registry: {e}")

    # Try to discover from Kubernetes service discovery
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        try:
            # This would integrate with Kubernetes API to discover services
            # For now, just log that Kubernetes discovery is available
            logger.info("Kubernetes service discovery available")
        except Exception as e:
            logger.warning(f"Kubernetes discovery failed: {e}")

    # Try to discover from Consul
    consul_url = os.getenv("CONSUL_URL")
    if consul_url and shared_client:
        try:
            response = await shared_client.get(f"{consul_url}/v1/catalog/services", timeout=5.0)
            if response.status_code == 200:
                services = response.json()
                # Filter for AI provider services
                ai_services = {name: tags for name, tags in services.items()
                             if any(tag in ['ai', 'llm', 'provider'] for tag in tags)}
                logger.info(f"Discovered {len(ai_services)} AI services from Consul")
        except Exception as e:
            logger.warning(f"Consul discovery failed: {e}")

    return discovered_providers

async def update_provider_config() -> None:
    """Update provider configuration with discovered providers"""
    try:
        discovered = await discover_providers()
        if discovered:
            # Merge with existing configuration
            current_config = load_provider_config()
            existing_names = {p["name"] for p in current_config}

            new_providers = [p for p in discovered if p["name"] not in existing_names]
            if new_providers:
                current_config.extend(new_providers)
                logger.info(f"Added {len(new_providers)} newly discovered providers")

                # Update global provider status tracking
                for provider in new_providers:
                    provider_name = provider["name"]
                    if provider_name not in provider_status:
                        provider_status[provider_name] = {
                            "status": "unknown",
                            "last_check": None,
                            "models": provider["models"]
                        }
    except Exception as e:
        logger.error(f"Provider discovery update failed: {e}")

# Structured logging setup
try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGING = True
except ImportError:
    JSON_LOGGING = False

# Configurable log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Request ID context
request_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('request_id', default=None)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_context.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.monotonic()
        response = await call_next(request)
        process_time = time.monotonic() - start_time
        logger.info(
            f"Request completed",
            extra={
                'method': request.method,
                'url': str(request.url),
                'status_code': response.status_code,
                'process_time': f"{process_time:.4f}s"
            }
        )
        return response

# Configure logging
if JSON_LOGGING:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(request_id)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
else:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(request_id)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    handlers=[handler]
)

# Custom logger adapter for request ID
class RequestIDAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        request_id = request_id_context.get()
        if request_id:
            return msg, {**kwargs, 'extra': {'request_id': request_id}}
        return msg, kwargs

logger = RequestIDAdapter(logging.getLogger(__name__), {})

class ErrorType(Enum):
    NETWORK = "network"
    TIMEOUT = "timeout"
    AUTH = "auth"
    SERVER = "server"
    UNKNOWN = "unknown"

class HealthCheckError(Exception):
    """Base exception for health check operations"""
    def __init__(self, message: str, provider_name: str = None, error_type: ErrorType = ErrorType.UNKNOWN):
        super().__init__(message)
        self.provider_name = provider_name
        self.error_type = error_type

class ProviderConfigError(Exception):
    """Exception for provider configuration issues"""
    pass

class CircuitBreakerOpenError(HealthCheckError):
    """Exception when circuit breaker is open"""
    def __init__(self, provider_name: str):
        super().__init__(f"Circuit breaker is open for provider {provider_name}", provider_name, ErrorType.UNKNOWN)

def classify_error(error: Exception) -> ErrorType:
    """Classify the type of error for better handling"""
    if isinstance(error, httpx.ConnectError):
        return ErrorType.NETWORK
    elif isinstance(error, httpx.TimeoutException):
        return ErrorType.TIMEOUT
    elif isinstance(error, httpx.HTTPStatusError):
        if error.response.status_code in (401, 403):
            return ErrorType.AUTH
        elif error.response.status_code >= 500:
            return ErrorType.SERVER
        else:
            return ErrorType.UNKNOWN
    else:
        return ErrorType.UNKNOWN

# Prometheus metrics
health_check_total = Counter('health_worker_health_check_total', 'Total health checks', ['provider', 'status'])
health_check_duration = Histogram('health_worker_health_check_duration_seconds', 'Health check duration', ['provider'])
health_check_response_time = Histogram('health_worker_response_time', 'Response time by status', ['provider', 'status'])
circuit_breaker_state = Gauge('health_worker_circuit_breaker_state', 'Circuit breaker state (0=closed, 1=open, 2=half-open)', ['provider'])
active_health_checks = Gauge('health_worker_active_health_checks', 'Number of active health checks')
error_total = Counter('health_worker_errors_total', 'Total errors by type', ['provider', 'error_type'])
retry_total = Counter('health_worker_retry_total', 'Total retry attempts', ['provider', 'attempt'])
logger.info("Prometheus metrics initialized")
semaphore_available = Gauge('health_worker_semaphore_available', 'Available semaphore slots')
health_check_cache_hits = Counter('health_worker_cache_hits_total', 'Cache hits for health checks', ['provider'])
health_check_cache_misses = Counter('health_worker_cache_misses_total', 'Cache misses for health checks', ['provider'])
class CircuitBreaker:
    """Simple circuit breaker implementation"""
    def __init__(self, provider_name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        circuit_breaker_state.labels(provider_name).set(0)

    def can_attempt(self) -> bool:
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self.last_failure_time is not None and time.monotonic() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                circuit_breaker_state.labels(self.provider_name).set(2)
                return True
            return False
        elif self.state == "half-open":
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
        circuit_breaker_state.labels(self.provider_name).set(0)

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            circuit_breaker_state.labels(self.provider_name).set(1)

async def retry_with_backoff(func, *args, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, **kwargs):
    """Retry function with exponential backoff and metrics"""
    delay = base_delay
    last_exception = None
    provider_name = args[0] if args else "unknown"

    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 0:  # If we succeeded after retries
                retry_total.labels(provider_name, str(attempt)).inc()
            return result
        except Exception as e:
            last_exception = e
            error_type = classify_error(e)

            # Don't retry for auth errors
            if error_type == ErrorType.AUTH:
                raise e

            if attempt < max_retries:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0.1, 1.0)
                sleep_time = min(delay * jitter, max_delay)
                retry_total.labels(provider_name, str(attempt + 1)).inc()
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {sleep_time:.2f}s",
                    extra={
                        'provider': provider_name,
                        'attempt': attempt + 1,
                        'error_type': error_type.value,
                        'retry_delay': sleep_time
                    }
                )
                await asyncio.sleep(sleep_time)
                delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"All {max_retries + 1} attempts failed for {func.__name__}: {e}",
                    extra={
                        'provider': provider_name,
                        'total_attempts': max_retries + 1,
                        'error_type': error_type.value
                    }
                )
                raise last_exception

# Initialize global variables
scheduler = AsyncIOScheduler()
provider_status: Dict[str, Any] = {}
semaphore = asyncio.Semaphore(10)
semaphore_available.set(10)
status_lock = asyncio.Lock()
circuit_breakers: Dict[str, CircuitBreaker] = {}

# Health check cache
health_check_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = int(os.getenv("HEALTH_CHECK_CACHE_TTL", "30"))  # 30 seconds default

# Shared HTTP client for connection pooling
shared_client: Optional[httpx.AsyncClient] = None

def get_cached_health_check(provider_name: str) -> Optional[Dict[str, Any]]:
    """Get cached health check result if still valid"""
    if provider_name in health_check_cache:
        cached_result = health_check_cache[provider_name]
        cache_time = cached_result.get("cached_at", 0)
        if time.monotonic() - cache_time < CACHE_TTL_SECONDS:
            health_check_cache_hits.labels(provider_name).inc()
            return cached_result
        else:
            # Cache expired, remove it
            del health_check_cache[provider_name]
    health_check_cache_misses.labels(provider_name).inc()
    return None

def set_cached_health_check(provider_name: str, result: Dict[str, Any]) -> None:
    """Cache health check result"""
    result["cached_at"] = time.monotonic()
    health_check_cache[provider_name] = result

async def _perform_health_check(provider_name: str, base_url: str, models: list) -> Dict[str, Any]:
    """Internal function to perform the actual health check"""
    if shared_client is None:
        raise RuntimeError("Shared HTTP client not initialized")

    # Try to call the models endpoint (common health check) using shared client
    response = await shared_client.get(f"{base_url}/v1/models")
    if response.status_code == 200:
        return {
            "status": "healthy",
            "last_check": time.monotonic(),
            "models": models,
            "response_time": response.elapsed.total_seconds() * 1000  # ms
        }
    else:
        raise httpx.HTTPStatusError(
            f"HTTP {response.status_code}",
            request=response.request,
            response=response
        )

async def check_provider_health(provider_name: str, base_url: str, models: list) -> None:
    """Check health of a single provider with retry, circuit breaker, and caching"""
    active_health_checks.inc()
    semaphore_available.set(semaphore._value)

    async with semaphore:
        semaphore_available.set(semaphore._value)  # Update after acquire

        # Check cache first
        cached_result = get_cached_health_check(provider_name)
        if cached_result:
            async with status_lock:
                provider_status[provider_name] = cached_result
            logger.debug(f"Using cached result for provider {provider_name}")
            active_health_checks.dec()
            semaphore_available.set(semaphore._value)
            return

        # Get or create circuit breaker for this provider
        if provider_name not in circuit_breakers:
            circuit_breakers[provider_name] = CircuitBreaker(provider_name)

        cb = circuit_breakers[provider_name]

        health_check_total.labels(provider_name, 'attempt').inc()

        if not cb.can_attempt():
            error = CircuitBreakerOpenError(provider_name)
            health_check_total.labels(provider_name, 'failure').inc()
            error_total.labels(provider_name, 'circuit_breaker').inc()
            async with status_lock:
                provider_status[provider_name] = {
                    "status": "circuit_open",
                    "last_check": time.monotonic(),
                    "error": str(error),
                    "error_type": error.error_type.value,
                    "models": models
                }
            logger.warning(f"Provider {provider_name} circuit breaker is open, skipping check")
            active_health_checks.dec()
            semaphore_available.set(semaphore._value)
            return

        try:
            result = await retry_with_backoff(_perform_health_check, provider_name, base_url, models)
            health_check_duration.labels(provider_name).observe(result["response_time"] / 1000)
            health_check_response_time.labels(provider_name, 'success').observe(result["response_time"] / 1000)
            health_check_total.labels(provider_name, 'success').inc()

            # Cache the successful result
            set_cached_health_check(provider_name, result)

            async with status_lock:
                provider_status[provider_name] = result
            cb.record_success()
            logger.info(f"Provider {provider_name} is healthy")
        except Exception as e:
            error_type = classify_error(e)
            health_check_total.labels(provider_name, 'failure').inc()
            health_check_response_time.labels(provider_name, 'failure').observe(0)
            error_total.labels(provider_name, error_type.value).inc()
            cb.record_failure()

            health_check_error = HealthCheckError(
                f"Health check failed: {str(e)}",
                provider_name,
                error_type
            )

            async with status_lock:
                provider_status[provider_name] = {
                    "status": "unhealthy",
                    "last_check": time.monotonic(),
                    "error": str(health_check_error),
                    "error_type": error_type.value,
                    "models": models
                }
            logger.error(f"Provider {provider_name} health check failed: {e} (type: {error_type.value})")
            # Re-raise for proper propagation
            raise health_check_error
        finally:
            active_health_checks.dec()
            semaphore_available.set(semaphore._value)

async def perform_health_checks():
    """Perform health checks for all configured providers"""
    logger.info("Starting health checks for all providers")

    # Load provider configuration
    providers = load_provider_config()

    tasks = []
    for provider in providers:
        task = asyncio.create_task(
            check_provider_health(provider["name"], provider["base_url"], provider["models"])
        )
        tasks.append(task)

    # Wait for all checks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Log any exceptions that occurred
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            provider_name = providers[i]["name"]
            logger.error(f"Health check for {provider_name} raised exception: {result}")

    logger.info("Health checks completed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global shared_client

    logger.info(
        "Health Worker starting up",
        extra={
            'event': 'startup',
            'service': 'health-worker',
            'version': '1.0.0'
        }
    )

    # Configure connection limits from environment
    max_connections = int(os.getenv("HTTP_MAX_CONNECTIONS", "100"))
    max_keepalive = int(os.getenv("HTTP_MAX_KEEPALIVE", "20"))
    timeout = float(os.getenv("HTTP_TIMEOUT", "5.0"))

    # Create shared HTTP client with connection pooling
    limits = httpx.Limits(max_connections=max_connections, max_keepalive_connections=max_keepalive)
    shared_client = httpx.AsyncClient(limits=limits, timeout=timeout)
    logger.info(
        "Created shared HTTP client",
        extra={
            'max_connections': max_connections,
            'max_keepalive': max_keepalive,
            'timeout': timeout
        }
    )

    # Perform provider discovery
    logger.info("Performing provider discovery")
    await update_provider_config()
    logger.info("Provider discovery completed")

    # Perform initial health check
    logger.info("Performing initial health checks")
    await perform_health_checks()
    logger.info("Initial health checks completed")

    # Schedule periodic health checks (every 60 seconds)
    check_interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
    scheduler.add_job(
        perform_health_checks,
        trigger=IntervalTrigger(seconds=check_interval),
        id="health_check_job",
        name="Periodic Health Check"
    )

    # Schedule periodic provider discovery (every 5 minutes)
    discovery_interval = int(os.getenv("PROVIDER_DISCOVERY_INTERVAL", "300"))
    scheduler.add_job(
        update_provider_config,
        trigger=IntervalTrigger(seconds=discovery_interval),
        id="provider_discovery_job",
        name="Provider Discovery"
    )

    # Start the scheduler
    scheduler.start()
    logger.info(
        "Scheduler started",
        extra={
            'check_interval': check_interval,
            'job_id': 'health_check_job'
        }
    )

    yield

    # Shutdown
    logger.info(
        "Health Worker shutting down",
        extra={
            'event': 'shutdown',
            'service': 'health-worker'
        }
    )

    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown completed")

    # Close shared HTTP client
    if shared_client:
        await shared_client.aclose()
        logger.info("Shared HTTP client closed")

app = FastAPI(
    title="Health Worker Service",
    description="Service for monitoring provider health status",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(PerformanceMiddleware)
app.add_middleware(RequestIDMiddleware)

@app.get("/status")
async def get_provider_status():
    """Get the current status of all providers"""
    return {
        "providers": provider_status,
        "timestamp": time.monotonic(),
        "total_providers": len(provider_status),
        "healthy_providers": sum(1 for p in provider_status.values() if p["status"] == "healthy"),
        "unhealthy_providers": sum(1 for p in provider_status.values() if p["status"] == "unhealthy")
    }

@app.get("/status/{provider_name}")
async def get_provider_status_detail(provider_name: str):
    """Get detailed status for a specific provider"""
    if provider_name not in provider_status:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    status = provider_status[provider_name]
    circuit_breaker = circuit_breakers.get(provider_name)

    return {
        "provider": provider_name,
        **status,
        "circuit_breaker": {
            "state": circuit_breaker.state if circuit_breaker else "not_initialized",
            "failure_count": circuit_breaker.failure_count if circuit_breaker else 0,
            "last_failure_time": circuit_breaker.last_failure_time if circuit_breaker else None
        } if circuit_breaker else None
    }

@app.post("/check")
async def trigger_health_check():
    """Manually trigger a health check"""
    await perform_health_checks()
    return {"message": "Health check triggered", "timestamp": time.monotonic()}

@app.post("/discover")
async def trigger_provider_discovery():
    """Manually trigger provider discovery"""
    await update_provider_config()
    return {"message": "Provider discovery triggered", "timestamp": time.monotonic()}

@app.post("/cache/clear")
async def clear_health_cache():
    """Clear the health check cache"""
    health_check_cache.clear()
    return {"message": "Health check cache cleared", "timestamp": time.monotonic()}

@app.get("/health")
async def health_check():
    """Health check endpoint for the health worker itself"""
    # Check if shared client is available
    client_healthy = shared_client is not None

    # Check scheduler status
    scheduler_healthy = scheduler.running if scheduler else False

    # Overall health
    overall_status = "healthy" if client_healthy and scheduler_healthy else "unhealthy"

    logger.info(
        f"Health check performed",
        extra={
            'overall_status': overall_status,
            'client_healthy': client_healthy,
            'scheduler_healthy': scheduler_healthy,
            'active_checks': active_health_checks._value.get((), 0) if hasattr(active_health_checks, '_value') else 0
        }
    )

    return {
        "status": overall_status,
        "service": "health-worker",
        "timestamp": time.monotonic(),
        "components": {
            "http_client": "healthy" if client_healthy else "unhealthy",
            "scheduler": "healthy" if scheduler_healthy else "unhealthy",
            "active_health_checks": active_health_checks._value.get((), 0) if hasattr(active_health_checks, '_value') else 0
        },
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Health Worker Service",
        "version": "1.0.0",
        "description": "Monitors provider health status with periodic checks, caching, and auto-discovery",
        "features": [
            "Circuit breaker pattern",
            "Health check caching",
            "Provider auto-discovery",
            "Comprehensive metrics",
            "Structured logging"
        ],
        "endpoints": {
            "GET /status": "Get status of all providers",
            "GET /status/{provider}": "Get status of specific provider",
            "POST /check": "Trigger manual health check",
            "POST /discover": "Trigger manual provider discovery",
            "POST /cache/clear": "Clear health check cache",
            "GET /health": "Health check for this service",
            "GET /metrics": "Prometheus metrics endpoint"
        },
        "configuration": {
            "PROVIDER_CONFIG_FILE": "Path to JSON config file",
            "PROVIDER_CONFIG": "JSON config as environment variable",
            "HEALTH_CHECK_INTERVAL": "Health check interval in seconds (default: 60)",
            "HEALTH_CHECK_CACHE_TTL": "Cache TTL in seconds (default: 30)",
            "PROVIDER_DISCOVERY_INTERVAL": "Discovery interval in seconds (default: 300)",
            "PROVIDER_REGISTRY_URL": "URL for provider registry",
            "LOG_LEVEL": "Logging level (default: INFO)"
        }
    }

if __name__ == "__main__":
    import uvicorn

    # Graceful shutdown handling
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        logger.info(
            f"Received signal {signum}, initiating graceful shutdown",
            extra={'signal': signum}
        )
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Run the server
    try:
        logger.info(
            "Starting uvicorn server",
            extra={
                'host': '0.0.0.0',
                'port': 8002
            }
        )
        uvicorn.run(app, host="0.0.0.0", port=8002)
    except KeyboardInterrupt:
        logger.info("Server stopped by KeyboardInterrupt")
    except Exception as e:
        logger.error(
            f"Server error: {e}",
            extra={'error': str(e)}
        )
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")