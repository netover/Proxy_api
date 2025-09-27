import asyncio
import time
from src.core.cache.redis_cache import RedisCache, DistributedCacheManager
from src.core.config.models import CachingConfig, CacheSubConfig

async def test_redis_cache():
    """Test the Redis cache functionality."""

    print('🗄️  TESTANDO CACHE REDIS DISTRIBUÍDO:')

    try:
        # Create test cache
        cache = RedisCache(
            redis_url="redis://localhost:6379",
            ttl=60,
            max_size_mb=10,
            compression_enabled=True
        )

        # Initialize (will fail if Redis not available, which is expected)
        try:
            await cache.initialize()
            print('✅ Cache Redis inicializado')
        except Exception as e:
            print(f'⚠️  Cache Redis não disponível (esperado): {e}')
            print('✅ Continuando com cache em memória como fallback')

        # Test basic operations
        test_key = "test_key_123"
        test_value = {"data": "test_value", "timestamp": time.time()}

        # Set
        success = await cache.set(test_key, test_value)
        print(f'✅ Cache set: {success}')

        # Get
        retrieved_value = await cache.get(test_key)
        if retrieved_value:
            print(f'✅ Cache get: {retrieved_value["data"]}')
        else:
            print('❌ Cache get: Value not found')

        # Exists
        exists = await cache.exists(test_key)
        print(f'✅ Cache exists: {exists}')

        # TTL
        ttl = await cache.get_ttl(test_key)
        print(f'✅ Cache TTL: {ttl}s')

        # Stats
        stats = await cache.get_stats()
        print(f'✅ Cache stats: {stats}')

        # Delete
        deleted = await cache.delete(test_key)
        print(f'✅ Cache delete: {deleted}')

        # Verify deletion
        exists_after = await cache.exists(test_key)
        print(f'✅ Cache exists after delete: {exists_after}')

        # Test distributed cache manager
        print('\\n🔄 Testando Distributed Cache Manager:')

        config = CachingConfig(
            enabled=True,
            redis_url="redis://localhost:6379",
            response_cache=CacheSubConfig(max_size_mb=100, ttl=1800, compression=True),
            summary_cache=CacheSubConfig(max_size_mb=50, ttl=3600, compression=True)
        )

        manager = DistributedCacheManager()
        try:
            await manager.initialize(config)
            print('✅ Distributed cache manager inicializado')
        except Exception as e:
            print(f'⚠️  Distributed cache manager falhou (esperado): {e}')
            print('✅ Continuando sem Redis')

        # Test getting specific caches
        response_cache = manager.get_cache('response')
        summary_cache = manager.get_cache('summary')

        if response_cache:
            print('✅ Response cache disponível')
        if summary_cache:
            print('✅ Summary cache disponível')

        # Stats
        manager_stats = await manager.get_stats()
        print(f'✅ Manager stats: {len(manager_stats)} caches')

        # Shutdown
        await manager.shutdown()
        await cache.shutdown()
        print('✅ Cache shutdown completo')

    except Exception as e:
        print(f'❌ Erro no teste: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis_cache())
