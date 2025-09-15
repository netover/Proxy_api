"""
Circuit breaker implementation for LLM Proxy API
Prevents cascading failures when providers become unresponsive
"""

import asyncio
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Type

import redis.asyncio as redis
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Tripped, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_changes: int = 0
    last_state_change: Optional[float] = None
    total_downtime_seconds: float = 0.0


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open"""

    def __init__(self, breaker_name: str, retry_after: Optional[int] = None):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        message = f"Circuit breaker '{breaker_name}' is open"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)


class DistributedCircuitBreaker:
    """
    A distributed circuit breaker using Redis for state management.
    """
    def __init__(
        self,
        redis_client: redis.Redis,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.redis = redis_client
        self.name = service_name
        self.key = f"circuit_breaker:{service_name}"
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        logger.info(
            f"Distributed circuit breaker initialized for {self.name}",
            extra={'threshold': self.failure_threshold, 'timeout': self.recovery_timeout}
        )

    async def _get_state(self) -> Tuple[CircuitState, int]:
        """Gets the current state and failure count from Redis."""
        state_data = await self.redis.get(self.key)
        if not state_data:
            return CircuitState.CLOSED, 0

        state_str, failures, timestamp = json.loads(state_data)
        state = CircuitState(state_str)

        if state == CircuitState.OPEN and (time.time() - timestamp) > self.recovery_timeout:
            await self.redis.set(self.key, json.dumps([CircuitState.HALF_OPEN.value, 0, time.time()]))
            return CircuitState.HALF_OPEN, 0

        return state, int(failures)

    async def _record_success(self):
        """Records a success, resetting the breaker if it was half-open."""
        await self.redis.delete(self.key)
        logger.debug(f"Circuit breaker {self.name} reset to CLOSED after success.")

    async def _record_failure(self):
        """Records a failure and potentially opens the circuit."""
        # Use a transaction to safely increment the failure count
        pipe = self.redis.pipeline()
        pipe.get(self.key)
        state_data, = await pipe.execute()

        state, failures = CircuitState.CLOSED, 0
        if state_data:
            state_str, stored_failures, _ = json.loads(state_data)
            state, failures = CircuitState(state_str), int(stored_failures)

        failures += 1

        if state == CircuitState.HALF_OPEN or failures >= self.failure_threshold:
            # Open the circuit
            new_state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} is now OPEN.")
        else:
            new_state = CircuitState.CLOSED

        await self.redis.set(self.key, json.dumps([new_state.value, failures, time.time()]))

    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        state, failures = await self._get_state()

        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenException(self.name)

        if state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker {self.name} is HALF-OPEN, testing with one request.")

        try:
            result = await func(*args, **kwargs)
            if state == CircuitState.HALF_OPEN:
                await self._record_success()
            return result
        except self.expected_exceptions as e:
            await self._record_failure()
            raise e


# Global circuit breaker registry
_circuit_breakers: Dict[str, DistributedCircuitBreaker] = {}

from src.core.unified_config import config_manager

# This would ideally come from a shared Redis client module
# For now, we'll create a placeholder function
import os

def get_redis_client() -> redis.Redis:
    """Placeholder for a global Redis client."""
    # In a real app, this would connect to Redis using config values
    try:
        # Use from_url for synchronous client
        return redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    except Exception as e:
        logger.error(f"Could not create Redis client for circuit breaker: {e}")
        # Return a mock/dummy client or raise an error if Redis is essential
        raise

def get_circuit_breaker(
    name: str,
    failure_threshold: Optional[int] = None,
    recovery_timeout: Optional[int] = None,
    expected_exception: Tuple[Type[Exception], ...] = (Exception,)
) -> DistributedCircuitBreaker:
    """Get or create a distributed circuit breaker."""
    if name not in _circuit_breakers:
        config = config_manager.load_config()
        threshold = failure_threshold or config.settings.circuit_breaker_threshold
        timeout = recovery_timeout or config.settings.circuit_breaker_timeout

        redis_client = get_redis_client()

        _circuit_breakers[name] = DistributedCircuitBreaker(
            redis_client=redis_client,
            service_name=name,
            failure_threshold=threshold,
            recovery_timeout=timeout,
            expected_exceptions=expected_exception
        )
    return _circuit_breakers[name]

def get_all_circuit_breakers() -> Dict[str, DistributedCircuitBreaker]:
    """Get all circuit breakers"""
    return _circuit_breakers.copy()

# get_circuit_breaker_metrics would need to be adapted to fetch metrics from Redis
# This is left as a future exercise.
def get_circuit_breaker_metrics() -> Dict[str, Dict[str, Any]]:
    """Get metrics for all circuit breakers (placeholder)."""
    return {name: {} for name in _circuit_breakers.keys()}

async def reset_all_circuit_breakers():
    """Reset all circuit breakers to closed state"""
    for breaker in _circuit_breakers.values():
        async with breaker.lock:
            await breaker._change_state(CircuitState.CLOSED)
            breaker.failure_count = 0
            breaker.half_open_success_count = 0

    logger.info("All circuit breakers reset to closed state")
