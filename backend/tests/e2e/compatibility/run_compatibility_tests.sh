#!/bin/bash

##############################################################################
# ブラウザ・デバイス互換性テスト実行スクリプト
#
# 使用方法:
#   ./run_compatibility_tests.sh [オプション]
#
# オプション:
#   --browsers-only     ブラウザテストのみ実行
#   --responsive-only   レスポンシブテストのみ実行
#   --browser <name>    特定のブラウザのみテスト (chromium|firefox|webkit|edge)
#   --headed           ヘッド付きモードで実行
#   --debug            デバッグモードで実行
#   --ui               UIモードで実行
#   --help             ヘルプ表示
##############################################################################

set -e  # エラー時に即座に終了

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# スクリプトのディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
E2E_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$(dirname "$(dirname "$E2E_DIR")")"

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ヘルプ表示
show_help() {
    cat << EOF
ブラウザ・デバイス互換性テスト実行スクリプト

使用方法:
    ./run_compatibility_tests.sh [オプション]

オプション:
    --browsers-only       ブラウザテストのみ実行
    --responsive-only     レスポンシブテストのみ実行
    --browser <name>      特定のブラウザのみテスト (chromium|firefox|webkit|edge)
    --headed              ヘッド付きモードで実行（ブラウザが表示される）
    --debug               デバッグモードで実行
    --ui                  UIモードで実行
    --no-server           Webサーバーを起動しない（既に起動済みの場合）
    --help                このヘルプを表示

例:
    # 全テスト実行
    ./run_compatibility_tests.sh

    # ブラウザテストのみ
    ./run_compatibility_tests.sh --browsers-only

    # Chrome（Chromium）のみでテスト
    ./run_compatibility_tests.sh --browser chromium

    # ヘッド付きモードで実行
    ./run_compatibility_tests.sh --headed

    # デバッグモード
    ./run_compatibility_tests.sh --debug
EOF
}

# デフォルト設定
RUN_BROWSERS=true
RUN_RESPONSIVE=true
SPECIFIC_BROWSER=""
HEADED=""
DEBUG=""
UI_MODE=""
NO_SERVER=""

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --browsers-only)
            RUN_BROWSERS=true
            RUN_RESPONSIVE=false
            shift
            ;;
        --responsive-only)
            RUN_BROWSERS=false
            RUN_RESPONSIVE=true
            shift
            ;;
        --browser)
            SPECIFIC_BROWSER="$2"
            shift 2
            ;;
        --headed)
            HEADED="--headed"
            shift
            ;;
        --debug)
            DEBUG="--debug"
            shift
            ;;
        --ui)
            UI_MODE="--ui"
            shift
            ;;
        --no-server)
            NO_SERVER="true"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

# ヘッダー表示
echo "======================================================================"
echo "  ブラウザ・デバイス互換性テスト"
echo "======================================================================"
echo ""

# 環境確認
log_info "環境確認中..."

# Node.js確認
if ! command -v node &> /dev/null; then
    log_error "Node.jsがインストールされていません"
    exit 1
fi
log_success "Node.js: $(node --version)"

# npm確認
if ! command -v npm &> /dev/null; then
    log_error "npmがインストールされていません"
    exit 1
fi
log_success "npm: $(npm --version)"

# E2Eディレクトリに移動
cd "$E2E_DIR"
log_info "作業ディレクトリ: $E2E_DIR"

# 依存関係インストール
if [ ! -d "node_modules" ]; then
    log_info "依存関係をインストール中..."
    npm install
    log_success "依存関係のインストールが完了しました"
else
    log_info "依存関係は既にインストールされています"
fi

# Playwrightブラウザインストール確認
log_info "Playwrightブラウザを確認中..."
if [ ! -d "$HOME/.cache/ms-playwright" ] && [ ! -d "$HOME/Library/Caches/ms-playwright" ]; then
    log_warning "Playwrightブラウザがインストールされていません"
    log_info "Playwrightブラウザをインストール中..."
    npx playwright install
    log_success "Playwrightブラウザのインストールが完了しました"
fi

# レポートディレクトリ作成
REPORT_DIR="$E2E_DIR/reports"
mkdir -p "$REPORT_DIR"
log_info "レポートディレクトリ: $REPORT_DIR"

# タイムスタンプ
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
log_info "テスト実行時刻: $(date '+%Y-%m-%d %H:%M:%S')"

# 環境変数設定
if [ -z "$NO_SERVER" ]; then
    export NO_WEB_SERVER=""
else
    export NO_WEB_SERVER="true"
fi

# テスト実行関数
run_test() {
    local test_file=$1
    local test_name=$2
    local project=$3

    log_info "実行中: $test_name"

    local cmd="npx playwright test $test_file $HEADED $DEBUG $UI_MODE"

    if [ -n "$project" ]; then
        cmd="$cmd --project=$project"
    fi

    echo "コマンド: $cmd"

    if $cmd; then
        log_success "$test_name が完了しました"
        return 0
    else
        log_error "$test_name が失敗しました"
        return 1
    fi
}

# テスト結果追跡
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ブラウザテスト実行
if [ "$RUN_BROWSERS" = true ]; then
    echo ""
    echo "======================================================================"
    echo "  ブラウザ互換性テスト"
    echo "======================================================================"

    if [ -n "$SPECIFIC_BROWSER" ]; then
        log_info "ブラウザ: $SPECIFIC_BROWSER"
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        if run_test "compatibility/browsers.spec.js" "ブラウザテスト ($SPECIFIC_BROWSER)" "$SPECIFIC_BROWSER-desktop"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        # 全ブラウザでテスト
        for browser in chromium firefox webkit; do
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            if run_test "compatibility/browsers.spec.js" "ブラウザテスト ($browser)" "$browser-desktop"; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
        done

        # Edgeテスト（利用可能な場合）
        if command -v microsoft-edge &> /dev/null || command -v msedge &> /dev/null; then
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
            if run_test "compatibility/browsers.spec.js" "ブラウザテスト (edge)" "edge-desktop"; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
        else
            log_warning "Microsoft Edgeが利用できないため、Edgeテストをスキップします"
        fi
    fi
fi

# レスポンシブテスト実行
if [ "$RUN_RESPONSIVE" = true ]; then
    echo ""
    echo "======================================================================"
    echo "  レスポンシブデザインテスト"
    echo "======================================================================"

    # デスクトップ
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "compatibility/responsive.spec.js" "レスポンシブテスト (デスクトップ)" "chromium-desktop"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # ノートPC
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "compatibility/responsive.spec.js" "レスポンシブテスト (ノートPC)" "chromium-laptop"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # タブレット
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "compatibility/responsive.spec.js" "レスポンシブテスト (タブレット)" "ipad-portrait"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # スマートフォン
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if run_test "compatibility/responsive.spec.js" "レスポンシブテスト (スマートフォン)" "iphone-13"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

# スクリーンショット収集
echo ""
log_info "スクリーンショットを収集中..."
SCREENSHOT_DIR="$REPORT_DIR/screenshots_$TIMESTAMP"
mkdir -p "$SCREENSHOT_DIR"

# Playwrightの成果物からスクリーンショットをコピー
if [ -d "$E2E_DIR/test-results" ]; then
    find "$E2E_DIR/test-results" -name "*.png" -exec cp {} "$SCREENSHOT_DIR/" \; 2>/dev/null || true
    SCREENSHOT_COUNT=$(find "$SCREENSHOT_DIR" -name "*.png" | wc -l)
    log_success "スクリーンショット $SCREENSHOT_COUNT 枚を保存しました: $SCREENSHOT_DIR"
fi

# レポート生成
echo ""
log_info "HTMLレポートを生成中..."
npx playwright show-report --host 127.0.0.1 --port 9323 &
REPORT_PID=$!
sleep 2
log_success "HTMLレポートサーバーを起動しました (PID: $REPORT_PID)"
log_info "ブラウザでレポートを確認: http://127.0.0.1:9323"

# 結果サマリー
echo ""
echo "======================================================================"
echo "  テスト結果サマリー"
echo "======================================================================"
echo "総テスト数:   $TOTAL_TESTS"
echo -e "${GREEN}成功:${NC}         $PASSED_TESTS"
echo -e "${RED}失敗:${NC}         $FAILED_TESTS"
echo ""
echo "詳細レポート: $REPORT_DIR/playwright-html/index.html"
echo "スクリーンショット: $SCREENSHOT_DIR"
echo ""

# 終了コード
if [ $FAILED_TESTS -eq 0 ]; then
    log_success "すべてのテストが成功しました！"
    echo ""
    echo "レポートサーバーを停止するには: kill $REPORT_PID"
    exit 0
else
    log_error "$FAILED_TESTS 件のテストが失敗しました"
    echo ""
    echo "レポートサーバーを停止するには: kill $REPORT_PID"
    exit 1
fi
