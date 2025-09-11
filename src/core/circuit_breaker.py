"""
Circuit breaker implementation for LLM Proxy API
Prevents cascading failures when providers become unresponsive
"""

import time
import asyncio
from enum import Enum
from typing import Dict, Any, Callable, Awaitable, Optional, Union, Tuple, Type
from dataclasses import dataclass
from src.core.logging import ContextualLogger
import logging

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


class ProductionCircuitBreaker:
    """
    Production-ready circuit breaker with:
    - Advanced failure detection
    - Success rate tracking
    - Adaptive thresholds
    - Comprehensive metrics
    - Memory-efficient operation
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        success_threshold: int = 3,  # Successes needed to close from half-open
        min_failure_threshold: int = 3,
        max_failure_threshold: int = 20,
        adaptive_thresholds: bool = True
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.success_threshold = success_threshold
        self.min_failure_threshold = min_failure_threshold
        self.max_failure_threshold = max_failure_threshold
        self.adaptive_thresholds = adaptive_thresholds

        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
        self.half_open_success_count = 0

        # Thread safety
        self.lock = asyncio.Lock()

        # Metrics
        self.metrics = CircuitBreakerMetrics()

        # EMA variables
        self.ema_success_rate: Optional[float] = None
        self.ema_alpha = 0.1  # Smoothing factor for EMA

        logger.info(
            f"Circuit breaker initialized for {name}",
            extra={
                'failure_threshold': failure_threshold,
                'recovery_timeout': recovery_timeout,
                'adaptive': adaptive_thresholds
            }
        )
    
    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is half-open"""
        return self.state == CircuitState.HALF_OPEN

    def get_success_rate(self) -> float:
        """Calculate success rate over recent requests"""
        total = len(self.success_rate_window)
        if total == 0:
            return 1.0

        successful = sum(1 for result in self.success_rate_window if result)
        return successful / total

    def _update_success_rate(self, success: bool):
        """Update EMA success rate"""
        if self.ema_success_rate is None:
            self.ema_success_rate = 1.0 if success else 0.0
        else:
            self.ema_success_rate = (self.ema_alpha * success) + (1 - self.ema_alpha) * self.ema_success_rate

    def _adapt_thresholds(self):
        """Adapt failure threshold based on success rate"""
        if not self.adaptive_thresholds:
            return

        success_rate = self.get_success_rate()

        if success_rate > 0.95:  # Very high success rate
            # Lower threshold - service is reliable
            self.failure_threshold = max(
                self.min_failure_threshold,
                self.failure_threshold - 1
            )
        elif success_rate < 0.80:  # Low success rate
            # Higher threshold - service is unreliable
            self.failure_threshold = min(
                self.max_failure_threshold,
                self.failure_threshold + 1
            )

    async def can_execute(self) -> bool:
        """Check if request can be executed"""
        async with self.lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if self.last_failure_time and \
                   (time.time() - self.last_failure_time) >= self.recovery_timeout:
                    await self._change_state(CircuitState.HALF_OPEN)
                    return True
                return False

            # HALF_OPEN state
            return True

    async def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state with metrics"""
        old_state = self.state
        self.state = new_state
        self.metrics.state_changes += 1
        self.metrics.last_state_change = time.time()

        if old_state == CircuitState.OPEN and new_state == CircuitState.CLOSED:
            # Calculate downtime
            if self.last_failure_time:
                downtime = time.time() - self.last_failure_time
                self.metrics.total_downtime_seconds += downtime

        logger.info(
            f"Circuit breaker {self.name} state changed",
            extra={
                'from_state': old_state.value,
                'to_state': new_state.value,
                'failure_count': self.failure_count,
                'success_rate': round(self.get_success_rate(), 3)
            }
        )

    async def on_success(self):
        """Handle successful request"""
        async with self.lock:
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.last_success_time = time.time()

            self._update_success_rate(True)

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_success_count += 1

                # Check if we have enough successes to close the circuit
                if self.half_open_success_count >= self.success_threshold:
                    await self._change_state(CircuitState.CLOSED)
                    self.half_open_success_count = 0
                    self.failure_count = 0
                    logger.info(
                        f"Circuit breaker {self.name} recovered",
                        extra={'success_threshold': self.success_threshold}
                    )
            else:
                # Reset failure count on success in closed state
                self.failure_count = 0

            self._adapt_thresholds()

    async def on_failure(self, exception: Exception):
        """Handle failed request"""
        async with self.lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.last_failure_time = time.time()

            self._update_success_rate(False)

            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state trips the circuit
                await self._change_state(CircuitState.OPEN)
                self.half_open_success_count = 0
                self.failure_count = 1
                logger.error(
                    f"Circuit breaker {self.name} tripped from HALF_OPEN",
                    extra={'error': str(exception)}
                )
            elif self.state == CircuitState.CLOSED:
                # Increment failure count
                self.failure_count += 1
                logger.warning(
                    f"Circuit breaker {self.name} failure",
                    extra={
                        'failure_count': self.failure_count,
                        'threshold': self.failure_threshold,
                        'error': str(exception)
                    }
                )

                # Check if we should trip the circuit
                if self.failure_count >= self.failure_threshold:
                    await self._change_state(CircuitState.OPEN)
                    logger.error(f"Circuit breaker {self.name} TRIPPED")

    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if not await self.can_execute():
            retry_after = None
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed < self.recovery_timeout:
                    retry_after = int(self.recovery_timeout - elapsed)

            self.metrics.rejected_requests += 1
            raise CircuitBreakerOpenException(self.name, retry_after)

        try:
            result = await func(*args, **kwargs)
            await self.on_success()
            return result
        except self.expected_exceptions as e:
            await self.on_failure(e)
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive circuit breaker metrics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout,
            'current_failure_count': self.failure_count,
            'success_rate': round(self.get_success_rate(), 4),
            'total_requests': self.metrics.total_requests,
            'successful_requests': self.metrics.successful_requests,
            'failed_requests': self.metrics.failed_requests,
            'rejected_requests': self.metrics.rejected_requests,
            'state_changes': self.metrics.state_changes,
            'total_downtime_seconds': round(self.metrics.total_downtime_seconds, 2),
            'last_failure_time': self.last_failure_time,
            'last_success_time': self.last_success_time,
            'adaptive_thresholds': self.adaptive_thresholds
        }

# Backward compatibility - keep old CircuitBreaker class
class CircuitBreaker:
    """Legacy circuit breaker implementation - kept for compatibility"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: tuple = (Exception,)
    ):
        # Create a production circuit breaker internally
        self._breaker = ProductionCircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exception,
            adaptive_thresholds=False  # Disable for backward compatibility
        )

    def is_closed(self) -> bool:
        return self._breaker.is_closed()

    def is_open(self) -> bool:
        return self._breaker.is_open()

    def is_half_open(self) -> bool:
        return self._breaker.is_half_open()

    async def can_execute(self) -> bool:
        return await self._breaker.can_execute()

    async def on_success(self):
        await self._breaker.on_success()

    async def on_failure(self, exception: Exception):
        await self._breaker.on_failure(exception)

    async def execute(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        return await self._breaker.execute(func, *args, **kwargs)

    def __getattr__(self, name):
        # Delegate other attributes to the production breaker
        return getattr(self._breaker, name)


# Global circuit breaker registry
_circuit_breakers: Dict[str, ProductionCircuitBreaker] = {}

from src.core.unified_config import config_manager

def get_circuit_breaker(
    name: str,
    failure_threshold: Optional[int] = None,
    recovery_timeout: Optional[int] = None,
    expected_exception: Tuple[Type[Exception], ...] = (Exception,)
) -> ProductionCircuitBreaker:
    """Get or create circuit breaker using unified config defaults"""
    config = config_manager.load_config()
    threshold = failure_threshold or config.settings.circuit_breaker_threshold
    timeout = recovery_timeout or config.settings.circuit_breaker_timeout

    if name not in _circuit_breakers:
        _circuit_breakers[name] = ProductionCircuitBreaker(
            name=name,
            failure_threshold=threshold,
            recovery_timeout=timeout,
            expected_exceptions=expected_exception
        )
        logger.info(
            f"Created circuit breaker for {name}",
            extra={'threshold': threshold, 'timeout': timeout}
        )
    return _circuit_breakers[name]

def get_all_circuit_breakers() -> Dict[str, ProductionCircuitBreaker]:
    """Get all circuit breakers"""
    return _circuit_breakers.copy()

def get_circuit_breaker_metrics() -> Dict[str, Dict[str, Any]]:
    """Get metrics for all circuit breakers"""
    return {
        name: breaker.get_metrics()
        for name, breaker in _circuit_breakers.items()
    }

async def reset_all_circuit_breakers():
    """Reset all circuit breakers to closed state"""
    for breaker in _circuit_breakers.values():
        async with breaker.lock:
            await breaker._change_state(CircuitState.CLOSED)
            breaker.failure_count = 0
            breaker.half_open_success_count = 0

    logger.info("All circuit breakers reset to closed state")
