#!/usr/bin/env python3
"""
Model Discovery Demo - Complete usage examples for the ProxyAPI Model Discovery system.

This script demonstrates all major features of the model discovery system including:
- Basic model discovery
- Advanced filtering
- Caching strategies
- Performance monitoring
- Custom provider integration
- Batch operations
- Real-time updates
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

# Import our discovery components
from src.core.model_discovery import ModelDiscovery
from src.core.cache_manager import CacheManager
from src.core.provider_factory import ProviderFactory
from src.models.model_info import ModelInfo
from src.models.requests import DiscoveryRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DemoConfig:
    """Configuration for demo scenarios."""
    enable_caching: bool = True
    cache_ttl: int = 300
    timeout: int = 30
    max_retries: int = 3
    enable_monitoring: bool = True


class ModelDiscoveryDemo:
    """Comprehensive demo class showcasing all model discovery features."""
    
    def __init__(self, config: DemoConfig = DemoConfig()):
        self.config = config
        self.cache_manager = CacheManager(
            ttl=config.cache_ttl,
            enable_monitoring=config.enable_monitoring
        )
        self.provider_factory = ProviderFactory()
        self.discovery = ModelDiscovery(
            cache_manager=self.cache_manager,
            provider_factory=self.provider_factory,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    
    async def demo_basic_discovery(self):
        """Demonstrate basic model discovery."""
        print("\n" + "="*60)
        print("DEMO 1: Basic Model Discovery")
        print("="*60)
        
        # Basic configuration
        config = {
            "providers": {
                "openai": {
                    "api_key": "demo-key",  # In real usage, use environment variables
                    "enabled": True
                },
                "anthropic": {
                    "api_key": "demo-key",
                    "enabled": True
                }
            }
        }
        
        # Mock provider responses for demo
        mock_models = [
            ModelInfo(
                id="gpt-4",
                name="GPT-4",
                provider="openai",
                context_length=8192,
                max_tokens=4096,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.03,
                output_cost=0.06,
                description="Most capable GPT-4 model"
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.0015,
                output_cost=0.002
            ),
            ModelInfo(
                id="claude-3-opus-20240229",
                name="Claude 3 Opus",
                provider="anthropic",
                context_length=200000,
                max_tokens=4096,
                supports_chat=True,
                supports_completion=False,
                input_cost=0.015,
                output_cost=0.075
            )
        ]
        
        # Simulate discovery with mock data
        print("Discovering models from configured providers...")
        
        # For demo purposes, we'll use the mock data
        discovered_models = mock_models
        
        print(f"\n✅ Discovered {len(discovered_models)} models:")
        for model in discovered_models:
            print(f"  📊 {model.name} ({model.provider})")
            print(f"     Context: {model.context_length:,} tokens")
            print(f"     Cost: ${model.input_cost}/1K input, ${model.output_cost}/1K output")
            print(f"     Features: {'Chat' if model.supports_chat else ''} {'Completion' if model.supports_completion else ''}")
            print()
        
        return discovered_models
    
    async def demo_advanced_filtering(self, models: List[ModelInfo]):
        """Demonstrate advanced filtering capabilities."""
        print("\n" + "="*60)
        print("DEMO 2: Advanced Filtering")
        print("="*60)
        
        # Filter 1: Chat-capable models under $0.01 per 1K tokens
        cheap_chat_models = [
            m for m in models 
            if m.supports_chat and m.input_cost < 0.01
        ]
        
        print("💰 Cheap chat models (< $0.01/1K tokens):")
        for model in cheap_chat_models:
            print(f"  • {model.name} - ${model.input_cost}/1K tokens")
        
        # Filter 2: High-context models (> 50K tokens)
        high_context_models = [
            m for m in models 
            if m.context_length > 50000
        ]
        
        print("\n📏 High-context models (> 50K tokens):")
        for model in high_context_models:
            print(f"  • {model.name} - {model.context_length:,} tokens")
        
        # Filter 3: Multi-modal models
        multimodal_models = [
            m for m in models 
            if "vision" in m.description.lower() or "image" in m.description.lower()
        ]
        
        print("\n🖼️  Multi-modal models:")
        for model in multimodal_models:
            print(f"  • {model.name}")
        
        return {
            "cheap_chat": cheap_chat_models,
            "high_context": high_context_models,
            "multimodal": multimodal_models
        }
    
    async def demo_caching_strategies(self):
        """Demonstrate different caching strategies."""
        print("\n" + "="*60)
        print("DEMO 3: Caching Strategies")
        print("="*60)
        
        # Create a new cache manager with different TTLs
        short_cache = CacheManager(ttl=60)  # 1 minute
        long_cache = CacheManager(ttl=3600)  # 1 hour
        
        # Simulate cache operations
        test_data = {"models": [{"id": "test-model", "name": "Test Model"}]}
        
        print("🔄 Testing cache TTL strategies:")
        
        # Short TTL cache
        start_time = time.time()
        short_cache.set("short_ttl", test_data)
        cached_data = short_cache.get("short_ttl")
        print(f"  Short TTL (60s): {'✅ Hit' if cached_data else '❌ Miss'}")
        
        # Long TTL cache
        long_cache.set("long_ttl", test_data)
        cached_data = long_cache.get("long_ttl")
        print(f"  Long TTL (3600s): {'✅ Hit' if cached_data else '❌ Miss'}")
        
        # Cache statistics
        stats = self.cache_manager.get_stats()
        print(f"\n📊 Cache Statistics:")
        print(f"  Hits: {stats.get('hits', 0)}")
        print(f"  Misses: {stats.get('misses', 0)}")
        print(f"  Hit Rate: {stats.get('hit_rate', 0):.1f}%")
        
        return stats
    
    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring and benchmarking."""
        print("\n" + "="*60)
        print("DEMO 4: Performance Monitoring")
        print("="*60)
        
        # Simulate discovery timing
        async def measure_discovery_time(provider: str, model_count: int):
            start_time = time.time()
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "provider": provider,
                "models_found": model_count,
                "duration_ms": duration * 1000,
                "models_per_second": model_count / duration
            }
        
        # Measure performance for different scenarios
        scenarios = [
            ("openai", 15),
            ("anthropic", 8),
            ("combined", 23)
        ]
        
        print("⏱️  Performance measurements:")
        for provider, count in scenarios:
            metrics = await measure_discovery_time(provider, count)
            print(f"  {provider.title()}: {metrics['duration_ms']:.1f}ms for {count} models "
                  f"({metrics['models_per_second']:.1f} models/sec)")
        
        return scenarios
    
    async def demo_batch_operations(self):
        """Demonstrate batch operations and bulk processing."""
        print("\n" + "="*60)
        print("DEMO 5: Batch Operations")
        print("="*60)
        
        # Create sample batch data
        batch_requests = [
            {"provider": "openai", "filters": {"supports_chat": True}},
            {"provider": "anthropic", "filters": {"min_context": 100000}},
            {"provider": "azure_openai", "filters": {"supports_completion": True}}
        ]
        
        print("🔄 Processing batch requests...")
        
        # Process requests concurrently
        async def process_batch_request(request: dict):
            provider = request["provider"]
            filters = request["filters"]
            
            # Simulate processing delay
            await asyncio.sleep(0.05)
            
            # Mock response
            mock_models = [
                ModelInfo(
                    id=f"{provider}-model-{i}",
                    name=f"{provider.title()} Model {i}",
                    provider=provider,
                    context_length=4000 + i * 1000,
                    max_tokens=2000,
                    supports_chat=filters.get("supports_chat", True),
                    supports_completion=filters.get("supports_completion", True),
                    input_cost=0.01 + i * 0.005,
                    output_cost=0.02 + i * 0.01
                )
                for i in range(1, 4)
            ]
            
            return {
                "provider": provider,
                "filters": filters,
                "models": mock_models,
                "count": len(mock_models)
            }
        
        # Execute batch processing
        start_time = time.time()
        results = await asyncio.gather(*[
            process_batch_request(req) for req in batch_requests
        ])
        end_time = time.time()
        
        print(f"✅ Batch processing completed in {(end_time - start_time)*1000:.1f}ms")
        
        for result in results:
            print(f"  {result['provider']}: {result['count']} models "
                  f"(filters: {result['filters']})")
        
        return results
    
    async def demo_custom_provider_integration(self):
        """Demonstrate custom provider integration."""
        print("\n" + "="*60)
        print("DEMO 6: Custom Provider Integration")
        print("="*60)
        
        # Example custom provider configuration
        custom_provider_config = {
            "custom_ai": {
                "api_key": "custom-demo-key",
                "base_url": "https://api.custom-ai.com/v1",
                "enabled": True
            }
        }
        
        # Mock custom provider models
        custom_models = [
            ModelInfo(
                id="custom-large-2024",
                name="Custom AI Large",
                provider="custom_ai",
                context_length=32000,
                max_tokens=8000,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.008,
                output_cost=0.016,
                description="Custom AI's most capable model"
            ),
            ModelInfo(
                id="custom-fast-2024",
                name="Custom AI Fast",
                provider="custom_ai",
                context_length=8000,
                max_tokens=2000,
                supports_chat=True,
                supports_completion=False,
                input_cost=0.002,
                output_cost=0.004,
                description="Custom AI's fastest model"
            )
        ]
        
        print("🔧 Custom provider integration:")
        print(f"  Provider: custom_ai")
        print(f"  Models: {len(custom_models)}")
        
        for model in custom_models:
            print(f"    • {model.name} - {model.context_length:,} tokens")
        
        return custom_models
    
    async def demo_real_time_updates(self):
        """Demonstrate real-time updates and notifications."""
        print("\n" + "="*60)
        print("DEMO 7: Real-time Updates")
        print("="*60)
        
        # Simulate real-time updates
        update_events = [
            {"type": "model_added", "model_id": "gpt-4-turbo", "provider": "openai"},
            {"type": "model_updated", "model_id": "claude-3-sonnet", "provider": "anthropic"},
            {"type": "model_removed", "model_id": "gpt-3.5-turbo-0301", "provider": "openai"}
        ]
        
        print("📡 Processing real-time updates...")
        
        async def process_update(event: dict):
            await asyncio.sleep(0.1)  # Simulate processing
            
            if event["type"] == "model_added":
                print(f"  ➕ Added: {event['model_id']} ({event['provider']})")
            elif event["type"] == "model_updated":
                print(f"  🔄 Updated: {event['model_id']} ({event['provider']})")
            elif event["type"] == "model_removed":
                print(f"  ➖ Removed: {event['model_id']} ({event['provider']})")
        
        # Process updates concurrently
        await asyncio.gather(*[process_update(event) for event in update_events])
        
        return update_events
    
    async def demo_cost_calculator(self, models: List[ModelInfo]):
        """Demonstrate cost calculation and optimization."""
        print("\n" + "="*60)
        print("DEMO 8: Cost Calculator")
        print("="*60)
        
        # Sample usage scenarios
        scenarios = [
            {"name": "Small Chat", "tokens": 1000, "type": "chat"},
            {"name": "Large Document", "tokens": 50000, "type": "completion"},
            {"name": "Code Generation", "tokens": 2000, "type": "completion"}
        ]
        
        print("💰 Cost analysis for different usage scenarios:")
        
        for scenario in scenarios:
            print(f"\n📋 {scenario['name']} ({scenario['tokens']:,} tokens):")
            
            # Calculate costs for each model
            model_costs = []
            for model in models:
                input_cost = (scenario["tokens"] / 1000) * model.input_cost
                output_cost = (scenario["tokens"] / 1000) * model.output_cost
                total_cost = input_cost + output_cost
                
                model_costs.append({
                    "model": model.name,
                    "total_cost": total_cost,
                    "input_cost": input_cost,
                    "output_cost": output_cost
                })
            
            # Sort by cost
            model_costs.sort(key=lambda x: x["total_cost"])
            
            # Show top 3 cheapest options
            for i, cost_info in enumerate(model_costs[:3]):
                print(f"  {i+1}. {cost_info['model']}: ${cost_info['total_cost']:.4f}")
        
        return scenarios
    
    async def demo_error_handling(self):
        """Demonstrate robust error handling and recovery."""
        print("\n" + "="*60)
        print("DEMO 9: Error Handling")
        print("="*60)
        
        # Simulate various error scenarios
        error_scenarios = [
            {"error": "timeout", "provider": "openai"},
            {"error": "auth_failure", "provider": "anthropic"},
            {"error": "rate_limit", "provider": "azure_openai"}
        ]
        
        print("🛡️  Testing error handling scenarios:")
        
        async def handle_error_scenario(scenario: dict):
            try:
                # Simulate error
                if scenario["error"] == "timeout":
                    await asyncio.sleep(2)  # Simulate timeout
                    raise TimeoutError("Request timed out")
                elif scenario["error"] == "auth_failure":
                    raise ValueError("Invalid API key")
                elif scenario["error"] == "rate_limit":
                    raise RuntimeError("Rate limit exceeded")
                    
            except Exception as e:
                # Handle error gracefully
                print(f"  ⚠️  {scenario['provider']}: {type(e).__name__} - {str(e)}")
                return {
                    "provider": scenario["provider"],
                    "error": type(e).__name__,
                    "handled": True,
                    "fallback_models": []  # Return empty list or cached data
                }
        
        # Process error scenarios
        results = await asyncio.gather(*[
            handle_error_scenario(scenario) for scenario in error_scenarios
        ])
        
        return results
    
    async def demo_usage_analytics(self, models: List[ModelInfo]):
        """Demonstrate usage analytics and reporting."""
        print("\n" + "="*60)
        print("DEMO 10: Usage Analytics")
        print("="*60)
        
        # Generate mock usage data
        usage_data = []
        for model in models:
            usage_data.append({
                "model_id": model.id,
                "model_name": model.name,
                "provider": model.provider,
                "usage_count": 100 + hash(model.id) % 1000,  # Mock usage
                "total_tokens": 50000 + hash(model.id) % 500000,
                "total_cost": 0.0
            })
        
        # Calculate total costs
        for usage in usage_data:
            model = next(m for m in models if m.id == usage["model_id"])
            usage["total_cost"] = (usage["total_tokens"] / 1000) * model.input_cost
        
        # Analytics
        total_usage = sum(u["usage_count"] for u in usage_data)
        total_cost = sum(u["total_cost"] for u in usage_data)
        provider_usage = {}
        
        for usage in usage_data:
            provider = usage["provider"]
            if provider not in provider_usage:
                provider_usage[provider] = {"count": 0, "cost": 0}
            provider_usage[provider]["count"] += usage["usage_count"]
            provider_usage[provider]["cost"] += usage["total_cost"]
        
        print("📊 Usage Analytics:")
        print(f"  Total API calls: {total_usage:,}")
        print(f"  Total cost: ${total_cost:.2f}")
        print(f"  Average cost per call: ${total_cost/total_usage:.4f}")
        
        print("\n📈 Provider breakdown:")
        for provider, stats in provider_usage.items():
            print(f"  {provider.title()}: {stats['count']:,} calls, ${stats['cost']:.2f}")
        
        return usage_data
    
    async def run_complete_demo(self):
        """Run the complete demonstration."""
        print("🚀 Starting Model Discovery Demo")
        print("="*80)
        
        try:
            # Run all demos
            models = await self.demo_basic_discovery()
            filtered_models = await self.demo_advanced_filtering(models)
            cache_stats = await self.demo_caching_strategies()
            performance_metrics = await self.demo_performance_monitoring()
            batch_results = await self.demo_batch_operations()
            custom_models = await self.demo_custom_provider_integration()
            updates = await self.demo_real_time_updates()
            cost_analysis = await self.demo_cost_calculator(models)
            error_handling = await self.demo_error_handling()
            analytics = await self.demo_usage_analytics(models)
            
            # Summary
            print("\n" + "="*80)
            print("🎯 DEMO SUMMARY")
            print("="*80)
            print(f"✅ Total models discovered: {len(models)}")
            print(f"✅ Cache hit rate: {cache_stats.get('hit_rate', 0):.1f}%")
            print(f"✅ Custom providers: 1")
            print(f"✅ Error scenarios handled: {len(error_handling)}")
            print(f"✅ Batch operations: {len(batch_results)}")
            print(f"✅ Real-time updates: {len(updates)}")
            print("="*80)
            
            return {
                "total_models": len(models),
                "cache_stats": cache_stats,
                "performance_metrics": performance_metrics,
                "error_handling": error_handling,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise


async def main():
    """Main demo execution."""
    demo = ModelDiscoveryDemo()
    
    try:
        results = await demo.run_complete_demo()
        logger.info("Demo completed successfully!")
        return results
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demo
    results = asyncio.run(main())
    
    # Save results to file
    with open("demo_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n💾 Demo results saved to demo_results.json")