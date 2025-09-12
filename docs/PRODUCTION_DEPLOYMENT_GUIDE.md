
# ProxyAPI Production Deployment Guide

Complete guide for deploying ProxyAPI to production environments with comprehensive coverage of containerization, orchestration, cloud platforms, security, monitoring, and operational procedures.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Docker Containerization](#docker-containerization)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platform Deployments](#cloud-platform-deployments)
- [Production Configuration](#production-configuration)
- [Environment-Specific Configurations](#environment-specific-configurations)
- [Scaling Strategies](#scaling-strategies)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Disaster Recovery](#backup-and-disaster-recovery)
- [Step-by-Step Deployment Guides](#step-by-step-deployment-guides)
- [Security Hardening](#security-hardening)
- [CI/CD Pipelines](#ci-cd-pipelines)
- [Deployment Strategies](#deployment-strategies)
- [Rollback Procedures](#rollback-procedures)
- [Production Troubleshooting](#production-troubleshooting)
- [Operational Best Practices](#operational-best-practices)

## Overview

ProxyAPI is a high-performance LLM proxy and discovery platform designed for production use. This guide covers all aspects of production deployment, from containerization to operational procedures.

### Key Production Features

- **High Availability**: Multi-instance deployment with automatic failover
- **Performance**: Optimized HTTP client with connection pooling and caching
- **Security**: Comprehensive authentication, rate limiting, and input validation
- **Monitoring**: Built-in Prometheus metrics and health checks
- **Scalability**: Horizontal scaling with load balancing
- **Reliability**: Circuit breakers, retries, and graceful degradation

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, CentOS 7+, RHEL 8+)
- **Python**: 3.11 or higher
- **Memory**: Minimum 2GB RAM, recommended 4GB+
- **Storage**: 10GB+ for application and logs
- **Network**: Stable internet connection

### Required Software

```bash
# Core dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv git curl wget

# Docker (if using containers)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### API Keys and Credentials

Collect all required API keys before deployment:

```bash
# Required API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export AZURE_OPENAI_KEY="your-azure-key"  # if using Azure
export PROXY_API_PROXY_API_KEYS="prod-key-1,prod-key-2"
```

## Docker Containerization

### Dockerfile

Create a production-ready Dockerfile:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
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
RUN mkdir -p logs cache metrics && \
    chown -R app:app /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER app

# Expose ports
EXPOSE 8000 9090

# Start application
CMD ["python", "main.py"]
```

### Multi-stage Build (Optimized)

For smaller production images:

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash app

COPY --from=builder /root/.local /home/app/.local
COPY . /app

RUN mkdir -p logs cache metrics && \
    chown -R app:app /app

USER app
ENV PATH=/home/app/.local/bin:$PATH

EXPOSE 8000 9090
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]
```

### Docker Compose for Development

```yaml
version: '3.8'

services:
  proxyapi:
    build: .
    ports:
      - "8000:8000"
      - "9090:9090"
    environment:
      - ENVIRONMENT=production
      - HOST=0.0.0.0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - PROXY_API_PROXY_API_KEYS=dev-key-123
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

### Building and Running

```bash
# Build the image
docker build -t proxyapi:latest .

# Run with environment variables
docker run -d \
  --name proxyapi \
  -p 8000:8000 \
  -p 9090:9090 \
  -e OPENAI_API_KEY="your-key" \
  -e ENVIRONMENT=production \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  proxyapi:latest

# Check logs
docker logs -f proxyapi

# Check health
curl http://localhost:8000/health
```

## Kubernetes Deployment

### Namespace and Resources

Create dedicated namespace:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: proxyapi
  labels:
    name: proxyapi
```

### ConfigMaps and Secrets

```yaml
# ConfigMap for application configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: proxyapi-config
  namespace: proxyapi
data:
  config.yaml: |
    providers:
      - name: "openai"
        type: "openai"
        base_url: "https://api.openai.com/v1"
        api_key_env: "OPENAI_API_KEY"
        models: ["gpt-3.5-turbo", "gpt-4"]
        enabled: true
        priority: 1
        timeout: 30
        rate_limit: 2000
        retry_attempts: 3
        max_connections: 200
        max_keepalive_connections: 100

      - name: "anthropic"
        type: "anthropic"
        base_url: "https://api.anthropic.com"
        api_key_env: "ANTHROPIC_API_KEY"
        models: ["claude-3-sonnet", "claude-3-opus"]
        enabled: true
        priority: 2
        timeout: 30
        rate_limit: 100
        retry_attempts: 3

    condensation:
      max_tokens_default: 512
      error_keywords: ["context_length_exceeded", "maximum context length"]
      adaptive_factor: 0.5
      cache_ttl: 1800

---
# Secret for API keys
apiVersion: v1
kind: Secret
metadata:
  name: proxyapi-secrets
  namespace: proxyapi
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  anthropic-api-key: <base64-encoded-key>
  proxy-api-keys: <base64-encoded-keys>
```

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: proxyapi
  namespace: proxyapi
  labels:
    app: proxyapi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: proxyapi
  template:
    metadata:
      labels:
        app: proxyapi
    spec:
      containers:
      - name: proxyapi
        image: your-registry/proxyapi:latest
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: HOST
          value: "0.0.0.0"
        - name: WORKERS
          value: "2"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: proxyapi-secrets
              key: openai-api-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: proxyapi-secrets
              key: anthropic-api-key
        - name: PROXY_API_PROXY_API_KEYS
          valueFrom:
            secretKeyRef:
              name: proxyapi-secrets
              key: proxy-api-keys
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
          readOnly: true
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: config
        configMap:
          name: proxyapi-config
      - name: logs
        emptyDir: {}
```

### Service Manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: proxyapi
  namespace: proxyapi
  labels:
    app: proxyapi
spec:
  selector:
    app: proxyapi
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP
```

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: proxyapi
  namespace: proxyapi
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: proxyapi-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: proxyapi
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: proxyapi-hpa
  namespace: proxyapi
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: proxyapi
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploying to Kubernetes

```bash
# Apply manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml

# Check deployment
kubectl get pods -n proxyapi
kubectl get svc -n proxyapi
kubectl get ingress -n proxyapi

# View logs
kubectl logs -f deployment/proxyapi -n proxyapi

# Scale deployment
kubectl scale deployment proxyapi --replicas=5 -n proxyapi
```

## Cloud Platform Deployments

### AWS ECS Fargate

#### Task Definition

```json
{
  "family": "proxyapi",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "proxyapi",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/proxyapi:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        },
        {
          "containerPort": 9090,
          "hostPort": 9090,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "HOST", "value": "0.0.0.0"},
        {"name": "WORKERS", "value": "2"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:openai-key"
        },
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:anthropic-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/proxyapi",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Application Load Balancer

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'ProxyAPI ALB'

Resources:
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: proxyapi-alb
      Type: application
      Scheme: internet-facing
      SecurityGroups:
        - !Ref LoadBalancerSecurityGroup
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  LoadBalancerListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: !Ref Certificate
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: proxyapi-targets
      Protocol: HTTP
      Port: 8000
      VpcId: !Ref VPC
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 30
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 2
```

### Google Cloud Run

#### Cloud Run Service

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: proxyapi
  namespace: default
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: 'false'
        run.googleapis.com/execution-environment: 'gen2'
    spec:
      containers:
      - image: gcr.io/your-project/proxyapi:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: 'production'
        - name: HOST
          value: '0.0.0.0'
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-key
              key: latest
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: anthropic-key
              key: latest
        resources:
          limits:
            cpu: '2'
            memory: '2Gi'
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          periodSeconds: 10
```

### Azure Container Apps

```yaml
apiVersion: containerapp.azure.com/v1alpha1
kind: ContainerApp
metadata:
  name: proxyapi
  namespace: default
spec:
  app:
    name: proxyapi
    image: your-registry.azurecr.io/proxyapi:latest
    replicas: 3
    scale:
      minReplicas: 3
      maxReplicas: 10
      rules:
      - name: cpu
        type: cpu
        value: 70
      - name: memory
        type: memory
        value: 80
    resources:
      cpu: 0.5
      memory: 1.0Gi
    env:
    - name: ENVIRONMENT
      value: production
    - name: OPENAI_API_KEY
      secretRef: openai-key
    - name: ANTHROPIC_API_KEY
      secretRef: anthropic-key
    probes:
    - type: liveness
      httpGet:
        path: /health/live
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
    - type: readiness
      httpGet:
        path: /health/ready
        port: 8000
      periodSeconds: 5
  secrets:
  - name: openai-key
    value: your-openai-key
  - name: anthropic-key
    value: your-anthropic-key
```

## Production Configuration

### Production Environment Variables

```bash
# Server Configuration
ENVIRONMENT=production
IS_PRODUCTION=true
HOST=0.0.0.0
PORT=8000
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50

# Performance Tuning
HTTP_MAX_CONNECTIONS=2000
HTTP_MAX_KEEPALIVE=500
HTTP_TIMEOUT=30.0
HTTP_CONNECT_TIMEOUT=10.0
HTTP_RETRY_ATTEMPTS=3

# Caching
RESPONSE_CACHE_SIZE=10000
RESPONSE_CACHE_TTL=1800
SUMMARY_CACHE_SIZE=2000
SUMMARY_CACHE_TTL=3600
CACHE_MAX_MEMORY_MB=1024

# Memory Management
MEMORY_THRESHOLD_MB=2048
EMERGENCY_MEMORY_MB=3072
CLEANUP_INTERVAL=300
ENABLE_GC_TUNING=true
LEAK_DETECTION=true

# Security
API_KEYS_REQUIRED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem

# Logging
LOG_LEVEL=WARNING
LOG_MAX_SIZE=500
LOG_BACKUP_COUNT=30
LOG_JSON_FORMAT=true

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
ALERT_CPU_THRESHOLD=80.0
ALERT_MEMORY_THRESHOLD=85.0

# External Services
REDIS_URL=redis://production-redis:6379
DATABASE_URL=postgresql://user:pass@prod-db:5432/proxyapi
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

### Production YAML Configuration

```yaml
# Production config.yaml
app:
  name: "LLM Proxy API"
  version: "2.0.0"
  environment: "production"
  debug: false

server:
  host: "0.0.0.0"
  port: 8000
  debug: false
  reload: false
  workers: 4
  worker_class: "uvicorn.workers.UvicornWorker"
  max_requests: 1000
  max_requests_jitter: 50

providers:
  - name: "openai-primary"
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
    enabled: true
    priority: 1
    timeout: 30
    rate_limit: 2000
    retry_attempts: 3
    max_connections: 200
    max_keepalive_connections: 100
    keepalive_expiry: 30.0

  - name: "anthropic-fallback"
    type: "anthropic"
    base_url: "https://api.anthropic.com"
    api_key_env: "ANTHROPIC_API_KEY"
    models: ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]
    enabled: true
    priority: 2
    timeout: 30
    rate_limit: 100
    retry_attempts: 3
    max_connections: 100
    max_keepalive_connections: 50

  - name: "azure-backup"
    type: "azure_openai"
    base_url: "https://your-resource.openai.azure.com/"
    api_key_env: "AZURE_OPENAI_KEY"
    models: ["gpt-35-turbo", "gpt-4"]
    enabled: true
    priority: 3
    timeout: 30
    rate_limit: 1000
    retry_attempts: 3

# HTTP Client Performance Settings
http_client:
  timeout: 30
  connect_timeout: 10
  read_timeout: 30
  pool_limits:
    max_connections: 2000
    max_keepalive_connections: 500
    keepalive_timeout: 30

# Advanced Caching Configuration
caching:
  enabled: true
  response_cache:
    max_size_mb: 1000
    ttl: 1800
    compression: true
  summary_cache:
    max_size_mb: 500
    ttl: 3600
    compression: true

# Context Condensation Settings
condensation:
  enabled: true
  truncation_threshold: 8000
  summary_max_tokens: 512
  cache_size: 10000
  cache_ttl: 1800
  cache_persist: true
  adaptive_enabled: true
  adaptive_factor: 0.5
  quality_threshold: 0.8

# Memory Management
memory:
  max_usage_percent: 85
  gc_threshold_percent: 80
  monitoring_interval: 30
  cache_cleanup_interval: 300
  emergency_threshold_percent: 95
  leak_detection:
    enabled: true
    dump_on_high_usage: true
    profile_interval: 300

# Circuit Breaker
circuit_breaker:
  enabled: true
  failure_threshold: 5
  recovery_timeout: 60
  half_open_max_calls: 3
  expected_exception: "ProviderError"
  monitoring:
    enabled: true
    metrics: true
    alerts: true

# Security Configuration
security:
  enforce_https: true
  ssl_verify: true
  rate_limiting:
    enabled: true
    requests_per_minute: 1000
    burst_limit: 100
  cors_origins: ["https://yourdomain.com"]
  trusted_proxies: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

# Logging Configuration
logging:
  level: "WARNING"
  format: "json"
  file: "logs/proxyapi.log"
  max_file_size: "500MB"
  max_files: 30
  rotation: "daily"
  compression: "gzip"
  structured:
    enabled: true
    include_trace_id: true
    include_span_id: true
    include_request_id: true

# Monitoring & Observability
telemetry:
  enabled: true
  service_name: "llm-proxy"
  service_version: "2.0.0"
  jaeger:
    enabled: true
    endpoint: "http://jaeger:14268/api/traces"
  zipkin:
    enabled: true
    endpoint: "http://zipkin:9411/api/v2/spans"
  sampling:
    probability: 0.1
    parent_based: true

metrics:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
    path: "/metrics"
  custom:
    enabled: true
    prefix: "llm_proxy"
    labels:
      environment: "production"
      region: "us-east-1"

# Health Check Configuration
health_check:
  enabled: true
  interval: 30
  timeout: 5
  unhealthy_threshold: 3
  checks:
    providers: true
    cache: true
    database: false
    external_services: true
  endpoints:
    liveness: "/health/live"
    readiness: "/health/ready"
    detailed: "/health"

# Load Testing Configuration
load_testing:
  enabled: false
  tiers:
    light:
      users: 30
      duration: "5m"
      ramp_up: "30s"
      expected_rps: 5
    medium:
      users: 100
      duration: "5m"
      ramp_up: "1m"
      expected_rps: 20
    heavy:
      users: 400
      duration: "15m"
      ramp_up: "5m"
      expected_rps: 80
    extreme:
      users: 1000
      duration: "20m"
      ramp_up: "10m"
      expected_rps: 200

# Chaos Engineering (Testing Only)
chaos_engineering:
  enabled: false
  faults:
    - type: "delay"
      severity: "medium"
      probability: 0.1
      duration_ms: 500
    - type: "error"
      severity: "low"
      probability: 0.05
      error_code: 503
      error_message: "Service temporarily unavailable"
```

## Environment-Specific Configurations

### Development Environment

```yaml
# config.dev.yaml
app:
  environment: "development"
  debug: true

server:
  host: "127.0.0.1"
  port: 8000
  reload: true
  workers: 1

logging:
  level: "INFO"
  format: "text"

caching:
  enabled: false

monitoring:
  enabled: false

chaos_engineering:
  enabled: false
```

### Staging Environment

```yaml
# config.staging.yaml
app:
  environment: "staging"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 2

logging:
  level: "INFO"
  format: "json"

caching:
  response_cache:
    max_size_mb: 100
    ttl: 900

monitoring:
  enabled: true

providers:
  # Use staging API keys
  - name: "openai"
    rate_limit: 500  # Lower limits for staging
```

### Production Environment

```yaml
# config.prod.yaml
app:
  environment: "production"
  debug: false

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  max_requests: 1000

logging:
  level: "WARNING"
  format: "json"
  file: "/var/log/proxyapi/app.log"

caching:
  response_cache:
    max_size_mb: 1000
    ttl: 1800

monitoring:
  enabled: true

security:
  enforce_https: true
  rate_limiting:
    requests_per_minute: 1000

providers:
  # Production API keys with higher limits
  - name: "openai"
    rate_limit: 2000
```

### Configuration Management Script

```python
# config_manager.py
import os
from pathlib import Path
from typing import Dict, Any
import yaml

class ConfigManager:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.environment = os.getenv("ENVIRONMENT", "development")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration based on environment"""
        config_files = [
            self.base_path / "config.yaml",  # Base config
            self.base_path / f"config.{self.environment}.yaml",  # Environment-specific
        ]

        config = {}

        for config_file in config_files:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    config = self._merge_configs(config, file_config)

        # Override with environment variables
        config = self._apply_env_overrides(config)

        return config

    def _merge_configs(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries"""
        merged = base.copy()

        for key, value in overlay.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        env_overrides = {
            "app.debug": os.getenv("DEBUG", "").lower() == "true",
            "server.host": os.getenv("HOST"),
            "server.port": int(os.getenv("PORT", 8000)),
            "caching.enabled": os.getenv("CACHE_ENABLED", "").lower() == "true",
        }

        def set_nested_value(d: Dict[str, Any], keys: str, value: Any):
            keys_list = keys.split(".")
            for key in keys_list[:-1]:
                d = d.setdefault(key, {})
            d[keys_list[-1]] = value

        for key, value in env_overrides.items():
            if value is not None:
                set_nested_value(config, key, value)

        return config

# Usage
config_manager = ConfigManager()
config = config_manager.load_config()
```

## Scaling Strategies

### Horizontal Scaling

#### Kubernetes HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: proxyapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: proxyapi
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_total
      target:
        type: AverageValue
        averageValue: 1000
```

#### AWS Auto Scaling

```json
{
  "AutoScalingGroupName": "proxyapi-asg",
  "MinSize": 3,
  "MaxSize": 20,
  "DesiredCapacity": 5,
  "DefaultCooldown": 300,
  "AvailabilityZones": ["us-east-1a", "us-east-1b", "us-east-1c"],
  "HealthCheckType": "ELB",
  "HealthCheckGracePeriod": 300,
  "LaunchTemplate": {
    "LaunchTemplateName": "proxyapi-lt",
    "Version": "$Latest"
  },
  "TargetGroupARNs": ["arn:aws:elasticloadbalancing:region:account:targetgroup/proxyapi/123456789"]
}
```

### Vertical Scaling

#### Resource Limits

```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### Performance Monitoring for Scaling

```bash
# Monitor current resource usage
kubectl top pods -n proxyapi
kubectl top nodes

# Check HPA status
kubectl get hpa proxyapi-hpa -n proxyapi

# Monitor custom metrics
curl http://localhost:9090/metrics | grep http_requests_total
```

### Load Balancing

#### NGINX Configuration

```nginx
upstream proxyapi_backend {
    least_conn;
    server proxyapi-1:8000 weight=1;
    server proxyapi-2:8000 weight=1;
    server proxyapi-3:8000 weight=1;

    keepalive 32;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://proxyapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # Buffers
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### Database Scaling

#### Redis Cluster Configuration

```yaml
# docker-compose.redis.yaml
version: '3.8'

services:
  redis-cluster:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file /data/nodes.conf --cluster-node-timeout 5000
    ports:
      - "7001:7001"
    volumes:
      - redis-data:/data
    networks:
      - proxyapi-network

  redis-sentinel:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    ports:
      - "26379:26379"
    volumes:
      - ./redis/sentinel.conf:/etc/redis/sentinel.conf
    depends_on:
      - redis-cluster
    networks:
      - proxyapi-network

volumes:
  redis-data:

networks:
  proxyapi-network:
    driver: bridge
```

### Caching Strategies

#### Multi-level Caching

```python
from cachetools import TTLCache, LRUCache
from diskcache import Cache
import redis

class MultiLevelCache:
    def __init__(self):
        # L1: Memory cache
        self.memory_cache = TTLCache(maxsize=10000, ttl=1800)

        # L2: Disk cache
        self.disk_cache = Cache('/app/cache/disk')

        # L3: Redis cache
        self.redis_cache = redis.Redis(host='redis', port=6379, db=0)

    def get(self, key: str) -> Any:
        # Try memory first
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Try disk cache
        if key in self.disk_cache:
            value = self.disk_cache[key]
            self.memory_cache[key] = value  # Promote to memory
            return value

        # Try Redis
        value = self.redis_cache.get(key)
        if value:
            self.memory_cache[key] = value  # Promote to memory
            self.disk_cache[key] = value    # Promote to disk
            return value

        return None

    def set(self, key: str, value: Any, ttl: int = 1800):
        self.memory_cache[key] = value
        self.disk_cache.set(key, value, expire=ttl)
        self.redis_cache.setex(key, ttl, value)
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'proxyapi'
    static_configs:
      - targets: ['proxyapi:9090']
    scrape_interval: 5s
    metrics_path: '/metrics'

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
```

### Grafana Dashboard

Import the pre-configured dashboard from `monitoring/grafana-dashboard.json`:

```json
{
  "dashboard": {
    "title": "ProxyAPI Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "cache_hits_total / (cache_hits_total + cache_misses_total) * 100",
            "legendFormat": "Hit Rate %"
          }
        ]
      }
    ]
  }
}
```

### Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: proxyapi_alerts
    rules:
      - alert: ProxyAPIHighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on ProxyAPI"
          description: "Error rate is {{ $value }}% (threshold: 5%)"

      - alert: ProxyAPIHighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on ProxyAPI"
          description: "95th percentile latency is {{ $value }}s (threshold: 5s)"

      - alert: ProxyAPIDown
        expr: up{job="proxyapi"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "ProxyAPI is down"
          description: "ProxyAPI has been down for more than 2 minutes"

      - alert: ProxyAPIHighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"

      - alert: ProxyAPIHighCPUUsage
        expr: rate(node_cpu_seconds_total{mode="idle"}[5m]) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 90%"
```

### Health Checks

```python
# health.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import psutil
import asyncio

router = APIRouter()

class HealthChecker:
    def __init__(self):
        self.start_time = time.time()

    async def check_providers(self) -> Dict[str, Any]:
        """Check provider connectivity"""
        results = {}
        providers = ["openai", "anthropic"]  # Add your providers

        for provider in providers:
            try:
                # Implement provider health check
                results[provider] = {
                    "status": "healthy",
                    "response_time": 0.1,
                    "last_check": time.time()
                }
            except Exception as e:
                results[provider] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": time.time()
                }

        return results

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu = psutil.cpu_percent(interval=1)

        return {
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "status": "healthy" if memory.percent < 90 else "warning"
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent,
                "status": "healthy" if disk.percent < 90 else "warning"
            },
            "cpu": {
                "percent": cpu,
                "status": "healthy" if cpu < 90 else "warning"
            }
        }

    def check_cache_health(self) -> Dict[str, Any]:
        """Check cache health"""
        try:
            # Implement cache health check
            return {
                "status": "healthy",
                "size": 1000,
                "hit_rate": 0.95
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        providers = await self.check_providers()
        system = self.check_system_resources()
        cache = self.check_cache_health()

        # Determine overall health
        unhealthy_components = []
        for component, checks in [("providers", providers), ("system", system), ("cache", cache)]:
            if isinstance(checks, dict) and any(
                check.get("status") == "unhealthy" for check in checks.values() if isinstance(check, dict)
            ):
                unhealthy_components.append(component)

        overall_status = "unhealthy" if unhealthy_components else "healthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "uptime": time.time() - self.start_time,
            "version": "2.0.0",
            "components": {
                "providers": providers,
                "system": system,
                "cache": cache
            },
            "unhealthy_components": unhealthy_components
        }

health_checker = HealthChecker()

@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe"""
    health = await health_checker.comprehensive_health_check()
    if health["status"] != "healthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}

@router.get("/health")
async def detailed_health():
    """Detailed health check"""
    return await health_checker.comprehensive_health_check()
```

## Backup and Disaster Recovery

### Configuration Backup

```bash
#!/bin/bash
# backup.sh - Daily backup script

BACKUP_DIR="/opt/proxyapi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configurations
tar -czf $BACKUP_DIR/config_$DATE.tar