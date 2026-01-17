#!/bin/bash
################################################################################
# PostgreSQL Restore Script for Mirai Knowledge Systems
# Purpose: Restore PostgreSQL database from backup file
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
LOG_FILE="/var/log/mirai-knowledge/restore.log"
SERVICE_NAME="mirai-knowledge-prod"

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

error_exit() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

print_usage() {
    cat << EOF
使用方法: $0 <backup_file.sql.gz>

PostgreSQLデータベースをバックアップからリストアします。

引数:
  backup_file.sql.gz    リストアするバックアップファイル（フルパスまたは相対パス）

例:
  $0 /var/backups/mirai-knowledge/postgresql/db_20260109_083000.sql.gz
  $0 db_20260109_083000.sql.gz

利用可能なバックアップファイル:
EOF
    list_available_backups
}

list_available_backups() {
    if [ -d "$BACKUP_DIR" ]; then
        echo ""
        ls -lht "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | head -10 | awk '{print "  " $9, "(" $5 ")", $6, $7, $8}'
        echo ""
        local total=$(find "$BACKUP_DIR" -name "db_*.sql.gz" | wc -l)
        echo "  合計: $total ファイル"
    else
        echo "  バックアップディレクトリが見つかりません: $BACKUP_DIR"
    fi
}

check_dependencies() {
    log "依存関係を確認中..."

    if ! command -v psql &> /dev/null; then
        error_exit "psql not found. Please install postgresql-client."
    fi

    if ! command -v gunzip &> /dev/null; then
        error_exit "gunzip not found. Please install gzip."
    fi

    log "すべての依存関係が確認されました"
}

validate_backup_file() {
    local backup_file=$1

    log "バックアップファイルを検証中: $backup_file"

    # Check if file exists
    if [ ! -f "$backup_file" ]; then
        error_exit "バックアップファイルが見つかりません: $backup_file"
    fi

    # Check if file is readable
    if [ ! -r "$backup_file" ]; then
        error_exit "バックアップファイルを読み取れません: $backup_file"
    fi

    # Check file size
    local file_size=$(stat -c%s "$backup_file" 2>/dev/null || stat -f%z "$backup_file" 2>/dev/null)
    if [ "$file_size" -lt 1000 ]; then
        error_exit "バックアップファイルが小さすぎます: $file_size bytes"
    fi

    # Verify gzip integrity
    if ! gunzip -t "$backup_file" 2>/dev/null; then
        error_exit "バックアップファイルが破損しています（gzip検証失敗）"
    fi

    log "バックアップファイルの検証に成功しました"
}

check_database_connection() {
    log "データベース接続を確認中..."

    if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h localhost -d postgres -c '\q' 2>/dev/null; then
        log "データベース接続成功"
    else
        error_exit "データベースに接続できません。PostgreSQLが起動しているか確認してください"
    fi
}

create_backup_before_restore() {
    log "リストア前の安全バックアップを作成中..."

    local safety_backup="$BACKUP_DIR/safety_before_restore_$(date +%Y%m%d_%H%M%S).sql.gz"

    if PGPASSWORD="$DB_PASSWORD" pg_dump -U "$DB_USER" -h localhost "$DB_NAME" 2>/dev/null | gzip > "$safety_backup"; then
        log "安全バックアップ作成完了: $safety_backup"
        echo "$safety_backup"
    else
        log "WARNING: 安全バックアップの作成に失敗しました（データベースが存在しない可能性があります）"
        echo ""
    fi
}

stop_application_service() {
    log "アプリケーションサービスを停止中..."

    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        if sudo systemctl stop "$SERVICE_NAME" 2>/dev/null; then
            log "サービス $SERVICE_NAME を停止しました"
            return 0
        else
            log "WARNING: サービスの停止にsudoが必要です（手動で停止してください）"
            return 1
        fi
    else
        log "サービス $SERVICE_NAME は稼働していません"
        return 0
    fi
}

start_application_service() {
    log "アプリケーションサービスを起動中..."

    if sudo systemctl start "$SERVICE_NAME" 2>/dev/null; then
        log "サービス $SERVICE_NAME を起動しました"

        # Wait for service to be active
        sleep 2

        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log "サービスが正常に起動しました"
        else
            log "WARNING: サービスの起動を確認できませんでした"
        fi
    else
        log "WARNING: サービスの起動にsudoが必要です（手動で起動してください）"
    fi
}

perform_restore() {
    local backup_file=$1

    log "リストアを実行中: $backup_file"
    log "データベース: $DB_NAME"

    # Drop and recreate database (optional, safer to just restore)
    echo -e "${YELLOW}警告: 既存のデータは上書きされます${NC}"

    # Restore database
    if gunzip -c "$backup_file" | PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h localhost "$DB_NAME" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ リストアが正常に完了しました${NC}"
        log "リストアが正常に完了しました"
    else
        echo -e "${RED}❌ リストアに失敗しました${NC}"
        error_exit "psqlコマンドが失敗しました"
    fi
}

verify_restore() {
    log "リストア結果を検証中..."

    # Count tables
    local table_count=$(PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h localhost "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

    if [ "$table_count" -gt 0 ]; then
        log "データベーステーブル数: $table_count"
        echo -e "${GREEN}✅ データベース検証成功（$table_count テーブル）${NC}"
    else
        log "WARNING: テーブルが見つかりませんでした"
        echo -e "${YELLOW}⚠️  警告: テーブルが見つかりません${NC}"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "=========================================="
    log "PostgreSQL Restore Script Started"
    log "=========================================="

    # Check if backup file is provided
    if [ $# -eq 0 ]; then
        print_usage
        exit 1
    fi

    BACKUP_FILE=$1

    # If relative path, prepend backup directory
    if [[ "$BACKUP_FILE" != /* ]]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    fi

    echo ""
    echo -e "${YELLOW}=========================================="
    echo "Mirai Knowledge Systems"
    echo "PostgreSQL Database Restore"
    echo "==========================================${NC}"
    echo ""
    echo "バックアップファイル: $BACKUP_FILE"
    echo "データベース: $DB_NAME"
    echo ""

    # Validate backup file
    validate_backup_file "$BACKUP_FILE"

    # Confirm with user
    echo -e "${RED}警告: この操作はデータベース $DB_NAME を上書きします${NC}"
    echo ""
    read -p "本当にリストアを実行しますか? (yes/no): " CONFIRM
    echo ""

    if [ "$CONFIRM" != "yes" ]; then
        echo "リストアをキャンセルしました"
        exit 0
    fi

    # Check dependencies
    check_dependencies

    # Check database connection
    check_database_connection

    # Create safety backup
    SAFETY_BACKUP=$(create_backup_before_restore)

    # Stop application service
    SERVICE_STOPPED=0
    if stop_application_service; then
        SERVICE_STOPPED=1
    fi

    # Perform restore
    perform_restore "$BACKUP_FILE"

    # Verify restore
    verify_restore

    # Start application service
    if [ $SERVICE_STOPPED -eq 1 ]; then
        start_application_service
    fi

    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ リストア完了"
    echo "==========================================${NC}"
    echo ""

    if [ -n "$SAFETY_BACKUP" ]; then
        echo "安全バックアップ: $SAFETY_BACKUP"
    fi

    log "=========================================="
    log "PostgreSQL Restore Script Completed"
    log "=========================================="
}

# Run main function
main "$@"
