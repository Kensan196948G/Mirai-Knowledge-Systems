#!/bin/bash
################################################################################
# Application Data Backup Script for Mirai Knowledge Systems
# Purpose: Backup JSON data, configuration files, and application assets
# Author: Mirai Knowledge Systems
# Version: 1.0.0
################################################################################

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================
BACKUP_DIR="/var/backups/mirai-knowledge/appdata"
APP_DIR="/mnt/LinuxHDD/Mirai-Knowledge-Systems"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/mirai-knowledge/backup.log"

# ============================================================================
# Functions
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

check_dependencies() {
    log "Checking dependencies..."

    if ! command -v tar &> /dev/null; then
        error_exit "tar not found. Please install tar."
    fi

    if ! command -v gzip &> /dev/null; then
        error_exit "gzip not found. Please install gzip."
    fi

    log "All dependencies are installed."
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"
        chmod 700 "$BACKUP_DIR"
    fi
}

backup_json_data() {
    local data_backup="$BACKUP_DIR/data_$DATE.tar.gz"

    log "Backing up JSON data..."

    if [ -d "$APP_DIR/backend/data" ]; then
        tar -czf "$data_backup" \
            -C "$APP_DIR/backend" data/ \
            --exclude='data/*.log' \
            --exclude='data/__pycache__' \
            --exclude='data/*.pyc' \
            --exclude='data/.DS_Store' \
            2>/dev/null

        if [ -f "$data_backup" ]; then
            local backup_size=$(du -h "$data_backup" | cut -f1)
            log "JSON data backup completed: $backup_size"
        else
            error_exit "JSON data backup file was not created"
        fi
    else
        log "WARNING: JSON data directory not found: $APP_DIR/backend/data"
    fi
}

backup_env_file() {
    local env_backup="$BACKUP_DIR/env_$DATE.backup"

    log "Backing up environment configuration..."

    if [ -f "$APP_DIR/backend/.env" ]; then
        cp "$APP_DIR/backend/.env" "$env_backup"
        chmod 600 "$env_backup"

        local backup_size=$(du -h "$env_backup" | cut -f1)
        log ".env file backup completed: $backup_size"
    else
        log "WARNING: .env file not found: $APP_DIR/backend/.env"
    fi
}

backup_ssl_certificates() {
    local ssl_backup="$BACKUP_DIR/ssl_$DATE.tar.gz"

    log "Backing up SSL certificates..."

    if [ -d "/etc/ssl/mks" ]; then
        tar -czf "$ssl_backup" -C /etc/ssl mks/ 2>/dev/null && \
        chmod 600 "$ssl_backup" && \
        log "SSL certificates backup completed" || \
        log "WARNING: Failed to backup SSL certificates (may require sudo)"
    else
        log "INFO: SSL certificates directory not found (skipping)"
    fi
}

backup_nginx_config() {
    local nginx_backup="$BACKUP_DIR/nginx_$DATE.conf"

    log "Backing up Nginx configuration..."

    if [ -f "/etc/nginx/sites-available/mirai-knowledge" ]; then
        cp "/etc/nginx/sites-available/mirai-knowledge" "$nginx_backup" 2>/dev/null && \
        chmod 600 "$nginx_backup" && \
        log "Nginx configuration backup completed" || \
        log "WARNING: Failed to backup Nginx config (may require sudo)"
    else
        log "INFO: Nginx configuration not found (skipping)"
    fi
}

backup_systemd_service() {
    local systemd_backup="$BACKUP_DIR/systemd_$DATE.service"

    log "Backing up systemd service file..."

    if [ -f "/etc/systemd/system/mirai-knowledge-prod.service" ]; then
        cp "/etc/systemd/system/mirai-knowledge-prod.service" "$systemd_backup" 2>/dev/null && \
        chmod 600 "$systemd_backup" && \
        log "systemd service backup completed" || \
        log "WARNING: Failed to backup systemd service (may require sudo)"
    else
        log "INFO: systemd service file not found (skipping)"
    fi
}

backup_application_logs() {
    local logs_backup="$BACKUP_DIR/logs_$DATE.tar.gz"

    log "Backing up application logs (last 7 days)..."

    if [ -d "/var/log/mirai-knowledge" ]; then
        find /var/log/mirai-knowledge -type f -mtime -7 -print0 | \
        tar -czf "$logs_backup" --null -T - 2>/dev/null && \
        log "Application logs backup completed" || \
        log "WARNING: Failed to backup logs (may require sudo)"
    else
        log "INFO: Application logs directory not found (skipping)"
    fi
}

create_backup_manifest() {
    local manifest_file="$BACKUP_DIR/manifest_$DATE.txt"

    log "Creating backup manifest..."

    {
        echo "=========================================="
        echo "Mirai Knowledge Systems - Backup Manifest"
        echo "=========================================="
        echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Hostname: $(hostname)"
        echo "User: $(whoami)"
        echo ""
        echo "Backup Files:"
        echo "----------------------------------------"
        ls -lh "$BACKUP_DIR"/*_$DATE.* 2>/dev/null | awk '{print $9, $5}'
        echo ""
        echo "Total Backup Size:"
        du -sh "$BACKUP_DIR" 2>/dev/null | awk '{print $1}'
    } > "$manifest_file"

    log "Backup manifest created: $manifest_file"
}

cleanup_old_backups() {
    log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."

    local deleted_count=0
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file"
            deleted_count=$((deleted_count + 1))
            log "Deleted old backup: $(basename "$file")"
        fi
    done < <(find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS)

    if [ $deleted_count -gt 0 ]; then
        log "Deleted $deleted_count old backup(s)"
    else
        log "No old backups to delete"
    fi
}

list_current_backups() {
    log "Current backup sessions:"

    # Group by date and show summary
    find "$BACKUP_DIR" -name "*_[0-9]*.tar.gz" -o -name "*_[0-9]*.backup" 2>/dev/null | \
    sed 's/.*_\([0-9]*\)_.*/\1/' | sort -u | tail -5 | while read -r session_date; do
        local session_files=$(find "$BACKUP_DIR" -name "*_${session_date}_*" 2>/dev/null | wc -l)
        log "  Session $session_date: $session_files file(s)"
    done

    # Total count
    local total_backups=$(find "$BACKUP_DIR" -type f | wc -l)
    log "Total backup files: $total_backups"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "=========================================="
    log "Application Data Backup Script Started"
    log "=========================================="

    # Check dependencies
    check_dependencies

    # Create backup directory if needed
    create_backup_dir

    # Perform backups
    backup_json_data
    backup_env_file
    backup_ssl_certificates
    backup_nginx_config
    backup_systemd_service
    backup_application_logs

    # Create manifest
    create_backup_manifest

    # Cleanup old backups
    cleanup_old_backups

    # List current backups
    list_current_backups

    log "=========================================="
    log "Application Data Backup Script Completed"
    log "=========================================="
}

# Run main function
main
