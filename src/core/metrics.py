import time
from typing import Dict, Any
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

@dataclass
class ProviderMetrics:
    """Metrics for a single provider"""
    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    total_tokens: int = 0
    errors: Dict[str, int] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = defaultdict(int)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


@dataclass
class SummarizationMetrics:
    """Metrics for context summarization operations"""
    total_summaries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_latency: float = 0.0
    avg_latency: float = 0.0
    
    def record_summary(self, is_cache_hit: bool, latency: float = 0.0):
        """Record a summarization event"""
        self.total_summaries += 1
        if is_cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.total_latency += latency
            self.avg_latency = self.total_latency / max(self.cache_misses, 1)
        # For cache hits, latency is 0, so avg remains for computation time

class MetricsCollector:
    """Collect and manage metrics for all providers"""
    
    def __init__(self):
        self.providers: Dict[str, ProviderMetrics] = {}
        self.summarization_metrics = SummarizationMetrics()
        self.request_history = deque(maxlen=1000)  # Keep last 1000 requests
        self.start_time = datetime.now()
    
    def get_or_create_provider(self, provider_name: str) -> ProviderMetrics:
        """Get or create provider metrics"""
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderMetrics(name=provider_name)
        return self.providers[provider_name]
    
    def record_request(self, provider_name: str, success: bool, response_time: float, 
                      tokens: int = 0, error_type: str = None):
        """Record a request for a provider"""
        provider = self.get_or_create_provider(provider_name)
        
        # Update counters
        provider.total_requests += 1
        if success:
            provider.successful_requests += 1
        else:
            provider.failed_requests += 1
            if error_type:
                provider.errors[error_type] += 1
        
        # Update response time (moving average)
        if success:
            if provider.avg_response_time == 0:
                provider.avg_response_time = response_time
            else:
                # Simple moving average
                provider.avg_response_time = (provider.avg_response_time * 0.9) + (response_time * 0.1)
        
        # Update tokens
        provider.total_tokens += tokens
        
        # Add to request history
        self.request_history.append({
            "timestamp": datetime.now().isoformat(),
            "provider": provider_name,
            "success": success,
            "response_time": response_time,
            "tokens": tokens,
            "error_type": error_type
        })
    
    def get_provider_stats(self, provider_name: str) -> Dict[str, Any]:
        """Get detailed stats for a provider"""
        provider = self.get_or_create_provider(provider_name)
        return asdict(provider)
    
    def record_summary(self, is_cache_hit: bool, latency: float = 0.0):
        """Record summarization metrics"""
        self.summarization_metrics.record_summary(is_cache_hit, latency)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get stats for all providers"""
        return {
            "providers": {name: asdict(metrics) for name, metrics in self.providers.items()},
            "summarization": asdict(self.summarization_metrics),
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "total_requests": sum(p.total_requests for p in self.providers.values()),
            "successful_requests": sum(p.successful_requests for p in self.providers.values()),
            "failed_requests": sum(p.failed_requests for p in self.providers.values())
        }
    
    def reset_stats(self):
        """Reset all metrics"""
        self.providers.clear()
        self.request_history.clear()
        self.start_time = datetime.now()

# Global metrics collector instance
metrics_collector = MetricsCollector()
