#!/bin/bash
# scripts/restore.sh - リストアスクリプト

set -e  # エラー発生時に停止

# 設定
BACKUP_DIR="/backup/mks"
LOG_FILE="/var/log/mks-restore.log"

# 関数定義
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

usage() {
    echo "使用方法: $0 <backup-date>"
    echo "例: $0 20240109_020000"
    echo ""
    echo "利用可能なバックアップ:"
    ls -la $BACKUP_DIR/db_* | head -10
    exit 1
}

# 引数チェック
if [ $# -eq 0 ]; then
    usage
fi

BACKUP_DATE=$1

log "=== リストア開始: $BACKUP_DATE ==="

# バックアップファイル存在確認
DB_BACKUP="$BACKUP_DIR/db_$BACKUP_DATE.dump"
if [ -n "$USE_POSTGRESQL" ] && [ "$USE_POSTGRESQL" = "true" ]; then
    DB_BACKUP="$BACKUP_DIR/db_$BACKUP_DATE.dump"
else
    DB_BACKUP="$BACKUP_DIR/db_$BACKUP_DATE.sqlite"
fi

UPLOAD_BACKUP="$BACKUP_DIR/uploads_$BACKUP_DATE.tar.gz"
CONFIG_BACKUP="$BACKUP_DIR/config_$BACKUP_DATE.tar.gz"

if [ ! -f "$DB_BACKUP" ]; then
    error_exit "データベースバックアップが見つかりません: $DB_BACKUP"
fi

log "バックアップファイル確認完了"

# サービス停止
log "サービス停止..."
sudo systemctl stop mks-backend

# データベースリストア
log "データベースリストア実行..."
if [ -n "$USE_POSTGRESQL" ] && [ "$USE_POSTGRESQL" = "true" ]; then
    # PostgreSQLリストア
    psql -U postgres -c "DROP DATABASE IF EXISTS mks_db;"
    psql -U postgres -c "CREATE DATABASE mks_db OWNER mks_user;"
    pg_restore -U mks_user -d mks_db --clean --if-exists $DB_BACKUP
    log "PostgreSQLリストア完了"
else
    # SQLiteリストア
    cp $DB_BACKUP /opt/mks/backend/dev.db
    log "SQLiteリストア完了"
fi

# アップロードファイルリストア
if [ -f "$UPLOAD_BACKUP" ]; then
    log "アップロードファイルリストア実行..."
    rm -rf /opt/mks/uploads/*
    tar -xzf $UPLOAD_BACKUP -C /
    chown -R mks:mks /opt/mks/uploads/
    log "アップロードファイルリストア完了"
else
    log "アップロードバックアップが見つからないためスキップ"
fi

# 設定ファイルリストア
if [ -f "$CONFIG_BACKUP" ]; then
    log "設定ファイルリストア実行..."
    tar -xzf $CONFIG_BACKUP -C /
    log "設定ファイルリストア完了"
else
    log "設定バックアップが見つからないためスキップ"
fi

# サービス起動
log "サービス起動..."
sudo systemctl start mks-backend

# ヘルスチェック
log "ヘルスチェック実行..."
sleep 10
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:5100/api/v1/health > /dev/null 2>&1; then
        log "ヘルスチェック成功"
        break
    else
        log "ヘルスチェック失敗、再試行..."
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    error_exit "ヘルスチェック失敗"
fi

log "=== リストア完了 ==="

# データ確認
if [ -n "$USE_POSTGRESQL" ] && [ "$USE_POSTGRESQL" = "true" ]; then
    PROJECTS_COUNT=$(psql -U mks_user -d mks_db -t -c "SELECT COUNT(*) FROM projects;")
    USERS_COUNT=$(psql -U mks_user -d mks_db -t -c "SELECT COUNT(*) FROM users;")
else
    PROJECTS_COUNT="SQLite - 確認不可"
    USERS_COUNT="SQLite - 確認不可"
fi

log "リストア結果 - Projects: $PROJECTS_COUNT, Users: $USERS_COUNT"</content>
<parameter name="filePath">scripts/restore.sh