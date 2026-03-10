#!/usr/bin/env bash
# Claude Code Statusline v2
# Format:
#   🤖 Opus 4.6 │ 📁 Linux-Management-Systm │ 🌿 main  │ 🔑 -  │ 🖥 Linux
#   📊 25% │ ✏️  +5/-1 │🌐 online
#   ⏱ 5h  ▰▰▰▱▱▱▱▱▱▱  28%  Resets 9pm (Asia/Tokyo)
#   📅 7d  ▰▰▰▰▰▰▱▱▱▱  59%  Resets Mar 6 at 1pm (Asia/Tokyo)
set -euo pipefail

# === 入力受付 ===
input="$(cat)"
if [ -z "$input" ]; then
    input="{\"model\":{\"display_name\":\"Unknown\"},\"workspace\":{\"current_dir\":\"$(pwd)\"},\"context_window\":{\"used_percentage\":0},\"session\":{}}"
fi

# === Line 1 パース ===
MODEL_FULL=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
MODEL_SHORT="${MODEL_FULL#Claude }"  # "Claude Opus 4.6" → "Opus 4.6"

USED_PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
USED_PCT=$(printf '%.0f' "${USED_PCT:-0}" 2>/dev/null || echo 0)

LINES_ADDED=$(echo "$input" | jq -r '.session.lines_added // 0')
LINES_REMOVED=$(echo "$input" | jq -r '.session.lines_removed // 0')

DIR=$(echo "$input" | jq -r '.workspace.current_dir // "."')
DIR="${DIR:-.}"

DIR_NAME=$(basename "$DIR")

# Git ブランチ
GIT_BRANCH=""
if git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1; then
    GIT_BRANCH=$(git -C "$DIR" branch --show-current 2>/dev/null || true)
    if [ -z "$GIT_BRANCH" ]; then
        GIT_BRANCH=$(git -C "$DIR" rev-parse --short HEAD 2>/dev/null || true)
    fi
fi
BRANCH_SEG=""
[ -n "$GIT_BRANCH" ] && BRANCH_SEG=" │ 🌿 $GIT_BRANCH"

# APIキー状態・OS種別・ネット状態
API_KEY_STATUS=$([ -n "${ANTHROPIC_API_KEY:-}" ] && echo "✓" || echo "-")
OS_TYPE=$(uname -s 2>/dev/null || echo "Linux")
NET_STATUS=$(curl -sf --max-time 2 https://api.anthropic.com >/dev/null 2>&1 && echo "online" || echo "offline")

# === Line 1 出力 ===
echo "🤖 ${MODEL_SHORT} │ 📁 ${DIR_NAME}${BRANCH_SEG}  │ 🔑 ${API_KEY_STATUS}  │ 🖥 ${OS_TYPE}"

# === Line 2 出力 ===
echo "📊 ${USED_PCT}% │ ✏️  +${LINES_ADDED}/-${LINES_REMOVED} │🌐 ${NET_STATUS}"

# === ユーティリティ関数 ===

# 10段階プログレスバー (▰=使用済み ▱=残り)
make_bar() {
    local pct="${1:-0}"
    local filled=$(( pct * 10 / 100 ))
    local bar="" i=0
    while [ $i -lt $filled ]; do bar="${bar}▰"; ((i++)) || true; done
    while [ $i -lt 10 ];     do bar="${bar}▱"; ((i++)) || true; done
    echo "$bar"
}

# リセット時刻フォーマット: ISO8601 → "Resets 9pm (Asia/Tokyo)" / "Resets Mar 6 at 1pm (Asia/Tokyo)"
format_reset() {
    local reset_utc="$1"
    [ -z "$reset_utc" ] && { echo "Resets ? (Asia/Tokyo)"; return; }

    local now_day reset_day
    now_day=$(TZ=Asia/Tokyo date +"%Y-%m-%d" 2>/dev/null) || { echo "Resets ? (Asia/Tokyo)"; return; }
    reset_day=$(TZ=Asia/Tokyo date -d "$reset_utc" +"%Y-%m-%d" 2>/dev/null) || { echo "Resets ? (Asia/Tokyo)"; return; }

    local hour_str
    if [ "$now_day" = "$reset_day" ]; then
        hour_str=$(TZ=Asia/Tokyo date -d "$reset_utc" +"%-I%p" 2>/dev/null | tr '[:upper:]' '[:lower:]')
        echo "Resets ${hour_str} (Asia/Tokyo)"
    else
        local month_day
        month_day=$(TZ=Asia/Tokyo date -d "$reset_utc" +"%b %-d at %-I%p" 2>/dev/null | tr '[:upper:]' '[:lower:]')
        # 先頭文字だけ大文字: "mar 6 at 1pm" → "Mar 6 at 1pm"
        echo "Resets $(echo "${month_day:0:1}" | tr '[:lower:]' '[:upper:]')${month_day:1} (Asia/Tokyo)"
    fi
}

# === Note: Haiku API probe removed to avoid consuming API quota ===
# Rate limit info (Line 3/4) is not displayed to prevent billable calls on every statusline update.
