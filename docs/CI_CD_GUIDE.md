# CI/CD Pipeline Guide

This document provides comprehensive information about the CI/CD pipeline setup for the LLM Proxy API project.

## Overview

The CI/CD pipeline consists of multiple GitHub Actions workflows that automate testing, security scanning, code quality checks, and deployment processes.

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Triggers:**
- Push to main/master/develop branches
- Pull requests to main/master/develop branches
- Manual workflow dispatch

**Jobs:**
- **Code Quality**: Linting, formatting, and type checking
- **Testing**: Unit and integration tests across multiple Python versions
- **Load Testing**: Performance testing with k6
- **Security Scanning**: Bandit, Safety, and Trivy vulnerability scans
- **Docker Build**: Container image building and registry push
- **Staging Deployment**: Automated deployment to staging environment
- **Production Deployment**: Automated deployment to production with rollback
- **Verification**: Post-deployment health checks and smoke tests

### 2. Code Quality Checks (`code-quality.yml`)

**Triggers:**
- Push to main/master/develop branches
- Pull requests
- Daily schedule (6 AM UTC)
- Manual workflow dispatch

**Jobs:**
- **Linting and Formatting**: Ruff, Black, isort
- **Type Checking**: MyPy static analysis
- **Pre-commit Hooks**: Automated code quality enforcement

### 3. Security Monitoring (`security-monitoring.yml`)

**Triggers:**
- Daily schedule (3 AM UTC)
- Manual workflow dispatch with scan type options

**Jobs:**
- **Dependency Audit**: pip-audit vulnerability scanning
- **Secrets Detection**: Gitleaks secret scanning
- **SAST Scanning**: Semgrep static application security testing
- **Container Security**: Trivy and Grype image vulnerability scans
- **License Compliance**: Automated license checking

### 4. Performance Testing (`performance.yml`)

**Triggers:**
- Push to main/master branches
- Weekly schedule (Sundays 2 AM UTC)
- Manual workflow dispatch with test type options

**Jobs:**
- **Benchmarks**: pytest-benchmark performance testing
- **Load Testing**: k6 load testing scenarios
- **Memory Profiling**: Memory usage analysis

## Required Secrets

Configure the following secrets in your GitHub repository:

### Deployment Secrets
```
STAGING_HOST          # Staging server hostname/IP
STAGING_USER          # SSH username for staging
STAGING_SSH_KEY       # Private SSH key for staging
STAGING_PORT          # SSH port for staging (default: 22)

PRODUCTION_HOST       # Production server hostname/IP
PRODUCTION_USER       # SSH username for production
PRODUCTION_SSH_KEY    # Private SSH key for production
PRODUCTION_PORT       # SSH port for production (default: 22)
```

### Security Secrets
```
GITHUB_TOKEN          # Auto-provided by GitHub
SEMGREP_APP_TOKEN     # For Semgrep SAST scanning
```

## Environment Setup

### Staging Environment
- Automatically deployed on pushes to main/master
- Health check endpoint: `http://localhost:8000/health`
- Rollback capability with backup restoration

### Production Environment
- Deployed after successful staging deployment
- Manual approval required for workflow_dispatch
- Health check endpoint: `https://api.yourdomain.com/health`
- Automatic rollback on deployment failure

## Local Development Setup

### Pre-commit Hooks

Install pre-commit hooks for local development:

```bash
pip install pre-commit
pre-commit install
```

Run hooks manually:
```bash
pre-commit run --all-files
```

### Code Quality Tools

Install development dependencies:
```bash
pip install -r requirements.txt
```

Run individual tools:
```bash
# Linting
ruff check src/ tests/

# Formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/ --config-file packages/mypy.ini

# Security scanning
bandit -r src/
safety check
```

## Testing

### Running Tests Locally

```bash
# Unit tests
pytest tests/ -v -m "unit"

# Integration tests
pytest tests/ -v -m "integration"

# All tests with coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Load Testing

```bash
# Install k6
# Run load tests
k6 run tests/load_tests/light_load_30_users.js
k6 run tests/load_tests/medium_load_100_users.test.js
```

## Deployment Process

### Automatic Deployment

1. **Push to main/master**: Triggers full CI pipeline
2. **Code Quality**: Linting, formatting, type checking
3. **Testing**: Unit and integration tests
4. **Security**: Vulnerability scanning
5. **Build**: Docker image creation and push
6. **Staging**: Automatic deployment to staging
7. **Production**: Deployment to production (after staging success)

### Manual Deployment

Use workflow dispatch to manually trigger deployments:

1. Go to Actions tab in GitHub
2. Select "CI Pipeline" workflow
3. Click "Run workflow"
4. Choose environment (staging/production)
5. Select deployment type (docker/systemd)

## Monitoring and Alerts

### GitHub Issues Integration

The pipeline automatically creates GitHub issues for:
- Deployment failures with rollback notifications
- Security vulnerabilities found
- Performance regressions
- Code quality violations

### Artifact Storage

Test results and reports are stored as artifacts:
- Coverage reports (30 days retention)
- Security scan results (30 days retention)
- Performance test results (30 days retention)
- Load test reports (30 days retention)

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check server connectivity and SSH keys
   - Verify environment secrets are configured
   - Review deployment logs in Actions tab

2. **Test Failures**
   - Run tests locally to reproduce issues
   - Check for missing dependencies
   - Review test configuration in `pytest.ini`

3. **Security Scan Failures**
   - Address high/critical vulnerabilities
   - Update dependencies to latest secure versions
   - Review security scan results in artifacts

4. **Code Quality Failures**
   - Run pre-commit hooks locally
   - Fix linting and formatting issues
   - Address type checking errors

### Rollback Procedures

**Automatic Rollback:**
- Triggered on deployment failures
- Restores previous working version
- Creates notification issue

**Manual Rollback:**
```bash
# On deployment server
cd /opt/llm-proxy-api
sudo ./rollback.sh --docker --force
```

## Best Practices

1. **Branch Strategy**
   - Use feature branches for development
   - Merge to develop for integration testing
   - Merge to main/master for production deployment

2. **Code Quality**
   - Run pre-commit hooks before pushing
   - Address all CI feedback promptly
   - Maintain high test coverage (>80%)

3. **Security**
   - Regularly update dependencies
   - Address security vulnerabilities immediately
   - Use secrets management for sensitive data

4. **Performance**
   - Monitor benchmark results for regressions
   - Run load tests before major releases
   - Optimize slow endpoints identified in tests

## Configuration Files

- `.github/workflows/ci.yml` - Main CI pipeline
- `.github/workflows/code-quality.yml` - Code quality checks
- `.github/workflows/security-monitoring.yml` - Security monitoring
- `.github/workflows/performance.yml` - Performance testing
- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `.markdownlint.json` - Markdown linting rules
- `pytest.ini` - Test configuration
- `packages/mypy.ini` - Type checking configuration
- `packages/pyproject.toml` - Python project configuration

## Support

For issues with the CI/CD pipeline:
1. Check the Actions tab for workflow run details
2. Review artifact downloads for detailed reports
3. Check GitHub issues for known problems
4. Contact the development team for assistance