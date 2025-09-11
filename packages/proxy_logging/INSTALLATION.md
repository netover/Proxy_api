# Installation Guide - Proxy Logging Package

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation Steps

### 1. Install Dependencies

From the project root directory, install the proxy-logging package with all dependencies:

```bash
cd d:/Python/projetos/ProxyAPI/Proxy_api
pip install -e packages/proxy_logging
```

### 2. Install OpenTelemetry Dependencies

The package uses OpenTelemetry for distributed tracing and metrics. Ensure all OpenTelemetry components are installed:

```bash
# Install main OpenTelemetry packages
pip install opentelemetry-api>=1.25.0
pip install opentelemetry-sdk>=1.25.0
pip install opentelemetry-exporter-otlp>=1.25.0
pip install opentelemetry-exporter-otlp-proto-grpc>=1.25.0
pip install opentelemetry-semantic-conventions>=0.46b0
```

### 3. Verify Installation

Check that the package and its dependencies are correctly installed:

```bash
python -c "import proxy_logging; print('Package installed successfully')"
python -c "from opentelemetry.sdk.trace.export import BatchSpanProcessor; print('OpenTelemetry SDK imports working')"
python -c "from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter; print('OTLP gRPC exporter imports working')"
```

### 4. Troubleshooting

#### Pylance/IDE Import Issues
If you see "Import could not be resolved" errors in your IDE:

1. **Ensure correct Python interpreter**: Check that your IDE is using the same Python environment where the packages are installed
2. **Refresh language server**: In VS Code, press `Ctrl+Shift+P` → "Python: Restart Language Server"
3. **Verify environment**: Run `pip list | grep opentelemetry` to confirm packages are installed

#### Missing Dependencies
If import errors persist:

```bash
# Force reinstall all OpenTelemetry packages
pip install --force-reinstall opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
```

### 5. Development Environment Setup

For development, install with dev dependencies:

```bash
pip install -e "packages/proxy_logging[dev]"
```

This includes tools like pytest, mypy, black, and ruff for development and testing.

## Environment Configuration

Set up OpenTelemetry environment variables as needed:

```bash
# OTLP endpoint (optional)
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Service configuration
export OTEL_SERVICE_NAME="proxy-api"
export OTEL_SERVICE_VERSION="1.0.0"
```

## Quick Start

```python
from proxy_logging.opentelemetry_config import OpenTelemetryConfig

# Initialize OpenTelemetry
otel_config = OpenTelemetryConfig(service_name="my-service")
otel_config.configure()

# Get tracer
tracer = otel_config.get_tracer("my-component")
```

## Support

For issues with installation or configuration, please check:
1. GitHub Issues: https://github.com/proxyapi/proxy-logging/issues
2. Documentation: https://proxy-logging.readthedocs.io