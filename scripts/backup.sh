#!/bin/bash
# scripts/backup.sh - バックアップスクリプト

set -e  # エラー発生時に停止

# 設定
BACKUP_DIR="/backup/mks"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/mks-backup.log"

# 関数定義
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# バックアップディレクトリ作成
mkdir -p $BACKUP_DIR

log "=== バックアップ開始 ==="

# データベースバックアップ
log "データベースバックアップ実行..."
if [ -n "$USE_POSTGRESQL" ] && [ "$USE_POSTGRESQL" = "true" ]; then
    # PostgreSQLバックアップ
    pg_dump -U mks_user -d mks_db > $BACKUP_DIR/db_$DATE.dump
    log "PostgreSQLバックアップ完了: db_$DATE.dump"
else
    # SQLiteバックアップ（開発環境）
    cp /opt/mks/backend/dev.db $BACKUP_DIR/db_$DATE.sqlite
    log "SQLiteバックアップ完了: db_$DATE.sqlite"
fi

# アップロードファイルバックアップ
log "アップロードファイルバックアップ実行..."
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/mks/uploads/
log "アップロードファイルバックアップ完了: uploads_$DATE.tar.gz"

# 設定ファイルバックアップ
log "設定ファイルバックアップ実行..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/mks/
log "設定ファイルバックアップ完了: config_$DATE.tar.gz"

# バックアップサイズ確認
DB_SIZE=$(du -h $BACKUP_DIR/db_$DATE.* | cut -f1)
UPLOAD_SIZE=$(du -h $BACKUP_DIR/uploads_$DATE.tar.gz | cut -f1)
CONFIG_SIZE=$(du -h $BACKUP_DIR/config_$DATE.tar.gz | cut -f1)

log "バックアップサイズ - DB: $DB_SIZE, Uploads: $UPLOAD_SIZE, Config: $CONFIG_SIZE"

# 古いバックアップ削除（30日以上前）
log "古いバックアップ削除..."
find $BACKUP_DIR -name "db_*.dump" -mtime +30 -delete
find $BACKUP_DIR -name "db_*.sqlite" -mtime +30 -delete
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 -delete

log "=== バックアップ完了 ==="

# バックアップ一覧表示
log "現在のバックアップ一覧:"
ls -la $BACKUP_DIR/</content>
<parameter name="filePath">scripts/backup.sh