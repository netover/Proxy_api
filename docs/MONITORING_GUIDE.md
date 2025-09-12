# 📊 Monitoring & Metrics Guide - LLM Proxy API

Comprehensive guide to monitoring, metrics collection, and observability in the LLM Proxy API.

## Table of Contents

- [Overview](#overview)
- [Metrics Architecture](#metrics-architecture)
- [Core Metrics](#core-metrics)
- [Monitoring Endpoints](#monitoring-endpoints)
- [Alerting System](#alerting-system)
- [Grafana Dashboards](#grafana-dashboards)
- [Performance Monitoring](#performance-monitoring)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The LLM Proxy API implements comprehensive monitoring and metrics collection to ensure high availability, performance optimization, and proactive issue detection. The system provides real-time insights into application health, performance, and usage patterns.

### Key Features

- **Real-time Metrics**: Comprehensive metrics collection with sub-millisecond latency
- **Multi-format Export**: Prometheus, JSON, and custom formats
- **Intelligent Alerting**: Configurable alerts with severity levels
- **Health Monitoring**: Automated health checks with detailed diagnostics
- **Performance Profiling**: Built-in performance monitoring and profiling
- **Distributed Tracing**: End-to-end request tracing capabilities

### Monitoring Coverage

- **Application Metrics**: Request rates, response times, error rates
- **System Metrics**: CPU, memory, disk, network usage
- **Provider Metrics**: Per-provider performance and health
- **Cache Metrics**: Hit rates, memory usage, eviction statistics
- **Connection Pool Metrics**: Connection utilization and health
- **Business Metrics**: Token usage, cost tracking, user patterns

## Metrics Architecture

### Metrics Collection System

```
┌─────────────────┐
│   Application   │
└─────────────────┘
         │
    ┌────────────┐
    │  Metrics   │ ← MetricsCollector
    │ Collector  │
    └────────────┘
         │
    ┌────┴────┐
    │         │
┌───┴───┐ ┌───┴───┐
│Prometheus│ │ JSON  │
│ Exporter │ │ Export│
└─────────┘ └───────┘
         │
    ┌────┴────┐
    │Monitoring│
    │ Systems │
    └─────────┘
```

#### Core Components

1. **MetricsCollector**: Central metrics collection and storage
2. **Provider Metrics**: Per-provider performance tracking
3. **System Metrics**: OS and runtime metrics
4. **Cache Metrics**: Caching performance and health
5. **Connection Metrics**: HTTP connection pool monitoring
6. **Business Metrics**: Application-specific metrics

### Metrics Storage

```python
class MetricsCollector:
    def __init__(self):
        self.providers = {}           # Provider-specific metrics
        self.system_health = {}       # System health metrics
        self.cache_metrics = {}       # Cache performance metrics
        self.connection_pool = {}     # Connection pool metrics
        self.business_metrics = {}    # Business logic metrics
        self.start_time = datetime.now()

    def record_request(self, provider_name: str, success: bool,
                      response_time: float, tokens: int = 0):
        """Record request metrics with automatic categorization"""
        pass

    def update_system_health(self):
        """Update system health metrics using psutil"""
        pass

    def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive metrics snapshot"""
        pass
```

## Core Metrics

### Application Metrics

#### Request Metrics

```python
# Request tracking
request_metrics = {
    'total_requests': 10000,
    'successful_requests': 9800,
    'failed_requests': 200,
    'success_rate': 0.98,
    'avg_response_time_ms': 245.8,
    'p50_response_time_ms': 180.0,
    'p95_response_time_ms': 450.0,
    'p99_response_time_ms': 890.0,
    'requests_per_second': 25.4
}
```

#### Error Metrics

```python
# Error categorization
error_metrics = {
    'total_errors': 200,
    'connection_errors': 45,
    'timeout_errors': 32,
    'rate_limit_errors': 28,
    'authentication_errors': 15,
    'server_errors': 65,
    'client_errors': 15,
    'error_rate_percent': 2.0
}
```

### Provider Metrics

#### Per-Provider Performance

```python
# Provider-specific metrics
provider_metrics = {
    'openai': {
        'total_requests': 5000,
        'successful_requests': 4850,
        'failed_requests': 150,
        'success_rate': 0.97,
        'avg_response_time_ms': 280.5,
        'total_tokens': 250000,
        'cost_usd': 125.50,
        'rate_limit_remaining': 45,
        'models_used': ['gpt-4', 'gpt-3.5-turbo']
    },
    'anthropic': {
        'total_requests': 3000,
        'successful_requests': 2940,
        'failed_requests': 60,
        'success_rate': 0.98,
        'avg_response_time_ms': 210.3,
        'total_tokens': 180000,
        'cost_usd': 90.25,
        'rate_limit_remaining': 35,
        'models_used': ['claude-3-opus', 'claude-3-haiku']
    }
}
```

#### Model-Specific Metrics

```python
# Model performance tracking
model_metrics = {
    'gpt-4': {
        'total_requests': 1200,
        'successful_requests': 1185,
        'avg_response_time_ms': 320.5,
        'total_tokens': 150000,
        'avg_tokens_per_request': 125.0,
        'cost_per_request_usd': 0.045,
        'error_rate': 0.0125
    },
    'claude-3-opus': {
        'total_requests': 800,
        'successful_requests': 792,
        'avg_response_time_ms': 280.3,
        'total_tokens': 120000,
        'avg_tokens_per_request': 150.0,
        'cost_per_request_usd': 0.0375,
        'error_rate': 0.01
    }
}
```

### System Metrics

#### Resource Usage

```python
# System resource metrics
system_metrics = {
    'cpu': {
        'percent': 45.2,
        'cores': 8,
        'frequency_mhz': 3200,
        'load_average': [1.2, 1.5, 1.8]
    },
    'memory': {
        'total_mb': 8192,
        'used_mb': 5523,
        'available_mb': 2669,
        'percent': 67.4,
        'swap_used_mb': 1024,
        'swap_total_mb': 4096
    },
    'disk': {
        'total_gb': 256,
        'used_gb': 89.5,
        'available_gb': 166.5,
        'percent': 34.9,
        'read_bytes_per_sec': 1024000,
        'write_bytes_per_sec': 2048000
    },
    'network': {
        'bytes_sent_mb': 45.2,
        'bytes_received_mb': 89.7,
        'packets_sent': 125000,
        'packets_received': 98000,
        'connections': 245,
        'errors': 12
    }
}
```

### Cache Metrics

#### Cache Performance

```python
# Cache performance metrics
cache_metrics = {
    'hit_rate': 0.85,
    'total_requests': 10000,
    'cache_hits': 8500,
    'cache_misses': 1500,
    'entries': 500,
    'memory_usage_mb': 45.2,
    'max_memory_mb': 100,
    'memory_utilization_percent': 45.2,
    'evictions': 150,
    'eviction_rate': 0.015,
    'avg_item_size_bytes': 94250,
    'oldest_entry_age_seconds': 1800,
    'newest_entry_age_seconds': 45
}
```

#### Cache Warming Metrics

```python
# Cache warming performance
warming_metrics = {
    'warming_enabled': True,
    'total_warming_requests': 100,
    'successful_warmings': 95,
    'failed_warmings': 5,
    'warming_success_rate': 0.95,
    'avg_warming_time_ms': 1250.5,
    'total_items_warmed': 2500,
    'warming_coverage_percent': 78.5,
    'last_warming_time': '2024-01-15T10:30:00Z',
    'next_warming_time': '2024-01-15T10:35:00Z'
}
```

### Connection Pool Metrics

#### HTTP Connection Metrics

```python
# Connection pool metrics
connection_metrics = {
    'max_connections': 200,
    'max_keepalive_connections': 50,
    'active_connections': 45,
    'idle_connections': 25,
    'pending_requests': 3,
    'total_connections_created': 150,
    'total_connections_closed': 105,
    'connection_errors': 5,
    'connection_timeouts': 2,
    'avg_connection_time_ms': 15.5,
    'pool_utilization_percent': 71.4,
    'connection_reuse_rate': 0.93
}
```

## Monitoring Endpoints

### Core Monitoring Endpoints

```bash
# Health check endpoints
GET /health                    # Comprehensive health check
GET /health/detailed          # Detailed health with metrics
GET /health/providers         # Provider-specific health
GET /health/system           # System resource health
GET /health/cache            # Cache health status
GET /health/connections      # Connection pool health

# Metrics endpoints
GET /metrics                  # All metrics in JSON format
GET /metrics/prometheus      # Prometheus format metrics
GET /metrics/providers       # Provider-specific metrics
GET /metrics/system          # System metrics only
GET /metrics/cache           # Cache metrics only
GET /metrics/performance     # Performance metrics only

# Debug endpoints
GET /debug/metrics           # Raw metrics data
GET /debug/profile           # Performance profiling data
GET /debug/memory           # Memory usage details
GET /debug/connections      # Connection pool details
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "checks": {
    "providers": {
      "status": "healthy",
      "total": 3,
      "healthy": 2,
      "degraded": 1,
      "unhealthy": 0,
      "details": {
        "openai": {
          "status": "healthy",
          "response_time_ms": 245,
          "error_rate": 0.015
        },
        "anthropic": {
          "status": "degraded",
          "response_time_ms": 850,
          "error_rate": 0.045
        }
      }
    },
    "memory": {
      "status": "healthy",
      "usage_percent": 67.4,
      "available_mb": 2669
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 0.85,
      "memory_usage_mb": 45.2
    },
    "connections": {
      "status": "healthy",
      "active": 45,
      "pending": 3
    }
  },
  "overall_status": "healthy"
}
```

### Metrics Response

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "collection_duration_ms": 45.2,
  "metrics": {
    "application": {
      "total_requests": 10000,
      "successful_requests": 9800,
      "failed_requests": 200,
      "success_rate": 0.98,
      "avg_response_time_ms": 245.8,
      "requests_per_second": 25.4
    },
    "providers": {
      "openai": {
        "requests": 5000,
        "success_rate": 0.97,
        "avg_response_time_ms": 280.5,
        "total_tokens": 250000,
        "cost_usd": 125.50
      },
      "anthropic": {
        "requests": 3000,
        "success_rate": 0.98,
        "avg_response_time_ms": 210.3,
        "total_tokens": 180000,
        "cost_usd": 90.25
      }
    },
    "system": {
      "cpu_percent": 45.2,
      "memory_percent": 67.4,
      "disk_percent": 34.9
    },
    "cache": {
      "hit_rate": 0.85,
      "entries": 500,
      "memory_usage_mb": 45.2
    },
    "connections": {
      "active": 45,
      "pending": 3,
      "error_rate": 0.002
    }
  }
}
```

## Alerting System

### Alert Configuration

```yaml
alerting:
  enabled: true
  alertmanager_url: "http://alertmanager:9093"
  slack_webhook: "${SLACK_WEBHOOK_URL}"

  rules:
    # Performance alerts
    - name: "high_response_time"
      condition: "avg_response_time_ms > 1000"
      severity: "warning"
      description: "Average response time above 1 second"
      channels: ["slack", "email"]
      cooldown_minutes: 5

    - name: "high_error_rate"
      condition: "error_rate > 0.05"
      severity: "critical"
      description: "Error rate above 5%"
      channels: ["slack", "pagerduty"]
      cooldown_minutes: 2

    # System alerts
    - name: "high_memory_usage"
      condition: "memory_percent > 85"
      severity: "warning"
      description: "Memory usage above 85%"
      channels: ["slack"]
      cooldown_minutes: 10

    - name: "high_cpu_usage"
      condition: "cpu_percent > 90"
      severity: "critical"
      description: "CPU usage above 90%"
      channels: ["slack", "pagerduty"]
      cooldown_minutes: 1

    # Provider alerts
    - name: "provider_down"
      condition: "provider_status == 'unhealthy'"
      severity: "critical"
      description: "Provider is unhealthy"
      channels: ["slack", "pagerduty"]
      cooldown_minutes: 1

    - name: "rate_limit_approaching"
      condition: "rate_limit_remaining < 10"
      severity: "warning"
      description: "Rate limit remaining below 10%"
      channels: ["slack"]
      cooldown_minutes: 15

    # Cache alerts
    - name: "low_cache_hit_rate"
      condition: "cache_hit_rate < 0.7"
      severity: "warning"
      description: "Cache hit rate below 70%"
      channels: ["slack"]
      cooldown_minutes: 10

    - name: "cache_memory_high"
      condition: "cache_memory_utilization_percent > 90"
      severity: "warning"
      description: "Cache memory usage above 90%"
      channels: ["slack"]
      cooldown_minutes: 15
```

### Alert Manager Integration

```yaml
# AlertManager configuration
alertmanager:
  enabled: true
  url: "http://alertmanager:9093/api/v2/alerts"
  timeout: 10
  retries: 3

  # Alert grouping
  group_by: ["alertname", "severity", "provider"]
  group_wait: "30s"
  group_interval: "5m"
  repeat_interval: "4h"

  # Routing
  routes:
    - match:
        severity: "critical"
      receiver: "pagerduty"
    - match:
        severity: "warning"
      receiver: "slack"
```

## Grafana Dashboards

### Main Dashboard

#### Key Panels

1. **Request Rate & Success Rate**
   ```
   Metrics: requests_per_second, success_rate
   Type: Graph
   Time Range: Last 1 hour
   ```

2. **Response Time Percentiles**
   ```
   Metrics: p50_response_time, p95_response_time, p99_response_time
   Type: Graph
   Thresholds: p95 < 500ms (green), 500ms-1000ms (yellow), >1000ms (red)
   ```

3. **Error Rate by Type**
   ```
   Metrics: connection_errors, timeout_errors, rate_limit_errors, server_errors
   Type: Pie Chart
   ```

4. **Provider Performance**
   ```
   Metrics: provider_requests, provider_success_rate, provider_avg_response_time
   Type: Table
   ```

### System Dashboard

#### Resource Monitoring

1. **CPU Usage**
   ```
   Metrics: cpu_percent, cpu_load_average
   Type: Graph
   Thresholds: <70% (green), 70-85% (yellow), >85% (red)
   ```

2. **Memory Usage**
   ```
   Metrics: memory_percent, memory_used_mb, swap_percent
   Type: Graph
   Thresholds: <80% (green), 80-90% (yellow), >90% (red)
   ```

3. **Disk Usage**
   ```
   Metrics: disk_percent, disk_read_bytes, disk_write_bytes
   Type: Graph
   ```

4. **Network I/O**
   ```
   Metrics: network_bytes_sent, network_bytes_received
   Type: Graph
   ```

### Cache Dashboard

#### Cache Performance

1. **Cache Hit Rate**
   ```
   Metrics: cache_hit_rate
   Type: Gauge
   Thresholds: >80% (green), 60-80% (yellow), <60% (red)
   ```

2. **Cache Operations**
   ```
   Metrics: cache_hits, cache_misses, cache_evictions
   Type: Graph
   ```

3. **Cache Memory Usage**
   ```
   Metrics: cache_memory_usage_mb, cache_memory_utilization_percent
   Type: Graph
   ```

4. **Cache Warming**
   ```
   Metrics: warming_requests, warming_success_rate, warming_duration
   Type: Graph
   ```

## Performance Monitoring

### Application Performance Monitoring

```python
# Performance profiling
@profile_function
async def handle_request(request):
    start_time = time.time()

    # Request processing
    result = await process_request(request)

    processing_time = time.time() - start_time

    # Record performance metrics
    metrics_collector.record_performance(
        endpoint=request.url.path,
        method=request.method,
        processing_time=processing_time,
        success=result.success
    )

    return result
```

### Database Performance Monitoring

```python
# Database query monitoring
async def execute_query(query, params=None):
    start_time = time.time()

    try:
        result = await database.execute(query, params)
        execution_time = time.time() - start_time

        # Record database metrics
        metrics_collector.record_database_query(
            query_type=query.split()[0],
            execution_time=execution_time,
            success=True
        )

        return result

    except Exception as e:
        execution_time = time.time() - start_time

        metrics_collector.record_database_query(
            query_type=query.split()[0],
            execution_time=execution_time,
            success=False,
            error=str(e)
        )

        raise
```

### External API Monitoring

```python
# External API call monitoring
async def call_external_api(provider, endpoint, **kwargs):
    start_time = time.time()

    try:
        response = await http_client.request(provider, endpoint, **kwargs)
        call_time = time.time() - start_time

        # Record external API metrics
        metrics_collector.record_external_api_call(
            provider=provider,
            endpoint=endpoint,
            call_time=call_time,
            status_code=response.status_code,
            success=response.status_code < 400
        )

        return response

    except Exception as e:
        call_time = time.time() - start_time

        metrics_collector.record_external_api_call(
            provider=provider,
            endpoint=endpoint,
            call_time=call_time,
            success=False,
            error=str(e)
        )

        raise
```

## Health Checks

### Comprehensive Health Checks

```python
class HealthChecker:
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'cache': self.check_cache,
            'providers': self.check_providers,
            'memory': self.check_memory,
            'disk': self.check_disk,
            'network': self.check_network
        }

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks concurrently"""
        tasks = []
        for name, check_func in self.checks.items():
            tasks.append(self.run_check(name, check_func))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        for (name, _), result in zip(self.checks.items(), results):
            if isinstance(result, Exception):
                health_status['checks'][name] = {
                    'status': 'unhealthy',
                    'error': str(result)
                }
                health_status['status'] = 'unhealthy'
            else:
                health_status['checks'][name] = result

        return health_status

    async def run_check(self, name: str, check_func) -> Dict[str, Any]:
        """Run individual health check with timeout"""
        try:
            result = await asyncio.wait_for(
                check_func(),
                timeout=10.0
            )
            return {
                'status': 'healthy',
                **result
            }
        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Check timed out'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
```

### Provider Health Checks

```python
async def check_providers(self) -> Dict[str, Any]:
    """Check health of all configured providers"""
    providers_status = {
        'total': len(config.providers),
        'healthy': 0,
        'degraded': 0,
        'unhealthy': 0,
        'details': {}
    }

    for provider_config in config.providers:
        try:
            # Quick health check (e.g., get models list)
            start_time = time.time()
            models = await provider_factory.get_provider(provider_config.name).list_models()
            response_time = time.time() - start_time

            if response_time < 1.0 and len(models) > 0:
                status = 'healthy'
                providers_status['healthy'] += 1
            elif response_time < 5.0:
                status = 'degraded'
                providers_status['degraded'] += 1
            else:
                status = 'unhealthy'
                providers_status['unhealthy'] += 1

            providers_status['details'][provider_config.name] = {
                'status': status,
                'response_time_ms': round(response_time * 1000, 2),
                'models_count': len(models)
            }

        except Exception as e:
            providers_status['unhealthy'] += 1
            providers_status['details'][provider_config.name] = {
                'status': 'unhealthy',
                'error': str(e)
            }

    return providers_status
```

## Troubleshooting

### Common Monitoring Issues

#### Missing Metrics

**Symptoms:**
- Metrics endpoints return empty data
- Grafana dashboards show no data
- Prometheus scraping fails

**Solutions:**
```bash
# Check metrics collection
curl http://localhost:8000/debug/metrics/status

# Verify metrics configuration
curl http://localhost:8000/api/config/metrics

# Check metrics collector logs
tail -f logs/metrics.log

# Restart metrics collection
curl -X POST http://localhost:8000/debug/metrics/restart
```

#### High Memory Usage

**Symptoms:**
- Metrics collector consuming excessive memory
- Application slowdown
- Memory alerts triggering

**Solutions:**
```yaml
# Reduce metrics retention
metrics:
  retention:
    max_entries: 10000  # Reduce from 50000
    cleanup_interval: 300  # Clean every 5 minutes

# Enable metrics compression
metrics:
  compression:
    enabled: true
    algorithm: "gzip"
    level: 6

# Reduce collection frequency
metrics:
  collection:
    interval: 60  # Collect every minute instead of 30 seconds
```

#### Alert Fatigue

**Symptoms:**
- Too many alerts
- Important alerts getting lost
- Alert thresholds too sensitive

**Solutions:**
```yaml
# Adjust alert thresholds
alerting:
  rules:
    - name: "high_response_time"
      condition: "avg_response_time_ms > 2000"  # Increase from 1000
      cooldown_minutes: 10  # Increase cooldown

# Group related alerts
alerting:
  group_by: ["alertname", "severity", "provider"]
  group_wait: "1m"
  group_interval: "5m"

# Use alert inhibition
alerting:
  inhibit_rules:
    - source_match:
        alertname: "high_cpu_usage"
      target_match:
        alertname: "high_response_time"
      equal: ["instance"]
```

### Performance Issues

#### Slow Metrics Collection

**Symptoms:**
- Metrics endpoints slow to respond
- High CPU usage during collection
- Collection timeouts

**Solutions:**
```yaml
# Optimize collection settings
metrics:
  collection:
    timeout: 30  # Increase timeout
    concurrency: 2  # Reduce concurrent collections
    batch_size: 100  # Process in smaller batches

# Enable background collection
metrics:
  background:
    enabled: true
    interval: 60
    priority: "low"
```

#### Database Performance Issues

**Symptoms:**
- Slow metrics queries
- Database connection timeouts
- High database load

**Solutions:**
```yaml
# Optimize database queries
metrics:
  database:
    query_timeout: 30
    connection_pool_size: 5
    enable_query_caching: true
    cache_ttl: 300

# Use read replicas
metrics:
  database:
    read_replica_enabled: true
    replica_hosts: ["replica1", "replica2"]
```

## Best Practices

### Monitoring Setup

1. **Define Key Metrics**
   - Focus on business-critical metrics
   - Set up SLIs (Service Level Indicators)
   - Define SLOs (Service Level Objectives)

2. **Alert Configuration**
   - Use different severity levels
   - Implement alert escalation
   - Set appropriate cooldown periods
   - Test alert configurations regularly

3. **Dashboard Organization**
   - Group related metrics together
   - Use consistent color schemes
   - Include trend indicators
   - Add contextual information

### Production Considerations

1. **Resource Allocation**
   - Allocate sufficient resources for monitoring
   - Monitor monitoring system performance
   - Implement monitoring system redundancy

2. **Security**
   - Secure metrics endpoints
   - Implement access controls
   - Encrypt sensitive metrics data
   - Regular security audits

3. **Scalability**
   - Design for horizontal scaling
   - Implement metrics aggregation
   - Use sampling for high-volume metrics
   - Plan for metrics retention

### Maintenance

1. **Regular Maintenance**
   - Review and update alert thresholds
   - Clean up old metrics data
   - Update monitoring configurations
   - Test monitoring system reliability

2. **Performance Optimization**
   - Optimize metrics collection queries
   - Implement metrics caching
   - Use efficient data structures
   - Monitor monitoring system performance

3. **Documentation**
   - Document monitoring setup procedures
   - Maintain runbooks for common issues
   - Document alert response procedures
   - Keep monitoring documentation current

---

## 📊 Monitoring Dashboard Examples

### Executive Dashboard

1. **System Overview**
   - Overall system health status
   - Key performance indicators
   - Active alerts summary
   - Recent incident timeline

2. **Business Metrics**
   - Total requests processed
   - User satisfaction scores
   - Cost per request
   - Service availability

### Technical Dashboard

1. **Application Performance**
   - Request rate and success rate
   - Response time percentiles
   - Error rate by category
   - Throughput trends

2. **Infrastructure Performance**
   - CPU, memory, disk usage
   - Network I/O statistics
   - Database performance
   - Cache performance

### Provider Dashboard

1. **Provider Health**
   - Provider status overview
   - Response time by provider
   - Error rate by provider
   - Rate limit status

2. **Provider Usage**
   - Requests per provider
   - Token usage by provider
   - Cost by provider
   - Model usage distribution

---

## 🔧 Advanced Configuration

### Custom Metrics

```python
# Custom metrics implementation
class CustomMetricsCollector:
    def __init__(self):
        self.custom_metrics = {}

    def define_metric(self, name: str, type: str, description: str,
                     labels: List[str] = None):
        """Define a custom metric"""
        self.custom_metrics[name] = {
            'type': type,
            'description': description,
            'labels': labels or [],
            'values': {}
        }

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value"""
        if name not in self.custom_metrics:
            raise ValueError(f"Metric {name} not defined")

        metric = self.custom_metrics[name]
        key = self._generate_key(labels or {})

        if metric['type'] == 'counter':
            metric['values'][key] = metric['values'].get(key, 0) + value
        elif metric['type'] == 'gauge':
            metric['values'][key] = value
        elif metric['type'] == 'histogram':
            # Implement histogram logic
            pass

    def _generate_key(self, labels: Dict[str, str]) -> str:
        """Generate metric key from labels"""
        return ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
```

### Distributed Monitoring

```yaml
# Distributed monitoring configuration
distributed_monitoring:
  enabled: true
  cluster_name: "llm-proxy-cluster"

  # Metrics aggregation
  aggregation:
    enabled: true
    interval: 60
    method: "average"  # average, sum, min, max

  # Metrics forwarding
  forwarding:
    enabled: true
    targets:
      - url: "http://monitoring-central:9090/metrics"
        format: "prometheus"
      - url: "http://metrics-aggregator:8080/api/metrics"
        format: "json"

  # Health check federation
  federation:
    enabled: true
    peers:
      - "http://node1:8000/health"
      - "http://node2:8000/health"
      - "http://node3:8000/health"
```

---

## 📚 References

- [Prometheus Monitoring](https://prometheus.io/docs/introduction/overview/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [OpenTelemetry Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/)
- [Monitoring Best Practices](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Alerting Strategies](https://prometheus.io/docs/alerting/latest/alertmanager/)

---

**📊 This comprehensive monitoring guide ensures complete observability with intelligent alerting, performance tracking, and proactive issue detection for the LLM Proxy API.**