#!/bin/bash
# データ移行ツールのテストスクリプト

set -e  # エラーが発生したら即座に終了

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=========================================="
echo "データ移行ツール - テストスクリプト"
echo "=========================================="
echo ""

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 関数: 成功メッセージ
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 関数: 警告メッセージ
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 関数: エラーメッセージ
error() {
    echo -e "${RED}✗ $1${NC}"
}

echo "ステップ 1: データベース接続確認"
echo "----------------------------------------"
if sudo systemctl is-active --quiet postgresql; then
    success "PostgreSQLが起動しています"
else
    warning "PostgreSQLが起動していません"
    echo "PostgreSQLを起動しますか? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        sudo systemctl start postgresql
        success "PostgreSQLを起動しました"
    else
        error "PostgreSQLが必要です。終了します。"
        exit 1
    fi
fi
echo ""

echo "ステップ 2: ナレッジインポートのプレビュー"
echo "----------------------------------------"
python3 tools/data_migration.py import-knowledge \
    --file tools/sample_data/knowledge_import_template.csv \
    --preview

echo ""
read -p "プレビュー結果を確認しました。続けますか? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    warning "ユーザーによりキャンセルされました"
    exit 0
fi

echo ""
echo "ステップ 3: SOPインポートのプレビュー"
echo "----------------------------------------"
python3 tools/data_migration.py import-sop \
    --file tools/sample_data/sop_import_template.csv \
    --preview

echo ""
read -p "プレビュー結果を確認しました。実際にインポートしますか? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    warning "ユーザーによりキャンセルされました"
    exit 0
fi

echo ""
echo "ステップ 4: ナレッジの実インポート"
echo "----------------------------------------"
python3 tools/data_migration.py import-knowledge \
    --file tools/sample_data/knowledge_import_template.csv

echo ""
success "ナレッジのインポートが完了しました"

echo ""
echo "ステップ 5: SOPの実インポート"
echo "----------------------------------------"
python3 tools/data_migration.py import-sop \
    --file tools/sample_data/sop_import_template.csv

echo ""
success "SOPのインポートが完了しました"

echo ""
echo "ステップ 6: バックアップ一覧の確認"
echo "----------------------------------------"
python3 tools/data_migration.py list-backups

echo ""
echo "=========================================="
success "すべてのテストが完了しました！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "  1. ブラウザでシステムにアクセスしてデータを確認"
echo "  2. 問題がある場合は、バックアップからロールバック可能"
echo "  3. 独自のデータファイルを準備してインポート"
echo ""
