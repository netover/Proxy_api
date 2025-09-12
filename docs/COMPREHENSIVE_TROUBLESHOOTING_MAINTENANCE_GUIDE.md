
# 🔧 Comprehensive Troubleshooting and Maintenance Guide - ProxyAPI

Complete guide for troubleshooting, maintenance, and operational procedures for the ProxyAPI LLM proxy system.

## Table of Contents

- [Introduction](#introduction)
- [Quick Diagnosis](#quick-diagnosis)
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Diagnostic Tools and Procedures](#diagnostic-tools-and-procedures)
- [Performance Troubleshooting](#performance-troubleshooting)
- [Memory Leak Diagnosis](#memory-leak-diagnosis)
- [Cache Issues](#cache-issues)
- [Provider Connectivity Problems](#provider-connectivity-problems)
- [Security Incidents](#security-incidents)
- [Log Analysis Techniques](#log-analysis-techniques)
- [Health Check Procedures](#health-check-procedures)
- [Backup and Recovery Procedures](#backup-and-recovery-procedures)
- [System Monitoring Best Practices](#system-monitoring-best-practices)
- [Diagnostic Scripts and Maintenance Checklists](#diagnostic-scripts-and-maintenance-checklists)
- [Troubleshooting Flowcharts](#troubleshooting-flowcharts)
- [Database Maintenance](#database-maintenance)
- [Code Deployment Procedures](#code-deployment-procedures)
- [Emergency Response Procedures](#emergency-response-procedures)
- [Preventive Maintenance Tasks](#preventive-maintenance-tasks)
- [Operational Procedures](#operational-procedures)

## Introduction

This comprehensive guide provides systematic approaches to diagnose, troubleshoot, and maintain the ProxyAPI system. It covers everything from basic troubleshooting to advanced maintenance procedures, security incident response, and operational best practices.

### Key Features

- **Comprehensive Coverage**: All aspects of troubleshooting and maintenance
- **Practical Procedures**: Step-by-step diagnostic and resolution procedures
- **Security Focus**: Security incident response and prevention
- **Performance Optimization**: Memory leak diagnosis, cache optimization, performance tuning
- **Operational Excellence**: Backup/recovery, deployment procedures, monitoring

### Prerequisites

- Access to ProxyAPI logs and configuration files
- System administration privileges
- Understanding of LLM proxy architecture
- Familiarity with monitoring and alerting systems

---

## Quick Diagnosis

### Health Check Script

```bash
#!/bin/bash
# Comprehensive health check script

echo "=== ProxyAPI Health Check ==="
echo "Timestamp: $(date)"
echo

# Service status
echo "1. Service Status:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Service is running"
else
    echo "❌ Service is not responding"
fi
echo

# API health
echo "2. API Health:"
HEALTH=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    STATUS=$(echo $HEALTH | jq -r '.status')
    echo "Status: $STATUS"

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ API is healthy"
    else
        echo "❌ API has issues"
        echo "Details: $HEALTH" | jq '.'
    fi
else
    echo "❌ Cannot connect to health endpoint"
fi
echo

# Provider status
echo "3. Provider Health:"
PROVIDERS=$(curl -s http://localhost:8000/health/providers)
if [ $? -eq 0 ]; then
    echo "Provider health details:"
    echo $PROVIDERS | jq '.'
else
    echo "❌ Cannot check provider status"
fi
echo

# System resources
echo "4. System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.2f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df / | tail -1 | awk '{print $5}')"
echo

# Cache status
echo "5. Cache Status:"
CACHE=$(curl -s http://localhost:8000/health/cache)
if [ $? -eq 0 ]; then
    echo "Cache health details:"
    echo $CACHE | jq '.'
else
    echo "❌ Cannot check cache status"
fi
echo

echo "=== Health Check Complete ==="
```

### Diagnostic Commands

```bash
# Service management
sudo systemctl status llm-proxy
docker-compose ps
ps aux | grep python

# Log inspection
tail -f logs/llm_proxy.log
docker-compose logs -f llm-proxy
journalctl -u llm-proxy -n 50

# Resource monitoring
top -p $(pgrep -f python)
htop
free -h
df -h

# Network diagnostics
netstat -tlnp | grep :8000
ss -tlnp | grep :8000
curl -I http://localhost:8000/health

# Process inspection
ps aux --sort=-%mem | head -10
lsof -p $(pgrep -f python) | wc -l
```

---

## Common Issues and Solutions

### Installation and Startup Issues

#### Python Version Compatibility

**Symptoms:**
- `ModuleNotFoundError` during installation
- `python3: command not found`
- Incompatible Python version errors

**Diagnosis:**
```bash
# Check Python version
python3 --version
python --version

# Check pip installation
pip3 --version

# Verify Python path
which python3
which pip3
```

**Solutions:**

1. **Install Compatible Python Version**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt install python3.11 python3.11-venv python3.11-pip

   # CentOS/RHEL
   sudo yum install python311 python311-pip

   # macOS
   brew install python@3.11
   ```

2. **Update pip**
   ```bash
   python3 -m pip install --upgrade pip
   ```

3. **Use Virtual Environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### Dependency Installation Failures

**Symptoms:**
- Compilation errors during pip install
- Missing system libraries
- Permission denied errors

**Diagnosis:**
```bash
# Check pip version and logs
pip --version
pip install -r requirements.txt -v

# Check system libraries
ldd $(which python3)
pkg-config --list-all | grep -i ssl
```

**Solutions:**

1. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt install build-essential python3-dev libssl-dev

   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install python3-devel openssl-devel

   # macOS
   xcode-select --install
   ```

2. **Use Pre-compiled Packages**
   ```bash
   # Use PyPI wheels
   pip install --only-binary=all -r requirements.txt
   ```

3. **Fix Permission Issues**
   ```bash
   # Use user installation
   pip install --user -r requirements.txt

   # Or fix virtual environment permissions
   sudo chown -R $USER:$USER venv/
   ```

#### Docker Installation Issues

**Symptoms:**
- `docker build` fails
- Container won't start
- Port binding issues

**Diagnosis:**
```bash
# Check Docker status
docker --version
docker info

# Inspect build logs
docker build -t proxyapi . --progress=plain

# Check container logs
docker logs proxyapi

# Verify port conflicts
docker ps
netstat -tlnp | grep :8000
```

**Solutions:**

1. **Fix Port Conflicts**
   ```bash
   # Use different host port
   docker run -p 8001:8000 proxyapi

   # Stop conflicting services
   sudo systemctl stop apache2
   ```

2. **Fix Permission Issues**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER

   # Or run with sudo
   sudo docker run -p 8000:8000 proxyapi
   ```

3. **Optimize Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       curl \
       && rm -rf /var/lib/apt/lists/*

   # Create application user
   RUN useradd --create-home --shell /bin/bash app

   # Set working directory
   WORKDIR /app

   # Copy requirements first for better caching
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .

   # Create necessary directories
   RUN mkdir -p logs cache && chown -R app:app /app

   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
       CMD curl -f http://localhost:8000/health || exit 1

   # Switch to non-root user
   USER app

   # Expose port
   EXPOSE 8000

   # Start application
   CMD ["python", "main.py"]
   ```

---

## Diagnostic Tools and Procedures

### System Resource Monitoring

#### CPU Usage Analysis

```bash
# Real-time CPU monitoring
top -d 1

# CPU usage by process
ps aux --sort=-%cpu | head -10

# CPU load average
uptime

# Detailed CPU statistics
mpstat -P ALL 1

# Process-specific CPU profiling
pidstat -p $(pgrep -f python) 1
```

#### Memory Usage Analysis

```bash
# Memory overview
free -h

# Process memory usage
ps aux --sort=-%mem | head -10

# Memory mapping
pmap -x $(pgrep -f python)

# Memory statistics
cat /proc/$(pgrep -f python)/status
```

#### Disk Usage Analysis

```bash
# Disk usage summary
df -h

# Directory sizes
du -sh /opt/proxyapi/*
du -sh /var/log/*

# Find large files
find /opt/proxyapi -type f -size +100M -exec ls -lh {} \;

# Disk I/O statistics
iostat -dx 1
```

#### Network Analysis

```bash
# Network connections
netstat -tlnp
ss -tlnp

# Network traffic
iftop
nload

# Connection tracking
conntrack -L | wc -l

# Network interface statistics
ip -s link
```

### Application Diagnostics

#### Performance Profiling

```python
# Application profiling script
import cProfile
import pstats
from io import StringIO

def profile_application():
    profiler = cProfile.Profile()
    profiler.enable()

    # Application code here
    import main_dynamic

    profiler.disable()

    # Generate report
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')

    # Print top functions
    output = StringIO()
    stats.print_stats(20, stream=output)
    print(output.getvalue())

if __name__ == "__main__":
    profile_application()
```

#### Memory Profiling

```python
# Memory usage profiling
from memory_profiler import profile, memory_usage
import tracemalloc

@profile
def memory_intensive_function():
    # Function to profile
    pass

def profile_memory():
    tracemalloc.start()

    # Code to profile
    memory_intensive_function()

    current, peak = tracemalloc.get_traced_memory()
    print(".1f")
    print(".1f")

    tracemalloc.stop()

if __name__ == "__main__":
    profile_memory()
```

#### Thread and Process Analysis

```bash
# Thread analysis
ps -T -p $(pgrep -f python)

# Thread stack traces
kill -QUIT $(pgrep -f python)  # Send SIGQUIT for thread dump

# Process tree
pstree -p $(pgrep -f python)

# Process limits
cat /proc/$(pgrep -f python)/limits
```

### Database Diagnostics

#### Connection Pool Analysis

```python
# Database connection analysis
import asyncpg
import asyncio

async def analyze_db_connections():
    try:
        conn = await asyncpg.connect(
            user='proxyapi',
            database='proxyapi_db',
            host='localhost'
        )

        # Check active connections
        result = await conn.fetchval("""
            SELECT count(*) FROM pg_stat_activity
            WHERE datname = 'proxyapi_db'
        """)
        print(f"Active connections: {result}")

        # Check connection age
        result = await conn.fetch("""
            SELECT pid, state, state_change
            FROM pg_stat_activity
            WHERE datname = 'proxyapi_db'
            ORDER BY state_change ASC
        """)

        for row in result:
            print(f"PID: {row['pid']}, State: {row['state']}, Age: {row['state_change']}")

        await conn.close()

    except Exception as e:
        print(f"Database analysis failed: {e}")

asyncio.run(analyze_db_connections())
```

#### Query Performance Analysis

```python
# Query performance analysis
async def analyze_query_performance():
    conn = await asyncpg.connect(
        user='proxyapi',
        database='proxyapi_db',
        host='localhost'
    )

    # Slow queries
    slow_queries = await conn.fetch("""
        SELECT query, mean_time, calls, rows
        FROM pg_stat_statements
        ORDER BY mean_time DESC
        LIMIT 10
    """)

    print("Top slow queries:")
    for query in slow_queries:
        print(f"Query: {query['query'][:100]}...")
        print(".2f")
        print(f"Calls: {query['calls']}")
        print("---"

    # Table statistics
    tables = await conn.fetch("""
        SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
        FROM pg_stat_user_tables
        ORDER BY n_tup_ins DESC
        LIMIT 10
    """)

    print("
Top tables by activity:")
    for table in tables:
        print(f"{table['schemaname']}.{table['tablename']}:")
        print(f"  Inserts: {table['n_tup_ins']}")
        print(f"  Updates: {table['n_tup_upd']}")
        print(f"  Deletes: {table['n_tup_del']}")

    await conn.close()

asyncio.run(analyze_query_performance())
```

---

## Performance Troubleshooting

### High Latency Issues

**Symptoms:**
- Response times > 500ms consistently
- Timeout errors
- User complaints about slow performance

**Diagnosis:**

```bash
# Check current latency metrics
curl http://localhost:8000/metrics | jq '.performance.avg_response_time_ms'

# Monitor request latency distribution
curl http://localhost:8000/metrics | jq '.performance.response_time_percentiles'

# Check provider latency
curl http://localhost:8000/health/providers

# Profile application performance
python -m cProfile -s cumulative main_dynamic.py
```

**Solutions:**

1. **Optimize Caching Strategy**
   ```yaml
   # config.yaml
   caching:
     enabled: true
     response_cache:
       max_size_mb: 1024
       ttl: 1800
       compression: true
     summary_cache:
       max_size_mb: 512
       ttl: 3600
       compression: true
   ```

2. **Tune Connection Pool**
   ```yaml
   http_client:
     pool_limits:
       max_connections: 200
       max_keepalive_connections: 50
     timeout: 25.0
     retry_attempts: 3
   ```

3. **Enable Performance Monitoring**
   ```yaml
   performance:
     profiling: true
     slow_request_threshold: 1000
     metrics_collection_interval: 30
   ```

### High CPU Usage

**Symptoms:**
- CPU usage > 80%
- Slow response times
- System becoming unresponsive

**Diagnosis:**

```bash
# CPU usage analysis
top -bn1 | head -10

# Process CPU consumption
ps aux --sort=-%cpu | head -10

# Thread analysis
ps -T -p $(pgrep -f python)

# CPU profiling
python -m cProfile -s time main_dynamic.py
```

**Solutions:**

1. **Optimize Worker Configuration**
   ```yaml
   server:
     workers: 4
     worker_class: "uvicorn.workers.UvicornWorker"
     worker_connections: 1000
     max_requests: 1000
     max_requests_jitter: 50
   ```

2. **Enable Async Operations**
   ```python
   # Use async/await for I/O operations
   async def handle_request(request):
       # Async database operations
       result = await database.fetch(query)

       # Async HTTP requests
       response = await http_client.request(url, data)

       return result
   ```

3. **Implement CPU Monitoring**
   ```yaml
   monitoring:
     cpu:
       threshold_percent: 80
       alert_enabled: true
       scaling_enabled: true
   ```

### Throughput Issues

**Symptoms:**
- Low requests per second
- Queue buildup
- Connection refused errors

**Diagnosis:**

```bash
# Check current throughput
curl http://localhost:8000/metrics | jq '.performance.requests_per_second'

# Monitor queue depth
curl http://localhost:8000/metrics | jq '.performance.queue_depth'

# Check connection pool utilization
curl http://localhost:8000/metrics | jq '.http_client.pool_utilization'
```

**Solutions:**

1. **Scale Horizontally**
   ```bash
   # Increase number of instances
   docker-compose up --scale proxyapi=3

   # Or use Kubernetes HPA
   kubectl scale deployment proxyapi --replicas=5
   ```

2. **Optimize Resource Allocation**
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "500m"
     limits:
       memory: "2Gi"
       cpu: "2000m"
   ```

3. **Implement Load Balancing**
   ```nginx
   upstream proxyapi_backend {
       least_conn;
       server proxyapi-1:8000;
       server proxyapi-2:8000;
       server proxyapi-3:8000;
   }
   ```

---

## Memory Leak Diagnosis

### Memory Usage Analysis

**Symptoms:**
- Gradual memory increase over time
- Out of memory errors
- Application restarts due to memory pressure

**Diagnosis:**

```bash
# Memory usage monitoring
free -h
ps aux --sort=-%mem | head -10

# Memory mapping
pmap -x $(pgrep -f python)

# Run memory profiling script
python scripts/memory_profiling_benchmark.py --light --both --export-results
```

**Diagnostic Script:**

```python
# memory_diagnostic.py
import tracemalloc
import gc
import psutil
from collections import defaultdict
import time

class MemoryDiagnostic:
    def __init__(self):
        self.snapshots = []
        self.process = psutil.Process()

    def start_diagnosis(self):
        """Start memory diagnosis"""
        tracemalloc.start()
        self.take_snapshot("baseline")

    def take_snapshot(self, label: str):
        """Take memory snapshot"""
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append({
            'label': label,
            'timestamp': time.time(),
            'snapshot': snapshot,
            'rss_mb': self.process.memory_info().rss / 1024 / 1024,
            'vms_mb': self.process.memory_info().vms / 1024 / 1024
        })

    def analyze_leaks(self):
        """Analyze potential memory leaks"""
        if len(self.snapshots) < 2:
            return "Need at least 2 snapshots for analysis"

        analysis = {
            'snapshots': len(self.snapshots),
            'leak_candidates': [],
            'gc_stats': gc.get_stats()
        }

        # Compare snapshots
        for i in range(1, len(self.snapshots)):
            prev = self.snapshots[i-1]['snapshot']
            curr = self.snapshots[i]['snapshot']

            stats = curr.compare_to(prev, 'lineno')

            # Find significant memory increases
            for stat in stats:
                if stat.size_diff > 1024 * 1024:  # > 1MB increase
                    analysis['leak_candidates'].append({
                        'file': stat.filename,
                        'line': stat.lineno,
                        'size_increase_mb': stat.size_diff / 1024 / 1024,
                        'count_diff': stat.count_diff
                    })

        return analysis

    def force_gc_and_analyze(self):
        """Force garbage collection and analyze"""
        before_gc = self.process.memory_info().rss / 1024 / 1024
        collected = gc.collect()
        after_gc = self.process.memory_info().rss / 1024 / 1024

        return {
            'before_gc_mb': before_gc,
            'after_gc_mb': after_gc,
            'freed_mb': before_gc - after_gc,
            'objects_collected': collected
        }

# Usage
diagnostic = MemoryDiagnostic()
diagnostic.start_diagnosis()

# Run application code here
# ... application logic ...

diagnostic.take_snapshot("after_operations")
analysis = diagnostic.analyze_leaks()
gc_analysis = diagnostic.force_gc_and_analyze()

print("Memory Analysis Results:")
print(f"Leak candidates: {len(analysis['leak_candidates'])}")
print(f"GC freed: {gc_analysis['freed_mb']:.2f} MB")
```

**Solutions:**

1. **Enable Memory Optimization**
   ```yaml
   memory:
     max_usage_percent: 80
     gc_threshold_percent: 75
     monitoring_interval: 30
     emergency_cleanup: true
     leak_detection: true
   ```

2. **Implement Memory Profiling**
   ```python
   # Add memory profiling to application
   from memory_profiler import profile

   @profile
   def memory_intensive_operation():
       # Operation code here
       pass
   ```

3. **Configure Memory Limits**
   ```yaml
   resources:
     limits:
       memory: "2Gi"
     requests:
       memory: "512Mi"
   ```

### Cache Memory Issues

**Symptoms:**
- Cache memory usage constantly increasing
- Cache eviction not working properly
- Memory pressure due to cache

**Diagnosis:**

```bash
# Check cache memory usage
curl http://localhost:8000/metrics | jq '.cache.memory_usage_mb'

# Monitor cache size
curl http://localhost:8000/metrics | jq '.cache.entries'

# Check cache hit rate
curl http://localhost:8000/metrics | jq '.cache.hit_rate'
```

**Solutions:**

1. **Configure Cache Limits**
   ```yaml
   caching:
     response_cache:
       max_size_mb: 512
       max_entries: 10000
     summary_cache:
       max_size_mb: 256
       max_entries: 5000
   ```

2. **Implement Cache Warming**
   ```yaml
   cache_warming:
     enabled: true
     interval: 300
     preload_popular: true
     max_warming_size_mb: 100
   ```

3. **Enable Memory-Aware Eviction**
   ```yaml
   memory_aware_cache:
     enabled: true
     memory_threshold: 80
     eviction_batch_size: 100
     emergency_cleanup: true
   ```

---

## Cache Issues

### Cache Hit Rate Problems

**Symptoms:**
- Low cache hit rate (< 50%)
- High external API calls
- Increased latency and costs

**Diagnosis:**

```bash
# Check cache metrics
curl http://localhost:8000/metrics/cache

# Analyze cache keys
curl http://localhost:8000/debug/cache/keys | jq '.'

# Monitor cache warming
curl http://localhost:8000/metrics/cache/warming
```

**Solutions:**

1. **Optimize Cache Configuration**
   ```yaml
   caching:
     response_cache:
       max_size_mb: 1024
       ttl: 1800
       compression: true
       strategy: "lru"
     summary_cache:
       max_size_mb: 512
       ttl: 3600
       compression: true
       strategy: "lfu"
   ```

2. **Implement Cache Warming**
   ```python
   # Cache warming script
   async def warm_cache():
       """Warm cache with popular requests"""
       popular_requests = [
           {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]},
           {"model": "claude-3-sonnet", "messages": [{"role": "user", "content": "Hello"}]}
       ]

       for request in popular_requests:
           await cache.set(f"warm_{hash(str(request))}", request, category="warming")
   ```

3. **Enable Cache Analytics**
   ```yaml
   cache_analytics:
     enabled: true
     track_popularity: true
     adaptive_ttl: true
     report_interval: 300
   ```

### Cache Invalidation Issues

**Symptoms:**
- Stale data in cache
- Inconsistent responses
- Cache not updating with new data

**Diagnosis:**

```bash
# Check cache TTL settings
curl http://localhost:8000/debug/cache/config

# Monitor cache age
curl http://localhost:8000/debug/cache/stats | jq '.oldest_entry_age_seconds'

# Test cache invalidation
curl -X DELETE http://localhost:8000/api/cache
```

**Solutions:**

1. **Configure Appropriate TTL**
   ```yaml
   caching:
     response_cache:
       ttl: 1800  # 30 minutes
       ttl_jitter: 0.1  # 10% jitter
     summary_cache:
       ttl: 3600  # 1 hour
       ttl_jitter: 0.1
   ```

2. **Implement Smart Invalidation**
   ```python
   # Smart cache invalidation
   class SmartCacheInvalidator:
       def __init__(self):
           self.patterns = {
               'model_updates': re.compile(r'model.*update'),
               'provider_changes': re.compile(r'provider.*change'),
               'config_changes': re.compile(r'config.*change')
           }

       async def invalidate_related(self, key: str):
           """Invalidate related cache entries"""
           for pattern_name, pattern in self.patterns.items():
               if pattern.search(key):
                   await self.invalidate_pattern(pattern_name)
   ```

3. **Enable Cache Versioning**
   ```yaml
   cache_versioning:
     enabled: true
     version_key: "cache_version"
     auto_invalidate_on_deploy: true
   ```

### Cache Memory Pressure

**Symptoms:**
- Cache using too much memory
- System memory pressure
- Cache eviction not working

**Diagnosis:**

```bash
# Check cache memory usage
curl http://localhost:8000/health/cache | jq '.memory_usage_mb'

# Monitor eviction rate
curl http://localhost:8000/metrics/cache | jq '.evictions'

# Check system memory
free -h
```

**Solutions:**

1. **Implement Memory-Aware Caching**
   ```yaml
   memory_aware_cache:
     enabled: true
     memory_threshold: 80
     eviction_policy: "memory_pressure"
     emergency_cleanup: true
   ```

2. **Configure Cache Limits**
   ```yaml
   caching:
     response_cache:
       max_size_mb: 512
       memory_pressure_threshold: 75
     summary_cache:
       max_size_mb: 256
       memory_pressure_threshold: 75
   ```

3. **Enable Compression**
   ```yaml
   cache_compression:
     enabled: true
     algorithm: "gzip"
     level: 6
     min_size_kb: 1
   ```

---

## Provider Connectivity Problems

### Connection Failures

**Symptoms:**
- Provider API connection errors
- Timeout errors
- DNS resolution failures

**Diagnosis:**

```bash
# Test basic connectivity
ping api.openai.com

# DNS resolution
nslookup api.openai.com

# HTTPS connectivity test
curl -I https://api.openai.com/v1/models

# Check proxy settings
env | grep -i proxy
```

**Solutions:**

1. **Fix DNS Issues**
   ```bash
   # Update DNS servers
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf
   ```

2. **Configure Proxy Settings**
   ```bash
   # Set proxy environment variables
   export HTTP_PROXY="http://proxy.company.com:8080"
   export HTTPS_PROXY="http://proxy.company.com:8080"
   export NO_PROXY="localhost,127.0.0.1"
   ```

3. **Update Connection Configuration**
   ```yaml
   http_client:
     timeout: 30.0
     connect_timeout: 10.0
     retry_attempts: 3
     proxies:
       http: "http://proxy.company.com:8080"
       https: "http://proxy.company.com:8080"
   ```

### Rate Limiting Issues

**Symptoms:**
- 429 Too Many Requests errors
- Intermittent failures
- Provider quota exhaustion

**Diagnosis:**

```bash
# Check rate limit headers
curl -I http://localhost:8000/api/models

# Monitor rate limit metrics
curl http://localhost:8000/metrics | jq '.rate_limiting'

# Check provider rate limits
curl http://localhost:8000/health/providers | jq '.[].rate_limit_remaining'
```

**Solutions:**

1. **Implement Rate Limiting**
   ```yaml
   rate_limiting:
     enabled: true
     strategy: "sliding_window"
     requests_per_minute: 60
     burst_limit: 10
     backoff_factor: 2.0
   ```

2. **Configure Provider-Specific Limits**
   ```yaml
   providers:
     - name: "openai"
       rate_limit: 100  # requests per minute
       burst_limit: 20
     - name: "anthropic"
       rate_limit: 50
       burst_limit: 10
   ```

3. **Implement Exponential Backoff**
   ```python
   import asyncio
   import time

   class RateLimitHandler:
       def __init__(self):
           self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff

       async def handle_rate_limit(self, response, retry_count=0):
           if response.status_code == 429 and retry_count < len(self.retry_delays):
               delay = self.retry_delays[retry_count]
               print(f"Rate limited. Retrying in {delay} seconds...")
               await asyncio.sleep(delay)
               return True  # Retry
           return False  # Don't retry
   ```

### Provider Authentication Issues

**Symptoms:**
- 401 Unauthorized errors
- Invalid API key errors
- Authentication failures

**Diagnosis:**

```bash
# Test API key validity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check API key format
echo $OPENAI_API_KEY | head -c 10

# Test with proxy
curl http://localhost:8000/api/models \
  -H "Authorization: Bearer $API_KEY"
```

**Solutions:**

1. **Update API Keys**
   ```bash
   # Update environment variables
   export OPENAI_API_KEY="sk-your-new-key"
   export ANTHROPIC_API_KEY="sk-ant-your-new-key"

   # Update configuration
   sed -i 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=sk-new-key/' .env
   ```

2. **Implement Key Rotation**
   ```yaml
   api_key_rotation:
     enabled: true
     rotation_interval_days: 30
     grace_period_hours: 24
     notification_enabled: true
   ```

3. **Configure Multiple Keys**
   ```yaml
   providers:
     - name: "openai"
       api_keys:
         - "sk-key1"
         - "sk-key2"
         - "sk-key3"
       key_rotation: true
   ```

---

## Security Incidents

### Authentication Security Incidents

**Symptoms:**
- Multiple failed authentication attempts
- Suspicious login patterns
- API key abuse

**Diagnosis:**

```bash
# Check authentication logs
grep "authentication" logs/security.log | tail -20

# Monitor failed attempts
curl http://localhost:8000/metrics/security | jq '.failed_auth_attempts'

# Analyze IP patterns
grep "failed_auth" logs/llm_proxy.log | awk '{print $NF}' | sort | uniq -c | sort -nr
```

**Response Procedures:**

1. **Immediate Actions**
   ```bash
   # Block suspicious IP
   sudo iptables -A INPUT -s SUSPICIOUS_IP -j DROP

   # Rotate API keys
   export API_KEY="new-secure-key"

   # Restart service
   sudo systemctl restart llm-proxy
   ```

2. **Investigation**
   ```bash
   # Analyze attack patterns
   grep "SUSPICIOUS_IP" logs/llm_proxy.log

   # Check for brute force patterns
   awk '/failed_auth/ {print $1, $NF}' logs/llm_proxy.log | sort | uniq -c

   # Review security logs
   tail -100 logs/security.log
   ```

3. **Recovery**
   ```bash
   # Restore from backup
   cp config.yaml.backup config.yaml

   # Update security policies
   echo "Rate limiting enabled with stricter limits"

   # Notify stakeholders
   echo "Security incident investigation complete"
   ```

### Data Breach Response

**Symptoms:**
- Unauthorized data access
- Sensitive data exposure
- Suspicious file access

**Diagnosis:**

```bash
# Check access logs
grep "unauthorized" logs/security.log

# Monitor data access
curl http://localhost:8000/metrics/security | jq '.data_access'

# Analyze file access
ausearch -m PATH -f /opt/proxyapi/
```

**Response Procedures:**

1. **Containment**
   ```bash
   # Isolate affected systems
   sudo systemctl stop llm-proxy

   # Change all credentials
   ./rotate_all_credentials.sh

   # Block external access
   sudo iptables -P INPUT DROP
   ```

2. **Assessment**
   ```bash
   # Identify compromised data
   grep "sensitive" logs/llm_proxy.log

   # Check data integrity
   sha256sum /opt/proxyapi/data/* > integrity_check.txt

   # Review access controls
   ls -la /opt/proxyapi/
   ```

3. **Recovery**
   ```bash
   # Restore from clean backup
   ./restore_from_backup.sh latest_clean_backup

   # Update security measures
   ./update_security_policies.sh

   # Monitor for recurrence
   ./enable_enhanced_monitoring.sh
   ```

### Incident Response Plan

#### Phase 1: Detection and Assessment
```bash
# 1. Confirm incident
curl http://localhost:8000/health

# 2. Isolate affected systems
sudo systemctl stop compromised-service

# 3. Preserve evidence
./collect_forensic_data.sh

# 4. Notify security team
./notify_security_team.sh
```

#### Phase 2: Containment
```bash
# 1. Block malicious activity
sudo iptables -A INPUT -s MALICIOUS_IP -j DROP

# 2. Change credentials
./rotate_credentials.sh

# 3. Update access controls
./update_firewall_rules.sh

# 4. Implement temporary measures
./enable_emergency_mode.sh
```

#### Phase 3: Recovery
```bash
# 1. Restore from backup
./restore_clean_backup.sh

# 2. Test system integrity
./run_security_tests.sh

# 3. Gradually restore services
./gradual_service_restoration.sh

# 4. Monitor for issues
./enable_enhanced_monitoring.sh
```

#### Phase 4: Lessons Learned
```bash
# 1. Conduct post-mortem
./conduct_post_mortem.sh

# 2. Update procedures
./update_incident_response_plan.sh

# 3. Implement improvements
./implement_security_improvements.sh

# 4. Train team
./conduct_security_training.sh
```

---

## Log Analysis Techniques

### Log Analysis Tools

#### Basic Log Analysis

```bash
# Search for errors
grep "ERROR" logs/llm_proxy.log | tail -10

# Count error types
grep "ERROR" logs/llm_proxy.log | awk '{print $4}' | sort | uniq -c | sort -nr

# Find slow requests
grep "response_time_ms" logs/llm_proxy.log | jq 'select(.response_time_ms > 5000)'

# Analyze by time period
grep "2024-01-15" logs/llm_proxy.log | jq -r '.level' | sort | uniq -c

# Find authentication failures
grep "authentication" logs/llm_proxy.log | jq 'select(.success == false)'
```

#### Advanced Log Analysis

```python
# log_analyzer.py
import json
from collections import defaultdict, Counter
import datetime
from pathlib import Path

class LogAnalyzer:
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.entries = []

    def parse_logs(self):
        """Parse log entries"""
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    self.entries.append(entry)
                except json.JSONDecodeError:
                    continue

    def analyze_errors(self):
        """Analyze error patterns"""
        errors = [e for e in self.entries if e.get('level') == 'ERROR']

        error_types = Counter()
        error_trends = defaultdict(int)

        for error in errors:
            # Categorize errors
            message = error.get('message', '').lower()
            if 'timeout' in message:
                error_types['timeout'] += 1
            elif 'connection' in message:
                error_types['connection'] += 1
            elif 'rate_limit' in message:
                error_types['rate_limit'] += 1
            else:
                error_types['other'] += 1

            # Time-based trends
            timestamp = error.get('timestamp', '')
            if timestamp:
                hour = timestamp.split('T')[1][:2]
                error_trends[hour] += 1

        return {
            'total_errors': len(errors),
            'error_types': dict(error_types),
            'error_trends': dict(error_trends)
        }

    def analyze_performance(self):
        """Analyze performance metrics"""
        response_times = []

        for entry in self.entries:
            if 'response_time_ms' in entry:
                response_times.append(entry['response_time_ms'])

        if not response_times:
            return {}

        response_times.sort()

        return {
            'total_requests': len(response_times),
            'avg_response_time': sum(response_times) / len(response_times),
            'p50_response_time': response_times[len(response_times) // 2],
            'p95_response_time': response_times[int(len(response_times) * 0.95)],
            'p99_response_time': response_times[int(len(response_times) * 0.99)],
            'max_response_time': max(response_times),
            'slow_requests': len([rt for rt in response_times if rt > 5000])
        }

    def analyze_security(self):
        """Analyze security events"""
        security_events = []

        for entry in self.entries:
            if any(keyword in str(entry).lower() for keyword in
                   ['auth', 'security', 'unauthorized', 'suspicious']):
                security_events.append(entry)

        return {
            'total_security_events': len(security_events),
            'events_by_type': self._categorize_security_events(security_events)
        }

    def _categorize_security_events(self, events):
        """Categorize security events"""
        categories = defaultdict(int)

        for event in events:
            message = str(event.get('message', '')).lower()
            if 'unauthorized' in message:
                categories['unauthorized_access'] += 1
            elif 'rate_limit' in message:
                categories['rate_limit'] += 1
            elif 'auth' in message:
                categories['authentication'] += 1
            else:
                categories['other'] += 1

        return dict(categories)

    def generate_report(self):
        """Generate comprehensive analysis report"""
        self.parse_logs()

        return {
            'summary': {
                'total_entries': len(self.entries),
                'time_range': self._get_time_range(),
                'log_file': str(self.log_file)
            },
            'errors': self.analyze_errors(),
            'performance': self.analyze_performance(),
            'security': self.analyze_security()
        }

    def _get_time_range(self):
        """Get time range of logs"""
        if not self.entries:
            return "No entries"

        timestamps = [e.get('timestamp') for e in self.entries if e.get('timestamp')]
        if not timestamps:
            return "No timestamps"

        timestamps.sort()
        return f"{timestamps[0]} to {timestamps[-1]}"

# Usage
analyzer = LogAnalyzer('logs/llm_proxy.log')
report = analyzer.generate_report()

print(json.dumps(report, indent=2))
```

#### Log Monitoring and Alerting

```yaml
# Log monitoring configuration
log_monitoring:
  enabled: true

  rules:
    - name: "high_error_rate"
      pattern: '"level": "ERROR"'
      threshold: 10
      window_minutes: 5
      severity: "critical"
      channels: ["slack", "email"]

    - name: "slow_requests"
      pattern: '"response_time_ms": \d+'
      condition: "response_time_ms > 5000"
      threshold: 5
      window_minutes: 10
      severity: "warning"
      channels: ["slack"]

    - name: "security_events"
      pattern: '"level": "(ERROR|WARNING)".*"security"'
      threshold: 1
      window_minutes: 1
      severity: "critical"
      channels: ["security_team", "pagerduty"]

    - name: "auth_failures"
      pattern: '"authentication".*"success": false'
      threshold: 5
      window_minutes: 15
      severity: "warning"
      channels: ["slack"]
```

#### Log Rotation and Retention

```yaml
# Log rotation configuration
logging:
  rotation:
    enabled: true
    max_file_size: "100MB"
    max_files: 30
    when: "midnight"
    compression: "gzip"
    compression_level: 6

  retention:
    policy: "time_based"
    max_age_days: 90
    min_free_space_gb: 10
    cleanup_schedule: "0 2 * * *"  # Daily at 2 AM

  archival:
    enabled: true
    archive_path: "/opt/proxyapi/logs/archive"
    archive_format: "tar.gz"
    archive_schedule: "0 3 * * 0"  # Weekly on Sunday
```

---

## Health Check Procedures

### Comprehensive Health Checks

#### System Health Check

```bash
#!/bin/bash
# system_health_check.sh

echo "=== System Health Check ==="
echo "Timestamp: $(date)"
echo

# CPU Health
echo "CPU Health:"
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/")
echo "CPU Usage: ${CPU_USAGE}%"
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "⚠️  High CPU usage detected"
fi
echo

# Memory Health
echo "Memory Health:"
MEMORY_INFO=$(free | grep Mem)
TOTAL_MEM=$(echo $MEMORY_INFO | awk '{print $2}')
USED_MEM=$(echo $MEMORY_INFO | awk '{print $3}')
MEMORY_PERCENT=$(echo "scale=2; $USED_MEM * 100 / $TOTAL_MEM" | bc)
echo "Memory Usage: ${MEMORY_PERCENT}%"
if (( $(echo "$MEMORY_PERCENT > 85" | bc -l) )); then
    echo "⚠️  High memory usage detected"
fi
echo

# Disk Health
echo "Disk Health:"
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
echo "Disk Usage: ${DISK_USAGE}%"
if (( DISK_USAGE > 90 )); then
    echo "⚠️  High disk usage detected"
fi
echo

# Network Health
echo "Network Health:"
NETWORK_ERRORS=$(ip -s link | grep -A 1 "eth0\|enp" | tail -1 | awk '{print $3}')
echo "Network Errors: $NETWORK_ERRORS"
if (( NETWORK_ERRORS > 0 )); then
    echo "⚠️  Network errors detected"
fi
echo

# Service Health
echo "Service Health:"
if pgrep -f "python.*main" > /dev/null; then
    echo "✅ ProxyAPI service is running"
else
    echo "❌ ProxyAPI service is not running"
fi
echo

echo "=== Health Check Complete ==="
```

#### Application Health Check

```python
# health_check.py
import asyncio
import aiohttp
import psutil
import time
from typing import Dict, Any

class HealthChecker:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.process = psutil.Process()

    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        health_status = {
            "timestamp": time.time(),
            "overall_status": "healthy",
            "checks": {}
        }

        try
            # Application health
            app_health = await self.check_application_health()
            health_status["checks"]["application"] = app_health

            # Provider health
            provider_health = await self.check_providers_health()
            health_status["checks"]["providers"] = provider_health

            # Cache health
            cache_health = await self.check_cache_health()
            health_status["checks"]["cache"] = cache_health

            # System health
            system_health = self.check_system_health()
            health_status["checks"]["system"] = system_health

            # Determine overall status
            all_checks = [app_health, provider_health, cache_health, system_health]
            if any(check.get("status") == "unhealthy" for check in all_checks):
                health_status["overall_status"] = "unhealthy"

        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)

        return health_status

    async def check_application_health(self) -> Dict[str, Any]:
        """Check application health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time_ms": response.headers.get("X-Response-Time", 0),
                            "version": data.get("version"),
                            "uptime": data.get("uptime_seconds", 0)
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}",
                            "response_time_ms": response.headers.get("X-Response-Time", 0)
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_providers_health(self) -> Dict[str, Any]:
        """Check providers health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health/providers") as response:
                    if response.status == 200:
                        data = await response.json()
                        healthy_count = sum(1 for p in data.values() if p.get("status") == "healthy")
                        return {
                            "status": "healthy" if healthy_count > 0 else "degraded",
                            "total_providers": len(data),
                            "healthy_providers": healthy_count,
                            "details": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_cache_health(self) -> Dict[str, Any]:
        """Check cache health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health/cache") as response:
                    if response.status == 200:
                        data = await response.json()
                        cache_usage = data.get("memory_usage_mb", 0)
                        max_cache = data.get("max_memory_mb", 1024)

                        status = "healthy"
                        if cache_usage > max_cache * 0.9:
                            status = "warning"
                        elif cache_usage > max_cache * 0.95:
                            status = "critical"

                        return {
                            "status": status,
                            "memory_usage_mb": cache_usage,
                            "max_memory_mb": max_cache,
                            "hit_rate": data.get("hit_rate", 0),
                            "entries": data.get("entries", 0)
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def check_system_health(self) -> Dict[str, Any]:
        """Check system health"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network I/O
            network = psutil.net_io_counters()
            network_errors = network.errin + network.errout

            # Determine status
            status = "healthy"
            if cpu_percent > 80 or memory_percent > 85 or disk_percent > 90:
                status = "warning"
            if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
                status = "critical"

            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network_errors": network_errors,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# Usage
async def main():
    checker = HealthChecker()
    health = await checker.run_comprehensive_health_check()
    print(json.dumps(health, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

#### Health Check Endpoints

```python
# health_endpoints.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import psutil

router = APIRouter()

@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe - basic service availability"""
    return {"status": "alive", "timestamp": time.time()}

@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe - service readiness"""
    # Check if service can accept traffic
    try:
        # Basic connectivity check
        return {"status": "ready", "timestamp": time.time()}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with all components"""
    health_checker = HealthChecker()
    return await health_checker.run_comprehensive_health_check()

@router.get("/health/quick")
async def quick_health():
    """Quick health check for monitoring"""
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)

    status = "healthy"
    if memory.percent > 90 or cpu > 90:
        status = "degraded"
    if memory.percent > 95 or cpu > 95:
        status = "unhealthy"

    return {
        "status": status,
        "memory_percent": memory.percent,
        "cpu_percent": cpu,
        "timestamp": time.time()
    }
```

---

## Backup and Recovery Procedures

### Backup Strategy

#### Configuration Backup

```bash
#!/bin/bash
# backup_config.sh

BACKUP_DIR="/opt/proxyapi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    config.yaml \
    .env \
    docker-compose.yml \
    systemd service files

# Backup logs (compressed)
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Create backup manifest
cat > $BACKUP_DIR/backup_$DATE.manifest << EOF
Backup Date: $(date)
Backup Type: Configuration
Files:
$(tar -tzf $BACKUP_DIR/config_$DATE.tar.gz)
Log Files:
$(tar -tzf $BACKUP_DIR/logs_$DATE.tar.gz)
EOF

# Cleanup old backups
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "logs_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup_*.manifest" -mtime +$RETENTION_DAYS -delete

echo "Configuration backup completed: $BACKUP_DIR/config_$DATE.tar.gz"
```

#### Database Backup

```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/opt/proxyapi/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL backup
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    -F c \
    -f $BACKUP_DIR/database_$DATE.dump

# Compress backup
gzip $BACKUP_DIR/database_$DATE.dump

# Verify backup
if [ $? -eq 0 ]; then
    echo "Database backup completed: $BACKUP_DIR/database_$DATE.dump.gz"

    # Create verification script
    cat > $BACKUP_DIR/verify_$DATE.sh << EOF
#!/bin/bash
gunzip -c $BACKUP_DIR/database_$DATE.dump.gz | head -20
echo "Backup verification completed"
EOF
    chmod +x $BACKUP_DIR/verify_$DATE.sh
else
    echo "Database backup failed!"
    exit 1
fi

# Cleanup old backups
find $BACKUP_DIR -name "database_*.dump.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "verify_*.sh" -mtime +$RETENTION_DAYS -delete

# Backup rotation
BACKUP_COUNT=$(ls $BACKUP_DIR/database_*.dump.gz 2>/dev/null | wc -l)
if [ $BACKUP_COUNT -gt 10 ]; then
    ls $BACKUP_DIR/database_*.dump.gz | head -n -$((10)) | xargs rm -f
fi
```

#### Cache Backup

```bash
#!/bin/bash
# backup_cache.sh

BACKUP_DIR="/opt/proxyapi/backups/cache"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop cache warming during backup
curl -X POST http://localhost:8000/api/cache/pause-warming

# Export cache data
curl http://localhost:8000/api/cache/export > $BACKUP_DIR/cache_$DATE.json

# Compress cache backup
gzip $BACKUP_DIR/cache_$DATE.json

# Resume cache warming
curl -X POST http://localhost:8000/api/cache/resume-warming

# Verify backup
CACHE_SIZE=$(stat -c%s $BACKUP_DIR/cache_$DATE.json.gz 2>/dev/null || echo 0)
if [ $CACHE_SIZE -gt 0 ]; then
    echo "Cache backup completed: $BACKUP_DIR/cache_$DATE.json.gz (${CACHE_SIZE} bytes)"
else
    echo "Cache backup failed or empty!"
fi

# Cleanup old cache backups (keep last 7 days)
find $BACKUP_DIR -name "cache_*.json.gz" -mtime +7 -delete
```

### Recovery Procedures

#### Configuration Recovery

```bash
#!/bin/bash
# restore_config.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la /opt/proxyapi/backups/config_*.tar.gz
    exit 1
fi

# Create restore point
mkdir -p /opt/proxyapi/restore/$(date +%Y%m%d_%H%M%S)
cp -r /opt/proxyapi/config /opt/proxyapi/restore/$(date +%Y%m%d_%H%M%S)/

# Stop service
sudo systemctl stop llm-proxy

# Extract backup
tar -xzf $BACKUP_FILE -C /

# Validate configuration
python3 -c "
import yaml
try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print('✅ Configuration is valid')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"

# Restart service
sudo systemctl start llm-proxy

# Verify service
sleep 10
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Configuration restore completed successfully"
else
    echo "❌ Service failed to start after restore"
    exit 1
fi
```

#### Database Recovery

```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la /opt/proxyapi/backups/database/database_*.dump.gz
    exit 1
fi

# Stop application
sudo systemctl stop llm-proxy

# Create database dump of current state
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    -f /tmp/pre_restore_$(date +%Y%m%d_%H%M%S).sql

# Drop and recreate database
PGPASSWORD=$DB_PASSWORD psql \
    -h $DB_HOST \
    -U $DB_USER \
    -d postgres \
    -c "DROP DATABASE IF EXISTS $DB_NAME;"

PGPASSWORD=$DB_PASSWORD psql \
    -h $DB_HOST \
    -U $DB_USER \
    -d postgres \
    -c "CREATE DATABASE $DB_NAME;"

# Restore from backup
gunzip -c $BACKUP_FILE | PGPASSWORD=$DB_PASSWORD pg_restore \
    -h $DB_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    -v

# Verify restore
PGPASSWORD=$DB_PASSWORD psql \
    -h $DB_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    -c "SELECT COUNT(*) FROM information_schema.tables;" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Database restore completed successfully"
    # Start application
    sudo systemctl start llm-proxy
else
    echo "❌ Database restore failed"
    exit 1
fi
```

#### Emergency Recovery

```bash
#!/bin/bash
# emergency_recovery.sh

echo "=== Emergency Recovery Procedure ==="

# 1. Stop all services
echo "Stopping services..."
sudo systemctl stop llm-proxy
docker-compose down

# 2. Check system resources
echo "Checking system resources..."
free -h
df -h

# 3. Clear temporary files
echo "Clearing temporary files..."
rm -rf /tmp/proxyapi_*
find /opt/proxyapi/cache -name "*.tmp" -delete

# 4. Restore from latest clean backup
LATEST_CONFIG=$(ls -t /opt/proxyapi/backups/config_*.tar.gz | head -1)
LATEST_DB=$(ls -t /opt/proxyapi/backups/database/database_*.dump.gz | head -1)

if [ -n "$LATEST_CONFIG" ]; then
    echo "Restoring configuration from: $LATEST_CONFIG"
    ./restore_config.sh $LATEST_CONFIG
fi

if [ -n "$LATEST_DB" ]; then
    echo "Restoring database from: $LATEST_DB"
    ./restore_database.sh $LATEST_DB
fi

# 5. Reset cache
echo "Resetting cache..."
curl -X DELETE http://localhost:8000/api/cache

# 6. Start services with minimal configuration
echo "Starting services..."
sudo systemctl start llm-proxy

# 7. Monitor startup
echo "Monitoring startup..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Service started successfully"
        break
    fi
    sleep 2
done

if [ $i -eq 30 ]; then
    echo "❌ Service failed to start"
    exit 1
fi

echo "=== Emergency Recovery Complete ==="
```

### Backup Verification

```bash
#!/bin/bash
# verify_backups.sh

BACKUP_DIR="/opt/proxyapi/backups"
REPORT_FILE="/opt/proxyapi/reports/backup_verification_$(date +%Y%m%d).txt"

echo "=== Backup Verification Report ===" > $REPORT_FILE
echo "Generated: $(date)" >> $REPORT_FILE
echo >> $REPORT_FILE

# Check configuration backups
echo "Configuration Backups:" >> $REPORT_FILE
ls -la $BACKUP_DIR/config_*.tar.gz >> $REPORT_FILE
echo >> $REPORT_FILE

# Verify latest configuration backup
LATEST_CONFIG=$(ls -t $BACKUP_DIR/config_*.tar.gz | head -1)
if [ -n "$LATEST_CONFIG" ]; then
    echo "Verifying latest configuration backup: $LATEST_CONFIG" >> $REPORT_FILE
    tar -tzf $LATEST_CONFIG > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Configuration backup is valid" >> $REPORT_FILE
    else
        echo "❌ Configuration backup is corrupted" >> $REPORT_FILE
    fi
fi

# Check database backups
echo "Database Backups:" >> $REPORT_FILE
ls -la $BACKUP_DIR/database/database_*.dump.gz >> $REPORT_FILE
echo >> $REPORT_FILE

# Verify latest database backup
LATEST_DB=$(ls -t $BACKUP_DIR/database/database_*.dump.gz | head -1)
if [ -n "$LATEST_DB" ]; then
    echo "Verifying latest database backup: $LATEST_DB" >> $REPORT_FILE
    gunzip -c $LATEST_DB | head -10 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Database backup is valid" >> $REPORT_FILE
    else
        echo "❌ Database backup is corrupted" >> $REPORT_FILE
    fi
fi

# Check backup sizes and ages
echo "Backup Statistics:" >> $REPORT_FILE
echo "Total configuration backups: $(ls $BACKUP_DIR/config_*.tar.gz 2>/dev/null | wc -l)" >> $REPORT_FILE
echo "Total database backups: $(ls $BACKUP_DIR/database/database_*.dump.gz 2>/dev/null | wc -l)" >> $REPORT_FILE

# Check for old backups
OLD_CONFIGS=$(find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 2>/dev/null | wc -l)
OLD_DBS=$(find $BACKUP_DIR/database -name "database_*.dump.gz" -mtime +30 2>/dev/null | wc -l)

if [ $OLD_CONFIGS -gt 0 ]; then
    echo "⚠️  Found $OLD_CONFIGS configuration backups older than 30 days" >> $REPORT_FILE
fi

if [ $OLD_DBS -gt 0 ]; then
    echo "⚠️  Found $OLD_DBS database backups older than 30 days" >> $REPORT_FILE
fi

echo >> $REPORT_FILE
echo "=== End Report ===" >> $REPORT_FILE

echo "Backup verification report generated: $REPORT_FILE"
```

---

## System Monitoring Best Practices

### Monitoring Architecture

#### Metrics Collection

```yaml
# monitoring_config.yaml
monitoring:
  enabled: true
  collection_interval: 30
  retention_days: 30

  exporters:
    - type: "prometheus"
      port: 9090
      path: "/metrics"
      labels:
        environment: "production"
        region: "us-east-1"

    - type: "json"
      endpoint: "/metrics/json"
      pretty_print: true

  metrics:
    # Application metrics
    application:
      enabled: true
      request_count: true
      response_time: true
      error_rate: true
      throughput: true

    # System metrics
    system:
      enabled: true
      cpu_usage: true
      memory_usage: true
      disk_usage: true
      network_io: true

    # Provider metrics
    providers:
      enabled: true
      request_count: true
      error_rate: true
      response_time: true
      token_usage: true

    # Cache metrics
    cache:
      enabled: true
      hit_rate: true
      memory_usage: true
      eviction_count: true
      warming_stats: true

    # Security metrics
    security:
      enabled: true
      auth_attempts: true
      failed_auth: true
      rate_limit_hits: true
      suspicious_activity: true
```

#### Alerting Configuration

```yaml
# alerting_config.yaml
alerting:
  enabled: true
  alertmanager_url: "http://alertmanager:9093"

  rules:
    # Critical alerts
    - name: "service_down"
      condition: "up{job='proxyapi'} == 0"
      severity: "critical"
      duration: "2m"
      description: "ProxyAPI service is down"
      channels: ["pagerduty", "slack", "email"]

    - name: "high_error_rate"
      condition: "rate(http_requests_total{status=~'5..'} [5m]) / rate(http_requests_total[5m]) > 0.05"
      severity: "critical"
      duration: "5m"
      description: "Error rate above 5%"
      channels: ["slack", "email"]

    # Warning alerts
    - name: "high_latency"
      condition: "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5"
      severity: "warning"
      duration: "5m"
      description: "95th percentile latency above 5 seconds"
      channels: ["slack"]

    - name: "high_memory_usage"
      condition: "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.85"
      severity: "warning"
      duration: "5m"
      description: "Memory usage above 85%"
      channels: ["slack"]

    - name: "low_cache_hit_rate"
      condition: "cache_hit_rate < 0.7"
      severity: "warning"
      duration: "10m"
      description: "Cache hit rate below 70%"
      channels: ["slack"]

    # Info alerts
    - name: "rate_limit_approaching"
      condition: "rate_limit_remaining < 100"
      severity: "info"
      duration: "1m"
      description: "Rate limit remaining below 100"
      channels: ["slack"]
```

### Dashboard Configuration

#### Grafana Dashboard Setup

```json
{
  "dashboard": {
    "title": "ProxyAPI Production Monitoring",
    "tags": ["proxyapi", "production"],
    "timezone": "UTC",
    "panels": [
      {
        "title": "Request Rate & Success Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Total Requests/sec"
          },
          {
            "expr": "rate(http_requests_total{status!~'5..'} [5m])",
            "legendFormat": "Successful Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time Percentiles",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "Error Rate by Type",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~'4..'} [5m])) by (status)",
            "legendFormat": "{{status}}"
          },
          {
            "expr": "sum(rate(http_requests_total{status=~'5..'} [5m])) by (status)",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "legendFormat": "Memory Usage %"
          },
          {
            "expr": "(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100",
            "legendFormat": "Disk Usage %"
          }
        ]
      },
      {
        "title": "Cache Performance",
        "type": "stat",
        "targets": [
          {
            "expr": "cache_hit_rate * 100",
            "legendFormat": "Hit Rate %"
          }
        ],
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"value": null, "color": "red"},
            {"value": 70, "color": "yellow"},
            {"value": 80, "color": "green"}
          ]
        }
      },
      {
        "title": "Provider Health",
        "type": "table",
        "targets": [
          {
            "expr": "rate(provider_requests_total[5m])",
            "legendFormat": "{{provider}} requests/sec"
          },
          {
            "expr": "rate(provider_errors_total[5m]) / rate(provider_requests_total[5m]) * 100",
            "legendFormat": "{{provider}} error rate %"
          }
        ]
      }
    ]
  }
}
```

#### Monitoring Best Practices

1. **Define Key Metrics**
   - Focus on business-critical metrics (request rate, success rate, latency)
   - Monitor system resources (CPU, memory, disk, network)
   - Track provider performance and errors
   - Monitor cache efficiency and security events

2. **Set Appropriate Alert Thresholds**
   - Use historical data to set realistic thresholds
   - Implement multiple severity levels (info, warning, critical)
   - Configure alert cooldown periods to prevent alert fatigue
   - Test alerts regularly to ensure they work

3. **Implement Alert Escalation**
   ```yaml
   alert_escalation:
     enabled: true
     levels:
       - name: "first_response"
         delay: "5m"
         channels: ["slack"]
       - name: "escalation"
         delay: "15m"
         channels: ["pagerduty", "sms"]
       - name: "critical"
         delay: "30m"
         channels: ["phone", "management"]
   ```

4. **Monitor Alert Effectiveness**
   - Track mean time to detection (MTTD)
   - Track mean time to resolution (MTTR)
   - Review false positive rates
   - Regularly update alert rules based on learnings

5. **Implement Alert Grouping and Inhibition**
   ```yaml
   alert_grouping:
     enabled: true
     group_by: ["alertname", "severity", "provider"]
     group_wait: "30s"
     group_interval: "5m"

   alert_inhibition:
     enabled: true
     rules:
       - source_match:
           alertname: "high_cpu_usage"
         target_match:
           alertname: "high_response_time"
         equal: ["instance"]
   ```

6. **Dashboard Organization**
   - Group related metrics together
   - Use consistent color schemes and thresholds
   - Include trend indicators and comparisons
   - Add contextual information and annotations

7. **Historical Analysis**
   - Store metrics for trend analysis
   - Implement anomaly detection
   - Generate weekly/monthly performance reports
   - Use metrics for capacity planning

---

## Diagnostic Scripts and Maintenance Checklists

### Diagnostic Scripts

#### System Diagnostic Script

```bash
#!/bin/bash
# system_diagnostic.sh

OUTPUT_FILE="/opt/proxyapi/reports/system_diagnostic_$(date +%Y%m%d_%H%M%S).txt"

echo "=== System Diagnostic Report ===" > $OUTPUT_FILE
echo "Generated: $(date)" >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# System Information
echo "System Information:" >> $OUTPUT_FILE
uname -a >> $OUTPUT_FILE
lsb_release -a >> $OUTPUT_FILE 2>/dev/null || echo "LSB release not available" >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# CPU Information
echo "CPU Information:" >> $OUTPUT_FILE
lscpu >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# Memory Information
echo "Memory Information:" >> $OUTPUT_FILE
free -h >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# Disk Information
echo "Disk Information:" >> $OUTPUT_FILE
df -h >> $OUTPUT_FILE
lsblk >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# Network Information
echo "Network Information:" >> $OUTPUT_FILE
ip addr show >> $OUTPUT_FILE
ip route show >> $OUTPUT_FILE
netstat -tlnp >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# Process Information
echo "Process Information:" >> $OUTPUT_FILE
ps aux --sort=-%cpu | head -20 >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# Service Status
echo "Service Status:" >> $OUTPUT_FILE
systemctl status llm-proxy --no-pager >> $OUTPUT_FILE 2>&1
docker ps >> $OUTPUT_FILE 2>&1
echo >> $OUTPUT_FILE

# Log File Analysis
echo "Log File Analysis:" >> $OUTPUT_FILE
echo "Log files in /opt/proxyapi/logs/:" >> $OUTPUT_FILE
ls -la /opt/proxyapi/logs/ >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

echo "Recent errors in logs:" >> $OUTPUT_FILE
grep -h "ERROR" /opt/proxyapi/logs/*.log | tail -10 >> $OUTPUT_FILE 2>/dev/null || echo "No recent errors" >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

# Configuration Validation
echo "Configuration Validation:" >> $OUTPUT_FILE
if [ -f "/opt/proxyapi/config.yaml" ]; then
    python3 -c "
import yaml
try:
    with open('/opt/proxyapi/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print('✅ Configuration file is valid YAML')
    print(f'Providers configured: {len(config.get(\"providers\", []))}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
" >> $OUTPUT_FILE
else
    echo "❌ Configuration file not found" >> $OUTPUT_FILE
fi
echo >> $OUTPUT_FILE

# API Health Check
echo "API Health Check:" >> $OUTPUT_FILE
curl -s http://localhost:8000/health >> $OUTPUT_FILE 2>&1 || echo "❌ API health check failed" >> $OUTPUT_FILE
echo >> $OUTPUT_FILE

echo "=== End System Diagnostic Report ===" >> $OUTPUT_FILE

echo "System diagnostic report generated: $OUTPUT_FILE"
```

#### Performance Diagnostic Script

```python
#!/usr/bin/env python3
# performance_diagnostic.py

import asyncio
import aiohttp
import time
import statistics
from typing import Dict, List, Any
import json

class PerformanceDiagnostic:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}

    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive performance diagnostics"""
        print("Running performance diagnostics...")

        # API endpoint response times
        endpoint_times = await self.test_endpoint_performance()

        # Concurrent request handling
        concurrency_results = await self.test_concurrency()

        # Memory usage during load
        memory_results = await self.test_memory_usage()

        # Cache performance
        cache_results = await self.test_cache_performance()

        self.results = {
            "timestamp": time.time(),
            "endpoint_performance": endpoint_times,
            "concurrency_test": concurrency_results,
            "memory_test": memory_results,
            "cache_test": cache_results,
            "recommendations": self.generate_recommendations()
        }

        return self.results

    async def test_endpoint_performance(self) -> Dict[str, Any]:
        """Test API endpoint response times"""
        endpoints = [
            "/health",
            "/api/models",
            "/metrics"
        ]

        results = {}

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                times = []
                for _ in range(10):  # 10 requests per endpoint
                    start_time = time.time()
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            await response.text()
                            end_time = time.time()
                            times.append(end_time - start_time)
                    except Exception as e:
                        print(f"Error testing {endpoint}: {e}")
                        continue

                if times:
                    results[endpoint] = {
                        "min_time": min(times),
                        "max_time": max(times),
                        "avg_time": statistics.mean(times),
                        "p95_time": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                        "requests": len(times)
                    }

        return results

    async def test_concurrency(self) -> Dict[str, Any]:
        """Test concurrent request handling"""
        async def make_request(session, request_id):
            start_time = time.time()
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    await response.text()
                    return time.time() - start_time
            except Exception as e:
                print(f"Request {request_id} failed: {e}")
                return None

        concurrency_levels = [10, 50, 100, 200]

        results = {}

        for concurrency in concurrency_levels:
            print(f"Testing concurrency level: {concurrency}")
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, i) for i in range(concurrency)]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()

            successful_responses = [r for r in responses if r is not None and not isinstance(r, Exception)]
            failed_responses = len([r for r in responses if r is None or isinstance(r, Exception)])

            if successful_responses:
                results[f"concurrency_{concurrency}"] = {
                    "total_time": end_time - start_time,
                    "successful_requests": len(successful_responses),
                    "failed_requests": failed_responses,
                    "avg_response_time": statistics.mean(successful_responses),
                    "min_response_time": min(successful_responses),
                    "max_response_time": max(successful_responses),
                    "requests_per_second": len(successful_responses) / (end_time - start_time)
                }

        return results

    async def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage during load"""
        # Note: This would require integration with memory profiling tools
        # For now, return basic memory metrics
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    memory_data = await response.json()
                    return memory_data.get("memory", {})
        except Exception as e:
            return {"error": str(e)}

    async def test_cache_performance(self) -> Dict[str, Any]:
        """Test cache performance"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics/cache") as response:
                    cache_data = await response.json()
                    return cache_data
        except Exception as e:
            return {"error": str(e)}

    def generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Analyze endpoint performance
        endpoint_perf = self.results.get("endpoint_performance", {})
        for endpoint, metrics in endpoint_perf.items():
            if metrics.get("avg_time", 0) > 1.0:
                recommendations.append(f"Optimize {endpoint} - average response time is {metrics['avg_time']:.2f}s")

        # Analyze concurrency
        concurrency_results = self.results.get("concurrency_test", {})
        for level, metrics in concurrency_results.items():
            if metrics.get("failed_requests", 0) > 0:
                recommendations.append(f"Improve concurrency handling - {metrics['failed_requests']} failed requests at {level}")

        return recommendations

async def main():
    diagnostic = PerformanceDiagnostic()
    results = await diagnostic.run_diagnostics()

    # Save results
    with open(f"performance_diagnostic_{int(time.time())}.json", 'w') as f:
        json.dump(results, f, indent=2)

    print("Performance diagnostic completed")
    print("Results saved to performance_diagnostic_*.json")

if __name__ == "__main__":
    asyncio.run(main())
```

#### Security Diagnostic Script

```python
#!/usr/bin/env python3
# security_diagnostic.py

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any
import re

class SecurityDiagnostic:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def run_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        print("Running security diagnostic...")

        results = {
            "timestamp": time.time(),
            "checks": {}
        }

        # Authentication tests
        results["checks"]["authentication"] = await self.test_authentication()

        # Authorization tests
        results["checks"]["authorization"] = await self.test_authorization()

        # Input validation tests
        results["checks"]["input_validation"] = await self.test_input_validation()

        # Rate limiting tests
        results["checks"]["rate_limiting"] = await self.test_rate_limiting()

        # Security headers
        results["checks"]["security_headers"] = await self.test_security_headers()

        # Log analysis
        results["checks"]["log_analysis"] = await self.analyze_security_logs()

        results["summary"] = self.generate_security_summary(results["checks"])

        return results

    async def test_authentication(self) -> Dict[str, Any]:
        """Test authentication mechanisms"""
        tests = {
            "invalid_api_key": False,
            "missing_auth_header": False,
            "malformed_auth_header": False,
            "timing_attack_resistance": False
        }

        async with aiohttp.ClientSession() as session:
            # Test invalid API key
            try:
                async with session.get(f"{self.base_url}/api/models",
                                     headers={"Authorization": "Bearer invalid_key"}) as response:
                    tests["invalid_api_key"] = response.status == 401
            except:
                pass

            # Test missing auth header
            try:
                async with session.get(f"{self.base_url}/api/models") as response:
                    tests["missing_auth_header"] = response.status == 401
            except:
                pass

            # Test malformed auth header
            try:
                async with session.get(f"{self.base_url}/api/models",
                                     headers={"Authorization": "Invalid format"}) as response:
                    tests["malformed_auth_header"] = response.status == 401
            except:
                pass

        return {
            "tests": tests,
            "passed": sum(tests.values()),
            "total": len(tests),
            "score": sum(tests.values()) / len(tests) * 100
        }

    async def test_authorization(self) -> Dict[str, Any]:
        """Test authorization mechanisms"""
        tests = {
            "role_based_access": False,
            "resource_permissions": False,
            "admin_restrictions": False
        }

        # These would require valid API keys with different permissions
        # Implementation depends on specific authorization system

        return {
            "tests": tests,
            "passed": sum(tests.values()),
            "total": len(tests),
            "score": sum(tests.values()) / len(tests) * 100
        }

    async def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation"""
        tests = {
            "sql_injection_prevention": False,
            "xss_prevention": False,
            "command_injection_prevention": False,
            "path_traversal_prevention": False
        }

        dangerous_payloads = [
            {"content": "' OR '1'='1", "type": "sql"},
            {"content": "<script>alert('xss')</script>", "type": "xss"},
            {"content": "; rm -rf /", "type": "command"},
            {"content": "../../../etc/passwd", "type": "path"}
        ]

        async with aiohttp.ClientSession() as session:
            for payload in dangerous_payloads:
                try:
                    data = {
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": payload["content"]}]
                    }

                    async with session.post(f"{self.base_url}/v1/chat/completions",
                                          json=data,
                                          headers={"Authorization": "Bearer test_key"}) as response:

                        if payload["type"] == "sql":
                            tests["sql_injection_prevention"] = response.status in [400, 422]
                        elif payload["type"] == "xss":
                            tests["xss_prevention"] = response.status in [400, 422]
                        elif payload["type"] == "command":
                            tests["command_injection_prevention"] = response.status in [400, 422]
                        elif payload["type"] == "path":
                            tests["path_traversal_prevention"] = response.status in [400, 422]

                except Exception as e:
                    print(f"Input validation test failed: {e}")

        return {
            "tests": tests,
            "passed": sum(tests.values()),
            "total": len(tests),
            "score": sum(tests.values()) / len(tests) * 100
        }

    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting effectiveness"""
        tests = {
            "rate_limit_enforced": False,
            "burst_limit_enforced": False,
            "rate_limit_headers": False
        }

        # Test rapid requests
        async with aiohttp.ClientSession() as session:
            for i in range(150):  # More than typical rate limit
                try:
                    async with session.get(f"{self.base_url}/api/models",
                                         headers={"Authorization": "Bearer test_key"}) as response:
                        if response.status == 429:
                            tests["rate_limit_enforced"] = True
                            break
                except:
                    pass

        return {
            "tests": tests,
            "passed": sum(tests.values()),
            "total": len(tests),
            "score": sum(tests.values()) / len(tests) * 100
        }

    async def test_security_headers(self) -> Dict[str, Any]:
        """Test security headers"""
        tests = {
            "https_enforced": False,
            "hsts_header": False,
            "csp_header": False,
            "x_frame_options": False,
            "x_content_type_options": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    headers = response.headers

                    tests["hsts_header"] = "Strict-Transport-Security" in headers
                    tests["csp_header"] = "Content-Security-Policy" in headers
                    tests["x_frame_options"] = "X-Frame-Options" in headers
                    tests["x_content_type_options"] = "X-Content-Type-Options" in headers

                    # Check if HTTPS is enforced (redirect to HTTPS)
                    if response.status in [301, 302] and "https://" in response.headers.get("Location", ""):
                        tests["https_enforced"] = True

        except Exception as e:
            print(f"Security headers test failed: {e}")

        return {
            "tests": tests,
            "passed": sum(tests.values()),
            "total": len(tests),
            "score": sum(tests.values()) / len(tests) * 100
        }

    async def analyze_security_logs(self) -> Dict[str, Any]:
        """Analyze security-related log entries"""
        # This would require access to log files
        # For demonstration, return placeholder
        return {
            "total_security_events": 0,
            "auth_failures": 0,
            "suspicious_activity": 0,
            "rate_limit_hits": 0,
            "recommendations": []
        }

    def generate_security_summary(self, checks: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security audit summary"""
        total_score = 0
        total_tests = 0

        for check_name, check_data in checks.items():
            if "score" in check_data:
                total_score += check_data["score"]
                total_tests += 1

        overall_score = total_score / total_tests if total_tests > 0 else 0

        recommendations = []
        if overall_score < 80:
            recommendations.append("Security score below 80% - immediate attention required")
        if overall_score < 90:
            recommendations.append("Consider implementing additional security measures")

        return {
            "overall_score": overall_score,
            "total_checks": len(checks),
            "recommendations": recommendations
        }

async def main():
    diagnostic = SecurityDiagnostic()
    results = await diagnostic.run_security_audit()

    # Save results
    with open(f"security_diagnostic_{int(time.time())}.json", 'w') as f:
        json.dump(results, f, indent=2)

    print("Security diagnostic completed")
    print(f"Overall security score: {results['summary']['overall_score']:.1f}%")
    print("Results saved to security_diagnostic_*.json")

if __name__ == "__main__":
    asyncio.run(main())
```

### Maintenance Checklists

#### Daily Maintenance Checklist

```markdown
# Daily Maintenance Checklist

## Morning Checks (9:00 AM)
- [ ] Verify service is running: `systemctl status llm-proxy`
- [ ]