#!/bin/bash
# Mirai Knowledge System 自動バックアップスクリプト
#
# 使用方法:
#   ./backup.sh              # データベースとJSONファイルの両方をバックアップ
#   ./backup.sh --db-only    # データベースのみ
#   ./backup.sh --json-only  # JSONファイルのみ

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトディレクトリ検出
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"
BACKUP_BASE_DIR="$PROJECT_DIR/backend/backups"
DATA_DIR="$PROJECT_DIR/backend/data"
LOGS_DIR="$PROJECT_DIR/backend/logs"

# バックアップディレクトリ作成
mkdir -p "$BACKUP_BASE_DIR"

# タイムスタンプ
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)

# バックアップ保持期間（日数）
RETENTION_DAYS_FULL=14    # 完全バックアップ: 14日
RETENTION_DAYS_DB=30      # DBのみ: 30日
RETENTION_DAYS_JSON=7     # JSONのみ: 7日

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Mirai Knowledge System${NC}"
echo -e "${BLUE}  自動バックアップスクリプト${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}開始時刻: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# バックアップモード判定
MODE="full"
if [[ "$1" == "--db-only" ]]; then
    MODE="db"
elif [[ "$1" == "--json-only" ]]; then
    MODE="json"
fi

echo -e "${YELLOW}バックアップモード: $MODE${NC}"
echo ""

# ====================================
# PostgreSQLバックアップ
# ====================================
backup_database() {
    echo -e "${BLUE}[1/3] PostgreSQLバックアップ開始${NC}"

    # .envファイルから設定読み取り
    if [ -f "$PROJECT_DIR/backend/.env" ]; then
        source "$PROJECT_DIR/backend/.env"
    fi

    # データベースURL解析
    DB_URL=${DATABASE_URL:-"postgresql://postgres:password@localhost:5432/mirai_knowledge_db"}

    # URLから接続情報抽出
    DB_HOST=$(echo $DB_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DB_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DB_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    DB_USER=$(echo $DB_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DB_URL | sed -n 's/.*\/\/[^:]*:\([^@]*\)@.*/\1/p')

    DB_BACKUP_DIR="$BACKUP_BASE_DIR/database"
    mkdir -p "$DB_BACKUP_DIR"

    DB_BACKUP_FILE="$DB_BACKUP_DIR/mirai_db_$TIMESTAMP.sql"
    DB_BACKUP_GZ="$DB_BACKUP_FILE.gz"

    echo "  データベース: $DB_NAME"
    echo "  ホスト: $DB_HOST:$DB_PORT"
    echo "  バックアップ先: $DB_BACKUP_GZ"

    # PostgreSQLが起動しているか確認
    if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -q 2>/dev/null; then
        echo -e "${YELLOW}  警告: PostgreSQLサーバーに接続できません。スキップします。${NC}"
        return 0
    fi

    # pg_dumpでバックアップ
    export PGPASSWORD=$DB_PASS
    if pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -F c -b -v -f "$DB_BACKUP_FILE" $DB_NAME 2>&1 | tee "$LOGS_DIR/backup_db.log"; then
        # 圧縮
        gzip "$DB_BACKUP_FILE"

        # ファイルサイズ取得
        BACKUP_SIZE=$(du -h "$DB_BACKUP_GZ" | cut -f1)

        echo -e "${GREEN}  ✓ データベースバックアップ完了 (サイズ: $BACKUP_SIZE)${NC}"

        # 古いバックアップ削除
        find "$DB_BACKUP_DIR" -name "mirai_db_*.sql.gz" -type f -mtime +$RETENTION_DAYS_DB -delete
        echo -e "${GREEN}  ✓ ${RETENTION_DAYS_DB}日以上前のDBバックアップを削除${NC}"
    else
        echo -e "${RED}  エラー: データベースバックアップに失敗しました${NC}"
        unset PGPASSWORD
        return 1
    fi
    unset PGPASSWORD

    echo ""
}

# ====================================
# JSONファイルバックアップ
# ====================================
backup_json_data() {
    echo -e "${BLUE}[2/3] JSONデータバックアップ開始${NC}"

    if [ ! -d "$DATA_DIR" ]; then
        echo -e "${YELLOW}  警告: JSONデータディレクトリが見つかりません。スキップします。${NC}"
        echo ""
        return 0
    fi

    JSON_BACKUP_DIR="$BACKUP_BASE_DIR/json"
    mkdir -p "$JSON_BACKUP_DIR"

    JSON_BACKUP_FILE="$JSON_BACKUP_DIR/mirai_json_$TIMESTAMP.tar.gz"

    echo "  ソース: $DATA_DIR"
    echo "  バックアップ先: $JSON_BACKUP_FILE"

    # tar.gzで圧縮バックアップ
    if tar -czf "$JSON_BACKUP_FILE" -C "$PROJECT_DIR/backend" data 2>&1 | tee "$LOGS_DIR/backup_json.log"; then
        # ファイルサイズ取得
        BACKUP_SIZE=$(du -h "$JSON_BACKUP_FILE" | cut -f1)

        echo -e "${GREEN}  ✓ JSONデータバックアップ完了 (サイズ: $BACKUP_SIZE)${NC}"

        # 古いバックアップ削除
        find "$JSON_BACKUP_DIR" -name "mirai_json_*.tar.gz" -type f -mtime +$RETENTION_DAYS_JSON -delete
        echo -e "${GREEN}  ✓ ${RETENTION_DAYS_JSON}日以上前のJSONバックアップを削除${NC}"
    else
        echo -e "${RED}  エラー: JSONデータバックアップに失敗しました${NC}"
        return 1
    fi

    echo ""
}

# ====================================
# 完全バックアップ（統合）
# ====================================
create_full_backup() {
    echo -e "${BLUE}[3/3] 完全バックアップ作成${NC}"

    FULL_BACKUP_DIR="$BACKUP_BASE_DIR/full"
    mkdir -p "$FULL_BACKUP_DIR"

    FULL_BACKUP_FILE="$FULL_BACKUP_DIR/mirai_full_$TIMESTAMP.tar.gz"

    echo "  バックアップ先: $FULL_BACKUP_FILE"

    # データベースとJSONバックアップを統合
    if tar -czf "$FULL_BACKUP_FILE" -C "$BACKUP_BASE_DIR" database json 2>&1; then
        # ファイルサイズ取得
        BACKUP_SIZE=$(du -h "$FULL_BACKUP_FILE" | cut -f1)

        echo -e "${GREEN}  ✓ 完全バックアップ作成完了 (サイズ: $BACKUP_SIZE)${NC}"

        # 古いバックアップ削除
        find "$FULL_BACKUP_DIR" -name "mirai_full_*.tar.gz" -type f -mtime +$RETENTION_DAYS_FULL -delete
        echo -e "${GREEN}  ✓ ${RETENTION_DAYS_FULL}日以上前の完全バックアップを削除${NC}"
    else
        echo -e "${RED}  エラー: 完全バックアップ作成に失敗しました${NC}"
        return 1
    fi

    echo ""
}

# ====================================
# バックアップメタデータ記録
# ====================================
record_metadata() {
    METADATA_FILE="$BACKUP_BASE_DIR/backup_metadata.log"

    echo "$(date '+%Y-%m-%d %H:%M:%S') | Mode: $MODE | Status: SUCCESS | Timestamp: $TIMESTAMP" >> "$METADATA_FILE"

    # 最新バックアップ情報を別ファイルに保存
    cat > "$BACKUP_BASE_DIR/LATEST_BACKUP.txt" <<EOF
最新バックアップ情報
==================
日時: $(date '+%Y-%m-%d %H:%M:%S')
モード: $MODE
タイムスタンプ: $TIMESTAMP

ファイル:
$(find "$BACKUP_BASE_DIR" -name "*$TIMESTAMP*" -type f -exec ls -lh {} \; | awk '{print "  - " $9 " (" $5 ")"  }')

保持期間:
  - 完全バックアップ: ${RETENTION_DAYS_FULL}日
  - データベースのみ: ${RETENTION_DAYS_DB}日
  - JSONのみ: ${RETENTION_DAYS_JSON}日

ディスク使用量:
$(du -sh "$BACKUP_BASE_DIR" | awk '{print "  合計: " $1}')
EOF
}

# ====================================
# メイン処理
# ====================================
main() {
    # モード別実行
    if [[ "$MODE" == "db" ]]; then
        backup_database
    elif [[ "$MODE" == "json" ]]; then
        backup_json_data
    else
        # 完全バックアップモード
        backup_database
        backup_json_data
        create_full_backup
    fi

    # メタデータ記録
    record_metadata

    # サマリー表示
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  バックアップ完了！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}終了時刻: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
    echo -e "${YELLOW}バックアップ場所:${NC}"
    echo "  $BACKUP_BASE_DIR"
    echo ""
    echo -e "${YELLOW}ディスク使用量:${NC}"
    du -sh "$BACKUP_BASE_DIR" | awk '{print "  " $1}'
    echo ""
    echo -e "${YELLOW}最新バックアップ:${NC}"
    find "$BACKUP_BASE_DIR" -name "*$TIMESTAMP*" -type f -exec ls -lh {} \; | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
}

# 実行
main
