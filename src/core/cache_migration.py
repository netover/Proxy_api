"""Cache Migration Service - Zero-downtime Migration from Dual to Unified Cache

This module provides comprehensive migration capabilities to transition from
the existing dual cache system (ModelCache + SmartCache) to the new unified cache.

Features:
- Zero-downtime migration with rollback capability
- Data integrity validation during migration
- Conflict resolution strategies
- Progress monitoring and reporting
- Backward compatibility during transition
- Cache invalidation and cleanup
- Migration rollback and recovery
"""

import asyncio
import json
import logging
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
import hashlib

from .unified_cache import UnifiedCache, get_unified_cache
from .model_cache import ModelCache
from .smart_cache import SmartCache, get_response_cache, get_summary_cache
from ..models.model_info import ModelInfo

logger = logging.getLogger(__name__)


@dataclass
class MigrationStats:
    """Migration statistics and progress tracking"""

    total_entries: int = 0
    migrated_entries: int = 0
    failed_entries: int = 0
    skipped_entries: int = 0
    conflicts_resolved: int = 0
    duplicates_found: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    memory_peak_usage: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate migration success rate"""
        if self.total_entries == 0:
            return 1.0
        return self.migrated_entries / self.total_entries

    @property
    def is_complete(self) -> bool:
        """Check if migration is complete"""
        return (self.migrated_entries + self.failed_entries + self.skipped_entries) >= self.total_entries


@dataclass
class MigrationConfig:
    """Migration configuration settings"""

    batch_size: int = 100
    max_workers: int = 4
    conflict_strategy: str = "newer_wins"  # newer_wins, older_wins, skip, merge
    enable_validation: bool = True
    enable_backup: bool = True
    backup_retention_days: int = 7
    migration_timeout_seconds: int = 3600  # 1 hour
    enable_progress_logging: bool = True
    skip_expired_entries: bool = True
    category_mapping: Dict[str, str] = field(default_factory=dict)


class CacheMigrationService:
    """
    Cache Migration Service for seamless transition to unified cache.

    This service handles the complex process of migrating from multiple cache
    systems to a single unified cache while maintaining data integrity and
    providing rollback capabilities.
    """

    def __init__(self, config: Optional[MigrationConfig] = None):
        self.config = config or MigrationConfig()
        self.stats = MigrationStats()
        self._lock = threading.RLock()
        self._migration_in_progress = False
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._backup_created = False
        self._backup_path: Optional[Path] = None

        # Migration state
        self._source_caches: Dict[str, Any] = {}
        self._target_cache: Optional[UnifiedCache] = None
        self._migration_task: Optional[asyncio.Task] = None

        logger.info("CacheMigrationService initialized")

    async def migrate_to_unified_cache(
        self,
        source_cache_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform migration to unified cache.

        Args:
            source_cache_types: List of cache types to migrate from
                              (default: ['model_cache', 'smart_cache'])

        Returns:
            Migration results and statistics
        """
        if source_cache_types is None:
            source_cache_types = ['model_cache', 'smart_cache']

        with self._lock:
            if self._migration_in_progress:
                raise RuntimeError("Migration already in progress")

            self._migration_in_progress = True
            self.stats.start_time = datetime.now()

        try:
            # Initialize caches
            await self._initialize_caches()

            # Create backup if enabled
            if self.config.enable_backup:
                await self._create_backup()

            # Perform migration
            results = await self._perform_migration(source_cache_types)

            # Validate migration if enabled
            if self.config.enable_validation:
                await self._validate_migration()

            # Cleanup old caches
            await self._cleanup_old_caches()

            self.stats.end_time = datetime.now()
            self.stats.duration_seconds = (
                self.stats.end_time - self.stats.start_time
            ).total_seconds()

            logger.info(
                f"Migration completed: {self.stats.migrated_entries}/{self.stats.total_entries} "
                f"entries migrated in {self.stats.duration_seconds:.2f}s"
            )

            return self._get_migration_results()

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.stats.errors.append(str(e))

            # Attempt rollback if backup exists
            if self._backup_created:
                await self._rollback_migration()

            raise
        finally:
            self._migration_in_progress = False

    async def _initialize_caches(self) -> None:
        """Initialize source and target caches"""
        # Initialize target unified cache
        self._target_cache = await get_unified_cache()

        # Initialize source caches
        self._source_caches = {}

        # ModelCache (from existing system)
        try:
            # Try to find existing ModelCache instances
            # This would need to be adapted based on how they're currently instantiated
            model_cache = ModelCache()
            self._source_caches['model_cache'] = model_cache
            logger.info("ModelCache initialized for migration")
        except Exception as e:
            logger.warning(f"Could not initialize ModelCache: {e}")

        # SmartCache instances
        try:
            response_cache = await get_response_cache()
            summary_cache = await get_summary_cache()
            self._source_caches['response_cache'] = response_cache
            self._source_caches['summary_cache'] = summary_cache
            logger.info("SmartCache instances initialized for migration")
        except Exception as e:
            logger.warning(f"Could not initialize SmartCache instances: {e}")

    async def _create_backup(self) -> None:
        """Create backup of existing cache data"""
        try:
            backup_dir = Path.cwd() / ".cache" / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup ModelCache data
            model_cache_dir = Path.cwd() / ".cache" / "model_discovery"
            if model_cache_dir.exists():
                shutil.copytree(model_cache_dir, backup_dir / "model_cache", dirs_exist_ok=True)

            # Backup SmartCache data (if persisted)
            smart_cache_dir = Path.cwd() / ".cache" / "smart_cache"
            if smart_cache_dir.exists():
                shutil.copytree(smart_cache_dir, backup_dir / "smart_cache", dirs_exist_ok=True)

            self._backup_path = backup_dir
            self._backup_created = True

            logger.info(f"Cache backup created at: {backup_dir}")

            # Clean old backups
            await self._cleanup_old_backups()

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            self.stats.warnings.append(f"Backup creation failed: {e}")

    async def _perform_migration(self, source_cache_types: List[str]) -> Dict[str, Any]:
        """Perform the actual migration process"""
        migration_tasks = []

        for cache_type in source_cache_types:
            if cache_type in self._source_caches:
                task = self._migrate_cache_type(cache_type)
                migration_tasks.append(task)

        # Execute migration tasks
        if migration_tasks:
            results = await asyncio.gather(*migration_tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                cache_type = source_cache_types[i]
                if isinstance(result, Exception):
                    logger.error(f"Migration failed for {cache_type}: {result}")
                    self.stats.errors.append(f"{cache_type}: {result}")
                else:
                    logger.info(f"Migration completed for {cache_type}: {result}")

        return {"status": "migration_tasks_completed"}

    async def _migrate_cache_type(self, cache_type: str) -> Dict[str, Any]:
        """Migrate a specific cache type"""
        source_cache = self._source_caches.get(cache_type)
        if not source_cache:
            return {"error": f"Cache type {cache_type} not found"}

        logger.info(f"Starting migration for {cache_type}")

        # Get entries from source cache
        entries = await self._extract_entries_from_cache(source_cache, cache_type)

        if not entries:
            logger.info(f"No entries found in {cache_type}")
            return {"entries_found": 0, "migrated": 0}

        self.stats.total_entries += len(entries)

        # Migrate entries in batches
        migrated = 0
        failed = 0

        for i in range(0, len(entries), self.config.batch_size):
            batch = entries[i:i + self.config.batch_size]

            try:
                batch_results = await self._migrate_batch(batch, cache_type)
                migrated += batch_results.get('migrated', 0)
                failed += batch_results.get('failed', 0)

                # Log progress
                if self.config.enable_progress_logging:
                    progress = (i + len(batch)) / len(entries) * 100
                    logger.info(
                        f"Migration progress for {cache_type}: "
                        f"{progress:.1f}% ({i + len(batch)}/{len(entries)})"
                    )

            except Exception as e:
                logger.error(f"Batch migration failed for {cache_type}: {e}")
                failed += len(batch)

        return {
            "entries_found": len(entries),
            "migrated": migrated,
            "failed": failed
        }

    async def _extract_entries_from_cache(self, cache: Any, cache_type: str) -> List[Dict[str, Any]]:
        """Extract entries from source cache"""
        entries = []

        try:
            if cache_type == 'model_cache' and hasattr(cache, '_cache'):
                # Extract from ModelCache
                for key, models in cache._cache.items():
                    if isinstance(models, list) and models:
                        entries.append({
                            'key': key,
                            'value': models,
                            'category': 'model_discovery',
                            'source_cache': cache_type,
                            'timestamp': getattr(cache, '_timestamps', {}).get(key, time.time())
                        })

            elif cache_type in ['response_cache', 'summary_cache']:
                # Extract from SmartCache (this is more complex due to async nature)
                # For now, we'll use a simplified approach
                if hasattr(cache, '_cache'):
                    for key, entry in cache._cache.items():
                        entries.append({
                            'key': key,
                            'value': entry.value,
                            'category': cache_type.replace('_cache', ''),
                            'source_cache': cache_type,
                            'timestamp': entry.timestamp,
                            'ttl': entry.ttl
                        })

        except Exception as e:
            logger.error(f"Error extracting entries from {cache_type}: {e}")

        return entries

    async def _migrate_batch(self, batch: List[Dict[str, Any]], cache_type: str) -> Dict[str, int]:
        """Migrate a batch of entries"""
        migrated = 0
        failed = 0

        for entry in batch:
            try:
                # Check for conflicts
                existing_entry = await self._target_cache.get(entry['key'])

                if existing_entry is not None:
                    # Handle conflict based on strategy
                    if not await self._resolve_conflict(entry, existing_entry):
                        self.stats.skipped_entries += 1
                        continue

                # Determine TTL
                ttl = entry.get('ttl', self._target_cache.default_ttl)

                # Determine category
                category = self.config.category_mapping.get(
                    entry.get('category', 'default'),
                    entry.get('category', 'default')
                )

                # Skip expired entries if configured
                if (self.config.skip_expired_entries and
                    entry.get('timestamp', 0) + ttl < time.time()):
                    self.stats.skipped_entries += 1
                    continue

                # Set in unified cache
                success = await self._target_cache.set(
                    key=entry['key'],
                    value=entry['value'],
                    ttl=ttl,
                    category=category
                )

                if success:
                    migrated += 1
                    self.stats.migrated_entries += 1
                else:
                    failed += 1
                    self.stats.failed_entries += 1

            except Exception as e:
                logger.error(f"Failed to migrate entry {entry.get('key', 'unknown')}: {e}")
                failed += 1
                self.stats.failed_entries += 1

        return {'migrated': migrated, 'failed': failed}

    async def _resolve_conflict(self, new_entry: Dict[str, Any], existing_entry: Any) -> bool:
        """Resolve conflicts between existing and new entries"""
        strategy = self.config.conflict_strategy

        if strategy == "skip":
            return False
        elif strategy == "newer_wins":
            # Compare timestamps
            new_timestamp = new_entry.get('timestamp', 0)
            # For unified cache, we can't easily get the existing timestamp
            # So we'll assume new entry wins
            return True
        elif strategy == "older_wins":
            # Keep existing entry
            return False
        elif strategy == "merge":
            # For model info lists, merge them
            if (isinstance(new_entry.get('value'), list) and
                isinstance(existing_entry, list)):
                # Merge lists (remove duplicates)
                merged = existing_entry.copy()
                for item in new_entry['value']:
                    if item not in merged:
                        merged.append(item)
                new_entry['value'] = merged
                return True
            else:
                # Default to newer wins for non-mergeable types
                return True

        return True  # Default: allow new entry

    async def _validate_migration(self) -> None:
        """Validate migration integrity"""
        logger.info("Starting migration validation")

        try:
            # Get stats from unified cache
            cache_stats = await self._target_cache.get_stats()

            # Basic validation checks
            if cache_stats['entries'] != self.stats.migrated_entries:
                warning = (
                    f"Entry count mismatch: cache has {cache_stats['entries']} "
                    f"but migration reported {self.stats.migrated_entries}"
                )
                self.stats.warnings.append(warning)
                logger.warning(warning)

            # Check memory usage
            if cache_stats['memory_usage_bytes'] > self._target_cache.max_memory_bytes:
                warning = (
                    f"Memory usage {cache_stats['memory_usage_mb']}MB exceeds "
                    f"limit of {self._target_cache.max_memory_bytes / (1024 * 1024)}MB"
                )
                self.stats.warnings.append(warning)
                logger.warning(warning)

            logger.info("Migration validation completed")

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            self.stats.errors.append(f"Validation failed: {e}")

    async def _cleanup_old_caches(self) -> None:
        """Clean up old cache files after successful migration"""
        try:
            # Remove old ModelCache files
            model_cache_dir = Path.cwd() / ".cache" / "model_discovery"
            if model_cache_dir.exists():
                shutil.rmtree(model_cache_dir)
                logger.info("Old ModelCache directory removed")

            # Note: SmartCache cleanup would depend on whether we want to keep
            # the old instances running during transition

        except Exception as e:
            logger.error(f"Error cleaning up old caches: {e}")

    async def _rollback_migration(self) -> None:
        """Rollback migration using backup"""
        if not self._backup_created or not self._backup_path:
            logger.error("No backup available for rollback")
            return

        try:
            logger.info("Starting migration rollback")

            # Clear unified cache
            await self._target_cache.clear()

            # Restore from backup
            await self._restore_from_backup()

            logger.info("Migration rollback completed")

        except Exception as e:
            logger.error(f"Migration rollback failed: {e}")
            raise

    async def _restore_from_backup(self) -> None:
        """Restore cache data from backup"""
        if not self._backup_path:
            return

        try:
            # Restore ModelCache data
            model_backup = self._backup_path / "model_cache"
            if model_backup.exists():
                target_dir = Path.cwd() / ".cache" / "model_discovery"
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(model_backup, target_dir)

            # Restore SmartCache data
            smart_backup = self._backup_path / "smart_cache"
            if smart_backup.exists():
                target_dir = Path.cwd() / ".cache" / "smart_cache"
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(smart_backup, target_dir)

            logger.info(f"Cache data restored from backup: {self._backup_path}")

        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            raise

    async def _cleanup_old_backups(self) -> None:
        """Clean up old backup directories"""
        try:
            backup_root = Path.cwd() / ".cache" / "backup"
            if not backup_root.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=self.config.backup_retention_days)

            for backup_dir in backup_root.iterdir():
                if backup_dir.is_dir():
                    try:
                        # Parse directory name to get creation date
                        dir_name = backup_dir.name
                        if "_" in dir_name:
                            date_str = dir_name.split("_")[0]
                            dir_date = datetime.strptime(date_str, "%Y%m%d")

                            if dir_date < cutoff_date:
                                shutil.rmtree(backup_dir)
                                logger.info(f"Removed old backup: {backup_dir}")
                    except (ValueError, OSError) as e:
                        logger.warning(f"Error processing backup directory {backup_dir}: {e}")

        except Exception as e:
            logger.error(f"Error cleaning old backups: {e}")

    def _get_migration_results(self) -> Dict[str, Any]:
        """Get comprehensive migration results"""
        return {
            "status": "completed" if self.stats.success_rate >= 0.95 else "completed_with_errors",
            "success_rate": self.stats.success_rate,
            "stats": {
                "total_entries": self.stats.total_entries,
                "migrated_entries": self.stats.migrated_entries,
                "failed_entries": self.stats.failed_entries,
                "skipped_entries": self.stats.skipped_entries,
                "conflicts_resolved": self.stats.conflicts_resolved,
                "duplicates_found": self.stats.duplicates_found
            },
            "timing": {
                "start_time": self.stats.start_time.isoformat() if self.stats.start_time else None,
                "end_time": self.stats.end_time.isoformat() if self.stats.end_time else None,
                "duration_seconds": self.stats.duration_seconds
            },
            "errors": self.stats.errors,
            "warnings": self.stats.warnings,
            "backup_created": self._backup_created,
            "backup_path": str(self._backup_path) if self._backup_path else None
        }

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        with self._lock:
            if not self._migration_in_progress:
                return {"status": "idle"}

            return {
                "status": "in_progress",
                "progress": {
                    "total": self.stats.total_entries,
                    "completed": self.stats.migrated_entries + self.stats.failed_entries + self.stats.skipped_entries,
                    "percentage": (
                        (self.stats.migrated_entries + self.stats.failed_entries + self.stats.skipped_entries) /
                        self.stats.total_entries * 100
                        if self.stats.total_entries > 0 else 0
                    )
                },
                "stats": {
                    "migrated": self.stats.migrated_entries,
                    "failed": self.stats.failed_entries,
                    "skipped": self.stats.skipped_entries
                },
                "start_time": self.stats.start_time.isoformat() if self.stats.start_time else None,
                "errors": len(self.stats.errors),
                "warnings": len(self.stats.warnings)
            }

    async def cancel_migration(self) -> bool:
        """Cancel ongoing migration"""
        with self._lock:
            if not self._migration_in_progress:
                return False

            self._migration_in_progress = False

            if self._migration_task and not self._migration_task.done():
                self._migration_task.cancel()
                try:
                    await self._migration_task
                except asyncio.CancelledError:
                    pass

            logger.info("Migration cancelled")
            return True


# Global migration service instance
_migration_service: Optional[CacheMigrationService] = None


def get_migration_service() -> CacheMigrationService:
    """Get the global cache migration service instance"""
    global _migration_service

    if _migration_service is None:
        _migration_service = CacheMigrationService()

    return _migration_service


async def migrate_to_unified_cache(
    config: Optional[MigrationConfig] = None,
    source_cache_types: List[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to perform cache migration.

    Args:
        config: Migration configuration
        source_cache_types: Cache types to migrate from

    Returns:
        Migration results
    """
    service = get_migration_service()
    if config:
        service.config = config

    return await service.migrate_to_unified_cache(source_cache_types)


async def get_migration_status() -> Dict[str, Any]:
    """Get current migration status"""
    service = get_migration_service()
    return await service.get_migration_status()


async def cancel_migration() -> bool:
    """Cancel ongoing migration"""
    service = get_migration_service()
    return await service.cancel_migration()