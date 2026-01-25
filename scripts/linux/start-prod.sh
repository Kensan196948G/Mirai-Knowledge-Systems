#!/bin/bash
# ============================================================
# Mirai Knowledge Systems - Linux本番環境起動スクリプト
# ============================================================
#
# 使用方法:
#   ./scripts/linux/start-prod.sh [オプション]
#
# オプション:
#   --force         確認プロンプトをスキップ
#   --workers N     Gunicornワーカー数（デフォルト: 4）
#   --help          ヘルプ表示
#
# ポート番号:
#   HTTP:  8100 (固定)
#   HTTPS: 8443 (固定)
#
# ============================================================

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# デフォルト値
FORCE=false
WORKERS=4
HTTP_PORT=8100
HTTPS_PORT=8443

# ヘルプ表示
show_help() {
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}  Mirai Knowledge Systems - 本番環境起動スクリプト${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --force         確認プロンプトをスキップ"
    echo "  --workers N     Gunicornワーカー数（デフォルト: 4）"
    echo "  --help          このヘルプを表示"
    echo ""
    echo "ポート番号（固定）:"
    echo "  HTTP:  ${HTTP_PORT}"
    echo "  HTTPS: ${HTTPS_PORT}"
    echo ""
    exit 0
}

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}不明なオプション: $1${NC}"
            show_help
            ;;
    esac
done

echo -e "${RED}============================================================${NC}"
echo -e "${RED}  Mirai Knowledge Systems - 本番環境起動${NC}"
echo -e "${RED}============================================================${NC}"
echo ""

# 確認プロンプト
if [[ "$FORCE" != "true" ]]; then
    echo -e "${YELLOW}[警告] 本番環境を起動しようとしています。${NC}"
    read -p "続行しますか? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo -e "${YELLOW}キャンセルしました。${NC}"
        exit 0
    fi
fi

# 環境変数設定
export MKS_ENV=production
export MKS_HTTP_PORT=${HTTP_PORT}
export MKS_HTTPS_PORT=${HTTPS_PORT}
export MKS_DEBUG=false
export MKS_LOAD_SAMPLE_DATA=false
export MKS_CREATE_DEMO_USERS=false
export MKS_FORCE_HTTPS=true
export MKS_HSTS_ENABLED=true

# .env.production を読み込み
ENV_FILE="${PROJECT_ROOT}/envs/production/.env.production"
if [[ -f "$ENV_FILE" ]]; then
    echo -e "${GREEN}[OK]${NC} 環境設定ファイルを読み込み: $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${RED}[ERROR]${NC} 本番環境設定ファイルが見つかりません: $ENV_FILE"
    echo -e "${RED}       本番環境には .env.production が必須です${NC}"
    exit 1
fi

# 必須環境変数チェック
required_vars=("MKS_SECRET_KEY" "MKS_JWT_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo -e "${RED}[ERROR]${NC} 必須環境変数が設定されていません: $var"
        exit 1
    fi
done

# Python仮想環境をアクティベート
VENV_PATH="${PROJECT_ROOT}/venv_linux/bin/activate"
if [[ -f "$VENV_PATH" ]]; then
    echo -e "${GREEN}[OK]${NC} Python仮想環境をアクティベート"
    source "$VENV_PATH"
else
    echo -e "${RED}[ERROR]${NC} venv_linux が見つかりません。"
    exit 1
fi

# SSL証明書チェック
SSL_CERT="${PROJECT_ROOT}/ssl/server.crt"
SSL_KEY="${PROJECT_ROOT}/ssl/server.key"
if [[ ! -f "$SSL_CERT" || ! -f "$SSL_KEY" ]]; then
    echo -e "${RED}[ERROR]${NC} SSL証明書が見つかりません"
    echo -e "${RED}       $SSL_CERT${NC}"
    echo -e "${RED}       $SSL_KEY${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} SSL証明書を確認"

# 起動設定表示
echo ""
echo -e "${RED}起動設定:${NC}"
echo -e "  環境:         ${RED}PRODUCTION${NC}"
echo -e "  HTTPポート:   ${RED}${HTTP_PORT}${NC}"
echo -e "  HTTPSポート:  ${RED}${HTTPS_PORT}${NC}"
echo -e "  ワーカー数:   ${RED}${WORKERS}${NC}"
echo -e "  HTTPS強制:    ${RED}有効${NC}"
echo -e "  HSTS:         ${RED}有効${NC}"
echo -e "  サンプルデータ: ${RED}無効${NC}"
echo -e "  デモユーザー:   ${RED}無効${NC}"
echo ""

# ディレクトリ移動
cd "${PROJECT_ROOT}/backend"

# Gunicornで起動
echo -e "${GREEN}[INFO]${NC} Gunicornで起動中..."
gunicorn \
    --bind "0.0.0.0:${HTTP_PORT}" \
    --workers "${WORKERS}" \
    --worker-class eventlet \
    --timeout 120 \
    --access-logfile "${PROJECT_ROOT}/logs/access.log" \
    --error-logfile "${PROJECT_ROOT}/logs/error.log" \
    --capture-output \
    --enable-stdio-inheritance \
    "app_v2:app"
