#!/bin/bash
################################################################################
# systemdサービス自動起動設定スクリプト
# Mirai Knowledge Systems - Phase C-1-2
#
# 用途: 本番環境の全サービス自動起動を設定・確認
# 実行: sudo ./scripts/setup-systemd-autostart.sh
################################################################################

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# root権限チェック
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}エラー: root権限で実行してください${NC}"
    echo "使用方法: sudo $0"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} systemdサービス自動起動設定${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# サービス一覧
REQUIRED_SERVICES=(
    "postgresql"
    "nginx"
    "mirai-knowledge-app"
)

OPTIONAL_SERVICES=(
    "prometheus"
    "grafana-server"
)

# ============================================================================
# 必須サービスの自動起動設定
# ============================================================================
echo -e "${BLUE}[1] 必須サービスの自動起動確認・設定${NC}"
echo ""

for service in "${REQUIRED_SERVICES[@]}"; do
    echo -n "  $service: "

    # サービス存在確認
    if ! systemctl list-unit-files | grep -q "^$service"; then
        echo -e "${RED}インストールされていません${NC}"
        continue
    fi

    # 自動起動状態確認
    if systemctl is-enabled --quiet "$service" 2>/dev/null; then
        echo -e "${GREEN}有効 (enabled)${NC}"
    else
        echo -n "無効 → "
        # 自動起動を有効化
        systemctl enable "$service" 2>/dev/null
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo -e "${GREEN}有効化完了${NC}"
        else
            echo -e "${RED}有効化失敗${NC}"
        fi
    fi
done

echo ""

# ============================================================================
# オプションサービスの自動起動確認
# ============================================================================
echo -e "${BLUE}[2] オプションサービスの自動起動確認${NC}"
echo ""

for service in "${OPTIONAL_SERVICES[@]}"; do
    echo -n "  $service: "

    # サービス存在確認
    if ! systemctl list-unit-files | grep -q "^$service"; then
        echo -e "${YELLOW}インストールされていません (オプション)${NC}"
        continue
    fi

    # 自動起動状態確認
    if systemctl is-enabled --quiet "$service" 2>/dev/null; then
        echo -e "${GREEN}有効 (enabled)${NC}"
    else
        echo -e "${YELLOW}無効 (disabled)${NC}"
    fi
done

echo ""

# ============================================================================
# サービスファイルの配置確認
# ============================================================================
echo -e "${BLUE}[3] サービスファイル配置確認${NC}"
echo ""

SERVICE_FILE="/etc/systemd/system/mirai-knowledge-app.service"
SOURCE_FILE="/mnt/LinuxHDD/Mirai-Knowledge-Systems/mirai-knowledge-app.service"

if [ -f "$SERVICE_FILE" ]; then
    echo -e "  ${GREEN}✓${NC} $SERVICE_FILE 存在"
else
    echo -e "  ${YELLOW}△${NC} $SERVICE_FILE なし"
    if [ -f "$SOURCE_FILE" ]; then
        echo "    ソースファイルからコピーしています..."
        cp "$SOURCE_FILE" "$SERVICE_FILE"
        systemctl daemon-reload
        echo -e "    ${GREEN}✓${NC} コピー完了"
    else
        echo -e "    ${RED}✗${NC} ソースファイルも見つかりません"
    fi
fi

echo ""

# ============================================================================
# 現在のサービス状態確認
# ============================================================================
echo -e "${BLUE}[4] 現在のサービス状態${NC}"
echo ""

printf "  %-25s %-12s %-12s\n" "サービス名" "状態" "自動起動"
printf "  %-25s %-12s %-12s\n" "-------------------------" "------------" "------------"

ALL_SERVICES=("${REQUIRED_SERVICES[@]}" "${OPTIONAL_SERVICES[@]}")

for service in "${ALL_SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "^$service"; then
        STATUS=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
        ENABLED=$(systemctl is-enabled "$service" 2>/dev/null || echo "disabled")

        if [ "$STATUS" = "active" ]; then
            STATUS_COLOR="${GREEN}$STATUS${NC}"
        else
            STATUS_COLOR="${RED}$STATUS${NC}"
        fi

        if [ "$ENABLED" = "enabled" ]; then
            ENABLED_COLOR="${GREEN}$ENABLED${NC}"
        else
            ENABLED_COLOR="${YELLOW}$ENABLED${NC}"
        fi

        printf "  %-25s %-12b %-12b\n" "$service" "$STATUS_COLOR" "$ENABLED_COLOR"
    fi
done

echo ""

# ============================================================================
# 完了メッセージ
# ============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ systemd自動起動設定完了${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "再起動テストを実行する場合:"
echo "  sudo reboot"
echo ""
echo "個別サービスの管理:"
echo "  sudo systemctl start/stop/restart <service-name>"
echo "  sudo systemctl enable/disable <service-name>"
echo ""
