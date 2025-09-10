from fastapi import Request
from typing import List, Optional
import hashlib
import time
import asyncio
import json
import os
import re
from pathlib import Path
from collections import OrderedDict
from src.providers.base import get_provider
from src.core.logging import ContextualLogger
from src.core.unified_config import config_manager
from src.core.metrics import metrics_collector

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
    """Async-compatible LRU Cache with persistence support"""
    def __init__(self, maxsize: int = 1000, persist_file: Optional[str] = None):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.persist_file = persist_file
        if self.persist_file and asyncio.iscoroutinefunction(self.load):
            asyncio.create_task(self.load())

    async def load(self):
        """Load cache from file if persistence enabled"""
        if not self.persist_file:
            return
        try:
            with open(self.persist_file, 'r') as f:
                data = json.load(f)
                self.cache = OrderedDict(data)
                logger.info(f"Loaded {len(self.cache)} items from {self.persist_file}")
        except FileNotFoundError:
            logger.info(f"No persistent cache file found: {self.persist_file}")
        except Exception as e:
            logger.error(f"Failed to load persistent cache: {e}")

    async def save(self):
        """Save cache to file if persistence enabled"""
        if not self.persist_file or len(self.cache) == 0:
            return
        try:
            with open(self.persist_file, 'w') as f:
                json.dump(dict(self.cache), f)
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
            self.cache[key] = value
        asyncio.create_task(self.save())  # Async save on set

    def clear(self):
        self.cache.clear()
        asyncio.create_task(self.save())

async def condense_context(request: Request, chunks: List[str], max_tokens: int = 512) -> str:
    """
    Usa o provider de maior prioridade para resumir mensagens longas.
    """
    start_time = time.time()
    
    # Dynamic config reload if enabled
    if hasattr(request.app.state, 'config_mtime') and condensation_config.dynamic_reload:
        try:
            current_mtime = os.path.getmtime(config_manager.config_path)
            if current_mtime > request.app.state.config_mtime:
                logger.info("Config changed, reloading...")
                reloaded_config = config_manager.load_config(force_reload=True)
                request.app.state.config = reloaded_config
                request.app.state.condensation_config = reloaded_config.settings.condensation
                request.app.state.config_mtime = current_mtime
                condensation_config = request.app.state.condensation_config  # Update local
                logger.info("Config reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")

    # Initialize or get LRU cache from app state
    if not hasattr(request.app.state, 'lru_cache') or request.app.state.lru_cache is None:
        persist_file = 'cache.json' if condensation_config.cache_persist else None
        request.app.state.lru_cache = AsyncLRUCache(maxsize=condensation_config.cache_size, persist_file=persist_file)
    lru_cache = request.app.state.lru_cache
    condensation_config = request.app.state.condensation_config
    
    # Compute adaptive max_tokens if enabled
    use_max_tokens = max_tokens  # Default to passed value
    if condensation_config.adaptive_enabled:
        original_size = sum(len(c) for c in chunks)
        adaptive_max_tokens = min(original_size * condensation_config.adaptive_factor, condensation_config.max_tokens_default)
        use_max_tokens = min(use_max_tokens, adaptive_max_tokens)  # Respect but cap with adaptive
    
    # Cache key
    chunk_hash = hashlib.md5(''.join(chunks).encode()).hexdigest()
    
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
        logger.info(f"Proactively truncated content from {len(content) + truncate_len} to {len(content)} chars due to threshold {condensation_config.truncation_threshold}")

    # Prepare providers for parallel or sequential
    enabled_providers = [p for p in request.app.state.config.providers if p.enabled]
    sorted_providers = sorted(enabled_providers, key=lambda p: p.priority)
    if not sorted_providers:
        raise ValueError("No enabled providers available for condensation")
    
    resp = None
    if condensation_config.parallel_providers > 1:
        # Parallel execution
        tasks = []
        max_parallel = min(condensation_config.parallel_providers, len(sorted_providers))
        for cfg in sorted_providers[:max_parallel]:
            prov = await get_provider(cfg)
            # Copy request_body for each
            body_copy = request_body.copy()
            body_copy["model"] = cfg.models[0]
            task = asyncio.create_task(
                call_provider_with_timeout(prov, cfg, body_copy)
            )
            tasks.append((task, cfg))
        # Wait for first completed
        done, pending = await asyncio.wait([t[0] for t in tasks], return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            for t, cfg in tasks:
                if t == task:
                    if not task.exception():
                        resp = task.result()
                        logger.info(f"Parallel success with provider: {cfg.name}")
                    else:
                        logger.error(f"Parallel task failed for {cfg.name}: {task.exception()}")
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
        provider = await get_provider(top_cfg)

        # Monta prompt de resumo
        content = "\n\n---\n\n".join(chunks)
        request_body = {
            "model": top_cfg.models[0],
            "messages": [
                {"role": "system", "content":
                    f"Resuma mantendo entidades e intents, "
                    f"limitando a {use_max_tokens} tokens."
                },
                {"role": "user", "content": content}
            ],
            "max_tokens": use_max_tokens
        }

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
                if any(re.search(pattern, error_msg, re.IGNORECASE) for pattern in condensation_config.error_patterns):
                    fallback_applied = False
                    if "truncate" in condensation_config.fallback_strategies:
                        half_len = len(content) // 2
                        content = content[-half_len:]
                        request_body["messages"][1]["content"] = content
                        use_max_tokens = min(use_max_tokens, len(content) // 4)
                        request_body["max_tokens"] = use_max_tokens
                        logger.info("Applied truncate fallback")
                        fallback_applied = True
                    if not fallback_applied and "secondary_provider" in condensation_config.fallback_strategies and len(sorted_providers) > 1:
                        current_idx = sorted_providers.index(top_cfg)
                        if current_idx + 1 < len(sorted_providers):
                            top_cfg = sorted_providers[current_idx + 1]
                            provider = await get_provider(top_cfg)
                            request_body["model"] = top_cfg.models[0]
                            logger.info(f"Applied secondary provider fallback: {top_cfg.name}")
                            fallback_applied = True
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