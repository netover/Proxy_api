# 📝 Logging Guide - LLM Proxy API

Comprehensive guide to logging, log analysis, and log management in the LLM Proxy API.

## Table of Contents

- [Overview](#overview)
- [Logging Architecture](#logging-architecture)
- [Log Levels and Configuration](#log-levels-and-configuration)
- [Structured Logging](#structured-logging)
- [Log Analysis and Processing](#log-analysis-and-processing)
- [Log Storage and Rotation](#log-storage-and-rotation)
- [Log Monitoring and Alerting](#log-monitoring-and-alerting)
- [Performance Logging](#performance-logging)
- [Security Logging](#security-logging)
- [Troubleshooting with Logs](#troubleshooting-with-logs)
- [Best Practices](#best-practices)

## Overview

The LLM Proxy API implements comprehensive logging capabilities designed for production environments, debugging, and compliance requirements. The logging system provides structured, searchable logs with configurable levels, formats, and destinations.

### Key Features

- **Structured Logging**: JSON-formatted logs with consistent schema
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Configurable Outputs**: File, console, external systems
- **Log Rotation**: Automatic log rotation and cleanup
- **Performance Optimized**: Minimal performance impact
- **Security Focused**: Audit trails and security event logging
- **Searchable**: Easy log analysis and filtering

### Logging Coverage

- **Application Logs**: Request/response cycles, errors, warnings
- **Performance Logs**: Response times, throughput, resource usage
- **Security Logs**: Authentication, authorization, suspicious activities
- **Audit Logs**: Configuration changes, admin actions
- **Debug Logs**: Detailed debugging information
- **System Logs**: Infrastructure and system-level events

## Logging Architecture

### Core Logging Components

```
┌─────────────────┐
│   Application   │
└─────────────────┘
         │
    ┌────────────┐
    │ Loggers    │ ← ContextualLogger, PerformanceLogger
    └────────────┘
         │
    ┌────┴────┐
    │         │
┌───┴───┐ ┌───┴───┐
│Handlers│ │Filters │
│        │ │       │
│ File   │ │ Level │
│ Console│ │ Module│
│ Syslog │ │ Content│
└────────┘ └───────┘
         │
    ┌────┴────┐
    │ Formatters│
    │          │
    │ JSON     │
    │ Text     │
    │ Custom   │
    └─────────┘
```

#### Core Components

1. **ContextualLogger**: Enhanced logger with context and structured data
2. **PerformanceLogger**: Specialized logger for performance metrics
3. **SecurityLogger**: Dedicated logger for security events
4. **AuditLogger**: Logger for audit trails and compliance
5. **LogProcessor**: Background log processing and analysis

### Logger Hierarchy

```python
# Logger hierarchy
root_logger = logging.getLogger()           # Root logger
app_logger = logging.getLogger('llm_proxy') # Application logger
api_logger = logging.getLogger('llm_proxy.api')     # API logger
cache_logger = logging.getLogger('llm_proxy.cache') # Cache logger
provider_logger = logging.getLogger('llm_proxy.provider') # Provider logger
```

## Log Levels and Configuration

### Log Levels

| Level | Numeric Value | Description | Use Case |
|-------|---------------|-------------|----------|
| DEBUG | 10 | Detailed debugging information | Development, troubleshooting |
| INFO | 20 | General information about application operation | Normal operations |
| WARNING | 30 | Warning messages for potential issues | Non-critical issues |
| ERROR | 40 | Error messages for failures | Application errors |
| CRITICAL | 50 | Critical errors requiring immediate attention | System failures |

### Configuration

```yaml
logging:
  # Basic configuration
  level: "INFO"
  format: "json"
  file: "logs/llm_proxy.log"
  max_file_size: "100MB"
  max_files: 5

  # Logger-specific levels
  loggers:
    llm_proxy.api: "DEBUG"
    llm_proxy.cache: "WARNING"
    llm_proxy.provider: "INFO"

  # Output destinations
  handlers:
    - type: "file"
      level: "INFO"
      format: "json"
      file: "logs/llm_proxy.log"
    - type: "console"
      level: "WARNING"
      format: "text"
    - type: "syslog"
      level: "ERROR"
      address: "localhost:514"

  # Advanced settings
  rotation: "daily"
  compression: "gzip"
  encoding: "utf-8"
  buffer_size: 8192
```

### Dynamic Log Level Configuration

```python
# Dynamic log level changes
from src.core.logging import set_log_level

# Change root logger level
set_log_level("DEBUG")

# Change specific logger level
set_log_level("INFO", logger_name="llm_proxy.api")

# Change level for specific module
set_log_level("WARNING", module="src.core.cache")
```

## Structured Logging

### JSON Log Format

```json
{
  "timestamp": "2024-01-15T10:30:15.123Z",
  "level": "INFO",
  "logger": "llm_proxy.api",
  "module": "src.api.endpoints",
  "function": "chat_completion",
  "line": 45,
  "message": "Chat completion request processed",
  "request_id": "req_1234567890",
  "user_id": "user_987654321",
  "provider": "openai",
  "model": "gpt-4",
  "tokens": 150,
  "response_time_ms": 245.67,
  "status_code": 200,
  "ip_address": "192.168.1.100",
  "user_agent": "LLM-Client/1.0",
  "trace_id": "trace_abcdef123456",
  "span_id": "span_789012345",
  "extra_data": {
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": false
  }
}
```

### Log Context Management

```python
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

# Automatic context capture
async def handle_request(request):
    with logger.context(
        request_id=request.headers.get('X-Request-ID'),
        user_id=get_user_id(request),
        trace_id=get_trace_id(request)
    ):
        logger.info("Processing request", extra={
            'endpoint': request.url.path,
            'method': request.method,
            'ip': request.client.host
        })

        # All log messages in this context will include
        # request_id, user_id, and trace_id automatically
        result = await process_request(request)

        logger.info("Request completed", extra={
            'response_time_ms': result.response_time,
            'status_code': result.status_code,
            'tokens_used': result.tokens
        })

        return result
```

### Custom Log Fields

```python
# Custom log fields for different components
API_LOG_FIELDS = {
    'request_id': str,
    'user_id': str,
    'endpoint': str,
    'method': str,
    'status_code': int,
    'response_time_ms': float,
    'tokens_used': int,
    'provider': str,
    'model': str,
    'cost_usd': float
}

CACHE_LOG_FIELDS = {
    'cache_key': str,
    'cache_hit': bool,
    'cache_ttl': int,
    'memory_usage_mb': float,
    'entries_count': int,
    'hit_rate': float
}

PROVIDER_LOG_FIELDS = {
    'provider_name': str,
    'api_call': str,
    'request_size_bytes': int,
    'response_size_bytes': int,
    'rate_limit_remaining': int,
    'retry_count': int
}
```

## Log Analysis and Processing

### Log Processing Pipeline

```python
class LogProcessor:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.processors = [
            self.parse_json_logs,
            self.enrich_logs,
            self.filter_logs,
            self.aggregate_metrics,
            self.detect_anomalies
        ]

    async def process_logs(self):
        """Process logs in real-time"""
        async for log_entry in self.tail_logs():
            for processor in self.processors:
                try:
                    log_entry = await processor(log_entry)
                    if log_entry is None:  # Filtered out
                        break
                except Exception as e:
                    logger.error(f"Log processing error: {e}")
                    continue

            if log_entry:
                await self.store_processed_log(log_entry)

    async def tail_logs(self):
        """Tail log file and yield new entries"""
        with open(self.log_file, 'r') as f:
            f.seek(0, 2)  # Go to end of file

            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                try:
                    yield json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
```

### Log Enrichment

```python
async def enrich_logs(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich log entries with additional context"""

    # Add geo information
    if 'ip_address' in log_entry:
        geo_info = await self.get_geo_info(log_entry['ip_address'])
        log_entry['geo'] = geo_info

    # Add user information
    if 'user_id' in log_entry:
        user_info = await self.get_user_info(log_entry['user_id'])
        log_entry['user'] = user_info

    # Add performance context
    if 'response_time_ms' in log_entry:
        log_entry['performance_category'] = self.categorize_performance(
            log_entry['response_time_ms']
        )

    # Add business context
    if 'endpoint' in log_entry:
        log_entry['business_unit'] = self.get_business_unit(
            log_entry['endpoint']
        )

    return log_entry

def categorize_performance(self, response_time_ms: float) -> str:
    """Categorize response time performance"""
    if response_time_ms < 100:
        return "excellent"
    elif response_time_ms < 500:
        return "good"
    elif response_time_ms < 1000:
        return "acceptable"
    elif response_time_ms < 5000:
        return "slow"
    else:
        return "very_slow"
```

### Log Filtering and Search

```python
class LogFilter:
    def __init__(self, filters: Dict[str, Any]):
        self.filters = filters

    def matches(self, log_entry: Dict[str, Any]) -> bool:
        """Check if log entry matches filters"""
        for field, condition in self.filters.items():
            if field not in log_entry:
                return False

            value = log_entry[field]

            if isinstance(condition, dict):
                # Complex condition
                if not self.check_condition(value, condition):
                    return False
            else:
                # Simple equality
                if value != condition:
                    return False

        return True

    def check_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        """Check complex condition"""
        if 'operator' in condition:
            operator = condition['operator']
            target = condition.get('value')

            if operator == 'gt':
                return value > target
            elif operator == 'lt':
                return value < target
            elif operator == 'gte':
                return value >= target
            elif operator == 'lte':
                return value <= target
            elif operator == 'contains':
                return target in str(value)
            elif operator == 'regex':
                import re
                return re.search(target, str(value)) is not None

        return False

# Usage examples
error_filter = LogFilter({
    'level': 'ERROR',
    'response_time_ms': {'operator': 'gt', 'value': 5000}
})

slow_requests = LogFilter({
    'endpoint': '/api/chat/completions',
    'response_time_ms': {'operator': 'gt', 'value': 2000},
    'status_code': 200
})

security_filter = LogFilter({
    'level': 'WARNING',
    'message': {'operator': 'contains', 'value': 'unauthorized'}
})
```

## Log Storage and Rotation

### Log Rotation Strategies

```yaml
# Log rotation configuration
rotation:
  # Time-based rotation
  time_based:
    enabled: true
    when: "midnight"  # daily rotation
    interval: 1
    backup_count: 30

  # Size-based rotation
  size_based:
    enabled: true
    max_bytes: 104857600  # 100MB
    backup_count: 5

  # Hybrid rotation
  hybrid:
    enabled: false
    max_bytes: 52428800   # 50MB
    when: "W0"           # weekly
    backup_count: 12

  # Compression
  compression:
    enabled: true
    method: "gzip"
    level: 6
    compress_delay: 300   # Compress after 5 minutes

  # Cleanup
  cleanup:
    enabled: true
    max_age_days: 90
    min_free_space_gb: 10
```

### Log Storage Backends

```python
class LogStorage:
    def __init__(self, config):
        self.config = config
        self.backends = {
            'file': FileLogStorage(config.file_config),
            'elasticsearch': ElasticsearchStorage(config.es_config),
            's3': S3LogStorage(config.s3_config),
            'database': DatabaseLogStorage(config.db_config)
        }

    async def store_log(self, log_entry: Dict[str, Any]):
        """Store log entry to configured backends"""
        tasks = []

        for backend_name, backend in self.backends.items():
            if self.config.enabled_backends.get(backend_name, False):
                tasks.append(self._store_to_backend(backend, log_entry))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _store_to_backend(self, backend, log_entry):
        """Store to specific backend with error handling"""
        try:
            await backend.store(log_entry)
        except Exception as e:
            logger.error(f"Failed to store log to {backend.__class__.__name__}: {e}")

class ElasticsearchStorage:
    def __init__(self, config):
        self.config = config
        self.client = AsyncElasticsearch(
            hosts=config.hosts,
            basic_auth=(config.username, config.password)
        )

    async def store(self, log_entry: Dict[str, Any]):
        """Store log entry to Elasticsearch"""
        # Add timestamp for indexing
        log_entry['@timestamp'] = log_entry.get('timestamp')

        # Create index name with date
        date = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
        index_name = f"llm-proxy-logs-{date.strftime('%Y-%m-%d')}"

        await self.client.index(
            index=index_name,
            document=log_entry
        )
```

## Log Monitoring and Alerting

### Log-Based Alerting

```yaml
# Log monitoring configuration
log_monitoring:
  enabled: true

  # Alert rules
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

    - name: "provider_failures"
      pattern: '"provider": "\w+", "level": "ERROR"'
      threshold: 3
      window_minutes: 5
      severity: "warning"
      channels: ["devops"]

  # Monitoring settings
  monitoring:
    check_interval: 60
    max_memory_mb: 100
    persist_state: true
    state_file: "logs/monitoring_state.json"
```

### Real-time Log Analysis

```python
class LogAnalyzer:
    def __init__(self):
        self.patterns = {
            'errors': re.compile(r'"level": "(ERROR|CRITICAL)"'),
            'slow_requests': re.compile(r'"response_time_ms": (\d+)'),
            'security_events': re.compile(r'"level": "(WARNING|ERROR)".*"security"'),
            'rate_limits': re.compile(r'"rate_limit"'),
            'timeouts': re.compile(r'"timeout"')
        }

        self.counters = defaultdict(int)
        self.window_start = time.time()
        self.window_size = 300  # 5 minutes

    async def analyze_log(self, log_entry: Dict[str, Any]):
        """Analyze log entry in real-time"""
        current_time = time.time()

        # Reset counters if window expired
        if current_time - self.window_start > self.window_size:
            self.reset_counters()
            self.window_start = current_time

        # Analyze patterns
        log_str = json.dumps(log_entry)

        for pattern_name, pattern in self.patterns.items():
            if pattern.search(log_str):
                self.counters[pattern_name] += 1

                # Check thresholds
                threshold = self.get_threshold(pattern_name)
                if self.counters[pattern_name] >= threshold:
                    await self.trigger_alert(pattern_name, self.counters[pattern_name])

        # Analyze response times
        if 'response_time_ms' in log_entry:
            response_time = log_entry['response_time_ms']
            if response_time > 5000:
                self.counters['very_slow_requests'] += 1

    def get_threshold(self, pattern_name: str) -> int:
        """Get threshold for pattern"""
        thresholds = {
            'errors': 10,
            'slow_requests': 20,
            'security_events': 1,
            'rate_limits': 5,
            'timeouts': 3,
            'very_slow_requests': 5
        }
        return thresholds.get(pattern_name, 10)

    async def trigger_alert(self, pattern_name: str, count: int):
        """Trigger alert for pattern"""
        alert_message = f"High {pattern_name}: {count} in last 5 minutes"

        logger.warning(f"Alert triggered: {alert_message}")

        # Send to alerting system
        await self.send_alert(pattern_name, alert_message, count)

    def reset_counters(self):
        """Reset all counters"""
        self.counters.clear()
```

## Performance Logging

### Performance Log Format

```json
{
  "timestamp": "2024-01-15T10:30:15.123Z",
  "level": "INFO",
  "logger": "llm_proxy.performance",
  "request_id": "req_1234567890",
  "operation": "chat_completion",
  "start_time": "2024-01-15T10:30:15.000Z",
  "end_time": "2024-01-15T10:30:15.245Z",
  "duration_ms": 245.67,
  "cpu_time_ms": 89.12,
  "memory_delta_mb": 2.34,
  "io_operations": 15,
  "network_bytes_sent": 1024,
  "network_bytes_received": 2048,
  "cache_hits": 3,
  "cache_misses": 1,
  "db_queries": 2,
  "db_query_time_ms": 12.45,
  "external_api_calls": 1,
  "external_api_time_ms": 123.89,
  "success": true,
  "performance_category": "good"
}
```

### Performance Profiling

```python
import cProfile
import pstats
from io import StringIO

class PerformanceProfiler:
    def __init__(self):
        self.profiler = cProfile.Profile()

    def start_profiling(self):
        """Start performance profiling"""
        self.profiler.enable()

    def stop_profiling(self) -> str:
        """Stop profiling and return statistics"""
        self.profiler.disable()

        # Get statistics
        stats = pstats.Stats(self.profiler)
        stats.sort_stats('cumulative')

        # Format as string
        output = StringIO()
        stats.print_stats(20)  # Top 20 functions
        stats.dump_stats(output)

        return output.getvalue()

    async def profile_async_function(self, func, *args, **kwargs):
        """Profile an async function"""
        self.start_profiling()

        try:
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()

            profiling_stats = self.stop_profiling()

            # Log performance data
            logger.info("Function profiling completed", extra={
                'function_name': func.__name__,
                'execution_time_ms': (end_time - start_time) * 1000,
                'profiling_stats': profiling_stats[:1000]  # Truncate for logging
            })

            return result

        except Exception as e:
            self.profiler.disable()
            logger.error(f"Function profiling failed: {e}")
            raise
```

## Security Logging

### Security Event Logging

```python
class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('llm_proxy.security')
        self.audit_logger = logging.getLogger('llm_proxy.audit')

    async def log_security_event(self, event_type: str, details: Dict[str, Any],
                                severity: str = "medium"):
        """Log security-related events"""
        log_entry = {
            'event_type': event_type,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'source_ip': details.get('ip_address'),
            'user_id': details.get('user_id'),
            'session_id': details.get('session_id')
        }

        if severity in ['high', 'critical']:
            self.logger.error(f"Security event: {event_type}", extra=log_entry)
        else:
            self.logger.warning(f"Security event: {event_type}", extra=log_entry)

        # Always log to audit trail
        self.audit_logger.info(f"AUDIT: {event_type}", extra=log_entry)

    async def log_authentication(self, user_id: str, success: bool,
                                method: str, ip_address: str):
        """Log authentication events"""
        await self.log_security_event(
            'authentication',
            {
                'user_id': user_id,
                'success': success,
                'method': method,
                'ip_address': ip_address
            },
            severity='low' if success else 'medium'
        )

    async def log_authorization(self, user_id: str, resource: str,
                               action: str, allowed: bool, ip_address: str):
        """Log authorization events"""
        await self.log_security_event(
            'authorization',
            {
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'allowed': allowed,
                'ip_address': ip_address
            },
            severity='low' if allowed else 'high'
        )

    async def log_suspicious_activity(self, activity_type: str,
                                     details: Dict[str, Any], ip_address: str):
        """Log suspicious activities"""
        await self.log_security_event(
            'suspicious_activity',
            {
                'activity_type': activity_type,
                'details': details,
                'ip_address': ip_address
            },
            severity='high'
        )
```

### Audit Logging

```python
class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('llm_proxy.audit')

    async def log_admin_action(self, admin_user: str, action: str,
                              target: str, details: Dict[str, Any]):
        """Log administrative actions"""
        await self.log_audit_event(
            'admin_action',
            {
                'admin_user': admin_user,
                'action': action,
                'target': target,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def log_config_change(self, user: str, config_section: str,
                               old_value: Any, new_value: Any):
        """Log configuration changes"""
        await self.log_audit_event(
            'config_change',
            {
                'user': user,
                'config_section': config_section,
                'old_value': str(old_value)[:500],  # Truncate for logging
                'new_value': str(new_value)[:500],
                'timestamp': datetime.now().isoformat()
            }
        )

    async def log_data_access(self, user: str, data_type: str,
                             operation: str, record_count: int):
        """Log data access events"""
        await self.log_audit_event(
            'data_access',
            {
                'user': user,
                'data_type': data_type,
                'operation': operation,
                'record_count': record_count,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def log_audit_event(self, event_type: str, details: Dict[str, Any]):
        """Log audit event with tamper-proof format"""
        # Create audit entry with hash for integrity
        audit_entry = {
            'event_type': event_type,
            'details': details,
            'audit_id': str(uuid.uuid4()),
            'hash': self.create_audit_hash(details)
        }

        self.logger.info(f"AUDIT: {event_type}", extra=audit_entry)

    def create_audit_hash(self, details: Dict[str, Any]) -> str:
        """Create hash for audit entry integrity"""
        content = json.dumps(details, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
```

## Troubleshooting with Logs

### Common Log Analysis Patterns

#### Finding Performance Issues

```bash
# Find slow requests
grep '"response_time_ms": [0-9]\{4,\}' logs/llm_proxy.log | jq 'select(.response_time_ms > 5000)'

# Find error patterns
grep '"level": "ERROR"' logs/llm_proxy.log | jq -r '.message' | sort | uniq -c | sort -nr

# Find provider failures
grep '"provider": "openai"' logs/llm_proxy.log | grep '"level": "ERROR"' | jq -r '.message'

# Analyze response time distribution
grep '"response_time_ms"' logs/llm_proxy.log | jq -r '.response_time_ms' | sort -n | awk '
  BEGIN { bin_size=100; max_bins=50 }
  { bin=int($1/bin_size); count[bin]++ }
  END { for (i=0; i<max_bins; i++) if (count[i]>0) print i*bin_size "-" (i+1)*bin_size-1 ": " count[i] }
'
```

#### Finding Security Issues

```bash
# Find authentication failures
grep '"event_type": "authentication"' logs/security.log | jq 'select(.details.success == false)'

# Find suspicious IPs
grep '"ip_address"' logs/llm_proxy.log | jq -r '.ip_address' | sort | uniq -c | sort -nr | head -10

# Find rate limit hits
grep '"rate_limit"' logs/llm_proxy.log | jq -r '.message'

# Find unusual request patterns
grep '"user_id"' logs/llm_proxy.log | jq -r '.user_id' | sort | uniq -c | sort -nr | awk '$1 > 100 {print $2 ": " $1 " requests"}'
```

#### System Health Analysis

```bash
# Check memory usage trends
grep '"memory_percent"' logs/system.log | jq -r '.memory_percent' | awk '
  { sum += $1; count++ }
  END { if (count > 0) print "Average memory usage: " sum/count "%" }
'

# Check error rate trends
grep '"level": "ERROR"' logs/llm_proxy.log | awk '
  { errors[substr($1,1,10)]++ }
  END { for (date in errors) print date ": " errors[date] " errors" }
' | sort

# Check cache performance
grep '"cache_hit":' logs/llm_proxy.log | jq -r '.cache_hit' | awk '
  /true/ { hits++ }
  /false/ { misses++ }
  END {
    total = hits + misses
    if (total > 0) {
      hit_rate = (hits / total) * 100
      print "Cache hit rate: " hit_rate "% (" hits "/" total ")"
    }
  }
'
```

### Log Analysis Tools

```python
class LogAnalyzer:
    def __init__(self, log_file: str):
        self.log_file = log_file

    def analyze_time_range(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Analyze logs within time range"""
        analysis = {
            'total_requests': 0,
            'error_count': 0,
            'avg_response_time': 0,
            'top_errors': {},
            'slow_requests': 0,
            'cache_hit_rate': 0.0
        }

        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())

                    # Check time range
                    log_time = datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
                    if not (start_time <= log_time.isoformat() <= end_time):
                        continue

                    # Analyze entry
                    self.analyze_log_entry(log_entry, analysis)

                except (json.JSONDecodeError, KeyError):
                    continue

        return analysis

    def analyze_log_entry(self, entry: Dict[str, Any], analysis: Dict[str, Any]):
        """Analyze individual log entry"""
        analysis['total_requests'] += 1

        if entry.get('level') == 'ERROR':
            analysis['error_count'] += 1
            error_msg = entry.get('message', 'Unknown error')
            analysis['top_errors'][error_msg] = analysis['top_errors'].get(error_msg, 0) + 1

        if 'response_time_ms' in entry:
            response_time = entry['response_time_ms']
            analysis['avg_response_time'] = (
                (analysis['avg_response_time'] * (analysis['total_requests'] - 1)) + response_time
            ) / analysis['total_requests']

            if response_time > 5000:
                analysis['slow_requests'] += 1

        if 'cache_hit' in entry:
            if entry['cache_hit']:
                analysis['cache_hits'] = analysis.get('cache_hits', 0) + 1
            else:
                analysis['cache_misses'] = analysis.get('cache_misses', 0) + 1

            total_cache = analysis.get('cache_hits', 0) + analysis.get('cache_misses', 0)
            if total_cache > 0:
                analysis['cache_hit_rate'] = analysis['cache_hits'] / total_cache
```

## Best Practices

### Logging Best Practices

1. **Structured Logging**
   - Use consistent JSON format
   - Include relevant context in every log entry
   - Use appropriate log levels
   - Include unique identifiers (request_id, trace_id)

2. **Performance Considerations**
   - Avoid logging in hot paths
   - Use async logging when possible
   - Implement log buffering
   - Configure appropriate log levels in production

3. **Security Considerations**
   - Never log sensitive information
   - Implement log sanitization
   - Use encryption for sensitive logs
   - Implement proper access controls

### Log Management Best Practices

1. **Log Rotation**
   - Implement time-based rotation
   - Set appropriate retention periods
   - Use compression to save space
   - Implement log cleanup policies

2. **Log Storage**
   - Use appropriate storage backends
   - Implement log archiving
   - Consider log encryption
   - Plan for log scalability

3. **Log Analysis**
   - Implement automated log analysis
   - Set up log monitoring and alerting
   - Create log analysis dashboards
   - Document common log analysis patterns

### Production Considerations

1. **Resource Management**
   - Monitor disk space for logs
   - Configure appropriate buffer sizes
   - Implement log rate limiting
   - Plan for log storage scaling

2. **Compliance and Audit**
   - Implement audit logging for compliance
   - Set up log integrity checks
   - Configure appropriate retention periods
   - Implement log access controls

3. **Monitoring and Alerting**
   - Set up alerts for log-related issues
   - Monitor log volume and patterns
   - Implement log anomaly detection
   - Create log-based health checks

---

## 📊 Log Analysis Dashboard

### Recommended Kibana/Grafana Panels

1. **Log Volume Trends**
   ```
   Query: *
   Group by: @timestamp (hourly)
   Chart: Line chart
   ```

2. **Error Rate Monitoring**
   ```
   Query: level: ERROR
   Group by: @timestamp (5m)
   Chart: Line chart with threshold
   ```

3. **Response Time Distribution**
   ```
   Query: response_time_ms:*
   Aggregation: Percentiles (p50, p95, p99)
   Chart: Line chart
   ```

4. **Top Error Messages**
   ```
   Query: level: ERROR
   Group by: message.keyword
   Size: 10
   Chart: Pie chart
   ```

5. **Provider Performance**
   ```
   Query: provider:*
   Group by: provider.keyword
   Metrics: Average response_time_ms
   Chart: Bar chart
   ```

### Key Performance Indicators

- **Log Volume**: Target < 1GB/day for normal operations
- **Error Rate**: Target < 1% of total logs
- **Log Processing Latency**: Target < 100ms
- **Log Storage Efficiency**: Target > 70% compression ratio
- **Log Search Performance**: Target < 5s for common queries

---

## 🔧 Advanced Configuration

### Custom Log Formatters

```python
class CustomJSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data

        # Add exception info
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add custom fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                          'pathname', 'filename', 'module', 'exc_info',
                          'exc_text', 'stack_info', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread',
                          'threadName', 'processName', 'process', 'message']:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)
```

### Distributed Logging

```yaml
# Distributed logging configuration
distributed_logging:
  enabled: true

  # Log aggregation
  aggregation:
    enabled: true
    endpoint: "http://log-aggregator:8080/logs"
    batch_size: 100
    flush_interval: 30

  # Log correlation
  correlation:
    enabled: true
    trace_id_header: "X-Trace-ID"
    span_id_header: "X-Span-ID"
    request_id_header: "X-Request-ID"

  # Log sampling
  sampling:
    enabled: true
    rate: 0.1  # Sample 10% of logs
    rules:
      - level: "DEBUG"
        sample_rate: 0.01  # Sample 1% of debug logs
      - level: "ERROR"
        sample_rate: 1.0   # Sample 100% of error logs
```

---

## 📚 References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/)
- [ELK Stack Documentation](https://www.elastic.co/guide/index.html)
- [Log Analysis Patterns](https://www.loggly.com/ultimate-guide/)
- [Security Logging Standards](https://www.pcisecuritystandards.org/)

---

**📝 This comprehensive logging guide ensures complete observability with structured logging, intelligent analysis, and proactive monitoring for the LLM Proxy API.**