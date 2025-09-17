import asyncio
import hashlib
import json
import os
import re
import time
from collections import OrderedDict
from typing import List, Optional

from fastapi import Request

from src.core.logging import ContextualLogger
from src.core.metrics import metrics_collector
from src.core.provider_factory import provider_factory
from src.core.unified_config import config_manager

# Optional Redis import for distributed caching in high-load environments
try:
    import redis.asyncio as redis  # type: ignore

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = ContextualLogger(__name__)


async def call_provider_with_timeout(provider, cfg, request_body):
    """Helper to call provider with timeout"""
    try:
        async with asyncio.timeout(cfg.timeout):
            resp = await provider.create_completion(request_body)
        return resp
    except Exception as e:
        logger.error(f"Provider {cfg.name} failed: {e}")
        raise e


class AsyncLRUCache:
    """Async-compatible LRU Cache with persistence support (file or Redis)"""

    def __init__(
        self,
        maxsize: int = 1000,
        persist_file: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.persist_file = persist_file
        self.redis_url = redis_url
        self.redis_client = None

        # Background task management
        self._background_tasks: set = set()
        self._shutdown_event = asyncio.Event()

        # Initialize Redis if URL provided and available
        if self.redis_url and REDIS_AVAILABLE:
            self.redis_client = redis.from_url(self.redis_url)
            logger.info(f"Redis cache enabled with URL: {self.redis_url}")
        elif self.redis_url and not REDIS_AVAILABLE:
            logger.warning(
                "Redis URL provided but redis package not available, falling back to in-memory cache"
            )

    async def load(self):
        """Load cache from file or Redis if persistence enabled"""
        if self.redis_client:
            # Load from Redis
            try:
                keys = await self.redis_client.keys("cache:*")
                if keys:
                    for key in keys:
                        value = await self.redis_client.get(key)
                        if value:
                            cache_key = key.decode("utf-8").replace("cache:", "")
                            data = json.loads(value.decode("utf-8"))
                            self.cache[cache_key] = tuple(data)
                    logger.info(f"Loaded {len(self.cache)} items from Redis")
            except Exception as e:
                logger.error(f"Failed to load Redis cache: {e}")
        elif self.persist_file:
            # Load from file
            try:
                with open(
                    self.persist_file, "r", encoding="utf-8", errors="ignore"
                ) as f:
                    data = json.load(f)
                    self.cache = OrderedDict(data)
                    logger.info(
                        f"Loaded {len(self.cache)} items from {self.persist_file}"
                    )
            except FileNotFoundError:
                logger.info(f"No persistent cache file found: {self.persist_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse cache file: {e}")
                # Handle corrupted cache file
                try:
                    os.rename(self.persist_file, f"{self.persist_file}.corrupted")
                    logger.info(
                        f"Renamed corrupted cache file to {self.persist_file}.corrupted"
                    )
                except Exception as rename_error:
                    logger.error(
                        f"Failed to rename corrupted cache file: {rename_error}"
                    )
            except Exception as e:
                logger.error(f"Failed to load persistent cache: {e}")

    async def save(self):
        """Save cache to file or Redis if persistence enabled"""
        if self.redis_client:
            # Save to Redis
            if len(self.cache) == 0:
                return
            try:
                for key, value in self.cache.items():
                    redis_key = f"cache:{key}"
                    await self.redis_client.set(
                        redis_key, json.dumps(value, default=str)
                    )
                logger.debug(f"Saved {len(self.cache)} items to Redis")
            except Exception as e:
                logger.error(f"Failed to save Redis cache: {e}")
        elif self.persist_file:
            # Save to file
            if len(self.cache) == 0:
                return
            try:
                with open(self.persist_file, "w", encoding="utf-8") as f:
                    json.dump(dict(self.cache), f, ensure_ascii=False, default=str)
                logger.debug(f"Saved {len(self.cache)} items to {self.persist_file}")
            except Exception as e:
                logger.error(f"Failed to save persistent cache: {e}")

    def get(self, key: str):
        """Get item, move to end (MRU)"""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: tuple):
        """Set item, evict if full"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                oldest_key, _ = self.cache.popitem(last=False)
                logger.debug(f"Evicted cache item: {oldest_key}")
                # Also remove from Redis if using Redis
                if self.redis_client:
                    task = asyncio.create_task(
                        self.redis_client.delete(f"cache:{oldest_key}")
                    )
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
            self.cache[key] = value
        # Async save on set
        task = asyncio.create_task(self.save())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def clear(self):
        self.cache.clear()
        # Async save on clear
        task = asyncio.create_task(self.save())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def initialize(self):
        """Initialize cache by loading from persistence if enabled"""
        await self.load()

    async def shutdown(self):
        """Shutdown cache and save to file/Redis if persistence enabled"""
        # Cancel all pending background tasks
        if self._background_tasks:
            logger.info(f"Cancelling {len(self._background_tasks)} background tasks")
            for task in list(self._background_tasks):
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete or be cancelled
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            logger.info("All background tasks cancelled")

        # Final save
        await self.save()
        if self.redis_client:
            await self.redis_client.close()
        logger.info(f"Cache shutdown, saved {len(self.cache)} items")


async def condense_context(
    request: Request, chunks: List[str], max_tokens: int = 512
) -> str:
    """
    Usa o provider de maior prioridade para resumir mensagens longas.
    """
    start_time = time.time()

    # Get condensation config from app state
    condensation_config = request.app.state.condensation_config

    # Dynamic config reload if enabled
    if (
        hasattr(request.app.state, "config_mtime")
        and condensation_config.dynamic_reload
    ):
        try:
            current_mtime = os.path.getmtime(config_manager.config_path)
            if current_mtime > request.app.state.config_mtime:
                logger.info("Config changed, reloading...")
                reloaded_config = config_manager.load_config(force_reload=True)
                request.app.state.config = reloaded_config
                request.app.state.condensation_config = (
                    reloaded_config.settings.condensation
                )
                request.app.state.config_mtime = current_mtime
                condensation_config = (
                    request.app.state.condensation_config
                )  # Update local
                logger.info("Config reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")

    # Initialize or get LRU cache from app state
    if (
        not hasattr(request.app.state, "lru_cache")
        or request.app.state.lru_cache is None
    ):
        persist_file = "cache.json" if condensation_config.cache_persist else None
        request.app.state.lru_cache = AsyncLRUCache(
            maxsize=condensation_config.cache_size, persist_file=persist_file
        )
        # Initialize cache loading if persistence is enabled
        if persist_file:
            await request.app.state.lru_cache.initialize()
    lru_cache = request.app.state.lru_cache
    condensation_config = request.app.state.condensation_config

    # Compute adaptive max_tokens if enabled
    use_max_tokens = max_tokens  # Default to passed value
    if condensation_config.adaptive_enabled:
        original_size = sum(len(c) for c in chunks)
        adaptive_max_tokens = min(
            original_size * condensation_config.adaptive_factor,
            condensation_config.max_tokens_default,
        )
        use_max_tokens = min(
            use_max_tokens, adaptive_max_tokens
        )  # Respect but cap with adaptive

    # Cache key
    chunk_hash = hashlib.md5("".join(chunks).encode()).hexdigest()

    # Check cache
    cached = lru_cache.get(chunk_hash)
    if cached:
        summary, timestamp = cached
        if time.time() - timestamp < condensation_config.cache_ttl:
            logger.debug(f"Cache hit for chunk hash: {chunk_hash}")
            metrics_collector.record_summary(True, 0.0)
            return summary

    # Proactive truncation if content would be too long
    content = "\n\n---\n\n".join(chunks)
    if len(content) > condensation_config.truncation_threshold:
        truncate_len = condensation_config.truncation_threshold // 2
        content = content[-truncate_len:]
        use_max_tokens = min(use_max_tokens, truncate_len // 4)
        logger.info(
            f"Proactively truncated content from {len(content) + truncate_len} to {len(content)} chars due to threshold {condensation_config.truncation_threshold}"
        )

    # Prepare providers for parallel or sequential
    enabled_providers = [p for p in request.app.state.config.providers if p.enabled]
    sorted_providers = sorted(enabled_providers, key=lambda p: p.priority)
    if not sorted_providers:
        raise ValueError("No enabled providers available for condensation")

    # Prepare base request body for condensation
    request_body = {
        "model": "",  # Will be set per provider
        "messages": [
            {
                "role": "system",
                "content": f"Resuma mantendo entidades e intents, limitando a {use_max_tokens} tokens.",
            },
            {"role": "user", "content": content},
        ],
        "max_tokens": use_max_tokens,
    }

    resp = None
    if condensation_config.parallel_providers > 1:
        # Parallel execution
        tasks = []
        max_parallel = min(
            condensation_config.parallel_providers, len(sorted_providers)
        )
        for cfg in sorted_providers[:max_parallel]:
            prov = await provider_factory.create_provider(cfg)
            # Copy request_body for each
            body_copy = request_body.copy()
            body_copy["model"] = cfg.models[0]
            task = asyncio.create_task(call_provider_with_timeout(prov, cfg, body_copy))
            tasks.append((task, cfg))
        # Wait for first completed
        done, pending = await asyncio.wait(
            [t[0] for t in tasks], return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            for t, cfg in tasks:
                if t == task:
                    if not task.exception():
                        resp = task.result()
                        logger.info(f"Parallel success with provider: {cfg.name}")
                    else:
                        logger.error(
                            f"Parallel task failed for {cfg.name}: {task.exception()}"
                        )
                    break
        # Cancel pending
        for task, _ in tasks:
            if not task.done():
                task.cancel()
        if not resp:
            raise ValueError("All parallel providers failed")
    else:
        # Sequential with fallback
        top_cfg = sorted_providers[0]
        provider = await provider_factory.create_provider(top_cfg)

        # Update request body for sequential execution
        request_body["model"] = top_cfg.models[0]

        fallback_attempted = False
        for attempt in range(2):
            try:
                async with asyncio.timeout(top_cfg.timeout):
                    resp = await provider.create_completion(request_body)
                break
            except asyncio.TimeoutError as e:
                error_msg = str(e)
                logger.error(error_msg)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Condensation failed: {error_msg}")

            if not fallback_attempted and condensation_config.error_patterns:
                if any(
                    re.search(pattern, error_msg, re.IGNORECASE)
                    for pattern in condensation_config.error_patterns
                ):
                    fallback_applied = False
                    if "truncate" in condensation_config.fallback_strategies:
                        half_len = len(content) // 2
                        content = content[-half_len:]
                        request_body["messages"][1]["content"] = content
                        use_max_tokens = min(use_max_tokens, len(content) // 4)
                        request_body["max_tokens"] = use_max_tokens
                        logger.info("Applied truncate fallback")
                        fallback_applied = True
                    if (
                        not fallback_applied
                        and "secondary_provider"
                        in condensation_config.fallback_strategies
                    ):
                        enabled_providers_count = len(
                            [p for p in sorted_providers if p.enabled]
                        )
                        if enabled_providers_count > 1:
                            current_idx = sorted_providers.index(top_cfg)
                            if current_idx + 1 < len(sorted_providers):
                                # Find next enabled provider
                                for next_idx in range(
                                    current_idx + 1, len(sorted_providers)
                                ):
                                    next_cfg = sorted_providers[next_idx]
                                    if next_cfg.enabled:
                                        top_cfg = next_cfg
                                        provider = (
                                            await provider_factory.create_provider(
                                                top_cfg
                                            )
                                        )
                                        request_body["model"] = top_cfg.models[0]
                                        logger.info(
                                            f"Applied secondary provider fallback: {top_cfg.name}"
                                        )
                                        fallback_applied = True
                                        break
                    if fallback_applied:
                        fallback_attempted = True
                        continue
            raise ValueError(error_msg)

    summary = resp["choices"][0]["message"]["content"]

    # Record latency for cache miss
    end_time = time.time()
    latency = end_time - start_time
    metrics_collector.record_summary(False, latency)

    # Store in cache
    lru_cache.set(chunk_hash, (summary, time.time()))
    logger.debug(f"Cache miss, stored for chunk hash: {chunk_hash}")

    return summary
