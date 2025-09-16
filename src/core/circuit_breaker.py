"""
Circuit breaker implementation for LLM Proxy API.
Prevents cascading failures when providers become unresponsive by using a distributed
state store in Redis, ensuring consistency across multiple instances.
"""

import asyncio
import json
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Type

import redis.asyncio as redis
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class CircuitState(Enum):
    """Enumeration for circuit breaker states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Exception raised when the circuit breaker is open."""

    def __init__(self, breaker_name: str, retry_after: Optional[int] = None):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        message = f"Circuit breaker '{breaker_name}' is open"
        if retry_after:
            message += f". Retry after {retry_after} seconds."
        super().__init__(message)


class DistributedCircuitBreaker:
    """
    A robust distributed circuit breaker using Redis for atomic state management.
    This implementation is designed to be safe for use in multi-instance deployments.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        """
        Initializes the distributed circuit breaker.

        Args:
            redis_client: An active asynchronous Redis client instance.
            service_name: A unique name for the service this breaker protects.
            failure_threshold: The number of failures to tolerate before opening the circuit.
            recovery_timeout: The time in seconds to wait before moving from OPEN to HALF_OPEN.
            expected_exceptions: A tuple of exception types that should be considered failures.
        """
        self.redis = redis_client
        self.name = service_name
        self.key = f"circuit_breaker:{self.name}"
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        logger.info(
            f"Distributed circuit breaker initialized for '{self.name}'",
            extra={
                "threshold": self.failure_threshold,
                "timeout": self.recovery_timeout,
            },
        )

    async def _get_state(self) -> Dict[str, Any]:
        """Retrieves the current state from Redis."""
        state_data = await self.redis.get(self.key)
        if not state_data:
            return {
                "state": CircuitState.CLOSED.value,
                "failures": 0,
                "timestamp": time.time(),
            }

        state = json.loads(state_data)

        # Check for recovery timeout
        if (
            state["state"] == CircuitState.OPEN.value
            and (time.time() - state["timestamp"]) > self.recovery_timeout
        ):
            new_state = {
                "state": CircuitState.HALF_OPEN.value,
                "failures": 0,
                "timestamp": time.time(),
            }
            await self.redis.set(self.key, json.dumps(new_state))
            logger.info(
                f"Circuit breaker '{self.name}' moved to HALF-OPEN state."
            )
            return new_state

        return state

    async def _record_success(self):
        """Records a successful call, resetting the circuit if it was HALF_OPEN."""
        await self.redis.delete(self.key)
        logger.info(
            f"Circuit breaker '{self.name}' reset to CLOSED after success."
        )

    async def _record_failure(self):
        """
        Records a failure atomically and opens the circuit if the threshold is met.
        Uses a Redis transaction (WATCH/MULTI/EXEC) to prevent race conditions.
        """
        async with self.redis.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(self.key)
                    state_data = await pipe.get(self.key)

                    state = {
                        "state": CircuitState.CLOSED.value,
                        "failures": 0,
                        "timestamp": time.time(),
                    }
                    if state_data:
                        state = json.loads(state_data)

                    failures = state.get("failures", 0) + 1

                    pipe.multi()
                    if (
                        state["state"] == CircuitState.HALF_OPEN.value
                        or failures >= self.failure_threshold
                    ):
                        new_state = {
                            "state": CircuitState.OPEN.value,
                            "failures": failures,
                            "timestamp": time.time(),
                        }
                        pipe.set(self.key, json.dumps(new_state))
                        logger.warning(
                            f"Circuit breaker '{self.name}' is now OPEN due to failure threshold."
                        )
                    else:
                        new_state = {
                            "state": CircuitState.CLOSED.value,
                            "failures": failures,
                            "timestamp": time.time(),
                        }
                        pipe.set(self.key, json.dumps(new_state))

                    await pipe.execute()
                    break
                except redis.WatchError:
                    logger.debug(
                        f"WatchError on circuit breaker '{self.name}', retrying transaction."
                    )
                    continue

    async def call(
        self, func: Callable[..., Awaitable[Any]], *args, **kwargs
    ) -> Any:
        """
        Executes the given function with circuit breaker protection.

        Args:
            func: The asynchronous function to execute.

        Returns:
            The result of the function if successful.

        Raises:
            CircuitBreakerOpenException: If the circuit is open.
            The original exception: If the function fails.
        """
        state = await self._get_state()

        if state["state"] == CircuitState.OPEN.value:
            raise CircuitBreakerOpenException(self.name, self.recovery_timeout)

        if state["state"] == CircuitState.HALF_OPEN.value:
            logger.info(
                f"Circuit breaker '{self.name}' is HALF-OPEN, testing with one request."
            )

        try:
            result = await func(*args, **kwargs)
            if state["state"] == CircuitState.HALF_OPEN.value:
                await self._record_success()
            return result
        except self.expected_exceptions:
            await self._record_failure()
            raise


# --- Global Circuit Breaker Management ---

_circuit_breakers: Dict[str, DistributedCircuitBreaker] = {}
_redis_client: Optional[redis.Redis] = None


async def initialize_circuit_breakers(redis_client: redis.Redis):
    """Initializes the global Redis client for all circuit breakers."""
    global _redis_client
    _redis_client = redis_client
    logger.info("Circuit breaker module initialized with Redis client.")


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
) -> DistributedCircuitBreaker:
    """
    Gets or creates a distributed circuit breaker instance for a given service name.

    Requires `initialize_circuit_breakers` to be called first.
    """
    global _redis_client
    if _redis_client is None:
        raise RuntimeError(
            "Circuit breaker module not initialized. Call `initialize_circuit_breakers` first."
        )

    if name not in _circuit_breakers:
        _circuit_breakers[name] = DistributedCircuitBreaker(
            redis_client=_redis_client,
            service_name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _circuit_breakers[name]


async def get_all_breaker_states() -> Dict[str, Dict]:
    """Retrieves the current state of all registered circuit breakers from Redis."""
    states = {}
    for name, breaker in _circuit_breakers.items():
        states[name] = await breaker._get_state()
    return states
