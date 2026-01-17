#!/bin/bash
# systemdサービスインストールスクリプト
# Mirai Knowledge System

set -e

echo "=========================================="
echo "Mirai Knowledge System"
echo "systemd Service Installation Script"
echo "=========================================="
echo ""

# 色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# サービスファイル選択
echo "インストールするサービスを選択してください："
echo "  1) 開発モード (python3直接実行、port 5100)"
echo "  2) 本番モード (gunicorn、port 5100、推奨)"
echo ""
read -p "選択 [1-2]: " choice

case $choice in
    1)
        SERVICE_FILE="mirai-knowledge-system-dev.service"
        SERVICE_NAME="mirai-knowledge-system"
        MODE="開発モード"
        ;;
    2)
        SERVICE_FILE="mirai-knowledge-production.service"
        SERVICE_NAME="mirai-knowledge-prod"
        MODE="本番モード"
        ;;
    *)
        echo -e "${RED}無効な選択です${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}モード: $MODE${NC}"
echo -e "${YELLOW}サービスファイル: $SERVICE_FILE${NC}"
echo ""

# 既存サービスの停止
echo "既存サービスを停止中..."
sudo systemctl stop mirai-knowledge-system.service 2>/dev/null || true
sudo systemctl stop mirai-knowledge-prod.service 2>/dev/null || true

# サービスファイルのコピー
echo "サービスファイルをコピー中..."
sudo cp "../config/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_NAME.service"

# systemdリロード
echo "systemdデーモンをリロード中..."
sudo systemctl daemon-reload

# サービスの有効化
echo "サービスを有効化中..."
sudo systemctl enable "$SERVICE_NAME.service"

# サービスの起動
echo "サービスを起動中..."
sudo systemctl start "$SERVICE_NAME.service"

# ステータス確認
echo ""
echo -e "${GREEN}セットアップ完了！${NC}"
echo ""
echo "サービス状態を確認中..."
sudo systemctl status "$SERVICE_NAME.service" --no-pager -l | head -20

echo ""
echo -e "${GREEN}=========================================="
echo "インストール完了"
echo "==========================================${NC}"
echo ""
echo "サービス管理コマンド："
echo "  起動: sudo systemctl start $SERVICE_NAME"
echo "  停止: sudo systemctl stop $SERVICE_NAME"
echo "  再起動: sudo systemctl restart $SERVICE_NAME"
echo "  状態確認: sudo systemctl status $SERVICE_NAME"
echo "  ログ確認: sudo journalctl -u $SERVICE_NAME -f"
echo ""
