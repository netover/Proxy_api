"""
Telemetry module for OpenTelemetry integration.

This is a minimal implementation for testing purposes.
In production, this would be a full OpenTelemetry setup.
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Import metrics collector for integration
try:
    from .metrics import metrics_collector

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("Metrics collector not available for telemetry integration")

# Adaptive sampling configuration
ADAPTIVE_SAMPLING_ENABLED = True
DEFAULT_SAMPLING_RATE = 0.1  # 10% default


class TelemetryManager:
    """Simple telemetry manager for testing."""

    def __init__(self):
        self._is_configured = False
        self._tracer = None

    def configure(self, settings: Any) -> None:
        """Configure telemetry (mock implementation)."""
        self._is_configured = True
        logger.info("Telemetry configured (mock)")

    def get_tracer(self):
        """Get tracer (mock implementation)."""
        if not self._is_configured:
            raise RuntimeError("Telemetry not configured")
        return MockTracer()

    def create_span(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ):
        """Create a span (mock implementation)."""
        return MockSpan(name, attributes or {})

    def record_error(self, span, error: Exception) -> None:
        """Record error in span (mock implementation)."""
        if hasattr(span, "record_error"):
            span.record_error(error)

    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI (mock implementation)."""

    def instrument_httpx(self) -> None:
        """Instrument HTTPX (mock implementation)."""


class MockTracer:
    """Mock tracer for testing."""

    def start_as_current_span(self, name: str):
        return MockSpan(name)


class MockSpan:
    """Mock span for testing."""

    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.name = name
        self.attributes = attributes or {}
        self.status = MockStatus()

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        self.attributes.update(attributes)

    def record_error(self, error: Exception) -> None:
        self.status.status_code = "ERROR"
        self.attributes["error"] = str(error)

    def __enter__(self):
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.record_error(exc_val)

        # Always track request timestamp for volume monitoring
        if METRICS_AVAILABLE:
            try:
                # Track timestamp regardless of sampling
                metrics_collector._request_timestamps.append(time.time())
            except Exception as e:
                logger.debug(f"Failed to track request timestamp: {e}")

        # Record span completion in metrics if available and sampled
        if METRICS_AVAILABLE and hasattr(self, "_start_time"):
            # Check if this span should be sampled based on adaptive sampling
            should_sample = True
            if ADAPTIVE_SAMPLING_ENABLED and hasattr(
                metrics_collector, "sampling_rate"
            ):
                import random

                should_sample = (
                    random.random() < metrics_collector.sampling_rate
                )

            if should_sample:
                duration = time.time() - self._start_time
                success = exc_type is None

                # Extract provider and model info from span name if available
                provider_name = self.attributes.get("provider", "unknown")
                model_name = self.attributes.get("model")

                # Record in metrics collector
                try:
                    metrics_collector.record_request(
                        provider_name=provider_name,
                        success=success,
                        response_time=duration
                        * 1000,  # Convert to milliseconds
                        tokens=self.attributes.get("tokens", 0),
                        error_type=str(exc_val) if exc_val else None,
                        model_name=model_name,
                    )
                except Exception as e:
                    logger.debug(f"Failed to record telemetry metrics: {e}")


@contextmanager
def TracedSpan(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Context manager for traced spans."""
    span = MockSpan(name, attributes)
    try:
        yield span
    except Exception as e:
        span.record_error(e)
        raise
    finally:
        pass  # Could log span completion here


def traced(operation: str = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator for tracing functions."""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = operation or f"{func.__module__}.{func.__name__}"
            with TracedSpan(span_name, attributes) as span:
                span.set_attribute("function.async", True)
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    raise
                finally:
                    span.set_attribute(
                        "function.duration", time.time() - start_time
                    )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = operation or f"{func.__module__}.{func.__name__}"
            with TracedSpan(span_name, attributes) as span:
                span.set_attribute("function.async", False)
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    raise
                finally:
                    span.set_attribute(
                        "function.duration", time.time() - start_time
                    )

        if hasattr(func, "__call__"):
            # Check if it's a coroutine function
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return sync_wrapper

    return decorator


class MockStatus:
    """Mock status for spans."""

    def __init__(self):
        self.status_code = "OK"


# Global telemetry instance
telemetry = TelemetryManager()
