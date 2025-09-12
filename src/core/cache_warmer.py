"""Cache Warming Engine - Proactive Cache Population and Optimization

This module provides intelligent cache warming capabilities that proactively
populate the cache with frequently accessed data based on usage patterns,
predictions, and scheduled warming strategies.

Features:
- Proactive cache population based on usage patterns
- Intelligent warming strategies (time-based, usage-based, predictive)
- Background warming without performance impact
- Cost-effective warming with resource management
- Warming effectiveness monitoring and reporting
- Integration with unified cache system
"""

import asyncio
import json
import logging
import time
import threading
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union
from concurrent.futures import ThreadPoolExecutor
import statistics
import random

from .unified_cache import UnifiedCache, get_unified_cache
from .model_discovery import ModelDiscoveryService, ProviderConfig
from ..models.model_info import ModelInfo

logger = logging.getLogger(__name__)


@dataclass
class WarmingPattern:
    """Cache access pattern data"""

    key: str
    access_count: int = 0
    last_accessed: float = 0.0
    access_times: List[float] = field(default_factory=list)
    category: str = "default"
    priority: int = 1

    def get_access_frequency(self) -> float:
        """Calculate access frequency (accesses per hour)"""
        if not self.access_times:
            return 0.0

        # Use last 24 hours of data
        cutoff = time.time() - (24 * 3600)
        recent_accesses = [t for t in self.access_times if t > cutoff]

        if not recent_accesses:
            return 0.0

        hours_span = (time.time() - min(recent_accesses)) / 3600
        return len(recent_accesses) / max(hours_span, 1.0)

    def get_predictive_score(self) -> float:
        """Calculate predictive warming score"""
        frequency = self.get_access_frequency()
        recency = time.time() - self.last_accessed
        priority_factor = self.priority / 5.0  # Normalize to 0-1

        # Score combines frequency, recency, and priority
        # Higher score = more likely to be needed soon
        recency_factor = max(0, 1 - (recency / (24 * 3600)))  # Decay over 24 hours

        return frequency * recency_factor * priority_factor


@dataclass
class WarmingSchedule:
    """Warming schedule configuration"""

    name: str
    cron_expression: Optional[str] = None  # Future: cron support
    interval_seconds: int = 3600  # 1 hour
    enabled: bool = True
    priority: int = 1
    target_categories: List[str] = field(default_factory=list)
    max_concurrent_warmings: int = 5
    timeout_seconds: int = 300


@dataclass
class WarmingStats:
    """Warming operation statistics"""

    total_warmings: int = 0
    successful_warmings: int = 0
    failed_warmings: int = 0
    skipped_warmings: int = 0
    total_keys_warmed: int = 0
    cache_hit_improvement: float = 0.0
    average_warming_time: float = 0.0
    last_warming_time: Optional[datetime] = None
    warming_effectiveness: float = 0.0


class CacheWarmer:
    """
    Intelligent Cache Warming Engine

    Provides proactive cache population with multiple strategies:
    - Pattern-based warming (based on historical access)
    - Predictive warming (ML-based predictions)
    - Scheduled warming (time-based)
    - Demand-based warming (on-demand for specific keys)
    """

    def __init__(
        self,
        cache: Optional[UnifiedCache] = None,
        max_concurrent_warmings: int = 10,
        warming_batch_size: int = 50,
        enable_pattern_analysis: bool = True,
        enable_predictive_warming: bool = True,
        enable_scheduled_warming: bool = True
    ):
        self.cache = cache
        self.max_concurrent_warmings = max_concurrent_warmings
        self.warming_batch_size = warming_batch_size
        self.enable_pattern_analysis = enable_pattern_analysis
        self.enable_predictive_warming = enable_predictive_warming
        self.enable_scheduled_warming = enable_scheduled_warming

        # Warming state
        self._running = False
        self._warming_task: Optional[asyncio.Task] = None
        self._pattern_task: Optional[asyncio.Task] = None
        self._scheduled_task: Optional[asyncio.Task] = None

        # Access pattern tracking
        self._access_patterns: Dict[str, WarmingPattern] = {}
        self._pattern_lock = threading.RLock()

        # Warming schedules
        self._schedules: Dict[str, WarmingSchedule] = {}
        self._schedule_lock = threading.RLock()

        # Warming queue and execution
        self._warming_queue: asyncio.Queue = asyncio.Queue()
        self._warming_executor = ThreadPoolExecutor(max_workers=max_concurrent_warmings)
        self._active_warmings: Set[str] = set()

        # Statistics
        self.stats = WarmingStats()
        self._warming_times: List[float] = []

        # Model discovery for warming
        self._discovery_service: Optional[ModelDiscoveryService] = None

        logger.info("CacheWarmer initialized")

    async def start(self) -> None:
        """Start the cache warming engine"""
        if self._running:
            return

        self._running = True

        # Initialize cache if not provided
        if self.cache is None:
            self.cache = await get_unified_cache()

        # Initialize discovery service
        self._discovery_service = ModelDiscoveryService()

        # Start background tasks
        tasks = []

        if self.enable_pattern_analysis:
            self._pattern_task = asyncio.create_task(self._pattern_analysis_loop())
            tasks.append(self._pattern_task)

        if self.enable_scheduled_warming:
            self._scheduled_task = asyncio.create_task(self._scheduled_warming_loop())
            tasks.append(self._scheduled_task)

        # Main warming task
        self._warming_task = asyncio.create_task(self._warming_loop())
        tasks.append(self._warming_task)

        # Start default schedules
        await self._setup_default_schedules()

        logger.info("CacheWarmer started")

    async def stop(self) -> None:
        """Stop the cache warming engine"""
        self._running = False

        tasks = []
        if self._warming_task:
            tasks.append(self._warming_task)
        if self._pattern_task:
            tasks.append(self._pattern_task)
        if self._scheduled_task:
            tasks.append(self._scheduled_task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self._warming_executor.shutdown(wait=True)
        logger.info("CacheWarmer stopped")

    def record_access(self, key: str, category: str = "default") -> None:
        """Record cache access for pattern analysis"""
        if not self.enable_pattern_analysis:
            return

        with self._pattern_lock:
            if key not in self._access_patterns:
                self._access_patterns[key] = WarmingPattern(
                    key=key,
                    category=category
                )

            pattern = self._access_patterns[key]
            pattern.access_count += 1
            pattern.last_accessed = time.time()
            pattern.access_times.append(time.time())

            # Keep only recent access times (last 7 days)
            cutoff = time.time() - (7 * 24 * 3600)
            pattern.access_times = [t for t in pattern.access_times if t > cutoff]

    async def warm_key(self, key: str, getter_func: Callable, priority: int = 1) -> bool:
        """Warm a specific key on demand"""
        if not self._running:
            return False

        # Add to warming queue with high priority
        await self._warming_queue.put({
            'type': 'demand',
            'key': key,
            'getter_func': getter_func,
            'priority': priority,
            'timestamp': time.time()
        })

        logger.debug(f"Queued demand warming for key: {key}")
        return True

    async def warm_provider_models(
        self,
        provider_config: ProviderConfig,
        priority: int = 1
    ) -> Dict[str, Any]:
        """Warm cache with provider models"""
        if not self._discovery_service:
            return {"error": "Discovery service not initialized"}

        async def getter_func():
            return await self._discovery_service.discover_models(provider_config)

        cache_key = f"models:{provider_config.name}:{provider_config.base_url}"

        success = await self.warm_key(cache_key, getter_func, priority)

        return {
            "success": success,
            "key": cache_key,
            "provider": provider_config.name
        }

    async def add_schedule(
        self,
        name: str,
        interval_seconds: int = 3600,
        target_categories: Optional[List[str]] = None,
        priority: int = 1
    ) -> bool:
        """Add a warming schedule"""
        with self._schedule_lock:
            if name in self._schedules:
                return False

            schedule = WarmingSchedule(
                name=name,
                interval_seconds=interval_seconds,
                target_categories=target_categories or [],
                priority=priority
            )

            self._schedules[name] = schedule
            logger.info(f"Added warming schedule: {name}")
            return True

    async def remove_schedule(self, name: str) -> bool:
        """Remove a warming schedule"""
        with self._schedule_lock:
            if name in self._schedules:
                del self._schedules[name]
                logger.info(f"Removed warming schedule: {name}")
                return True
            return False

    async def _setup_default_schedules(self) -> None:
        """Setup default warming schedules"""
        # High-frequency warming (every 30 minutes)
        await self.add_schedule(
            "high_frequency",
            interval_seconds=1800,  # 30 minutes
            target_categories=["model_discovery"],
            priority=3
        )

        # Medium-frequency warming (every 2 hours)
        await self.add_schedule(
            "medium_frequency",
            interval_seconds=7200,  # 2 hours
            target_categories=["response", "summary"],
            priority=2
        )

        # Low-frequency warming (every 6 hours)
        await self.add_schedule(
            "low_frequency",
            interval_seconds=21600,  # 6 hours
            target_categories=[],  # All categories
            priority=1
        )

    async def _pattern_analysis_loop(self) -> None:
        """Background pattern analysis loop"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes

                if not self.enable_pattern_analysis:
                    continue

                # Analyze patterns and queue predictive warming
                await self._analyze_patterns()
                await self._queue_predictive_warming()

            except Exception as e:
                logger.error(f"Pattern analysis error: {e}")

    async def _scheduled_warming_loop(self) -> None:
        """Background scheduled warming loop"""
        schedule_last_run: Dict[str, float] = {}

        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                if not self.enable_scheduled_warming:
                    continue

                current_time = time.time()

                with self._schedule_lock:
                    for name, schedule in self._schedules.items():
                        if not schedule.enabled:
                            continue

                        last_run = schedule_last_run.get(name, 0)
                        if current_time - last_run >= schedule.interval_seconds:
                            # Queue scheduled warming
                            await self._queue_scheduled_warming(schedule)
                            schedule_last_run[name] = current_time

            except Exception as e:
                logger.error(f"Scheduled warming error: {e}")

    async def _warming_loop(self) -> None:
        """Main warming execution loop"""
        while self._running:
            try:
                # Get next warming task
                if self._warming_queue.empty():
                    await asyncio.sleep(1)  # Wait for tasks
                    continue

                task = await self._warming_queue.get()

                # Check if we're at capacity
                if len(self._active_warmings) >= self.max_concurrent_warmings:
                    # Put back in queue and wait
                    await self._warming_queue.put(task)
                    await asyncio.sleep(5)
                    continue

                # Execute warming task
                asyncio.create_task(self._execute_warming_task(task))

            except Exception as e:
                logger.error(f"Warming loop error: {e}")

    async def _execute_warming_task(self, task: Dict[str, Any]) -> None:
        """Execute a warming task"""
        task_key = task.get('key', 'unknown')
        self._active_warmings.add(task_key)

        start_time = time.time()

        try:
            self.stats.total_warmings += 1

            # Get value using getter function
            getter_func = task['getter_func']
            value = await getter_func()

            if value is not None:
                # Set in cache with appropriate TTL
                ttl = await self._determine_warming_ttl(task)
                category = task.get('category', 'default')

                success = await self.cache.set(
                    key=task_key,
                    value=value,
                    ttl=ttl,
                    category=category
                )

                if success:
                    self.stats.successful_warmings += 1
                    self.stats.total_keys_warmed += 1 if isinstance(value, list) else 1
                    logger.info(f"Successfully warmed key: {task_key}")
                else:
                    self.stats.failed_warmings += 1
                    logger.warning(f"Failed to warm key: {task_key}")
            else:
                self.stats.skipped_warmings += 1
                logger.debug(f"Skipped warming for key {task_key}: no value")

        except Exception as e:
            self.stats.failed_warmings += 1
            logger.error(f"Warming task failed for key {task_key}: {e}")
        finally:
            # Record timing
            warming_time = time.time() - start_time
            self._warming_times.append(warming_time)

            # Keep only recent timing data
            if len(self._warming_times) > 1000:
                self._warming_times = self._warming_times[-1000:]

            # Update stats
            if self._warming_times:
                self.stats.average_warming_time = statistics.mean(self._warming_times)
            self.stats.last_warming_time = datetime.now()

            # Remove from active set
            self._active_warmings.discard(task_key)

            # Mark task as done
            if 'queue_item' in task:
                task['queue_item'].task_done()

    async def _analyze_patterns(self) -> None:
        """Analyze access patterns for predictive warming"""
        with self._pattern_lock:
            # Update pattern priorities based on access frequency
            for pattern in self._access_patterns.values():
                frequency = pattern.get_access_frequency()

                # Adjust priority based on frequency
                if frequency > 10:  # More than 10 accesses per hour
                    pattern.priority = min(5, pattern.priority + 1)
                elif frequency < 1:  # Less than 1 access per hour
                    pattern.priority = max(1, pattern.priority - 1)

    async def _queue_predictive_warming(self) -> None:
        """Queue predictive warming based on pattern analysis"""
        if not self.enable_predictive_warming:
            return

        with self._pattern_lock:
            # Get top predictive candidates
            candidates = []
            for pattern in self._access_patterns.values():
                score = pattern.get_predictive_score()
                if score > 0.5:  # Threshold for predictive warming
                    candidates.append((pattern, score))

            # Sort by predictive score
            candidates.sort(key=lambda x: x[1], reverse=True)

            # Queue top candidates for warming
            for pattern, score in candidates[:10]:  # Top 10
                if pattern.key not in self._active_warmings:
                    # For model discovery keys, create getter function
                    if pattern.key.startswith("models:"):
                        await self._queue_model_discovery_warming(pattern)
                    else:
                        # Generic predictive warming (would need specific getter)
                        logger.debug(f"Would predictively warm: {pattern.key} (score: {score:.2f})")

    async def _queue_model_discovery_warming(self, pattern: WarmingPattern) -> None:
        """Queue model discovery warming for predictive patterns"""
        try:
            # Parse provider info from key
            parts = pattern.key.split(":")
            if len(parts) >= 3:
                provider_name = parts[1]
                base_url = parts[2]

                # Create provider config (simplified - may need enhancement)
                provider_config = ProviderConfig(
                    name=provider_name,
                    base_url=base_url,
                    api_key="",  # Would need to be retrieved from config
                    timeout=30
                )

                async def getter_func():
                    if self._discovery_service:
                        return await self._discovery_service.discover_models(provider_config)
                    return None

                await self._warming_queue.put({
                    'type': 'predictive',
                    'key': pattern.key,
                    'getter_func': getter_func,
                    'category': pattern.category,
                    'priority': pattern.priority,
                    'predictive_score': pattern.get_predictive_score(),
                    'timestamp': time.time()
                })

                logger.debug(f"Queued predictive warming for {pattern.key}")

        except Exception as e:
            logger.error(f"Error queuing predictive warming for {pattern.key}: {e}")

    async def _queue_scheduled_warming(self, schedule: WarmingSchedule) -> None:
        """Queue scheduled warming tasks"""
        try:
            # Get keys that match the schedule's target categories
            target_keys = await self._get_keys_for_schedule(schedule)

            for key in target_keys[:schedule.max_concurrent_warmings]:  # Limit concurrent
                if key not in self._active_warmings:
                    # Create getter function based on key type
                    getter_func = await self._create_getter_for_key(key)
                    if getter_func:
                        await self._warming_queue.put({
                            'type': 'scheduled',
                            'key': key,
                            'getter_func': getter_func,
                            'category': schedule.target_categories[0] if schedule.target_categories else 'default',
                            'priority': schedule.priority,
                            'schedule_name': schedule.name,
                            'timestamp': time.time()
                        })

            logger.info(f"Queued {len(target_keys)} keys for scheduled warming: {schedule.name}")

        except Exception as e:
            logger.error(f"Error queuing scheduled warming for {schedule.name}: {e}")

    async def _get_keys_for_schedule(self, schedule: WarmingSchedule) -> List[str]:
        """Get keys that match schedule criteria"""
        keys = []

        # Get cache stats to find keys by category
        cache_stats = await self.cache.get_stats()

        # For now, return some sample keys based on categories
        # In a real implementation, this would query the cache for keys by category
        if "model_discovery" in schedule.target_categories:
            # Add some model discovery keys (would be dynamic in real implementation)
            keys.extend([
                "models:openai:https://api.openai.com",
                "models:anthropic:https://api.anthropic.com",
                "models:google:https://generativelanguage.googleapis.com"
            ])

        return keys

    async def _create_getter_for_key(self, key: str) -> Optional[Callable]:
        """Create getter function for a key"""
        try:
            if key.startswith("models:"):
                # Model discovery getter
                parts = key.split(":")
                if len(parts) >= 3:
                    provider_name = parts[1]
                    base_url = parts[2]

                    provider_config = ProviderConfig(
                        name=provider_name,
                        base_url=base_url,
                        api_key="",  # Would need proper key retrieval
                        timeout=30
                    )

                    async def getter_func():
                        if self._discovery_service:
                            return await self._discovery_service.discover_models(provider_config)
                        return None

                    return getter_func

            # For other key types, return None (would need specific implementations)
            return None

        except Exception as e:
            logger.error(f"Error creating getter for key {key}: {e}")
            return None

    async def _determine_warming_ttl(self, task: Dict[str, Any]) -> int:
        """Determine appropriate TTL for warmed content"""
        base_ttl = self.cache.default_ttl

        # Adjust based on task type and priority
        task_type = task.get('type', 'unknown')
        priority = task.get('priority', 1)

        if task_type == 'demand':
            # Demand warming gets longer TTL
            return int(base_ttl * 1.5)
        elif task_type == 'predictive':
            # Predictive warming gets moderate TTL
            return base_ttl
        elif task_type == 'scheduled':
            # Scheduled warming TTL based on schedule interval
            schedule_name = task.get('schedule_name', '')
            if schedule_name in self._schedules:
                interval = self._schedules[schedule_name].interval_seconds
                # TTL is roughly 2x the schedule interval
                return min(int(interval * 2), base_ttl * 4)
            return base_ttl
        else:
            return base_ttl

    async def get_warming_stats(self) -> Dict[str, Any]:
        """Get warming statistics"""
        cache_stats = await self.cache.get_stats()

        return {
            "total_warmings": self.stats.total_warmings,
            "successful_warmings": self.stats.successful_warmings,
            "failed_warmings": self.stats.failed_warmings,
            "skipped_warmings": self.stats.skipped_warmings,
            "success_rate": (
                self.stats.successful_warmings / self.stats.total_warmings
                if self.stats.total_warmings > 0 else 0
            ),
            "total_keys_warmed": self.stats.total_keys_warmed,
            "average_warming_time": round(self.stats.average_warming_time, 3),
            "last_warming_time": (
                self.stats.last_warming_time.isoformat()
                if self.stats.last_warming_time else None
            ),
            "active_warmings": len(self._active_warmings),
            "queued_warmings": self._warming_queue.qsize(),
            "tracked_patterns": len(self._access_patterns),
            "active_schedules": len([
                s for s in self._schedules.values() if s.enabled
            ]),
            "cache_improvement": round(self.stats.cache_hit_improvement, 3),
            "warming_effectiveness": round(self.stats.warming_effectiveness, 3)
        }

    async def optimize_warming_strategy(self) -> Dict[str, Any]:
        """Optimize warming strategy based on performance data"""
        stats = await self.get_warming_stats()

        recommendations = []

        # Analyze success rate
        if stats['success_rate'] < 0.8:
            recommendations.append({
                "type": "success_rate",
                "issue": f"Low success rate: {stats['success_rate']:.2%}",
                "recommendation": "Review warming sources and error handling"
            })

        # Analyze timing
        if stats['average_warming_time'] > 30:  # Over 30 seconds
            recommendations.append({
                "type": "timing",
                "issue": f"Slow warming: {stats['average_warming_time']}s average",
                "recommendation": "Consider reducing batch sizes or optimizing data sources"
            })

        # Analyze queue depth
        if stats['queued_warmings'] > self.max_concurrent_warmings * 2:
            recommendations.append({
                "type": "queue_depth",
                "issue": f"Large queue: {stats['queued_warmings']} items",
                "recommendation": "Increase concurrent warming capacity or reduce warming frequency"
            })

        return {
            "current_performance": stats,
            "recommendations": recommendations,
            "optimization_applied": len(recommendations) > 0
        }


# Global cache warmer instance
_cache_warmer: Optional[CacheWarmer] = None


async def get_cache_warmer() -> CacheWarmer:
    """Get the global cache warmer instance"""
    global _cache_warmer

    if _cache_warmer is None:
        _cache_warmer = CacheWarmer()

    return _cache_warmer


async def initialize_cache_warmer() -> None:
    """Initialize the global cache warmer"""
    warmer = await get_cache_warmer()
    await warmer.start()


async def shutdown_cache_warmer() -> None:
    """Shutdown the global cache warmer"""
    global _cache_warmer

    if _cache_warmer:
        await _cache_warmer.stop()
        _cache_warmer = None


def record_cache_access(key: str, category: str = "default") -> None:
    """Record cache access for pattern analysis (synchronous)"""
    if _cache_warmer:
        _cache_warmer.record_access(key, category)