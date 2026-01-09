#!/bin/bash
#
# Mirai Knowledge System - ログ分析スクリプト
#
# このスクリプトはシステムログを分析し、統計情報や異常検知を行います。
#
# 使用方法:
#   ./scripts/log-analysis.sh [command] [options]
#
# コマンド:
#   error-summary     エラーログの集計
#   access-stats      アクセスログの統計
#   disk-usage        ログディスク使用量確認
#   recent-errors     最近のエラー一覧
#   slow-requests     遅いリクエストの検出
#   status-codes      HTTPステータスコード集計
#   top-ips           アクセス元IP集計
#   user-activity     ユーザーアクティビティ分析
#   full-report       全レポート出力
#   clean-old-logs    古いログの削除（慎重に使用）
#

set -e

# ==============================================================================
# 設定
# ==============================================================================

LOG_DIR="/var/log/mirai-knowledge"
ACCESS_LOG="$LOG_DIR/access.log"
ERROR_LOG="$LOG_DIR/error.log"
APP_LOG="$LOG_DIR/app.log"
AUDIT_LOG="$LOG_DIR/audit.log"

# 色付き出力
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

# ==============================================================================
# ヘルパー関数
# ==============================================================================

print_header() {
    echo -e "\n${COLOR_BLUE}========================================${COLOR_RESET}"
    echo -e "${COLOR_BLUE}$1${COLOR_RESET}"
    echo -e "${COLOR_BLUE}========================================${COLOR_RESET}\n"
}

print_success() {
    echo -e "${COLOR_GREEN}✓ $1${COLOR_RESET}"
}

print_warning() {
    echo -e "${COLOR_YELLOW}⚠ $1${COLOR_RESET}"
}

print_error() {
    echo -e "${COLOR_RED}✗ $1${COLOR_RESET}"
}

check_log_file() {
    local log_file=$1
    if [ ! -f "$log_file" ]; then
        print_error "ログファイルが見つかりません: $log_file"
        return 1
    fi
    return 0
}

# ==============================================================================
# エラーログ分析
# ==============================================================================

error_summary() {
    print_header "エラーログ集計"

    if ! check_log_file "$ERROR_LOG"; then
        return 1
    fi

    echo "=== ログレベル別集計 ==="
    if grep -q '"level":' "$ERROR_LOG" 2>/dev/null; then
        # JSON形式
        grep -o '"level":"[^"]*"' "$ERROR_LOG" | sort | uniq -c | sort -rn
    else
        # テキスト形式
        grep -E '(ERROR|WARNING|CRITICAL|INFO|DEBUG)' "$ERROR_LOG" | \
            grep -o -E '(ERROR|WARNING|CRITICAL|INFO|DEBUG)' | sort | uniq -c | sort -rn
    fi

    echo -e "\n=== エラー数統計 ==="
    local total_lines=$(wc -l < "$ERROR_LOG")
    local error_lines=$(grep -c '"level":"ERROR"' "$ERROR_LOG" 2>/dev/null || echo 0)
    local warning_lines=$(grep -c '"level":"WARNING"' "$ERROR_LOG" 2>/dev/null || echo 0)
    local critical_lines=$(grep -c '"level":"CRITICAL"' "$ERROR_LOG" 2>/dev/null || echo 0)

    echo "総行数: $total_lines"
    echo "ERROR: $error_lines"
    echo "WARNING: $warning_lines"
    echo "CRITICAL: $critical_lines"

    if [ "$critical_lines" -gt 0 ]; then
        print_error "CRITICALエラーが検出されました！"
    elif [ "$error_lines" -gt 100 ]; then
        print_warning "ERRORが多数検出されています"
    else
        print_success "エラーレベルは正常範囲です"
    fi
}

# ==============================================================================
# アクセスログ統計
# ==============================================================================

access_stats() {
    print_header "アクセスログ統計"

    if ! check_log_file "$ACCESS_LOG"; then
        return 1
    fi

    echo "=== HTTPステータスコード集計 ==="
    if grep -q '"status":' "$ACCESS_LOG" 2>/dev/null; then
        # JSON形式
        grep -o '"status":[0-9]*' "$ACCESS_LOG" | cut -d: -f2 | sort | uniq -c | sort -rn | head -10
    else
        # テキスト形式（標準アクセスログ形式）
        awk '{print $9}' "$ACCESS_LOG" | sort | uniq -c | sort -rn | head -10
    fi

    echo -e "\n=== リクエストメソッド集計 ==="
    if grep -q '"method":' "$ACCESS_LOG" 2>/dev/null; then
        # JSON形式
        grep -o '"method":"[^"]*"' "$ACCESS_LOG" | cut -d'"' -f4 | sort | uniq -c | sort -rn
    fi

    echo -e "\n=== アクセス数集計 ==="
    local total_requests=$(wc -l < "$ACCESS_LOG")
    local success_requests=$(grep -c '"status":200' "$ACCESS_LOG" 2>/dev/null || echo 0)
    local error_requests=$(grep -c '"status":[45][0-9][0-9]' "$ACCESS_LOG" 2>/dev/null || echo 0)

    echo "総リクエスト数: $total_requests"
    echo "成功 (200): $success_requests"
    echo "エラー (4xx/5xx): $error_requests"

    if [ "$total_requests" -gt 0 ]; then
        local success_rate=$((success_requests * 100 / total_requests))
        echo "成功率: ${success_rate}%"

        if [ "$success_rate" -lt 95 ]; then
            print_warning "成功率が低下しています"
        else
            print_success "成功率は正常範囲です"
        fi
    fi
}

# ==============================================================================
# ディスク使用量確認
# ==============================================================================

disk_usage() {
    print_header "ログディスク使用量"

    if [ ! -d "$LOG_DIR" ]; then
        print_error "ログディレクトリが見つかりません: $LOG_DIR"
        return 1
    fi

    echo "=== ディレクトリ全体 ==="
    du -sh "$LOG_DIR"

    echo -e "\n=== ファイル別使用量（上位10件） ==="
    du -h "$LOG_DIR"/* 2>/dev/null | sort -rh | head -10

    echo -e "\n=== 圧縮ファイル数 ==="
    local compressed_count=$(find "$LOG_DIR" -name "*.gz" 2>/dev/null | wc -l)
    echo "圧縮済みログ: $compressed_count ファイル"

    echo -e "\n=== ディスクパーティション使用率 ==="
    df -h "$LOG_DIR" | tail -1

    local disk_usage_percent=$(df "$LOG_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage_percent" -gt 90 ]; then
        print_error "ディスク使用率が90%を超えています！"
    elif [ "$disk_usage_percent" -gt 80 ]; then
        print_warning "ディスク使用率が80%を超えています"
    else
        print_success "ディスク使用率は正常範囲です"
    fi
}

# ==============================================================================
# 最近のエラー
# ==============================================================================

recent_errors() {
    print_header "最近のエラー（直近50件）"

    if ! check_log_file "$ERROR_LOG"; then
        return 1
    fi

    if grep -q '"level":"ERROR"' "$ERROR_LOG" 2>/dev/null; then
        # JSON形式
        grep '"level":"ERROR"' "$ERROR_LOG" | tail -50 | jq -r '[.timestamp, .level, .message] | @tsv' 2>/dev/null || \
        grep '"level":"ERROR"' "$ERROR_LOG" | tail -50
    else
        # テキスト形式
        grep 'ERROR' "$ERROR_LOG" | tail -50
    fi
}

# ==============================================================================
# 遅いリクエスト検出
# ==============================================================================

slow_requests() {
    print_header "遅いリクエスト（レスポンス時間 > 1秒）"

    if ! check_log_file "$ACCESS_LOG"; then
        return 1
    fi

    # JSON形式のログから1秒以上かかったリクエストを抽出
    if grep -q '"response_time_ms":' "$ACCESS_LOG" 2>/dev/null; then
        echo "=== 1秒以上のリクエスト ==="
        grep '"response_time_ms":' "$ACCESS_LOG" | \
            awk -F'"response_time_ms":' '{print $2}' | \
            awk -F',' '{if ($1 > 1000) print $0}' | \
            wc -l | \
            xargs -I {} echo "検出数: {} 件"

        echo -e "\n=== 上位10件（遅い順） ==="
        grep '"response_time_ms":' "$ACCESS_LOG" | \
            jq -r '[.timestamp, .method, .path, .response_time_ms, .status] | @tsv' 2>/dev/null | \
            awk '$4 > 1000' | \
            sort -k4 -rn | \
            head -10 || echo "jqがインストールされていないため、詳細を表示できません"
    else
        print_warning "JSON形式のログではないため、レスポンス時間を解析できません"
    fi
}

# ==============================================================================
# HTTPステータスコード集計
# ==============================================================================

status_codes() {
    print_header "HTTPステータスコード詳細"

    if ! check_log_file "$ACCESS_LOG"; then
        return 1
    fi

    if grep -q '"status":' "$ACCESS_LOG" 2>/dev/null; then
        echo "=== ステータスコード別集計 ==="
        grep -o '"status":[0-9]*' "$ACCESS_LOG" | \
            cut -d: -f2 | \
            sort | \
            uniq -c | \
            sort -rn | \
            awk '{
                status = $2;
                count = $1;
                if (status >= 200 && status < 300) category = "Success";
                else if (status >= 300 && status < 400) category = "Redirect";
                else if (status >= 400 && status < 500) category = "Client Error";
                else if (status >= 500) category = "Server Error";
                else category = "Unknown";
                printf "%-15s %s (%d件)\n", category, status, count;
            }'

        echo -e "\n=== クライアントエラー（4xx）上位 ==="
        grep -o '"status":4[0-9][0-9]' "$ACCESS_LOG" | \
            cut -d: -f2 | \
            sort | \
            uniq -c | \
            sort -rn | \
            head -5

        echo -e "\n=== サーバーエラー（5xx）上位 ==="
        grep -o '"status":5[0-9][0-9]' "$ACCESS_LOG" | \
            cut -d: -f2 | \
            sort | \
            uniq -c | \
            sort -rn | \
            head -5
    fi
}

# ==============================================================================
# アクセス元IP集計
# ==============================================================================

top_ips() {
    print_header "アクセス元IP集計（上位20件）"

    if ! check_log_file "$ACCESS_LOG"; then
        return 1
    fi

    if grep -q '"remote_addr":' "$ACCESS_LOG" 2>/dev/null; then
        # JSON形式
        grep -o '"remote_addr":"[^"]*"' "$ACCESS_LOG" | \
            cut -d'"' -f4 | \
            sort | \
            uniq -c | \
            sort -rn | \
            head -20 | \
            awk '{printf "%8d  %s\n", $1, $2}'
    else
        # テキスト形式
        awk '{print $1}' "$ACCESS_LOG" | \
            sort | \
            uniq -c | \
            sort -rn | \
            head -20
    fi
}

# ==============================================================================
# ユーザーアクティビティ分析
# ==============================================================================

user_activity() {
    print_header "ユーザーアクティビティ分析"

    if ! check_log_file "$APP_LOG"; then
        print_warning "app.log が見つかりません。スキップします。"
        return 0
    fi

    echo "=== ユーザーID別アクティビティ ==="
    if grep -q '"user_id":' "$APP_LOG" 2>/dev/null; then
        grep -o '"user_id":[0-9]*' "$APP_LOG" | \
            cut -d: -f2 | \
            sort | \
            uniq -c | \
            sort -rn | \
            head -10 | \
            awk '{printf "User ID %s: %d アクション\n", $2, $1}'
    else
        echo "ユーザーID情報が見つかりません"
    fi
}

# ==============================================================================
# 全レポート出力
# ==============================================================================

full_report() {
    print_header "Mirai Knowledge System - ログ分析レポート"
    echo "生成日時: $(date '+%Y-%m-%d %H:%M:%S')"

    error_summary
    access_stats
    disk_usage
    slow_requests
    status_codes
    top_ips
    user_activity

    print_header "レポート完了"
}

# ==============================================================================
# 古いログの削除（慎重に使用）
# ==============================================================================

clean_old_logs() {
    print_header "古いログの削除"

    print_warning "この操作は古いログファイルを削除します。"
    echo -n "本当に実行しますか？ (yes/no): "
    read -r confirmation

    if [ "$confirmation" != "yes" ]; then
        echo "キャンセルされました"
        return 0
    fi

    echo -e "\n=== 90日以上前の圧縮ログを削除 ==="
    find "$LOG_DIR" -name "*.gz" -mtime +90 -type f -print -delete

    echo -e "\n=== 削除後のディスク使用量 ==="
    du -sh "$LOG_DIR"

    print_success "古いログの削除が完了しました"
}

# ==============================================================================
# メイン処理
# ==============================================================================

show_usage() {
    echo "使用方法: $0 [command]"
    echo ""
    echo "コマンド:"
    echo "  error-summary      エラーログの集計"
    echo "  access-stats       アクセスログの統計"
    echo "  disk-usage         ログディスク使用量確認"
    echo "  recent-errors      最近のエラー一覧"
    echo "  slow-requests      遅いリクエストの検出"
    echo "  status-codes       HTTPステータスコード集計"
    echo "  top-ips            アクセス元IP集計"
    echo "  user-activity      ユーザーアクティビティ分析"
    echo "  full-report        全レポート出力"
    echo "  clean-old-logs     古いログの削除（慎重に使用）"
    echo ""
    echo "例:"
    echo "  $0 full-report"
    echo "  $0 error-summary"
}

main() {
    local command=${1:-full-report}

    case "$command" in
        error-summary)
            error_summary
            ;;
        access-stats)
            access_stats
            ;;
        disk-usage)
            disk_usage
            ;;
        recent-errors)
            recent_errors
            ;;
        slow-requests)
            slow_requests
            ;;
        status-codes)
            status_codes
            ;;
        top-ips)
            top_ips
            ;;
        user-activity)
            user_activity
            ;;
        full-report)
            full_report
            ;;
        clean-old-logs)
            clean_old_logs
            ;;
        -h|--help|help)
            show_usage
            ;;
        *)
            print_error "不明なコマンド: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
