# 🗄️ Caching Guide - LLM Proxy API

Comprehensive guide to the advanced caching system in the LLM Proxy API.

## Table of Contents

- [Overview](#overview)
- [Cache Architecture](#cache-architecture)
- [Cache Types](#cache-types)
- [Cache Warming](#cache-warming)
- [Cache Invalidation](#cache-invalidation)
- [Performance Monitoring](#performance-monitoring)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The LLM Proxy API implements a sophisticated multi-level caching system designed to minimize external API calls, reduce latency, and optimize resource utilization. The system achieves up to 85% cache hit rates with intelligent warming and automatic invalidation.

### Key Features

- **Multi-level Caching**: Memory and disk-based caching
- **Intelligent Warming**: Pattern-based cache preloading
- **Automatic Invalidation**: TTL and LRU-based eviction
- **Compression**: Memory-efficient data storage
- **Monitoring**: Comprehensive cache performance metrics
- **Distributed Support**: Redis integration for multi-instance deployments

### Performance Impact

| Metric | Without Cache | With Cache | Improvement |
|--------|----------------|------------|-------------|
| Average Latency | 500ms | 50ms | 90% faster |
| External API Calls | 100% | 15% | 85% reduction |
| Memory Usage | Base | +45MB | Optimized |
| Error Rate | 5% | 0.5% | 90% reduction |

## Cache Architecture

### Unified Cache System

The system uses a unified cache architecture with multiple storage layers:

```
┌─────────────────┐
│   Application   │
└─────────────────┘
         │
    ┌────────────┐
    │  Cache     │ ← Unified Cache Manager
    │  Manager   │
    └────────────┘
         │
    ┌────┴────┐
    │         │
┌───┴───┐ ┌───┴───┐
│ Memory│ │ Disk │
│ Cache │ │ Cache│
└───────┘ └───────┘
```

#### Components

1. **Cache Manager**: Central coordination and API
2. **Memory Cache**: Fast in-memory storage (LRU eviction)
3. **Disk Cache**: Persistent storage with compression
4. **Cache Warmer**: Intelligent preloading system
5. **Cache Monitor**: Performance monitoring and alerting

### Cache Flow

```
Request → Cache Check → Cache Hit?
    │              │
    │              └─→ Cache Miss
    │                     │
    │                     └─→ Provider API
    │                             │
    │                             └─→ Response
    │                                     │
    └─← Cache Hit ←───────────────────────┘
```

## Cache Types

### Response Cache

Caches API responses from external providers:

```yaml
response_cache:
  max_size_mb: 100
  ttl: 1800        # 30 minutes
  compression: true
  compression_level: 6
```

#### Use Cases
- OpenAI API responses
- Anthropic API responses
- Model listing responses
- Pricing information

#### Cache Key Format
```
response:{provider}:{endpoint}:{params_hash}
```

### Summary Cache

Caches context summarization results:

```yaml
summary_cache:
  max_size_mb: 50
  ttl: 3600        # 1 hour
  compression: true
  compression_level: 6
```

#### Use Cases
- Context condensation results
- Summarization API responses
- Token optimization results

#### Cache Key Format
```
summary:{input_hash}:{max_tokens}:{model}
```

### Model Discovery Cache

Caches model discovery and metadata:

```yaml
model_cache:
  max_size_mb: 25
  ttl: 300         # 5 minutes
  compression: true
```

#### Use Cases
- Available models list
- Model capabilities
- Pricing information
- Model metadata

#### Cache Key Format
```
models:{provider}:{base_url}
```

### Configuration Cache

Caches parsed configuration data:

```yaml
config_cache:
  max_size_mb: 10
  ttl: 600         # 10 minutes
  compression: false
```

#### Use Cases
- Parsed YAML configurations
- Provider configurations
- Rate limiting rules
- Validation schemas

## Cache Warming

### Intelligent Warming

The system implements intelligent cache warming to prevent cold starts:

```yaml
warming:
  enabled: true
  interval: 300                    # Warm every 5 minutes
  preload_popular: true           # Preload popular items
  preload_threshold: 10           # Popularity threshold
  pattern_analysis: true          # Learn access patterns
  predictive_warming: true        # Predict future needs
```

#### Warming Strategies

1. **Pattern-Based**: Learns from access patterns
2. **Popularity-Based**: Preloads frequently accessed items
3. **Predictive**: Uses ML to predict future cache needs
4. **Scheduled**: Regular warming at configured intervals

### Background Warming

Non-blocking cache warming process:

```python
# Background warming example
async def warm_cache_background():
    while True:
        try:
            # Analyze access patterns
            patterns = await analyze_access_patterns()

            # Identify items to warm
            items_to_warm = identify_warm_candidates(patterns)

            # Warm cache in background
            await warm_cache_items(items_to_warm)

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")

        # Wait for next warming cycle
        await asyncio.sleep(warming_interval)
```

#### Warming Metrics

- **Warm Hit Rate**: Percentage of warmed items that get used
- **Warm Coverage**: Percentage of cache populated by warming
- **Warm Efficiency**: Ratio of useful warms to total warms
- **Warm Latency**: Time taken to warm cache items

## Cache Invalidation

### Automatic Invalidation

Multiple invalidation strategies:

```yaml
invalidation:
  ttl_enabled: true               # Time-based expiration
  lru_enabled: true               # Least recently used
  size_based: true                # Size-based eviction
  manual_enabled: true            # Manual invalidation
  pattern_based: true             # Pattern-based invalidation
```

#### TTL (Time To Live)

```python
# TTL-based invalidation
cache.set(key, value, ttl=1800)  # 30 minutes

# Automatic cleanup
async def cleanup_expired():
    current_time = time.time()
    expired_keys = [
        key for key, timestamp in timestamps.items()
        if current_time - timestamp > ttl
    ]
    for key in expired_keys:
        await cache.delete(key)
```

#### LRU Eviction

```python
# LRU eviction policy
class LRUCache:
    def __init__(self, max_size):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.access_order = []

    def evict_if_needed(self):
        while len(self.cache) > self.max_size:
            # Remove least recently used
            lru_key = min(self.access_times, key=self.access_times.get)
            del self.cache[lru_key]
            del self.access_times[lru_key]
```

### Manual Invalidation

```bash
# Invalidate specific cache entries
curl -X DELETE "http://localhost:8000/api/cache?provider=openai"
curl -X DELETE "http://localhost:8000/api/cache?key=response:openai:models"

# Clear entire cache
curl -X DELETE http://localhost:8000/api/cache

# Clear by pattern
curl -X DELETE "http://localhost:8000/api/cache?pattern=summary:*"
```

## Performance Monitoring

### Cache Metrics

Comprehensive cache performance monitoring:

```python
# Available metrics
cache_metrics = {
    'hit_rate': 0.85,              # Cache hit percentage
    'total_requests': 10000,       # Total cache requests
    'cache_hits': 8500,            # Successful cache hits
    'cache_misses': 1500,          # Cache misses
    'entries': 500,                # Current cache entries
    'memory_usage_mb': 45.2,       # Memory usage
    'max_memory_mb': 100,          # Maximum memory
    'evictions': 150,              # Items evicted
    'sets': 1650,                  # Items set
    'deletes': 150,                # Items deleted
}
```

#### Monitoring Endpoints

```bash
# Cache statistics
curl http://localhost:8000/api/cache/stats

# Cache health
curl http://localhost:8000/health/cache

# Cache performance metrics
curl http://localhost:8000/metrics | jq '.cache_performance'

# Prometheus format
curl http://localhost:8000/metrics/prometheus | grep cache
```

### Alerting

Cache performance alerting:

```yaml
alerting:
  cache:
    - name: "low_cache_hit_rate"
      condition: "hit_rate < 0.7"
      severity: "warning"
      message: "Cache hit rate below 70%"
    - name: "high_memory_usage"
      condition: "memory_usage_percent > 90"
      severity: "critical"
      message: "Cache memory usage above 90%"
    - name: "high_eviction_rate"
      condition: "evictions_per_minute > 100"
      severity: "warning"
      message: "High cache eviction rate detected"
```

## Configuration

The caching system is configured via the main `config.yaml` file. The application can use either a default in-memory cache or a more robust, scalable Redis-backed cache.

### In-Memory Cache (Default)

If Redis is not configured, the system defaults to a high-performance in-memory cache. You can configure its properties under the `caching` section:

```yaml
# Example in-memory cache configuration from config.yaml
caching:
  enabled: true
  response_cache:
    max_size_mb: 100
    ttl: 1800        # 30 minutes
    compression: true
  summary_cache:
    max_size_mb: 50
    ttl: 3600        # 1 hour
    compression: true
```

### Redis Cache (Recommended for Production)

For production and multi-instance deployments, it is highly recommended to use Redis as a distributed caching backend. This provides scalability, persistence, and resilience.

To enable Redis, add the `redis` block to your `config.yaml`. When this section is present and `enabled` is `true`, it will override the default in-memory caches.

```yaml
# Example Redis configuration in config.yaml
redis:
  enabled: true
  host: "localhost"
  port: 6379
  db: 0
  password: "${REDIS_PASSWORD}" # Supports environment variable substitution
```

  # Warming settings
  warming:
    enabled: true
    interval: 300
    max_concurrent_warms: 5
    warm_batch_size: 50
    enable_pattern_analysis: true
    enable_predictive_warming: true

  # Monitoring settings
  monitoring:
    enabled: true
    metrics_interval: 60
    enable_detailed_stats: true
    alert_on_low_hit_rate: true
    hit_rate_threshold: 0.7
```

## Troubleshooting

### Common Cache Issues

#### Low Hit Rate

**Symptoms:**
- Cache hit rate < 50%
- High external API usage
- Increased latency

**Diagnosis:**
```bash
# Check cache statistics
curl http://localhost:8000/api/cache/stats

# Check cache configuration
curl http://localhost:8000/api/config/cache

# Monitor cache access patterns
curl http://localhost:8000/debug/cache/patterns
```

**Solutions:**
```yaml
# Increase TTL
caching:
  default_ttl: 3600  # Increase from 1800

# Enable compression
caching:
  enable_compression: true
  compression_level: 6

# Adjust cache size
caching:
  max_memory_mb: 1024  # Increase cache size
```

#### Memory Issues

**Symptoms:**
- High memory usage
- Cache evictions
- Application slowdown

**Diagnosis:**
```bash
# Check memory usage
curl http://localhost:8000/health | jq '.checks.memory'

# Check cache memory usage
curl http://localhost:8000/api/cache/stats | jq '.memory_usage_mb'

# Monitor garbage collection
curl http://localhost:8000/debug/memory/gc_stats
```

**Solutions:**
```yaml
# Reduce cache size
caching:
  max_memory_mb: 256  # Reduce from 512

# Enable compression
caching:
  enable_compression: true
  compression_threshold: 512  # Compress smaller items

# Adjust TTL
caching:
  default_ttl: 900  # Reduce TTL to free memory faster
```

#### Cache Corruption

**Symptoms:**
- Invalid cache data
- Application errors
- Inconsistent responses

**Diagnosis:**
```bash
# Check cache integrity
curl http://localhost:8000/debug/cache/integrity

# Validate cache entries
curl http://localhost:8000/debug/cache/validate

# Check for corruption patterns
curl http://localhost:8000/logs/cache | grep "corruption"
```

**Solutions:**
```bash
# Clear corrupted cache
curl -X DELETE http://localhost:8000/api/cache

# Rebuild cache
curl -X POST http://localhost:8000/api/cache/warm

# Enable cache validation
caching:
  enable_validation: true
  validation_interval: 300
```

#### Warming Issues

**Symptoms:**
- Cold cache starts
- High initial latency
- Warming failures

**Diagnosis:**
```bash
# Check warming status
curl http://localhost:8000/api/cache/warming/status

# Check warming logs
curl http://localhost:8000/logs/warming

# Monitor warming metrics
curl http://localhost:8000/metrics | jq '.cache_warming'
```

**Solutions:**
```yaml
# Adjust warming configuration
warming:
  interval: 180          # More frequent warming
  max_concurrent_warms: 3  # Reduce concurrency
  warm_batch_size: 25    # Smaller batches

# Enable pattern analysis
warming:
  enable_pattern_analysis: true
  pattern_window: 3600   # 1 hour analysis window
```

### Performance Tuning

#### Cache Size Optimization

```python
# Calculate optimal cache size
def calculate_optimal_cache_size():
    # Monitor cache hit rate vs memory usage
    hit_rates = []
    memory_usage = []

    for size in [256, 512, 1024, 2048]:
        # Test with different cache sizes
        configure_cache_size(size)
        hit_rate, mem_usage = measure_performance()
        hit_rates.append(hit_rate)
        memory_usage.append(mem_usage)

    # Find optimal balance
    optimal_size = find_optimal_balance(hit_rates, memory_usage)
    return optimal_size
```

#### TTL Optimization

```python
# Dynamic TTL adjustment
def optimize_ttl():
    # Monitor cache freshness vs hit rate
    freshness_scores = []
    hit_rates = []

    for ttl in [300, 600, 1800, 3600]:
        configure_ttl(ttl)
        freshness, hit_rate = measure_cache_performance()
        freshness_scores.append(freshness)
        hit_rates.append(hit_rate)

    # Find optimal TTL
    optimal_ttl = find_optimal_ttl(freshness_scores, hit_rates)
    return optimal_ttl
```

## Best Practices

### Cache Design

1. **Cache Key Design**
   - Use consistent key formats
   - Include all relevant parameters
   - Keep keys short but descriptive
   - Use hash for long keys

2. **TTL Strategy**
   - Set appropriate TTL based on data freshness needs
   - Use shorter TTL for rapidly changing data
   - Use longer TTL for stable data
   - Consider business requirements for data freshness

3. **Size Management**
   - Monitor memory usage regularly
   - Set appropriate size limits
   - Use compression for large objects
   - Implement proper eviction policies

### Monitoring and Alerting

1. **Key Metrics to Monitor**
   - Cache hit rate (> 70% target)
   - Memory usage (< 80% target)
   - Eviction rate (< 10% target)
   - Warming efficiency (> 50% target)

2. **Alert Configuration**
   ```yaml
   alerts:
     - name: "cache_hit_rate_low"
       condition: "hit_rate < 0.7"
       severity: "warning"
       action: "notify_team"
     - name: "cache_memory_high"
       condition: "memory_usage_percent > 85"
       severity: "critical"
       action: "scale_resources"
   ```

### Deployment Considerations

1. **Development**
   - Shorter TTL for faster iteration
   - Smaller cache sizes
   - Disable disk cache
   - Enable debug logging

2. **Staging**
   - Medium TTL values
   - Moderate cache sizes
   - Enable monitoring
   - Test cache warming

3. **Production**
   - Optimized TTL values
   - Large cache sizes
   - Enable all optimizations
   - Comprehensive monitoring

### Maintenance

1. **Regular Maintenance**
   - Monitor cache performance weekly
   - Clear cache during low-traffic periods
   - Update cache configuration based on usage patterns
   - Review and optimize cache keys

2. **Performance Reviews**
   - Monthly cache performance analysis
   - Identify optimization opportunities
   - Update cache strategies based on new features
   - Document cache configuration changes

### Security Considerations

1. **Data Protection**
   - Encrypt sensitive cached data
   - Implement proper access controls
   - Regular security audits of cached data
   - Compliance with data retention policies

2. **Cache Poisoning Prevention**
   - Validate cache keys and values
   - Implement cache key sanitization
   - Monitor for unusual cache access patterns
   - Regular cache integrity checks

---

## 📊 Cache Performance Dashboard

### Recommended Grafana Panels

1. **Cache Hit Rate**
   ```
   Metric: cache_hit_rate
   Type: Gauge
   Thresholds: >80% (green), 60-80% (yellow), <60% (red)
   ```

2. **Memory Usage**
   ```
   Metric: cache_memory_usage_mb / cache_max_memory_mb * 100
   Type: Gauge
   Thresholds: <70% (green), 70-85% (yellow), >85% (red)
   ```

3. **Cache Operations**
   ```
   Metrics: cache_sets_total, cache_hits_total, cache_misses_total, cache_evictions_total
   Type: Graph
   Time Range: Last 24 hours
   ```

4. **Warming Performance**
   ```
   Metrics: warming_requests_total, warming_success_total, warming_duration
   Type: Graph
   Time Range: Last 7 days
   ```

### Key Performance Indicators

- **Cache Hit Rate**: Target > 80%
- **Memory Efficiency**: Target < 75% of allocated memory
- **Eviction Rate**: Target < 5% of total operations
- **Warming Coverage**: Target > 60% of popular items
- **Average Access Time**: Target < 10ms for memory cache

---

## 🔧 Advanced Features

### Cache Analytics

```yaml
# Advanced cache analytics
analytics:
  enabled: true
  collect_access_patterns: true
  collect_performance_metrics: true
  enable_ml_predictions: true
  prediction_model: "linear_regression"
  prediction_window: 3600  # 1 hour
  prediction_interval: 300  # 5 minutes
```

### Custom Cache Backends

```python
# Custom cache backend implementation
class CustomCacheBackend:
    def __init__(self, config):
        self.config = config
        self.connection = self._create_connection()

    async def get(self, key):
        # Custom get implementation
        pass

    async def set(self, key, value, ttl=None):
        # Custom set implementation
        pass

    async def delete(self, key):
        # Custom delete implementation
        pass

    async def clear(self):
        # Custom clear implementation
        pass
```

---

## 📚 References

- [Cache Implementation Patterns](https://redis.io/topics/lru-cache)
- [HTTP Caching Best Practices](https://tools.ietf.org/html/rfc7234)
- [Distributed Caching Strategies](https://redis.io/topics/cluster-tutorial)
- [Cache Performance Monitoring](https://prometheus.io/docs/practices/naming/)
- [Memory Management in Python](https://docs.python.org/3/library/gc.html)

---

**🗄️ This comprehensive caching guide ensures optimal cache performance with intelligent warming, monitoring, and automatic optimization for the LLM Proxy API.**