#!/bin/bash
# 本番環境セットアップスクリプト
# Mirai Knowledge System

set -e

# 色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Mirai Knowledge System${NC}"
echo -e "${GREEN}  本番環境セットアップ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# root権限チェック
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}エラー: このスクリプトはroot権限で実行してください${NC}"
    echo "使用方法: sudo $0"
    exit 1
fi

echo -e "${YELLOW}1. ログディレクトリを作成中...${NC}"
mkdir -p /var/log/mirai-knowledge
chown kensan:kensan /var/log/mirai-knowledge
chmod 755 /var/log/mirai-knowledge
echo -e "${GREEN}✓ ログディレクトリ作成完了: /var/log/mirai-knowledge${NC}"

echo ""
echo -e "${YELLOW}2. データディレクトリを作成中...${NC}"
mkdir -p /var/lib/mirai-knowledge-system/data
chown -R kensan:kensan /var/lib/mirai-knowledge-system
chmod 755 /var/lib/mirai-knowledge-system
echo -e "${GREEN}✓ データディレクトリ作成完了: /var/lib/mirai-knowledge-system${NC}"

echo ""
echo -e "${YELLOW}3. ログローテーション設定を確認中...${NC}"
if [ -f /etc/logrotate.d/mirai-knowledge-system ]; then
    echo -e "${GREEN}✓ ログローテーション設定済み${NC}"
else
    echo -e "${YELLOW}⚠ ログローテーション未設定${NC}"
    echo "  backend/tools/setup-logrotate.sh を実行してください"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  セットアップ完了！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}次のステップ:${NC}"
echo "  1. systemdサービスをインストール:"
echo "     ./install-systemd-service.sh"
echo ""
echo "  2. サービス状態を確認:"
echo "     sudo systemctl status mirai-knowledge-prod"
echo ""
