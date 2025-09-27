"""
Circuit breaker implementation for LLM Proxy API.
Prevents cascading failures when providers become unresponsive by using a distributed
state store in Redis, ensuring consistency across multiple instances.
"""

import json
import random
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Type

import redis
import redis.asyncio as aioredis
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class CircuitBreakerState(Enum):
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


class InMemoryCircuitBreaker:
    """A non-persistent, in-memory circuit breaker for fallback."""

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.state = CircuitBreakerState.CLOSED
        self.failures = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_calls = 0
        self.last_failure_time = 0

    async def _get_state(self) -> str:
        if (
            self.state == CircuitBreakerState.OPEN
            and (time.time() - self.last_failure_time) > self.recovery_timeout
        ):
            self.state = CircuitBreakerState.HALF_OPEN
        return self.state

    async def _record_success(self):
        self.failures = 0
        self.state = CircuitBreakerState.CLOSED

    async def _record_failure(self):
        self.failures += 1
        self.failure_count += 1
        self.total_calls += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.last_failure_time = time.time()

    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        state = await self._get_state()
        if state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenException(self.name)

        try:
            result = await func(*args, **kwargs)
            self.success_count += 1
            self.total_calls += 1
            if state == CircuitBreakerState.HALF_OPEN:
                await self._record_success()
            return result
        except self.expected_exceptions:
            await self._record_failure()
            raise

    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection (alias for call)."""
        return await self.call(func, *args, **kwargs)


class DistributedCircuitBreaker:
    """
    A robust distributed circuit breaker using Redis for atomic state management.
    This implementation is designed to be safe for use in multi-instance deployments.
    """

    def __init__(
        self,
        redis_client: aioredis.Redis,
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
        self.in_memory_state: Dict[str, Any] = {}

        logger.info(
            f"Distributed circuit breaker initialized for '{self.name}'",
            extra={
                "threshold": self.failure_threshold,
                "timeout": self.recovery_timeout,
            },
        )

    async def _get_state(self) -> Dict[str, Any]:
        """
        Retrieves the current state from Redis, with a fallback to in-memory state.
        """
        try:
            state_data = await self.redis.get(self.key)
            if not state_data:
                # No state in Redis, return default closed state
                return {
                    "state": CircuitBreakerState.CLOSED.value,
                    "failures": 0,
                    "timestamp": time.time(),
                }
            state = json.loads(state_data)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(
                f"Redis connection error in circuit breaker '{self.name}': {e}. "
                "Falling back to in-memory state."
            )
            # Use in-memory state as a fallback
            if not self.in_memory_state:
                self.in_memory_state = {
                    "state": CircuitBreakerState.CLOSED.value,
                    "failures": 0,
                    "timestamp": time.time(),
                }
            return self.in_memory_state

        state = json.loads(state_data)

        # Check for recovery timeout
        # Add jitter to recovery timeout to prevent thundering herd
        jitter = self.recovery_timeout * 0.1 * random.random()
        if (
            state["state"] == CircuitBreakerState.OPEN.value
            and (time.time() - state["timestamp"]) > (self.recovery_timeout + jitter)
        ):
            new_state = {
                "state": CircuitBreakerState.HALF_OPEN.value,
                "failures": 0,
                "timestamp": time.time(),
            }
            await self.redis.set(self.key, json.dumps(new_state))
            logger.info(f"Circuit breaker '{self.name}' moved to HALF-OPEN state.")
            return new_state

        return state

    async def _record_success(self):
        """Records a successful call, resetting the circuit if it was HALF_OPEN."""
        try:
            await self.redis.delete(self.key)
            logger.info(f"Circuit breaker '{self.name}' reset to CLOSED after success.")
            self.in_memory_state.clear()  # Clear in-memory state on success
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(
                f"Redis connection error while recording success for '{self.name}': {e}. "
                "State may be inconsistent."
            )

    async def _record_failure(self):
        """
        Records a failure atomically and opens the circuit if the threshold is met.
        Uses a Redis transaction (WATCH/MULTI/EXEC) to prevent race conditions.
        """
        try:
            pipeline = self.redis.pipeline()
            async with pipeline as pipe:
                while True:
                    try:
                        await pipe.watch(self.key)
                        state_data = await pipe.get(self.key)

                        state = {
                            "state": CircuitBreakerState.CLOSED.value,
                            "failures": 0,
                            "timestamp": time.time(),
                        }
                        if state_data:
                            state = json.loads(state_data)

                        failures = state.get("failures", 0) + 1

                        pipe.multi()
                        if (
                            state["state"] == CircuitBreakerState.HALF_OPEN.value
                            or failures >= self.failure_threshold
                        ):
                            new_state = {
                                "state": CircuitBreakerState.OPEN.value,
                                "failures": failures,
                                "timestamp": time.time(),
                            }
                            pipe.set(self.key, json.dumps(new_state))
                            logger.warning(
                                f"Circuit breaker '{self.name}' is now OPEN due to failure threshold."
                            )
                        else:
                            new_state = {
                                "state": CircuitBreakerState.CLOSED.value,
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
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(
                f"Redis connection error while recording failure for '{self.name}': {e}. "
                "Falling back to in-memory state."
            )
            # Update in-memory state
            self.in_memory_state["failures"] = self.in_memory_state.get("failures", 0) + 1
            if self.in_memory_state["failures"] >= self.failure_threshold:
                self.in_memory_state["state"] = CircuitState.OPEN.value

    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
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

        if state["state"] == CircuitBreakerState.OPEN.value:
            raise CircuitBreakerOpenException(self.name, self.recovery_timeout)

        if state["state"] == CircuitBreakerState.HALF_OPEN.value:
            logger.info(
                f"Circuit breaker '{self.name}' is HALF-OPEN, testing with one request."
            )

        try:
            result = await func(*args, **kwargs)
            if state["state"] == CircuitBreakerState.HALF_OPEN.value:
                await self._record_success()
            return result
        except self.expected_exceptions:
            await self._record_failure()
            raise

    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection (alias for call)."""
        return await self.call(func, *args, **kwargs)


# --- Global Circuit Breaker Management ---

_circuit_breakers: Dict[str, DistributedCircuitBreaker] = {}
_redis_client: Optional[aioredis.Redis] = None


async def initialize_circuit_breakers(redis_client: Optional[aioredis.Redis]):
    """
    Initializes the global Redis client for all circuit breakers.
    If the client is not available or fails to connect, it logs a warning
    and the system will use non-persistent circuit breakers.
    """
    global _redis_client
    if not redis_client:
        logger.warning("No Redis client provided. Circuit breakers will be non-persistent.")
        _redis_client = None
        return

    try:
        # Test the connection to Redis
        await redis_client.ping()
        _redis_client = redis_client
        logger.info("Circuit breaker module initialized with Redis client.")
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.error(f"Failed to connect to Redis for circuit breakers: {e}")
        logger.warning("Circuit breakers will be non-persistent.")
        _redis_client = None
    except Exception as e:
        logger.error(f"An unexpected error occurred during Redis initialization for circuit breakers: {e}")
        _redis_client = None


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
) -> DistributedCircuitBreaker | InMemoryCircuitBreaker:
    """
    Gets or creates a circuit breaker instance for a given service name.
    Returns a DistributedCircuitBreaker if Redis is available, otherwise
    an InMemoryCircuitBreaker.
    """
    global _redis_client
    if name not in _circuit_breakers:
        if _redis_client:
            _circuit_breakers[name] = DistributedCircuitBreaker(
                redis_client=_redis_client,
                service_name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        else:
            logger.warning(f"Creating in-memory circuit breaker for '{name}'.")
            _circuit_breakers[name] = InMemoryCircuitBreaker(
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


class CircuitBreaker:
    """Main circuit breaker class that wraps the in-memory implementation."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
        expected_exception: Optional[str] = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception

        # Use in-memory circuit breaker as the implementation
        self._impl = InMemoryCircuitBreaker(
            service_name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=(Exception,) if expected_exception is None else (Exception,)
        )

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self._impl.state

    @property
    def success_count(self) -> int:
        """Get success count."""
        return self._impl.success_count

    @property
    def failure_count(self) -> int:
        """Get failure count."""
        return self._impl.failure_count

    @property
    def total_calls(self) -> int:
        """Get total calls."""
        return self._impl.total_calls

    async def call(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """Execute function with circuit breaker protection."""
        return await self._impl.call(func)

    async def execute(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """Execute function with circuit breaker protection (alias for call)."""
        return await self.call(func)

    async def _get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_calls": self.total_calls,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


