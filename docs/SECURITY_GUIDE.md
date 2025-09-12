# ProxyAPI Security Guide

## Overview

This comprehensive security guide covers the authentication system, API key management, rate limiting implementation, input validation, data protection mechanisms, security monitoring, and best practices for the ProxyAPI project. The guide includes detailed documentation of security features, implementation details, and production deployment guidelines.

## Table of Contents

- [Authentication System](#authentication-system)
- [API Key Management](#api-key-management)
- [Rate Limiting](#rate-limiting)
- [Input Validation & Sanitization](#input-validation--sanitization)
- [Data Protection Mechanisms](#data-protection-mechanisms)
- [Security Monitoring](#security-monitoring)
- [Code Review Security Fixes](#code-review-security-fixes)
- [Security Hardening Guidelines](#security-hardening-guidelines)
- [Threat Modeling](#threat-modeling)
- [Compliance Considerations](#compliance-considerations)
- [Incident Response Procedures](#incident-response-procedures)
- [Security Testing Procedures](#security-testing-procedures)
- [Vulnerability Assessment](#vulnerability-assessment)
- [Security Monitoring Tools](#security-monitoring-tools)
- [Production Deployment Best Practices](#production-deployment-best-practices)

## Authentication System

### API Key Authentication Implementation

The ProxyAPI implements a robust API key authentication system with timing attack protection and secure key management.

#### Core Components

**APIKeyAuth Class** (`src/core/auth.py`)
```python
class APIKeyAuth:
    """API Key authentication with timing attack protection"""

    def __init__(self, api_keys: list[str]):
        self.valid_api_key_hashes = self._load_api_keys(api_keys)

    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key securely with timing attack protection"""
        if not api_key or not self.valid_api_key_hashes:
            return False

        # Hash the provided key to compare with stored hashes
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Securely compare using secrets.compare_digest to prevent timing attacks
        is_valid = False
        for valid_hash in self.valid_api_key_hashes:
            if secrets.compare_digest(key_hash, valid_hash):
                is_valid = True
                break

        return is_valid
```

#### Timing Attack Protection

The authentication system uses `secrets.compare_digest()` to prevent timing attacks:

- **Secure Comparison**: Uses constant-time comparison regardless of key length
- **Hash Storage**: Stores SHA-256 hashes of API keys, never plaintext keys
- **Comprehensive Testing**: Includes timing attack resistance tests in `tests/security/test_authentication_security.py`

#### Authentication Flow

1. **Header Extraction**: Supports both `Authorization: Bearer <key>` and custom headers
2. **Key Verification**: Secure hash comparison with timing attack protection
3. **Logging**: Secure logging with API key masking
4. **Error Handling**: Proper HTTP 401 responses without information leakage

## API Key Management

### Secure API Key Storage

#### Hash-Based Storage
```python
def _load_api_keys(self, api_keys: list[str]) -> set[str]:
    """Load and hash API keys"""
    hashed_keys = set()
    for key in api_keys:
        if key:
            hashed_keys.add(hashlib.sha256(key.encode()).hexdigest())
    return hashed_keys
```

### API Key Masking in Logs

#### ContextualLogger Implementation
The system implements comprehensive API key masking in all log outputs:

```python
def mask_secrets(text: str) -> str:
    """Mask sensitive information in log messages"""
    patterns = [
        # OpenAI API keys: sk-... (keep first 3 and last 3 chars)
        (r'\b(sk-[a-zA-Z0-9]{3})[a-zA-Z0-9]{30,}([a-zA-Z0-9]{3})\b', r'\1***\2'),
        # Generic API keys with prefixes
        (r'\b(api[_-]?key[_-]?[:=]\s*)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        (r'\b(token[_-]?[:=]\s*)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        (r'\b(secret[_-]?[:=]\s*)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        # Authorization headers
        (r'\b(Bearer\s+)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        # Password patterns
        (r'\b(password[_-]?[:=]\s*)[^\s]{3,}\b', r'\1***MASKED***'),
    ]

    masked_text = text
    for pattern, replacement in patterns:
        masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)

    return masked_text
```

#### Masking Patterns
- **OpenAI Keys**: `sk-abc...xyz` → `sk-abc***xyz`
- **Bearer Tokens**: `Bearer abc123...` → `Bearer ***MASKED***`
- **Generic Tokens**: All sensitive patterns masked with `***MASKED***`

### API Key Rotation

The system supports API key rotation with graceful transitions:

```python
def test_api_key_rotation_simulation(self):
    """Test API key rotation mechanisms"""
    old_keys = ["old_key_1", "old_key_2"]
    new_keys = ["new_key_1", "new_key_2"]

    # During transition, both old and new keys work
    auth = APIKeyAuth(old_keys + new_keys)

    # After rotation, only new keys are valid
    auth_rotated = APIKeyAuth(new_keys)
```

## Rate Limiting

### Implementation Architecture

The ProxyAPI implements multi-level rate limiting using the `slowapi` library:

#### RateLimiter Class (`packages/proxy_core/src/proxy_core/rate_limiter.py`)

```python
class RateLimiter:
    """Enhanced rate limiter with global, per-provider, and fallback strategies"""

    def __init__(self):
        self.limiter = Limiter(key_func=get_remote_address)
        self._default_limit = "100/minute"
        self._global_limits: Dict[str, str] = {}
        self._provider_limits: Dict[str, str] = {}
        self._fallback_strategies: Dict[str, Any] = {}
```

#### Rate Limiting Features

1. **Global Limits**: Default rate limits applied to all requests
2. **Per-Provider Limits**: Provider-specific rate limiting
3. **Fallback Strategies**: Graceful handling of rate limit exceeded scenarios
4. **Dynamic Configuration**: Runtime configuration updates

#### Configuration Example

```python
# Configure from settings
def configure_from_config(self, config: Any):
    settings = config.settings if hasattr(config, 'settings') else config

    # Global rate limits
    if hasattr(settings, 'rate_limit_rpm'):
        self._default_limit = f"{settings.rate_limit_rpm}/minute"

    # Provider-specific limits
    if hasattr(config, 'providers'):
        for provider in config.providers:
            if hasattr(provider, 'rate_limit') and provider.rate_limit:
                self._provider_limits[provider.name] = f"{provider.rate_limit}/hour"
```

#### Fallback Strategies

```python
async def _handle_rate_limit_exceeded(self, func: Callable, provider: str, *args, **kwargs):
    """Handle rate limit exceeded with fallback strategies"""
    logger.warning("Rate limit exceeded", provider=provider, function=func.__name__)

    # Apply fallback strategies
    if "secondary_provider" in self._fallback_strategies:
        logger.info("Applying secondary provider fallback", provider=provider)
        # Switch to secondary provider

    if "delay" in self._fallback_strategies:
        delay = self._fallback_strategies["delay"]
        logger.info(f"Applying delay fallback: {delay}s", provider=provider)
        await asyncio.sleep(delay)
        return await func(*args, **kwargs)

    # Default: return rate limit error
    raise RateLimitExceeded("Rate limit exceeded")
```

## Input Validation & Sanitization

### Request Validation Middleware

The system implements comprehensive input validation through middleware:

#### RequestValidator (`src/api/validation/request_validator.py`)

```python
class RequestValidator:
    """Centralized request validation and sanitization."""

    async def validate_chat_completion_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize chat completion request."""
        try:
            # Validate and sanitize messages
            sanitized_messages = []
            for i, msg in enumerate(messages):
                # Validate message structure
                role = msg.get('role', '')
                content = msg.get('content', '')

                # Sanitize content
                sanitized_content = self._sanitize_text(content)
                sanitized_messages.append({
                    'role': role,
                    'content': sanitized_content
                })

            # Validate temperature
            if 'temperature' in sanitized_request:
                temp = sanitized_request['temperature']
                if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                    raise InvalidRequestError("Temperature must be between 0 and 2")

            return sanitized_request
        except Exception as e:
            raise InvalidRequestError(f"Request validation failed: {str(e)}")
```

#### Content Sanitization

```python
def _sanitize_text(self, text: str) -> str:
    """Sanitize text content for security."""
    if not isinstance(text, str):
        return str(text)

    # Remove or escape potentially dangerous content
    # Implement HTML escaping, remove script tags, etc.
    import html
    sanitized = html.escape(text)

    # Additional sanitization rules
    # Remove null bytes, control characters, etc.
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)

    return sanitized
```

### Response Validation

The system also validates and sanitizes API responses before sending them to clients:

#### ResponseValidator (`src/api/validation/response_validator.py`)

```python
class ResponseValidator:
    """Centralized response validation and formatting."""

    def _sanitize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive information from response."""
        def sanitize_value(value: Any) -> Any:
            if isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()
                       if k.lower() not in self.sensitive_fields}
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            else:
                return value

        return sanitize_value(response)
```

## Data Protection Mechanisms

### Secure Logging Practices

All logging in the ProxyAPI follows secure practices:

#### ContextualLogger (`src/core/logging.py`)

```python
class ContextualLogger:
    """Logger with request context and automatic secret masking"""

    def _log_with_context(self, level: int, msg: str, extra_data: Dict[str, Any] = None):
        # Mask sensitive information in the message
        masked_msg = mask_secrets(msg)

        # Also mask sensitive information in extra_data values
        masked_extra_data = extra_data or {}
        if masked_extra_data:
            masked_extra_data = {}
            for key, value in (extra_data or {}).items():
                if isinstance(value, str):
                    masked_extra_data[key] = mask_secrets(value)
                else:
                    masked_extra_data[key] = value

        extra = {"extra_data": {**self.context, **masked_extra_data}}
        self.logger.log(level, masked_msg, extra=extra)
```

### HTTP Client Security

The optimized HTTP client includes security features:

#### OptimizedHTTPClient (`packages/proxy_core/src/proxy_core/http_client.py`)

```python
class OptimizedHTTPClient:
    """Production-ready HTTP client with security features"""

    def __init__(
        self,
        timeout: float = 30.0,
        connect_timeout: float = 10.0,
        # ... other params
    ):
        # Circuit breaker integration
        self.circuit_breaker = circuit_breaker

        # Initialize client with security settings
        self._client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
            http2=True  # HTTP/2 for better security
        )
```

## Security Monitoring

### OpenTelemetry Integration

The system includes distributed tracing and metrics:

#### OpenTelemetryConfig (`packages/proxy_logging/src/proxy_logging/opentelemetry_config.py`)

```python
class OpenTelemetryConfig:
    """Configuration for OpenTelemetry tracing and metrics."""

    def configure(self) -> bool:
        """Configure OpenTelemetry if available."""
        try:
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: self.service_version,
            })

            provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(provider)

            # Configure OTLP exporter for external monitoring
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            if otlp_endpoint:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                span_processor = BatchSpanProcessor(otlp_exporter)
                provider.add_span_processor(span_processor)

            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to configure OpenTelemetry: {e}")
            return False
```

### Prometheus Metrics

Comprehensive metrics collection for monitoring:

#### PrometheusExporter (`packages/proxy_logging/src/proxy_logging/prometheus_exporter.py`)

```python
class PrometheusExporter:
    """Prometheus metrics exporter for the proxy API."""

    def _setup_metrics(self) -> None:
        """Setup Prometheus metrics."""
        # Request metrics
        self.request_count = Counter(
            'proxy_api_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        # Provider metrics
        self.provider_requests = Counter(
            'proxy_api_provider_requests_total',
            'Total provider requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )

        # Security metrics
        self.failed_auth_attempts = Counter(
            'proxy_api_failed_auth_attempts_total',
            'Total failed authentication attempts',
            ['reason'],
            registry=self.registry
        )
```

### Structured Logging

JSON-formatted logging for better monitoring:

#### StructuredLogger (`packages/proxy_logging/src/proxy_logging/structured_logger.py`)

```python
class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra data
        if hasattr(record, "extra_data"):
            log_entry["extra_data"] = record.extra_data

        return json.dumps(log_entry, ensure_ascii=False)
```

## Code Review Security Fixes

### Timing Attack Protection

**Issue**: API key verification was vulnerable to timing attacks.

**Fix**: Implemented constant-time comparison using `secrets.compare_digest()`:

```python
# Before (vulnerable to timing attacks)
if key_hash == valid_hash:
    return True

# After (timing attack resistant)
if secrets.compare_digest(key_hash, valid_hash):
    return True
```

### API Key Masking

**Issue**: Sensitive API keys were being logged in plaintext.

**Fix**: Implemented comprehensive secret masking in all log outputs:

```python
def mask_secrets(text: str) -> str:
    """Mask sensitive information in log messages"""
    # Implementation with regex patterns for various secret types
    patterns = [
        (r'\b(sk-[a-zA-Z0-9]{3})[a-zA-Z0-9]{30,}([a-zA-Z0-9]{3})\b', r'\1***\2'),
        (r'\b(api[_-]?key[_-]?[:=]\s*)[a-zA-Z0-9]{10,}\b', r'\1***MASKED***'),
        # ... additional patterns
    ]
```

### Secure Logging Practices

**Issue**: Error messages could leak sensitive information.

**Fix**: Added sanitization to error handlers and logging:

```python
def _sanitize_error_message(self, message: str) -> str:
    """Sanitize error message to prevent information leakage."""
    # Remove sensitive patterns from error messages
    sanitized = mask_secrets(message)
    # Additional sanitization rules
    return sanitized
```

## Security Hardening Guidelines

### Production Configuration

1. **Environment Variables**: Never store secrets in code
```bash
export API_KEY="your-secure-api-key"
export LOG_LEVEL="WARNING"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://your-monitoring-endpoint"
```

2. **HTTPS Enforcement**: Always use HTTPS in production
```python
# FastAPI configuration
app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)
```

3. **Rate Limiting Configuration**:
```yaml
# config.yaml
settings:
  rate_limit_rpm: 60
  max_concurrent_requests: 100

providers:
  - name: openai
    rate_limit: 50  # requests per hour
```

4. **Logging Configuration**:
```python
# Secure logging setup
setup_logging(
    log_level="WARNING",
    log_file=Path("/var/log/proxy-api/secure.log"),
    enable_json=True,
    mask_secrets=True
)
```

### Network Security

1. **Firewall Configuration**:
   - Restrict incoming connections to necessary ports only
   - Use security groups to limit access to trusted IPs
   - Implement WAF (Web Application Firewall) rules

2. **TLS Configuration**:
   - Use TLS 1.3
   - Implement HSTS headers
   - Regular certificate renewal

### Access Control

1. **Principle of Least Privilege**:
   - API keys with minimal required permissions
   - Read-only keys for monitoring
   - Time-limited tokens for temporary access

2. **Multi-Factor Authentication**:
   - Consider implementing MFA for admin operations
   - Use hardware security keys where possible

## Threat Modeling

### STRIDE Threat Analysis

#### Spoofing
- **Threat**: API key theft or forgery
- **Mitigation**: SHA-256 hashing, timing attack protection, secure key storage
- **Detection**: Failed authentication monitoring

#### Tampering
- **Threat**: Request/response manipulation
- **Mitigation**: HTTPS enforcement, input validation, response sanitization
- **Detection**: Integrity monitoring, anomaly detection

#### Repudiation
- **Threat**: Denial of actions
- **Mitigation**: Comprehensive audit logging, request tracking
- **Detection**: Log analysis, compliance monitoring

#### Information Disclosure
- **Threat**: Sensitive data leakage
- **Mitigation**: Secret masking, error sanitization, secure logging
- **Detection**: Data loss prevention monitoring

#### Denial of Service
- **Threat**: Resource exhaustion
- **Mitigation**: Rate limiting, circuit breakers, resource limits
- **Detection**: Performance monitoring, automated scaling

#### Elevation of Privilege
- **Threat**: Unauthorized access escalation
- **Mitigation**: Role-based access control, least privilege principle
- **Detection**: Access pattern analysis, anomaly detection

### Attack Surface Analysis

#### External Interfaces
- REST API endpoints
- WebSocket connections (if implemented)
- Monitoring interfaces
- Administrative interfaces

#### Internal Components
- Provider integrations
- Cache systems
- Database connections
- Message queues

## Compliance Considerations

### GDPR Compliance

1. **Data Minimization**:
   - Collect only necessary data
   - Implement data retention policies
   - Regular data cleanup procedures

2. **Right to Access/Erasure**:
   - User data access endpoints
   - Data deletion procedures
   - Audit trails for data operations

3. **Data Protection**:
   - Encryption at rest and in transit
   - Secure logging practices
   - Access control implementation

### Security Audit Logging

```python
class AuditLogger:
    """GDPR-compliant audit logging"""

    def log_data_access(self, user_id: str, data_type: str, action: str):
        """Log data access for compliance"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "data_type": data_type,
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }
        self._write_audit_log(audit_entry)
```

## Incident Response Procedures

### Incident Response Plan

1. **Detection Phase**:
   - Monitor security alerts and anomalies
   - Review authentication failures
   - Check rate limiting violations
   - Analyze error patterns

2. **Assessment Phase**:
   - Determine incident scope and impact
   - Identify affected systems and data
   - Assess potential data exposure
   - Document findings

3. **Containment Phase**:
   - Isolate affected systems
   - Block malicious traffic
   - Rotate compromised credentials
   - Implement emergency rate limiting

4. **Recovery Phase**:
   - Restore systems from clean backups
   - Validate system integrity
   - Monitor for recurrence
   - Document recovery procedures

5. **Lessons Learned Phase**:
   - Conduct post-mortem analysis
   - Update security measures
   - Improve monitoring and detection
   - Update incident response procedures

### Automated Response Actions

```python
class IncidentResponder:
    """Automated incident response system"""

    def handle_brute_force_attack(self, ip_address: str):
        """Respond to brute force attack"""
        # Block IP address
        self._block_ip(ip_address)

        # Notify security team
        self._send_alert("Brute force attack detected", {
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            "action": "IP blocked"
        })

        # Log incident
        self._log_incident("brute_force", ip_address)
```

## Security Testing Procedures

### Authentication Security Tests

#### Timing Attack Resistance Test

```python
def test_timing_attack_resistance_comprehensive(self):
    """Comprehensive test for timing attack resistance"""
    api_keys = ["short_key", "a_very_long_key_that_should_take_similar_time_to_verify"]
    auth = APIKeyAuth(api_keys)

    test_keys = [
        "a", "medium_length_key", "a_very_long_key_that_should_have_similar_timing_characteristics",
        "", "special_chars_!@#$%^&*()", "unicode_key_🚀_test"
    ]

    times = []
    for key in test_keys:
        start_time = time.perf_counter()
        auth.verify_api_key(key)
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    # Verify timing consistency
    avg_time = sum(times) / len(times)
    max_deviation = max(abs(t - avg_time) for t in times)
    relative_deviation = max_deviation / avg_time if avg_time > 0 else 0

    assert relative_deviation < 0.1, f"Timing attack vulnerability: {relative_deviation:.3f}"
```

#### Brute Force Protection Test

```python
def test_brute_force_protection(self):
    """Test protection against brute force attacks"""
    api_keys = ["valid_key_123"]
    auth = APIKeyAuth(api_keys)

    # Simulate multiple failed attempts
    failed_attempts = 0
    max_attempts = 100

    for i in range(max_attempts):
        result = auth.verify_api_key(f"invalid_key_{i}")
        if not result:
            failed_attempts += 1

    assert failed_attempts == max_attempts
    assert auth.verify_api_key("valid_key_123") is True
```

### Input Validation Security Tests

#### SQL Injection Prevention

```python
def test_sql_injection_prevention(self):
    """Test SQL injection prevention"""
    dangerous_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "admin' --",
        "1' OR '1' = '1"
    ]

    for payload in dangerous_payloads:
        # Simulate input validation
        sanitized = sanitize_sql_input(payload)
        assert "'" not in sanitized or payload != sanitized
        assert ";" not in sanitized or payload != sanitized
```

#### XSS Prevention

```python
def test_xss_prevention(self):
    """Test cross-site scripting prevention"""
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(\"XSS\")'>",
        "<svg onload=alert('XSS')>"
    ]

    for payload in xss_payloads:
        sanitized = sanitize_html_input(payload)
        assert '<script>' not in sanitized.lower()
        assert 'javascript:' not in sanitized.lower()
        assert 'onerror' not in sanitized.lower()
        assert 'onload' not in sanitized.lower()
```

### Penetration Testing

```python
class TestPenetrationTesting:
    """Automated penetration testing capabilities"""

    def test_api_endpoint_security(self):
        """Test API endpoint security"""
        endpoints_to_test = [
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/models",
            "/health",
            "/metrics"
        ]

        for endpoint in endpoints_to_test:
            # Test various attack vectors
            self._test_sql_injection(endpoint)
            self._test_xss(endpoint)
            self._test_command_injection(endpoint)
            self._test_directory_traversal(endpoint)
            self._test_authentication_bypass(endpoint)
```

## Vulnerability Assessment

### Automated Vulnerability Scanning

```python
class VulnerabilityScanner:
    """Automated vulnerability assessment"""

    def scan_dependencies(self):
        """Scan for vulnerable dependencies"""
        # Use safety or similar tools
        vulnerable_packages = self._check_package_vulnerabilities()

        for package, vulnerabilities in vulnerable_packages.items():
            for vuln in vulnerabilities:
                self._report_vulnerability({
                    "package": package,
                    "vulnerability_id": vuln["id"],
                    "severity": vuln["severity"],
                    "description": vuln["description"],
                    "fix_available": vuln["fix_available"]
                })

    def scan_configuration(self):
        """Scan configuration for security issues"""
        # Check for insecure configurations
        issues = []

        if self._is_debug_enabled():
            issues.append({
                "type": "debug_enabled",
                "severity": "medium",
                "description": "Debug mode is enabled in production"
            })

        if not self._is_https_enforced():
            issues.append({
                "type": "no_https",
                "severity": "high",
                "description": "HTTPS is not enforced"
            })

        return issues

    def scan_code_security(self):
        """Scan code for security issues"""
        # Use bandit or similar tools
        security_issues = self._run_bandit_scan()

        for issue in security_issues:
            self._report_security_issue({
                "file": issue["file"],
                "line": issue["line"],
                "issue_type": issue["test_id"],
                "severity": issue["severity"],
                "description": issue["issue_text"]
            })
```

### Security Health Check

```python
def security_health_check():
    """Comprehensive security health assessment"""
    health_status = {
        "overall_score": 0,
        "categories": {},
        "recommendations": []
    }

    # Authentication security
    auth_score = check_authentication_security()
    health_status["categories"]["authentication"] = auth_score

    # Input validation
    validation_score = check_input_validation()
    health_status["categories"]["input_validation"] = validation_score

    # Configuration security
    config_score = check_configuration_security()
    health_status["categories"]["configuration"] = config_score

    # Calculate overall score
    health_status["overall_score"] = (
        auth_score * 0.4 +
        validation_score * 0.3 +
        config_score * 0.3
    )

    return health_status
```

## Security Monitoring Tools

### Log Analysis Tools

```python
class SecurityLogAnalyzer:
    """Analyze logs for security events"""

    def analyze_authentication_failures(self, logs):
        """Analyze authentication failure patterns"""
        failure_patterns = {}

        for log_entry in logs:
            if log_entry.get("event") == "auth_failure":
                ip = log_entry.get("ip_address")
                if ip not in failure_patterns:
                    failure_patterns[ip] = {
                        "count": 0,
                        "timestamps": [],
                        "user_agents": set()
                    }

                failure_patterns[ip]["count"] += 1
                failure_patterns[ip]["timestamps"].append(log_entry["timestamp"])
                failure_patterns[ip]["user_agents"].add(log_entry.get("user_agent", ""))

        # Detect brute force attacks
        brute_force_ips = []
        for ip, data in failure_patterns.items():
            if data["count"] > 10:  # Threshold for brute force detection
                time_window = 3600  # 1 hour
                recent_failures = [
                    ts for ts in data["timestamps"]
                    if datetime.fromisoformat(ts).timestamp() > time.time() - time_window
                ]
                if len(recent_failures) > 5:
                    brute_force_ips.append(ip)

        return brute_force_ips

    def detect_anomalous_activity(self, logs):
        """Detect anomalous user behavior"""
        # Implement anomaly detection algorithms
        pass
```

### Real-time Security Monitoring

```python
class SecurityMonitor:
    """Real-time security monitoring"""

    def __init__(self):
        self.alerts = []
        self.metrics = {}

    def monitor_authentication_attempts(self, success: bool, ip_address: str):
        """Monitor authentication attempts"""
        key = f"auth_attempts_{ip_address}"

        if key not in self.metrics:
            self.metrics[key] = {
                "total": 0,
                "success": 0,
                "failure": 0,
                "last_attempt": 0
            }

        self.metrics[key]["total"] += 1
        if success:
            self.metrics[key]["success"] += 1
        else:
            self.metrics[key]["failure"] += 1

        self.metrics[key]["last_attempt"] = time.time()

        # Check for brute force patterns
        failure_rate = self.metrics[key]["failure"] / self.metrics[key]["total"]
        if failure_rate > 0.8 and self.metrics[key]["total"] > 10:
            self._trigger_alert("high_failure_rate", {
                "ip_address": ip_address,
                "failure_rate": failure_rate,
                "total_attempts": self.metrics[key]["total"]
            })

    def monitor_rate_limits(self, endpoint: str, exceeded: bool):
        """Monitor rate limiting"""
        if exceeded:
            self._trigger_alert("rate_limit_exceeded", {
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat()
            })
```

## Production Deployment Best Practices

### Security Configuration Checklist

- [ ] HTTPS/TLS 1.3 enforced
- [ ] Secure headers configured (HSTS, CSP, X-Frame-Options)
- [ ] Rate limiting configured with appropriate limits
- [ ] API keys rotated regularly
- [ ] Logging configured with secret masking
- [ ] Monitoring and alerting set up
- [ ] Backup and recovery procedures documented
- [ ] Incident response plan in place

### Infrastructure Security

#### Docker Security

```dockerfile
# Use minimal base image
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Install dependencies securely
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set proper permissions
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

#### Kubernetes Security

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: proxy-api
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: proxy-api
    image: proxy-api:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    env:
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: proxy-api-secrets
          key: api-key
    resources:
      limits:
        cpu: 500m
        memory: 1Gi
      requests:
        cpu: 100m
        memory: 256Mi
```

### Continuous Security

#### Security Pipeline Integration

```yaml
# .github/workflows/security.yml
name: Security Checks
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Run Bandit Security Linter
      uses: PyCQA/bandit-action@v1
      with:
        path: "."
        options: "-r"

    - name: Run Safety Dependency Check
      uses: Lucas-C/pre-commit-hooks-safety@0.1.1
      with:
        files: requirements.txt

    - name: Run Trivy Vulnerability Scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
```

#### Dependency Vulnerability Management

```python
# requirements-security.txt
safety==2.3.5
bandit==1.7.5
trivy==0.40.0

# Security monitoring
prometheus-client==0.17.1
opentelemetry-distro==0.40b0
opentelemetry-exporter-otlp==1.19.0
```

### Final Security Recommendations

1. **Regular Security Audits**: Conduct quarterly security assessments
2. **Dependency Updates**: Keep all dependencies updated with security patches
3. **Access Reviews**: Regularly review and rotate access credentials
4. **Security Training**: Ensure team members are trained on security best practices
5. **Backup Security**: Encrypt backups and test restoration procedures
6. **Compliance Monitoring**: Regular compliance checks and documentation updates
7. **Incident Drills**: Conduct regular incident response drills
8. **Security Metrics**: Track and improve security metrics over time

This comprehensive security guide provides the foundation for secure deployment and operation of the ProxyAPI. Regular review and updates to security measures are essential to maintain robust protection against evolving threats.

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [GDPR Compliance Guidelines](https://gdpr-info.eu/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)