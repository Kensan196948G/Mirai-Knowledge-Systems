#!/bin/bash

# ============================================================================
# SSL証明書有効期限チェックスクリプト
# Mirai Knowledge System
# ============================================================================
#
# 用途: SSL証明書の有効期限を確認し、期限が近い場合は警告
#
# 実行方法:
#   chmod +x scripts/check-ssl-expiry.sh
#   ./scripts/check-ssl-expiry.sh
#
# cron設定例（毎週月曜 9:00）:
#   0 9 * * 1 /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/check-ssl-expiry.sh
#
# ============================================================================

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 証明書ファイルパス
CERT_FILE="/mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/server.crt"

# 警告閾値（日数）
WARNING_DAYS=30
CRITICAL_DAYS=7

# ============================================================================
# メイン処理
# ============================================================================

main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}SSL証明書有効期限チェック${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # 証明書ファイル存在確認
    if [ ! -f "$CERT_FILE" ]; then
        echo -e "${RED}[ERROR]${NC} 証明書ファイルが見つかりません: $CERT_FILE"
        exit 1
    fi

    echo "証明書ファイル: $CERT_FILE"
    echo ""

    # 証明書情報取得
    CERT_INFO=$(openssl x509 -in "$CERT_FILE" -noout -subject -issuer -dates 2>&1)

    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} 証明書の読み取りに失敗しました"
        exit 1
    fi

    # 証明書詳細表示
    echo -e "${BLUE}証明書情報:${NC}"
    echo "$CERT_INFO" | sed 's/^/  /'
    echo ""

    # 有効期限計算
    NOT_BEFORE=$(echo "$CERT_INFO" | grep "notBefore" | cut -d= -f2)
    NOT_AFTER=$(echo "$CERT_INFO" | grep "notAfter" | cut -d= -f2)

    EXPIRY_EPOCH=$(date -d "$NOT_AFTER" +%s)
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

    # 有効期限ステータス判定
    echo -e "${BLUE}有効期限ステータス:${NC}"
    echo "  発行日: $NOT_BEFORE"
    echo "  有効期限: $NOT_AFTER"
    echo ""

    if [ $DAYS_LEFT -lt 0 ]; then
        # 期限切れ
        echo -e "${RED}[CRITICAL]${NC} 証明書の有効期限が切れています！"
        echo -e "  期限切れ日数: ${RED}$((-$DAYS_LEFT)) 日前${NC}"
        echo ""
        echo "対応が必要:"
        echo "  1. 新しい証明書を生成してください"
        echo "  2. docs/HTTPS_SETUP_COMPLETE.md の「証明書更新手順」を参照"
        exit 2

    elif [ $DAYS_LEFT -lt $CRITICAL_DAYS ]; then
        # 緊急警告（7日以内）
        echo -e "${RED}[CRITICAL]${NC} 証明書の有効期限が迫っています！"
        echo -e "  残り日数: ${RED}$DAYS_LEFT 日${NC}"
        echo ""
        echo "至急対応が必要:"
        echo "  1. 直ちに証明書を更新してください"
        echo "  2. docs/HTTPS_SETUP_COMPLETE.md の「証明書更新手順」を参照"
        exit 2

    elif [ $DAYS_LEFT -lt $WARNING_DAYS ]; then
        # 警告（30日以内）
        echo -e "${YELLOW}[WARNING]${NC} 証明書の有効期限が近づいています"
        echo -e "  残り日数: ${YELLOW}$DAYS_LEFT 日${NC}"
        echo ""
        echo "推奨される対応:"
        echo "  1. 証明書の更新を計画してください"
        echo "  2. docs/HTTPS_SETUP_COMPLETE.md の「証明書更新手順」を参照"
        exit 1

    elif [ $DAYS_LEFT -lt 90 ]; then
        # 情報（90日以内）
        echo -e "${GREEN}[INFO]${NC} 証明書は有効です"
        echo -e "  残り日数: ${GREEN}$DAYS_LEFT 日${NC}"
        echo ""
        echo "次回更新予定: $(date -d "$NOT_AFTER - 30 days" "+%Y年%m月%d日") 頃"

    else
        # 正常（90日以上）
        echo -e "${GREEN}[OK]${NC} 証明書は有効です"
        echo -e "  残り日数: ${GREEN}$DAYS_LEFT 日${NC}"
        echo ""
        echo "次回チェック: $(date -d "$NOT_AFTER - 90 days" "+%Y年%m月%d日") 頃"
    fi

    echo ""
    echo -e "${BLUE}========================================${NC}"

    # 正常終了
    exit 0
}

# スクリプト実行
main
