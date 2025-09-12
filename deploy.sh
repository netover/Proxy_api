#!/bin/bash

# LLM Proxy API Deployment Script
# This script handles automated deployment with rollback capabilities

set -e  # Exit on any error

# Configuration
APP_NAME="llm-proxy-api"
DEPLOY_DIR="/opt/$APP_NAME"
BACKUP_DIR="/opt/${APP_NAME}_backups"
LOG_FILE="/var/log/${APP_NAME}_deploy.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${APP_NAME}_backup_$TIMESTAMP"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    log "DEPLOYMENT FAILED: $1"
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
    log "SUCCESS: $1"
}

# Warning message
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
    log "WARNING: $1"
}

# Info message
info() {
    echo -e "${BLUE}INFO: $1${NC}"
    log "INFO: $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error_exit "This script should not be run as root for security reasons"
    fi
}

# Create backup
create_backup() {
    info "Creating backup: $BACKUP_NAME"

    # Create backup directory if it doesn't exist
    sudo mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"

    # Create backup archive
    if [[ -d "$DEPLOY_DIR" ]]; then
        sudo tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$(dirname "$DEPLOY_DIR")" "$(basename "$DEPLOY_DIR")" 2>/dev/null || warning "No existing deployment to backup"
    else
        warning "No existing deployment directory found"
    fi

    # Keep only last 5 backups
    sudo find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | head -n -5 | cut -d' ' -f2- | xargs -r sudo rm
}

# Stop services
stop_services() {
    info "Stopping existing services..."

    # Stop systemd services if they exist
    for service in llm-proxy context-service health-worker; do
        if sudo systemctl is-active --quiet "$service" 2>/dev/null; then
            sudo systemctl stop "$service" || warning "Failed to stop $service"
        fi
    done

    # Stop Docker containers if using Docker
    if command -v docker &> /dev/null && docker ps -q --filter "name=$APP_NAME" | grep -q .; then
        docker-compose down || warning "Failed to stop Docker containers"
    fi
}

# Deploy application
deploy_app() {
    info "Deploying application to $DEPLOY_DIR"

    # Create deployment directory
    sudo mkdir -p "$DEPLOY_DIR" || error_exit "Failed to create deployment directory"

    # Copy application files
    sudo cp -r . "$DEPLOY_DIR/" || error_exit "Failed to copy application files"

    # Set proper permissions
    sudo chown -R www-data:www-data "$DEPLOY_DIR" || warning "Failed to set ownership"
    sudo chmod -R 755 "$DEPLOY_DIR" || warning "Failed to set permissions"

    # Create virtual environment if not using Docker
    if [[ "$USE_DOCKER" != "true" ]]; then
        info "Setting up Python virtual environment..."
        sudo -u www-data python3 -m venv "$DEPLOY_DIR/venv" || error_exit "Failed to create virtual environment"
        sudo -u www-data "$DEPLOY_DIR/venv/bin/pip" install --upgrade pip || warning "Failed to upgrade pip"
        sudo -u www-data "$DEPLOY_DIR/venv/bin/pip" install -r "$DEPLOY_DIR/requirements.txt" || error_exit "Failed to install dependencies"
    fi
}

# Configure environment
configure_environment() {
    info "Configuring environment variables..."

    # Copy environment file if it exists
    if [[ -f ".env" ]]; then
        sudo cp .env "$DEPLOY_DIR/.env" || warning "Failed to copy environment file"
        sudo chown www-data:www-data "$DEPLOY_DIR/.env" || warning "Failed to set env file ownership"
        sudo chmod 600 "$DEPLOY_DIR/.env" || warning "Failed to set env file permissions"
    else
        warning "No .env file found. Please configure environment variables manually."
    fi
}

# Start services
start_services() {
    if [[ "$USE_DOCKER" == "true" ]]; then
        info "Starting services with Docker..."

        cd "$DEPLOY_DIR" || error_exit "Failed to change to deployment directory"

        # Start Docker services
        docker-compose up -d || error_exit "Failed to start Docker services"

        # Wait for services to be healthy
        info "Waiting for services to start..."
        sleep 30

        # Check if services are running
        if docker-compose ps | grep -q "Up"; then
            success "Docker services started successfully"
        else
            error_exit "Docker services failed to start"
        fi

    else
        info "Starting services with systemd..."

        # Copy systemd service files
        sudo cp systemd-services/*.service /etc/systemd/system/ || error_exit "Failed to copy service files"

        # Update service file paths
        for service_file in /etc/systemd/system/llm-proxy.service /etc/systemd/system/context-service.service /etc/systemd/system/health-worker.service; do
            if [[ -f "$service_file" ]]; then
                sudo sed -i "s|/path/to/ProxyAPI|$DEPLOY_DIR|g" "$service_file" || warning "Failed to update paths in $service_file"
                sudo sed -i "s|/path/to/venv|$DEPLOY_DIR/venv|g" "$service_file" || warning "Failed to update venv path in $service_file"
            fi
        done

        # Reload systemd
        sudo systemctl daemon-reload || error_exit "Failed to reload systemd"

        # Enable and start services
        for service in context-service health-worker llm-proxy; do
            sudo systemctl enable "$service" || warning "Failed to enable $service"
            sudo systemctl start "$service" || error_exit "Failed to start $service"
        done

        # Wait for services to start
        sleep 10

        # Check service status
        for service in llm-proxy context-service health-worker; do
            if sudo systemctl is-active --quiet "$service"; then
                success "Service $service is running"
            else
                error_exit "Service $service failed to start"
            fi
        done
    fi
}

# Health check
health_check() {
    info "Performing health checks..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        info "Health check attempt $attempt/$max_attempts"

        # Check main service
        if curl -s --max-time 10 http://localhost:8000/health > /dev/null 2>&1; then
            success "Main service health check passed"
            return 0
        fi

        sleep 5
        ((attempt++))
    done

    error_exit "Health check failed after $max_attempts attempts"
}

# Rollback function
rollback() {
    warning "Initiating rollback to previous version..."

    # Stop current services
    stop_services

    # Restore from backup
    if [[ -f "$BACKUP_DIR/$BACKUP_NAME.tar.gz" ]]; then
        info "Restoring from backup: $BACKUP_NAME"
        sudo rm -rf "$DEPLOY_DIR" || warning "Failed to remove current deployment"
        sudo mkdir -p "$DEPLOY_DIR" || error_exit "Failed to recreate deployment directory"
        sudo tar -xzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$(dirname "$DEPLOY_DIR")" || error_exit "Failed to restore backup"

        # Restart services
        start_services

        success "Rollback completed successfully"
    else
        error_exit "No backup found for rollback"
    fi
}

# Cleanup function
cleanup() {
    info "Performing cleanup..."

    # Remove old backups (keep last 5)
    if [[ -d "$BACKUP_DIR" ]]; then
        sudo find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | head -n -5 | cut -d' ' -f2- | xargs -r sudo rm
    fi

    # Clean up temporary files
    sudo find "$DEPLOY_DIR" -name "*.pyc" -delete 2>/dev/null || true
    sudo find "$DEPLOY_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
}

# Main deployment function
main() {
    info "Starting deployment of $APP_NAME"
    info "Timestamp: $TIMESTAMP"
    info "Deployment directory: $DEPLOY_DIR"
    info "Backup directory: $BACKUP_DIR"

    # Parse command line arguments
    USE_DOCKER=false
    SKIP_BACKUP=false
    FORCE_DEPLOY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker)
                USE_DOCKER=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --docker       Use Docker for deployment"
                echo "  --skip-backup  Skip backup creation"
                echo "  --force        Force deployment even if health checks fail"
                echo "  --help         Show this help message"
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done

    # Pre-deployment checks
    check_root

    # Check if Docker is available when requested
    if [[ "$USE_DOCKER" == "true" ]]; then
        if ! command -v docker &> /dev/null; then
            error_exit "Docker is not installed. Please install Docker or run without --docker flag."
        fi
        if ! command -v docker-compose &> /dev/null; then
            error_exit "Docker Compose is not installed. Please install Docker Compose or run without --docker flag."
        fi
    fi

    # Create backup unless skipped
    if [[ "$SKIP_BACKUP" != "true" ]]; then
        create_backup
    fi

    # Stop existing services
    stop_services

    # Deploy application
    deploy_app

    # Configure environment
    configure_environment

    # Start services
    start_services

    # Perform health check
    if [[ "$FORCE_DEPLOY" != "true" ]]; then
        health_check
    else
        warning "Skipping health check due to --force flag"
    fi

    # Cleanup
    cleanup

    success "Deployment completed successfully!"
    info "Application is available at:"
    info "  Main API: http://localhost:8000"
    info "  Health Check: http://localhost:8000/health"
    info "  API Docs: http://localhost:8000/docs"

    if [[ "$USE_DOCKER" != "true" ]]; then
        info "Services status:"
        sudo systemctl status llm-proxy --no-pager -l || warning "Failed to get service status"
    fi
}

# Trap for cleanup on error
trap 'error_exit "Deployment interrupted by user"' INT TERM

# Run main function with all arguments
main "$@"