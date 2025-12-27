# バックアップ・リストア詳細手順

建設土木ナレッジシステムのバックアップとリストアの詳細手順を定義します。

## 目次

1. [バックアップ戦略](#バックアップ戦略)
2. [バックアップスケジュール](#バックアップスケジュール)
3. [バックアップスクリプト詳細](#バックアップスクリプト詳細)
4. [リストア手順](#リストア手順)
5. [バックアップ検証手順](#バックアップ検証手順)
6. [リモートストレージ連携](#リモートストレージ連携)
7. [災害復旧（DR）計画](#災害復旧dr計画)

---

## バックアップ戦略

### バックアップの種類

#### 1. フルバックアップ

**概要:**
- 全データを完全にバックアップ
- リストアが最も簡単
- ストレージ容量が大きい

**実施頻度:**
- 本番環境: 毎日1回（深夜）
- 開発環境: 毎週1回

**対象データ:**
- JSONデータベースファイル（users.json, knowledges.json等）
- アップロードファイル
- 設定ファイル
- SSL証明書

**保持期間:**
- 日次: 30日間
- 週次: 12週間（3ヶ月）
- 月次: 12ヶ月

---

#### 2. 増分バックアップ

**概要:**
- 前回のバックアップ以降の変更分のみバックアップ
- ストレージ効率が良い
- リストアに複数ファイルが必要

**実施頻度:**
- 本番環境: 6時間ごと
- 開発環境: 実施しない

**対象データ:**
- 変更されたJSONファイル
- 新規アップロードファイル
- 変更された設定ファイル

**保持期間:**
- 直近7日分

---

#### 3. スナップショット

**概要:**
- 特定時点の完全な状態を保存
- メジャーリリース前、重要な変更前に実施

**実施タイミング:**
- システムアップグレード前
- データベース移行前
- 大規模な設定変更前

**保持期間:**
- 6ヶ月間

---

### データの優先順位

| 優先度 | データ種類 | RPO | RTO | バックアップ頻度 |
|--------|------------|-----|-----|------------------|
| P1（最優先） | ユーザーデータ（users.json） | 6時間 | 1時間 | 6時間ごと |
| P1（最優先） | ナレッジデータ（knowledges.json） | 6時間 | 1時間 | 6時間ごと |
| P2（高） | アクセスログ（access_logs.json） | 24時間 | 4時間 | 日次 |
| P2（高） | アップロードファイル | 24時間 | 4時間 | 日次 |
| P3（中） | 設定ファイル | 24時間 | 4時間 | 日次 |
| P4（低） | ログファイル | 7日 | 1日 | 週次 |

**RPO (Recovery Point Objective):** 許容されるデータ損失時間
**RTO (Recovery Time Objective):** 許容される復旧時間

---

## バックアップスケジュール

### 本番環境のスケジュール

```
日次フルバックアップ:      毎日 03:00
増分バックアップ:          毎日 09:00, 15:00, 21:00
週次フルバックアップ:      毎週日曜 02:00
月次フルバックアップ:      毎月1日 01:00
リモートストレージ同期:    毎日 04:00
バックアップ検証:          毎日 05:00
古いバックアップ削除:      毎日 06:00
```

### cron設定例

```bash
# crontab -e

# 日次フルバックアップ（毎日3:00）
0 3 * * * /usr/local/bin/backup_full.sh >> /var/log/backup.log 2>&1

# 増分バックアップ（9時、15時、21時）
0 9,15,21 * * * /usr/local/bin/backup_incremental.sh >> /var/log/backup.log 2>&1

# 週次フルバックアップ（毎週日曜2:00）
0 2 * * 0 /usr/local/bin/backup_weekly.sh >> /var/log/backup.log 2>&1

# 月次フルバックアップ（毎月1日1:00）
0 1 1 * * /usr/local/bin/backup_monthly.sh >> /var/log/backup.log 2>&1

# リモートストレージ同期（毎日4:00）
0 4 * * * /usr/local/bin/sync_to_remote.sh >> /var/log/backup.log 2>&1

# バックアップ検証（毎日5:00）
0 5 * * * /usr/local/bin/verify_backup.sh >> /var/log/backup.log 2>&1

# 古いバックアップ削除（毎日6:00）
0 6 * * * /usr/local/bin/cleanup_old_backups.sh >> /var/log/backup.log 2>&1
```

---

## バックアップスクリプト詳細

### フルバックアップスクリプト

```bash
#!/bin/bash
# /usr/local/bin/backup_full.sh
#
# 建設土木ナレッジシステム - フルバックアップスクリプト
#

set -e

# ==========================================================
# 設定
# ==========================================================

# バックアップ元
SOURCE_DIR="/var/lib/mirai-knowledge-system"
DATA_DIR="${SOURCE_DIR}/data"
CONFIG_DIR="${SOURCE_DIR}/config"
UPLOADS_DIR="${SOURCE_DIR}/uploads"
SSL_DIR="/etc/letsencrypt/live"

# バックアップ先
BACKUP_ROOT="/backup/mirai-knowledge-system"
BACKUP_TYPE="daily"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_TYPE}/${TIMESTAMP}"

# 保持期間（日数）
RETENTION_DAYS=30

# ログ
LOG_FILE="/var/log/backup.log"

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ==========================================================
# 関数定義
# ==========================================================

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1" | tee -a "$LOG_FILE"
}

# ==========================================================
# 事前チェック
# ==========================================================

log "=== バックアップ開始 (Full Backup) ==="

# ディレクトリ存在確認
if [ ! -d "$DATA_DIR" ]; then
    log_error "データディレクトリが見つかりません: $DATA_DIR"
    exit 1
fi

# バックアップディレクトリ作成
mkdir -p "$BACKUP_DIR"/{data,config,uploads,ssl,logs}

# ディスク容量確認
REQUIRED_SPACE=$(du -sb "$SOURCE_DIR" | awk '{print $1}')
AVAILABLE_SPACE=$(df -B1 "$BACKUP_ROOT" | tail -1 | awk '{print $4}')

if [ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]; then
    log_error "ディスク容量不足: 必要 ${REQUIRED_SPACE} バイト, 利用可能 ${AVAILABLE_SPACE} バイト"
    exit 1
fi

# ==========================================================
# バックアップ実行
# ==========================================================

log "バックアップディレクトリ: $BACKUP_DIR"

# 1. データファイルのバックアップ
log "データファイルをバックアップしています..."
if [ -d "$DATA_DIR" ]; then
    cp -r "$DATA_DIR"/* "$BACKUP_DIR/data/" 2>/dev/null || true
    log "データファイルのバックアップ完了"
else
    log_warn "データディレクトリが見つかりません: $DATA_DIR"
fi

# 2. 設定ファイルのバックアップ
log "設定ファイルをバックアップしています..."
if [ -d "$CONFIG_DIR" ]; then
    cp -r "$CONFIG_DIR"/* "$BACKUP_DIR/config/" 2>/dev/null || true
    log "設定ファイルのバックアップ完了"
else
    log_warn "設定ディレクトリが見つかりません: $CONFIG_DIR"
fi

# 環境変数ファイル
if [ -f "${SOURCE_DIR}/.env.production" ]; then
    cp "${SOURCE_DIR}/.env.production" "$BACKUP_DIR/config/"
fi

# 3. アップロードファイルのバックアップ
log "アップロードファイルをバックアップしています..."
if [ -d "$UPLOADS_DIR" ]; then
    cp -r "$UPLOADS_DIR"/* "$BACKUP_DIR/uploads/" 2>/dev/null || true
    log "アップロードファイルのバックアップ完了"
else
    log_warn "アップロードディレクトリが見つかりません: $UPLOADS_DIR"
fi

# 4. SSL証明書のバックアップ
log "SSL証明書をバックアップしています..."
if [ -d "$SSL_DIR" ]; then
    # Let's Encrypt証明書をバックアップ
    cp -rL "$SSL_DIR" "$BACKUP_DIR/ssl/" 2>/dev/null || true
    log "SSL証明書のバックアップ完了"
else
    log_warn "SSL証明書ディレクトリが見つかりません: $SSL_DIR"
fi

# 5. ログファイルのバックアップ（オプション）
log "ログファイルをバックアップしています..."
if [ -d "/var/log/mirai-knowledge-system" ]; then
    cp -r /var/log/mirai-knowledge-system/*.log "$BACKUP_DIR/logs/" 2>/dev/null || true
    log "ログファイルのバックアップ完了"
fi

# 6. メタデータ作成
log "メタデータを作成しています..."
cat > "$BACKUP_DIR/backup_metadata.json" << EOF
{
    "backup_type": "full",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "source_dir": "$SOURCE_DIR",
    "backup_size_bytes": $(du -sb "$BACKUP_DIR" | awk '{print $1}'),
    "files_count": $(find "$BACKUP_DIR" -type f | wc -l),
    "version": "1.0"
}
EOF

# 7. チェックサムファイル作成
log "チェックサムファイルを作成しています..."
cd "$BACKUP_DIR"
find . -type f ! -name "checksums.sha256" -exec sha256sum {} \; > checksums.sha256
cd - > /dev/null

# 8. バックアップの圧縮（オプション）
if [ "${COMPRESS_BACKUP:-false}" = "true" ]; then
    log "バックアップを圧縮しています..."
    tar -czf "${BACKUP_DIR}.tar.gz" -C "$BACKUP_ROOT/$BACKUP_TYPE" "$TIMESTAMP"
    rm -rf "$BACKUP_DIR"
    BACKUP_FILE="${BACKUP_DIR}.tar.gz"
    log "圧縮完了: $BACKUP_FILE"
fi

# ==========================================================
# バックアップ検証
# ==========================================================

log "バックアップを検証しています..."

# JSONファイルの整合性チェック
for json_file in "$BACKUP_DIR/data"/*.json; do
    if [ -f "$json_file" ]; then
        if ! python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
            log_error "JSONファイルが破損しています: $json_file"
            exit 1
        fi
    fi
done

log "バックアップ検証完了"

# ==========================================================
# 統計情報
# ==========================================================

BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | awk '{print $1}')
FILES_COUNT=$(find "$BACKUP_DIR" -type f | wc -l)

log "=== バックアップ完了 ==="
log "バックアップサイズ: $BACKUP_SIZE"
log "ファイル数: $FILES_COUNT"
log "保存先: $BACKUP_DIR"

# Slack通知（オプション）
if [ -n "${MKS_SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "$MKS_SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"Backup completed successfully\nSize: $BACKUP_SIZE\nFiles: $FILES_COUNT\"}" \
        2>/dev/null || true
fi

exit 0
```

---

### 増分バックアップスクリプト

```bash
#!/bin/bash
# /usr/local/bin/backup_incremental.sh
#
# 建設土木ナレッジシステム - 増分バックアップスクリプト
#

set -e

# ==========================================================
# 設定
# ==========================================================

SOURCE_DIR="/var/lib/mirai-knowledge-system"
DATA_DIR="${SOURCE_DIR}/data"
BACKUP_ROOT="/backup/mirai-knowledge-system"
BACKUP_TYPE="incremental"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_TYPE}/${TIMESTAMP}"

# 前回のバックアップ時刻を記録するファイル
TIMESTAMP_FILE="${BACKUP_ROOT}/.last_backup_timestamp"

# 保持期間（日数）
RETENTION_DAYS=7

LOG_FILE="/var/log/backup.log"

# ==========================================================
# 関数定義
# ==========================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE"
}

# ==========================================================
# 増分バックアップ実行
# ==========================================================

log "=== 増分バックアップ開始 ==="

mkdir -p "$BACKUP_DIR/data"

# 前回のタイムスタンプ取得
if [ -f "$TIMESTAMP_FILE" ]; then
    LAST_BACKUP=$(cat "$TIMESTAMP_FILE")
    log "前回のバックアップ: $LAST_BACKUP"
else
    log "初回の増分バックアップです"
    LAST_BACKUP=$(date -d "1 hour ago" +%Y%m%d%H%M%S)
fi

# 変更されたファイルのみコピー
log "変更されたファイルを検索しています..."
CHANGED_FILES=0

# データファイルの増分バックアップ
find "$DATA_DIR" -type f -newer "$TIMESTAMP_FILE" 2>/dev/null | while read file; do
    RELATIVE_PATH="${file#$DATA_DIR/}"
    DEST_DIR=$(dirname "$BACKUP_DIR/data/$RELATIVE_PATH")
    mkdir -p "$DEST_DIR"
    cp "$file" "$DEST_DIR/"
    CHANGED_FILES=$((CHANGED_FILES + 1))
done

if [ $CHANGED_FILES -eq 0 ]; then
    log "変更されたファイルはありません"
    rmdir "$BACKUP_DIR/data" 2>/dev/null || true
    rmdir "$BACKUP_DIR" 2>/dev/null || true
else
    log "$CHANGED_FILES 個のファイルをバックアップしました"

    # メタデータ作成
    cat > "$BACKUP_DIR/backup_metadata.json" << EOF
{
    "backup_type": "incremental",
    "timestamp": "$(date -Iseconds)",
    "base_backup": "$LAST_BACKUP",
    "changed_files": $CHANGED_FILES
}
EOF
fi

# タイムスタンプ更新
date +%Y%m%d%H%M%S > "$TIMESTAMP_FILE"

log "=== 増分バックアップ完了 ==="

exit 0
```

---

### 古いバックアップの削除スクリプト

```bash
#!/bin/bash
# /usr/local/bin/cleanup_old_backups.sh
#
# 古いバックアップファイルを削除
#

set -e

BACKUP_ROOT="/backup/mirai-knowledge-system"
LOG_FILE="/var/log/backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 古いバックアップのクリーンアップ開始 ==="

# 日次バックアップ: 30日以上古いものを削除
log "日次バックアップのクリーンアップ..."
find "$BACKUP_ROOT/daily" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

# 増分バックアップ: 7日以上古いものを削除
log "増分バックアップのクリーンアップ..."
find "$BACKUP_ROOT/incremental" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true

# 週次バックアップ: 12週以上古いものを削除
log "週次バックアップのクリーンアップ..."
find "$BACKUP_ROOT/weekly" -type d -mtime +84 -exec rm -rf {} \; 2>/dev/null || true

# 月次バックアップ: 12ヶ月以上古いものを削除
log "月次バックアップのクリーンアップ..."
find "$BACKUP_ROOT/monthly" -type d -mtime +365 -exec rm -rf {} \; 2>/dev/null || true

# ディスク使用量確認
DISK_USAGE=$(du -sh "$BACKUP_ROOT" | awk '{print $1}')
log "バックアップディスク使用量: $DISK_USAGE"

log "=== クリーンアップ完了 ==="

exit 0
```

---

## リストア手順

### 完全リストア（システム全体）

#### ステップ1: 事前準備

```bash
# 1. システム停止
cd /path/to/backend
./run_production.sh stop

# 2. 現在のデータをバックアップ（念のため）
BACKUP_CURRENT="/tmp/backup_before_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_CURRENT"
cp -r /var/lib/mirai-knowledge-system/data "$BACKUP_CURRENT/"

# 3. バックアップファイルの確認
RESTORE_SOURCE="/backup/mirai-knowledge-system/daily/20250127_030000"
ls -lah "$RESTORE_SOURCE"

# 4. バックアップの整合性確認
cd "$RESTORE_SOURCE"
sha256sum -c checksums.sha256
```

#### ステップ2: データリストア

```bash
# 1. データディレクトリのリストア
log "データファイルをリストアしています..."
rm -rf /var/lib/mirai-knowledge-system/data/*
cp -r "$RESTORE_SOURCE/data"/* /var/lib/mirai-knowledge-system/data/

# 2. パーミッション設定
chown -R www-data:www-data /var/lib/mirai-knowledge-system/data
chmod 755 /var/lib/mirai-knowledge-system/data
chmod 644 /var/lib/mirai-knowledge-system/data/*.json

# 3. JSONファイルの整合性確認
for json_file in /var/lib/mirai-knowledge-system/data/*.json; do
    echo "Checking $json_file..."
    python3 -c "import json; json.load(open('$json_file'))"
done
```

#### ステップ3: 設定ファイルのリストア

```bash
# 設定ファイルのリストア
cp -r "$RESTORE_SOURCE/config"/* /var/lib/mirai-knowledge-system/config/

# 環境変数ファイル
cp "$RESTORE_SOURCE/config/.env.production" /var/lib/mirai-knowledge-system/
```

#### ステップ4: アップロードファイルのリストア

```bash
# アップロードファイルのリストア
rm -rf /var/lib/mirai-knowledge-system/uploads/*
cp -r "$RESTORE_SOURCE/uploads"/* /var/lib/mirai-knowledge-system/uploads/

# パーミッション設定
chown -R www-data:www-data /var/lib/mirai-knowledge-system/uploads
```

#### ステップ5: SSL証明書のリストア（必要な場合）

```bash
# SSL証明書のリストア
cp -r "$RESTORE_SOURCE/ssl"/* /etc/letsencrypt/live/

# パーミッション設定
chmod 600 /etc/letsencrypt/live/*/privkey.pem
```

#### ステップ6: システム起動と検証

```bash
# 1. システム起動
cd /path/to/backend
./run_production.sh start

# 2. プロセス確認
./run_production.sh status

# 3. ヘルスチェック
curl -v https://api.example.com/health

# 4. ログ確認
tail -f logs/error.log
tail -f logs/access.log

# 5. 機能テスト
# - ログイン機能
# - ナレッジ検索
# - ナレッジ作成
# - ユーザー管理
```

---

### 部分リストア（特定ファイルのみ）

#### 単一JSONファイルのリストア

```bash
#!/bin/bash
# 単一ファイルのリストア例

RESTORE_SOURCE="/backup/mirai-knowledge-system/daily/20250127_030000"
TARGET_FILE="knowledges.json"
DATA_DIR="/var/lib/mirai-knowledge-system/data"

# 1. 現在のファイルをバックアップ
cp "$DATA_DIR/$TARGET_FILE" "$DATA_DIR/${TARGET_FILE}.before_restore"

# 2. バックアップから復元
cp "$RESTORE_SOURCE/data/$TARGET_FILE" "$DATA_DIR/$TARGET_FILE"

# 3. パーミッション設定
chown www-data:www-data "$DATA_DIR/$TARGET_FILE"
chmod 644 "$DATA_DIR/$TARGET_FILE"

# 4. JSON整合性チェック
python3 -c "import json; json.load(open('$DATA_DIR/$TARGET_FILE'))"

# 5. アプリケーション再起動（必要に応じて）
cd /path/to/backend
./run_production.sh reload  # グレースフルリロード
# または
./run_production.sh restart  # 完全再起動

echo "リストア完了: $TARGET_FILE"
```

---

### リストアスクリプト（全自動）

```bash
#!/bin/bash
# /usr/local/bin/restore_full.sh
#
# 建設土木ナレッジシステム - 完全リストアスクリプト
#

set -e

# ==========================================================
# 設定
# ==========================================================

RESTORE_SOURCE="$1"
TARGET_DIR="/var/lib/mirai-knowledge-system"
BACKEND_DIR="/path/to/backend"
LOG_FILE="/var/log/restore.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ==========================================================
# 関数定義
# ==========================================================

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1" | tee -a "$LOG_FILE"
}

# ==========================================================
# 引数チェック
# ==========================================================

if [ -z "$RESTORE_SOURCE" ]; then
    echo "使用方法: $0 <リストア元ディレクトリ>"
    echo ""
    echo "例: $0 /backup/mirai-knowledge-system/daily/20250127_030000"
    exit 1
fi

if [ ! -d "$RESTORE_SOURCE" ]; then
    log_error "リストア元ディレクトリが見つかりません: $RESTORE_SOURCE"
    exit 1
fi

# ==========================================================
# 確認プロンプト
# ==========================================================

log "=== リストア準備 ==="
log "リストア元: $RESTORE_SOURCE"
log "リストア先: $TARGET_DIR"
log ""
log_warn "この操作は現在のデータを上書きします。"
read -p "続行しますか? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log "リストアをキャンセルしました"
    exit 0
fi

# ==========================================================
# リストア実行
# ==========================================================

log "=== リストア開始 ==="

# 1. システム停止
log "アプリケーションを停止しています..."
cd "$BACKEND_DIR"
./run_production.sh stop || log_warn "アプリケーションは既に停止しています"

# 2. 現在のデータをバックアップ
BACKUP_CURRENT="/tmp/backup_before_restore_$(date +%Y%m%d_%H%M%S)"
log "現在のデータをバックアップしています: $BACKUP_CURRENT"
mkdir -p "$BACKUP_CURRENT"
cp -r "$TARGET_DIR/data" "$BACKUP_CURRENT/" 2>/dev/null || true

# 3. チェックサム検証
log "バックアップの整合性を検証しています..."
cd "$RESTORE_SOURCE"
if [ -f "checksums.sha256" ]; then
    if sha256sum -c checksums.sha256 > /dev/null 2>&1; then
        log "チェックサム検証成功"
    else
        log_error "チェックサム検証失敗"
        exit 1
    fi
else
    log_warn "チェックサムファイルが見つかりません"
fi

# 4. データのリストア
log "データファイルをリストアしています..."
rm -rf "$TARGET_DIR/data"/*
cp -r "$RESTORE_SOURCE/data"/* "$TARGET_DIR/data/"
chown -R www-data:www-data "$TARGET_DIR/data"
chmod 755 "$TARGET_DIR/data"
find "$TARGET_DIR/data" -type f -exec chmod 644 {} \;

# 5. 設定ファイルのリストア
log "設定ファイルをリストアしています..."
cp -r "$RESTORE_SOURCE/config"/* "$TARGET_DIR/config/" 2>/dev/null || true

# 6. アップロードファイルのリストア
log "アップロードファイルをリストアしています..."
rm -rf "$TARGET_DIR/uploads"/*
cp -r "$RESTORE_SOURCE/uploads"/* "$TARGET_DIR/uploads/" 2>/dev/null || true
chown -R www-data:www-data "$TARGET_DIR/uploads"

# 7. JSONファイル整合性チェック
log "データ整合性を検証しています..."
for json_file in "$TARGET_DIR/data"/*.json; do
    if [ -f "$json_file" ]; then
        if ! python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
            log_error "JSONファイルが破損しています: $json_file"
            log_error "リストアを中止します。元のデータは $BACKUP_CURRENT に保存されています。"
            exit 1
        fi
    fi
done

# 8. システム起動
log "アプリケーションを起動しています..."
cd "$BACKEND_DIR"
./run_production.sh start

# 9. ヘルスチェック
log "ヘルスチェックを実行しています..."
sleep 5
if curl -f -s https://api.example.com/health > /dev/null; then
    log "ヘルスチェック成功"
else
    log_error "ヘルスチェック失敗"
    exit 1
fi

# ==========================================================
# 完了
# ==========================================================

log "=== リストア完了 ==="
log "元のデータは以下に保存されています: $BACKUP_CURRENT"
log "アプリケーションは正常に起動しました"

exit 0
```

**使用方法:**

```bash
# 最新のバックアップからリストア
sudo /usr/local/bin/restore_full.sh /backup/mirai-knowledge-system/daily/20250127_030000

# 特定の日付のバックアップからリストア
sudo /usr/local/bin/restore_full.sh /backup/mirai-knowledge-system/daily/20250120_030000
```

---

## バックアップ検証手順

### 自動検証スクリプト

```bash
#!/bin/bash
# /usr/local/bin/verify_backup.sh
#
# バックアップの整合性検証
#

set -e

BACKUP_ROOT="/backup/mirai-knowledge-system"
LOG_FILE="/var/log/backup_verify.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE"
}

# 最新のバックアップを検証
LATEST_BACKUP=$(find "$BACKUP_ROOT/daily" -mindepth 1 -maxdepth 1 -type d | sort | tail -1)

if [ -z "$LATEST_BACKUP" ]; then
    log_error "バックアップが見つかりません"
    exit 1
fi

log "=== バックアップ検証開始 ==="
log "検証対象: $LATEST_BACKUP"

# 1. チェックサム検証
log "チェックサムを検証しています..."
cd "$LATEST_BACKUP"
if [ -f "checksums.sha256" ]; then
    if sha256sum -c checksums.sha256 > /dev/null 2>&1; then
        log "チェックサム検証: OK"
    else
        log_error "チェックサム検証: FAILED"
        exit 1
    fi
else
    log_error "チェックサムファイルが見つかりません"
    exit 1
fi

# 2. JSON整合性チェック
log "JSONファイルを検証しています..."
JSON_FILES=$(find "$LATEST_BACKUP/data" -name "*.json" -type f)
JSON_ERROR=0

for json_file in $JSON_FILES; do
    if ! python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
        log_error "JSONファイルが破損: $json_file"
        JSON_ERROR=1
    fi
done

if [ $JSON_ERROR -eq 0 ]; then
    log "JSON整合性チェック: OK"
else
    log_error "JSON整合性チェック: FAILED"
    exit 1
fi

# 3. 必須ファイルの存在確認
log "必須ファイルを確認しています..."
REQUIRED_FILES=(
    "data/users.json"
    "data/knowledges.json"
    "backup_metadata.json"
)

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$LATEST_BACKUP/$file" ]; then
        log_error "必須ファイルが見つかりません: $file"
        MISSING_FILES=1
    fi
done

if [ $MISSING_FILES -eq 0 ]; then
    log "必須ファイルチェック: OK"
else
    log_error "必須ファイルチェック: FAILED"
    exit 1
fi

# 4. バックアップサイズチェック
log "バックアップサイズを確認しています..."
BACKUP_SIZE=$(du -sb "$LATEST_BACKUP" | awk '{print $1}')
MIN_SIZE=1048576  # 1MB

if [ $BACKUP_SIZE -lt $MIN_SIZE ]; then
    log_error "バックアップサイズが小さすぎます: $BACKUP_SIZE bytes"
    exit 1
else
    BACKUP_SIZE_MB=$(echo "scale=2; $BACKUP_SIZE / 1024 / 1024" | bc)
    log "バックアップサイズチェック: OK (${BACKUP_SIZE_MB}MB)"
fi

# 5. リストアテスト（オプション - 週次で実行推奨）
if [ "${RUN_RESTORE_TEST:-false}" = "true" ]; then
    log "リストアテストを実行しています..."
    TEST_DIR="/tmp/restore_test_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$TEST_DIR"

    cp -r "$LATEST_BACKUP/data"/* "$TEST_DIR/"

    # テスト用のPythonスクリプトで読み込みテスト
    python3 << EOF
import json
import sys
try:
    with open('$TEST_DIR/users.json', 'r') as f:
        users = json.load(f)
    with open('$TEST_DIR/knowledges.json', 'r') as f:
        knowledges = json.load(f)
    print(f"Users: {len(users)}, Knowledges: {len(knowledges)}")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log "リストアテスト: OK"
        rm -rf "$TEST_DIR"
    else
        log_error "リストアテスト: FAILED"
        rm -rf "$TEST_DIR"
        exit 1
    fi
fi

log "=== バックアップ検証完了 ==="
log "全ての検証に合格しました"

exit 0
```

---

## リモートストレージ連携

### AWS S3連携

#### S3バケット作成

```bash
# AWS CLIのインストール
sudo apt-get install awscli

# AWS認証情報設定
aws configure

# S3バケット作成
aws s3 mb s3://mirai-knowledge-backup --region ap-northeast-1

# バケットポリシー設定（暗号化）
aws s3api put-bucket-encryption \
    --bucket mirai-knowledge-backup \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# ライフサイクルポリシー（古いバックアップの自動削除）
aws s3api put-bucket-lifecycle-configuration \
    --bucket mirai-knowledge-backup \
    --lifecycle-configuration file://lifecycle-policy.json
```

**lifecycle-policy.json:**

```json
{
    "Rules": [
        {
            "Id": "DeleteOldDailyBackups",
            "Status": "Enabled",
            "Prefix": "daily/",
            "Expiration": {
                "Days": 30
            }
        },
        {
            "Id": "DeleteOldIncrementalBackups",
            "Status": "Enabled",
            "Prefix": "incremental/",
            "Expiration": {
                "Days": 7
            }
        },
        {
            "Id": "ArchiveWeeklyBackups",
            "Status": "Enabled",
            "Prefix": "weekly/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            }
        }
    ]
}
```

#### S3同期スクリプト

```bash
#!/bin/bash
# /usr/local/bin/sync_to_remote.sh
#
# S3へのバックアップ同期
#

set -e

LOCAL_BACKUP_DIR="/backup/mirai-knowledge-system"
S3_BUCKET="s3://mirai-knowledge-backup"
LOG_FILE="/var/log/backup_sync.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== S3同期開始 ==="

# 日次バックアップの同期
log "日次バックアップを同期しています..."
aws s3 sync "$LOCAL_BACKUP_DIR/daily" "$S3_BUCKET/daily" \
    --storage-class STANDARD_IA \
    --exclude "*.tmp" \
    --delete

# 週次バックアップの同期
log "週次バックアップを同期しています..."
aws s3 sync "$LOCAL_BACKUP_DIR/weekly" "$S3_BUCKET/weekly" \
    --storage-class STANDARD_IA \
    --exclude "*.tmp"

# 月次バックアップの同期
log "月次バックアップを同期しています..."
aws s3 sync "$LOCAL_BACKUP_DIR/monthly" "$S3_BUCKET/monthly" \
    --storage-class GLACIER \
    --exclude "*.tmp"

# 同期結果確認
TOTAL_SIZE=$(aws s3 ls "$S3_BUCKET" --recursive --summarize | grep "Total Size" | awk '{print $3}')
TOTAL_SIZE_GB=$(echo "scale=2; $TOTAL_SIZE / 1024 / 1024 / 1024" | bc)

log "S3バックアップサイズ: ${TOTAL_SIZE_GB}GB"
log "=== S3同期完了 ==="

exit 0
```

---

### MinIO（オンプレミスS3互換ストレージ）

#### MinIOセットアップ

```bash
# MinIOのインストール
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# MinIO設定
sudo mkdir -p /data/minio
sudo useradd -r minio-user -s /sbin/nologin

# Systemdサービス作成
sudo tee /etc/systemd/system/minio.service > /dev/null << 'EOF'
[Unit]
Description=MinIO
After=network.target

[Service]
Type=notify
User=minio-user
Group=minio-user
Environment="MINIO_ROOT_USER=admin"
Environment="MINIO_ROOT_PASSWORD=your-secret-password"
ExecStart=/usr/local/bin/minio server /data/minio --console-address ":9001"
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# サービス起動
sudo systemctl daemon-reload
sudo systemctl enable minio
sudo systemctl start minio

# MinIOクライアント（mc）のインストール
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# MinIO接続設定
mc alias set local http://localhost:9000 admin your-secret-password

# バケット作成
mc mb local/mirai-knowledge-backup
```

#### MinIO同期スクリプト

```bash
#!/bin/bash
# /usr/local/bin/sync_to_minio.sh

LOCAL_BACKUP_DIR="/backup/mirai-knowledge-system"
MINIO_ALIAS="local"
MINIO_BUCKET="mirai-knowledge-backup"

mc mirror "$LOCAL_BACKUP_DIR/daily" "$MINIO_ALIAS/$MINIO_BUCKET/daily"
mc mirror "$LOCAL_BACKUP_DIR/weekly" "$MINIO_ALIAS/$MINIO_BUCKET/weekly"
mc mirror "$LOCAL_BACKUP_DIR/monthly" "$MINIO_ALIAS/$MINIO_BUCKET/monthly"

echo "MinIO同期完了"
```

---

## 災害復旧（DR）計画

### RPO/RTO目標

| シナリオ | RPO | RTO | 復旧優先度 |
|----------|-----|-----|------------|
| サーバー障害 | 6時間 | 1時間 | P1 |
| データセンター障害 | 24時間 | 4時間 | P1 |
| データ破損 | 6時間 | 2時間 | P1 |
| ランサムウェア攻撃 | 24時間 | 8時間 | P1 |
| 人為的ミス | 6時間 | 1時間 | P2 |

---

### DR手順

#### シナリオ1: サーバー完全障害

**状況:** サーバーハードウェア障害で起動不可

**復旧手順:**

1. **新サーバー準備（30分）**
   ```bash
   # 同等スペックのサーバーを用意
   # OS: Ubuntu 22.04 LTS
   # CPU: 4コア以上
   # メモリ: 8GB以上
   # ディスク: 100GB以上
   ```

2. **ベースシステムセットアップ（15分）**
   ```bash
   # システム更新
   sudo apt update && sudo apt upgrade -y

   # 必要パッケージインストール
   sudo apt install -y python3 python3-pip python3-venv nginx

   # アプリケーションユーザー作成
   sudo useradd -m -s /bin/bash mks-app
   ```

3. **アプリケーション配置（10分）**
   ```bash
   # Gitからクローン
   cd /opt
   sudo git clone https://github.com/your-org/Mirai-Knowledge-Systems.git
   cd Mirai-Knowledge-Systems/backend

   # 仮想環境作成
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **バックアップからデータリストア（20分）**
   ```bash
   # S3から最新バックアップ取得
   aws s3 sync s3://mirai-knowledge-backup/daily/latest /tmp/restore/

   # リストア実行
   sudo /usr/local/bin/restore_full.sh /tmp/restore
   ```

5. **サービス起動と確認（5分）**
   ```bash
   # アプリケーション起動
   ./run_production.sh start

   # 動作確認
   curl https://api.example.com/health
   ```

**所要時間:** 約80分（RTO目標: 1時間以内に復旧）

---

#### シナリオ2: ランサムウェア攻撃

**状況:** データが暗号化された

**復旧手順:**

1. **システム隔離（即座）**
   ```bash
   # ネットワーク切断
   sudo ifconfig eth0 down

   # 全サービス停止
   sudo systemctl stop nginx
   sudo systemctl stop mirai-knowledge-system
   ```

2. **影響範囲調査（30分）**
   ```bash
   # 暗号化されたファイル確認
   find / -name "*.encrypted" -o -name "*.locked" 2>/dev/null

   # 最後の正常バックアップ特定
   ls -ltr /backup/mirai-knowledge-system/daily/
   ```

3. **クリーンな環境構築（1時間）**
   ```bash
   # 新規サーバー構築
   # または
   # 既存サーバーのクリーンインストール
   ```

4. **最後の正常バックアップからリストア（2時間）**
   ```bash
   # 攻撃前の最後の正常バックアップからリストア
   sudo /usr/local/bin/restore_full.sh /backup/clean/20250126_030000
   ```

5. **セキュリティ強化（1時間）**
   ```bash
   # パスワード全変更
   # ファイアウォール設定強化
   # セキュリティパッチ適用
   ```

**所要時間:** 約4〜8時間

---

### DRテスト計画

**実施頻度:** 四半期に1回

**テスト内容:**

1. **バックアップからの完全リストアテスト**
   - テスト環境での完全リストア
   - データ整合性確認
   - 機能テスト

2. **フェイルオーバーテスト**
   - プライマリサーバー停止
   - セカンダリサーバーへの切り替え
   - 切り戻し

3. **データ復旧テスト**
   - 特定データの削除
   - バックアップからの部分リストア
   - データ整合性確認

**成功基準:**
- RTO以内での復旧完了
- データ損失がRPO以内
- 全機能の正常動作確認

---

## チェックリスト

### バックアップ実施チェックリスト

- [ ] バックアップスケジュールが正常に実行されている
- [ ] バックアップファイルが正常に作成されている
- [ ] バックアップサイズが妥当（異常に大きい・小さくない）
- [ ] チェックサムファイルが作成されている
- [ ] リモートストレージへの同期が完了している
- [ ] ディスク容量に余裕がある（80%未満）
- [ ] バックアップログにエラーがない

### リストア実施チェックリスト

- [ ] リストア元バックアップの整合性を確認
- [ ] 現在のデータをバックアップ済み
- [ ] システムを停止済み
- [ ] リストア先のディスク容量を確認
- [ ] リストア完了後のパーミッション確認
- [ ] JSON整合性チェック実施
- [ ] システム起動確認
- [ ] ヘルスチェック成功
- [ ] 主要機能の動作確認

---

## 参考資料

- [障害対応手順書](./06_Incident-Response-Procedures.md)
- [監視設定ガイド](./07_Monitoring-Setup-Guide.md)
- [運用手順(Operations-Guide)](./01_運用手順(Operations-Guide).md)

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-12-27 | 1.0 | 初版作成 - 詳細なバックアップ・リストア手順を追加 | Codex |
