#!/usr/bin/env python3
"""
Simple test script to verify enhanced ConsolidatedCache functionality
"""

import asyncio
import sys
import os

from src.core.cache.consolidated import ConsolidatedCacheManager, CacheCategory
from src.core.cache.interface import CacheStats


async def test_enhanced_cache():
    """Test enhanced cache functionality"""

    print("=== Testing Enhanced ConsolidatedCacheManager ===\n")

    # Create enhanced cache manager
    cache = ConsolidatedCacheManager(
        max_memory_mb=64,
        enable_tiering=True,
        enable_warming=True,
        enable_monitoring=True,
        enable_migration=True,
    )

    try:
        # Initialize
        await cache.initialize()
        print("✓ Cache initialized successfully")

        # Test category-based operations
        print("\n--- Testing Category-Based Operations ---")

        # Test models category
        test_models = [
            {"id": "gpt-4", "provider": "openai"},
            {"id": "claude-3", "provider": "anthropic"},
        ]
        success = await cache.set(
            "models:openai", test_models, category=CacheCategory.MODELS
        )
        print(f"✓ Set models: {success}")

        retrieved = await cache.get(
            "models:openai", category=CacheCategory.MODELS
        )
        print(
            f"✓ Retrieved models: {len(retrieved) if retrieved else 0} items"
        )

        # Test responses category
        test_response = {"result": "test response", "status": "success"}
        success = await cache.set(
            "response:123", test_response, category=CacheCategory.RESPONSES
        )
        print(f"✓ Set response: {success}")

        # Test summaries category
        test_summary = {"summary": "test summary", "confidence": 0.95}
        success = await cache.set(
            "summary:456", test_summary, category=CacheCategory.SUMMARIES
        )
        print(f"✓ Set summary: {success}")

        # Test metrics category
        test_metrics = {"hit_rate": 0.85, "response_time": 150}
        success = await cache.set(
            "metrics:api", test_metrics, category=CacheCategory.METRICS
        )
        print(f"✓ Set metrics: {success}")

        # Test tiering
        print("\n--- Testing Tiering Logic ---")

        # Get tier info for different categories
        print(
            f"Models tier: {cache._get_tier_for_category(CacheCategory.MODELS).value}"
        )
        print(
            f"Responses tier: {cache._get_tier_for_category(CacheCategory.RESPONSES).value}"
        )
        print(
            f"Summaries tier: {cache._get_tier_for_category(CacheCategory.SUMMARIES).value}"
        )
        print(
            f"Analytics tier: {cache._get_tier_for_category(CacheCategory.ANALYTICS).value}"
        )

        # Test backward compatibility
        print("\n--- Testing Backward Compatibility ---")

        # Test legacy methods
        success = await cache.set_models(
            "anthropic", "https://api.anthropic.com", [{"id": "claude-2"}]
        )
        print(f"✓ Legacy set_models: {success}")

        models = await cache.get_models(
            "anthropic", "https://api.anthropic.com"
        )
        print(f"✓ Legacy get_models: {len(models) if models else 0} items")

        success = await cache.set_response(
            "legacy:resp:789", {"legacy": "response"}
        )
        print(f"✓ Legacy set_response: {success}")

        response = await cache.get_response("legacy:resp:789")
        print(f"✓ Legacy get_response: {'success' if response else 'failed'}")

        # Test statistics
        print("\n--- Testing Enhanced Statistics ---")
        stats = await cache.get_stats()
        print("Cache Statistics:")
        print(f"  Total entries: {stats.get('entries', 0)}")
        print(f"  Manager type: {stats.get('manager_type', 'unknown')}")
        print(f"  Tiering enabled: {stats.get('tiering_enabled', False)}")
        print(f"  Hit rate: {stats.get('hit_rate', 0):.2%}")

        if stats.get("category_tiers"):
            print("  Category tiers:")
            for cat, tier in stats["category_tiers"].items():
                print(f"    {cat}: {tier}")

        # Test categories
        print("\n--- Testing Categories ---")
        categories = await cache.get_categories()
        print(f"All categories: {categories}")

        # Test category clearing
        cleared = await cache.clear_category(CacheCategory.RESPONSES)
        print(f"✓ Cleared {cleared} items from responses category")

        print("\n=== All tests completed successfully! ===")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await cache.stop()

    return True


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_cache())
    sys.exit(0 if success else 1)
