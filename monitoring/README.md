# Monitoring Setup for LLM Proxy Services

This directory contains monitoring configuration for the LLM Proxy microservices architecture.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Node Exporter**: System metrics collection

## Quick Start

### 1. Install Prometheus

```bash
# Download and install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvf prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64/

# Create user and directories
sudo useradd --no-create-home --shell /bin/false prometheus
sudo mkdir -p /etc/prometheus /var/lib/prometheus
sudo chown prometheus:prometheus /var/lib/prometheus

# Copy binary and configuration
sudo cp prometheus /usr/local/bin/
sudo cp prometheus.yml /etc/prometheus/
sudo cp -r consoles/ console_libraries/ /etc/prometheus/

# Create systemd service
sudo tee /etc/systemd/system/prometheus.service > /dev/null <<EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \\
    --config.file /etc/prometheus/prometheus.yml \\
    --storage.tsdb.path /var/lib/prometheus/ \\
    --web.console.templates=/etc/prometheus/consoles \\
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

### 2. Install Grafana

```bash
# Add Grafana repository
sudo apt-get install -y apt-transport-https
sudo apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list

# Install and start Grafana
sudo apt-get update
sudo apt-get install grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### 3. Install Node Exporter

```bash
# Download and install Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvf node_exporter-1.6.1.linux-amd64.tar.gz
sudo cp node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/

# Create user
sudo useradd --no-create-home --shell /bin/false node-exporter

# Create systemd service
sudo tee /etc/systemd/system/node-exporter.service > /dev/null <<EOF
[Unit]
Description=Node Exporter

[Service]
User=node-exporter
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=default.target
EOF

sudo systemctl daemon-reload
sudo systemctl start node-exporter
sudo systemctl enable node-exporter
```

### 4. Configure Services

1. Copy `prometheus.yml` to `/etc/prometheus/prometheus.yml`
2. Restart Prometheus: `sudo systemctl restart prometheus`
3. Access Grafana at [http://localhost:3000](http://localhost:3000) (admin/admin)
4. Import the dashboard from `grafana-dashboard.json`

## Metrics Available

### LLM Proxy Metrics

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration histogram
- `llm_requests_total`: Total LLM API calls
- `llm_tokens_total`: Total tokens processed
- `cache_hits_total`: Cache hit counter
- `cache_misses_total`: Cache miss counter

### Context Service Metrics

- `context_condensations_total`: Total condensation operations
- `context_cache_size`: Current cache size
- `context_processing_time_seconds`: Processing time histogram

### Health Worker Metrics

- `health_checks_total`: Total health checks performed
- `provider_status`: Current provider status (0=unhealthy, 1=healthy)

### System Metrics (Node Exporter)

- CPU usage, memory usage, disk I/O, network I/O
- System load, process count, file descriptors

## Alerting Rules

Create `/etc/prometheus/alert_rules.yml`:

```yaml
groups:
  - name: llm_proxy_alerts
    rules:
      - alert: LLMProxyDown
        expr: up{job="llm-proxy"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "LLM Proxy is down"
          description: "LLM Proxy has been down for more than 5 minutes"

      - alert: ContextServiceDown
        expr: up{job="context-service"} == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Context Service is down"
          description: "Context Service has been down for more than 5 minutes"

      - alert: HighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90% for more than 5 minutes"
```

## Logging

All services log to systemd journal. View logs with:

```bash
# View all service logs
sudo journalctl -u llm-proxy -u context-service -u health-worker

# Follow logs in real-time
sudo journalctl -u llm-proxy -f

# View logs for specific time period
sudo journalctl -u llm-proxy --since "2025-01-01" --until "2025-01-02"
```

## Custom Metrics

To add custom metrics to your services, use the metrics collector:

```python
from src.core.metrics import metrics_collector

# Counter
metrics_collector.increment_counter("custom_operation_total", {"service": "my_service"})

# Histogram
with metrics_collector.time_histogram("operation_duration_seconds", {"operation": "my_op"}):
    # Your operation here
    pass

# Gauge
metrics_collector.set_gauge("active_connections", 42, {"service": "my_service"})
```

## Troubleshooting

### Prometheus Issues

- Check configuration syntax: `prometheus --config.check`
- Verify targets are reachable: Check `/targets` endpoint
- Check Prometheus logs: `sudo journalctl -u prometheus`

### Grafana Issues

- Default login: admin/admin
- Check Grafana logs: `sudo journalctl -u grafana-server`
- Verify data sources are configured correctly

### Service Metrics Not Appearing

- Ensure services are running and accessible
- Check that `/metrics` endpoints are responding
- Verify Prometheus can scrape the targets
- Check firewall settings for metric ports
