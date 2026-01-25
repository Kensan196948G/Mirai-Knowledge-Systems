#!/bin/bash
# ==========================================================
# 建設土木ナレッジシステム - 本番環境起動スクリプト
# ==========================================================
#
# 使用方法:
#   1. 環境変数を設定（.env.productionファイルまたは直接export）
#   2. chmod +x run_production.sh
#   3. ./run_production.sh [start|stop|restart|status|check]
#
# ==========================================================

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="mirai-knowledge-system"
PID_FILE="${SCRIPT_DIR}/gunicorn.pid"
LOG_DIR="${SCRIPT_DIR}/logs"
VENV_DIR="${SCRIPT_DIR}/venv"

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==========================================================
# 環境変数チェック
# ==========================================================

check_env() {
    log_info "環境変数をチェックしています..."

    # 本番環境設定ファイルの読み込み
    if [ -f "${SCRIPT_DIR}/.env.production" ]; then
        log_info ".env.production から環境変数を読み込みます"
        set -a
        source "${SCRIPT_DIR}/.env.production"
        set +a
    elif [ -f "${SCRIPT_DIR}/.env" ]; then
        log_warn ".env.production が見つかりません。.env を使用します"
        set -a
        source "${SCRIPT_DIR}/.env"
        set +a
    fi

    # 必須環境変数のチェック
    local required_vars=("MKS_SECRET_KEY" "MKS_JWT_SECRET_KEY" "MKS_CORS_ORIGINS")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "必須環境変数が設定されていません: ${missing_vars[*]}"
        log_error "以下の環境変数を設定してください:"
        echo ""
        echo "  export MKS_ENV=production"
        echo "  export MKS_SECRET_KEY=\"your-secret-key\""
        echo "  export MKS_JWT_SECRET_KEY=\"your-jwt-secret-key\""
        echo "  export MKS_CORS_ORIGINS=\"https://example.com\""
        echo ""
        return 1
    fi

    # 本番環境フラグを設定
    export MKS_ENV="${MKS_ENV:-production}"

    log_info "環境変数チェック完了"
    return 0
}

# ==========================================================
# 前提条件チェック
# ==========================================================

check_prerequisites() {
    log_info "前提条件をチェックしています..."

    # Python仮想環境
    if [ -d "$VENV_DIR" ]; then
        log_info "仮想環境を検出: $VENV_DIR"
        source "$VENV_DIR/bin/activate"
    else
        log_warn "仮想環境が見つかりません。システムPythonを使用します"
    fi

    # Gunicornのインストール確認
    if ! command -v gunicorn &> /dev/null; then
        log_error "Gunicornがインストールされていません"
        log_info "インストール: pip install gunicorn"
        return 1
    fi

    # ログディレクトリの作成
    mkdir -p "$LOG_DIR"

    # SSL証明書の確認（HTTPS使用時）
    SSL_CERT="${MKS_SSL_CERT_PATH:-${SCRIPT_DIR}/ssl/server.crt}"
    SSL_KEY="${MKS_SSL_KEY_PATH:-${SCRIPT_DIR}/ssl/server.key}"

    if [ "${MKS_USE_SSL:-false}" = "true" ]; then
        if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
            log_error "SSL証明書が見つかりません"
            log_info "証明書パス: $SSL_CERT"
            log_info "秘密鍵パス: $SSL_KEY"
            return 1
        fi
        log_info "SSL証明書を確認しました"
    fi

    log_info "前提条件チェック完了"
    return 0
}

# ==========================================================
# Gunicorn設定
# ==========================================================

get_gunicorn_options() {
    local options=""

    # ワーカー数（デフォルト: CPUコア数 * 2 + 1）
    local workers="${MKS_GUNICORN_WORKERS:-$(( $(nproc) * 2 + 1 ))}"
    options="$options --workers $workers"

    # ワーカークラス
    options="$options --worker-class ${MKS_GUNICORN_WORKER_CLASS:-sync}"

    # スレッド数
    options="$options --threads ${MKS_GUNICORN_THREADS:-2}"

    # バインドアドレス
    options="$options --bind ${MKS_GUNICORN_BIND:-127.0.0.1:8000}"

    # タイムアウト
    options="$options --timeout ${MKS_GUNICORN_TIMEOUT:-30}"

    # グレースフルタイムアウト
    options="$options --graceful-timeout ${MKS_GUNICORN_GRACEFUL_TIMEOUT:-30}"

    # Keep-Alive
    options="$options --keep-alive ${MKS_GUNICORN_KEEPALIVE:-5}"

    # PIDファイル
    options="$options --pid $PID_FILE"

    # ログ
    options="$options --access-logfile ${LOG_DIR}/access.log"
    options="$options --error-logfile ${LOG_DIR}/error.log"
    options="$options --log-level ${MKS_LOG_LEVEL:-info}"

    # SSL（Gunicornで直接SSL終端する場合）
    if [ "${MKS_USE_SSL:-false}" = "true" ]; then
        options="$options --certfile $SSL_CERT"
        options="$options --keyfile $SSL_KEY"
    fi

    # デーモンモード
    options="$options --daemon"

    echo "$options"
}

# ==========================================================
# コマンド実行
# ==========================================================

start_server() {
    log_info "サーバーを起動しています..."

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_error "サーバーは既に起動しています (PID: $pid)"
            return 1
        else
            log_warn "古いPIDファイルを削除します"
            rm -f "$PID_FILE"
        fi
    fi

    check_env || return 1
    check_prerequisites || return 1

    cd "$SCRIPT_DIR"

    local options=$(get_gunicorn_options)

    log_info "Gunicornを起動: gunicorn $options app_v2:app"
    gunicorn $options app_v2:app

    sleep 2

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        log_info "サーバーが起動しました (PID: $pid)"
        log_info "アクセスログ: ${LOG_DIR}/access.log"
        log_info "エラーログ: ${LOG_DIR}/error.log"
    else
        log_error "サーバーの起動に失敗しました"
        return 1
    fi
}

stop_server() {
    log_info "サーバーを停止しています..."

    if [ ! -f "$PID_FILE" ]; then
        log_warn "PIDファイルが見つかりません"
        return 0
    fi

    local pid=$(cat "$PID_FILE")

    if kill -0 "$pid" 2>/dev/null; then
        log_info "グレースフルシャットダウンを実行 (PID: $pid)"
        kill -TERM "$pid"

        # プロセスの終了を待機（最大30秒）
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 30 ]; do
            sleep 1
            count=$((count + 1))
        done

        if kill -0 "$pid" 2>/dev/null; then
            log_warn "グレースフルシャットダウンがタイムアウト。強制終了します"
            kill -KILL "$pid"
        fi

        rm -f "$PID_FILE"
        log_info "サーバーを停止しました"
    else
        log_warn "プロセスが見つかりません"
        rm -f "$PID_FILE"
    fi
}

restart_server() {
    log_info "サーバーを再起動しています..."
    stop_server
    sleep 2
    start_server
}

status_server() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "サーバーは起動しています (PID: $pid)"

            # ワーカー情報を表示
            local worker_count=$(pgrep -P "$pid" | wc -l)
            log_info "アクティブワーカー数: $worker_count"

            # メモリ使用量
            local mem=$(ps -o rss= -p "$pid" 2>/dev/null | awk '{print $1/1024}')
            log_info "メモリ使用量 (マスター): ${mem}MB"

            return 0
        else
            log_warn "PIDファイルは存在しますが、プロセスが見つかりません"
            return 1
        fi
    else
        log_info "サーバーは停止しています"
        return 1
    fi
}

reload_server() {
    log_info "設定をリロードしています..."

    if [ ! -f "$PID_FILE" ]; then
        log_error "サーバーが起動していません"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill -HUP "$pid"
        log_info "リロードシグナルを送信しました (PID: $pid)"
    else
        log_error "プロセスが見つかりません"
        return 1
    fi
}

check_config() {
    log_info "設定をチェックしています..."

    check_env || return 1
    check_prerequisites || return 1

    # Pythonモジュールのインポートテスト
    python3 -c "from app_v2 import app; print('[OK] app_v2 モジュールのインポート成功')" || {
        log_error "app_v2 モジュールのインポートに失敗しました"
        return 1
    }

    # 設定ファイルのチェック
    if [ -f "${SCRIPT_DIR}/config/production.py" ]; then
        python3 -c "from config.production import get_config; print('[OK] production.py のロード成功')" || {
            log_error "production.py のロードに失敗しました"
            return 1
        }
    fi

    log_info "設定チェック完了"
}

show_help() {
    echo "使用方法: $0 {start|stop|restart|status|reload|check|help}"
    echo ""
    echo "コマンド:"
    echo "  start   - サーバーを起動"
    echo "  stop    - サーバーを停止"
    echo "  restart - サーバーを再起動"
    echo "  status  - サーバーの状態を表示"
    echo "  reload  - 設定をリロード（ダウンタイムなし）"
    echo "  check   - 設定と前提条件をチェック"
    echo "  help    - このヘルプを表示"
    echo ""
    echo "環境変数:"
    echo "  MKS_ENV                    - 環境 (production/development)"
    echo "  MKS_SECRET_KEY             - アプリケーション秘密鍵"
    echo "  MKS_JWT_SECRET_KEY         - JWT秘密鍵"
    echo "  MKS_CORS_ORIGINS           - 許可オリジン（カンマ区切り）"
    echo "  MKS_GUNICORN_WORKERS       - ワーカー数"
    echo "  MKS_GUNICORN_BIND          - バインドアドレス"
    echo "  MKS_USE_SSL                - GunicornでSSLを使用 (true/false)"
    echo "  MKS_SSL_CERT_PATH          - SSL証明書パス"
    echo "  MKS_SSL_KEY_PATH           - SSL秘密鍵パス"
}

# ==========================================================
# メイン処理
# ==========================================================

case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    reload)
        reload_server
        ;;
    check)
        check_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|reload|check|help}"
        exit 1
        ;;
esac
