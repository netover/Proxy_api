"""
Load Balancer & Priority Queue for LLM Proxy API
Intelligent provider selection with cost-aware routing
"""

import asyncio
import heapq
import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .logging import ContextualLogger
from .provider_discovery import ProviderHealth, provider_discovery

logger = ContextualLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""

    ROUND_ROBIN = "round_robin"  # Simple round-robin
    LEAST_CONNECTIONS = "least_connections"  # Least active connections
    WEIGHTED_RANDOM = "weighted_random"  # Weighted by performance
    LEAST_LATENCY = "least_latency"  # Fastest recent response
    COST_OPTIMIZED = "cost_optimized"  # Cost-aware routing
    ADAPTIVE = "adaptive"  # Adaptive based on real-time metrics


@dataclass(order=True)
class ProviderScore:
    """Priority queue element for provider selection"""

    score: float
    provider_name: str
    metrics: Dict[str, Any] = field(compare=False)

    def __post_init__(self):
        # Invert score for min-heap behavior (lower score = higher priority)
        pass


@dataclass
class ProviderLoadMetrics:
    """Real-time load metrics for a provider"""

    active_connections: int = 0
    total_requests: int = 0
    recent_latency_ms: float = 0.0
    error_rate: float = 0.0
    cost_per_token: float = 0.0
    last_request_time: float = 0.0
    performance_score: float = 1.0  # Higher is better

    def update_performance_score(self):
        """Update the performance score based on current metrics"""
        # Performance score combines multiple factors
        latency_factor = max(
            0.1, 1000.0 / max(self.recent_latency_ms, 100.0)
        )  # Higher for lower latency
        reliability_factor = max(
            0.1, 1.0 - self.error_rate
        )  # Higher for lower error rate
        load_factor = max(
            0.1, 10.0 / max(self.active_connections, 1)
        )  # Higher for lower load

        self.performance_score = (
            latency_factor * 0.4 + reliability_factor * 0.4 + load_factor * 0.2
        )


class LoadBalancer:
    """
    Advanced load balancer with intelligent provider selection
    Features cost-aware routing and performance-based prioritization
    """

    def __init__(self):
        self._provider_metrics: Dict[str, ProviderLoadMetrics] = {}
        self._round_robin_index: Dict[str, int] = defaultdict(int)
        self._active_requests: Dict[str, Set[str]] = defaultdict(
            set
        )  # provider -> set of request_ids

        # Cost configuration (could be loaded from external source)
        self._cost_config = {
            "openai": {"gpt-4": 0.03, "gpt-3.5-turbo": 0.002},
            "anthropic": {"claude-3-opus": 0.015, "claude-3-sonnet": 0.003},
            "perplexity": {"sonar-pro": 0.005},
            "grok": {"grok-1": 0.01},
            "blackbox": {"default": 0.001},
            "openrouter": {"default": 0.002},
            "cohere": {"command": 0.002},
        }

        # Performance tracking
        self._request_counter = 0
        self._load_update_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        logger.info("Load Balancer initialized")

    async def select_provider(
        self,
        model: str,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE,
        exclude_providers: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Select the best provider for a model using the specified strategy

        Args:
            model: The model name
            strategy: Load balancing strategy to use
            exclude_providers: List of providers to exclude

        Returns:
            Selected provider name or None if no suitable provider found
        """
        exclude_providers = exclude_providers or []

        # Get healthy providers for the model
        candidate_providers = provider_discovery.get_healthy_providers_for_model(model)

        # Filter out excluded providers
        available_providers = [
            p for p in candidate_providers if p not in exclude_providers
        ]

        if not available_providers:
            logger.warning(f"No available providers for model: {model}")
            return None

        try:
            if strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._select_round_robin(model, available_providers)
            elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._select_least_connections(available_providers)
            elif strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
                return self._select_weighted_random(available_providers)
            elif strategy == LoadBalancingStrategy.LEAST_LATENCY:
                return self._select_least_latency(available_providers)
            elif strategy == LoadBalancingStrategy.COST_OPTIMIZED:
                return self._select_cost_optimized(model, available_providers)
            elif strategy == LoadBalancingStrategy.ADAPTIVE:
                return self._select_adaptive(model, available_providers)
            else:
                logger.warning(
                    f"Unknown strategy: {strategy}, falling back to adaptive"
                )
                return self._select_adaptive(model, available_providers)

        except Exception as e:
            logger.error(f"Provider selection failed: {e}, using first available")
            return available_providers[0] if available_providers else None

    def _select_round_robin(self, model: str, providers: List[str]) -> str:
        """Simple round-robin selection"""
        model_key = f"rr_{model}"
        current_index = self._round_robin_index[model_key]
        selected_provider = providers[current_index % len(providers)]
        self._round_robin_index[model_key] = (current_index + 1) % len(providers)
        return selected_provider

    def _select_least_connections(self, providers: List[str]) -> str:
        """Select provider with least active connections"""
        provider_loads = [
            (self._get_provider_metric(p).active_connections, p) for p in providers
        ]
        return min(provider_loads)[1]

    def _select_weighted_random(self, providers: List[str]) -> str:
        """Weighted random selection based on performance"""
        weights = []
        for provider in providers:
            metrics = self._get_provider_metric(provider)
            # Weight by performance score and inverse of active connections
            weight = metrics.performance_score / max(metrics.active_connections + 1, 1)
            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(providers)

        normalized_weights = [w / total_weight for w in weights]

        # Weighted random selection
        r = random.random()
        cumulative = 0.0
        for i, weight in enumerate(normalized_weights):
            cumulative += weight
            if r <= cumulative:
                return providers[i]

        return providers[-1]  # Fallback

    def _select_least_latency(self, providers: List[str]) -> str:
        """Select provider with lowest recent latency"""
        provider_latencies = [
            (self._get_provider_metric(p).recent_latency_ms, p) for p in providers
        ]
        return min(provider_latencies)[1]

    def _select_cost_optimized(self, model: str, providers: List[str]) -> str:
        """Cost-optimized selection"""
        provider_costs = []
        for provider in providers:
            cost_per_token = self._get_cost_per_token(provider, model)
            metrics = self._get_provider_metric(provider)
            # Combine cost with performance penalty
            effective_cost = cost_per_token * (2.0 - metrics.performance_score)
            provider_costs.append((effective_cost, provider))

        return min(provider_costs)[1]

    def _select_adaptive(self, model: str, providers: List[str]) -> str:
        """Adaptive selection using comprehensive scoring"""
        scored_providers = []

        for provider in providers:
            metrics = self._get_provider_metric(provider)
            health = provider_discovery.get_provider_health(provider)

            # Base score from performance
            score = metrics.performance_score

            # Adjust based on health
            if health == ProviderHealth.EXCELLENT:
                score *= 1.2
            elif health == ProviderHealth.POOR:
                score *= 0.7
            elif health == ProviderHealth.UNHEALTHY:
                score *= 0.3

            # Penalize high load
            load_penalty = min(metrics.active_connections / 10.0, 0.5)
            score *= 1.0 - load_penalty

            # Cost consideration (slight preference for cheaper providers)
            cost_per_token = self._get_cost_per_token(provider, model)
            cost_factor = min(cost_per_token / 0.01, 2.0)  # Cap at 2x penalty
            score *= 1.0 / cost_factor

            scored_providers.append(ProviderScore(-score, provider, {"score": score}))

        # Use priority queue to get the best
        heapq.heapify(scored_providers)
        return heapq.heappop(scored_providers).provider_name

    def _get_provider_metric(self, provider_name: str) -> ProviderLoadMetrics:
        """Get or create load metrics for a provider"""
        if provider_name not in self._provider_metrics:
            self._provider_metrics[provider_name] = ProviderLoadMetrics()

            # Initialize cost per token
            self._update_provider_cost(provider_name)

        return self._provider_metrics[provider_name]

    def _get_cost_per_token(self, provider_name: str, model: str) -> float:
        """Get cost per token for a provider/model combination"""
        metrics = self._get_provider_metric(provider_name)

        if metrics.cost_per_token > 0:
            return metrics.cost_per_token

        # Fallback to default costs
        provider_costs = self._cost_config.get(provider_name.lower(), {})
        return provider_costs.get(model, provider_costs.get("default", 0.002))

    def _update_provider_cost(self, provider_name: str):
        """Update cost information for a provider"""
        # In a real implementation, this would fetch from a cost API
        # For now, use static configuration

    async def record_request_start(self, provider_name: str, request_id: str):
        """Record the start of a request"""
        self._active_requests[provider_name].add(request_id)
        metrics = self._get_provider_metric(provider_name)
        metrics.active_connections = len(self._active_requests[provider_name])
        metrics.last_request_time = time.time()

    async def record_request_complete(
        self,
        provider_name: str,
        request_id: str,
        success: bool,
        latency_ms: float,
    ):
        """Record the completion of a request"""
        self._active_requests[provider_name].discard(request_id)

        metrics = self._get_provider_metric(provider_name)
        metrics.active_connections = len(self._active_requests[provider_name])
        metrics.total_requests += 1

        if success:
            # Update rolling average latency
            alpha = 0.1  # Smoothing factor
            metrics.recent_latency_ms = (
                alpha * latency_ms + (1 - alpha) * metrics.recent_latency_ms
            )

            # Update error rate (decay over time)
            metrics.error_rate *= 0.99
        else:
            metrics.error_rate = min(1.0, metrics.error_rate + 0.01)

        # Update performance score
        metrics.update_performance_score()

    def get_provider_queue_depth(self, provider_name: str) -> int:
        """Get the current queue depth for a provider"""
        return len(self._active_requests[provider_name])

    def get_load_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get load distribution across all providers"""
        distribution = {}

        for provider_name, metrics in self._provider_metrics.items():
            distribution[provider_name] = {
                "active_connections": metrics.active_connections,
                "total_requests": metrics.total_requests,
                "recent_latency_ms": round(metrics.recent_latency_ms, 2),
                "error_rate": round(metrics.error_rate, 4),
                "performance_score": round(metrics.performance_score, 3),
                "cost_per_token": metrics.cost_per_token,
                "last_request_time": metrics.last_request_time,
            }

        return distribution

    def get_optimal_provider_count(self, model: str) -> int:
        """Determine optimal number of providers for parallel execution"""
        available_providers = provider_discovery.get_healthy_providers_for_model(model)

        if len(available_providers) <= 2:
            return len(available_providers)  # Use all available

        # Analyze performance diversity
        performance_scores = [
            self._get_provider_metric(p).performance_score for p in available_providers
        ]

        # Calculate coefficient of variation
        if performance_scores:
            mean_score = sum(performance_scores) / len(performance_scores)
            variance = sum((s - mean_score) ** 2 for s in performance_scores) / len(
                performance_scores
            )
            cv = math.sqrt(variance) / max(mean_score, 0.1)

            # Higher variation suggests more providers for diversity
            optimal_count = min(len(available_providers), max(2, int(3 + cv * 2)))
            return optimal_count

        return min(len(available_providers), 3)  # Default to 3

    def prioritize_providers_for_parallel(
        self, model: str, max_providers: int = 5
    ) -> List[str]:
        """
        Prioritize providers for parallel execution
        Returns providers in order of preference for parallel requests
        """
        available_providers = provider_discovery.get_healthy_providers_for_model(model)

        if len(available_providers) <= max_providers:
            return available_providers

        # Score providers for parallel execution
        scored_providers = []
        for provider in available_providers:
            metrics = self._get_provider_metric(provider)
            provider_discovery.get_provider_health(provider)

            # Parallel score considers performance, load, and diversity
            base_score = metrics.performance_score
            load_penalty = metrics.active_connections / max(
                metrics.active_connections + 1, 1
            )
            diversity_bonus = 1.0  # Could be enhanced with provider diversity logic

            final_score = base_score * (1 - load_penalty) * diversity_bonus
            scored_providers.append((final_score, provider))

        # Sort by score descending and return top providers
        scored_providers.sort(reverse=True)
        return [p for _, p in scored_providers[:max_providers]]

    async def start_load_monitoring(self):
        """Start background load monitoring"""
        if self._load_update_task and not self._load_update_task.done():
            return

        self._load_update_task = asyncio.create_task(self._load_monitoring_loop())
        logger.info("Started load balancer monitoring")

    async def stop_load_monitoring(self):
        """Stop background load monitoring"""
        self._shutdown_event.set()

        if self._load_update_task:
            self._load_update_task.cancel()
            try:
                await self._load_update_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped load balancer monitoring")

    async def _load_monitoring_loop(self):
        """Background load monitoring loop"""
        while not self._shutdown_event.is_set():
            try:
                # Update provider costs periodically
                await self._update_all_provider_costs()

                # Clean up old active requests (safety mechanism)
                await self._cleanup_stale_requests()

                # Wait for next monitoring cycle or shutdown
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=30.0,  # Update every 30 seconds
                )

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Load monitoring error: {e}")
                await asyncio.sleep(30)

    async def _update_all_provider_costs(self):
        """Update cost information for all providers"""
        # In a real implementation, this would fetch current pricing
        # For now, this is a placeholder

    async def _cleanup_stale_requests(self):
        """Clean up stale request tracking"""
        time.time()
        stale_threshold = 300  # 5 minutes

        for provider_name in list(self._active_requests.keys()):
            request_ids = self._active_requests[provider_name]
            stale_requests = set()

            # In a real implementation, we'd track request start times
            # For now, just ensure we don't have unbounded growth
            if len(request_ids) > 1000:
                # Remove oldest requests (simplified cleanup)
                sorted_requests = sorted(request_ids)
                stale_requests = set(sorted_requests[: len(sorted_requests) // 2])

            for request_id in stale_requests:
                self._active_requests[provider_name].discard(request_id)
                metrics = self._get_provider_metric(provider_name)
                metrics.active_connections = len(self._active_requests[provider_name])

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            "timestamp": time.time(),
            "load_distribution": self.get_load_distribution(),
            "total_active_connections": sum(
                len(requests) for requests in self._active_requests.values()
            ),
            "providers_tracked": len(self._provider_metrics),
            "round_robin_indices": dict(self._round_robin_index),
        }

    async def shutdown(self):
        """Shutdown the load balancer"""
        logger.info("Shutting down Load Balancer")

        await self.stop_load_monitoring()

        # Clear all state
        self._provider_metrics.clear()
        self._round_robin_index.clear()
        self._active_requests.clear()

        logger.info("Load Balancer shutdown complete")


# Global instance
load_balancer = LoadBalancer()
