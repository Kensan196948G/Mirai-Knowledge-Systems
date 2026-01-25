#!/bin/bash
# Mirai Knowledge System ログローテーション設定スクリプト
#
# 使用方法: sudo ./setup-logrotate.sh

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Mirai Knowledge System${NC}"
echo -e "${GREEN}  ログローテーション設定${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# root権限チェック
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}エラー: このスクリプトはroot権限で実行してください${NC}"
    echo "使用方法: sudo $0"
    exit 1
fi

# プロジェクトディレクトリ検出
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"
LOGROTATE_SRC="$PROJECT_DIR/backend/logrotate.d/mirai-knowledge-system"
LOGROTATE_DEST="/etc/logrotate.d/mirai-knowledge-system"
LOGS_DIR="$PROJECT_DIR/backend/logs"

echo -e "${YELLOW}プロジェクトディレクトリ: $PROJECT_DIR${NC}"
echo -e "${YELLOW}ログディレクトリ: $LOGS_DIR${NC}"
echo ""

# ログディレクトリ作成
if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${YELLOW}ログディレクトリを作成中...${NC}"
    mkdir -p "$LOGS_DIR"
    chown -R $SUDO_USER:$SUDO_USER "$LOGS_DIR"
    echo -e "${GREEN}✓ ログディレクトリを作成しました${NC}"
else
    echo -e "${GREEN}✓ ログディレクトリは既に存在します${NC}"
fi

# logrotate設定ファイルの存在確認
if [ ! -f "$LOGROTATE_SRC" ]; then
    echo -e "${RED}エラー: ログローテーション設定ファイルが見つかりません${NC}"
    echo "場所: $LOGROTATE_SRC"
    exit 1
fi

# logrotateがインストールされているか確認
if ! command -v logrotate &> /dev/null; then
    echo -e "${YELLOW}logrotateがインストールされていません。インストール中...${NC}"
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y logrotate
    elif command -v yum &> /dev/null; then
        yum install -y logrotate
    else
        echo -e "${RED}エラー: パッケージマネージャが見つかりません${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ logrotateをインストールしました${NC}"
fi

# ログローテーション設定をコピー
echo -e "${YELLOW}ログローテーション設定をコピー中...${NC}"
cp "$LOGROTATE_SRC" "$LOGROTATE_DEST"
chmod 644 "$LOGROTATE_DEST"
echo -e "${GREEN}✓ 設定ファイルをコピーしました: $LOGROTATE_DEST${NC}"

# 設定ファイルの検証
echo -e "${YELLOW}設定ファイルを検証中...${NC}"
if logrotate -d "$LOGROTATE_DEST" 2>&1 | grep -i "error" > /dev/null; then
    echo -e "${RED}エラー: ログローテーション設定に問題があります${NC}"
    logrotate -d "$LOGROTATE_DEST"
    exit 1
fi
echo -e "${GREEN}✓ 設定ファイルの検証に成功しました${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  設定完了！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "ログローテーション設定が完了しました。"
echo ""
echo -e "${YELLOW}設定内容:${NC}"
echo "  - 日次ローテーション"
echo "  - 通常ログ: 7日間保持"
echo "  - アクセスログ: 14日間保持（または100MB超過時）"
echo "  - エラーログ: 30日間保持"
echo "  - 圧縮: 有効（遅延圧縮）"
echo ""
echo -e "${YELLOW}手動テスト:${NC}"
echo "  sudo logrotate -f /etc/logrotate.d/mirai-knowledge-system"
echo ""
echo -e "${YELLOW}ログファイルの確認:${NC}"
echo "  ls -lh $LOGS_DIR"
echo ""
