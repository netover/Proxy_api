from typing import List, Optional, Dict, Any
import hashlib
import time
import asyncio
import json
import os
import re
from collections import OrderedDict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional Redis import for distributed caching in high-load environments
try:
    import redis.asyncio as redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

class SimpleConfig:
    """Simplified configuration for context service"""
    def __init__(self):
        self.cache_size = int(os.getenv("CACHE_SIZE", "1000"))
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))
        self.cache_persist = os.getenv("CACHE_PERSIST", "false").lower() == "true"
        self.adaptive_enabled = os.getenv("ADAPTIVE_ENABLED", "true").lower() == "true"
        self.adaptive_factor = float(os.getenv("ADAPTIVE_FACTOR", "0.5"))
        self.max_tokens_default = int(os.getenv("MAX_TOKENS_DEFAULT", "512"))
        self.truncation_threshold = int(os.getenv("TRUNCATION_THRESHOLD", "10000"))
        self.parallel_providers = int(os.getenv("PARALLEL_PROVIDERS", "1"))
        self.error_patterns = os.getenv("ERROR_PATTERNS", "context.*exceeded,token.*limit").split(",")
        self.fallback_strategies = os.getenv("FALLBACK_STRATEGIES", "truncate,secondary_provider").split(",")

class AsyncLRUCache:
    """Async-compatible LRU Cache with persistence support (file or Redis)"""
    def __init__(self, maxsize: int = 1000, persist_file: Optional[str] = None, redis_url: Optional[str] = None):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.persist_file = persist_file
        self.redis_url = redis_url
        self.redis_client = None

        # Initialize Redis if URL provided and available
        if self.redis_url and REDIS_AVAILABLE:
            self.redis_client = redis.from_url(self.redis_url)
            logger.info(f"Redis cache enabled with URL: {self.redis_url}")
        elif self.redis_url and not REDIS_AVAILABLE:
            logger.warning("Redis URL provided but redis package not available, falling back to in-memory cache")

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
                            cache_key = key.decode('utf-8').replace("cache:", "")
                            data = json.loads(value.decode('utf-8'))
                            self.cache[cache_key] = tuple(data)
                    logger.info(f"Loaded {len(self.cache)} items from Redis")
            except Exception as e:
                logger.error(f"Failed to load Redis cache: {e}")
        elif self.persist_file:
            # Load from file
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
        """Save cache to file or Redis if persistence enabled"""
        if self.redis_client:
            # Save to Redis
            if len(self.cache) == 0:
                return
            try:
                for key, value in self.cache.items():
                    redis_key = f"cache:{key}"
                    await self.redis_client.set(redis_key, json.dumps(value))
                logger.debug(f"Saved {len(self.cache)} items to Redis")
            except Exception as e:
                logger.error(f"Failed to save Redis cache: {e}")
        elif self.persist_file:
            # Save to file
            if len(self.cache) == 0:
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
                # Also remove from Redis if using Redis
                if self.redis_client:
                    asyncio.create_task(self.redis_client.delete(f"cache:{oldest_key}"))
            self.cache[key] = value
        asyncio.create_task(self.save())  # Async save on set

    def clear(self):
        self.cache.clear()
        asyncio.create_task(self.save())

    async def initialize(self):
        """Initialize cache by loading from persistence if enabled"""
        await self.load()

    async def shutdown(self):
        """Shutdown cache and save to file/Redis if persistence enabled"""
        await self.save()
        if self.redis_client:
            await self.redis_client.close()
        logger.info(f"Cache shutdown, saved {len(self.cache)} items")

# Global cache instance
_cache = None
_config = None

async def get_cache():
    global _cache, _config
    if _cache is None:
        _config = SimpleConfig()
        persist_file = 'cache.json' if _config.cache_persist else None
        _cache = AsyncLRUCache(maxsize=_config.cache_size, persist_file=persist_file)
        if persist_file:
            await _cache.initialize()
    return _cache

async def get_config():
    global _config
    if _config is None:
        _config = SimpleConfig()
    return _config

# Mock provider classes for the context service
class MockProvider:
    def __init__(self, name: str, base_url: str, models: List[str], timeout: int = 30):
        self.name = name
        self.base_url = base_url
        self.models = models
        self.timeout = timeout

    async def create_completion(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation - in real service, this would call actual providers"""
        # Simulate API call delay
        await asyncio.sleep(0.1)

        # Mock response
        content = request_body["messages"][1]["content"]
        summary = f"Summary of: {content[:100]}..." if len(content) > 100 else f"Summary of: {content}"

        return {
            "choices": [{
                "message": {
                    "content": summary
                }
            }]
        }

# Mock provider factory
async def get_provider(cfg):
    """Mock provider factory - in real implementation, this would load actual providers"""
    return MockProvider(cfg.name, cfg.base_url, cfg.models, cfg.timeout)

async def condense_context(chunks: List[str], max_tokens: int = 512) -> str:
    """
    Condense context using available providers with caching and fallback support.
    """
    start_time = time.time()

    cache = await get_cache()
    config = await get_config()

    # Compute adaptive max_tokens if enabled
    use_max_tokens = max_tokens
    if config.adaptive_enabled:
        original_size = sum(len(c) for c in chunks)
        adaptive_max_tokens = min(original_size * config.adaptive_factor, config.max_tokens_default)
        use_max_tokens = min(use_max_tokens, adaptive_max_tokens)

    # Cache key
    chunk_hash = hashlib.md5(''.join(chunks).encode()).hexdigest()

    # Check cache
    cached = cache.get(chunk_hash)
    if cached:
        summary, timestamp = cached
        if time.time() - timestamp < config.cache_ttl:
            logger.debug(f"Cache hit for chunk hash: {chunk_hash}")
            return summary

    # Proactive truncation if content would be too long
    content = "\n\n---\n\n".join(chunks)
    if len(content) > config.truncation_threshold:
        truncate_len = config.truncation_threshold // 2
        content = content[-truncate_len:]
        use_max_tokens = min(use_max_tokens, truncate_len // 4)
        logger.info(f"Proactively truncated content from {len(content) + truncate_len} to {len(content)} chars")

    # Mock providers for demonstration
    providers = [
        type('ProviderConfig', (), {
            'name': 'mock-provider-1',
            'base_url': 'http://mock1.com',
            'models': ['gpt-3.5-turbo'],
            'timeout': 30,
            'priority': 1,
            'enabled': True
        })(),
        type('ProviderConfig', (), {
            'name': 'mock-provider-2',
            'base_url': 'http://mock2.com',
            'models': ['gpt-4'],
            'timeout': 30,
            'priority': 2,
            'enabled': True
        })()
    ]

    enabled_providers = [p for p in providers if p.enabled]
    sorted_providers = sorted(enabled_providers, key=lambda p: p.priority)

    if not sorted_providers:
        raise ValueError("No enabled providers available for condensation")

    # Prepare base request body for condensation
    request_body = {
        "model": "",
        "messages": [
            {"role": "system", "content": f"Resuma mantendo entidades e intents, limitando a {use_max_tokens} tokens."},
            {"role": "user", "content": content}
        ],
        "max_tokens": use_max_tokens
    }

    resp = None
    if config.parallel_providers > 1:
        # Parallel execution
        tasks = []
        max_parallel = min(config.parallel_providers, len(sorted_providers))
        for cfg in sorted_providers[:max_parallel]:
            prov = await get_provider(cfg)
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

            if not fallback_attempted and config.error_patterns:
                if any(re.search(pattern.strip(), error_msg, re.IGNORECASE) for pattern in config.error_patterns):
                    fallback_applied = False
                    if "truncate" in config.fallback_strategies:
                        half_len = len(content) // 2
                        content = content[-half_len:]
                        request_body["messages"][1]["content"] = content
                        use_max_tokens = min(use_max_tokens, len(content) // 4)
                        request_body["max_tokens"] = use_max_tokens
                        logger.info("Applied truncate fallback")
                        fallback_applied = True
                    if not fallback_applied and "secondary_provider" in config.fallback_strategies and len(sorted_providers) > 1:
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

    # Record latency
    end_time = time.time()
    latency = end_time - start_time
    logger.info(f"Condensation completed in {latency:.2f}s")

    # Store in cache
    cache.set(chunk_hash, (summary, time.time()))
    logger.debug(f"Cache miss, stored for chunk hash: {chunk_hash}")

    return summary

async def call_provider_with_timeout(provider, cfg, request_body):
    """Helper to call provider with timeout"""
    try:
        async with asyncio.timeout(cfg.timeout):
            resp = await provider.create_completion(request_body)
        return resp
    except Exception as e:
        logger.error(f"Provider {cfg.name} failed: {e}")
        raise e