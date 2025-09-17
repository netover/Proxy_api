"""
Memory Management System for Production Use
This module provides a SmartContextManager to prevent memory leaks in long-running
sessions by using an LRU (Least Recently Used) cache mechanism and proactive
garbage collection.
"""

import asyncio
import gc
import logging
from collections import OrderedDict
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class SmartContextManager:
    """
    Manages session contexts with an LRU eviction policy to prevent unbounded memory growth.
    It also triggers proactive garbage collection when memory usage reaches a certain threshold.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initializes the context manager.
        Args:
            max_size: The maximum number of session contexts to store before evicting the oldest.
        """
        self.max_size = max_size
        self.contexts = OrderedDict()
        self.gc_threshold = int(max_size * 0.8)  # Trigger GC at 80% capacity
        self.lock = asyncio.Lock()
        logger.info(
            f"SmartContextManager initialized with max_size={max_size} and gc_threshold={self.gc_threshold}"
        )

    async def add_context(self, session_id: str, context: Any):
        """
        Adds a context for a session. If the manager is full, it evicts the least recently used context.
        If the threshold is reached, it triggers garbage collection.
        """
        async with self.lock:
            if len(self.contexts) >= self.max_size:
                await self._evict_oldest()

            self.contexts[session_id] = context
            self.contexts.move_to_end(session_id)  # Mark as most recently used

            if len(self.contexts) > self.gc_threshold:
                await self._trigger_gc()

    async def get_context(self, session_id: str) -> Optional[Any]:
        """
        Retrieves a context for a session, marking it as most recently used.
        """
        async with self.lock:
            if session_id in self.contexts:
                self.contexts.move_to_end(session_id)
                return self.contexts[session_id]
            return None

    async def remove_context(self, session_id: str) -> bool:
        """Removes a context for a session."""
        async with self.lock:
            if session_id in self.contexts:
                del self.contexts[session_id]
                return True
            return False

    async def _evict_oldest(self):
        """Evicts the least recently used item."""
        if not self.contexts:
            return
        oldest_key, _ = self.contexts.popitem(last=False)
        logger.info(f"Evicted oldest context '{oldest_key}' due to size limit.")

    async def _trigger_gc(self):
        """
        Triggers a generational garbage collection.
        This is an expensive operation and should be called sparingly.
        """
        logger.info(
            f"Context manager threshold ({self.gc_threshold}) reached, triggering GC."
        )
        # gc.collect(2) is a full, aggressive collection of long-lived objects.
        gc.collect(2)

    async def clear(self):
        """Clears all stored contexts."""
        async with self.lock:
            self.contexts.clear()
        logger.info("All contexts have been cleared.")

    def get_stats(self) -> dict:
        """Returns statistics about the context manager."""
        return {
            "current_size": len(self.contexts),
            "max_size": self.max_size,
            "gc_threshold": self.gc_threshold,
        }


# --- Global Instance Management ---

_memory_manager: Optional[SmartContextManager] = None


async def get_memory_manager(config: Dict[str, Any] = None) -> SmartContextManager:
    """
    Gets the global singleton instance of the SmartContextManager.
    This function is intended to be the primary access point for the memory manager.
    """
    global _memory_manager
    if _memory_manager is None:
        if config:
            # Note: The current SmartContextManager doesn't use the full config.
            # This is a pragmatic fix to allow startup. A future refactor should
            # align the MemoryManager with the config settings.
             _memory_manager = SmartContextManager(max_size=1000)
        else:
            _memory_manager = SmartContextManager(max_size=1000)
    return _memory_manager


async def shutdown_memory_manager():
    """
    Shuts down the memory manager, clearing its contexts.
    """
    global _memory_manager
    if _memory_manager:
        logger.info("Shutting down memory manager and clearing contexts.")
        # .clear() is synchronous
        _memory_manager.clear()
        _memory_manager = None
