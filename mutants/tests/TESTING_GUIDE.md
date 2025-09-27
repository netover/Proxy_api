# LLM Proxy API Testing Guide

This comprehensive testing guide covers all aspects of testing the LLM Proxy API, including unit tests, integration tests, load tests, and chaos engineering.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Test Types Overview](#test-types-overview)
3. [Load Testing](#load-testing)
4. [Chaos Engineering](#chaos-engineering)
5. [Security Testing](#security-testing)
6. [OpenTelemetry Testing](#opentelemetry-testing)
7. [Template Testing](#template-testing)
8. [Performance Benchmarking](#performance-benchmarking)
9. [CI/CD Integration](#cicd-integration)

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
| **Security Tests** | Vulnerability scanning, auth testing, penetration testing | pytest, bandit, safety | Every PR |
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

## Security Testing

### Security Testing Overview

The LLM Proxy API includes comprehensive security testing capabilities covering:

- **Vulnerability Scanning**: Automated code vulnerability detection using Bandit
- **Authentication Testing**: Comprehensive auth mechanism validation
- **Input Validation Testing**: SQL injection, XSS, and other injection attack prevention
- **Penetration Testing**: Automated penetration testing scenarios
- **Dependency Scanning**: Third-party library vulnerability detection

### Prerequisites

```bash
# Install security testing tools
pip install bandit safety

# For advanced penetration testing (optional)
pip install sqlmap nikto dirbuster
```

### Running Security Tests

#### Quick Security Scan
```bash
# Run all security tests
python tests/security/run_security_tests.py

# Run specific test types
python tests/security/run_security_tests.py --test-type vuln     # Vulnerability scanning only
python tests/security/run_security_tests.py --test-type auth     # Authentication tests only
python tests/security/run_security_tests.py --test-type input    # Input validation tests only
python tests/security/run_security_tests.py --test-type pentest  # Penetration tests only
```

#### Individual Security Test Suites
```bash
# Run vulnerability scanning tests
python -m pytest tests/security/test_vulnerability_scanning.py -v

# Run authentication security tests
python -m pytest tests/security/test_authentication_security.py -v

# Run input validation security tests
python -m pytest tests/security/test_input_validation_security.py -v

# Run penetration testing
python -m pytest tests/security/test_penetration_testing.py -v
```

### Security Test Results Analysis

After running security tests, review the generated report:

```bash
# View latest security test report
cat security_test_report_*.json | jq .

# Check for high-severity vulnerabilities
cat security_test_report_*.json | jq '.summary.vulnerability_counts'
```

### Automated Vulnerability Scanning

#### Bandit Code Security Scanning
```bash
# Scan source code for security issues
bandit -r src/ -f json -o bandit_report.json

# Generate HTML report
bandit -r src/ -f html -o bandit_report.html

# Scan with custom configuration
bandit -r src/ -c .bandit -f json
```

#### Dependency Vulnerability Scanning
```bash
# Check dependencies for known vulnerabilities
safety check

# Generate JSON report
safety check --json > safety_report.json

# Check specific packages
safety check --package requests
```

### Authentication Security Testing

#### Brute Force Protection Testing
```bash
# Test brute force protection mechanisms
python -m pytest tests/security/test_authentication_security.py::TestAuthenticationSecurity::test_brute_force_protection -v
```

#### API Key Security Testing
```bash
# Test API key validation and security
python -m pytest tests/security/test_authentication_security.py::TestAuthenticationSecurity::test_api_key_entropy -v
```

### Input Validation Security Testing

#### SQL Injection Testing
```bash
# Test SQL injection prevention
python -m pytest tests/security/test_input_validation_security.py::TestInputValidationSecurity::test_sql_injection_prevention -v
```

#### XSS Prevention Testing
```bash
# Test Cross-Site Scripting prevention
python -m pytest tests/security/test_input_validation_security.py::TestInputValidationSecurity::test_xss_prevention -v
```

#### File Upload Security Testing
```bash
# Test file upload security
python -m pytest tests/security/test_input_validation_security.py::TestInputValidationSecurity::test_file_upload_security -v
```

### Penetration Testing Scenarios

#### Automated Penetration Testing
```bash
# Run automated penetration tests
python -m pytest tests/security/test_penetration_testing.py -v
```

#### Directory Traversal Testing
```bash
# Test directory traversal attack prevention
python -m pytest tests/security/test_penetration_testing.py::TestPenetrationTesting::test_directory_traversal_attack -v
```

#### Session Security Testing
```bash
# Test session hijacking prevention
python -m pytest tests/security/test_penetration_testing.py::TestPenetrationTesting::test_session_hijacking_simulation -v
```

### Security Testing Configuration

#### Custom Security Test Configuration
```python
# tests/security/config.py
SECURITY_TEST_CONFIG = {
    "max_brute_force_attempts": 5,
    "lockout_duration_minutes": 15,
    "vulnerability_thresholds": {
        "critical": 0,
        "high": 5,
        "medium": 20,
        "low": 50
    },
    "scan_exclusions": [
        "tests/",
        "docs/",
        "*.md"
    ]
}
```

#### Environment Variables for Security Testing
```bash
# Security test configuration
export SECURITY_TEST_MAX_ATTEMPTS=5
export SECURITY_TEST_LOCKOUT_MINUTES=15
export SECURITY_TEST_VERBOSE=true

# Target configuration
export SECURITY_TEST_TARGET_URL=http://localhost:8000
export SECURITY_TEST_API_KEY=test_key_123
```

### Security Test Integration with CI/CD

#### GitHub Actions Security Testing
```yaml
# .github/workflows/security.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install bandit safety

    - name: Run security tests
      run: python tests/security/run_security_tests.py --output security_results.json

    - name: Upload security results
      uses: actions/upload-artifact@v2
      with:
        name: security-results
        path: security_results.json

    - name: Check for critical vulnerabilities
      run: |
        CRITICAL=$(cat security_results.json | jq '.summary.vulnerability_counts.CRITICAL')
        if [ "$CRITICAL" -gt 0 ]; then
          echo "Critical vulnerabilities found: $CRITICAL"
          exit 1
        fi
```

### Security Testing Best Practices

#### Regular Security Testing Schedule
1. **Every PR**: Run basic security tests
2. **Daily**: Automated vulnerability scanning
3. **Weekly**: Full penetration testing
4. **Monthly**: Comprehensive security audit

#### Security Test Maintenance
1. **Update Dependencies**: Keep security tools updated
2. **Review False Positives**: Regularly review and update exclusions
3. **Monitor New Threats**: Stay updated with latest security threats
4. **Document Findings**: Maintain security testing documentation

#### Handling Security Test Failures
1. **Triage Vulnerabilities**: Assess severity and impact
2. **Create Issues**: Document security findings
3. **Implement Fixes**: Address critical and high-severity issues
4. **Update Tests**: Improve test coverage for new vulnerabilities

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