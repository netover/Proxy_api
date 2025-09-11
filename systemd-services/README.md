# Systemd Services for LLM Proxy

This directory contains systemd service files for deploying the LLM Proxy as separate services.

## Services

1. **context-service.service** - Context condensation service (port 8001)
2. **health-worker.service** - Health monitoring service (port 8002)
3. **llm-proxy.service** - Main proxy service (port 8000)

## Installation

1. Copy the service files to `/etc/systemd/system/`:

    ```bash
    sudo cp *.service /etc/systemd/system/
    ```

2. Update the paths in the service files to match your installation:
   - Replace `/path/to/ProxyAPI` with the actual path
   - Replace `/path/to/venv` with the virtual environment path
   - Update user/group if needed (default: www-data)

3. Reload systemd and enable services:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable context-service
    sudo systemctl enable health-worker
    sudo systemctl enable llm-proxy
    ```

4. Start the services:

    ```bash
    sudo systemctl start context-service
    sudo systemctl start health-worker
    sudo systemctl start llm-proxy
    ```

## Service Management

### Check status

```bash
sudo systemctl status context-service
sudo systemctl status health-worker
sudo systemctl status llm-proxy
```

### View logs

```bash
sudo journalctl -u context-service -f
sudo journalctl -u health-worker -f
sudo journalctl -u llm-proxy -f
```

### Restart services

```bash
sudo systemctl restart context-service
sudo systemctl restart health-worker
sudo systemctl restart llm-proxy
```

### Stop services

```bash
sudo systemctl stop llm-proxy
sudo systemctl stop health-worker
sudo systemctl stop context-service
```

## Environment Variables

Configure the following environment variables as needed:

### Context Service

- `CACHE_SIZE`: Cache size (default: 1000)
- `CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `CACHE_PERSIST`: Enable file persistence (default: false)
- `ADAPTIVE_ENABLED`: Enable adaptive token limits (default: true)
- `TRUNCATION_THRESHOLD`: Content length threshold (default: 10000)

### Health Worker

- `HEALTH_CHECK_INTERVAL`: Health check interval in seconds (default: 60)

### Main Proxy

- `CONTEXT_SERVICE_URL`: URL for context service (default: <http://localhost:8001>)
- `HEALTH_WORKER_URL`: URL for health worker (default: <http://localhost:8002>)

## Monitoring

All services log to systemd journal. Use `journalctl` to view logs:

```bash
# View all service logs
sudo journalctl -u context-service -u health-worker -u llm-proxy

# Follow logs in real-time
sudo journalctl -u llm-proxy -f
```

## Troubleshooting

1. **Service fails to start**: Check the journal logs for error messages
2. **Port conflicts**: Ensure ports 8000, 8001, 8002 are available
3. **Permission issues**: Ensure the user has access to the working directory
4. **Dependency issues**: Make sure all Python dependencies are installed in the virtual environment

## Security Notes

- Services run as `www-data` user with limited privileges
- Memory and CPU limits are set to prevent resource exhaustion
- File system access is restricted to the service directories
- Network access is limited to the required ports
