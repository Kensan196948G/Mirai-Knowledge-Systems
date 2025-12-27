#!/bin/bash
# ==============================================================================
# Mirai Knowledge Systems - 統合起動スクリプト
# ==============================================================================
#
# バックエンドとフロントエンド（開発用サーバー）を同時に起動します
#
# 使用方法:
#   ./start_all.sh [オプション]
#
# オプション:
#   --port PORT        バックエンドポート番号（デフォルト: 5010）
#   --frontend-port    フロントエンドポート番号（デフォルト: 3000）
#   --debug            デバッグモードで起動
#   --background       バックグラウンドで起動
#   --help             ヘルプを表示
#
# 停止方法:
#   ./stop_all.sh
#   または Ctrl+C
#
# ==============================================================================

set -e

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# デフォルト設定
BACKEND_PORT=5010
FRONTEND_PORT=3000
DEBUG_MODE=false
BACKGROUND_MODE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PIDファイル
BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"

# ヘルプ表示
show_help() {
    cat << EOF
Mirai Knowledge Systems - 統合起動スクリプト

使用方法:
    $0 [オプション]

オプション:
    --port PORT           バックエンドポート番号（デフォルト: 5010）
    --frontend-port PORT  フロントエンドポート（デフォルト: 3000）
    --debug               デバッグモードで起動
    --background          バックグラウンドで起動
    --help                このヘルプを表示

例:
    # デフォルト設定で起動
    $0

    # カスタムポートで起動
    $0 --port 8080

    # バックグラウンドで起動
    $0 --background

    # デバッグモード
    $0 --debug

停止方法:
    ./stop_all.sh
    または Ctrl+C（フォアグラウンド起動時）

EOF
}

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --background)
            BACKGROUND_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}不明なオプション: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# ヘッダー表示
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Mirai Knowledge Systems - 統合起動${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 既存プロセスのクリーンアップ
cleanup() {
    echo ""
    echo -e "${YELLOW}サービスを停止しています...${NC}"

    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo -e "${YELLOW}バックエンドを停止中 (PID: $BACKEND_PID)${NC}"
            kill "$BACKEND_PID"
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo -e "${YELLOW}フロントエンドを停止中 (PID: $FRONTEND_PID)${NC}"
            kill "$FRONTEND_PID"
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    echo -e "${GREEN}✓ 停止完了${NC}"
    exit 0
}

# Ctrl+C でクリーンアップ
trap cleanup INT TERM

# ポート使用確認
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}エラー: ポート $port は既に使用されています${NC}"
        echo ""
        lsof -i :$port
        echo ""
        return 1
    fi
    return 0
}

# バックエンドポート確認
if ! check_port $BACKEND_PORT; then
    echo "既存のプロセスを停止してから再実行してください"
    exit 1
fi

echo -e "${GREEN}✓ ポート $BACKEND_PORT は使用可能です${NC}"
echo ""

# バックエンドディレクトリに移動
cd "$SCRIPT_DIR/backend"

# 仮想環境確認
if [ -d "venv" ]; then
    echo -e "${GREEN}仮想環境をアクティベート: venv${NC}"
    source venv/bin/activate
elif [ -d "../venv_linux" ]; then
    echo -e "${GREEN}仮想環境をアクティベート: ../venv_linux${NC}"
    source ../venv_linux/bin/activate
else
    echo -e "${YELLOW}仮想環境が見つかりません。システムPythonを使用します${NC}"
fi

# 環境変数設定
export MKS_PORT=$BACKEND_PORT
export MKS_ENV=${MKS_ENV:-development}

if [ "$DEBUG_MODE" = true ]; then
    export MKS_DEBUG=true
fi

# データディレクトリ確認
mkdir -p data logs

# 必須ファイル作成
for file in users.json knowledge.json sop.json access_logs.json notifications.json approvals.json; do
    if [ ! -f "data/$file" ]; then
        echo "[]" > "data/$file"
    fi
done

# 起動情報表示
echo ""
echo -e "${BLUE}起動設定:${NC}"
echo -e "  バックエンドポート: ${GREEN}$BACKEND_PORT${NC}"
echo -e "  環境: ${GREEN}$MKS_ENV${NC}"
echo -e "  デバッグ: ${GREEN}${MKS_DEBUG:-false}${NC}"
echo ""

# バックエンド起動
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  バックエンドを起動しています...${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

if [ "$BACKGROUND_MODE" = true ]; then
    # バックグラウンド起動
    if [ "$PRODUCTION_MODE" = true ] && command -v gunicorn &> /dev/null; then
        gunicorn \
            --bind 0.0.0.0:$BACKEND_PORT \
            --workers $WORKERS \
            --daemon \
            --pid "$BACKEND_PID_FILE" \
            --access-logfile logs/access.log \
            --error-logfile logs/error.log \
            app_v2:app

        echo -e "${GREEN}✓ バックエンドをバックグラウンドで起動しました${NC}"
        echo -e "  PID: $(cat $BACKEND_PID_FILE)"
    else
        nohup python3 app_v2.py > logs/app.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > "$BACKEND_PID_FILE"

        echo -e "${GREEN}✓ バックエンドをバックグラウンドで起動しました${NC}"
        echo -e "  PID: $BACKEND_PID"
    fi

    # 起動確認
    sleep 3
    if curl -f -s "http://localhost:$BACKEND_PORT/" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ バックエンドが正常に起動しました${NC}"
    else
        echo -e "${RED}✗ バックエンドの起動に失敗しました${NC}"
        echo "ログを確認してください: tail -f backend/logs/error.log"
        exit 1
    fi

    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${GREEN}  起動完了${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
    echo -e "${GREEN}アクセスURL:${NC}"
    echo -e "  ${BLUE}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  ${BLUE}http://192.168.0.187:$BACKEND_PORT${NC}"
    echo ""
    echo -e "${YELLOW}停止方法:${NC}"
    echo -e "  ./stop_all.sh"
    echo -e "  または"
    echo -e "  kill \$(cat $BACKEND_PID_FILE)"
    echo ""
    echo -e "${YELLOW}ログ確認:${NC}"
    echo -e "  tail -f backend/logs/app.log"
    echo -e "  tail -f backend/logs/error.log"
    echo ""

else
    # フォアグラウンド起動
    echo -e "${GREEN}バックエンドを起動中（Ctrl+C で停止）...${NC}"
    echo ""

    # Pythonスクリプト実行
    python3 app_v2.py
fi
