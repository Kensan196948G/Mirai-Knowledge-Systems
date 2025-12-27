#!/bin/bash
# ==============================================================================
# Mirai Knowledge Systems - 停止スクリプト
# ==============================================================================

set -e

# カラー出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"

echo -e "${YELLOW}サービスを停止しています...${NC}"
echo ""

# バックエンド停止
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${YELLOW}バックエンドを停止中 (PID: $BACKEND_PID)${NC}"
        kill "$BACKEND_PID"

        # プロセスが終了するまで待機（最大10秒）
        for i in {1..10}; do
            if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done

        # まだ動いている場合は強制終了
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo -e "${RED}強制終了します...${NC}"
            kill -9 "$BACKEND_PID"
        fi

        echo -e "${GREEN}✓ バックエンドを停止しました${NC}"
    else
        echo -e "${YELLOW}バックエンドは既に停止しています${NC}"
    fi
    rm -f "$BACKEND_PID_FILE"
else
    echo -e "${YELLOW}バックエンドPIDファイルが見つかりません${NC}"

    # プロセス名で検索して停止
    PIDS=$(pgrep -f "python.*app_v2.py" || true)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}実行中のバックエンドプロセスを発見: $PIDS${NC}"
        echo -e "${YELLOW}停止しますか? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            kill $PIDS
            echo -e "${GREEN}✓ プロセスを停止しました${NC}"
        fi
    fi
fi

# フロントエンド停止
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${YELLOW}フロントエンドを停止中 (PID: $FRONTEND_PID)${NC}"
        kill "$FRONTEND_PID"
        echo -e "${GREEN}✓ フロントエンドを停止しました${NC}"
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

echo ""
echo -e "${GREEN}✓ すべてのサービスを停止しました${NC}"
