
# Advanced Usage Scenarios - ProxyAPI

This guide covers advanced usage scenarios and techniques for getting the most out of ProxyAPI in complex production environments.

## Table of Contents

- [Custom Provider Integration](#custom-provider-integration)
- [Advanced Routing Strategies](#advanced-routing-strategies)
- [Intelligent Caching Patterns](#intelligent-caching-patterns)
- [Context Condensation Workflows](#context-condensation-workflows)
- [Chaos Engineering Scenarios](#chaos-engineering-scenarios)
- [Multi-Region Deployment](#multi-region-deployment)
- [Advanced Monitoring & Alerting](#advanced-monitoring--alerting)
- [Performance Optimization Techniques](#performance-optimization-techniques)
- [Security Hardening](#security-hardening)

## Custom Provider Integration

### Building a Custom Provider

```python
from src.providers.base import BaseProvider
from src.core.provider_factory import ProviderStatus
from typing import Dict, Any, List
import httpx

class CustomAIProvider(BaseProvider):
    """Example custom AI provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.custom-ai.com/v1")
        self.timeout = config.get("timeout", 30)

    async def initialize(self) -> None:
        """Initialize the provider."""
        # Test connection
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            if response.status_code != 200:
                raise Exception("Provider health check failed")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return {
                    "healthy": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds(),
                    "details": response.json()
                }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion."""
        # Transform request to provider format
        provider_request = self._transform_request(request)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await client.post(
                f"{self.base_url}/completions",
                json=provider_request,
                headers=headers
            )
            response.raise_for_status()

            # Transform response back
            return self._transform_response(response.json())

    def _transform_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform OpenAI-style request to custom provider format."""
        return {
            "prompt": request.get("messages", []),
            "max_tokens": request.get("max_tokens", 100),
            "temperature": request.get("temperature", 0.7),
            "model": request.get("model", "default")
        }

    def _transform_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Transform custom provider response to OpenAI format."""
        return {
            "id": f"custom_{response['id']}",
            "object": "text_completion",
            "created": response["created"],
            "model": response["model"],
            "choices": [{
                "text": response["text"],
                "index": 0,
                "finish_reason": response.get("finish_reason", "stop")
            }],
            "usage": response.get("usage", {})
        }

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models from this provider."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await client.get(f"{self.base_url}/models", headers=headers)
            response.raise_for_status()

            models_data = response.json()
            return self._transform_models(models_data)

    def _transform_models(self, models_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform provider models to standard format."""
        return [{
            "id": f"custom-{model['id']}",
            "name": model["name"],
            "context_length": model.get("context_length", 4096),
            "max_tokens": model.get("max_tokens", 2048),
            "input_cost": model.get("pricing", {}).get("input", 0),
            "output_cost": model.get("pricing", {}).get("output", 0),
            "supports_chat": model.get("supports_chat", False),
            "supports_completion": True,
            "capabilities": model.get("capabilities", []),
            "provider": self.name
        } for model in models_data]
```

### Registering Custom Providers

```python
# In your configuration
from src.core.provider_factory import provider_factory

# Register your custom provider
provider_factory.register_provider_type("custom_ai", CustomAIProvider)

# Configuration example
config = {
    "providers": [
        {
            "name": "my_custom_ai",
            "type": "custom_ai",
            "api_key": "your-custom-api-key",
            "base_url": "https://api.custom-ai.com/v1",
            "enabled": True,
            "priority": 1,
            "models": ["model-1", "model-2"]
        }
    ]
}
```

## Advanced Routing Strategies

### Intelligent Provider Selection

```python
from src.core.routing_engine import RoutingEngine
from typing import List, Dict, Any

class IntelligentRouter(RoutingEngine):
    """Advanced routing based on multiple criteria."""

    def __init__(self):
        self.performance_history = {}
        self.cost_tracker = {}
        self.quality_scores = {}

    async def select_provider(self, request: Dict[str, Any], providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select best provider based on context."""
        model = request.get("model")
        context_length = self._estimate_context_length(request)

        # Filter by capability
        capable_providers = [
            p for p in providers
            if self._can_handle_request(p, model, context_length)
        ]

        if not capable_providers:
            raise ValueError("No providers can handle this request")

        # Score providers
        scored_providers = []
        for provider in capable_providers:
            score = await self._calculate_provider_score(provider, request)
            scored_providers.append((provider, score))

        # Sort by score (higher is better)
        scored_providers.sort(key=lambda x: x[1], reverse=True)

        best_provider, score = scored_providers[0]
        self._record_selection(best_provider, score, request)

        return best_provider

    async def _calculate_provider_score(self, provider: Dict[str, Any], request: Dict[str, Any]) -> float:
        """Calculate comprehensive provider score."""
        score = 0.0

        # Performance score (0-40 points)
        perf_score = self._get_performance_score(provider)
        score += perf_score * 0.4

        # Cost score (0-30 points)
        cost_score = self._get_cost_score(provider, request)
        score += cost_score * 0.3

        # Reliability score (0-20 points)
        reliability_score = self._get_reliability_score(provider)
        score += reliability_score * 0.2

        # Load balancing score (0-10 points)
        load_score = self._get_load_balance_score(provider)
        score += load_score * 0.1

        return score

    def _get_performance_score(self, provider: Dict[str, Any]) -> float:
        """Score based on recent performance."""
        provider_name = provider["name"]
        history = self.performance_history.get(provider_name, [])

        if not history:
            return 50.0  # Neutral score for new providers

        recent_responses = history[-10:]  # Last 10 requests
        avg_latency = sum(r["latency"] for r in recent_responses) / len(recent_responses)
        error_rate = sum(1 for r in recent_responses if r["error"]) / len(recent_responses)

        # Lower latency and error rate = higher score
        latency_score = max(0, 100 - (avg_latency * 10))  # Penalize >10s latency
        error_score = (1 - error_rate) * 100

        return (latency_score + error_score) / 2

    def _get_cost_score(self, provider: Dict[str, Any], request: Dict[str, Any]) -> float:
        """Score based on cost efficiency."""
        # Estimate token usage
        estimated_tokens = self._estimate_token_usage(request)

        provider_cost = self.cost_tracker.get(provider["name"], {}).get("avg_cost_per_token", 0.01)
        estimated_cost = estimated_tokens * provider_cost

        # Lower cost = higher score (inverse relationship)
        return max(0, 100 - (estimated_cost * 1000))

    def _get_reliability_score(self, provider: Dict[str, Any]) -> float:
        """Score based on uptime and consistency."""
        provider_name = provider["name"]
        history = self.performance_history.get(provider_name, [])

        if len(history) < 10:
            return 50.0  # Neutral for limited data

        uptime = sum(1 for r in history if not r.get("error")) / len(history)
        consistency = self._calculate_consistency_score(history)

        return (uptime * 100 + consistency) / 2

    def _calculate_consistency_score(self, history: List[Dict[str, Any]]) -> float:
        """Calculate consistency based on response time variance."""
        latencies = [r["latency"] for r in history if "latency" in r]
        if len(latencies) < 2:
            return 50.0

        mean_latency = sum(latencies) / len(latencies)
        variance = sum((l - mean_latency) ** 2 for l in latencies) / len(latencies)
        std_dev = variance ** 0.5

        # Lower variance = higher consistency score
        return max(0, 100 - (std_dev * 20))

    def _record_selection(self, provider: Dict[str, Any], score: float, request: Dict[str, Any]):
        """Record provider selection for learning."""
        provider_name = provider["name"]
        if provider_name not in self.performance_history:
            self.performance_history[provider_name] = []

        self.performance_history[provider_name].append({
            "timestamp": time.time(),
            "score": score,
            "model": request.get("model"),
            "estimated_tokens": self._estimate_token_usage(request)
        })

        # Keep only recent history
        self.performance_history[provider_name] = self.performance_history[provider_name][-100:]
```

### Load Balancing Strategies

```python
from enum import Enum
from typing import List, Dict, Any

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    GEOGRAPHIC = "geographic"

class AdvancedLoadBalancer:
    """Advanced load balancer with multiple strategies."""

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS):
        self.strategy = strategy
        self.provider_states = {}
        self.round_robin_index = {}

    async def select_provider(self, providers: List[Dict[str, Any]], request: Dict[str, Any]) -> Dict[str, Any]:
        """Select provider using configured strategy."""
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(providers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_selection(providers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
            return self._weighted_random_selection(providers)
        elif self.strategy == LoadBalancingStrategy.GEOGRAPHIC:
            return await self._geographic_selection(providers, request)
        else:
            return providers[0]  # Fallback

    def _round_robin_selection(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple round-robin selection."""
        provider_names = [p["name"] for p in providers]
        provider_names.sort()  # Consistent ordering

        for name in provider_names:
            if name not in self.round_robin_index:
                self.round_robin_index[name] = 0

        # Find next provider
        current_name = provider_names[self.round_robin_index.get("global", 0) % len(provider_names)]
        self.round_robin_index["global"] = (self.round_robin_index.get("global", 0) + 1) % len(provider_names)

        return next(p for p in providers if p["name"] == current_name)

    async def _least_connections_selection(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select provider with least active connections."""
        provider_loads = []

        for provider in providers:
            name = provider["name"]
            if name not in self.provider_states:
                self.provider_states[name] = {"active_connections": 0, "last_updated": time.time()}

            # Get current load (you'd implement actual connection tracking)
            load = await self._get_provider_load(provider)
            provider_loads.append((provider, load))

        # Select provider with minimum load
        provider_loads.sort(key=lambda x: x[1])
        return provider_loads[0][0]

    def _weighted_random_selection(self, providers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Weighted random selection based on provider capacity."""
        import random

        total_weight = sum(p.get("weight", 1) for p in providers)
        random_value = random.uniform(0, total_weight)

        current_weight = 0
        for provider in providers:
            current_weight += provider.get("weight", 1)
            if random_value <= current_weight:
                return provider

        return providers[-1]  # Fallback

    async def _geographic_selection(self, providers: List[Dict[str, Any]], request: Dict[str, Any]) -> Dict[str, Any]:
        """Select provider based on geographic location."""
        # Extract client location from request headers or IP
        client_location = self._get_client_location(request)

        # Score providers by geographic proximity
        scored_providers = []
        for provider in providers:
            proximity_score = self._calculate_geographic_proximity(
                client_location,
                provider.get("region", "us-east-1")
            )
            scored_providers.append((provider, proximity_score))

        scored_providers.sort(key=lambda x: x[1], reverse=True)
        return scored_providers[0][0]
```

## Intelligent Caching Patterns

### Multi-Level Caching Strategy

```python
from typing import Dict, Any, Optional, List
import asyncio
import json
from datetime import datetime, timedelta

class MultiLevelCache:
    """Multi-level caching with automatic data flow."""

    def __init__(self):
        self.l1_cache = {}  # Memory cache
        self.l2_cache = None  # Redis cache
        self.l3_cache = None  # Disk cache
        self.access_patterns = {}
        self.prefetch_queue = asyncio.Queue()

    async def initialize(self):
        """Initialize cache backends."""
        # Initialize Redis
        self.l2_cache = await self._init_redis()

        # Initialize disk cache
        self.l3_cache = await self._init_disk_cache()

        # Start prefetch worker
        asyncio.create_task(self._prefetch_worker())

    async def get(self, key: str, ttl_check: bool = True) -> Optional[Any]:
        """Get value from multi-level cache."""
        # L1: Memory cache
        if key in self.l1_cache:
            value, timestamp = self.l1_cache[key]
            if not ttl_check or not self._is_expired(timestamp, key):
                self._record_access(key, "l1_hit")
                return value
            else:
                del self.l1_cache[key]

        # L2: Redis cache
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value:
                value_data = json.loads(value)
                if not ttl_check or not self._is_expired(value_data["timestamp"], key):
                    self.l1_cache[key] = (value_data["data"], value_data["timestamp"])
                    self._record_access(key, "l2_hit")
                    return value_data["data"]
                else:
                    await self.l2_cache.delete(key)

        # L3: Disk cache
        if self.l3_cache:
            value = await self.l3_cache.get(key)
            if value:
                value_data = json.loads(value)
                if not ttl_check or not self._is_expired(value_data["timestamp"], key):
                    # Promote to higher caches
                    self.l1_cache[key] = (value_data["data"], value_data["timestamp"])
                    if self.l2_cache:
                        await self.l2_cache.setex(key, 3600, json.dumps(value_data))
                    self._record_access(key, "l3_hit")
                    return value_data["data"]

        self._record_access(key, "miss")
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600, metadata: Dict[str, Any] = None):
        """Set value in all cache levels."""
        timestamp = datetime.utcnow().isoformat()
        cache_data = {
            "data": value,
            "timestamp": timestamp,
            "ttl": ttl,
            "metadata": metadata or {}
        }

        # L1: Memory cache
        self.l1_cache[key] = (value, timestamp)

        # L2: Redis cache
        if self.l2_cache:
            await self.l2_cache.setex(key, ttl, json.dumps(cache_data))

        # L3: Disk cache
        if self.l3_cache:
            await self.l3_cache.set(key, json.dumps(cache_data), ttl)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching a pattern."""
        # Invalidate L1
        keys_to_remove = [k for k in self.l1_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.l1_cache[key]

        # Invalidate L2 (Redis)
        if self.l2_cache:
            # Use Redis SCAN for pattern matching
            cursor = 0
            while True:
                cursor, keys = await self.l2_cache.scan(cursor, match=pattern)
                for key in keys:
                    await self.l2_cache.delete(key)
                if cursor == 0:
                    break

        # Invalidate L3
        if self.l3_cache:
            await self.l3_cache.invalidate_pattern(pattern)

    def _record_access(self, key: str, access_type: str):
        """Record access patterns for analysis."""
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                "accesses": [],
                "pattern": self._analyze_key_pattern(key)
            }

        self.access_patterns[key]["accesses"].append({
            "timestamp": datetime.utcnow(),
            "type": access_type
        })

        # Keep only recent accesses
        self.access_patterns[key]["accesses"] = self.access_patterns[key]["accesses"][-10:]

    def _analyze_key_pattern(self, key: str) -> str:
        """Analyze key pattern for prefetching."""
        if "model:" in key:
            return "model_data"
        elif "provider:" in key:
            return "provider_info"
        elif "user:" in key:
            return "user_data"
        else:
            return "generic"

    async def _prefetch_worker(self):
        """Background worker for intelligent prefetching."""
        while True:
            try:
                # Analyze access patterns
                await self._analyze_and_prefetch()

                # Wait before next analysis
                await asyncio.sleep(60)  # Analyze every minute

            except Exception as e:
                print(f"Prefetch worker error: {e}")
                await asyncio.sleep(30)

    async def _analyze_and_prefetch(self):
        """Analyze patterns and prefetch likely needed data."""
        now = datetime.utcnow()

        # Find frequently accessed patterns
        pattern_counts = {}
        for key, data in self.access_patterns.items():
            pattern = data["pattern"]
            recent_accesses = [
                a for a in data["accesses"]
                if (now - a["timestamp"]).seconds < 300  # Last 5 minutes
            ]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + len(recent_accesses)

        # Prefetch high-frequency patterns
        for pattern, count in pattern_counts.items():
            if count > 5:  # Threshold for prefetching
                await self._prefetch_pattern(pattern)

    async def _prefetch_pattern(self, pattern: str):
        """Prefetch data for a pattern."""
        if pattern == "model_data":
            # Prefetch commonly used models
            common_models = ["gpt-3.5-turbo", "gpt-4", "claude-3-haiku"]
            for model in common_models:
                key = f"model:{model}"
                if await self.get(key) is None:
                    # Trigger background fetch
                    await self.prefetch_queue.put(("model", model))
```

### Predictive Caching

```python
class PredictiveCache:
    """Cache that predicts and preloads data based on usage patterns."""

    def __init__(self, base_cache):
        self.cache = base_cache
        self.prediction_model = {}
        self.access_history = []

    async def predict_and_cache(self, current_key: str, context: Dict[str, Any] = None):
        """Predict and cache related data."""
        # Record current access
        self.access_history.append({
            "key": current_key,
            "timestamp": datetime.utcnow(),
            "context": context
        })

        # Keep history manageable
        self.access_history = self.access_history[-1000:]

        # Analyze patterns and predict
        predictions = await self._analyze_patterns(current_key, context)

        # Prefetch predicted items
        for prediction in predictions[:3]:  # Limit concurrent prefetches
            if await self.cache.get(prediction["key"]) is None:
                asyncio.create_task(self._prefetch_item(prediction))

    async def _analyze_patterns(self, current_key: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze access patterns to make predictions."""
        predictions = []

        # Find similar contexts
        similar_accesses = [
            a for a in self.access_history
            if self._context_similarity(a["context"], context) > 0.7
        ]

        if len(similar_accesses) < 3:
            return predictions

        # Find next items in sequence
        next_items = self._find_next_items(similar_accesses, current_key)

        for item, probability in next_items:
            if probability > 0.6:  # Confidence threshold
                predictions.append({
                    "key": item,
                    "probability": probability,
                    "reason": "sequential_pattern"
                })

        # Find correlated items
        correlations = self._find_correlations(current_key)
        for item, correlation in correlations:
            if correlation > 0.8:
                predictions.append({
                    "key": item,
                    "probability": correlation,
                    "reason": "correlation"
                })

        return sorted(predictions, key=lambda x: x["probability"], reverse=True)

    def _context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between contexts."""
        if not context1 or not context2:
            return 0.0

        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0

        matches = sum(1 for key in common_keys if context1[key] == context2[key])
        return matches / len(common_keys)

    def _find_next_items(self, accesses: List[Dict[str, Any]], current_key: str) -> List[tuple]:
        """Find items that typically follow the current key."""
        sequences = []
        current_sequence = []

        # Build sequences from history
        for access in sorted(accesses, key=lambda x: x["timestamp"]):
            if not current_sequence or (access["timestamp"] - current_sequence[-1]["timestamp"]).seconds > 300:
                if len(current_sequence) > 1:
                    sequences.append(current_sequence)
                current_sequence = [access]
            else:
                current_sequence.append(access)

        if len(current_sequence) > 1:
            sequences.append(current_sequence)

        # Find transitions from current_key
        transitions = {}
        for sequence in sequences:
            for i, access in enumerate(sequence):
                if access["key"] == current_key and i < len(sequence) - 1:
                    next_key = sequence[i + 1]["key"]
                    transitions[next_key] = transitions.get(next_key, 0) + 1

        # Calculate probabilities
        total_transitions = sum(transitions.values())
        return [
            (key, count / total_transitions)
            for key, count in transitions.items()
        ]
```

## Context Condensation Workflows

### Advanced Condensation Strategies

```python
from typing import List, Dict, Any, Tuple
import re
from collections import Counter

class AdvancedContextCondenser:
    """Advanced context condensation with multiple strategies."""

    def __init__(self):
        self.strategies = {
            "semantic": self._semantic_condensation,
            "structural": self._structural_condensation,
            "temporal": self._temporal_condensation,
            "hybrid": self._hybrid_condensation
        }

    async def condense(self, messages: List[Dict[str, Any]], strategy: str = "hybrid",
                       max_tokens: int = 512) -> str:
        """Condense context using specified strategy."""
        if strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy}")

        return await self.strategies[strategy](messages, max_tokens)

    async def _semantic_condensation(self, messages: List[Dict[str, Any]], max_tokens: int) -> str:
        """Semantic condensation using AI to summarize."""
        # Group messages by topic/conversation
        topics = self._identify_topics(messages)

        # Generate summaries for each topic
        summaries = []
        for topic, topic_messages in topics.items():
            if len(topic_messages) > 3:  # Only condense large topics
                summary = await self._summarize_topic(topic_messages)
                summaries.append(f"Topic: {topic}\n{summary}")
            else:
                # Keep original messages for small topics
                summaries.extend([msg["content"] for msg in topic_messages])

        return "\n\n".join(summaries)

    async def _structural_condensation(self, messages: List[Dict[str, Any]], max_tokens: int) -> str:
        """Structural condensation preserving important elements."""
        condensed = []
        code_blocks = []
        important_statements = []

        for msg in messages:
            content = msg["content"]

            # Extract code blocks
            code_pattern = r'```[\w]*\n(.*?)\n```'
            codes = re.findall(code_pattern, content, re.DOTALL)
            code_blocks.extend(codes)

            # Remove code from content for analysis
            content_no_code = re.sub(code_pattern, '[CODE_BLOCK]', content, flags=re.DOTALL)

            # Identify important statements
            sentences = self._split_sentences(content_no_code)
            for sentence in sentences:
                if self._is_important_sentence(sentence):
                    important_statements.append(sentence)

        # Combine elements
        result = []

        if important_statements:
            result.append("Key Points:\n" + "\n".join(important_statements[:10]))  # Limit

        if code_blocks:
            result.append("Code Blocks:\n" + "\n\n".join(code_blocks[:5]))  # Limit

        return "\n\n".join(result)

    async def _temporal_condensation(self, messages: List[Dict[str, Any]], max_tokens: int) -> str:
        """Temporal condensation preserving recent and important history."""
        # Score messages by recency and importance
        scored_messages = []
        now = datetime.utcnow()

        for i, msg in enumerate(messages):
            recency_score = 1.0 / (1 + (now - msg.get("timestamp", now)).seconds / 3600)  # Hours ago
            importance_score = self._calculate_importance(msg["content"])
            position_score = i / len(messages)  # Prefer later messages

            total_score = (recency_score * 0.4) + (importance_score * 0.4) + (position_score * 0.2)
            scored_messages.append((total_score, msg))

        # Sort by score and select top messages
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        selected_messages = scored_messages[:int(max_tokens / 50)]  # Estimate tokens

        # Reorder by original sequence and condense
        selected_messages.sort(key=lambda x: messages.index(x[1]))
        condensed_content = [msg["content"] for _, msg in selected_messages]

        return "\n\n".join(condensed_content)

    async def _hybrid_condensation(self, messages: List[Dict[str, Any]], max_tokens: int) -> str:
        """Hybrid approach combining multiple strategies."""
        # First apply structural condensation
        structural = await self._structural_condensation(messages, max_tokens // 2)

        # Then apply temporal filtering
        temporal = await self._temporal_condensation(messages, max_tokens // 2)

        # Combine intelligently
        combined = f"Structural Summary:\n{structural}\n\nTemporal Summary:\n{temporal}"

        # If still too long, apply final semantic condensation
        if self._estimate_tokens(combined) > max_tokens:
            combined = await self._semantic_condensation(messages, max_tokens)

        return combined

    def _identify_topics(self, messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Identify conversation topics."""
        topics = {}

        for msg in messages:
            # Simple topic identification (could use ML)
            content = msg["content"].lower()
            if any(word in content for word in ["error", "bug", "issue", "problem"]):
                topic = "technical_issues"
            elif any(word in content for word in ["feature", "implement", "add"]):
                topic = "feature_discussion"
            elif any(word in content for word in ["question", "how", "what", "why"]):
                topic = "questions_answers"
            else:
                topic = "general_discussion"

            if topic not in topics:
                topics[topic] = []
            topics[topic].append(msg)

        return topics

    async def _summarize_topic(self, messages: List[Dict[str, Any]]) -> str:
        """Summarize a topic using AI."""
        # This would call an AI service to summarize
        # For now, return a simple concatenation with length limit
        content = " ".join([msg["content"] for msg in messages])
        return content[:500] + "..." if len(content) > 500 else content

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import nltk
        try:
            return nltk.sent_tokenize(text)
        except:
            # Fallback sentence splitting
            return re.split(r'[.!?]+', text)

    def _is_important_sentence(self, sentence: str) -> bool:
        """Determine if a sentence is important."""
        important_indicators = [
            "important", "critical", "must", "required", "key",
            "summary", "conclusion", "result", "outcome"
        ]

        sentence_lower = sentence.lower()
        return any(indicator in sentence_lower for indicator in important_indicators)

    def _calculate_importance(self, content: str) -> float:
        """Calculate importance score for content."""
        score = 0.0

        # Length factor
        score += min(len(content) / 1000, 1.0) * 0.3

        # Keyword factor
        important_keywords = ["error", "bug", "fix", "important", "critical", "urgent"]
        keyword_count = sum(1 for word in important_keywords if word in content.lower())
        score += min(keyword_count / 3, 1.0) * 0.4

        # Question factor (questions might be important)
        if "?" in content:
            score += 0.3

        return score

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
```

## Chaos Engineering Scenarios

### Advanced Fault Injection

```python
from typing import Dict, Any, List, Callable
import asyncio
import random
import time
from dataclasses import dataclass

@dataclass
class FaultConfig:
    """Configuration for fault injection."""
    name: str
    probability: float
    duration_ms: int
    error_type: str
    error_message: str = ""
    affects_provider: str = None

class ChaosController:
    """Advanced chaos engineering controller."""

    def __init__(self):
        self.active_faults = {}
        self.fault_history = []
        self.metrics_collector = None

    async def inject_fault(self, config: FaultConfig):
        """Inject a fault into the system."""
        if random.random() < config.probability:
            fault_id = f"{config.name}_{int(time.time())}"

            self.active_faults[fault_id] = {
                "config": config,
                "start_time": time.time(),
                "affected_requests": 0
            }

            # Schedule fault removal
            asyncio.create_task(self._remove_fault_after_delay(fault_id, config.duration_ms))

            self._record_fault_injection(config)
            return fault_id

        return None

    async def _remove_fault_after_delay(self, fault_id: str, delay_ms: int):
        """Remove fault after specified delay."""
        await asyncio.sleep(delay_ms / 1000)
        if fault_id in self.active_faults:
            del self.active_faults[fault_id]

    def should_inject_fault(self, provider: str = None) -> FaultConfig:
        """Determine if a fault should be injected for this request."""
        for fault_id, fault_data in self.active_faults.items():
            config = fault_data["config"]

            # Check if fault applies to this provider
            if config.affects_provider and config.affects_provider != provider:
                continue

            if random.random() < config.probability:
                fault_data["affected_requests"] += 1
                return config

        return None

    def apply_fault_to_request(self, fault: FaultConfig, request: Dict[str, Any]) -> Dict[str, Any]:
        """Apply fault effects to a request."""
        if fault.error_type == "delay":
            # Add artificial delay
            request["_artificial_delay"] = fault.duration_ms / 1000

        elif fault.error_type == "error":
            # Force error response
            request["_force_error"] = {
                "type": "artificial_fault",
                "message": fault.error_message or f"Artificial fault: {fault.name}"
            }

        elif fault.error_type == "timeout":
            # Force timeout
            request["_force_timeout"] = fault.duration_ms / 1000

        elif fault.error_type == "corruption":
            # Corrupt response data
            request["_corrupt_response"] = True

        return request

    def _record_fault_injection(self, config: FaultConfig):
        """Record fault injection for analysis."""
        self.fault_history.append({
            "timestamp": time.time(),
            "fault": config.name,
            "probability": config.probability,
            "duration_ms": config.duration_ms,
            "provider": config.affects_provider
        })

        # Keep history manageable
        self.fault_history = self.fault_history[-1000:]

    async def get_fault_statistics(self) -> Dict[str, Any]:
        """Get statistics about fault injections."""
        total_faults = len(self.fault_history)
        if total_faults == 0:
            return {"total_faults": 0}

        # Analyze fault patterns
        fault_types = {}
        provider_impacts = {}
        time_distribution = {}

        for fault in self.fault_history:
            fault_type = fault["fault"]
            fault_types[fault_type] = fault_types.get(fault_type, 0) + 1

            if fault.get("provider"):
                provider = fault["provider"]
                provider_impacts[provider] = provider_impacts.get(provider, 0) + 1

        return {
            "total_faults": total_faults,
            "active_faults": len(self.active_faults),
            "fault_types": fault_types,
            "provider_impacts": provider_impacts,
            "average_duration_ms": sum(f["duration_ms"] for f in self.fault_history) / total_faults,
            "most_common_fault": max(fault_types.items(), key=lambda x: x[1])[0] if fault_types else None
        }
```

### Automated Chaos Experiments

```python
from typing import List, Dict, Any
import asyncio
import time
from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    """Configuration for chaos experiments."""
    name: str
    duration_minutes: int
    fault_configs: List[FaultConfig]
    success_criteria: Dict[str, Any]
    rollback_on_failure: bool = True

class ChaosExperimentRunner:
    """Automated chaos experiment runner."""

    def __init__(self, chaos_controller: ChaosController):
        self.chaos = chaos_controller
        self.experiments = {}
        self.results = {}

    async def run_experiment(self, config: ExperimentConfig) -> Dict[str, Any]:
        """Run a complete chaos experiment."""
        experiment_id = f"exp_{config.name}_{int(time.time())}"

        self.experiments[experiment_id] = {
            "config": config,
            "start_time": time.time(),
            "status": "running",
            "metrics": {}
        }

        try:
            # Start monitoring
            await self._start_monitoring(experiment_id)

            # Inject faults
            fault_ids = []
            for fault_config in config.fault_configs:
                fault_id = await self.chaos.inject_fault(fault_config)
                if fault_id:
                    fault_ids.append(fault_id)

            # Wait for experiment duration
            await asyncio.sleep(config.duration_minutes * 60)

            # Evaluate results
            success = await self._evaluate_success(experiment_id, config.success_criteria)

            result = {
                "experiment_id": experiment_id,
                "success": success,
                "duration_minutes": config.duration_minutes,
                "faults_injected": len(fault_ids),
                "metrics": self.experiments[experiment_id]["metrics"],
                "recommendations": await self._generate_recommendations(experiment_id, success)
            }

            self.results[experiment_id] = result

            # Cleanup
            if not success and config.rollback_on_failure:
                await self._rollback_experiment(experiment_id)

            return result

        except Exception as e:
            self.experiments[experiment_id]["status"] = "failed"
            self.experiments[experiment_id]["error"] = str(e)
            raise
        finally:
            self.experiments[experiment_id]["end_time"] = time.time()

    async def _start_monitoring(self, experiment_id: str):
        """Start monitoring for the experiment."""
        # This would integrate with your metrics system
        # For example, start collecting error rates, latency, etc.
        pass

    async def _evaluate_success(self, experiment_id: str, criteria: Dict[str, Any]) -> bool:
        """Evaluate if the experiment met success criteria."""
        metrics = self.experiments[experiment_id]["metrics"]

        # Example criteria evaluation
        if "max_error_rate" in criteria:
            actual_error_rate = metrics.get("error_rate", 0)
            if actual_error_rate > criteria["max_error_rate"]:
                return False

        if "min_throughput" in criteria:
            actual_throughput = metrics.get("throughput", 0)
            if actual_throughput < criteria["min_throughput"]:
                return False

        if "max_latency_p95" in criteria:
            actual_p95 = metrics.get("latency_p95", 0)
            if actual_p95 > criteria["max_latency_p95"]:
                return False

        return True

    async def _generate_recommendations(self, experiment_id: str, success: bool) -> List[str]:
        """Generate recommendations based on experiment results."""
        recommendations = []
        metrics = self.experiments[experiment_id]["metrics"]

        if not success:
            if metrics.get("error_rate", 0) > 0.1:  # 10%
                recommendations.append("Consider implementing better error handling and retry logic")

            if metrics.get("latency_p95", 0) > 5000:  # 5 seconds
                recommendations.append("Review and optimize slow code paths")

        if metrics.get("recovery_time", 0) > 30:  # 30 seconds
            recommendations.append("Improve system recovery time")

        return recommendations

    async def _rollback_experiment(self, experiment_id: str):
        """Rollback changes made by the experiment."""
        # This would undo any persistent changes made during the experiment
        # For example, restore configuration, clear caches, etc.
        pass

    async def get_experiment_report(self, experiment_id: str) -> Dict[str, Any]:
        """Generate a detailed report for an experiment."""
        if experiment_id not in self.results:
            raise ValueError(f"Experiment {experiment_id} not found")

        result = self.results[experiment_id]
        experiment = self.experiments[experiment_id]

        return {
            "experiment_id": experiment_id,
            "config": experiment["config"].__dict__,
            "result": result,
            "timeline": {
                "start_time": experiment["start_time"],
                "end_time": experiment.get("end_time"),
                "duration_seconds": experiment.get("end_time", time.time()) - experiment["start_time"]
            },
            "fault_statistics": await self.chaos.get_fault_statistics()
        }
```

## Performance Optimization Techniques

### Advanced Connection Pooling

```python
from typing import Dict, Any, Optional
import asyncio
import aiohttp
from aiohttp import ClientSession, TCPConnector
from dataclasses import dataclass, field

@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pooling."""
    max_connections: int = 100
    max_connections_per_host: int = 30
    keepalive_timeout: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    pool_recycle: float = 3600.0  # 1 hour
    dns_cache_ttl: float = 300.0   # 5 minutes

class AdaptiveConnectionPool:
    """Adaptive connection pool that adjusts based on usage patterns."""

    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.pools: Dict[str, ClientSession] = {}
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        self.adjustment_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the connection pool manager."""
        # Start adaptive adjustment task
        self.adjustment_task = asyncio.create_task(self._adaptive_adjustment_loop())

    async def get_session(self, base_url: str) -> ClientSession:
        """Get or create a session for the given base URL."""
        host_key = self._extract_host(base_url)

        if host_key not in self.pools:
            await self._create_session(host_key, base_url)

        session = self.pools[host_key]

        # Update usage statistics
        self._update_usage_stats(host_key)

        return session

    async def _create_session(self, host_key: str, base_url: str):
        """Create a new session for a host."""
        connector = TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections_per_host,
            keepalive_timeout=self.config.keepalive_timeout,
            ttl_dns_cache=self.config.dns_cache_ttl,
            use_dns_cache=True
        )

        timeout = aiohttp.ClientTimeout(
            connect=self.config.connect_timeout,
            sock_read=self.config.read_timeout
        )

        session = ClientSession(
            base_url=base_url,
            connector=connector,
            timeout=timeout
        )

        self.pools[host_key] = session
        self.usage_stats[host_key] = {
            "created_at": asyncio.get_event_loop().time(),
            "request_count": 0,
            "error_count": 0,
            "avg_response_time": 0.0,
            "last_used": asyncio.get_event_loop().time()
        }

    def _update_usage_stats(self, host_key: str):
        """Update usage statistics for a host."""
        now = asyncio.get_event_loop().time()
        stats = self.usage_stats[host_key]

        stats["request_count"] += 1
        stats["last_used"] = now

    async def record_response(self, host_key: str, response_time: float, success: bool):
        """Record response metrics."""
        stats = self.usage_stats[host_key]

        if not success:
            stats["error_count"] += 1

        # Update moving average response time
        alpha = 0.1  # Smoothing factor
        stats["avg_response_time"] = (
            alpha * response_time +
            (1 - alpha) * stats["avg_response_time"]
        )

    async def _adaptive_adjustment_loop(self):
        """Continuously adjust pool parameters based on usage."""
        while True:
            try:
                await self._adjust_pools()
                await asyncio.sleep(60)  # Adjust every minute
            except Exception as e:
                print(f"Error in adaptive adjustment: {e}")
                await asyncio.sleep(30)

    async def _adjust_pools(self):
        """Adjust connection pool parameters based on current usage."""
        for host_key, stats in self.usage_stats.items():
            if host_key not in self.pools:
                continue

            session = self.pools[host_key]
            connector = session.connector

            # Calculate optimal pool size based on usage
            optimal_size = self._calculate_optimal
            # Calculate optimal pool size based on usage
            optimal_size = self._calculate_optimal_pool_size(stats)

            # Adjust pool size if needed
            if optimal_size != connector.limit:
                await self._resize_pool(host_key, optimal_size)

    def _calculate_optimal_pool_size(self, stats: Dict[str, Any]) -> int:
        """Calculate optimal pool size based on usage statistics."""
        request_rate = stats["request_count"] / max(1, asyncio.get_event_loop().time() - stats["created_at"])
        error_rate = stats["error_count"] / max(1, stats["request_count"])

        # Base size on request rate and error rate
        base_size = min(50, max(5, int(request_rate * 10)))

        # Reduce size if high error rate
        if error_rate > 0.1:  # 10% error rate
            base_size = max(1, int(base_size * 0.5))

        # Increase size if high response time variability
        if stats["avg_response_time"] > 5.0:  # 5 seconds average
            base_size = min(100, int(base_size * 1.5))

        return base_size

    async def _resize_pool(self, host_key: str, new_size: int):
        """Resize the connection pool for a host."""
        if host_key not in self.pools:
            return

        session = self.pools[host_key]
        connector = session.connector

        # Close existing session
        await session.close()

        # Create new session with adjusted size
        base_url = str(session._base_url) if hasattr(session, '_base_url') else None
        await self._create_session(host_key, base_url)

        print(f"Resized connection pool for {host_key} to {new_size} connections")

    def _extract_host(self, url: str) -> str:
        """Extract host from URL for pool management."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def close_all(self):
        """Close all connection pools."""
        for session in self.pools.values():
            await session.close()
        self.pools.clear()

        if self.adjustment_task:
            self.adjustment_task.cancel()
            try:
                await self.adjustment_task
            except asyncio.CancelledError:
                pass
```

### Request Batching and Optimization

```python
from typing import List, Dict, Any, Callable, Awaitable
import asyncio
import time
from collections import defaultdict

class RequestBatcher:
    """Batch similar requests to reduce API calls and improve throughput."""

    def __init__(self, max_batch_size: int = 10, max_wait_time: float = 0.1):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.batches: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.batch_handlers: Dict[str, Callable[[List[Dict[str, Any]]], Awaitable[List[Any]]]] = {}
        self.timers: Dict[str, asyncio.TimerHandle] = {}

    def register_handler(self, batch_type: str, handler: Callable[[List[Dict[str, Any]]], Awaitable[List[Any]]]):
        """Register a handler for a specific batch type."""
        self.batch_handlers[batch_type] = handler

    async def submit_request(self, batch_type: str, request: Dict[str, Any]) -> Any:
        """Submit a request for batching."""
        if batch_type not in self.batch_handlers:
            raise ValueError(f"No handler registered for batch type: {batch_type}")

        # Add request to batch
        future = asyncio.Future()
        request["_future"] = future
        request["_submitted_at"] = time.time()

        self.batches[batch_type].append(request)

        # Check if we should process immediately
        if len(self.batches[batch_type]) >= self.max_batch_size:
            await self._process_batch(batch_type)
        else:
            # Schedule timer if not already scheduled
            if batch_type not in self.timers:
                loop = asyncio.get_event_loop()
                self.timers[batch_type] = loop.call_later(
                    self.max_wait_time,
                    lambda: asyncio.create_task(self._process_batch(batch_type))
                )

        return await future

    async def _process_batch(self, batch_type: str):
        """Process a batch of requests."""
        if batch_type in self.timers:
            self.timers[batch_type].cancel()
            del self.timers[batch_type]

        batch = self.batches[batch_type]
        if not batch:
            return

        # Clear the batch
        self.batches[batch_type] = []

        try:
            # Call the handler
            handler = self.batch_handlers[batch_type]
            results = await handler(batch)

            # Distribute results to waiting futures
            for i, request in enumerate(batch):
                if i < len(results):
                    request["_future"].set_result(results[i])
                else:
                    request["_future"].set_exception(
                        RuntimeError(f"No result for request {i} in batch")
                    )

        except Exception as e:
            # Fail all futures in the batch
            for request in batch:
                request["_future"].set_exception(e)

    async def flush_all(self):
        """Flush all pending batches."""
        tasks = []
        for batch_type in list(self.batches.keys()):
            if self.batches[batch_type]:
                tasks.append(self._process_batch(batch_type))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Usage example: Model discovery batching
class ModelDiscoveryBatcher:
    """Batch model discovery requests for efficiency."""

    def __init__(self, discovery_service):
        self.discovery = discovery_service
        self.batcher = RequestBatcher(max_batch_size=20, max_wait_time=0.2)

        # Register batch handler
        self.batcher.register_handler("model_discovery", self._handle_model_batch)

    async def _handle_model_batch(self, requests: List[Dict[str, Any]]) -> List[Any]:
        """Handle a batch of model discovery requests."""
        # Group by provider
        by_provider = defaultdict(list)
        for request in requests:
            provider = request.get("provider", "all")
            by_provider[provider].append(request)

        results = []
        for provider, provider_requests in by_provider.items():
            if provider == "all":
                # Discover from all providers
                batch_result = await self.discovery.discover_all_models()
                # Distribute result to each request in this batch
                results.extend([batch_result] * len(provider_requests))
            else:
                # Discover from specific provider
                batch_result = await self.discovery.discover_provider_models(provider)
                results.extend([batch_result] * len(provider_requests))

        return results

    async def discover_models(self, provider: str = None, **options) -> List[Dict[str, Any]]:
        """Discover models with batching."""
        request = {
            "provider": provider,
            **options
        }

        return await self.batcher.submit_request("model_discovery", request)
```

## Security Hardening

### Advanced Authentication & Authorization

```python
from typing import Dict, Any, List, Optional
import jwt
import time
import hashlib
import hmac
from dataclasses import dataclass

@dataclass
class SecurityContext:
    """Security context for requests."""
    user_id: str
    roles: List[str]
    permissions: List[str]
    api_key_hash: str
    ip_address: str
    user_agent: str
    request_limits: Dict[str, int]

class AdvancedSecurityManager:
    """Advanced security manager with multiple authentication methods."""

    def __init__(self, jwt_secret: str, api_keys: Dict[str, str]):
        self.jwt_secret = jwt_secret
        self.api_keys = {self._hash_key(k): v for k, v in api_keys.items()}
        self.rate_limiters = {}
        self.suspicious_activity = {}

    def authenticate_request(self, request) -> Optional[SecurityContext]:
        """Authenticate a request using multiple methods."""
        # Try JWT first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                return self._create_context_from_jwt(payload, request)
            except jwt.ExpiredSignatureError:
                raise ValueError("Token expired")
            except jwt.InvalidTokenError:
                pass  # Try other methods

        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return self._authenticate_api_key(api_key, request)

        # Try query parameter (less secure)
        api_key = request.query_params.get("api_key")
        if api_key:
            self._log_security_event("api_key_in_query", request)
            return self._authenticate_api_key(api_key, request)

        return None

    def _authenticate_api_key(self, api_key: str, request) -> Optional[SecurityContext]:
        """Authenticate using API key."""
        key_hash = self._hash_key(api_key)

        if key_hash in self.api_keys:
            user_data = self.api_keys[key_hash]
            return SecurityContext(
                user_id=user_data.get("user_id", "api_user"),
                roles=user_data.get("roles", ["user"]),
                permissions=user_data.get("permissions", ["read"]),
                api_key_hash=key_hash,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("User-Agent", ""),
                request_limits=user_data.get("limits", {"requests_per_hour": 1000})
            )

        return None

    def _create_context_from_jwt(self, payload: Dict[str, Any], request) -> SecurityContext:
        """Create security context from JWT payload."""
        return SecurityContext(
            user_id=payload["sub"],
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            api_key_hash="",  # JWT doesn't use API keys
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            request_limits=payload.get("limits", {})
        )

    def authorize_request(self, context: SecurityContext, resource: str, action: str) -> bool:
        """Authorize a request based on context and resource."""
        if not context:
            return False

        # Check roles
        required_roles = self._get_required_roles(resource, action)
        if required_roles and not any(role in context.roles for role in required_roles):
            return False

        # Check permissions
        required_permissions = self._get_required_permissions(resource, action)
        if required_permissions and not any(perm in context.permissions for perm in required_permissions):
            return False

        # Check rate limits
        if not self._check_rate_limits(context):
            return False

        return True

    def _check_rate_limits(self, context: SecurityContext) -> bool:
        """Check if request is within rate limits."""
        user_key = context.user_id
        now = int(time.time())

        if user_key not in self.rate_limiters:
            self.rate_limiters[user_key] = {
                "requests": [],
                "blocked_until": 0
            }

        limiter = self.rate_limiters[user_key]

        # Check if currently blocked
        if now < limiter["blocked_until"]:
            return False

        # Clean old requests (keep last hour)
        limiter["requests"] = [r for r in limiter["requests"] if now - r < 3600]

        # Check limits
        limits = context.request_limits

        # Requests per hour
        if len(limiter["requests"]) >= limits.get("requests_per_hour", 1000):
            limiter["blocked_until"] = now + 3600  # Block for 1 hour
            self._log_security_event("rate_limit_exceeded", {"user": user_key})
            return False

        # Requests per minute
        recent_requests = [r for r in limiter["requests"] if now - r < 60]
        if len(recent_requests) >= limits.get("requests_per_minute", 100):
            limiter["blocked_until"] = now + 60  # Block for 1 minute
            return False

        # Add current request
        limiter["requests"].append(now)

        return True

    def _get_required_roles(self, resource: str, action: str) -> List[str]:
        """Get required roles for a resource and action."""
        # This would be configurable
        role_map = {
            ("models", "write"): ["admin", "editor"],
            ("providers", "configure"): ["admin"],
            ("system", "restart"): ["admin"],
        }

        return role_map.get((resource, action), [])

    def _get_required_permissions(self, resource: str, action: str) -> List[str]:
        """Get required permissions for a resource and action."""
        permission_map = {
            ("models", "read"): ["models:read"],
            ("models", "write"): ["models:write"],
            ("providers", "read"): ["providers:read"],
            ("system", "read"): ["system:read"],
        }

        return permission_map.get((resource, action), [])

    def _hash_key(self, key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    def _get_client_ip(self, request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.client.host if hasattr(request, 'client') else "unknown"

    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events."""
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "details": details
        }

        # Store in suspicious activity log
        if event_type not in self.suspicious_activity:
            self.suspicious_activity[event_type] = []

        self.suspicious_activity[event_type].append(event)

        # Keep only recent events
        self.suspicious_activity[event_type] = self.suspicious_activity[event_type][-100:]

    def get_security_report(self) -> Dict[str, Any]:
        """Generate security report."""
        return {
            "suspicious_activity": self.suspicious_activity,
            "rate_limited_users": [
                user for user, data in self.rate_limiters.items()
                if data.get("blocked_until", 0) > time.time()
            ],
            "total_api_keys": len(self.api_keys)
        }
```

## Multi-Region Deployment

### Cross-Region Load Balancing

```python
from typing import Dict, List, Any, Optional
import asyncio
import time
import statistics

@dataclass
class RegionInfo:
    """Information about a deployment region."""
    name: str
    location: str
    endpoint: str
    health_check_url: str
    capacity: int  # Max concurrent requests
    current_load: int = 0
    latency_ms: float = 0.0
    last_health_check: float = 0.0
    healthy: bool = True

class MultiRegionLoadBalancer:
    """Load balancer for multi-region deployments."""

    def __init__(self):
        self.regions: Dict[str, RegionInfo] = {}
        self.client_regions: Dict[str, str] = {}  # IP -> preferred region
        self.health_check_interval = 30  # seconds

    async def initialize(self):
        """Initialize the load balancer."""
        # Start health checking task
        asyncio.create_task(self._health_check_loop())

    def add_region(self, region: RegionInfo):
        """Add a region to the load balancer."""
        self.regions[region.name] = region

    async def route_request(self, request, client_ip: str) -> Optional[RegionInfo]:
        """Route a request to the best region."""
        available_regions = [r for r in self.regions.values() if r.healthy]

        if not available_regions:
            return None

        # Try preferred region first
        preferred_region = self._get_preferred_region(client_ip)
        if preferred_region and preferred_region in [r.name for r in available_regions]:
            region = self.regions[preferred_region]
            if region.current_load < region.capacity:
                return region

        # Find best available region
        return self._select_best_region(available_regions)

    def _get_preferred_region(self, client_ip: str) -> Optional[str]:
        """Get preferred region for a client IP."""
        # Check cache first
        if client_ip in self.client_regions:
            return self.client_regions[client_ip]

        # Determine based on IP geolocation (simplified)
        region = self._geolocate_ip(client_ip)
        self.client_regions[client_ip] = region

        # Cache for 1 hour
        asyncio.get_event_loop().call_later(3600, lambda: self.client_regions.pop(client_ip, None))

        return region

    def _geolocate_ip(self, ip: str) -> str:
        """Simple IP geolocation (would use a real service)."""
        # Simplified logic - in practice use a geolocation service
        if ip.startswith("192.168.") or ip == "127.0.0.1":
            return "local"

        # Check first octet for rough geographic estimation
        try:
            first_octet = int(ip.split(".")[0])
            if first_octet <= 50:
                return "us-east"
            elif first_octet <= 100:
                return "us-west"
            elif first_octet <= 150:
                return "eu-west"
            else:
                return "ap-southeast"
        except:
            return "us-east"  # Default

    def _select_best_region(self, available_regions: List[RegionInfo]) -> RegionInfo:
        """Select the best region based on load and latency."""
        # Score each region
        region_scores = []

        for region in available_regions:
            # Skip if at capacity
            if region.current_load >= region.capacity:
                continue

            # Calculate load factor (0-1, lower is better)
            load_factor = region.current_load / region.capacity

            # Calculate latency factor (normalized, lower is better)
            max_latency = max(r.latency_ms for r in available_regions)
            latency_factor = region.latency_ms / max_latency if max_latency > 0 else 0

            # Combined score (weighted average)
            score = (load_factor * 0.6) + (latency_factor * 0.4)

            region_scores.append((score, region))

        if not region_scores:
            # All regions at capacity, return least loaded
            return min(available_regions, key=lambda r: r.current_load)

        # Return region with lowest score
        return min(region_scores, key=lambda x: x[0])[1]

    async def record_request(self, region_name: str, latency_ms: float, success: bool):
        """Record request metrics for a region."""
        if region_name in self.regions:
            region = self.regions[region_name]

            # Update latency (moving average)
            alpha = 0.1
            region.latency_ms = (alpha * latency_ms) + ((1 - alpha) * region.latency_ms)

            if success:
                region.current_load = max(0, region.current_load - 1)
            else:
                # Failed request, still decrement load but mark as unhealthy if too many failures
                region.current_load = max(0, region.current_load - 1)

    async def _health_check_loop(self):
        """Continuously check health of all regions."""
        while True:
            try:
                await self._check_all_regions()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                print(f"Health check error: {e}")
                await asyncio.sleep(10)

    async def _check_all_regions(self):
        """Check health of all regions."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            tasks = []
            for region in self.regions.values():
                tasks.append(self._check_region_health(session, region))

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_region_health(self, session: aiohttp.ClientSession, region: RegionInfo):
        """Check health of a specific region."""
        try:
            start_time = time.time()

            async with session.get(region.health_check_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                healthy = response.status == 200
                latency = (time.time() - start_time) * 1000

                region.healthy = healthy
                region.latency_ms = latency
                region.last_health_check = time.time()

        except Exception as e:
            region.healthy = False
            region.last_health_check = time.time()
            print(f"Health check failed for {region.name}: {e}")

    def get_region_stats(self) -> Dict[str, Any]:
        """Get statistics for all regions."""
        return {
            region.name: {
                "healthy": region.healthy,
                "load": region.current_load,
                "capacity": region.capacity,
                "latency_ms": region.latency_ms,
                "load_percentage": (region.current_load / region.capacity) * 100 if region.capacity > 0 else 0
            }
            for region in self.regions.values()
        }
```

## Advanced Monitoring & Alerting

### Intelligent Alerting System

```python
from typing import Dict, Any, List, Callable, Awaitable
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class Alert:
    """Alert definition."""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    value: Any = None
    threshold: Any = None

@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    condition: str  # Python expression
    severity: AlertSeverity
    title_template: str
    description_template: str
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    cooldown_minutes: int = 5  # Don't re-alert within this time

class IntelligentAlertingSystem:
    """Advanced alerting system with intelligent rules and correlation."""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable[[Alert], Awaitable[None]]] = []
        self.metrics_store = {}

    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)

    def add_notification_handler(self, handler: Callable[[Alert], Awaitable[None]]):
        """Add a notification handler."""
        self.notification_handlers.append(handler)

    async def evaluate_rules(self, metrics: Dict[str, Any]):
        """Evaluate all rules against current metrics."""
        self.metrics_store.update(metrics)

        for rule in self.rules:
            await self._evaluate_rule(rule)

    async def _evaluate_rule(self, rule: AlertRule):
        """Evaluate a single rule."""
        try:
            # Evaluate condition
            condition_result = self._evaluate_condition(rule.condition)

            if condition_result:
                # Condition met, create or update alert
                alert_key = f"{rule.name}"

                if alert_key not in self.active_alerts:
                    # New alert
                    alert = Alert(
                        id=f"{alert_key}_{int(time.time())}",
                        title=self._format_template(rule.title_template),
                        description=self._format_template(rule.description_template),
                        severity=rule.severity,
                        labels=rule.labels.copy(),
                        annotations=rule.annotations.copy()
                    )

                    self.active_alerts[alert_key] = alert
                    self.alert_history.append(alert)

                    # Send notifications
                    await self._send_notifications(alert)
                else:
                    # Update existing alert
                    alert = self.active_alerts[alert_key]
                    alert.updated_at = time.time()
                    alert.value = self._get_condition_value(rule.condition)

            else:
                # Condition not met, resolve alert if it exists
                alert_key = f"{rule.name}"
                if alert_key in self.active_alerts:
                    alert = self.active_alerts[alert_key]
                    alert.status = AlertStatus.RESOLVED
                    alert.updated_at = time.time()

                    # Send resolution notification
                    await self._send_notifications(alert)

                    # Remove from active alerts
                    del self.active_alerts[alert_key]

        except Exception as e:
            print(f"Error evaluating rule {rule.name}: {e}")

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a condition expression."""
        try:
            # Safe evaluation with limited globals
            allowed_names = {
                "metrics": self.metrics_store,
                "time": time,
                "len": len,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs
            }

            return bool(eval(condition, {"__builtins__": {}}, allowed_names))
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False

    def _get_condition_value(self, condition: str) -> Any:
        """Get the value that triggered the condition."""
        # This is a simplified implementation
        # In practice, you'd parse the condition to extract the relevant metric
        return None

    def _format_template(self, template: str) -> str:
        """Format a template string with metrics values."""
        try:
            return template.format(**self.metrics_store)
        except Exception as e:
            return template

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications."""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                print(f"Notification handler error: {e}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the specified hours."""
        cutoff_time = time.time() - (hours * 3600)
        return [alert for alert in self.alert_history if alert.created_at >= cutoff_time]

    def acknowledge_alert(self, alert_id: str, user: str):
        """Acknowledge an alert."""
        for alert in self.active_alerts.values():
            if alert.id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.annotations["acknowledged_by"] = user
                alert.annotations["acknowledged_at"] = str(time.time())
                break

# Example usage
async def setup_alerting():
    """Set up intelligent alerting."""
    alerting = IntelligentAlertingSystem()

    # Add rules
    alerting.add_rule(AlertRule(
        name="high_error_rate",
        condition="metrics.get('error_rate', 0) > 0.05",
        severity=AlertSeverity.WARNING,
        title_template="High error rate detected",
        description_template="Error rate is {metrics[error_rate]}% which exceeds threshold",
        cooldown_minutes=10
    ))

    alerting.add_rule(AlertRule(
        name="high_latency",
        condition="metrics.get('latency_p95', 0) > 5000",
        severity=AlertSeverity.ERROR,
        title_template="High latency detected",
        description_template="95th percentile latency is {metrics[latency_p95]}ms",
        cooldown_minutes=5
    ))

    # Add notification handler (e.g., Slack, email, etc.)
    async def slack_notification(alert: Alert):
        # Implement Slack notification
        pass

    alerting.add_notification_handler(slack_notification)

    return alerting
```

This advanced usage guide covers sophisticated techniques for production deployments. For more detailed implementation examples and additional scenarios, refer to the specific guides mentioned in the main README.