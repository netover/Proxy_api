# 🚀 LLM Proxy API Deployment Guide

This guide provides comprehensive instructions for deploying and managing the LLM Proxy API in various environments with automated rollback capabilities.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Methods](#deployment-methods)
- [Automated Deployment](#automated-deployment)
- [Rollback Procedures](#rollback-procedures)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## 🔧 Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.11+
- **Docker**: 20.10+ (optional but recommended)
- **Docker Compose**: 2.0+ (for multi-service deployment)
- **Memory**: 2GB minimum, 4GB recommended
- **Disk Space**: 5GB minimum for application and logs

### Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git build-essential python3 python3-pip python3-venv

# Install Docker (optional but recommended)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Network Requirements

- **Ports**: 8000 (main API), 8001 (context service), 8002 (health worker)
- **Firewall**: Allow inbound traffic on required ports
- **DNS**: Configure domain names if needed

## 🏗️ Deployment Methods

### Method 1: Docker Deployment (Recommended)

#### Single Service Deployment

```bash
# Clone repository
git clone https://github.com/your-org/llm-proxy-api.git
cd llm-proxy-api

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### Multi-Service Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services if needed
docker-compose up -d --scale llm-proxy=3
```

### Method 2: Systemd Deployment

#### Automated Deployment

```bash
# Run deployment script
sudo ./deploy.sh

# Or with Docker
sudo ./deploy.sh --docker

# Check deployment status
sudo systemctl status llm-proxy
```

#### Manual Systemd Setup

```bash
# Copy service files
sudo cp systemd-services/*.service /etc/systemd/system/

# Update paths in service files
sudo sed -i 's|/path/to/ProxyAPI|/opt/llm-proxy-api|g' /etc/systemd/system/*.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable llm-proxy context-service health-worker
sudo systemctl start llm-proxy context-service health-worker
```

### Method 3: Manual Python Deployment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file

# Start application
python main.py
```

## 🚀 Automated Deployment

### Using Deploy Script

The `deploy.sh` script provides automated deployment with the following features:

- **Automatic backups** before deployment
- **Health checks** after deployment
- **Rollback on failure**
- **Multi-environment support**

#### Basic Deployment

```bash
# Deploy with systemd
sudo ./deploy.sh

# Deploy with Docker
sudo ./deploy.sh --docker

# Skip backup (not recommended)
sudo ./deploy.sh --skip-backup

# Force deployment (skip health checks)
sudo ./deploy.sh --force
```

#### Deployment Options

| Option | Description |
|--------|-------------|
| `--docker` | Use Docker for deployment |
| `--skip-backup` | Skip creating backup before deployment |
| `--force` | Force deployment even if health checks fail |
| `--help` | Show help message |

### Deployment Process

1. **Pre-deployment checks**
   - Validate system requirements
   - Check available disk space
   - Verify Docker availability (if using Docker)

2. **Backup creation**
   - Create timestamped backup of current deployment
   - Maintain last 5 backups automatically

3. **Service stop**
   - Gracefully stop existing services
   - Wait for services to terminate

4. **Application deployment**
   - Copy new application files
   - Set proper permissions
   - Install/update dependencies

5. **Environment configuration**
   - Copy environment files
   - Set secure permissions on sensitive files

6. **Service start**
   - Start services in correct order
   - Enable systemd services (if applicable)

7. **Health verification**
   - Perform comprehensive health checks
   - Verify all endpoints are responding
   - Check service dependencies

8. **Cleanup**
   - Remove temporary files
   - Clean up old backups

## 🔄 Rollback Procedures

### Automated Rollback

The `rollback.sh` script provides automated rollback capabilities:

```bash
# List available backups
sudo ./rollback.sh --list

# Rollback to latest backup
sudo ./rollback.sh

# Rollback to specific backup
sudo ./rollback.sh --backup llm-proxy_backup_20231201_143022.tar.gz

# Force rollback (skip confirmation)
sudo ./rollback.sh --force
```

### Rollback Options

| Option | Description |
|--------|-------------|
| `--list` | List all available backups |
| `--backup FILE` | Specify backup file to rollback to |
| `--docker` | Use Docker for rollback |
| `--force` | Force rollback without confirmation |
| `--help` | Show help message |

### Manual Rollback

If automated rollback fails, perform manual rollback:

```bash
# Stop services
sudo systemctl stop llm-proxy context-service health-worker

# Restore from backup
sudo rm -rf /opt/llm-proxy-api/current
sudo tar -xzf /opt/llm-proxy-api/backups/backup_file.tar.gz -C /opt/llm-proxy-api

# Restart services
sudo systemctl start context-service health-worker llm-proxy

# Verify rollback
curl http://localhost:8000/health
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline includes:

1. **Automated Testing**
   - Unit tests
   - Integration tests
   - Security scanning
   - Code coverage

2. **Docker Image Build**
   - Multi-stage build
   - Security scanning
   - Image optimization

3. **Staging Deployment**
   - Automated deployment to staging
   - Health checks
   - Smoke tests

4. **Production Deployment**
   - Manual approval required
   - Blue-green deployment
   - Automated rollback on failure

### Required Secrets

Configure the following secrets in your GitHub repository:

```bash
# Staging environment
STAGING_HOST=your-staging-server.com
STAGING_USER=deploy
STAGING_SSH_KEY=your-ssh-private-key
STAGING_PORT=22

# Production environment
PRODUCTION_HOST=your-production-server.com
PRODUCTION_USER=deploy
PRODUCTION_SSH_KEY=your-ssh-private-key
PRODUCTION_PORT=22
```

### Workflow Triggers

- **Push to main/master**: Full CI/CD pipeline
- **Pull requests**: Testing and security scans
- **Manual dispatch**: Custom deployments with parameters

## 📊 Monitoring & Health Checks

### Health Check Endpoints

| Endpoint | Description | Expected Response |
|----------|-------------|-------------------|
| `/health` | Overall system health | `{"status": "healthy"}` |
| `/health/providers` | Provider connectivity | Provider status object |
| `/health/system` | System resources | CPU, memory, disk usage |
| `/health/cache` | Cache performance | Cache hit rates, size |

### Monitoring Commands

```bash
# Check service status
sudo systemctl status llm-proxy

# View service logs
sudo journalctl -u llm-proxy -f

# Check Docker containers
docker ps

# View Docker logs
docker-compose logs -f llm-proxy

# Monitor resource usage
htop
```

### Metrics Collection

The application exposes Prometheus metrics at `/metrics`:

```bash
# Get all metrics
curl http://localhost:8000/metrics

# Get Prometheus-formatted metrics
curl http://localhost:8000/metrics/prometheus
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check service status
sudo systemctl status llm-proxy

# View detailed logs
sudo journalctl -u llm-proxy -n 50

# Check for port conflicts
sudo netstat -tlnp | grep :8000

# Verify configuration
sudo journalctl -u llm-proxy | grep -i error
```

#### Health Check Failures

```bash
# Manual health check
curl -v http://localhost:8000/health

# Check service logs
sudo journalctl -u llm-proxy -f

# Verify dependencies
curl http://localhost:8001/health  # Context service
curl http://localhost:8002/health  # Health worker
```

#### Docker Issues

```bash
# Check Docker status
sudo systemctl status docker

# View container logs
docker-compose logs llm-proxy

# Restart containers
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

#### Permission Issues

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/llm-proxy-api

# Fix permissions
sudo chmod -R 755 /opt/llm-proxy-api
sudo chmod 600 /opt/llm-proxy-api/.env
```

### Performance Issues

```bash
# Check system resources
top
htop

# Monitor network connections
sudo netstat -tlnp

# Check disk usage
df -h

# View application metrics
curl http://localhost:8000/metrics
```

## 🔒 Security Considerations

### Deployment Security

1. **User Permissions**
   - Run services as non-root user (`www-data`)
   - Use dedicated deployment user
   - Restrict file permissions

2. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Use internal networks for service communication

3. **Secret Management**
   - Store API keys securely
   - Use environment variables
   - Rotate secrets regularly

4. **Access Control**
   - Implement authentication
   - Use API keys for external access
   - Configure rate limiting

### Security Checklist

- [ ] Services run as non-root user
- [ ] File permissions are restrictive
- [ ] Sensitive data is encrypted
- [ ] Network access is limited
- [ ] HTTPS is enabled
- [ ] API keys are rotated regularly
- [ ] Audit logging is enabled
- [ ] Security updates are applied

## 📈 Scaling and Performance

### Horizontal Scaling

```bash
# Scale with Docker Compose
docker-compose up -d --scale llm-proxy=3

# Scale with systemd (manual)
sudo systemctl start llm-proxy@2
sudo systemctl start llm-proxy@3
```

### Vertical Scaling

```bash
# Increase memory limits
sudo systemctl edit llm-proxy
# Add: MemoryLimit=2G

# Increase CPU limits
sudo systemctl edit llm-proxy
# Add: CPUQuota=200%
```

### Load Balancing

```bash
# Install nginx
sudo apt install nginx

# Configure upstream servers
upstream llm_proxy_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

# Configure nginx virtual host
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://llm_proxy_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Maintenance Procedures

### Regular Maintenance

```bash
# Update application
sudo ./deploy.sh

# Clean up old backups
sudo find /opt/llm-proxy-api/backups -name "*.tar.gz" -mtime +30 -delete

# Rotate logs
sudo logrotate /etc/logrotate.d/llm-proxy

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Backup Strategy

```bash
# Automated daily backups
crontab -e
# Add: 0 2 * * * /opt/llm-proxy-api/backup.sh

# Manual backup
sudo ./deploy.sh --skip-backup  # Creates backup automatically
```

### Log Management

```bash
# View logs
sudo journalctl -u llm-proxy -f

# Export logs
sudo journalctl -u llm-proxy --since "2024-01-01" --until "2024-01-31" > logs_2024_01.txt

# Log rotation
sudo journalctl --vacuum-time=30d
```

## 📞 Support and Resources

### Getting Help

1. **Check logs**: `sudo journalctl -u llm-proxy -f`
2. **Health checks**: `curl http://localhost:8000/health`
3. **Documentation**: This guide and inline comments
4. **Community**: GitHub issues and discussions

### Useful Commands

```bash
# Quick status check
sudo systemctl status llm-proxy context-service health-worker

# Full system health
curl -s http://localhost:8000/health | jq .

# Performance metrics
curl -s http://localhost:8000/metrics | head -20

# Docker status
docker stats
```

### Emergency Contacts

- **System Administrator**: admin@yourcompany.com
- **DevOps Team**: devops@yourcompany.com
- **Security Team**: security@yourcompany.com

---

**Remember**: Always test deployments in staging before production, and have a rollback plan ready!