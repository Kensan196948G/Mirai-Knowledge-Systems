#!/bin/bash

###############################################################################
# 機能テスト一括実行スクリプト
#
# 全ての自動機能テストを実行し、結果をレポートとして出力します。
#
# 使用方法:
#   ./tests/run_functional_tests.sh [OPTIONS]
#
# オプション:
#   --html         HTML形式のレポートを生成
#   --coverage     カバレッジレポートを生成
#   --verbose      詳細な出力
#   --parallel     並列実行（高速化）
#   --acceptance   受け入れテストのみ実行
#   --endpoints    エンドポイントテストのみ実行
#   --help         ヘルプを表示
#
# 例:
#   ./tests/run_functional_tests.sh --html --coverage
#   ./tests/run_functional_tests.sh --acceptance --verbose
###############################################################################

set -e

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト設定
GENERATE_HTML=false
GENERATE_COVERAGE=false
VERBOSE=false
PARALLEL=false
TEST_SCOPE="all"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/tests/reports/functional"

# ヘルプメッセージ
show_help() {
    cat << EOF
機能テスト実行スクリプト

使用方法:
    $0 [OPTIONS]

オプション:
    --html          HTML形式のレポートを生成
    --coverage      カバレッジレポートを生成
    --verbose       詳細な出力
    --parallel      並列実行（高速化）
    --acceptance    受け入れテストのみ実行
    --endpoints     エンドポイントテストのみ実行
    --help          このヘルプを表示

例:
    $0 --html --coverage
    $0 --acceptance --verbose
    $0 --parallel --html

EOF
}

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --html)
            GENERATE_HTML=true
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --acceptance)
            TEST_SCOPE="acceptance"
            shift
            ;;
        --endpoints)
            TEST_SCOPE="endpoints"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 開始メッセージ
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  機能テスト実行開始${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 環境確認
echo -e "${YELLOW}環境確認中...${NC}"
cd "$PROJECT_ROOT"

if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${RED}エラー: Python仮想環境が見つかりません${NC}"
    echo -e "${YELLOW}以下のコマンドで仮想環境を作成してください:${NC}"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 仮想環境のアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 必要なパッケージの確認
echo -e "${YELLOW}依存パッケージ確認中...${NC}"
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${RED}エラー: pytest がインストールされていません${NC}"
    echo -e "${YELLOW}以下のコマンドでインストールしてください:${NC}"
    echo "  pip install pytest pytest-cov pytest-html pytest-xdist"
    exit 1
fi

# レポートディレクトリ作成
mkdir -p "$REPORT_DIR"

# テスト実行パスの決定
case $TEST_SCOPE in
    acceptance)
        TEST_PATH="tests/acceptance/test_all_features.py"
        ;;
    endpoints)
        TEST_PATH="tests/acceptance/test_api_endpoints.py"
        ;;
    all)
        TEST_PATH="tests/acceptance/"
        ;;
esac

# pytestオプション構築
PYTEST_OPTS="-v"

if [ "$VERBOSE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -vv -s"
fi

if [ "$PARALLEL" = true ]; then
    if python -c "import xdist" 2>/dev/null; then
        PYTEST_OPTS="$PYTEST_OPTS -n auto"
        echo -e "${GREEN}並列実行モード有効${NC}"
    else
        echo -e "${YELLOW}警告: pytest-xdist がインストールされていません。並列実行を無効化します${NC}"
        echo -e "${YELLOW}インストール: pip install pytest-xdist${NC}"
    fi
fi

if [ "$GENERATE_HTML" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS --html=$REPORT_DIR/report.html --self-contained-html"
fi

if [ "$GENERATE_COVERAGE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS --cov=. --cov-report=html:$REPORT_DIR/coverage --cov-report=term"
fi

# テスト実行
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  テスト実行中: $TEST_SCOPE${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$REPORT_DIR/test_run_$TIMESTAMP.log"

if pytest $PYTEST_OPTS "$TEST_PATH" 2>&1 | tee "$LOG_FILE"; then
    TEST_RESULT=0
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  ✓ 全テスト成功${NC}"
    echo -e "${GREEN}================================================${NC}"
else
    TEST_RESULT=$?
    echo ""
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}  ✗ テスト失敗${NC}"
    echo -e "${RED}================================================${NC}"
fi

# レポート生成メッセージ
echo ""
echo -e "${BLUE}テスト結果サマリー:${NC}"
echo -e "  ログファイル: ${YELLOW}$LOG_FILE${NC}"

if [ "$GENERATE_HTML" = true ]; then
    echo -e "  HTMLレポート: ${YELLOW}$REPORT_DIR/report.html${NC}"
    echo -e "  ${GREEN}ブラウザで開く: file://$REPORT_DIR/report.html${NC}"
fi

if [ "$GENERATE_COVERAGE" = true ]; then
    echo -e "  カバレッジレポート: ${YELLOW}$REPORT_DIR/coverage/index.html${NC}"
    echo -e "  ${GREEN}ブラウザで開く: file://$REPORT_DIR/coverage/index.html${NC}"
fi

# テスト統計の表示
echo ""
echo -e "${BLUE}テスト統計:${NC}"
grep -E "(passed|failed|error|skipped)" "$LOG_FILE" | tail -5 || true

# CI/CD環境での使用を考慮した終了コード
echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}全ての機能テストが正常に完了しました${NC}"
    exit 0
else
    echo -e "${RED}一部のテストが失敗しました (終了コード: $TEST_RESULT)${NC}"
    echo -e "${YELLOW}詳細はログファイルを確認してください: $LOG_FILE${NC}"
    exit $TEST_RESULT
fi
