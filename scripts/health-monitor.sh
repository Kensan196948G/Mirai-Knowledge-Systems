#!/bin/bash
# Health Monitor Script for Mirai Knowledge Systems
# Version: 1.0.0
# Last Updated: 2026-01-09
# Description: ヘルスチェックを実行し、問題があればアラートを送信

set -euo pipefail

# ========================================
# 設定
# ========================================

API_URL="${API_URL:-http://localhost:5100}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
LOG_FILE="${LOG_FILE:-/var/log/mks/health-monitor.log}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ========================================
# ロギング関数
# ========================================

log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$TIMESTAMP] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# ========================================
# アラート送信関数
# ========================================

send_alert() {
    local alertname="$1"
    local severity="$2"
    local summary="$3"
    local description="$4"

    local alert_payload=$(cat <<EOF
[{
  "labels": {
    "alertname": "$alertname",
    "severity": "$severity",
    "component": "health-monitor",
    "category": "manual-check"
  },
  "annotations": {
    "summary": "$summary",
    "description": "$description",
    "timestamp": "$TIMESTAMP"
  }
}]
EOF
)

    if curl -sf -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "$alert_payload" > /dev/null 2>&1; then
        log "Alert sent: $alertname ($severity)"
    else
        log_error "Failed to send alert: $alertname"
    fi
}

# ========================================
# ヘルスチェック関数
# ========================================

check_health() {
    log "Starting health check..."

    # API ヘルスチェック
    if ! response=$(curl -sf "$API_URL/api/v1/health" 2>&1); then
        log_error "Failed to connect to API"
        send_alert \
            "ManualHealthCheckFailed" \
            "critical" \
            "Health check failed - API unreachable" \
            "Unable to connect to $API_URL/api/v1/health"
        return 1
    fi

    # JSON パース（jqがインストールされている場合）
    if command -v jq &> /dev/null; then
        status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")
    else
        # jqがない場合はPythonで代替
        status=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    fi

    log "Health status: $status"

    if [ "$status" != "healthy" ]; then
        log_error "System is unhealthy: $status"
        send_alert \
            "ManualHealthCheckUnhealthy" \
            "critical" \
            "Health check failed - System unhealthy" \
            "API returned status: $status. Response: $response"
        return 1
    fi

    log "Health check passed"
    return 0
}

# ========================================
# データベース接続チェック
# ========================================

check_database() {
    log "Checking database connectivity..."

    # データベースステータスをヘルスエンドポイントから確認
    if ! response=$(curl -sf "$API_URL/api/v1/health" 2>&1); then
        log_error "Cannot check database - API unreachable"
        return 1
    fi

    if command -v jq &> /dev/null; then
        db_status=$(echo "$response" | jq -r '.database.status' 2>/dev/null || echo "unknown")
    else
        db_status=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('database', {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    fi

    log "Database status: $db_status"

    if [ "$db_status" != "connected" ] && [ "$db_status" != "healthy" ]; then
        log_error "Database connection issue: $db_status"
        send_alert \
            "DatabaseConnectionFailed" \
            "critical" \
            "Database connection check failed" \
            "Database status: $db_status"
        return 1
    fi

    log "Database check passed"
    return 0
}

# ========================================
# ディスク容量チェック
# ========================================

check_disk_space() {
    log "Checking disk space..."

    # ルートパーティションの使用率を取得
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

    log "Disk usage: ${disk_usage}%"

    if [ "$disk_usage" -ge 95 ]; then
        log_error "Disk space critical: ${disk_usage}%"
        send_alert \
            "DiskSpaceCritical" \
            "critical" \
            "Disk space critically low" \
            "Disk usage is at ${disk_usage}%. Immediate action required."
        return 1
    elif [ "$disk_usage" -ge 85 ]; then
        log_error "Disk space warning: ${disk_usage}%"
        send_alert \
            "DiskSpaceLow" \
            "warning" \
            "Disk space running low" \
            "Disk usage is at ${disk_usage}%. Consider cleaning up."
        return 1
    fi

    log "Disk space check passed"
    return 0
}

# ========================================
# メモリ使用率チェック
# ========================================

check_memory() {
    log "Checking memory usage..."

    # メモリ使用率を計算
    if command -v free &> /dev/null; then
        memory_percent=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
        log "Memory usage: ${memory_percent}%"

        if [ "$memory_percent" -ge 95 ]; then
            log_error "Memory usage critical: ${memory_percent}%"
            send_alert \
                "CriticalMemoryUsage" \
                "critical" \
                "Memory usage critically high" \
                "Memory usage is at ${memory_percent}%"
            return 1
        elif [ "$memory_percent" -ge 90 ]; then
            log_error "Memory usage high: ${memory_percent}%"
            send_alert \
                "HighMemoryUsage" \
                "warning" \
                "Memory usage high" \
                "Memory usage is at ${memory_percent}%"
            return 1
        fi
    else
        log "Warning: 'free' command not available, skipping memory check"
    fi

    log "Memory check passed"
    return 0
}

# ========================================
# プロセスチェック
# ========================================

check_process() {
    log "Checking MKS backend process..."

    # systemd サービスの状態を確認
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet mks-backend; then
            log "MKS backend service is active"
        else
            log_error "MKS backend service is not active"
            send_alert \
                "ServiceDown" \
                "critical" \
                "MKS Backend service is down" \
                "systemctl reports mks-backend service is not active"
            return 1
        fi
    else
        # systemctl がない場合はプロセスを直接確認
        if pgrep -f "gunicorn.*app_v2:app" > /dev/null; then
            log "MKS backend process is running"
        else
            log_error "MKS backend process not found"
            send_alert \
                "ServiceDown" \
                "critical" \
                "MKS Backend process not running" \
                "Cannot find gunicorn process for MKS backend"
            return 1
        fi
    fi

    log "Process check passed"
    return 0
}

# ========================================
# ログファイルチェック
# ========================================

check_logs() {
    log "Checking for recent errors in logs..."

    local error_count=0
    local log_files=(
        "/var/log/mks/backend.log"
        "/var/log/mks/error.log"
    )

    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            # 過去5分間のERRORログをカウント
            error_count=$(grep -c "ERROR" "$log_file" 2>/dev/null | tail -100 || echo "0")

            if [ "$error_count" -gt 10 ]; then
                log_error "High error count in $log_file: $error_count"
                send_alert \
                    "HighErrorCount" \
                    "warning" \
                    "High error count in logs" \
                    "Found $error_count ERROR entries in $log_file"
            fi
        fi
    done

    log "Log check completed"
    return 0
}

# ========================================
# メイン処理
# ========================================

main() {
    log "=========================================="
    log "Health Monitor Started"
    log "=========================================="

    local exit_code=0

    # 各チェックを実行
    check_health || exit_code=1
    check_database || exit_code=1
    check_disk_space || exit_code=1
    check_memory || exit_code=1
    check_process || exit_code=1
    check_logs || exit_code=1

    if [ $exit_code -eq 0 ]; then
        log "All health checks passed ✓"
    else
        log_error "Some health checks failed ✗"
    fi

    log "=========================================="
    log "Health Monitor Completed (exit: $exit_code)"
    log "=========================================="

    return $exit_code
}

# ========================================
# スクリプト実行
# ========================================

# ログディレクトリの作成
mkdir -p "$(dirname "$LOG_FILE")"

# メイン処理を実行
main "$@"
