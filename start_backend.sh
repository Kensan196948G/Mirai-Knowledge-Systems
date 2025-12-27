#!/bin/bash
# ==============================================================================
# Mirai Knowledge Systems - バックエンド起動スクリプト
# ==============================================================================
#
# 使用方法:
#   ./start_backend.sh [オプション]
#
# オプション:
#   --port PORT        ポート番号を指定（デフォルト: 5010）
#   --debug            デバッグモードで起動
#   --production       本番モードで起動
#   --workers N        Gunicornワーカー数を指定（本番モードのみ）
#   --help             ヘルプを表示
#
# ==============================================================================

set -e

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# デフォルト設定
PORT=5010
DEBUG_MODE=false
PRODUCTION_MODE=false
WORKERS=4
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ヘルプ表示
show_help() {
    cat << EOF
Mirai Knowledge Systems - バックエンド起動スクリプト

使用方法:
    $0 [オプション]

オプション:
    --port PORT        ポート番号を指定（デフォルト: 5010）
    --debug            デバッグモードで起動
    --production       本番モードで起動（Gunicorn使用）
    --workers N        Gunicornワーカー数（本番モードのみ、デフォルト: 4）
    --help             このヘルプを表示

例:
    # 開発モード（ポート5010）
    $0

    # デバッグモード
    $0 --debug

    # カスタムポート
    $0 --port 8000

    # 本番モード
    $0 --production --workers 8

EOF
}

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --production)
            PRODUCTION_MODE=true
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
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

# バックエンドディレクトリに移動
cd "$SCRIPT_DIR/backend"

# ヘッダー表示
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Mirai Knowledge Systems - バックエンド起動${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Python確認
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}エラー: Python 3がインストールされていません${NC}"
    exit 1
fi

echo -e "${GREEN}Python: $(python3 --version)${NC}"

# 仮想環境の確認・アクティベート
if [ -d "venv" ]; then
    echo -e "${GREEN}仮想環境を検出: venv${NC}"
    source venv/bin/activate
elif [ -d "../venv_linux" ]; then
    echo -e "${GREEN}仮想環境を検出: ../venv_linux${NC}"
    source ../venv_linux/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}仮想環境を検出: .venv${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}警告: 仮想環境が見つかりません${NC}"
    echo -e "${YELLOW}システムのPythonを使用します${NC}"

    # 依存関係チェック
    if ! python3 -c "import flask" 2>/dev/null; then
        echo -e "${RED}エラー: Flaskがインストールされていません${NC}"
        echo -e "${YELLOW}以下のコマンドで依存関係をインストールしてください:${NC}"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
fi

# 環境変数設定
export MKS_PORT=$PORT

if [ "$DEBUG_MODE" = true ]; then
    export MKS_DEBUG=true
    export MKS_ENV=development
    echo -e "${YELLOW}デバッグモード有効${NC}"
fi

if [ "$PRODUCTION_MODE" = true ]; then
    export MKS_ENV=production

    # 本番環境設定ファイルの読み込み
    if [ -f ".env.production" ]; then
        echo -e "${GREEN}.env.production を読み込み中...${NC}"
        set -a
        source .env.production
        set +a
    else
        echo -e "${YELLOW}警告: .env.production が見つかりません${NC}"
    fi
fi

# 起動情報表示
echo ""
echo -e "${BLUE}起動設定:${NC}"
echo -e "  ポート番号: ${GREEN}$PORT${NC}"
echo -e "  環境: ${GREEN}${MKS_ENV:-development}${NC}"
echo -e "  デバッグ: ${GREEN}${MKS_DEBUG:-false}${NC}"

if [ "$PRODUCTION_MODE" = true ]; then
    echo -e "  モード: ${GREEN}本番（Gunicorn）${NC}"
    echo -e "  ワーカー数: ${GREEN}$WORKERS${NC}"
else
    echo -e "  モード: ${GREEN}開発（Flask開発サーバー）${NC}"
fi

echo ""
echo -e "${BLUE}アクセスURL:${NC}"
echo -e "  ${GREEN}http://localhost:$PORT${NC}"
echo -e "  ${GREEN}http://192.168.0.187:$PORT${NC}"
echo ""

# 起動前チェック
echo -e "${YELLOW}起動前チェック中...${NC}"

# ポート使用確認
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}エラー: ポート $PORT は既に使用されています${NC}"
    echo ""
    echo "使用中のプロセス:"
    lsof -i :$PORT
    echo ""
    echo "プロセスを終了してから再実行してください"
    exit 1
fi

# データディレクトリ確認
if [ ! -d "data" ]; then
    echo -e "${YELLOW}dataディレクトリが見つかりません。作成します...${NC}"
    mkdir -p data
fi

# 必須データファイル作成
for file in users.json knowledge.json sop.json access_logs.json notifications.json approvals.json; do
    if [ ! -f "data/$file" ]; then
        echo "[]" > "data/$file"
        echo -e "${GREEN}作成: data/$file${NC}"
    fi
done

echo -e "${GREEN}✓ 起動前チェック完了${NC}"
echo ""

# アプリケーション起動
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  バックエンドを起動しています...${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

if [ "$PRODUCTION_MODE" = true ]; then
    # 本番モード（Gunicorn）
    if ! command -v gunicorn &> /dev/null; then
        echo -e "${RED}エラー: Gunicornがインストールされていません${NC}"
        echo "  pip install gunicorn"
        exit 1
    fi

    echo -e "${GREEN}Gunicornで起動中...${NC}"
    gunicorn \
        --bind 0.0.0.0:$PORT \
        --workers $WORKERS \
        --threads 2 \
        --timeout 30 \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --log-level info \
        app_v2:app
else
    # 開発モード（Flask開発サーバー）
    echo -e "${GREEN}Flask開発サーバーで起動中...${NC}"
    python3 app_v2.py
fi
