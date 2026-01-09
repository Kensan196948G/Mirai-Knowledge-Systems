#!/bin/bash
################################################################################
# PostgreSQL Backup Script for Mirai Knowledge Systems
# Purpose: Automated PostgreSQL database backup with compression and retention
# Author: Mirai Knowledge Systems
# Version: 1.0.0
################################################################################

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================
BACKUP_DIR="/var/backups/mirai-knowledge/postgresql"
DB_NAME="mirai_knowledge_db"
DB_USER="postgres"
DB_PASSWORD="ELzion1969"
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

    if ! command -v pg_dump &> /dev/null; then
        error_exit "pg_dump not found. Please install postgresql-client."
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

perform_backup() {
    local backup_file="$BACKUP_DIR/db_$DATE.sql.gz"

    log "Starting PostgreSQL backup for database: $DB_NAME"
    log "Backup file: $backup_file"

    # Perform backup with compression
    if PGPASSWORD="$DB_PASSWORD" pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$backup_file"; then
        log "Backup completed successfully"

        # Get backup file size
        if [ -f "$backup_file" ]; then
            local backup_size=$(du -h "$backup_file" | cut -f1)
            log "Backup size: $backup_size"

            # Verify backup file is not empty
            local file_size=$(stat -c%s "$backup_file" 2>/dev/null || stat -f%z "$backup_file" 2>/dev/null)
            if [ "$file_size" -lt 1000 ]; then
                error_exit "Backup file is suspiciously small: $file_size bytes"
            fi

            log "Backup verification passed"
        else
            error_exit "Backup file was not created"
        fi
    else
        error_exit "pg_dump failed"
    fi
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
    done < <(find "$BACKUP_DIR" -name "db_*.sql.gz" -type f -mtime +$RETENTION_DAYS)

    if [ $deleted_count -gt 0 ]; then
        log "Deleted $deleted_count old backup(s)"
    else
        log "No old backups to delete"
    fi
}

list_current_backups() {
    log "Current backups (last 5):"
    ls -lht "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | head -5 | while read -r line; do
        log "  $line"
    done

    # Count total backups
    local total_backups=$(find "$BACKUP_DIR" -name "db_*.sql.gz" -type f | wc -l)
    log "Total backups: $total_backups"
}

send_notification() {
    local status=$1
    local message=$2

    # Optional: Send notification to monitoring system
    # curl -X POST "http://monitoring.example.com/api/alerts" \
    #      -H "Content-Type: application/json" \
    #      -d "{\"status\": \"$status\", \"message\": \"$message\"}"

    log "Notification: [$status] $message"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "=========================================="
    log "PostgreSQL Backup Script Started"
    log "=========================================="

    # Check dependencies
    check_dependencies

    # Create backup directory if needed
    create_backup_dir

    # Perform backup
    perform_backup

    # Cleanup old backups
    cleanup_old_backups

    # List current backups
    list_current_backups

    # Send success notification
    send_notification "success" "PostgreSQL backup completed successfully"

    log "=========================================="
    log "PostgreSQL Backup Script Completed"
    log "=========================================="
}

# Run main function
main
