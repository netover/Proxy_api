"""
Optimized Configuration Loader for ProxyAPI

Features:
- Lazy loading for non-critical configurations
- Async file I/O operations
- Advanced caching with TTL
- File watching for hot reload
- Performance timing measurements
- Memory-efficient parsing
"""

import asyncio
import time
import yaml
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

logger = logging.getLogger(__name__)

@dataclass
class ConfigTiming:
    """Tracks configuration loading performance"""
    start_time: float
    end_time: float
    file_size: int
    cache_hit: bool
    lazy_loaded: bool

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

class ConfigCache:
    """Advanced configuration cache with TTL and memory management"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, float] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._executor = ThreadPoolExecutor(max_workers=2)

    def _get_cache_key(self, file_path: Path, section: Optional[str] = None) -> str:
        """Generate cache key from file path and optional section"""
        content = f"{file_path}:{section or 'full'}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > self.ttl_seconds

    def _evict_old_entries(self):
        """Evict expired and least recently used entries"""
        current_time = time.time()

        # Remove expired entries
        expired_keys = [k for k in self.cache.keys() if self._is_expired(k)]
        for key in expired_keys:
            del self.cache[key]
            del self.timestamps[key]
            del self.access_times[key]

        # If still over size limit, remove least recently used
        if len(self.cache) > self.max_size:
            # Sort by access time (oldest first)
            sorted_keys = sorted(self.access_times.keys(),
                               key=lambda k: self.access_times[k])
            keys_to_remove = sorted_keys[:len(self.cache) - self.max_size]

            for key in keys_to_remove:
                del self.cache[key]
                del self.timestamps[key]
                del self.access_times[key]

    def get(self, file_path: Path, section: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached configuration"""
        key = self._get_cache_key(file_path, section)

        if key in self.cache and not self._is_expired(key):
            self.access_times[key] = time.time()
            return self.cache[key].copy()

        return None

    def set(self, file_path: Path, data: Dict[str, Any], section: Optional[str] = None):
        """Cache configuration data"""
        self._evict_old_entries()

        key = self._get_cache_key(file_path, section)
        self.cache[key] = data.copy()
        self.timestamps[key] = time.time()
        self.access_times[key] = time.time()

    def invalidate(self, file_path: Path, section: Optional[str] = None):
        """Invalidate cache for specific file/section"""
        key = self._get_cache_key(file_path, section)
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            del self.access_times[key]

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()
        self.access_times.clear()

class ConfigFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration changes"""

    def __init__(self, config_loader):
        self.config_loader = config_loader

    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            file_path = Path(event.src_path)
            logger.info(f"Configuration file changed: {file_path}")
            self.config_loader.invalidate_cache(file_path)

class OptimizedConfigLoader:
    """Optimized configuration loader with lazy loading and caching"""

    # Define critical vs non-critical sections
    CRITICAL_SECTIONS = {
        'app', 'server', 'auth', 'providers', 'logging',
        'rate_limit', 'circuit_breaker', 'health_check'
    }

    NON_CRITICAL_SECTIONS = {
        'telemetry', 'chaos_engineering', 'templates',
        'condensation', 'caching', 'memory', 'http_client',
        'load_testing', 'network_simulation'
    }

    def __init__(self, config_path: Path, enable_watching: bool = True):
        self.config_path = config_path
        self.cache = ConfigCache()
        self.timings: List[ConfigTiming] = []
        self._loaded_sections: Set[str] = set()
        self._full_config: Optional[Dict[str, Any]] = None
        self._file_hash: Optional[str] = None
        self._executor = ThreadPoolExecutor(max_workers=4)

        # File watching
        if enable_watching:
            self._setup_file_watching()

    def _setup_file_watching(self):
        """Setup file system watching for config changes"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog not available, file watching disabled")
            self.observer = None
            return

        try:
            self.observer = Observer()
            self.watcher = ConfigFileWatcher(self)
            self.observer.schedule(self.watcher, str(self.config_path.parent), recursive=False)
            self.observer.start()
        except Exception as e:
            logger.warning(f"Failed to setup file watching: {e}")
            self.observer = None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for change detection"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    async def _load_file_async(self, file_path: Path) -> Dict[str, Any]:
        """Asynchronously load configuration file"""
        loop = asyncio.get_event_loop()

        def _sync_load():
            start_time = time.time()
            file_size = file_path.stat().st_size

            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {file_path.suffix}")

            end_time = time.time()
            self.timings.append(ConfigTiming(
                start_time=start_time,
                end_time=end_time,
                file_size=file_size,
                cache_hit=False,
                lazy_loaded=False
            ))

            return data

        return await loop.run_in_executor(self._executor, _sync_load)

    async def load_critical_config(self) -> Dict[str, Any]:
        """Load only critical configuration sections"""
        cache_key = f"critical:{self.config_path}"

        # Check cache first
        cached = self.cache.get(self.config_path, "critical")
        if cached:
            self.timings.append(ConfigTiming(
                start_time=time.time(),
                end_time=time.time(),
                file_size=0,
                cache_hit=True,
                lazy_loaded=True
            ))
            return cached

        # Load full config and extract critical sections
        full_config = await self._load_file_async(self.config_path)
        critical_config = {
            key: value for key, value in full_config.items()
            if key in self.CRITICAL_SECTIONS
        }

        # Cache the result
        self.cache.set(self.config_path, critical_config, "critical")
        self._loaded_sections.update(critical_config.keys())

        return critical_config

    async def load_section_lazy(self, section: str) -> Optional[Any]:
        """Lazily load a specific configuration section"""
        if section in self._loaded_sections:
            # Already loaded, return from cache
            cached = self.cache.get(self.config_path, section)
            if cached:
                return cached.get(section)

        # Load full config if not loaded
        if self._full_config is None:
            self._full_config = await self._load_file_async(self.config_path)

        # Extract and cache the section
        if section in self._full_config:
            section_data = {section: self._full_config[section]}
            self.cache.set(self.config_path, section_data, section)
            self._loaded_sections.add(section)
            return self._full_config[section]

        return None

    async def load_full_config(self) -> Dict[str, Any]:
        """Load complete configuration with caching"""
        # Check if file has changed
        current_hash = self._calculate_file_hash(self.config_path)
        if self._file_hash != current_hash:
            self.cache.invalidate(self.config_path)  # Invalidate all cache
            self._file_hash = current_hash
            self._loaded_sections.clear()

        # Check cache
        cached = self.cache.get(self.config_path)
        if cached:
            self.timings.append(ConfigTiming(
                start_time=time.time(),
                end_time=time.time(),
                file_size=0,
                cache_hit=True,
                lazy_loaded=False
            ))
            return cached

        # Load fresh
        config = await self._load_file_async(self.config_path)
        self.cache.set(self.config_path, config)
        self._full_config = config
        self._loaded_sections.update(config.keys())

        return config

    def invalidate_cache(self, file_path: Path = None):
        """Invalidate cache for specific file or all files"""
        if file_path is None or file_path == self.config_path:
            self.cache.clear()
            self._loaded_sections.clear()
            self._full_config = None
            self._file_hash = None

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.timings:
            return {"total_loads": 0, "average_duration_ms": 0, "cache_hit_rate": 0}

        total_loads = len(self.timings)
        cache_hits = sum(1 for t in self.timings if t.cache_hit)
        total_duration = sum(t.duration_ms for t in self.timings)

        return {
            "total_loads": total_loads,
            "average_duration_ms": total_duration / total_loads,
            "cache_hit_rate": cache_hits / total_loads if total_loads > 0 else 0,
            "total_file_size_loaded": sum(t.file_size for t in self.timings),
            "lazy_loads": sum(1 for t in self.timings if t.lazy_loaded)
        }

    async def shutdown(self):
        """Cleanup resources"""
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()

        self._executor.shutdown(wait=True)
        self.cache.clear()

# Global instance
config_loader = OptimizedConfigLoader(Path("config.yaml"))

# Convenience functions
async def load_critical_config() -> Dict[str, Any]:
    """Load critical configuration sections only"""
    return await config_loader.load_critical_config()

async def load_config_section(section: str) -> Optional[Any]:
    """Load a specific configuration section lazily"""
    return await config_loader.load_section_lazy(section)

async def load_full_config() -> Dict[str, Any]:
    """Load complete configuration"""
    return await config_loader.load_full_config()

def get_config_performance_stats() -> Dict[str, Any]:
    """Get configuration loading performance statistics"""
    return config_loader.get_performance_stats()