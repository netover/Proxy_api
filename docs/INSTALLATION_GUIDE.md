# 🚀 Installation Guide - LLM Proxy API

Complete installation and deployment guide for the LLM Proxy API with multiple deployment options and configurations.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Installation](#docker-installation)
- [Manual Installation](#manual-installation)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Post-Installation](#post-installation)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## Prerequisites

### System Requirements

#### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10+
- **CPU**: 2 cores (4 cores recommended)
- **RAM**: 4GB (8GB recommended)
- **Disk**: 10GB free space
- **Network**: Stable internet connection

#### Recommended Requirements
- **OS**: Linux (Ubuntu 20.04+ or CentOS 8+)
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 50GB+ SSD
- **Network**: 100Mbps+ connection

### Software Dependencies

#### Required Software
- **Python**: 3.11 or higher
- **pip**: Latest version
- **Git**: For cloning repository
- **curl**: For testing API endpoints

#### Optional Software
- **Docker**: For containerized deployment
- **Docker Compose**: For multi-container deployments
- **PostgreSQL**: For advanced features
- **Redis**: For caching and session storage
- **Nginx**: For reverse proxy and load balancing

### API Keys and Credentials

#### Required API Keys
Before installation, obtain API keys from the following providers:

1. **OpenAI**
   - Visit: https://platform.openai.com/api-keys
   - Create a new API key
   - Note: Use a key with appropriate rate limits

2. **Anthropic** (Optional)
   - Visit: https://console.anthropic.com/
   - Create API key for Claude models

3. **Azure OpenAI** (Optional)
   - Visit: https://portal.azure.com
   - Create Azure OpenAI resource
   - Obtain endpoint URL and API key

4. **Other Providers** (Optional)
   - Cohere, Grok, OpenRouter, etc.

#### Environment Variables
Set up environment variables for API keys:
```bash
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
export AZURE_OPENAI_KEY="your-azure-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

## Quick Start

### One-Command Installation

For the fastest setup, use our automated installer:

```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/your-org/llm-proxy-api/main/install.sh | bash

# Or using wget
wget -qO- https://raw.githubusercontent.com/your-org/llm-proxy-api/main/install.sh | bash
```

The installer will:
- Check system requirements
- Install dependencies
- Configure the application
- Start the service
- Provide access information

### Basic Setup (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/llm-proxy-api.git
cd llm-proxy-api

# 2. Set up environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env with your API keys

# 5. Start the application
python main_dynamic.py

# 6. Verify installation
curl http://localhost:8000/health
```

## Docker Installation

### Single Container Deployment

```bash
# 1. Clone repository
git clone https://github.com/your-org/llm-proxy-api.git
cd llm-proxy-api

# 2. Create environment file
cat > .env << EOF
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ENVIRONMENT=production
EOF

# 3. Build and run container
docker build -t llm-proxy-api .
docker run -d \
  --name llm-proxy \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  llm-proxy-api

# 4. Verify deployment
curl http://localhost:8000/health
```

### Docker Compose Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  llm-proxy:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Optional: PostgreSQL for advanced features
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: llm_proxy
      POSTGRES_USER: llm_proxy
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f llm-proxy

# Scale the deployment
docker-compose up -d --scale llm-proxy=3
```

### Docker Swarm Deployment

```yaml
# docker-compose.swarm.yml
version: '3.8'

services:
  llm-proxy:
    image: llm-proxy-api:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    volumes:
      - llm_proxy_logs:/app/logs
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    deploy:
      placement:
        constraints:
          - node.role == manager

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - llm-proxy
    deploy:
      placement:
        constraints:
          - node.role == manager

volumes:
  llm_proxy_logs:
  redis_data:
```

```bash
# Deploy to Docker Swarm
docker stack deploy -c docker-compose.swarm.yml llm-proxy

# Check service status
docker stack services llm-proxy

# Scale services
docker service scale llm-proxy_llm-proxy=5
```

## Manual Installation

### Step-by-Step Installation

#### 1. System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# or
sudo yum update -y  # CentOS/RHEL

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Install development tools (optional)
sudo apt install -y build-essential python3-dev
```

#### 2. User and Directory Setup

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash llm-proxy

# Create application directory
sudo mkdir -p /opt/llm-proxy
sudo chown llm-proxy:llm-proxy /opt/llm-proxy

# Switch to application user
sudo -u llm-proxy bash
cd /opt/llm-proxy
```

#### 3. Application Installation

```bash
# Clone repository
git clone https://github.com/your-org/llm-proxy-api.git .
git checkout main  # or specific version tag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies for production
pip install gunicorn uvicorn[standard]  # For production server
```

#### 4. Configuration Setup

```bash
# Create configuration directory
mkdir -p config logs cache

# Copy configuration templates
cp config.yaml.example config.yaml
cp .env.example .env

# Edit configuration files
nano config.yaml  # Configure application settings
nano .env         # Set API keys and environment variables
```

#### 5. Database Setup (Optional)

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres createuser llm_proxy
sudo -u postgres createdb llm_proxy_db -O llm_proxy
sudo -u postgres psql -c "ALTER USER llm_proxy PASSWORD 'your_password';"

# Configure database connection in config.yaml
database:
  url: "postgresql://llm_proxy:your_password@localhost/llm_proxy_db"
```

#### 6. Redis Setup (Optional)

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set appropriate memory limits and persistence

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Configure Redis connection in config.yaml
redis:
  url: "redis://localhost:6379"
  max_connections: 20
```

#### 7. Service Configuration

```bash
# Create systemd service file
sudo tee /etc/systemd/system/llm-proxy.service > /dev/null <<EOF
[Unit]
Description=LLM Proxy API
After=network.target
Requires=redis.service postgresql.service

[Service]
Type=exec
User=llm-proxy
Group=llm-proxy
WorkingDirectory=/opt/llm-proxy
Environment=PATH=/opt/llm-proxy/venv/bin
ExecStart=/opt/llm-proxy/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable llm-proxy
sudo systemctl start llm-proxy

# Check service status
sudo systemctl status llm-proxy
```

#### 8. Reverse Proxy Setup (Optional)

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/llm-proxy > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Rate limiting
    limit_req zone=api burst=100 nodelay;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site and reload Nginx
sudo ln -s /etc/nginx/sites-available/llm-proxy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Production Deployment

### High Availability Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - llm-proxy
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == manager

  # Application servers
  llm-proxy:
    build: .
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    volumes:
      - llm_proxy_logs:/app/logs
    deploy:
      replicas: 4
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
        interval: 30s
        timeout: 10s
        retries: 3
        start_period: 60s

  # Redis cluster
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.labels.type == cache

  # PostgreSQL with replication
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: llm_proxy
      POSTGRES_USER: llm_proxy
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.labels.type == database

  # Monitoring stack
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    deploy:
      placement:
        constraints:
          - node.role == manager

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    deploy:
      placement:
        constraints:
          - node.role == manager

volumes:
  llm_proxy_logs:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:
```

### SSL/TLS Configuration

```bash
# Obtain SSL certificate (Let's Encrypt)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Or using self-signed certificate for testing
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/llm-proxy.key \
  -out /etc/ssl/certs/llm-proxy.crt

# Update Nginx configuration for SSL
sudo tee /etc/nginx/sites-available/llm-proxy-ssl > /dev/null <<EOF
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/llm-proxy.crt;
    ssl_certificate_key /etc/ssl/private/llm-proxy.key;

    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GSSHA384:DHE-RSA-AES256-GSSHA384:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}
EOF
```

## Cloud Deployment

### AWS Deployment

#### EC2 Instance Setup

```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups llm-proxy-sg

# Connect to instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip git

# Clone and setup application
git clone https://github.com/your-org/llm-proxy-api.git
cd llm-proxy-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Start application
python main_dynamic.py
```

#### AWS ECS/Fargate Deployment

```json
// task-definition.json
{
  "family": "llm-proxy",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "llm-proxy",
      "image": "your-registry/llm-proxy-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "OPENAI_API_KEY", "value": "${OPENAI_API_KEY}"}
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:anthropic-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/llm-proxy",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Google Cloud Platform

#### GKE Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-proxy
  labels:
    app: llm-proxy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-proxy
  template:
    metadata:
      labels:
        app: llm-proxy
    spec:
      containers:
      - name: llm-proxy
        image: gcr.io/your-project/llm-proxy-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-proxy-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: llm-proxy-service
spec:
  selector:
    app: llm-proxy
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Azure Deployment

#### Azure Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group your-resource-group \
  --name llm-proxy \
  --image your-registry/llm-proxy-api:latest \
  --cpu 1 \
  --memory 2 \
  --registry-login-server your-registry.azurecr.io \
  --registry-username your-registry \
  --registry-password your-password \
  --environment-variables \
    ENVIRONMENT=production \
    OPENAI_API_KEY=$OPENAI_API_KEY \
  --ports 8000 \
  --dns-name-label llm-proxy \
  --query ipAddress.fqdn
```

## Configuration

### Environment Configuration

```bash
# .env file configuration
# Application settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Server settings
HOST=0.0.0.0
PORT=8000
WORKERS=4

# API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
AZURE_OPENAI_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# External services
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

### Application Configuration

```yaml
# config.yaml - Complete configuration
app:
  name: "LLM Proxy API"
  version: "2.0.0"
  environment: "production"
  debug: false

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  worker_class: "uvicorn.workers.UvicornWorker"
  max_requests: 1000
  max_requests_jitter: 50

auth:
  api_keys:
    - "${API_KEY_1}"
    - "${API_KEY_2}"
  jwt:
    enabled: false
    secret_key: "${JWT_SECRET}"
    algorithm: "HS256"

providers:
  - name: "openai"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    enabled: true
    priority: 1
    timeout: 30
    max_retries: 3

  - name: "anthropic"
    type: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    enabled: true
    priority: 2
    timeout: 30
    max_retries: 3

caching:
  enabled: true
  response_cache:
    max_size_mb: 100
    ttl: 1800
  summary_cache:
    max_size_mb: 50
    ttl: 3600

logging:
  level: "INFO"
  format: "json"
  file: "logs/llm_proxy.log"
  max_file_size: "100MB"
  max_files: 5

metrics:
  enabled: true
  prometheus:
    enabled: true
    port: 9090

health_check:
  enabled: true
  interval: 30
  timeout: 5
```

## Post-Installation

### Verification Steps

```bash
# 1. Check service status
sudo systemctl status llm-proxy  # For systemd
docker-compose ps               # For Docker Compose
docker stack services llm-proxy # For Docker Swarm

# 2. Verify API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl http://localhost:8000/api/models

# 3. Test basic functionality
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'

# 4. Check logs
tail -f logs/llm_proxy.log
docker-compose logs -f llm-proxy

# 5. Verify monitoring
curl http://localhost:8000/metrics/prometheus
```

### Performance Tuning

```bash
# 1. Adjust worker processes
# Edit config.yaml or environment variables
WORKERS=8  # Increase for higher throughput

# 2. Tune connection pools
# Edit http_client configuration
max_connections: 200
max_keepalive_connections: 50

# 3. Configure caching
# Enable and tune cache settings
caching:
  enabled: true
  response_cache:
    max_size_mb: 512
    ttl: 1800

# 4. Optimize memory usage
# Configure memory limits
memory:
  max_usage_percent: 80
  gc_tuning: true
```

### Security Hardening

```bash
# 1. Configure firewall
sudo ufw enable
sudo ufw allow 8000
sudo ufw allow ssh

# 2. Set up SSL/TLS
# Use certbot or configure SSL certificates
sudo certbot --nginx -d your-domain.com

# 3. Configure rate limiting
# Edit config.yaml rate limiting settings
rate_limit:
  enabled: true
  requests_per_minute: 1000

# 4. Set up log monitoring
# Configure log analysis and alerting
logging:
  security_events: true
  audit_trail: true
```

## Troubleshooting

### Common Installation Issues

#### Python Version Issues

**Problem:** Python 3.11+ required but older version installed
```bash
# Check Python version
python3 --version

# Install Python 3.11 on Ubuntu
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11 python3.11-venv

# Use Python 3.11 explicitly
python3.11 -m venv venv
source venv/bin/activate
```

#### Permission Issues

**Problem:** Permission denied when starting service
```bash
# Fix directory permissions
sudo chown -R llm-proxy:llm-proxy /opt/llm-proxy
sudo chmod -R 755 /opt/llm-proxy

# Fix log directory permissions
sudo mkdir -p /opt/llm-proxy/logs
sudo chown llm-proxy:llm-proxy /opt/llm-proxy/logs
```

#### Port Already in Use

**Problem:** Port 8000 already in use
```bash
# Check what's using the port
sudo lsof -i :8000
sudo netstat -tlnp | grep :8000

# Kill the process using the port
sudo kill -9 <PID>

# Or change the port in configuration
PORT=8001
```

#### API Key Issues

**Problem:** API calls failing due to invalid keys
```bash
# Check API key format
echo $OPENAI_API_KEY | head -c 10  # Should start with 'sk-'

# Test API key validity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check environment variables
env | grep API_KEY
```

#### Memory Issues

**Problem:** Application running out of memory
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Increase system memory or optimize application
# Edit config.yaml memory settings
memory:
  max_usage_percent: 70
  emergency_cleanup: true

# Add swap space if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Network Issues

**Problem:** Unable to connect to external APIs
```bash
# Check network connectivity
ping api.openai.com
curl -I https://api.openai.com/v1/models

# Check DNS resolution
nslookup api.openai.com

# Check firewall settings
sudo ufw status
sudo iptables -L

# Test with different DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Docker Issues

#### Container Won't Start

```bash
# Check Docker logs
docker logs llm-proxy

# Check container status
docker ps -a
docker inspect llm-proxy

# Check resource limits
docker stats llm-proxy

# Rebuild container
docker build --no-cache -t llm-proxy-api .
```

#### Port Binding Issues

```bash
# Check port availability
docker run --rm -p 8000:8000 busybox nc -l 0.0.0.0:8000

# Use different host port
docker run -d -p 8001:8000 --name llm-proxy llm-proxy-api

# Check Docker networking
docker network ls
docker network inspect bridge
```

### Database Issues

#### Connection Failures

```bash
# Check database status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Test database connection
psql -h localhost -U llm_proxy -d llm_proxy_db

# Check connection limits
psql -c "SHOW max_connections;"
```

#### Migration Issues

```bash
# Run database migrations
cd /opt/llm-proxy
source venv/bin/activate
alembic upgrade head

# Check migration status
alembic current

# Fix migration issues
alembic revision --autogenerate -m "Fix migration"
alembic upgrade head
```

## Uninstallation

### Docker Uninstall

```bash
# Stop and remove containers
docker-compose down

# Remove images and volumes
docker-compose down --volumes --rmi all

# Remove networks
docker network prune

# Clean up unused resources
docker system prune -a --volumes
```

### Manual Uninstall

```bash
# Stop service
sudo systemctl stop llm-proxy
sudo systemctl disable llm-proxy

# Remove service file
sudo rm /etc/systemd/system/llm-proxy.service
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/llm-proxy

# Remove user
sudo userdel llm-proxy

# Remove database (optional)
sudo -u postgres dropdb llm_proxy_db
sudo -u postgres dropuser llm_proxy

# Remove Redis data (optional)
sudo rm -rf /var/lib/redis/dump.rdb

# Remove Nginx configuration (optional)
sudo rm /etc/nginx/sites-enabled/llm-proxy
sudo rm /etc/nginx/sites-available/llm-proxy
sudo systemctl reload nginx
```

### Cloud Cleanup

#### AWS Cleanup

```bash
# Terminate EC2 instance
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0

# Delete load balancer
aws elb delete-load-balancer --load-balancer-name llm-proxy-lb

# Clean up security groups, IAM roles, etc.
aws ec2 delete-security-group --group-id sg-12345678
aws iam detach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam delete-role --role-name ecsTaskExecutionRole
```

#### GCP Cleanup

```bash
# Delete GKE cluster
gcloud container clusters delete llm-proxy-cluster

# Delete persistent disks
gcloud compute disks delete llm-proxy-disk

# Clean up firewall rules
gcloud compute firewall-rules delete llm-proxy-allow
```

#### Azure Cleanup

```bash
# Delete resource group (removes all resources)
az group delete --name llm-proxy-rg

# Or delete individual resources
az container delete --name llm-proxy --resource-group llm-proxy-rg
az network public-ip delete --name llm-proxy-ip --resource-group llm-proxy-rg
```

---

## 📞 Support

### Getting Help

1. **Documentation**: Check this installation guide and API documentation
2. **GitHub Issues**: Report bugs and request features
3. **Community Forum**: Ask questions and share experiences
4. **Professional Support**: Contact our support team for enterprise deployments

### Health Check Commands

```bash
# Quick health check
curl http://localhost:8000/health

# Detailed health check
curl "http://localhost:8000/health?detailed=true"

# Component-specific checks
curl http://localhost:8000/health/providers
curl http://localhost:8000/health/cache
curl http://localhost:8000/health/database

# Performance metrics
curl http://localhost:8000/metrics
curl http://localhost:8000/metrics/prometheus
```

---

**🚀 This comprehensive installation guide covers all deployment scenarios from simple Docker setups to complex production clusters with monitoring and security best practices.**