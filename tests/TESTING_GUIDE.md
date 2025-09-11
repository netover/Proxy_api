# LLM Proxy API Testing Guide

This comprehensive testing guide covers all aspects of testing the LLM Proxy API, including unit tests, integration tests, load tests, and chaos engineering.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Test Types Overview](#test-types-overview)
3. [Load Testing](#load-testing)
4. [Chaos Engineering](#chaos-engineering)
5. [OpenTelemetry Testing](#opentelemetry-testing)
6. [Template Testing](#template-testing)
7. [Performance Benchmarking](#performance-benchmarking)
8. [CI/CD Integration](#cicd-integration)

## Quick Start

### Prerequisites
```bash
# Install k6 for load testing
# Windows
winget install k6

# macOS
brew install k6

# Linux
sudo apt-get update && sudo apt-get install k6  # Ubuntu/Debian
```

### Environment Setup
```bash
# Copy environment file
cp .env.example .env

# Set required variables
echo "TEST_API_KEY=test-key-123" >> .env
echo "TEST_BASE_URL=http://localhost:8000" >> .env
```

### Run Basic Tests
```bash
# Start the application
python main.py

# Run unit tests
pytest tests/

# Run load test (light tier)
k6 run tests/load_tests/light_load_30_users.js
```

## Test Types Overview

| Test Type | Purpose | Tools | Frequency |
|-----------|---------|-------|-----------|
| **Unit Tests** | Individual component validation | pytest | Every PR |
| **Integration Tests** | API endpoint testing | pytest-asyncio | Every PR |
| **Load Tests** | Performance under load | k6 | Daily |
| **Chaos Tests** | Resilience testing | Custom framework | Weekly |
| **Template Tests** | Jinja2 template validation | pytest | Every PR |
| **Telemetry Tests** | OpenTelemetry integration | pytest | Every PR |

## Load Testing

### Load Tiers Configuration

The system supports four load testing tiers with specific configurations:

| Tier | Users | Duration | Expected RPS | Use Case |
|------|-------|----------|--------------|----------|
| **Light** | 30 | 5m | 5 RPS | Development testing |
| **Medium** | 100 | 5m | 20 RPS | QA testing |
| **Heavy** | 400 | 15m | 80 RPS | Production readiness |
| **Extreme** | 1000 | 20m | 200 RPS | Stress testing |

### Running Load Tests

#### Light Load (30 users)
```bash
k6 run tests/load_tests/light_load_30_users.js
```

#### Medium Load (100 users)
```bash
k6 run tests/load_tests/medium_load_100_users.js
```

#### Heavy Load (400 users)
```bash
k6 run tests/load_tests/heavy_load_400_users.js
```

#### Extreme Load (1000 users)
```bash
k6 run tests/load_tests/extreme_load_1000_users.js
```

### Custom Load Testing

Create custom load scenarios using the provided templates:

```javascript
// custom_load_test.js
import { scenario } from './templates/load_template.js';

export let options = scenario({
    users: 750,
    duration: '10m',
    ramp_up: '2m',
    payload: {
        model: 'gpt-3.5-turbo',
        max_tokens: 200
    }
});
```

### Load Test Results Analysis

After running load tests, review the generated summary files:

```bash
# View results
cat light_load_summary.json | jq .
cat medium_load_summary.json | jq .
cat heavy_load_summary.json | jq .
cat extreme_load_summary.json | jq .
```

## Chaos Engineering

### Enable Chaos Engineering

```bash
# Enable chaos engineering (disabled by default)
export CHAOS_ENGINEERING_ENABLED=true
export CHAOS_PROBABILITY=0.1
```

### Available Fault Types

| Fault Type | Description | Configuration |
|------------|-------------|---------------|
| **Delay** | Network latency simulation | `duration_ms: 100-2000` |
| **Error** | HTTP error responses | `error_code: 503, 429, 500` |
| **Timeout** | Request timeout simulation | `duration_ms: 5000-30000` |
| **Rate Limit** | 429 Too Many Requests | Automatic |
| **Network Failure** | Connection failures | Simulated |
| **Memory Pressure** | Resource constraints | Simulated |

### Running Chaos Tests

```bash
# Start with chaos engineering enabled
CHAOS_ENGINEERING=true python main.py

# Run chaos tests
python tests/test_chaos.py

# Monitor chaos injection stats
curl http://localhost:8000/metrics | grep chaos
```

### Chaos Test Results

Chaos tests generate detailed reports including:
- Fault injection statistics
- System resilience metrics
- Recovery time analysis
- Provider failover behavior

## OpenTelemetry Testing

### Jaeger Setup

```bash
# Start Jaeger (All-in-One)
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest

# Access Jaeger UI
# http://localhost:16686
```

### Zipkin Setup

```bash
# Start Zipkin
docker run -d -p 9411:9411 openzipkin/zipkin

# Access Zipkin UI
# http://localhost:9411/zipkin/
```

### Verifying OpenTelemetry Integration

```bash
# Check trace exports
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key-123" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}'

# View traces in Jaeger/Zipkin
# Traces should appear under service: llm-proxy
```

### Custom Span Testing

```python
# tests/test_telemetry.py
from src.core.telemetry import TracedSpan, traced

@traced("test_operation")
async def test_function():
    with TracedSpan("test_span", attributes={"test": True}):
        return "success"
```

## Template Testing

### Jinja2 Template Validation

```bash
# Run template tests
python -m pytest tests/test_templates.py -v

# Validate specific templates
python tests/validate_templates.py --template prompt_chat.j2
```

### Template Performance Benchmarking

```bash
# Run template performance tests
python tests/benchmark_templates.py --iterations 10000

# Compare template rendering performance
python tests/compare_templates.py --template1 prompt_chat.j2 --template2 prompt_text.j2
```

### Template Context Validation

```python
# Validate template variables
from src.core.template_manager import template_manager

context = {
    "messages": [{"role": "user", "content": "test"}],
    "system_message": "You are helpful"
}

is_valid = template_manager.validate_template_variables("prompt_chat.j2", context)
```

## Performance Benchmarking

### Benchmarking Tools

```bash
# Install benchmarking tools
pip install pytest-benchmark memory-profiler

# Run performance benchmarks
pytest tests/benchmarks/ --benchmark-only --benchmark-sort=mean
```

### Memory Profiling

```bash
# Profile memory usage
python -m memory_profiler tests/memory_profile.py

# Generate memory usage report
python tests/generate_memory_report.py
```

### CPU Profiling

```bash
# Profile CPU usage
python -m cProfile -o profile_output.pstats tests/profile_app.py

# View profile results
snakeviz profile_output.pstats
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      jaeger:
        image: jaegertracing/all-in-one:latest
        ports:
          - 16686:16686
          - 14268:14268
      zipkin:
        image: openzipkin/zipkin:latest
        ports:
          - 9411:9411
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-benchmark
    
    - name: Run unit tests
      run: pytest tests/test_*.py -v
    
    - name: Run load tests
      run: |
        docker run --rm -v $PWD:/tests loadimpact/k6 run /tests/load_tests/light_load_30_users.js
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: |
          *.json
          *.xml
```

### Docker Testing Environment

```bash
# Build test environment
docker-compose -f docker-compose.test.yml up --build

# Run tests in container
docker-compose -f docker-compose.test.yml run app pytest tests/

# Run load tests
docker-compose -f docker-compose.test.yml run k6 k6 run /tests/load_tests/medium_load_100_users.js
```

## Test Data Generation

### Synthetic Test Data

```bash
# Generate synthetic test data
python tests/generate_test_data.py --count 1000 --output test_data.jsonl

# Create load testing dataset
python tests/create_load_test_dataset.py --size large --format k6
```

### Real-world Scenarios

```bash
# Test with production-like data
python tests/simulate_real_scenarios.py --scenario e_commerce
python tests/simulate_real_scenarios.py --scenario customer_support
python tests/simulate_real_scenarios.py --scenario code_review
```

## Monitoring and Alerts

### Test Monitoring

```bash
# Monitor test execution
python tests/monitor_tests.py --output test_monitoring.log

# Set up alerts for test failures
python tests/setup_alerts.py --webhook-url https://hooks.slack.com/...
```

### Grafana Dashboards

Import the provided Grafana dashboards for:

- Load test metrics
- Chaos engineering results
- OpenTelemetry traces
- Application performance
- System health

## Troubleshooting Common Issues

### Load Test Failures

| Issue | Solution |
|-------|----------|
| **High Error Rate** | Check provider availability and API limits |
| **Timeout Errors** | Increase timeout values in test configuration |
| **Memory Issues** | Monitor memory usage and adjust cache settings |
| **Rate Limiting** | Verify rate limiting configuration |

### Chaos Test Issues

| Issue | Solution |
|-------|----------|
| **No Fault Injection** | Verify chaos engineering is enabled |
| **Too Many Failures** | Reduce chaos probability or severity |
| **System Unresponsive** | Check circuit breaker configuration |

### OpenTelemetry Issues

| Issue | Solution |
|-------|----------|
| **No Traces in Jaeger** | Verify Jaeger is running and accessible |
| **Missing Spans** | Check span creation and attributes |
| **High Resource Usage** | Reduce sampling rate |

## Best Practices

### Load Testing Best Practices

1. **Gradual Ramp-up**: Always use gradual user ramp-up
2. **Realistic Data**: Use production-like test data
3. **Monitor Metrics**: Watch memory, CPU, and network usage
4. **Clean Environment**: Reset between test runs
5. **Document Results**: Keep detailed test result logs

### Chaos Engineering Best Practices

1. **Start Small**: Begin with low-probability faults
2. **Monitor Impact**: Track system behavior during faults
3. **Test Recovery**: Verify automatic recovery mechanisms
4. **Document Findings**: Record resilience improvements
5. **Gradual Increase**: Increase fault severity over time

## Support and Resources

- **Documentation**: See `/docs/` directory
- **Examples**: Check `/examples/` directory
- **Issues**: Report on GitHub
- **Discord**: Join community discussions
- **Email**: support@llm-proxy.com