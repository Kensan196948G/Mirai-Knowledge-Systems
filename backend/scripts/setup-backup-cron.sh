#!/bin/bash
# Mirai Knowledge System バックアップCronジョブ設定スクリプト
#
# 使用方法: sudo ./setup-backup-cron.sh

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Mirai Knowledge System${NC}"
echo -e "${GREEN}  バックアップCronジョブ設定${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# プロジェクトディレクトリ検出
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"
BACKUP_SCRIPT="$PROJECT_DIR/backend/scripts/backup.sh"

echo -e "${YELLOW}プロジェクトディレクトリ: $PROJECT_DIR${NC}"
echo -e "${YELLOW}バックアップスクリプト: $BACKUP_SCRIPT${NC}"
echo ""

# バックアップスクリプトの存在確認
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}エラー: バックアップスクリプトが見つかりません${NC}"
    echo "場所: $BACKUP_SCRIPT"
    exit 1
fi

# 実行権限確認
if [ ! -x "$BACKUP_SCRIPT" ]; then
    echo -e "${YELLOW}バックアップスクリプトに実行権限を付与中...${NC}"
    chmod +x "$BACKUP_SCRIPT"
    echo -e "${GREEN}✓ 実行権限を付与しました${NC}"
fi

# Cronジョブ設定
CRON_FILE="/etc/cron.d/mirai-knowledge-backup"
CRON_ENTRY="0 2 * * * root $BACKUP_SCRIPT >> /var/log/mirai-backup.log 2>&1"

echo -e "${YELLOW}Cronジョブ設定内容:${NC}"
echo "  スケジュール: 毎日 午前2時"
echo "  コマンド: $BACKUP_SCRIPT"
echo "  ログ: /var/log/mirai-backup.log"
echo ""

# root権限チェック
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}警告: このスクリプトはroot権限で実行するとCronジョブを自動設定します${NC}"
    echo ""
    echo -e "${YELLOW}手動設定方法:${NC}"
    echo "  1. cronジョブを編集:"
    echo "     crontab -e"
    echo ""
    echo "  2. 以下の行を追加:"
    echo "     0 2 * * * $BACKUP_SCRIPT >> /var/log/mirai-backup.log 2>&1"
    echo ""
    echo "  3. 保存して終了"
    echo ""
    exit 0
fi

# Cronファイル作成
echo -e "${YELLOW}Cronジョブを設定中...${NC}"
cat > "$CRON_FILE" <<EOF
# Mirai Knowledge System 自動バックアップ
# 毎日午前2時に実行
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 毎日午前2時: 完全バックアップ
0 2 * * * root $BACKUP_SCRIPT >> /var/log/mirai-backup.log 2>&1

# 6時間ごと: データベースのみバックアップ（オプション、コメント解除で有効化）
# 0 */6 * * * root $BACKUP_SCRIPT --db-only >> /var/log/mirai-backup.log 2>&1
EOF

chmod 644 "$CRON_FILE"
echo -e "${GREEN}✓ Cronファイルを作成しました: $CRON_FILE${NC}"

# cronサービス再起動
if systemctl is-active --quiet cron; then
    systemctl reload cron
    echo -e "${GREEN}✓ cronサービスを再読み込みしました${NC}"
elif systemctl is-active --quiet crond; then
    systemctl reload crond
    echo -e "${GREEN}✓ crondサービスを再読み込みしました${NC}"
else
    echo -e "${YELLOW}警告: cronサービスが起動していません${NC}"
fi

# ログファイル作成
touch /var/log/mirai-backup.log
chmod 644 /var/log/mirai-backup.log
echo -e "${GREEN}✓ ログファイルを作成しました: /var/log/mirai-backup.log${NC}"

# テストバックアップ実行確認
echo ""
echo -e "${YELLOW}テストバックアップを実行しますか? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}テストバックアップを実行中...${NC}"
    echo ""
    $BACKUP_SCRIPT
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  設定完了！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}バックアップスケジュール:${NC}"
echo "  - 毎日午前2時: 完全バックアップ（DB + JSON）"
echo ""
echo -e "${YELLOW}手動バックアップ実行:${NC}"
echo "  $BACKUP_SCRIPT"
echo ""
echo -e "${YELLOW}ログ確認:${NC}"
echo "  tail -f /var/log/mirai-backup.log"
echo ""
echo -e "${YELLOW}Cronジョブ確認:${NC}"
echo "  cat $CRON_FILE"
echo ""
