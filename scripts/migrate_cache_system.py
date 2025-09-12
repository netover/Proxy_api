#!/usr/bin/env python3
"""
Cache System Migration Script

This script performs zero-downtime migration from the legacy cache systems
(ModelCache, SmartCache) to the new ConsolidatedCache system.

Usage:
    python scripts/migrate_cache_system.py [options]

Options:
    --dry-run          Perform dry run without actual migration
    --backup-only      Only create backup, don't migrate
    --force            Force migration even if already migrated
    --verbose          Enable verbose output
    --help             Show this help message

Environment Variables:
    CACHE_MIGRATION_BACKUP_DIR    Directory for migration backups (default: .cache/migration_backup)
    CACHE_MIGRATION_TIMEOUT       Migration timeout in seconds (default: 3600)
    CACHE_MIGRATION_BATCH_SIZE    Batch size for migration (default: 100)

Example:
    python scripts/migrate_cache_system.py --verbose
    python scripts/migrate_cache_system.py --dry-run
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.consolidated_cache import (
    get_consolidated_cache_manager,
    ConsolidatedCacheManager
)
from src.core.cache_migration import CacheMigrationService, MigrationConfig
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class CacheMigrationRunner:
    """Handles the cache system migration process"""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.backup_dir = Path(os.getenv(
            'CACHE_MIGRATION_BACKUP_DIR',
            '.cache/migration_backup'
        ))
        self.timeout = int(os.getenv('CACHE_MIGRATION_TIMEOUT', '3600'))
        self.batch_size = int(os.getenv('CACHE_MIGRATION_BATCH_SIZE', '100'))

        # Setup logging
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    async def run_migration(self) -> Dict[str, Any]:
        """Run the complete migration process"""
        logger.info("Starting cache system migration")

        start_time = time.time()

        try:
            # Initialize consolidated cache
            logger.info("Initializing consolidated cache manager")
            cache_manager = await get_consolidated_cache_manager()

            # Check if already migrated
            if not self.args.force and await self._is_already_migrated(cache_manager):
                logger.info("Cache system already migrated, skipping")
                return {
                    "status": "skipped",
                    "message": "Already migrated",
                    "duration": time.time() - start_time
                }

            # Create migration configuration
            config = MigrationConfig(
                batch_size=self.batch_size,
                enable_backup=not self.args.backup_only,
                migration_timeout_seconds=self.timeout,
                enable_progress_logging=self.args.verbose
            )

            # Initialize migration service
            migration_service = CacheMigrationService(config)

            if self.args.dry_run:
                logger.info("Performing dry run migration")
                results = await self._perform_dry_run()
            else:
                logger.info("Performing actual migration")
                results = await migration_service.migrate_to_unified_cache([
                    'model_cache',
                    'response_cache',
                    'summary_cache'
                ])

            # Validate migration
            if not self.args.dry_run and not self.args.backup_only:
                logger.info("Validating migration")
                validation_results = await migration_service._validate_migration()
                results['validation'] = validation_results

            # Generate report
            duration = time.time() - start_time
            report = self._generate_migration_report(results, duration)

            logger.info(f"Migration completed in {duration:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time
            }

    async def _is_already_migrated(self, cache_manager: ConsolidatedCacheManager) -> bool:
        """Check if migration has already been performed"""
        try:
            stats = await cache_manager.get_stats()
            return stats.get('migrated', False)
        except Exception:
            return False

    async def _perform_dry_run(self) -> Dict[str, Any]:
        """Perform a dry run migration without actual data transfer"""
        logger.info("Analyzing legacy cache systems for migration")

        results = {
            "status": "dry_run",
            "analysis": {},
            "estimated_entries": 0,
            "estimated_size_mb": 0
        }

        try:
            # Analyze ModelCache if available
            try:
                from src.core.model_cache import ModelCache
                model_cache = ModelCache()
                model_stats = model_cache.get_stats()
                results["analysis"]["model_cache"] = model_stats
                results["estimated_entries"] += model_stats.get("size", 0)
                logger.info(f"ModelCache analysis: {model_stats}")
            except Exception as e:
                logger.warning(f"Could not analyze ModelCache: {e}")

            # Analyze SmartCache instances if available
            try:
                from src.core.smart_cache import get_response_cache, get_summary_cache
                response_cache = await get_response_cache()
                summary_cache = await get_summary_cache()

                response_stats = response_cache.get_stats()
                summary_stats = summary_cache.get_stats()

                results["analysis"]["response_cache"] = response_stats
                results["analysis"]["summary_cache"] = summary_stats
                results["estimated_entries"] += len(response_cache._cache)
                results["estimated_entries"] += len(summary_cache._cache)
                logger.info(f"Response cache analysis: {response_stats}")
                logger.info(f"Summary cache analysis: {summary_stats}")
            except Exception as e:
                logger.warning(f"Could not analyze SmartCache: {e}")

        except Exception as e:
            logger.error(f"Dry run analysis failed: {e}")

        return results

    def _generate_migration_report(self, results: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """Generate a comprehensive migration report"""
        report = {
            "status": results.get("status", "unknown"),
            "duration_seconds": round(duration, 2),
            "timestamp": time.time(),
            "results": results
        }

        # Add summary statistics
        if "stats" in results:
            stats = results["stats"]
            report["summary"] = {
                "total_entries": stats.get("total_entries", 0),
                "migrated_entries": stats.get("migrated_entries", 0),
                "failed_entries": stats.get("failed_entries", 0),
                "skipped_entries": stats.get("skipped_entries", 0),
                "success_rate": stats.get("migrated_entries", 0) / max(stats.get("total_entries", 1), 1)
            }

        # Add recommendations
        report["recommendations"] = self._generate_recommendations(results)

        return report

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate post-migration recommendations"""
        recommendations = []

        if results.get("status") == "completed":
            recommendations.append("Migration completed successfully")
            recommendations.append("Consider running performance benchmarks before/after")
            recommendations.append("Monitor cache hit rates for the first 24 hours")
            recommendations.append("Update any custom cache configurations to use consolidated cache")

        if results.get("stats", {}).get("failed_entries", 0) > 0:
            recommendations.append("Some entries failed to migrate - check logs for details")
            recommendations.append("Consider manual migration for failed entries if critical")

        if results.get("backup_created"):
            recommendations.append("Backup created - keep until migration is validated in production")

        return recommendations


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Cache System Migration Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry run without actual migration"
    )

    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Only create backup, don't migrate"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if already migrated"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_arguments()

    # Validate arguments
    if args.backup_only and args.dry_run:
        logger.error("Cannot use --backup-only with --dry-run")
        sys.exit(1)

    # Run migration
    runner = CacheMigrationRunner(args)
    results = await runner.run_migration()

    # Output results
    print(json.dumps(results, indent=2, default=str))

    # Exit with appropriate code
    if results.get("status") in ["completed", "skipped"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())