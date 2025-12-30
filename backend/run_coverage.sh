#!/bin/bash

# テストカバレッジ測定スクリプト
# 使用方法: ./run_coverage.sh

set -e

echo "=========================================="
echo "テストカバレッジ測定を開始します"
echo "=========================================="
echo ""

# カレントディレクトリ確認
if [ ! -f "app_v2.py" ]; then
    echo "エラー: backendディレクトリで実行してください"
    exit 1
fi

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "エラー: 仮想環境が見つかりません"
    echo "仮想環境を作成してください: python -m venv venv"
    exit 1
fi

# 仮想環境の有効化
echo "仮想環境を有効化中..."
source venv/bin/activate

# 依存関係の確認
echo "依存関係を確認中..."
pip install -q pytest pytest-cov pytest-flask 2>/dev/null || true

# レポートディレクトリの作成
echo "レポートディレクトリを作成中..."
mkdir -p tests/reports/coverage_html

# テスト実行とカバレッジ測定
echo ""
echo "=========================================="
echo "ユニットテスト & 統合テストを実行中..."
echo "=========================================="
echo ""

pytest tests/unit tests/integration \
    --cov=app_v2 \
    --cov=schemas \
    --cov-report=html:tests/reports/coverage_html \
    --cov-report=xml:tests/reports/coverage.xml \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v

COVERAGE_RESULT=$?

echo ""
echo "=========================================="
echo "カバレッジレポート生成完了"
echo "=========================================="
echo ""
echo "HTMLレポート: tests/reports/coverage_html/index.html"
echo "XMLレポート: tests/reports/coverage.xml"
echo ""

if [ $COVERAGE_RESULT -eq 0 ]; then
    echo "✓ カバレッジ目標 (80%) を達成しました！"
else
    echo "✗ カバレッジ目標 (80%) に達していません"
    echo "  HTMLレポートで詳細を確認してください"
fi

echo ""
echo "HTMLレポートをブラウザで開くには："
echo "  xdg-open tests/reports/coverage_html/index.html  # Linux"
echo "  open tests/reports/coverage_html/index.html      # macOS"
echo "  start tests/reports/coverage_html/index.html     # Windows"
echo ""

exit $COVERAGE_RESULT
