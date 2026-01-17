#!/bin/bash
# ============================================================
# Mirai Knowledge Systems - Linux開発環境起動スクリプト
# ============================================================
#
# 使用方法:
#   ./scripts/linux/start-dev.sh [オプション]
#
# オプション:
#   --background    バックグラウンドで起動
#   --debug         デバッグモード有効
#   --help          ヘルプ表示
#
# ポート番号:
#   HTTP:  5100 (固定)
#   HTTPS: 5443 (固定)
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
BACKGROUND=false
DEBUG=true
HTTP_PORT=5100
HTTPS_PORT=5443

# ヘルプ表示
show_help() {
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  Mirai Knowledge Systems - 開発環境起動スクリプト${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --background    バックグラウンドで起動"
    echo "  --debug         デバッグモード有効（デフォルト）"
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
        --background)
            BACKGROUND=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
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

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Mirai Knowledge Systems - 開発環境起動${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# 環境変数設定
export MKS_ENV=development
export MKS_HTTP_PORT=${HTTP_PORT}
export MKS_HTTPS_PORT=${HTTPS_PORT}
export MKS_DEBUG=${DEBUG}
export MKS_LOAD_SAMPLE_DATA=true
export MKS_CREATE_DEMO_USERS=true
export MKS_FORCE_HTTPS=false

# .env.development を読み込み
ENV_FILE="${PROJECT_ROOT}/envs/development/.env.development"
if [[ -f "$ENV_FILE" ]]; then
    echo -e "${GREEN}[OK]${NC} 環境設定ファイルを読み込み: $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}[WARN]${NC} 環境設定ファイルが見つかりません: $ENV_FILE"
    echo -e "${YELLOW}      デフォルト設定を使用します${NC}"
fi

# Python仮想環境をアクティベート
VENV_PATH="${PROJECT_ROOT}/venv_linux/bin/activate"
if [[ -f "$VENV_PATH" ]]; then
    echo -e "${GREEN}[OK]${NC} Python仮想環境をアクティベート"
    source "$VENV_PATH"
else
    echo -e "${YELLOW}[WARN]${NC} venv_linux が見つかりません。システムPythonを使用します。"
fi

# 起動設定表示
echo ""
echo -e "${BLUE}起動設定:${NC}"
echo -e "  環境:         ${GREEN}development${NC}"
echo -e "  HTTPポート:   ${GREEN}${HTTP_PORT}${NC}"
echo -e "  HTTPSポート:  ${GREEN}${HTTPS_PORT}${NC}"
echo -e "  デバッグ:     ${GREEN}${DEBUG}${NC}"
echo -e "  サンプルデータ: ${GREEN}有効${NC}"
echo -e "  デモユーザー:   ${GREEN}有効${NC}"
echo ""

# ディレクトリ移動
cd "${PROJECT_ROOT}/backend"

# バックエンド起動
if [[ "$BACKGROUND" == "true" ]]; then
    echo -e "${GREEN}[INFO]${NC} バックグラウンドで起動中..."
    nohup python app_v2.py > "${PROJECT_ROOT}/logs/dev.log" 2>&1 &
    PID=$!
    echo -e "${GREEN}[OK]${NC} バックエンドを起動しました (PID: ${PID})"
    echo ""
    echo -e "${CYAN}アクセスURL:${NC}"
    echo -e "  HTTP:  http://localhost:${HTTP_PORT}"
    echo -e "  HTTPS: https://localhost:${HTTPS_PORT}"
else
    echo -e "${GREEN}[INFO]${NC} フォアグラウンドで起動中..."
    echo -e "${CYAN}Ctrl+C で停止${NC}"
    echo ""
    python app_v2.py
fi
