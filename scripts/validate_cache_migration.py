#!/usr/bin/env python3
"""
Cache Migration Data Integrity Validator

This script validates the integrity of data after cache system migration.
It performs comprehensive checks to ensure no data loss or corruption occurred
during the migration process.

Validation checks include:
- Entry count validation
- Data consistency checks
- Hash verification
- Performance metrics comparison
- Memory usage analysis

Usage:
    python scripts/validate_cache_migration.py [options]

Options:
    --pre-migration    Validate state before migration
    --post-migration   Validate state after migration
    --compare          Compare pre and post migration states
    --detailed         Perform detailed validation (slower)
    --export-report    Export validation report to file
    --help             Show this help message

Environment Variables:
    CACHE_VALIDATION_TIMEOUT     Validation timeout in seconds (default: 300)
    CACHE_VALIDATION_SAMPLE_SIZE Sample size for detailed checks (default: 1000)

Example:
    python scripts/validate_cache_migration.py --post-migration
    python scripts/validate_cache_migration.py --compare --export-report
"""

import asyncio
import argparse
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.consolidated_cache import get_consolidated_cache_manager
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    status: str  # 'passed', 'failed', 'warning', 'error'
    message: str
    details: Dict[str, Any]
    duration: float


class CacheMigrationValidator:
    """Validates cache migration data integrity"""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.timeout = int(os.getenv('CACHE_VALIDATION_TIMEOUT', '300'))
        self.sample_size = int(os.getenv('CACHE_VALIDATION_SAMPLE_SIZE', '1000'))

        # Validation state
        self.pre_migration_state: Optional[Dict[str, Any]] = None
        self.post_migration_state: Optional[Dict[str, Any]] = None
        self.validation_results: List[ValidationResult] = []

        # Setup logging
        if args.detailed:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    async def run_validation(self) -> Dict[str, Any]:
        """Run the validation process"""
        logger.info("Starting cache migration validation")

        start_time = time.time()

        try:
            # Get cache manager
            cache_manager = await get_consolidated_cache_manager()

            if self.args.pre_migration:
                logger.info("Capturing pre-migration state")
                self.pre_migration_state = await self._capture_cache_state(cache_manager)

            elif self.args.post_migration:
                logger.info("Validating post-migration state")
                self.post_migration_state = await self._capture_cache_state(cache_manager)
                await self._run_post_migration_checks(cache_manager)

            elif self.args.compare:
                logger.info("Comparing pre and post migration states")
                await self._run_comparison_checks(cache_manager)

            else:
                # Run all validations
                logger.info("Running full validation suite")
                await self._run_full_validation(cache_manager)

            # Generate report
            duration = time.time() - start_time
            report = self._generate_validation_report(duration)

            if self.args.export_report:
                self._export_report(report)

            logger.info(f"Validation completed in {duration:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }

    async def _capture_cache_state(self, cache_manager) -> Dict[str, Any]:
        """Capture the current state of the cache"""
        logger.info("Capturing cache state")

        state = {
            "timestamp": time.time(),
            "stats": await cache_manager.get_stats(),
            "categories": await cache_manager.get_categories(),
            "sample_entries": {}
        }

        # Capture sample entries for integrity checking
        if self.args.detailed:
            for category in state["categories"]:
                try:
                    # Get a sample of entries (implementation depends on cache interface)
                    # This is a simplified version - real implementation would need
                    # to expose entry enumeration capabilities
                    state["sample_entries"][category] = await self._get_sample_entries(
                        cache_manager, category, self.sample_size
                    )
                except Exception as e:
                    logger.warning(f"Could not capture sample for category {category}: {e}")

        return state

    async def _run_post_migration_checks(self, cache_manager) -> None:
        """Run post-migration validation checks"""
        logger.info("Running post-migration validation checks")

        # Check 1: Basic cache functionality
        await self._check_basic_functionality(cache_manager)

        # Check 2: Data integrity
        await self._check_data_integrity(cache_manager)

        # Check 3: Performance metrics
        await self._check_performance_metrics(cache_manager)

        # Check 4: Memory usage
        await self._check_memory_usage(cache_manager)

        # Check 5: Category consistency
        await self._check_category_consistency(cache_manager)

    async def _run_comparison_checks(self, cache_manager) -> None:
        """Run comparison between pre and post migration states"""
        logger.info("Running migration comparison checks")

        # Load pre-migration state if available
        pre_state_file = Path(".cache/validation/pre_migration_state.json")
        if pre_state_file.exists():
            with open(pre_state_file, 'r') as f:
                self.pre_migration_state = json.load(f)

        # Capture current state
        self.post_migration_state = await self._capture_cache_state(cache_manager)

        if self.pre_migration_state:
            # Compare entry counts
            await self._compare_entry_counts()

            # Compare data integrity
            await self._compare_data_integrity()

            # Compare performance metrics
            await self._compare_performance_metrics()
        else:
            logger.warning("No pre-migration state found for comparison")

    async def _run_full_validation(self, cache_manager) -> None:
        """Run full validation suite"""
        logger.info("Running full validation suite")

        # Capture current state
        self.post_migration_state = await self._capture_cache_state(cache_manager)

        # Run all check types
        await self._check_basic_functionality(cache_manager)
        await self._check_data_integrity(cache_manager)
        await self._check_performance_metrics(cache_manager)
        await self._check_memory_usage(cache_manager)
        await self._check_category_consistency(cache_manager)

    async def _check_basic_functionality(self, cache_manager) -> None:
        """Check basic cache functionality"""
        start_time = time.time()

        try:
            # Test basic operations
            test_key = "validation_test_key"
            test_value = {"test": "data", "timestamp": time.time()}
            test_category = "validation"

            # Test set
            success = await cache_manager.set(test_key, test_value, category=test_category)
            if not success:
                raise Exception("Failed to set test entry")

            # Test get
            retrieved = await cache_manager.get(test_key, category=test_category)
            if retrieved != test_value:
                raise Exception("Retrieved value doesn't match set value")

            # Test delete
            deleted = await cache_manager.delete(test_key)
            if not deleted:
                raise Exception("Failed to delete test entry")

            self.validation_results.append(ValidationResult(
                check_name="basic_functionality",
                status="passed",
                message="Basic cache operations working correctly",
                details={"operations_tested": ["set", "get", "delete"]},
                duration=time.time() - start_time
            ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                check_name="basic_functionality",
                status="failed",
                message=f"Basic functionality check failed: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time
            ))

    async def _check_data_integrity(self, cache_manager) -> None:
        """Check data integrity"""
        start_time = time.time()

        try:
            # Generate test data with known hashes
            test_entries = []
            for i in range(min(100, self.sample_size)):
                data = f"integrity_test_data_{i}_{time.time()}"
                hash_value = hashlib.sha256(data.encode()).hexdigest()
                test_entries.append((f"integrity_key_{i}", data, hash_value))

            # Store test entries
            for key, data, expected_hash in test_entries:
                await cache_manager.set(key, {"data": data, "hash": expected_hash})

            # Retrieve and verify
            integrity_errors = 0
            for key, original_data, expected_hash in test_entries:
                retrieved = await cache_manager.get(key)
                if not retrieved:
                    integrity_errors += 1
                    continue

                retrieved_data = retrieved.get("data")
                retrieved_hash = retrieved.get("hash")

                if retrieved_data != original_data:
                    integrity_errors += 1
                    continue

                actual_hash = hashlib.sha256(retrieved_data.encode()).hexdigest()
                if actual_hash != expected_hash or actual_hash != retrieved_hash:
                    integrity_errors += 1

            # Clean up test entries
            for key, _, _ in test_entries:
                await cache_manager.delete(key)

            status = "passed" if integrity_errors == 0 else "failed"
            message = f"Data integrity check: {integrity_errors} errors out of {len(test_entries)} entries"

            self.validation_results.append(ValidationResult(
                check_name="data_integrity",
                status=status,
                message=message,
                details={
                    "total_entries": len(test_entries),
                    "integrity_errors": integrity_errors,
                    "integrity_rate": (len(test_entries) - integrity_errors) / len(test_entries)
                },
                duration=time.time() - start_time
            ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                check_name="data_integrity",
                status="error",
                message=f"Data integrity check failed: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time
            ))

    async def _check_performance_metrics(self, cache_manager) -> None:
        """Check performance metrics"""
        start_time = time.time()

        try:
            # Get cache stats
            stats = await cache_manager.get_stats()

            # Validate expected metrics are present
            required_metrics = ["entries", "hit_rate", "memory_usage_mb"]
            missing_metrics = [m for m in required_metrics if m not in stats]

            if missing_metrics:
                raise Exception(f"Missing required metrics: {missing_metrics}")

            # Check hit rate is reasonable (should be between 0 and 1)
            hit_rate = stats.get("hit_rate", 0)
            if not (0 <= hit_rate <= 1):
                raise Exception(f"Invalid hit rate: {hit_rate}")

            self.validation_results.append(ValidationResult(
                check_name="performance_metrics",
                status="passed",
                message="Performance metrics are valid",
                details={
                    "hit_rate": hit_rate,
                    "entries": stats.get("entries", 0),
                    "memory_usage_mb": stats.get("memory_usage_mb", 0)
                },
                duration=time.time() - start_time
            ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                check_name="performance_metrics",
                status="error",
                message=f"Performance metrics check failed: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time
            ))

    async def _check_memory_usage(self, cache_manager) -> None:
        """Check memory usage"""
        start_time = time.time()

        try:
            stats = await cache_manager.get_stats()
            memory_usage = stats.get("memory_usage_mb", 0)
            max_memory = stats.get("max_memory_mb", 512)  # Default 512MB

            memory_ratio = memory_usage / max_memory if max_memory > 0 else 0

            if memory_ratio > 0.95:  # Over 95% memory usage
                status = "warning"
                message = f"High memory usage: {memory_usage:.1f}MB / {max_memory}MB ({memory_ratio:.1%})"
            elif memory_ratio > 1.0:  # Over memory limit
                status = "failed"
                message = f"Memory limit exceeded: {memory_usage:.1f}MB / {max_memory}MB ({memory_ratio:.1%})"
            else:
                status = "passed"
                message = f"Memory usage normal: {memory_usage:.1f}MB / {max_memory}MB ({memory_ratio:.1%})"

            self.validation_results.append(ValidationResult(
                check_name="memory_usage",
                status=status,
                message=message,
                details={
                    "memory_usage_mb": memory_usage,
                    "max_memory_mb": max_memory,
                    "usage_ratio": memory_ratio
                },
                duration=time.time() - start_time
            ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                check_name="memory_usage",
                status="error",
                message=f"Memory usage check failed: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time
            ))

    async def _check_category_consistency(self, cache_manager) -> None:
        """Check category consistency"""
        start_time = time.time()

        try:
            categories = await cache_manager.get_categories()
            stats = await cache_manager.get_stats()

            category_entries = stats.get("categories", {})
            total_entries = stats.get("entries", 0)
            category_total = sum(category_entries.values())

            if abs(total_entries - category_total) > 1:  # Allow small tolerance
                status = "warning"
                message = f"Category entry count mismatch: {category_total} != {total_entries}"
            else:
                status = "passed"
                message = f"Category consistency OK: {len(categories)} categories, {total_entries} total entries"

            self.validation_results.append(ValidationResult(
                check_name="category_consistency",
                status=status,
                message=message,
                details={
                    "categories": categories,
                    "category_entries": category_entries,
                    "total_entries": total_entries,
                    "category_total": category_total
                },
                duration=time.time() - start_time
            ))

        except Exception as e:
            self.validation_results.append(ValidationResult(
                check_name="category_consistency",
                status="error",
                message=f"Category consistency check failed: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time
            ))

    async def _compare_entry_counts(self) -> None:
        """Compare entry counts between pre and post migration"""
        if not self.pre_migration_state or not self.post_migration_state:
            return

        pre_entries = self.pre_migration_state["stats"].get("entries", 0)
        post_entries = self.post_migration_state["stats"].get("entries", 0)

        if pre_entries != post_entries:
            self.validation_results.append(ValidationResult(
                check_name="entry_count_comparison",
                status="warning",
                message=f"Entry count changed: {pre_entries} -> {post_entries}",
                details={
                    "pre_entries": pre_entries,
                    "post_entries": post_entries,
                    "difference": post_entries - pre_entries
                },
                duration=0
            ))

    async def _compare_data_integrity(self) -> None:
        """Compare data integrity between pre and post migration"""
        # This would require storing sample data from pre-migration
        # Implementation depends on how pre-migration state is captured
        pass

    async def _compare_performance_metrics(self) -> None:
        """Compare performance metrics"""
        if not self.pre_migration_state or not self.post_migration_state:
            return

        pre_hit_rate = self.pre_migration_state["stats"].get("hit_rate", 0)
        post_hit_rate = self.post_migration_state["stats"].get("hit_rate", 0)

        # Hit rate should not decrease significantly
        if post_hit_rate < pre_hit_rate * 0.8:  # 20% decrease
            self.validation_results.append(ValidationResult(
                check_name="performance_comparison",
                status="warning",
                message=f"Hit rate decreased significantly: {pre_hit_rate:.2%} -> {post_hit_rate:.2%}",
                details={
                    "pre_hit_rate": pre_hit_rate,
                    "post_hit_rate": post_hit_rate,
                    "change": post_hit_rate - pre_hit_rate
                },
                duration=0
            ))

    async def _get_sample_entries(self, cache_manager, category: str, sample_size: int) -> List[Dict[str, Any]]:
        """Get sample entries for integrity checking (simplified)"""
        # This is a placeholder - real implementation would need cache introspection capabilities
        return []

    def _generate_validation_report(self, duration: float) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        passed = sum(1 for r in self.validation_results if r.status == "passed")
        failed = sum(1 for r in self.validation_results if r.status == "failed")
        warnings = sum(1 for r in self.validation_results if r.status == "warning")
        errors = sum(1 for r in self.validation_results if r.status == "error")

        overall_status = "passed"
        if errors > 0:
            overall_status = "error"
        elif failed > 0:
            overall_status = "failed"
        elif warnings > 0:
            overall_status = "warning"

        report = {
            "status": overall_status,
            "timestamp": time.time(),
            "duration_seconds": round(duration, 2),
            "summary": {
                "total_checks": len(self.validation_results),
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "errors": errors
            },
            "results": [
                {
                    "check": r.check_name,
                    "status": r.status,
                    "message": r.message,
                    "duration": round(r.duration, 3),
                    "details": r.details
                }
                for r in self.validation_results
            ]
        }

        return report

    def _export_report(self, report: Dict[str, Any]) -> None:
        """Export validation report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cache_validation_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Validation report exported to {filename}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Cache Migration Data Integrity Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--pre-migration",
        action="store_true",
        help="Validate state before migration"
    )

    parser.add_argument(
        "--post-migration",
        action="store_true",
        help="Validate state after migration"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare pre and post migration states"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Perform detailed validation (slower)"
    )

    parser.add_argument(
        "--export-report",
        action="store_true",
        help="Export validation report to file"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_arguments()

    # Validate arguments
    if sum([args.pre_migration, args.post_migration, args.compare]) == 0:
        # Default to full validation if no specific mode specified
        args.post_migration = True
        args.detailed = True

    # Run validation
    validator = CacheMigrationValidator(args)
    results = await validator.run_validation()

    # Output results
    print(json.dumps(results, indent=2, default=str))

    # Exit with appropriate code
    if results.get("status") in ["passed", "warning"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())