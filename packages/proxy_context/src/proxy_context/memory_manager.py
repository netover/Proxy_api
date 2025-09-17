"""
Memory Management System for Production Use
Prevents memory leaks and optimizes memory usage in high-throughput scenarios.
"""

import asyncio
import gc
import psutil
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import logging

from .feature_flags import get_feature_flag_manager, is_feature_enabled

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics"""

    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    memory_percent: float
    process_memory_mb: float
    gc_collections: Dict[int, int]
    object_counts: Dict[str, int]


class MemoryManager:
    """
    Production memory manager with:
    - Automatic garbage collection tuning
    - Memory usage monitoring
    - Leak detection
    - Emergency cleanup procedures
    - Memory pressure handling
    """

    def __init__(
        self,
        memory_threshold_mb: int = 1024,  # 1GB
        emergency_threshold_mb: int = 1536,  # 1.5GB
        cleanup_interval: int = 300,  # 5 minutes
        enable_gc_tuning: bool = True,
        leak_detection_enabled: bool = True,
    ):
        # Feature flag manager
        self._feature_manager = get_feature_flag_manager()

        # Apply feature flags
        if is_feature_enabled("memory_manager_aggressive_gc"):
            # Enable more aggressive GC settings
            self.enable_gc_tuning = True
            self.cleanup_interval = max(
                60, cleanup_interval // 2
            )  # More frequent cleanup
            logger.info("Memory manager aggressive GC enabled")
        else:
            self.enable_gc_tuning = enable_gc_tuning
            self.cleanup_interval = cleanup_interval

        self.memory_threshold_mb = memory_threshold_mb
        self.emergency_threshold_mb = emergency_threshold_mb
        self.leak_detection_enabled = leak_detection_enabled

        # Memory tracking
        self.baseline_memory = 0
        self.last_cleanup = time.time()
        self.memory_pressure_events = 0
        self.emergency_cleanups = 0

        # Object tracking for leak detection
        self.object_snapshots: List[Dict[str, int]] = []
        self.max_snapshots = 10

        # Cleanup callbacks
        self.cleanup_callbacks: List[Callable] = []

        # Thread safety
        self.lock = threading.Lock()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start memory monitoring"""
        if self._running:
            return

        self._running = True
        self.baseline_memory = self._get_process_memory_mb()

        # Tune garbage collector for high-throughput
        if self.enable_gc_tuning:
            self._tune_gc()

        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info(
            "Memory manager started",
            extra={
                "baseline_memory_mb": round(self.baseline_memory, 2),
                "threshold_mb": self.memory_threshold_mb,
                "emergency_threshold_mb": self.emergency_threshold_mb,
            },
        )

    async def stop(self):
        """Stop memory monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # Final cleanup
        await self.force_cleanup()
        logger.info("Memory manager stopped")

    def _tune_gc(self):
        """Tune garbage collector for better performance"""
        # Disable automatic GC and take control
        gc.disable()

        # Set GC thresholds for more aggressive collection
        # (generations 0, 1, 2 thresholds)
        gc.set_threshold(1000, 10, 10)

        logger.info("GC tuned for high-throughput operation")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._check_memory_pressure()
                await self._periodic_cleanup()
                self._detect_memory_leaks()
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")

    async def _check_memory_pressure(self):
        """Check for memory pressure and take action"""
        current_memory = self._get_process_memory_mb()

        # Emergency cleanup
        if current_memory > self.emergency_threshold_mb:
            logger.warning(
                "Emergency memory threshold exceeded",
                extra={
                    "current_memory_mb": round(current_memory, 2),
                    "threshold_mb": self.emergency_threshold_mb,
                },
            )
            await self._emergency_cleanup()
            self.emergency_cleanups += 1
            return

        # High memory pressure
        if current_memory > self.memory_threshold_mb:
            logger.warning(
                "High memory usage detected",
                extra={
                    "current_memory_mb": round(current_memory, 2),
                    "threshold_mb": self.memory_threshold_mb,
                },
            )
            await self._high_memory_cleanup()
            self.memory_pressure_events += 1

    async def _periodic_cleanup(self):
        """Periodic cleanup operations"""
        # Force garbage collection
        collected = gc.collect()

        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")

        if collected > 0:
            logger.debug(f"GC collected {collected} objects")

    async def _emergency_cleanup(self):
        """Emergency cleanup when memory is critical"""
        logger.warning("Performing emergency memory cleanup")

        # Aggressive garbage collection
        for generation in range(3):
            collected = gc.collect(generation)
            logger.info(f"Emergency GC generation {generation}: {collected} objects")

        # Clear any cached objects
        gc.collect()

        # Force cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Emergency cleanup callback error: {e}")

    async def _high_memory_cleanup(self):
        """Cleanup when memory usage is high"""
        # Less aggressive than emergency cleanup
        collected = gc.collect(2)  # Collect generation 2 only
        logger.info(f"High memory cleanup: {collected} objects collected")

    def _detect_memory_leaks(self):
        """Detect potential memory leaks"""
        if not self.leak_detection_enabled:
            return

        # Take object count snapshot
        snapshot = self._get_object_snapshot()

        # Store snapshot
        self.object_snapshots.append(snapshot)
        if len(self.object_snapshots) > self.max_snapshots:
            self.object_snapshots.pop(0)

        # Analyze trends if we have enough snapshots
        if len(self.object_snapshots) >= 3:
            self._analyze_leak_trends()

    def _get_object_snapshot(self) -> Dict[str, int]:
        """Get snapshot of object counts"""
        return {
            "dict": len([obj for obj in gc.get_objects() if isinstance(obj, dict)]),
            "list": len([obj for obj in gc.get_objects() if isinstance(obj, list)]),
            "tuple": len([obj for obj in gc.get_objects() if isinstance(obj, tuple)]),
            "str": len([obj for obj in gc.get_objects() if isinstance(obj, str)]),
            "function": len([obj for obj in gc.get_objects() if callable(obj)]),
            "total": len(gc.get_objects()),
        }

    def _analyze_leak_trends(self):
        """Analyze object count trends for leak detection"""
        if len(self.object_snapshots) < 3:
            return

        # Check for consistent growth in object counts
        recent = self.object_snapshots[-3:]

        for obj_type in ["dict", "list", "function"]:
            counts = [snapshot.get(obj_type, 0) for snapshot in recent]

            # Check if all counts are increasing
            if all(counts[i] < counts[i + 1] for i in range(len(counts) - 1)):
                growth_rate = (
                    (counts[-1] - counts[0]) / counts[0] if counts[0] > 0 else 0
                )

                if growth_rate > 0.1:  # 10% growth
                    logger.warning(
                        "Potential memory leak detected",
                        extra={
                            "object_type": obj_type,
                            "growth_rate": round(growth_rate, 3),
                            "counts": counts,
                        },
                    )

    def _get_process_memory_mb(self) -> float:
        """Get current process memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def add_cleanup_callback(self, callback: Callable):
        """Add a cleanup callback function"""
        self.cleanup_callbacks.append(callback)

    def remove_cleanup_callback(self, callback: Callable):
        """Remove a cleanup callback function"""
        if callback in self.cleanup_callbacks:
            self.cleanup_callbacks.remove(callback)

    async def force_cleanup(self):
        """Force immediate cleanup"""
        logger.info("Forcing memory cleanup")
        collected = gc.collect()
        logger.info(f"Force cleanup collected {collected} objects")

    def get_memory_stats(self) -> MemoryStats:
        """Get comprehensive memory statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()

        return MemoryStats(
            total_memory_mb=round(psutil.virtual_memory().total / (1024 * 1024), 2),
            available_memory_mb=round(
                psutil.virtual_memory().available / (1024 * 1024), 2
            ),
            used_memory_mb=round(psutil.virtual_memory().used / (1024 * 1024), 2),
            memory_percent=round(psutil.virtual_memory().percent, 2),
            process_memory_mb=round(memory_info.rss / (1024 * 1024), 2),
            gc_collections=dict(gc.get_stats()),
            object_counts=self._get_object_snapshot(),
        )

    def get_manager_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics"""
        return {
            "baseline_memory_mb": round(self.baseline_memory, 2),
            "current_memory_mb": round(self._get_process_memory_mb(), 2),
            "memory_threshold_mb": self.memory_threshold_mb,
            "emergency_threshold_mb": self.emergency_threshold_mb,
            "memory_pressure_events": self.memory_pressure_events,
            "emergency_cleanups": self.emergency_cleanups,
            "cleanup_callbacks_count": len(self.cleanup_callbacks),
            "leak_detection_enabled": self.leak_detection_enabled,
            "gc_tuning_enabled": self.enable_gc_tuning,
            "snapshots_count": len(self.object_snapshots),
            "last_cleanup": self.last_cleanup,
        }


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


async def get_memory_manager() -> MemoryManager:
    """Get global memory manager instance"""
    global _memory_manager

    if _memory_manager is None:
        _memory_manager = MemoryManager()

    if not _memory_manager._running:
        await _memory_manager.start()

    return _memory_manager


async def initialize_memory_manager():
    """Initialize global memory manager"""
    manager = await get_memory_manager()
    return manager


async def shutdown_memory_manager():
    """Shutdown global memory manager"""
    global _memory_manager

    if _memory_manager:
        await _memory_manager.stop()
        _memory_manager = None


def get_memory_stats() -> MemoryStats:
    """Get current memory statistics (synchronous)"""
    if _memory_manager:
        return _memory_manager.get_memory_stats()

    # Fallback if manager not initialized
    process = psutil.Process()
    memory_info = process.memory_info()

    return MemoryStats(
        total_memory_mb=round(psutil.virtual_memory().total / (1024 * 1024), 2),
        available_memory_mb=round(psutil.virtual_memory().available / (1024 * 1024), 2),
        used_memory_mb=round(psutil.virtual_memory().used / (1024 * 1024), 2),
        memory_percent=round(psutil.virtual_memory().percent, 2),
        process_memory_mb=round(memory_info.rss / (1024 * 1024), 2),
        gc_collections=dict(gc.get_stats()),
        object_counts={},
    )
