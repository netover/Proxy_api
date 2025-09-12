#!/bin/bash

# LLM Proxy API Rollback Script
# This script handles automated rollback to previous deployment versions

set -e  # Exit on any error

# Configuration
APP_NAME="llm-proxy-api"
DEPLOY_DIR="/opt/$APP_NAME"
BACKUP_DIR="/opt/${APP_NAME}_backups"
LOG_FILE="/var/log/${APP_NAME}_rollback.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

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
    log "ROLLBACK FAILED: $1"
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

# List available backups
list_backups() {
    info "Available backups:"

    if [[ ! -d "$BACKUP_DIR" ]]; then
        error_exit "Backup directory does not exist: $BACKUP_DIR"
    fi

    local backup_count=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)

    if [[ $backup_count -eq 0 ]]; then
        error_exit "No backups found in $BACKUP_DIR"
    fi

    echo "Found $backup_count backup(s):"
    echo "----------------------------------------"

    # List backups with size and date
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf '%T@ %s %p\n' | sort -nr | while read -r line; do
        local timestamp=$(echo "$line" | cut -d' ' -f1)
        local size=$(echo "$line" | cut -d' ' -f2)
        local path=$(echo "$line" | cut -d' ' -f3-)
        local filename=$(basename "$path")
        local date=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S')
        local human_size=$(numfmt --to=iec-i --suffix=B "$size")

        printf "  %-30s %10s %s\n" "$filename" "$human_size" "$date"
    done

    echo "----------------------------------------"
}

# Select backup for rollback
select_backup() {
    local backup_file="$1"

    if [[ -z "$backup_file" ]]; then
        # Interactive selection
        echo ""
        echo "Select a backup to rollback to:"
        echo "(Enter the full backup filename, or 'latest' for most recent)"

        read -r selection

        if [[ "$selection" == "latest" ]]; then
            backup_file=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf '%T@ %p\n' | sort -nr | head -n1 | cut -d' ' -f2-)
        else
            backup_file="$BACKUP_DIR/$selection"
        fi
    fi

    # Validate backup file exists
    if [[ ! -f "$backup_file" ]]; then
        error_exit "Backup file does not exist: $backup_file"
    fi

    # Validate backup file is readable
    if [[ ! -r "$backup_file" ]]; then
        error_exit "Backup file is not readable: $backup_file"
    fi

    echo "$backup_file"
}

# Stop services
stop_services() {
    info "Stopping current services..."

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

# Backup current state before rollback
backup_current() {
    info "Creating backup of current state before rollback..."

    local current_backup="${APP_NAME}_current_$TIMESTAMP.tar.gz"

    if [[ -d "$DEPLOY_DIR" ]]; then
        sudo tar -czf "$BACKUP_DIR/$current_backup" -C "$(dirname "$DEPLOY_DIR")" "$(basename "$DEPLOY_DIR")" || error_exit "Failed to backup current state"
        success "Current state backed up as: $current_backup"
    else
        warning "No current deployment directory found"
    fi
}

# Perform rollback
perform_rollback() {
    local backup_file="$1"

    info "Performing rollback using: $(basename "$backup_file")"

    # Extract backup information
    local backup_info=$(tar -tzf "$backup_file" | head -n1)
    info "Backup contains: $backup_info"

    # Remove current deployment
    if [[ -d "$DEPLOY_DIR" ]]; then
        info "Removing current deployment..."
        sudo rm -rf "$DEPLOY_DIR" || error_exit "Failed to remove current deployment"
    fi

    # Create fresh deployment directory
    sudo mkdir -p "$DEPLOY_DIR" || error_exit "Failed to create deployment directory"

    # Extract backup
    info "Extracting backup..."
    sudo tar -xzf "$backup_file" -C "$(dirname "$DEPLOY_DIR")" || error_exit "Failed to extract backup"

    # Set proper permissions
    sudo chown -R www-data:www-data "$DEPLOY_DIR" 2>/dev/null || warning "Failed to set ownership"
    sudo chmod -R 755 "$DEPLOY_DIR" 2>/dev/null || warning "Failed to set permissions"

    success "Backup extracted successfully"
}

# Restore virtual environment if needed
restore_venv() {
    if [[ -d "$DEPLOY_DIR/venv" ]]; then
        info "Virtual environment found in backup - no need to recreate"
        return 0
    fi

    if [[ "$USE_DOCKER" != "true" ]]; then
        info "Recreating virtual environment..."
        sudo -u www-data python3 -m venv "$DEPLOY_DIR/venv" || error_exit "Failed to create virtual environment"
        sudo -u www-data "$DEPLOY_DIR/venv/bin/pip" install --upgrade pip || warning "Failed to upgrade pip"
        sudo -u www-data "$DEPLOY_DIR/venv/bin/pip" install -r "$DEPLOY_DIR/requirements.txt" || error_exit "Failed to install dependencies"
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

        # Ensure systemd service files exist and are up to date
        for service_file in /etc/systemd/system/llm-proxy.service /etc/systemd/system/context-service.service /etc/systemd/system/health-worker.service; do
            if [[ ! -f "$service_file" ]]; then
                warning "Service file missing: $service_file"
                continue
            fi

            # Update paths in service files
            sudo sed -i "s|/path/to/ProxyAPI|$DEPLOY_DIR|g" "$service_file" || warning "Failed to update paths in $service_file"
            sudo sed -i "s|/path/to/venv|$DEPLOY_DIR/venv|g" "$service_file" || warning "Failed to update venv path in $service_file"
        done

        # Reload systemd
        sudo systemctl daemon-reload || error_exit "Failed to reload systemd"

        # Enable and start services
        for service in context-service health-worker llm-proxy; do
            if [[ -f "/etc/systemd/system/$service.service" ]]; then
                sudo systemctl enable "$service" || warning "Failed to enable $service"
                sudo systemctl start "$service" || error_exit "Failed to start $service"
            fi
        done

        # Wait for services to start
        sleep 10

        # Check service status
        for service in llm-proxy context-service health-worker; do
            if [[ -f "/etc/systemd/system/$service.service" ]] && sudo systemctl is-active --quiet "$service"; then
                success "Service $service is running"
            elif [[ -f "/etc/systemd/system/$service.service" ]]; then
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

# Verify rollback
verify_rollback() {
    info "Verifying rollback..."

    # Check if services are running
    local services_ok=true

    if [[ "$USE_DOCKER" == "true" ]]; then
        if ! docker-compose ps | grep -q "Up"; then
            services_ok=false
        fi
    else
        for service in llm-proxy context-service health-worker; do
            if [[ -f "/etc/systemd/system/$service.service" ]] && ! sudo systemctl is-active --quiet "$service"; then
                services_ok=false
                break
            fi
        done
    fi

    if [[ "$services_ok" != "true" ]]; then
        error_exit "Services are not running after rollback"
    fi

    # Check if application responds
    if ! curl -s --max-time 10 http://localhost:8000/health > /dev/null 2>&1; then
        error_exit "Application is not responding after rollback"
    fi

    success "Rollback verification completed successfully"
}

# Cleanup function
cleanup() {
    info "Performing cleanup..."

    # Clean up temporary files
    sudo find "$DEPLOY_DIR" -name "*.pyc" -delete 2>/dev/null || true
    sudo find "$DEPLOY_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
}

# Main rollback function
main() {
    info "Starting rollback of $APP_NAME"
    info "Timestamp: $TIMESTAMP"

    # Parse command line arguments
    USE_DOCKER=false
    BACKUP_FILE=""
    FORCE_ROLLBACK=false
    LIST_BACKUPS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker)
                USE_DOCKER=true
                shift
                ;;
            --backup)
                BACKUP_FILE="$2"
                shift 2
                ;;
            --force)
                FORCE_ROLLBACK=true
                shift
                ;;
            --list)
                LIST_BACKUPS=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --docker       Use Docker for rollback"
                echo "  --backup FILE  Specify backup file to use"
                echo "  --force        Force rollback even if health checks fail"
                echo "  --list         List available backups"
                echo "  --help         Show this help message"
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done

    # Pre-rollback checks
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

    # List backups if requested
    if [[ "$LIST_BACKUPS" == "true" ]]; then
        list_backups
        exit 0
    fi

    # Select backup
    BACKUP_FILE=$(select_backup "$BACKUP_FILE")

    info "Selected backup: $(basename "$BACKUP_FILE")"

    # Confirm rollback unless forced
    if [[ "$FORCE_ROLLBACK" != "true" ]]; then
        echo ""
        echo -e "${YELLOW}WARNING: This will rollback the application to a previous version.${NC}"
        echo "Current data and configuration may be lost."
        echo ""
        read -p "Are you sure you want to continue? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Rollback cancelled by user"
            exit 0
        fi
    fi

    # Backup current state
    backup_current

    # Stop services
    stop_services

    # Perform rollback
    perform_rollback "$BACKUP_FILE"

    # Restore virtual environment if needed
    restore_venv

    # Start services
    start_services

    # Perform health check
    if [[ "$FORCE_ROLLBACK" != "true" ]]; then
        health_check
    else
        warning "Skipping health check due to --force flag"
    fi

    # Verify rollback
    verify_rollback

    # Cleanup
    cleanup

    success "Rollback completed successfully!"
    info "Application has been rolled back to previous version"
    info "Application is available at:"
    info "  Main API: http://localhost:8000"
    info "  Health Check: http://localhost:8000/health"
    info "  API Docs: http://localhost:8000/docs"

    if [[ "$USE_DOCKER" != "true" ]]; then
        info "Services status:"
        sudo systemctl status llm-proxy --no-pager -l 2>/dev/null || warning "Failed to get service status"
    fi
}

# Trap for cleanup on error
trap 'error_exit "Rollback interrupted by user"' INT TERM

# Run main function with all arguments
main "$@"