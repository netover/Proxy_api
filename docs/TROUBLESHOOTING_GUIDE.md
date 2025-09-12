# 🔧 Troubleshooting Guide - LLM Proxy API

Comprehensive troubleshooting guide for diagnosing and resolving issues with the LLM Proxy API.

## Table of Contents

- [Quick Diagnosis](#quick-diagnosis)
- [Installation Issues](#installation-issues)
- [Startup Problems](#startup-problems)
- [API Errors](#api-errors)
- [Performance Issues](#performance-issues)
- [Connection Problems](#connection-problems)
- [Authentication Issues](#authentication-issues)
- [Provider-Specific Issues](#provider-specific-issues)
- [Monitoring and Logs](#monitoring-and-logs)
- [Advanced Diagnostics](#advanced-diagnostics)
- [Common Solutions](#common-solutions)

## Quick Diagnosis

### Health Check Script

```bash
#!/bin/bash
# Quick health check script

echo "=== LLM Proxy API Health Check ==="
echo

# Check if service is running
echo "1. Service Status:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Service is running"
else
    echo "❌ Service is not responding"
fi
echo

# Check API health
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

# Check providers
echo "3. Provider Status:"
PROVIDERS=$(curl -s http://localhost:8000/health/providers)
if [ $? -eq 0 ]; then
    echo "Provider health details:"
    echo $PROVIDERS | jq '.'
else
    echo "❌ Cannot check provider status"
fi
echo

# Check system resources
echo "4. System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.2f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df / | tail -1 | awk '{print $5}')"
echo

echo "=== End Health Check ==="
```

### Diagnostic Commands

```bash
# Check service status
sudo systemctl status llm-proxy
docker-compose ps

# Check logs
tail -f logs/llm_proxy.log
docker-compose logs -f llm-proxy

# Check resource usage
top -p $(pgrep -f "python.*main")
ps aux --sort=-%mem | head -10

# Check network connections
netstat -tlnp | grep :8000
ss -tlnp | grep :8000

# Check disk space
df -h
du -sh /opt/llm-proxy/
```

## Installation Issues

### Python Version Problems

**Symptoms:**
- `python3: command not found`
- `ModuleNotFoundError` during installation
- Incompatible Python version

**Diagnosis:**
```bash
# Check Python version
python3 --version
python --version

# Check if pip is installed
pip3 --version
pip --version

# Check Python path
which python3
which pip3
```

**Solutions:**

1. **Install Python 3.11+**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install software-properties-common
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt install python3.11 python3.11-venv python3.11-pip

   # CentOS/RHEL
   sudo yum install python311 python311-pip

   # macOS
   brew install python@3.11
   ```

2. **Use correct Python version**
   ```bash
   # Specify Python version explicitly
   python3.11 -m venv venv
   source venv/bin/activate
   python3.11 -m pip install -r requirements.txt
   ```

3. **Update pip**
   ```bash
   python3 -m pip install --upgrade pip
   ```

### Dependency Installation Failures

**Symptoms:**
- `pip install` fails with compilation errors
- Missing system libraries
- Permission denied errors

**Diagnosis:**
```bash
# Check pip version
pip --version

# Check for compilation errors
pip install -r requirements.txt -v

# Check system libraries
ldd $(which python3)
```

**Solutions:**

1. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt install build-essential python3-dev

   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install python3-devel

   # macOS
   xcode-select --install
   ```

2. **Use pre-compiled packages**
   ```bash
   # Use PyPI wheels
   pip install --only-binary=all -r requirements.txt

   # Or install specific problematic packages
   pip install --no-cache-dir <package-name>
   ```

3. **Fix permission issues**
   ```bash
   # Use user installation
   pip install --user -r requirements.txt

   # Or use virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Docker Installation Issues

**Symptoms:**
- `docker build` fails
- Container won't start
- Port binding issues

**Diagnosis:**
```bash
# Check Docker status
docker --version
docker info

# Check build logs
docker build -t llm-proxy . --progress=plain

# Check container logs
docker logs llm-proxy

# Check port conflicts
docker ps
netstat -tlnp | grep :8000
```

**Solutions:**

1. **Fix Dockerfile issues**
   ```dockerfile
   # Use correct base image
   FROM python:3.11-slim

   # Install dependencies first
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .

   # Expose port
   EXPOSE 8000

   # Use proper CMD
   CMD ["python", "main_dynamic.py"]
   ```

2. **Fix port conflicts**
   ```bash
   # Use different host port
   docker run -p 8001:8000 llm-proxy

   # Or stop conflicting service
   sudo systemctl stop apache2
   ```

3. **Fix permission issues**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER

   # Or run with sudo
   sudo docker run -p 8000:8000 llm-proxy
   ```

## Startup Problems

### Service Won't Start

**Symptoms:**
- Service fails to start
- Port already in use
- Permission denied errors

**Diagnosis:**
```bash
# Check service logs
sudo journalctl -u llm-proxy -n 50

# Check application logs
tail -f logs/llm_proxy.log

# Check port availability
sudo netstat -tlnp | grep :8000

# Check permissions
ls -la /opt/llm-proxy/
```

**Solutions:**

1. **Fix port conflicts**
   ```bash
   # Find process using port
   sudo lsof -i :8000
   sudo kill -9 <PID>

   # Or change port in configuration
   sed -i 's/8000/8001/g' config.yaml
   ```

2. **Fix permission issues**
   ```bash
   # Fix directory permissions
   sudo chown -R llm-proxy:llm-proxy /opt/llm-proxy
   sudo chmod -R 755 /opt/llm-proxy

   # Fix log directory
   sudo mkdir -p /opt/llm-proxy/logs
   sudo chown llm-proxy:llm-proxy /opt/llm-proxy/logs
   ```

3. **Fix systemd service**
   ```bash
   # Check service file
   sudo systemctl cat llm-proxy

   # Reload systemd
   sudo systemctl daemon-reload

   # Check service status
   sudo systemctl status llm-proxy
   ```

### Configuration Errors

**Symptoms:**
- Invalid configuration file
- Missing required settings
- YAML parsing errors

**Diagnosis:**
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check configuration file
cat config.yaml

# Test configuration loading
python3 -c "from src.core.config import load_config; print(load_config())"
```

**Solutions:**

1. **Fix YAML syntax**
   ```yaml
   # Correct YAML format
   app:
     name: "LLM Proxy API"
     environment: "production"

   server:
     host: "0.0.0.0"
     port: 8000

   providers:
     - name: "openai"
       type: "openai"
       api_key_env: "OPENAI_API_KEY"
   ```

2. **Add missing environment variables**
   ```bash
   # Check required variables
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY

   # Add to .env file
   cat >> .env << EOF
   OPENAI_API_KEY=sk-your-key
   ANTHROPIC_API_KEY=sk-ant-your-key
   EOF
   ```

3. **Validate configuration**
   ```python
   # Configuration validation script
   from src.core.config import load_config
   import sys

   try:
       config = load_config()
       print("✅ Configuration is valid")
       print(f"Providers: {len(config.get('providers', []))}")
   except Exception as e:
       print(f"❌ Configuration error: {e}")
       sys.exit(1)
   ```

## API Errors

### 400 Bad Request

**Symptoms:**
- Invalid request format
- Missing required parameters
- Malformed JSON

**Diagnosis:**
```bash
# Test with valid request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Check request format
curl -v -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"invalid": "json"}'
```

**Solutions:**

1. **Fix request format**
   ```python
   # Correct request format
   import requests

   response = requests.post(
       "http://localhost:8000/v1/chat/completions",
       headers={
           "Authorization": "Bearer your-api-key",
           "Content-Type": "application/json"
       },
       json={
           "model": "gpt-3.5-turbo",
           "messages": [
               {"role": "user", "content": "Hello, world!"}
           ],
           "max_tokens": 100,
           "temperature": 0.7
       }
   )
   ```

2. **Validate required parameters**
   ```python
   # Check required fields
   required_fields = ["model", "messages"]
   data = {"model": "gpt-3.5-turbo", "messages": []}

   missing = [field for field in required_fields if field not in data]
   if missing:
       print(f"Missing required fields: {missing}")
   ```

### 401 Unauthorized

**Symptoms:**
- Authentication failed
- Invalid API key
- Missing authorization header

**Diagnosis:**
```bash
# Test authentication
curl http://localhost:8000/api/models \
  -H "Authorization: Bearer your-api-key"

# Check API key format
echo "your-api-key" | grep -E "^sk-"

# Test with invalid key
curl http://localhost:8000/api/models \
  -H "Authorization: Bearer invalid-key"
```

**Solutions:**

1. **Fix API key**
   ```bash
   # Check environment variable
   echo $OPENAI_API_KEY

   # Update .env file
   sed -i 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=sk-your-correct-key/' .env

   # Restart service
   sudo systemctl restart llm-proxy
   ```

2. **Fix authorization header**
   ```bash
   # Correct format
   curl -H "Authorization: Bearer sk-your-key" \
        http://localhost:8000/api/models

   # Check for extra spaces
   curl -H "Authorization: Bearer sk-your-key " \
        http://localhost:8000/api/models
   ```

### 429 Too Many Requests

**Symptoms:**
- Rate limit exceeded
- Requests being throttled
- Intermittent failures

**Diagnosis:**
```bash
# Check rate limit headers
curl -I http://localhost:8000/api/models \
  -H "Authorization: Bearer your-key"

# Monitor request rate
curl http://localhost:8000/metrics | jq '.rate_limiting'

# Check provider rate limits
curl http://localhost:8000/health/providers
```

**Solutions:**

1. **Implement rate limiting**
   ```python
   import time
   from collections import deque

   class RateLimiter:
       def __init__(self, requests_per_minute=60):
           self.requests_per_minute = requests_per_minute
           self.requests = deque()

       def wait_if_needed(self):
           now = time.time()
           while self.requests and now - self.requests[0] > 60:
               self.requests.popleft()

           if len(self.requests) >= self.requests_per_minute:
               sleep_time = 60 - (now - self.requests[0])
               if sleep_time > 0:
                   time.sleep(sleep_time)

           self.requests.append(now)

   limiter = RateLimiter()

   # Use before making requests
   limiter.wait_if_needed()
   response = requests.post(url, json=data, headers=headers)
   ```

2. **Increase rate limits**
   ```yaml
   # Update configuration
   rate_limits:
     openai:
       requests_per_minute: 100
     anthropic:
       requests_per_minute: 50
   ```

### 500 Internal Server Error

**Symptoms:**
- Unexpected server errors
- Application crashes
- Service unavailability

**Diagnosis:**
```bash
# Check application logs
tail -f logs/llm_proxy.log

# Check system logs
sudo journalctl -u llm-proxy -n 100

# Check error details
curl http://localhost:8000/health/detailed

# Monitor system resources
top -p $(pgrep -f python)
free -h
```

**Solutions:**

1. **Check application logs**
   ```bash
   # Search for error patterns
   grep "ERROR" logs/llm_proxy.log | tail -10

   # Check for stack traces
   grep "Traceback" logs/llm_proxy.log
   ```

2. **Restart service**
   ```bash
   sudo systemctl restart llm-proxy
   docker-compose restart llm-proxy
   ```

3. **Check system resources**
   ```bash
   # Monitor memory usage
   ps aux --sort=-%mem | head -5

   # Check disk space
   df -h

   # Monitor CPU usage
   top -bn1 | head -10
   ```

## Performance Issues

### High Latency

**Symptoms:**
- Slow response times
- Timeout errors
- Degraded user experience

**Diagnosis:**
```bash
# Check response times
curl http://localhost:8000/metrics | jq '.performance.avg_response_time_ms'

# Monitor cache performance
curl http://localhost:8000/metrics | jq '.cache'

# Check connection pool
curl http://localhost:8000/metrics | jq '.connection_pool'

# Profile application
python3 -c "import cProfile; cProfile.run('import main_dynamic')"
```

**Solutions:**

1. **Optimize caching**
   ```yaml
   # Improve cache configuration
   caching:
     enabled: true
     response_cache:
       max_size_mb: 512
       ttl: 1800
     summary_cache:
       max_size_mb: 256
       ttl: 3600
   ```

2. **Tune connection pool**
   ```yaml
   # Optimize connection settings
   http_client:
     pool_limits:
       max_connections: 200
       max_keepalive_connections: 50
     timeout: 25.0
   ```

3. **Enable performance monitoring**
   ```yaml
   # Add performance profiling
   performance:
     profiling: true
     slow_request_threshold: 1000  # Log requests > 1s
   ```

### Memory Issues

**Symptoms:**
- High memory usage
- Out of memory errors
- Application restarts

**Diagnosis:**
```bash
# Check memory usage
curl http://localhost:8000/health | jq '.checks.memory'

# Monitor garbage collection
curl http://localhost:8000/debug/memory/gc

# Check for memory leaks
curl http://localhost:8000/debug/memory/profile

# System memory info
free -h
ps aux --sort=-%mem | head -5
```

**Solutions:**

1. **Reduce cache size**
   ```yaml
   caching:
     response_cache:
       max_size_mb: 256  # Reduce from 512
     summary_cache:
       max_size_mb: 128  # Reduce from 256
   ```

2. **Enable memory optimization**
   ```yaml
   memory:
     max_usage_percent: 75
     gc_tuning: true
     emergency_cleanup: true
   ```

3. **Monitor memory usage**
   ```bash
   # Add memory monitoring
   watch -n 5 'ps aux --sort=-%mem | head -5'
   ```

### High CPU Usage

**Symptoms:**
- High CPU utilization
- Slow response times
- System overload

**Diagnosis:**
```bash
# Check CPU usage
top -bn1 | head -10

# Monitor application threads
ps -T -p $(pgrep -f python)

# Check for blocking operations
curl http://localhost:8000/debug/threads

# Profile CPU usage
python3 -m cProfile -s cumulative main_dynamic.py
```

**Solutions:**

1. **Optimize worker processes**
   ```yaml
   server:
     workers: 4  # Adjust based on CPU cores
     worker_class: "uvicorn.workers.UvicornWorker"
   ```

2. **Enable async operations**
   ```python
   # Use async/await for I/O operations
   async def handle_request(request):
       # Async database queries
       result = await database.fetch(query)

       # Async HTTP requests
       response = await http_client.request(url, data)

       return result
   ```

3. **Add CPU monitoring**
   ```yaml
   monitoring:
     cpu:
       threshold_percent: 80
       alert_enabled: true
   ```

## Connection Problems

### Network Connectivity

**Symptoms:**
- Connection refused errors
- DNS resolution failures
- Network timeouts

**Diagnosis:**
```bash
# Test basic connectivity
ping api.openai.com

# Check DNS resolution
nslookup api.openai.com

# Test HTTPS connectivity
curl -I https://api.openai.com/v1/models

# Check firewall rules
sudo ufw status
sudo iptables -L
```

**Solutions:**

1. **Fix DNS issues**
   ```bash
   # Update DNS servers
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf
   ```

2. **Configure proxy settings**
   ```bash
   # Set HTTP proxy
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080

   # Or in configuration
   http_client:
     proxy:
       http: "http://proxy.company.com:8080"
       https: "http://proxy.company.com:8080"
   ```

3. **Fix firewall rules**
   ```bash
   # Allow outbound connections
   sudo ufw allow out to any port 443
   sudo ufw allow out to any port 80
   ```

### SSL/TLS Issues

**Symptoms:**
- SSL certificate errors
- TLS handshake failures
- Certificate verification errors

**Diagnosis:**
```bash
# Test SSL connection
openssl s_client -connect api.openai.com:443

# Check certificate validity
curl -v https://api.openai.com/v1/models 2>&1 | grep -A 5 "SSL certificate"

# Test with certificate verification disabled
curl --insecure https://api.openai.com/v1/models
```

**Solutions:**

1. **Update CA certificates**
   ```bash
   # Ubuntu/Debian
   sudo apt install ca-certificates
   sudo update-ca-certificates

   # CentOS/RHEL
   sudo yum install ca-certificates
   sudo update-ca-trust
   ```

2. **Configure SSL settings**
   ```yaml
   http_client:
     ssl:
       verify: true
       cert_file: "/path/to/cert.pem"
       key_file: "/path/to/key.pem"
       ca_bundle: "/path/to/ca-bundle.crt"
   ```

3. **Disable SSL verification (not recommended)**
   ```yaml
   http_client:
     ssl:
       verify: false  # Only for testing
   ```

## Authentication Issues

### API Key Problems

**Symptoms:**
- Authentication failures
- Invalid API key errors
- Key rotation issues

**Diagnosis:**
```bash
# Test API key validity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check key format
echo $OPENAI_API_KEY | head -c 10

# Test with proxy
curl http://localhost:8000/api/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Solutions:**

1. **Update API keys**
   ```bash
   # Update environment variables
   export OPENAI_API_KEY="sk-new-key-here"
   export ANTHROPIC_API_KEY="sk-ant-new-key-here"

   # Update .env file
   sed -i 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=sk-new-key/' .env

   # Restart service
   sudo systemctl restart llm-proxy
   ```

2. **Configure key rotation**
   ```yaml
   auth:
     key_rotation:
       enabled: true
       rotation_interval_days: 30
       grace_period_hours: 24
   ```

### Permission Issues

**Symptoms:**
- Access denied errors
- Insufficient permissions
- Role-based access failures

**Diagnosis:**
```bash
# Check user permissions
curl http://localhost:8000/api/user/permissions \
  -H "Authorization: Bearer your-key"

# Test with different keys
curl http://localhost:8000/api/models \
  -H "Authorization: Bearer admin-key"

# Check audit logs
grep "permission" logs/audit.log
```

**Solutions:**

1. **Update user permissions**
   ```yaml
   auth:
     users:
       - username: "admin"
         api_key: "sk-admin-key"
         permissions: ["read", "write", "admin"]
       - username: "user"
         api_key: "sk-user-key"
         permissions: ["read"]
   ```

2. **Configure rate limits per user**
   ```yaml
   rate_limits:
     admin:
       requests_per_minute: 1000
     user:
       requests_per_minute: 100
   ```

## Provider-Specific Issues

### OpenAI Issues

**Symptoms:**
- OpenAI API errors
- Model not found
- Rate limit exceeded

**Diagnosis:**
```bash
# Test OpenAI API directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check model availability
curl http://localhost:8000/api/models?provider=openai

# Check OpenAI status
curl https://status.openai.com/api/v2/status.json
```

**Solutions:**

1. **Update OpenAI configuration**
   ```yaml
   providers:
     - name: "openai"
       type: "openai"
       api_key_env: "OPENAI_API_KEY"
       base_url: "https://api.openai.com/v1"
       timeout: 30
       max_retries: 3
   ```

2. **Handle rate limits**
   ```python
   # Implement exponential backoff
   import time

   def call_openai_with_retry(data, max_retries=3):
       for attempt in range(max_retries):
           response = requests.post(
               "https://api.openai.com/v1/chat/completions",
               headers={"Authorization": f"Bearer {API_KEY}"},
               json=data
           )

           if response.status_code == 429:
               wait_time = 2 ** attempt
               time.sleep(wait_time)
               continue

           return response

       raise Exception("Max retries exceeded")
   ```

### Anthropic Issues

**Symptoms:**
- Claude API errors
- Token limit exceeded
- Authentication failures

**Diagnosis:**
```bash
# Test Anthropic API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"

# Check model availability
curl http://localhost:8000/api/models?provider=anthropic
```

**Solutions:**

1. **Update Anthropic configuration**
   ```yaml
   providers:
     - name: "anthropic"
       type: "anthropic"
       api_key_env: "ANTHROPIC_API_KEY"
       base_url: "https://api.anthropic.com"
       timeout: 30
       max_retries: 3
   ```

2. **Handle token limits**
   ```python
   # Check token count before sending
   def estimate_tokens(text):
       return len(text.split()) * 1.3  # Rough estimation

   def call_anthropic_safe(messages, model="claude-3-sonnet-20240229"):
       total_tokens = sum(estimate_tokens(msg["content"]) for msg in messages)

       if total_tokens > 180000:  # Claude's limit
           raise ValueError("Message too long for Claude")

       # Make API call
       response = requests.post(
           "https://api.anthropic.com/v1/messages",
           headers={
               "x-api-key": ANTHROPIC_KEY,
               "anthropic-version": "2023-06-01"
           },
           json={
               "model": model,
               "max_tokens": 4096,
               "messages": messages
           }
       )

       return response
   ```

## Monitoring and Logs

### Log Analysis

**Symptoms:**
- Log files growing too large
- Missing log entries
- Log parsing errors

**Diagnosis:**
```bash
# Check log file size
ls -lh logs/llm_proxy.log

# Check log rotation
ls -la logs/llm_proxy.log*

# Test log parsing
python3 -c "
import json
with open('logs/llm_proxy.log', 'r') as f:
    for line in f:
        try:
            json.loads(line.strip())
        except json.JSONDecodeError as e:
            print(f'Invalid JSON: {e}')
            break
"

# Check log levels
grep '"level"' logs/llm_proxy.log | sort | uniq -c
```

**Solutions:**

1. **Configure log rotation**
   ```yaml
   logging:
     rotation:
       enabled: true
       max_file_size: "100MB"
       max_files: 5
       when: "midnight"
       compression: "gzip"
   ```

2. **Fix log parsing issues**
   ```python
   # Validate log entries
   import json

   def validate_logs(log_file):
       errors = []
       with open(log_file, 'r') as f:
           for i, line in enumerate(f, 1):
               line = line.strip()
               if not line:
                   continue
               try:
                   json.loads(line)
               except json.JSONDecodeError as e:
                   errors.append(f"Line {i}: {e}")
       return errors

   errors = validate_logs('logs/llm_proxy.log')
   if errors:
       print("Log validation errors:")
       for error in errors[:10]:  # Show first 10
           print(error)
   ```

### Metrics Issues

**Symptoms:**
- Missing metrics data
- Incorrect metric values
- Metrics collection failures

**Diagnosis:**
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Test Prometheus format
curl http://localhost:8000/metrics/prometheus

# Check metrics collection
curl http://localhost:8000/debug/metrics/status

# Validate metrics data
curl http://localhost:8000/metrics | jq '.'
```

**Solutions:**

1. **Fix metrics collection**
   ```yaml
   metrics:
     enabled: true
     collection_interval: 60
     retention_days: 30
     prometheus:
       enabled: true
       port: 9090
   ```

2. **Validate metrics data**
   ```python
   # Metrics validation script
   import requests
   import json

   def validate_metrics():
       response = requests.get("http://localhost:8000/metrics")
       if response.status_code != 200:
           print(f"Metrics endpoint failed: {response.status_code}")
           return False

       try:
           metrics = response.json()
           required_fields = ["total_requests", "successful_requests", "error_rate"]

           for field in required_fields:
               if field not in metrics:
                   print(f"Missing required metric: {field}")
                   return False

           print("✅ Metrics validation passed")
           return True

       except json.JSONDecodeError:
           print("Invalid JSON in metrics response")
           return False

   validate_metrics()
   ```

## Advanced Diagnostics

### Performance Profiling

```python
# Application profiling
import cProfile
import pstats
from io import StringIO

def profile_application():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run your application code here
    import main_dynamic
    # ... application logic ...

    profiler.disable()

    # Generate report
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')

    # Save to file
    stats.dump_stats('profile.prof')

    # Print top 20 functions
    output = StringIO()
    stats.print_stats(20, stream=output)
    print(output.getvalue())

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    pass

# Network profiling
import requests
from requests_toolbelt import sessions

def profile_http_request(url, data):
    with sessions.BaseUrlSession(base_url="http://localhost:8000") as session:
        # Enable debugging
        import logging
        logging.basicConfig()
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

        response = session.post(url, json=data)
        return response
```

### System Diagnostics

```bash
# Comprehensive system check
#!/bin/bash

echo "=== System Diagnostics ==="

# CPU information
echo "CPU Info:"
lscpu | grep -E "(Architecture|CPU\(s\)|Model name|CPU MHz)"

# Memory information
echo -e "\nMemory Info:"
free -h

# Disk information
echo -e "\nDisk Info:"
df -h

# Network information
echo -e "\nNetwork Info:"
ip addr show | grep -E "(inet |link/ether)"

# Process information
echo -e "\nProcess Info:"
ps aux --sort=-%cpu | head -10

# System load
echo -e "\nSystem Load:"
uptime

# Open files
echo -e "\nOpen Files:"
lsof -p $(pgrep -f python) | wc -l

echo "=== End Diagnostics ==="
```

### Database Diagnostics

```python
# Database connection check
import asyncpg
import asyncio

async def check_database():
    try:
        conn = await asyncpg.connect(
            user='llm_proxy',
            password='password',
            database='llm_proxy_db',
            host='localhost'
        )

        # Test query
        result = await conn.fetchval("SELECT version()")
        print(f"Database version: {result}")

        # Check table sizes
        tables = await conn.fetch("""
            SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
            FROM pg_stat_user_tables
            ORDER BY n_tup_ins DESC
            LIMIT 10
        """)

        print("Top tables by inserts:")
        for table in tables:
            print(f"  {table['schemaname']}.{table['tablename']}: {table['n_tup_ins']}")

        await conn.close()
        print("✅ Database check passed")

    except Exception as e:
        print(f"❌ Database check failed: {e}")

asyncio.run(check_database())
```

## Common Solutions

### Quick Fixes

1. **Restart Service**
   ```bash
   sudo systemctl restart llm-proxy
   docker-compose restart llm-proxy
   ```

2. **Clear Cache**
   ```bash
   curl -X DELETE http://localhost:8000/api/cache
   rm -rf cache/*
   ```

3. **Check Logs**
   ```bash
   tail -f logs/llm_proxy.log
   grep "ERROR" logs/llm_proxy.log | tail -10
   ```

4. **Update Configuration**
   ```bash
   # Backup current config
   cp config.yaml config.yaml.backup

   # Edit configuration
   nano config.yaml

   # Restart service
   sudo systemctl restart llm-proxy
   ```

### Emergency Procedures

1. **Service Unavailable**
   ```bash
   # Check service status
   sudo systemctl status llm-proxy

   # Check logs for errors
   sudo journalctl -u llm-proxy -n 50

   # Restart service
   sudo systemctl restart llm-proxy

   # If restart fails, check dependencies
   sudo systemctl status redis postgresql
   ```

2. **High Resource Usage**
   ```bash
   # Check resource usage
   top -p $(pgrep -f python)

   # Kill problematic processes
   sudo kill -9 <PID>

   # Restart with new configuration
   sudo systemctl restart llm-proxy
   ```

3. **Data Loss Recovery**
   ```bash
   # Check backups
   ls -la backups/

   # Restore from backup
   cp backups/config.yaml.backup config.yaml
   cp backups/database.dump latest.dump

   # Restore database
   pg_restore -d llm_proxy_db latest.dump
   ```

### Preventive Measures

1. **Regular Maintenance**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade

   # Clean old logs
   find logs/ -name "*.log.*" -mtime +30 -delete

   # Update application
   git pull origin main
   pip install -r requirements.txt --upgrade
   ```

2. **Monitoring Setup**
   ```yaml
   monitoring:
     alerts:
       - name: "high_error_rate"
         condition: "error_rate > 0.05"
         action: "notify_team"
       - name: "service_down"
         condition: "health_status != 'healthy'"
         action: "restart_service"
   ```

3. **Backup Strategy**
   ```bash
   # Database backup
   pg_dump llm_proxy_db > backups/database_$(date +%Y%m%d).dump

   # Configuration backup
   cp config.yaml backups/config_$(date +%Y%m%d).yaml

   # Log archival
   tar -czf backups/logs_$(date +%Y%m%d).tar.gz logs/
   ```

---

**🔧 This comprehensive troubleshooting guide provides systematic approaches to diagnose and resolve issues with the LLM Proxy API, from basic setup problems to advanced performance tuning and emergency recovery procedures.**