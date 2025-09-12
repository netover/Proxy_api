"""
Circuit Breaker Pool for LLM Proxy API
Individual circuit breakers per provider with adaptive timeouts
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .circuit_breaker import (CircuitBreakerOpenException,
                              ProductionCircuitBreaker)
from .logging import ContextualLogger
from .provider_discovery import provider_discovery

logger = ContextualLogger(__name__)


class TimeoutStrategy(Enum):
    """Timeout adaptation strategies"""
    FIXED = "fixed"                          # Fixed timeout values
    ADAPTIVE = "adaptive"                     # Adaptive based on provider performance
    QUANTILE = "quantile"                     # Based on response time quantiles
    PREDICTIVE = "predictive"                 # Predictive based on historical data


@dataclass
class AdaptiveTimeoutConfig:
    """Configuration for adaptive timeouts"""
    base_timeout: float = 30.0               # Base timeout in seconds
    min_timeout: float = 5.0                 # Minimum allowed timeout
    max_timeout: float = 120.0               # Maximum allowed timeout
    adaptation_factor: float = 0.1           # How aggressively to adapt (0.1 = 10%)
    quantile_threshold: float = 0.95         # Quantile for timeout calculation
    history_window: int = 100                # Number of requests to keep in history
    strategy: TimeoutStrategy = TimeoutStrategy.ADAPTIVE


@dataclass
class ProviderCircuitBreaker:
    """Circuit breaker configuration for a specific provider"""
    provider_name: str
    circuit_breaker: ProductionCircuitBreaker
    adaptive_config: AdaptiveTimeoutConfig
    request_history: List[float] = field(default_factory=list)
    last_adaptation: float = 0.0
    current_timeout: float = 30.0

    def __post_init__(self):
        self.current_timeout = self.adaptive_config.base_timeout


class CircuitBreakerPool:
    """
    Advanced circuit breaker pool with individual breakers per provider
    Features adaptive timeouts and performance-based configuration
    """

    def __init__(self):
        self._provider_breakers: Dict[str, ProviderCircuitBreaker] = {}
        self._adaptation_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Default configuration
        self._default_config = AdaptiveTimeoutConfig()
        self._adaptation_interval = 60  # Adapt every 60 seconds

        # Performance tracking
        self._pool_metrics = {
            "total_providers": 0,
            "active_breakers": 0,
            "tripped_breakers": 0,
            "adaptation_cycles": 0
        }

        logger.info("Circuit Breaker Pool initialized")

    async def get_provider_breaker(
        self,
        provider_name: str,
        config: Optional[AdaptiveTimeoutConfig] = None
    ) -> ProviderCircuitBreaker:
        """
        Get or create a circuit breaker for a provider

        Args:
            provider_name: Name of the provider
            config: Optional adaptive timeout configuration

        Returns:
            ProviderCircuitBreaker instance
        """
        if provider_name not in self._provider_breakers:
            config = config or self._default_config

            # Create circuit breaker
            circuit_breaker = ProductionCircuitBreaker(
                name=provider_name,
                failure_threshold=5,  # Configurable via unified config
                recovery_timeout=60,
                adaptive_thresholds=True
            )

            # Create provider breaker wrapper
            provider_breaker = ProviderCircuitBreaker(
                provider_name=provider_name,
                circuit_breaker=circuit_breaker,
                adaptive_config=config,
                current_timeout=config.base_timeout
            )

            self._provider_breakers[provider_name] = provider_breaker
            self._pool_metrics["total_providers"] += 1
            self._pool_metrics["active_breakers"] += 1

            logger.info(
                f"Created circuit breaker for provider: {provider_name}",
                extra={
                    'base_timeout': config.base_timeout,
                    'strategy': config.strategy.value
                }
            )

        return self._provider_breakers[provider_name]

    async def execute_with_breaker(
        self,
        provider_name: str,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with the provider's circuit breaker protection

        Args:
            provider_name: Name of the provider
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit breaker is open
        """
        provider_breaker = await self.get_provider_breaker(provider_name)
        breaker = provider_breaker.circuit_breaker

        start_time = time.time()

        try:
            # Execute with circuit breaker protection
            result = await breaker.execute(func, *args, **kwargs)
            execution_time = time.time() - start_time

            # Record successful execution
            await self._record_execution(provider_name, True, execution_time)

            return result

        except CircuitBreakerOpenException:
            # Circuit breaker is open
            self._pool_metrics["tripped_breakers"] += 1
            raise

        except Exception as e:
            # Record failed execution
            execution_time = time.time() - start_time
            await self._record_execution(provider_name, False, execution_time)
            raise

    async def _record_execution(
        self,
        provider_name: str,
        success: bool,
        execution_time: float
    ):
        """Record execution result for adaptive timeout calculation"""
        if provider_name not in self._provider_breakers:
            return

        provider_breaker = self._provider_breakers[provider_name]

        # Add to request history
        provider_breaker.request_history.append(execution_time)

        # Maintain history window
        if len(provider_breaker.request_history) > provider_breaker.adaptive_config.history_window:
            provider_breaker.request_history.pop(0)

        # Record in provider discovery service
        await provider_discovery.record_request_result(
            provider_name, success, execution_time * 1000  # Convert to ms
        )

    def get_provider_timeout(self, provider_name: str) -> float:
        """Get the current adaptive timeout for a provider"""
        if provider_name not in self._provider_breakers:
            return self._default_config.base_timeout

        return self._provider_breakers[provider_name].current_timeout

    async def adapt_provider_timeout(self, provider_name: str):
        """Adapt the timeout for a specific provider based on performance"""
        if provider_name not in self._provider_breakers:
            return

        provider_breaker = self._provider_breakers[provider_name]
        config = provider_breaker.adaptive_config
        history = provider_breaker.request_history

        if len(history) < 10:  # Need minimum history for adaptation
            return

        try:
            if config.strategy == TimeoutStrategy.ADAPTIVE:
                await self._adapt_adaptive_timeout(provider_breaker)
            elif config.strategy == TimeoutStrategy.QUANTILE:
                await self._adapt_quantile_timeout(provider_breaker)
            elif config.strategy == TimeoutStrategy.PREDICTIVE:
                await self._adapt_predictive_timeout(provider_breaker)

            provider_breaker.last_adaptation = time.time()

        except Exception as e:
            logger.warning(f"Failed to adapt timeout for {provider_name}: {e}")

    async def _adapt_adaptive_timeout(self, provider_breaker: ProviderCircuitBreaker):
        """Adaptive timeout based on recent performance"""
        config = provider_breaker.adaptive_config
        history = provider_breaker.request_history[-20:]  # Last 20 requests

        if not history:
            return

        # Calculate recent average
        recent_avg = sum(history) / len(history)

        # Adapt timeout based on performance
        if recent_avg < config.base_timeout * 0.5:
            # Very fast responses - can reduce timeout
            new_timeout = max(
                config.min_timeout,
                provider_breaker.current_timeout * (1 - config.adaptation_factor)
            )
        elif recent_avg > config.base_timeout * 1.5:
            # Slow responses - increase timeout
            new_timeout = min(
                config.max_timeout,
                provider_breaker.current_timeout * (1 + config.adaptation_factor)
            )
        else:
            # Stable performance - slight adjustment toward base
            if provider_breaker.current_timeout > config.base_timeout:
                new_timeout = max(
                    config.base_timeout,
                    provider_breaker.current_timeout * (1 - config.adaptation_factor * 0.5)
                )
            else:
                new_timeout = min(
                    config.base_timeout,
                    provider_breaker.current_timeout * (1 + config.adaptation_factor * 0.5)
                )

        if abs(new_timeout - provider_breaker.current_timeout) > 0.1:  # Only log significant changes
            logger.info(
                f"Adapted timeout for {provider_breaker.provider_name}",
                extra={
                    'old_timeout': round(provider_breaker.current_timeout, 2),
                    'new_timeout': round(new_timeout, 2),
                    'recent_avg': round(recent_avg, 2)
                }
            )

        provider_breaker.current_timeout = new_timeout

    async def _adapt_quantile_timeout(self, provider_breaker: ProviderCircuitBreaker):
        """Quantile-based timeout adaptation"""
        config = provider_breaker.adaptive_config
        history = sorted(provider_breaker.request_history)

        if len(history) < 10:
            return

        # Calculate quantile
        quantile_idx = int(len(history) * config.quantile_threshold)
        quantile_value = history[min(quantile_idx, len(history) - 1)]

        # Add safety margin
        new_timeout = min(
            config.max_timeout,
            max(config.min_timeout, quantile_value * 1.5)
        )

        provider_breaker.current_timeout = new_timeout

    async def _adapt_predictive_timeout(self, provider_breaker: ProviderCircuitBreaker):
        """Predictive timeout based on trend analysis"""
        # This would implement more sophisticated prediction
        # For now, fall back to adaptive strategy
        await self._adapt_adaptive_timeout(provider_breaker)

    async def start_adaptation_loop(self):
        """Start the timeout adaptation loop"""
        if self._adaptation_task and not self._adaptation_task.done():
            return

        self._adaptation_task = asyncio.create_task(self._adaptation_loop())
        logger.info("Started circuit breaker adaptation loop")

    async def stop_adaptation_loop(self):
        """Stop the timeout adaptation loop"""
        self._shutdown_event.set()

        if self._adaptation_task:
            self._adaptation_task.cancel()
            try:
                await self._adaptation_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped circuit breaker adaptation loop")

    async def _adaptation_loop(self):
        """Background loop for timeout adaptation"""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_adaptation_cycle()
                self._pool_metrics["adaptation_cycles"] += 1

                # Wait for next adaptation cycle or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self._adaptation_interval
                )

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Circuit breaker adaptation error: {e}")
                await asyncio.sleep(self._adaptation_interval)

    async def _perform_adaptation_cycle(self):
        """Perform one cycle of timeout adaptation for all providers"""
        for provider_name in list(self._provider_breakers.keys()):
            try:
                await self.adapt_provider_timeout(provider_name)
            except Exception as e:
                logger.warning(f"Failed to adapt timeout for {provider_name}: {e}")

    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pool metrics"""
        metrics = dict(self._pool_metrics)

        # Add per-provider metrics
        provider_metrics = {}
        for provider_name, provider_breaker in self._provider_breakers.items():
            breaker_metrics = provider_breaker.circuit_breaker.get_metrics()

            provider_metrics[provider_name] = {
                "circuit_state": breaker_metrics["state"],
                "failure_count": breaker_metrics["current_failure_count"],
                "success_rate": breaker_metrics["success_rate"],
                "current_timeout": round(provider_breaker.current_timeout, 2),
                "request_history_size": len(provider_breaker.request_history),
                "last_adaptation": provider_breaker.last_adaptation,
                "adaptive_strategy": provider_breaker.adaptive_config.strategy.value
            }

        metrics["providers"] = provider_metrics
        return metrics

    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """Get detailed status for a specific provider"""
        if provider_name not in self._provider_breakers:
            return {"status": "not_found"}

        provider_breaker = self._provider_breakers[provider_name]
        breaker_metrics = provider_breaker.circuit_breaker.get_metrics()
        health = provider_discovery.get_provider_health(provider_name)

        return {
            "provider_name": provider_name,
            "circuit_state": breaker_metrics["state"],
            "health_status": health.value,
            "current_timeout": round(provider_breaker.current_timeout, 2),
            "failure_count": breaker_metrics["current_failure_count"],
            "success_rate": breaker_metrics["success_rate"],
            "total_requests": breaker_metrics["total_requests"],
            "last_failure": breaker_metrics["last_failure_time"],
            "adaptive_strategy": provider_breaker.adaptive_config.strategy.value,
            "request_history_size": len(provider_breaker.request_history)
        }

    def get_all_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all providers"""
        return {
            provider_name: self.get_provider_status(provider_name)
            for provider_name in self._provider_breakers.keys()
        }

    async def reset_provider_breaker(self, provider_name: str):
        """Reset a provider's circuit breaker"""
        if provider_name in self._provider_breakers:
            provider_breaker = self._provider_breakers[provider_name]

            # Reset circuit breaker state
            async with provider_breaker.circuit_breaker.lock:
                from .circuit_breaker import CircuitState
                await provider_breaker.circuit_breaker._change_state(CircuitState.CLOSED)
                provider_breaker.circuit_breaker.failure_count = 0
                provider_breaker.circuit_breaker.half_open_success_count = 0

            # Reset adaptive timeout
            provider_breaker.current_timeout = provider_breaker.adaptive_config.base_timeout
            provider_breaker.request_history.clear()
            provider_breaker.last_adaptation = time.time()

            logger.info(f"Reset circuit breaker for provider: {provider_name}")

    async def shutdown(self):
        """Shutdown the circuit breaker pool"""
        logger.info("Shutting down Circuit Breaker Pool")

        await self.stop_adaptation_loop()

        # Reset all breakers
        for provider_breaker in self._provider_breakers.values():
            await self.reset_provider_breaker(provider_breaker.provider_name)

        self._provider_breakers.clear()
        logger.info("Circuit Breaker Pool shutdown complete")


# Global instance
circuit_breaker_pool = CircuitBreakerPool()