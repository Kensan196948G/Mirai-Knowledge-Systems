#!/bin/bash
################################################################################
# 本番環境ヘルスチェックスクリプト
# Mirai Knowledge Systems - Phase C-1-1
#
# 用途: 本番環境の全サービス稼働状況を一括確認
# 実行: ./scripts/production-health-check.sh
################################################################################

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 設定
PROD_HTTP_PORT=8100
PROD_HTTPS_PORT=8443
PROD_IP="192.168.0.187"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} Mirai Knowledge Systems${NC}"
echo -e "${BLUE} 本番環境ヘルスチェック${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# エラーカウンタ
ERRORS=0
WARNINGS=0

check_status() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name"
        ((ERRORS++))
        return 1
    fi
}

check_warning() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "  ${YELLOW}△${NC} $name (警告)"
        ((WARNINGS++))
        return 1
    fi
}

# ============================================================================
# 1. systemdサービス確認
# ============================================================================
echo -e "${BLUE}[1] systemdサービス状態${NC}"

check_status "PostgreSQL" "systemctl is-active --quiet postgresql"
check_status "Nginx" "systemctl is-active --quiet nginx"
check_status "Mirai Knowledge App" "systemctl is-active --quiet mirai-knowledge-app"
check_warning "Prometheus" "systemctl is-active --quiet prometheus"
check_warning "Grafana" "systemctl is-active --quiet grafana-server"

echo ""

# ============================================================================
# 2. ポート確認
# ============================================================================
echo -e "${BLUE}[2] ポートリスニング確認${NC}"

check_status "PostgreSQL (5432)" "ss -tlnp | grep -q ':5432'"
check_status "Nginx HTTP (80)" "ss -tlnp | grep -q ':80'"
check_status "Nginx HTTPS (443)" "ss -tlnp | grep -q ':443'"
check_status "Gunicorn (8100)" "ss -tlnp | grep -q ':$PROD_HTTP_PORT'"
check_warning "Prometheus (9090)" "ss -tlnp | grep -q ':9090'"
check_warning "Grafana (3000)" "ss -tlnp | grep -q ':3000'"

echo ""

# ============================================================================
# 3. API ヘルスチェック
# ============================================================================
echo -e "${BLUE}[3] API ヘルスチェック${NC}"

# HTTP -> HTTPS リダイレクト確認
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "http://$PROD_IP:$PROD_HTTP_PORT/api/v1/health" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo -e "  ${GREEN}✓${NC} HTTP API応答 (Status: $HTTP_STATUS)"
else
    echo -e "  ${RED}✗${NC} HTTP API応答なし (Status: $HTTP_STATUS)"
    ((ERRORS++))
fi

# HTTPS確認
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 5 -k "https://$PROD_IP:$PROD_HTTPS_PORT/api/v1/health" 2>/dev/null || echo "000")
if [ "$HTTPS_STATUS" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} HTTPS API応答 (Status: $HTTPS_STATUS)"
else
    echo -e "  ${RED}✗${NC} HTTPS API応答なし (Status: $HTTPS_STATUS)"
    ((ERRORS++))
fi

echo ""

# ============================================================================
# 4. データベース確認
# ============================================================================
echo -e "${BLUE}[4] データベース確認${NC}"

if command -v psql &> /dev/null; then
    DB_COUNT=$(sudo -u postgres psql -d mirai_knowledge_db -t -c "SELECT COUNT(*) FROM knowledge;" 2>/dev/null | xargs || echo "N/A")
    if [ "$DB_COUNT" != "N/A" ]; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL接続OK (ナレッジ件数: $DB_COUNT)"
    else
        echo -e "  ${RED}✗${NC} PostgreSQL接続エラー"
        ((ERRORS++))
    fi
else
    echo -e "  ${YELLOW}△${NC} psqlコマンドなし（スキップ）"
fi

echo ""

# ============================================================================
# 5. SSL証明書確認
# ============================================================================
echo -e "${BLUE}[5] SSL証明書確認${NC}"

CERT_FILE="/mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/server.crt"
if [ -f "$CERT_FILE" ]; then
    EXPIRY=$(openssl x509 -in "$CERT_FILE" -noout -enddate 2>/dev/null | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo "0")
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

    if [ "$DAYS_LEFT" -gt 30 ]; then
        echo -e "  ${GREEN}✓${NC} SSL証明書有効 (残り ${DAYS_LEFT} 日)"
    elif [ "$DAYS_LEFT" -gt 7 ]; then
        echo -e "  ${YELLOW}△${NC} SSL証明書更新推奨 (残り ${DAYS_LEFT} 日)"
        ((WARNINGS++))
    else
        echo -e "  ${RED}✗${NC} SSL証明書期限切れ間近 (残り ${DAYS_LEFT} 日)"
        ((ERRORS++))
    fi
else
    echo -e "  ${YELLOW}△${NC} SSL証明書ファイルなし"
    ((WARNINGS++))
fi

echo ""

# ============================================================================
# 6. ディスク容量確認
# ============================================================================
echo -e "${BLUE}[6] ディスク容量確認${NC}"

DISK_USAGE=$(df -h /mnt/LinuxHDD 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%' || echo "N/A")
if [ "$DISK_USAGE" != "N/A" ]; then
    if [ "$DISK_USAGE" -lt 80 ]; then
        echo -e "  ${GREEN}✓${NC} ディスク使用率: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        echo -e "  ${YELLOW}△${NC} ディスク使用率: ${DISK_USAGE}% (警告)"
        ((WARNINGS++))
    else
        echo -e "  ${RED}✗${NC} ディスク使用率: ${DISK_USAGE}% (危険)"
        ((ERRORS++))
    fi
else
    echo -e "  ${YELLOW}△${NC} ディスク情報取得不可"
fi

echo ""

# ============================================================================
# 7. バックアップ確認
# ============================================================================
echo -e "${BLUE}[7] 最新バックアップ確認${NC}"

BACKUP_DIR="/var/backups/mirai-knowledge/postgresql"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP" 2>/dev/null || echo "0")) / 86400 ))
        if [ "$BACKUP_AGE" -lt 1 ]; then
            echo -e "  ${GREEN}✓${NC} 最新バックアップ: $(basename "$LATEST_BACKUP") (本日)"
        elif [ "$BACKUP_AGE" -lt 7 ]; then
            echo -e "  ${YELLOW}△${NC} 最新バックアップ: ${BACKUP_AGE} 日前"
            ((WARNINGS++))
        else
            echo -e "  ${RED}✗${NC} バックアップ古い: ${BACKUP_AGE} 日前"
            ((ERRORS++))
        fi
    else
        echo -e "  ${RED}✗${NC} バックアップファイルなし"
        ((ERRORS++))
    fi
else
    echo -e "  ${YELLOW}△${NC} バックアップディレクトリなし"
    ((WARNINGS++))
fi

echo ""

# ============================================================================
# 結果サマリー
# ============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} チェック結果サマリー${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ すべてのチェックに合格しました${NC}"
    EXIT_CODE=0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}△ 警告: ${WARNINGS} 件${NC}"
    echo "  確認事項がありますが、サービスは正常稼働中です"
    EXIT_CODE=0
else
    echo -e "${RED}✗ エラー: ${ERRORS} 件${NC}"
    echo -e "${YELLOW}△ 警告: ${WARNINGS} 件${NC}"
    echo "  対応が必要な項目があります"
    EXIT_CODE=1
fi

echo ""
echo "詳細ログ: /var/log/mirai-knowledge/health-check.log"
echo -e "${BLUE}========================================${NC}"

exit $EXIT_CODE
