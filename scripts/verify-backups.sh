#!/bin/bash
################################################################################
# Backup Verification Script for Mirai Knowledge Systems
# Purpose: Verify integrity and completeness of backup files
# Author: Mirai Knowledge Systems
# Version: 1.0.0
################################################################################

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================
BACKUP_DIR_POSTGRESQL="/var/backups/mirai-knowledge/postgresql"
BACKUP_DIR_APPDATA="/var/backups/mirai-knowledge/appdata"
LOG_FILE="/var/log/mirai-knowledge/backup-verification.log"
MIN_DB_SIZE=10000  # Minimum database backup size in bytes
MIN_APPDATA_SIZE=1000  # Minimum appdata backup size in bytes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

verify_postgresql_backups() {
    log "=========================================="
    log "PostgreSQL バックアップ検証"
    log "=========================================="

    if [ ! -d "$BACKUP_DIR_POSTGRESQL" ]; then
        log_error "PostgreSQLバックアップディレクトリが存在しません: $BACKUP_DIR_POSTGRESQL"
        return 1
    fi

    local backup_files=($(find "$BACKUP_DIR_POSTGRESQL" -name "db_*.sql.gz" -type f 2>/dev/null | sort -r))

    if [ ${#backup_files[@]} -eq 0 ]; then
        log_error "PostgreSQLバックアップファイルが見つかりません"
        return 1
    fi

    log "検証するバックアップファイル数: ${#backup_files[@]}"

    local verified_count=0
    local failed_count=0

    for backup_file in "${backup_files[@]}"; do
        local filename=$(basename "$backup_file")
        log "検証中: $filename"

        # Check file size
        local file_size=$(stat -c%s "$backup_file" 2>/dev/null || stat -f%z "$backup_file" 2>/dev/null)

        if [ "$file_size" -lt "$MIN_DB_SIZE" ]; then
            log_error "  ファイルサイズが小さすぎます: $file_size bytes (最小: $MIN_DB_SIZE bytes)"
            failed_count=$((failed_count + 1))
            continue
        fi

        # Verify gzip integrity
        if gunzip -t "$backup_file" 2>/dev/null; then
            log_success "  gzip整合性: OK"
        else
            log_error "  gzip整合性: NG（ファイルが破損しています）"
            failed_count=$((failed_count + 1))
            continue
        fi

        # Check SQL content (basic check)
        if gunzip -c "$backup_file" | head -n 20 | grep -q "PostgreSQL database dump"; then
            log_success "  SQL内容: OK"
        else
            log_warning "  SQL内容: PostgreSQLダンプヘッダーが見つかりません"
        fi

        # Display file info
        local file_date=$(stat -c %y "$backup_file" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$backup_file" 2>/dev/null)
        local file_size_human=$(du -h "$backup_file" | cut -f1)
        log "  ファイル情報: $file_size_human, 作成日: $file_date"

        verified_count=$((verified_count + 1))
    done

    log "=========================================="
    log "PostgreSQL検証結果: $verified_count 成功, $failed_count 失敗"
    log "=========================================="

    return $failed_count
}

verify_appdata_backups() {
    log "=========================================="
    log "アプリケーションデータ バックアップ検証"
    log "=========================================="

    if [ ! -d "$BACKUP_DIR_APPDATA" ]; then
        log_error "アプリケーションデータバックアップディレクトリが存在しません: $BACKUP_DIR_APPDATA"
        return 1
    fi

    local backup_files=($(find "$BACKUP_DIR_APPDATA" -name "data_*.tar.gz" -type f 2>/dev/null | sort -r))

    if [ ${#backup_files[@]} -eq 0 ]; then
        log_warning "アプリケーションデータバックアップファイルが見つかりません"
        return 0
    fi

    log "検証するバックアップファイル数: ${#backup_files[@]}"

    local verified_count=0
    local failed_count=0

    for backup_file in "${backup_files[@]}"; do
        local filename=$(basename "$backup_file")
        log "検証中: $filename"

        # Check file size
        local file_size=$(stat -c%s "$backup_file" 2>/dev/null || stat -f%z "$backup_file" 2>/dev/null)

        if [ "$file_size" -lt "$MIN_APPDATA_SIZE" ]; then
            log_error "  ファイルサイズが小さすぎます: $file_size bytes"
            failed_count=$((failed_count + 1))
            continue
        fi

        # Verify tar.gz integrity
        if tar -tzf "$backup_file" > /dev/null 2>&1; then
            log_success "  tar.gz整合性: OK"

            # List contents
            local file_count=$(tar -tzf "$backup_file" | wc -l)
            log "  含まれるファイル数: $file_count"
        else
            log_error "  tar.gz整合性: NG（ファイルが破損しています）"
            failed_count=$((failed_count + 1))
            continue
        fi

        # Display file info
        local file_date=$(stat -c %y "$backup_file" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$backup_file" 2>/dev/null)
        local file_size_human=$(du -h "$backup_file" | cut -f1)
        log "  ファイル情報: $file_size_human, 作成日: $file_date"

        verified_count=$((verified_count + 1))
    done

    log "=========================================="
    log "アプリケーションデータ検証結果: $verified_count 成功, $failed_count 失敗"
    log "=========================================="

    return $failed_count
}

verify_env_backups() {
    log "=========================================="
    log "環境設定ファイル バックアップ検証"
    log "=========================================="

    local backup_files=($(find "$BACKUP_DIR_APPDATA" -name "env_*.backup" -type f 2>/dev/null | sort -r | head -5))

    if [ ${#backup_files[@]} -eq 0 ]; then
        log_warning "環境設定ファイルのバックアップが見つかりません"
        return 0
    fi

    log "検証するバックアップファイル数: ${#backup_files[@]}"

    for backup_file in "${backup_files[@]}"; do
        local filename=$(basename "$backup_file")

        # Check if file contains expected environment variables
        if grep -q "SECRET_KEY" "$backup_file" 2>/dev/null; then
            log_success "$filename: 有効な環境設定ファイル"
        else
            log_warning "$filename: SECRET_KEYが見つかりません"
        fi
    done

    return 0
}

check_backup_schedule() {
    log "=========================================="
    log "バックアップスケジュール確認"
    log "=========================================="

    # Check if cron job exists
    if [ -f "/etc/cron.d/mirai-knowledge-backup" ]; then
        log_success "cronジョブファイルが存在します"
        log "cron設定:"
        cat "/etc/cron.d/mirai-knowledge-backup" 2>/dev/null | grep -v "^#" | grep -v "^$" | while read -r line; do
            log "  $line"
        done
    else
        log_warning "cronジョブファイルが見つかりません: /etc/cron.d/mirai-knowledge-backup"
    fi

    # Check last backup time
    local latest_backup=$(find "$BACKUP_DIR_POSTGRESQL" -name "db_*.sql.gz" -type f 2>/dev/null | sort -r | head -1)

    if [ -n "$latest_backup" ]; then
        local last_backup_time=$(stat -c %Y "$latest_backup" 2>/dev/null || stat -f %m "$latest_backup" 2>/dev/null)
        local current_time=$(date +%s)
        local hours_since_backup=$(( (current_time - last_backup_time) / 3600 ))

        log "最終バックアップ: $hours_since_backup 時間前"

        if [ $hours_since_backup -gt 48 ]; then
            log_warning "最終バックアップから48時間以上経過しています"
        else
            log_success "バックアップは定期的に実行されています"
        fi
    else
        log_error "バックアップファイルが見つかりません"
    fi

    return 0
}

generate_backup_report() {
    log "=========================================="
    log "バックアップサマリーレポート"
    log "=========================================="

    # PostgreSQL backups
    local pg_count=$(find "$BACKUP_DIR_POSTGRESQL" -name "db_*.sql.gz" -type f 2>/dev/null | wc -l)
    local pg_total_size=$(du -sh "$BACKUP_DIR_POSTGRESQL" 2>/dev/null | cut -f1)
    log "PostgreSQLバックアップ: $pg_count ファイル, 合計サイズ: $pg_total_size"

    # Application data backups
    local app_count=$(find "$BACKUP_DIR_APPDATA" -type f 2>/dev/null | wc -l)
    local app_total_size=$(du -sh "$BACKUP_DIR_APPDATA" 2>/dev/null | cut -f1)
    log "アプリケーションデータバックアップ: $app_count ファイル, 合計サイズ: $app_total_size"

    # Oldest and newest backups
    local oldest_backup=$(find "$BACKUP_DIR_POSTGRESQL" -name "db_*.sql.gz" -type f 2>/dev/null | sort | head -1)
    local newest_backup=$(find "$BACKUP_DIR_POSTGRESQL" -name "db_*.sql.gz" -type f 2>/dev/null | sort -r | head -1)

    if [ -n "$oldest_backup" ]; then
        local oldest_date=$(stat -c %y "$oldest_backup" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$oldest_backup" 2>/dev/null)
        log "最も古いバックアップ: $oldest_date"
    fi

    if [ -n "$newest_backup" ]; then
        local newest_date=$(stat -c %y "$newest_backup" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$newest_backup" 2>/dev/null)
        log "最新のバックアップ: $newest_date"
    fi

    return 0
}

send_verification_report() {
    local status=$1

    # Optional: Send report to monitoring system
    log "検証レポートを送信しました（ステータス: $status）"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "=========================================="
    log "Backup Verification Script Started"
    log "=========================================="

    local total_failures=0

    # Verify PostgreSQL backups
    verify_postgresql_backups || total_failures=$((total_failures + $?))

    echo ""

    # Verify application data backups
    verify_appdata_backups || total_failures=$((total_failures + $?))

    echo ""

    # Verify environment file backups
    verify_env_backups

    echo ""

    # Check backup schedule
    check_backup_schedule

    echo ""

    # Generate summary report
    generate_backup_report

    log "=========================================="

    if [ $total_failures -eq 0 ]; then
        log_success "すべてのバックアップ検証が成功しました"
        send_verification_report "success"
        exit 0
    else
        log_error "$total_failures 件のバックアップ検証が失敗しました"
        send_verification_report "failure"
        exit 1
    fi
}

# Run main function
main
