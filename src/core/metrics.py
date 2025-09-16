import asyncio
import json
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from .logging import ContextualLogger

logger = ContextualLogger(__name__)


@dataclass
class ModelMetrics:
    """Metrics for a specific model within a provider"""

    model_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0
    total_tokens: int = 0
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


@dataclass
class ProviderMetrics:
    """Enhanced metrics for a single provider"""

    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = float("inf")
    max_response_time: float = 0.0
    total_tokens: int = 0
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    models: Dict[str, ModelMetrics] = field(default_factory=dict)

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

    def get_or_create_model(self, model_name: str) -> ModelMetrics:
        """Get or create model-specific metrics"""
        if model_name not in self.models:
            self.models[model_name] = ModelMetrics(model_name=model_name)
        return self.models[model_name]


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


@dataclass
class CachePerformanceMetrics:
    """Cache performance metrics"""

    hit_rate: float = 0.0
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    entries: int = 0
    memory_usage_mb: float = 0.0
    max_memory_mb: float = 0.0
    evictions: int = 0
    last_updated: float = 0.0


@dataclass
class ConnectionPoolMetrics:
    """HTTP connection pool metrics"""

    max_keepalive_connections: int = 0
    max_connections: int = 0
    active_connections: int = 0
    available_connections: int = 0
    pending_requests: int = 0
    total_requests: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0


@dataclass
class ConfigurationMetrics:
    """Configuration loading metrics"""

    total_loads: int = 0
    successful_loads: int = 0
    failed_loads: int = 0
    avg_load_time_ms: float = 0.0
    last_load_time: float = 0.0
    config_file_size: int = 0
    providers_count: int = 0


@dataclass
class SystemHealthMetrics:
    """System health and resource metrics"""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    network_connections: int = 0
    open_files: int = 0
    threads_count: int = 0
    last_updated: float = 0.0


@dataclass
class ErrorRateMetrics:
    """Detailed error rate metrics by category"""

    total_errors: int = 0
    connection_errors: int = 0
    timeout_errors: int = 0
    rate_limit_errors: int = 0
    authentication_errors: int = 0
    server_errors: int = 0
    client_errors: int = 0
    other_errors: int = 0
    error_rate_percent: float = 0.0


@dataclass
class MetricsHistory:
    """Historical metrics data point"""

    timestamp: str
    providers: Dict[str, Dict[str, Any]]
    summarization: Dict[str, Any]
    total_requests: int
    successful_requests: int
    failed_requests: int


class MetricsPersistence:
    """Handle persistence of metrics data"""

    def __init__(
        self, storage_path: Optional[str] = None, max_age_days: int = 30
    ):
        self.storage_path = (
            Path(storage_path) if storage_path else Path("metrics_data.json")
        )
        self.max_age_days = max_age_days
        self._executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="metrics-persistence"
        )
        self._lock = threading.Lock()

    def save_metrics(self, metrics_data: Dict[str, Any]) -> None:
        """Asynchronously save metrics to storage"""
        self._executor.submit(self._save_sync, metrics_data)

    def _save_sync(self, metrics_data: Dict[str, Any]) -> None:
        """Synchronously save metrics to storage"""
        try:
            with self._lock:
                # Load existing data
                existing_data = self._load_existing_data()

                # Add timestamp to current metrics
                timestamp = datetime.now().isoformat()
                history_entry = MetricsHistory(
                    timestamp=timestamp,
                    providers=metrics_data.get("providers", {}),
                    summarization=metrics_data.get("summarization", {}),
                    total_requests=metrics_data.get("total_requests", 0),
                    successful_requests=metrics_data.get(
                        "successful_requests", 0
                    ),
                    failed_requests=metrics_data.get("failed_requests", 0),
                )

                # Add to history and clean old entries
                existing_data["history"].append(asdict(history_entry))
                existing_data["history"] = self._clean_old_entries(
                    existing_data["history"]
                )
                existing_data["last_updated"] = timestamp

                # Save to file
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error("Failed to save metrics", error=str(e))

    def load_metrics_history(self, days: int = 7) -> List[MetricsHistory]:
        """Load metrics history for the specified number of days"""
        try:
            data = self._load_existing_data()
            cutoff_date = datetime.now() - timedelta(days=days)

            history = []
            for entry in data.get("history", []):
                entry_date = datetime.fromisoformat(entry["timestamp"])
                if entry_date >= cutoff_date:
                    history.append(MetricsHistory(**entry))

            return history

        except Exception as e:
            logger.error("Failed to load metrics history", error=str(e))
            return []

    def _load_existing_data(self) -> Dict[str, Any]:
        """Load existing metrics data from storage"""
        if not self.storage_path.exists():
            return {"history": [], "last_updated": None}

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"history": [], "last_updated": None}

    def _clean_old_entries(
        self, history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove entries older than max_age_days"""
        if not history:
            return history

        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        cleaned = []

        for entry in history:
            try:
                entry_date = datetime.fromisoformat(entry["timestamp"])
                if entry_date >= cutoff_date:
                    cleaned.append(entry)
            except (ValueError, KeyError):
                continue  # Skip invalid entries

        return cleaned

    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format with enhanced per-model metrics"""
        history = self.load_metrics_history(days=1)  # Last 24 hours

        if not history:
            return "# No metrics data available"

        lines = []
        lines.append(
            "# HELP proxy_api_requests_total Total number of requests"
        )
        lines.append("# TYPE proxy_api_requests_total counter")

        lines.append(
            "# HELP proxy_api_requests_successful_total Total number of successful requests"
        )
        lines.append("# TYPE proxy_api_requests_successful_total counter")

        lines.append(
            "# HELP proxy_api_requests_failed_total Total number of failed requests"
        )
        lines.append("# TYPE proxy_api_requests_failed_total counter")

        lines.append(
            "# HELP proxy_api_response_time_avg Average response time in seconds"
        )
        lines.append("# TYPE proxy_api_response_time_avg gauge")

        lines.append(
            "# HELP proxy_api_provider_success_rate Success rate per provider"
        )
        lines.append("# TYPE proxy_api_provider_success_rate gauge")

        lines.append(
            "# HELP proxy_api_model_requests_total Total requests per model"
        )
        lines.append("# TYPE proxy_api_model_requests_total counter")

        lines.append(
            "# HELP proxy_api_model_success_rate Success rate per model"
        )
        lines.append("# TYPE proxy_api_model_success_rate gauge")

        lines.append(
            "# HELP proxy_api_model_response_time_avg Average response time per model in seconds"
        )
        lines.append("# TYPE proxy_api_model_response_time_avg gauge")

        lines.append(
            "# HELP proxy_api_model_tokens_total Total tokens used per model"
        )
        lines.append("# TYPE proxy_api_model_tokens_total counter")

        # Cache performance metrics
        lines.append(
            "# HELP proxy_api_cache_hit_rate Cache hit rate percentage"
        )
        lines.append("# TYPE proxy_api_cache_hit_rate gauge")
        lines.append(
            "# HELP proxy_api_cache_entries_total Total cache entries"
        )
        lines.append("# TYPE proxy_api_cache_entries_total gauge")
        lines.append(
            "# HELP proxy_api_cache_memory_usage_mb Cache memory usage in MB"
        )
        lines.append("# TYPE proxy_api_cache_memory_usage_mb gauge")
        lines.append(
            "# HELP proxy_api_cache_evictions_total Total cache evictions"
        )
        lines.append("# TYPE proxy_api_cache_evictions_total counter")

        # Connection pool metrics
        lines.append(
            "# HELP proxy_api_connection_pool_active Active connections"
        )
        lines.append("# TYPE proxy_api_connection_pool_active gauge")
        lines.append(
            "# HELP proxy_api_connection_pool_max Maximum connections"
        )
        lines.append("# TYPE proxy_api_connection_pool_max gauge")
        lines.append(
            "# HELP proxy_api_connection_pool_errors_total Connection pool errors"
        )
        lines.append("# TYPE proxy_api_connection_pool_errors_total counter")

        # Configuration metrics
        lines.append(
            "# HELP proxy_api_config_loads_total Total configuration loads"
        )
        lines.append("# TYPE proxy_api_config_loads_total counter")
        lines.append(
            "# HELP proxy_api_config_load_time_avg_ms Average config load time in ms"
        )
        lines.append("# TYPE proxy_api_config_load_time_avg_ms gauge")
        lines.append(
            "# HELP proxy_api_config_file_size_bytes Configuration file size in bytes"
        )
        lines.append("# TYPE proxy_api_config_file_size_bytes gauge")

        # System health metrics
        lines.append(
            "# HELP proxy_api_system_cpu_percent CPU usage percentage"
        )
        lines.append("# TYPE proxy_api_system_cpu_percent gauge")
        lines.append(
            "# HELP proxy_api_system_memory_percent Memory usage percentage"
        )
        lines.append("# TYPE proxy_api_system_memory_percent gauge")
        lines.append(
            "# HELP proxy_api_system_memory_used_mb Memory used in MB"
        )
        lines.append("# TYPE proxy_api_system_memory_used_mb gauge")
        lines.append(
            "# HELP proxy_api_system_disk_percent Disk usage percentage"
        )
        lines.append("# TYPE proxy_api_system_disk_percent gauge")

        # Error rate metrics
        lines.append("# HELP proxy_api_errors_total Total errors")
        lines.append("# TYPE proxy_api_errors_total counter")
        lines.append(
            "# HELP proxy_api_errors_connection_total Connection errors"
        )
        lines.append("# TYPE proxy_api_errors_connection_total counter")
        lines.append("# HELP proxy_api_errors_timeout_total Timeout errors")
        lines.append("# TYPE proxy_api_errors_timeout_total counter")
        lines.append(
            "# HELP proxy_api_errors_rate_limit_total Rate limit errors"
        )
        lines.append("# TYPE proxy_api_errors_rate_limit_total counter")
        lines.append(
            "# HELP proxy_api_errors_server_total Server errors (5xx)"
        )
        lines.append("# TYPE proxy_api_errors_server_total counter")
        lines.append(
            "# HELP proxy_api_errors_client_total Client errors (4xx)"
        )
        lines.append("# TYPE proxy_api_errors_client_total counter")

        # Cache performance metrics
        lines.append(
            "# HELP proxy_api_cache_hit_rate Cache hit rate percentage"
        )
        lines.append("# TYPE proxy_api_cache_hit_rate gauge")
        lines.append(
            "# HELP proxy_api_cache_entries_total Total cache entries"
        )
        lines.append("# TYPE proxy_api_cache_entries_total gauge")
        lines.append(
            "# HELP proxy_api_cache_memory_usage_mb Cache memory usage in MB"
        )
        lines.append("# TYPE proxy_api_cache_memory_usage_mb gauge")
        lines.append(
            "# HELP proxy_api_cache_evictions_total Total cache evictions"
        )
        lines.append("# TYPE proxy_api_cache_evictions_total counter")

        # Connection pool metrics
        lines.append(
            "# HELP proxy_api_connection_pool_active Active connections"
        )
        lines.append("# TYPE proxy_api_connection_pool_active gauge")
        lines.append(
            "# HELP proxy_api_connection_pool_max Maximum connections"
        )
        lines.append("# TYPE proxy_api_connection_pool_max gauge")
        lines.append(
            "# HELP proxy_api_connection_pool_errors_total Connection pool errors"
        )
        lines.append("# TYPE proxy_api_connection_pool_errors_total counter")

        # Configuration metrics
        lines.append(
            "# HELP proxy_api_config_loads_total Total configuration loads"
        )
        lines.append("# TYPE proxy_api_config_loads_total counter")
        lines.append(
            "# HELP proxy_api_config_load_time_avg_ms Average config load time in ms"
        )
        lines.append("# TYPE proxy_api_config_load_time_avg_ms gauge")
        lines.append(
            "# HELP proxy_api_config_file_size_bytes Configuration file size in bytes"
        )
        lines.append("# TYPE proxy_api_config_file_size_bytes gauge")

        # System health metrics
        lines.append(
            "# HELP proxy_api_system_cpu_percent CPU usage percentage"
        )
        lines.append("# TYPE proxy_api_system_cpu_percent gauge")
        lines.append(
            "# HELP proxy_api_system_memory_percent Memory usage percentage"
        )
        lines.append("# TYPE proxy_api_system_memory_percent gauge")
        lines.append(
            "# HELP proxy_api_system_memory_used_mb Memory used in MB"
        )
        lines.append("# TYPE proxy_api_system_memory_used_mb gauge")
        lines.append(
            "# HELP proxy_api_system_disk_percent Disk usage percentage"
        )
        lines.append("# TYPE proxy_api_system_disk_percent gauge")

        # Error rate metrics
        lines.append("# HELP proxy_api_errors_total Total errors")
        lines.append("# TYPE proxy_api_errors_total counter")
        lines.append(
            "# HELP proxy_api_errors_connection_total Connection errors"
        )
        lines.append("# TYPE proxy_api_errors_connection_total counter")
        lines.append("# HELP proxy_api_errors_timeout_total Timeout errors")
        lines.append("# TYPE proxy_api_errors_timeout_total counter")
        lines.append(
            "# HELP proxy_api_errors_rate_limit_total Rate limit errors"
        )
        lines.append("# TYPE proxy_api_errors_rate_limit_total counter")
        lines.append(
            "# HELP proxy_api_errors_server_total Server errors (5xx)"
        )
        lines.append("# TYPE proxy_api_errors_server_total counter")
        lines.append(
            "# HELP proxy_api_errors_client_total Client errors (4xx)"
        )
        lines.append("# TYPE proxy_api_errors_client_total counter")

        # Use the most recent data point
        if history:
            latest = history[-1]

            lines.append(f"proxy_api_requests_total {latest.total_requests}")
            lines.append(
                f"proxy_api_requests_successful_total {latest.successful_requests}"
            )
            lines.append(
                f"proxy_api_requests_failed_total {latest.failed_requests}"
            )

            # Provider-specific metrics
            for provider_name, provider_data in latest.providers.items():
                if isinstance(provider_data, dict):
                    success_rate = provider_data.get("success_rate", 0)
                    avg_response_time = provider_data.get(
                        "avg_response_time", 0
                    )

                    lines.append(
                        f'proxy_api_provider_success_rate{{provider="{provider_name}"}} {success_rate}'
                    )
                    lines.append(
                        f'proxy_api_response_time_avg{{provider="{provider_name}"}} {avg_response_time}'
                    )

                    # Model-specific metrics within each provider
                    models = provider_data.get("models", {})
                    if isinstance(models, dict):
                        for model_name, model_data in models.items():
                            if isinstance(model_data, dict):
                                model_requests = model_data.get(
                                    "total_requests", 0
                                )
                                model_successful = model_data.get(
                                    "successful_requests", 0
                                )
                                model_failed = model_data.get(
                                    "failed_requests", 0
                                )
                                model_avg_time = model_data.get(
                                    "avg_response_time", 0
                                )
                                model_tokens = model_data.get(
                                    "total_tokens", 0
                                )

                                # Calculate model success rate
                                model_success_rate = (
                                    model_successful / model_requests
                                    if model_requests > 0
                                    else 0
                                )

                                lines.append(
                                    f'proxy_api_model_requests_total{{provider="{provider_name}",model="{model_name}"}} {model_requests}'
                                )
                                lines.append(
                                    f'proxy_api_model_success_rate{{provider="{provider_name}",model="{model_name}"}} {model_success_rate}'
                                )
                                lines.append(
                                    f'proxy_api_model_response_time_avg{{provider="{provider_name}",model="{model_name}"}} {model_avg_time}'
                                )
                                lines.append(
                                    f'proxy_api_model_tokens_total{{provider="{provider_name}",model="{model_name}"}} {model_tokens}'
                                )

                            # Add cache performance metrics
                            if hasattr(latest, "cache_performance"):
                                cache_data = latest.get(
                                    "cache_performance", {}
                                )
                                lines.append(
                                    f'proxy_api_cache_hit_rate {cache_data.get("hit_rate", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_cache_entries_total {cache_data.get("entries", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_cache_memory_usage_mb {cache_data.get("memory_usage_mb", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_cache_evictions_total {cache_data.get("evictions", 0)}'
                                )

                            # Add connection pool metrics
                            if hasattr(latest, "connection_pool"):
                                pool_data = latest.get("connection_pool", {})
                                lines.append(
                                    f'proxy_api_connection_pool_active {pool_data.get("active_connections", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_connection_pool_max {pool_data.get("max_connections", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_connection_pool_errors_total {pool_data.get("error_count", 0)}'
                                )

                            # Add configuration metrics
                            if hasattr(latest, "configuration"):
                                config_data = latest.get("configuration", {})
                                lines.append(
                                    f'proxy_api_config_loads_total {config_data.get("total_loads", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_config_load_time_avg_ms {config_data.get("avg_load_time_ms", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_config_file_size_bytes {config_data.get("config_file_size", 0)}'
                                )

                            # Add system health metrics
                            if hasattr(latest, "system_health"):
                                health_data = latest.get("system_health", {})
                                lines.append(
                                    f'proxy_api_system_cpu_percent {health_data.get("cpu_percent", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_system_memory_percent {health_data.get("memory_percent", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_system_memory_used_mb {health_data.get("memory_used_mb", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_system_disk_percent {health_data.get("disk_percent", 0)}'
                                )

                            # Add error rate metrics
                            if hasattr(latest, "error_rates"):
                                error_data = latest.get("error_rates", {})
                                lines.append(
                                    f'proxy_api_errors_total {error_data.get("total_errors", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_errors_connection_total {error_data.get("connection_errors", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_errors_timeout_total {error_data.get("timeout_errors", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_errors_rate_limit_total {error_data.get("rate_limit_errors", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_errors_server_total {error_data.get("server_errors", 0)}'
                                )
                                lines.append(
                                    f'proxy_api_errors_client_total {error_data.get("client_errors", 0)}'
                                )

                            return "\n".join(lines)


class MetricsCollector:
    """Enhanced metrics collector with persistence and advanced features"""

    def __init__(
        self,
        enable_persistence: bool = True,
        persistence_path: Optional[str] = None,
        enable_sampling: bool = True,
        sampling_rate: float = 0.1,
        enable_adaptive_sampling: bool = True,
    ):
        self.providers: Dict[str, ProviderMetrics] = {}
        self.summarization_metrics = SummarizationMetrics()
        self.request_history = deque(maxlen=10000)  # Keep last 10k requests
        self.start_time = datetime.now()

        # New enhanced metrics
        self.cache_metrics = CachePerformanceMetrics()
        self.connection_pool_metrics = ConnectionPoolMetrics()
        self.config_metrics = ConfigurationMetrics()
        self.system_health_metrics = SystemHealthMetrics()
        self.error_rate_metrics = ErrorRateMetrics()

        # Sampling configuration
        self.enable_sampling = enable_sampling
        self.sampling_rate = sampling_rate  # Sample 10% of requests by default
        self._sampling_counter = 0

        # Adaptive sampling configuration
        self.enable_adaptive_sampling = True
        self.adaptive_sampling_min_rate = 0.01  # Minimum 1% sampling
        self.adaptive_sampling_max_rate = 0.5  # Maximum 50% sampling
        self.adaptive_sampling_target_overhead = 0.02  # Target 2% overhead

        # Request volume tracking for adaptive sampling
        self._request_timestamps = deque(
            maxlen=1000
        )  # Track last 1000 request timestamps
        self._adaptive_update_interval = (
            60  # Update sampling rate every 60 seconds
        )
        self._last_adaptive_update = 0
        self._adaptive_task = None

        # Persistence
        self.persistence = (
            MetricsPersistence(persistence_path)
            if enable_persistence
            else None
        )
        self._last_save_time = 0
        self._save_interval = 300  # Save every 5 minutes

        # Background save task - will be started when event loop is available
        self._save_task = None
        self._system_health_task = None
        if self.persistence:
            self._start_background_save()

        # Start system health monitoring
        self._start_system_health_monitoring()

    def _start_background_save(self):
        """Start the background save task if event loop is available."""
        try:
            loop = asyncio.get_running_loop()
            self._save_task = loop.create_task(self._background_save())
        except RuntimeError:
            # No event loop running, will start later when needed
            pass

    def _start_system_health_monitoring(self):
        """Start the system health monitoring task if event loop is available."""
        try:
            loop = asyncio.get_running_loop()
            self._system_health_task = loop.create_task(
                self._background_system_health()
            )
            if self.enable_adaptive_sampling:
                self._adaptive_task = loop.create_task(
                    self._background_adaptive_sampling()
                )
        except RuntimeError:
            # No event loop running, will start later when needed
            pass

    async def _background_save(self):
        """Background task to periodically save metrics"""
        while True:
            try:
                await asyncio.sleep(self._save_interval)
                if time.time() - self._last_save_time >= self._save_interval:
                    self._save_metrics()
            except Exception as e:
                logger.error("Background save failed", error=str(e))
                await asyncio.sleep(60)  # Retry after 1 minute

    async def _background_system_health(self):
        """Background task to periodically update system health metrics"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                self.update_system_health()
            except Exception as e:
                logger.error(
                    "Background system health update failed", error=str(e)
                )
                await asyncio.sleep(60)  # Retry after 1 minute

    async def _background_adaptive_sampling(self):
        """Background task to periodically adjust sampling rate based on system load"""
        while True:
            try:
                await asyncio.sleep(self._adaptive_update_interval)
                if self.enable_adaptive_sampling:
                    self._adjust_sampling_rate()
            except Exception as e:
                logger.error(
                    "Background adaptive sampling update failed", error=str(e)
                )
                await asyncio.sleep(60)  # Retry after 1 minute

    def _save_metrics(self):
        """Save current metrics to persistence"""
        if self.persistence:
            metrics_data = self.get_all_stats()
            self.persistence.save_metrics(metrics_data)
            self._last_save_time = time.time()

    def get_or_create_provider(self, provider_name: str) -> ProviderMetrics:
        """Get or create provider metrics"""
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderMetrics(name=provider_name)
        return self.providers[provider_name]

    def record_request(
        self,
        provider_name: str,
        success: bool,
        response_time: float,
        tokens: int = 0,
        error_type: str = None,
        model_name: str = None,
    ):
        """Record a request for a provider with optional sampling"""
        provider = self.get_or_create_provider(provider_name)

        # Track request timestamp for volume calculation
        self._request_timestamps.append(time.time())

        # Always update basic counters
        provider.total_requests += 1

        if success:
            provider.successful_requests += 1
        else:
            provider.failed_requests += 1
            if error_type:
                provider.errors[error_type] += 1
                # Update detailed error metrics
                self._categorize_error(error_type)

        # Update tokens
        provider.total_tokens += tokens

        # Determine if this request should be sampled for detailed metrics
        should_sample = (
            not self.enable_sampling
            or (self._sampling_counter % int(1 / self.sampling_rate)) == 0
        )
        self._sampling_counter += 1

        if should_sample:
            # Update detailed metrics only for sampled requests
            provider.min_response_time = min(
                provider.min_response_time, response_time
            )
            provider.max_response_time = max(
                provider.max_response_time, response_time
            )

            if success:
                # Update response time (moving average)
                if provider.avg_response_time == 0:
                    provider.avg_response_time = response_time
                else:
                    provider.avg_response_time = (
                        provider.avg_response_time * 0.9
                    ) + (response_time * 0.1)

            # Update model-specific metrics
            if model_name:
                model_metrics = provider.get_or_create_model(model_name)
                model_metrics.total_requests += 1
                model_metrics.min_response_time = min(
                    model_metrics.min_response_time, response_time
                )
                model_metrics.max_response_time = max(
                    model_metrics.max_response_time, response_time
                )

                if success:
                    model_metrics.successful_requests += 1
                    if model_metrics.avg_response_time == 0:
                        model_metrics.avg_response_time = response_time
                    else:
                        model_metrics.avg_response_time = (
                            model_metrics.avg_response_time * 0.9
                        ) + (response_time * 0.1)
                else:
                    model_metrics.failed_requests += 1
                    if error_type:
                        model_metrics.errors[error_type] += 1

                model_metrics.total_tokens += tokens

            # Add to request history (sampled)
            self.request_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "provider": provider_name,
                    "model": model_name,
                    "success": success,
                    "response_time": response_time,
                    "tokens": tokens,
                    "error_type": error_type,
                    "sampled": True,
                }
            )
        else:
            # Add minimal entry to request history for non-sampled requests
            self.request_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "provider": provider_name,
                    "model": model_name,
                    "success": success,
                    "sampled": False,
                }
            )

    def _categorize_error(self, error_type: str):
        """Categorize error for detailed error rate metrics"""
        self.error_rate_metrics.total_errors += 1

        error_lower = error_type.lower() if error_type else ""
        if "connect" in error_lower or "connection" in error_lower:
            self.error_rate_metrics.connection_errors += 1
        elif "timeout" in error_lower:
            self.error_rate_metrics.timeout_errors += 1
        elif "rate" in error_lower or "limit" in error_lower:
            self.error_rate_metrics.rate_limit_errors += 1
        elif "auth" in error_lower or "unauthorized" in error_lower:
            self.error_rate_metrics.authentication_errors += 1
        elif error_type and error_type.startswith("5"):
            self.error_rate_metrics.server_errors += 1
        elif error_type and error_type.startswith("4"):
            self.error_rate_metrics.client_errors += 1
        else:
            self.error_rate_metrics.other_errors += 1

        # Update error rate percentage
        total_requests = sum(p.total_requests for p in self.providers.values())
        if total_requests > 0:
            self.error_rate_metrics.error_rate_percent = (
                self.error_rate_metrics.total_errors / total_requests
            ) * 100

    def get_provider_stats(self, provider_name: str) -> Dict[str, Any]:
        """Get detailed stats for a provider"""
        provider = self.get_or_create_provider(provider_name)
        stats = asdict(provider)
        # Convert defaultdict to regular dict for JSON serialization
        stats["errors"] = dict(stats["errors"])
        return stats

    def record_summary(self, is_cache_hit: bool, latency: float = 0.0):
        """Record summarization metrics"""
        self.summarization_metrics.record_summary(is_cache_hit, latency)

    def update_cache_metrics(self, cache_stats: Dict[str, Any]):
        """Update cache performance metrics"""
        self.cache_metrics.hit_rate = cache_stats.get("hit_rate", 0)
        self.cache_metrics.total_requests = cache_stats.get(
            "total_requests", 0
        )
        self.cache_metrics.cache_hits = cache_stats.get("cache_hits", 0)
        self.cache_metrics.cache_misses = cache_stats.get("cache_misses", 0)
        self.cache_metrics.entries = cache_stats.get("entries", 0)
        self.cache_metrics.memory_usage_mb = cache_stats.get(
            "memory_usage_mb", 0
        )
        self.cache_metrics.max_memory_mb = cache_stats.get("max_memory_mb", 0)
        self.cache_metrics.evictions = cache_stats.get("evictions", 0)
        self.cache_metrics.last_updated = time.time()

    def update_connection_pool_metrics(self, pool_stats: Dict[str, Any]):
        """Update connection pool metrics"""
        self.connection_pool_metrics.max_keepalive_connections = (
            pool_stats.get("max_keepalive_connections", 0)
        )
        self.connection_pool_metrics.max_connections = pool_stats.get(
            "max_connections", 0
        )
        self.connection_pool_metrics.active_connections = pool_stats.get(
            "active_connections", 0
        )
        self.connection_pool_metrics.available_connections = pool_stats.get(
            "available_connections", 0
        )
        self.connection_pool_metrics.pending_requests = pool_stats.get(
            "pending_requests", 0
        )
        self.connection_pool_metrics.total_requests = pool_stats.get(
            "total_requests", 0
        )
        self.connection_pool_metrics.error_count = pool_stats.get(
            "error_count", 0
        )
        self.connection_pool_metrics.avg_response_time_ms = pool_stats.get(
            "avg_response_time_ms", 0
        )

    def record_config_load(
        self,
        load_time_ms: float,
        success: bool,
        config_file_size: int = 0,
        providers_count: int = 0,
    ):
        """Record configuration loading metrics"""
        self.config_metrics.total_loads += 1
        if success:
            self.config_metrics.successful_loads += 1
            # Update average load time (moving average)
            if self.config_metrics.avg_load_time_ms == 0:
                self.config_metrics.avg_load_time_ms = load_time_ms
            else:
                self.config_metrics.avg_load_time_ms = (
                    self.config_metrics.avg_load_time_ms * 0.9
                ) + (load_time_ms * 0.1)
        else:
            self.config_metrics.failed_loads += 1

        self.config_metrics.last_load_time = time.time()
        self.config_metrics.config_file_size = config_file_size
        self.config_metrics.providers_count = providers_count

    def update_system_health(self):
        """Update system health metrics"""
        try:
            # CPU usage
            self.system_health_metrics.cpu_percent = psutil.cpu_percent(
                interval=1
            )

            # Memory usage
            memory = psutil.virtual_memory()
            self.system_health_metrics.memory_percent = memory.percent
            self.system_health_metrics.memory_used_mb = memory.used / (
                1024 * 1024
            )
            self.system_health_metrics.memory_total_mb = memory.total / (
                1024 * 1024
            )

            # Disk usage
            disk = psutil.disk_usage("/")
            self.system_health_metrics.disk_percent = disk.percent
            self.system_health_metrics.disk_used_gb = disk.used / (
                1024 * 1024 * 1024
            )
            self.system_health_metrics.disk_total_gb = disk.total / (
                1024 * 1024 * 1024
            )

            # Network connections
            self.system_health_metrics.network_connections = len(
                psutil.net_connections()
            )

            # Process information
            process = psutil.Process()
            self.system_health_metrics.open_files = len(process.open_files())
            self.system_health_metrics.threads_count = process.num_threads()

            self.system_health_metrics.last_updated = time.time()

        except Exception as e:
            logger.error(
                "Failed to update system health metrics", error=str(e)
            )

    def _calculate_request_volume(self) -> float:
        """Calculate current request volume (requests per second)"""
        if len(self._request_timestamps) < 2:
            return 0.0

        # Calculate requests per second over the last minute
        now = time.time()
        one_minute_ago = now - 60

        # Count requests in the last minute
        recent_requests = sum(
            1 for ts in self._request_timestamps if ts > one_minute_ago
        )
        return recent_requests / 60.0

    def _calculate_system_load_score(self) -> float:
        """Calculate system load score (0.0 to 1.0)"""
        cpu_weight = 0.4
        memory_weight = 0.4
        volume_weight = 0.2

        # Normalize CPU and memory (already in percent)
        cpu_score = self.system_health_metrics.cpu_percent / 100.0
        memory_score = self.system_health_metrics.memory_percent / 100.0

        # Normalize request volume (assume max 1000 req/sec is high load)
        request_volume = self._calculate_request_volume()
        volume_score = min(request_volume / 1000.0, 1.0)

        # Calculate weighted score
        load_score = (
            cpu_score * cpu_weight
            + memory_score * memory_weight
            + volume_score * volume_weight
        )

        return min(load_score, 1.0)

    def _adjust_sampling_rate(self):
        """Adjust sampling rate based on current system load"""
        if not self.enable_adaptive_sampling:
            return

        load_score = self._calculate_system_load_score()
        request_volume = self._calculate_request_volume()

        # Calculate target sampling rate
        # Higher load = lower sampling rate
        # Lower load = higher sampling rate
        if load_score < 0.3:
            # Low load: increase sampling for better observability
            target_rate = self.adaptive_sampling_max_rate
        elif load_score < 0.7:
            # Medium load: maintain current rate or slight adjustment
            target_rate = self.sampling_rate
        else:
            # High load: decrease sampling to reduce overhead
            target_rate = self.adaptive_sampling_min_rate

        # Smooth transitions to avoid sudden changes
        smoothing_factor = 0.3
        new_rate = (
            self.sampling_rate * (1 - smoothing_factor)
            + target_rate * smoothing_factor
        )

        # Ensure within bounds
        new_rate = max(
            self.adaptive_sampling_min_rate,
            min(self.adaptive_sampling_max_rate, new_rate),
        )

        # Only update if change is significant (>1%)
        if abs(new_rate - self.sampling_rate) > 0.01:
            old_rate = self.sampling_rate
            self.sampling_rate = new_rate
            self._last_adaptive_update = time.time()

            logger.info(
                "Adaptive sampling rate adjusted",
                old_rate=f"{old_rate:.3f}",
                new_rate=f"{new_rate:.3f}",
                load_score=f"{load_score:.3f}",
                request_volume=f"{request_volume:.1f}",
                cpu_percent=f"{self.system_health_metrics.cpu_percent:.1f}",
                memory_percent=f"{self.system_health_metrics.memory_percent:.1f}",
            )

    def get_all_stats(self) -> Dict[str, Any]:
        """Get stats for all providers"""
        total_requests = sum(p.total_requests for p in self.providers.values())
        successful_requests = sum(
            p.successful_requests for p in self.providers.values()
        )
        failed_requests = sum(
            p.failed_requests for p in self.providers.values()
        )

        # Calculate sampling statistics
        sampled_requests = sum(
            1 for req in self.request_history if req.get("sampled", False)
        )
        total_history_requests = len(self.request_history)

        return {
            "providers": {
                name: self.get_provider_stats(name)
                for name in self.providers.keys()
            },
            "summarization": asdict(self.summarization_metrics),
            "cache_performance": asdict(self.cache_metrics),
            "connection_pool": asdict(self.connection_pool_metrics),
            "configuration": asdict(self.config_metrics),
            "system_health": asdict(self.system_health_metrics),
            "error_rates": asdict(self.error_rate_metrics),
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "overall_success_rate": (
                (successful_requests / total_requests)
                if total_requests > 0
                else 0
            ),
            "request_history_size": len(self.request_history),
            "sampling": {
                "enabled": self.enable_sampling,
                "sampling_rate": self.sampling_rate,
                "sampled_requests": sampled_requests,
                "total_history_requests": total_history_requests,
                "sampling_ratio": (
                    sampled_requests / total_history_requests
                    if total_history_requests > 0
                    else 0
                ),
                "adaptive": {
                    "enabled": self.enable_adaptive_sampling,
                    "min_rate": self.adaptive_sampling_min_rate,
                    "max_rate": self.adaptive_sampling_max_rate,
                    "target_overhead": self.adaptive_sampling_target_overhead,
                    "current_load_score": self._calculate_system_load_score(),
                    "current_request_volume": self._calculate_request_volume(),
                    "last_update": self._last_adaptive_update,
                },
            },
        }

    def get_model_stats(
        self, provider_name: str, model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get stats for a specific model"""
        provider = self.providers.get(provider_name)
        if not provider:
            return None

        model = provider.models.get(model_name)
        if not model:
            return None

        stats = asdict(model)
        stats["errors"] = dict(stats["errors"])
        return stats

    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format with enhanced per-model metrics"""
        if self.persistence:
            return self.persistence.get_prometheus_format()

        # Fallback to current metrics if no persistence
        lines = ["# Current metrics (no persistence configured)"]
        stats = self.get_all_stats()

        # Add HELP and TYPE declarations
        lines.extend(
            [
                "# HELP proxy_api_requests_total Total number of requests",
                "# TYPE proxy_api_requests_total counter",
                "# HELP proxy_api_requests_successful_total Total number of successful requests",
                "# TYPE proxy_api_requests_successful_total counter",
                "# HELP proxy_api_requests_failed_total Total number of failed requests",
                "# TYPE proxy_api_requests_failed_total counter",
                "# HELP proxy_api_response_time_avg Average response time in seconds",
                "# TYPE proxy_api_response_time_avg gauge",
                "# HELP proxy_api_provider_success_rate Success rate per provider",
                "# TYPE proxy_api_provider_success_rate gauge",
                "# HELP proxy_api_model_requests_total Total requests per model",
                "# TYPE proxy_api_model_requests_total counter",
                "# HELP proxy_api_model_success_rate Success rate per model",
                "# TYPE proxy_api_model_success_rate gauge",
                "# HELP proxy_api_model_response_time_avg Average response time per model in seconds",
                "# TYPE proxy_api_model_response_time_avg gauge",
                "# HELP proxy_api_model_tokens_total Total tokens used per model",
                "# TYPE proxy_api_model_tokens_total counter",
            ]
        )

        lines.append(f'proxy_api_requests_total {stats["total_requests"]}')
        lines.append(
            f'proxy_api_requests_successful_total {stats["successful_requests"]}'
        )
        lines.append(
            f'proxy_api_requests_failed_total {stats["failed_requests"]}'
        )

        for provider_name, provider_data in stats["providers"].items():
            success_rate = provider_data.get("success_rate", 0)
            avg_response_time = provider_data.get("avg_response_time", 0)

            lines.append(
                f'proxy_api_provider_success_rate{{provider="{provider_name}"}} {success_rate}'
            )
            lines.append(
                f'proxy_api_response_time_avg{{provider="{provider_name}"}} {avg_response_time}'
            )

            # Model-specific metrics
            models = provider_data.get("models", {})
            if isinstance(models, dict):
                for model_name, model_data in models.items():
                    if isinstance(model_data, dict):
                        model_requests = model_data.get("total_requests", 0)
                        model_successful = model_data.get(
                            "successful_requests", 0
                        )
                        model_failed = model_data.get("failed_requests", 0)
                        model_avg_time = model_data.get("avg_response_time", 0)
                        model_tokens = model_data.get("total_tokens", 0)

                        # Calculate model success rate
                        model_success_rate = (
                            model_successful / model_requests
                            if model_requests > 0
                            else 0
                        )

                        lines.append(
                            f'proxy_api_model_requests_total{{provider="{provider_name}",model="{model_name}"}} {model_requests}'
                        )
                        lines.append(
                            f'proxy_api_model_success_rate{{provider="{provider_name}",model="{model_name}"}} {model_success_rate}'
                        )
                        lines.append(
                            f'proxy_api_model_response_time_avg{{provider="{provider_name}",model="{model_name}"}} {model_avg_time}'
                        )
                        lines.append(
                            f'proxy_api_model_tokens_total{{provider="{provider_name}",model="{model_name}"}} {model_tokens}'
                        )

        # Add cache performance metrics
        lines.append(f"proxy_api_cache_hit_rate {self.cache_metrics.hit_rate}")
        lines.append(
            f"proxy_api_cache_entries_total {self.cache_metrics.entries}"
        )
        lines.append(
            f"proxy_api_cache_memory_usage_mb {self.cache_metrics.memory_usage_mb}"
        )
        lines.append(
            f"proxy_api_cache_evictions_total {self.cache_metrics.evictions}"
        )

        # Add connection pool metrics
        lines.append(
            f"proxy_api_connection_pool_active {self.connection_pool_metrics.active_connections}"
        )
        lines.append(
            f"proxy_api_connection_pool_max {self.connection_pool_metrics.max_connections}"
        )
        lines.append(
            f"proxy_api_connection_pool_errors_total {self.connection_pool_metrics.error_count}"
        )

        # Add configuration metrics
        lines.append(
            f"proxy_api_config_loads_total {self.config_metrics.total_loads}"
        )
        lines.append(
            f"proxy_api_config_load_time_avg_ms {self.config_metrics.avg_load_time_ms}"
        )
        lines.append(
            f"proxy_api_config_file_size_bytes {self.config_metrics.config_file_size}"
        )

        # Add system health metrics
        lines.append(
            f"proxy_api_system_cpu_percent {self.system_health_metrics.cpu_percent}"
        )
        lines.append(
            f"proxy_api_system_memory_percent {self.system_health_metrics.memory_percent}"
        )
        lines.append(
            f"proxy_api_system_memory_used_mb {self.system_health_metrics.memory_used_mb}"
        )
        lines.append(
            f"proxy_api_system_disk_percent {self.system_health_metrics.disk_percent}"
        )

        # Add error rate metrics
        lines.append(
            f"proxy_api_errors_total {self.error_rate_metrics.total_errors}"
        )
        lines.append(
            f"proxy_api_errors_connection_total {self.error_rate_metrics.connection_errors}"
        )
        lines.append(
            f"proxy_api_errors_timeout_total {self.error_rate_metrics.timeout_errors}"
        )
        lines.append(
            f"proxy_api_errors_rate_limit_total {self.error_rate_metrics.rate_limit_errors}"
        )
        lines.append(
            f"proxy_api_errors_server_total {self.error_rate_metrics.server_errors}"
        )
        lines.append(
            f"proxy_api_errors_client_total {self.error_rate_metrics.client_errors}"
        )

        return "\n".join(lines)

    def get_metrics_history(self, days: int = 7) -> List[MetricsHistory]:
        """Get historical metrics data"""
        if self.persistence:
            return self.persistence.load_metrics_history(days)
        return []

    def reset_stats(self):
        """Reset all metrics"""
        self.providers.clear()
        self.request_history.clear()
        self.start_time = datetime.now()
        self.summarization_metrics = SummarizationMetrics()

    async def shutdown(self):
        """Shutdown the collector and save final metrics"""
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass

        if self._system_health_task:
            self._system_health_task.cancel()
            try:
                await self._system_health_task
            except asyncio.CancelledError:
                pass

        if self._adaptive_task:
            self._adaptive_task.cancel()
            try:
                await self._adaptive_task
            except asyncio.CancelledError:
                pass

        # Final save
        self._save_metrics()


# Global metrics collector instance
metrics_collector = MetricsCollector()
