#!/usr/bin/env bash
# ==============================================================================
# 暴走防止ガードスクリプト
# ==============================================================================
# 機能:
#   1. 無限ループ防止（最大試行回数制限）
#   2. 同一エラー繰り返し検出
#   3. 差分量ガード（20行超でabort）
#   4. 対象ファイルガード（.ps1以外禁止）
# ==============================================================================

set -e

echo "=== 暴走防止ガードチェック ==="
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 設定値
MAX_ATTEMPTS=5
ATTEMPT_FILE=".ci_attempt"
ERROR_HASH_FILE=".ci_error_hash"
MAX_DIFF_LINES=20

# ==============================================================================
# 1. 無限ループ防止（試行回数チェック）
# ==============================================================================
echo "[GUARD 1/4] 試行回数チェック..."

ATTEMPT=$(cat "$ATTEMPT_FILE" 2>/dev/null || echo 0)
ATTEMPT=$((ATTEMPT + 1))
echo "$ATTEMPT" > "$ATTEMPT_FILE"

echo "  現在の試行回数: ${ATTEMPT}/${MAX_ATTEMPTS}"

if [ "$ATTEMPT" -gt "$MAX_ATTEMPTS" ]; then
    echo "[ABORT] 最大試行回数(${MAX_ATTEMPTS})に達しました"
    echo "        手動介入が必要です"
    exit 1
fi

# ==============================================================================
# 2. 同一エラー繰り返し検出
# ==============================================================================
echo "[GUARD 2/4] 同一エラー繰り返しチェック..."

if [ -f "build.log" ]; then
    HASH=$(sha1sum build.log 2>/dev/null | awk '{print $1}' || shasum build.log | awk '{print $1}')

    if [ -f "$ERROR_HASH_FILE" ]; then
        LAST_HASH=$(cat "$ERROR_HASH_FILE")
        if [ "$HASH" = "$LAST_HASH" ]; then
            echo "[ABORT] 同一エラーが繰り返し発生しています"
            echo "        Claude Codeによる自動修復が効果なし"
            echo "        手動介入が必要です"
            exit 1
        fi
    fi

    echo "$HASH" > "$ERROR_HASH_FILE"
    echo "  エラーハッシュ: ${HASH:0:12}..."
else
    echo "  [SKIP] build.log が見つかりません"
fi

# ==============================================================================
# 3. 差分量ガード
# ==============================================================================
echo "[GUARD 3/4] 差分量チェック..."

DIFF_LINES=$(git diff --stat 2>/dev/null | tail -1 | grep -oE '[0-9]+' | head -1 || echo 0)

if [ -z "$DIFF_LINES" ]; then
    DIFF_LINES=0
fi

echo "  変更行数: ${DIFF_LINES}行"

if [ "$DIFF_LINES" -gt "$MAX_DIFF_LINES" ]; then
    echo "[ABORT] 差分が大きすぎます（${DIFF_LINES}行 > ${MAX_DIFF_LINES}行）"
    echo "        大規模な変更は手動レビューが必要です"
    echo ""
    echo "=== 差分詳細 ==="
    git diff --stat
    exit 1
fi

# ==============================================================================
# 4. 対象ファイルガード（.ps1以外禁止）
# ==============================================================================
echo "[GUARD 4/4] 対象ファイルチェック..."

CHANGED_FILES=$(git diff --name-only 2>/dev/null || echo "")

if [ -n "$CHANGED_FILES" ]; then
    FORBIDDEN_FILES=""

    while IFS= read -r f; do
        # .ps1 ファイルまたは ci/ ディレクトリ内は許可
        if [[ ! "$f" =~ \.ps1$ ]] && [[ ! "$f" =~ ^ci/ ]]; then
            FORBIDDEN_FILES="${FORBIDDEN_FILES}${f}\n"
        fi
    done <<< "$CHANGED_FILES"

    if [ -n "$FORBIDDEN_FILES" ]; then
        echo "[ABORT] 許可されていないファイルが変更されています:"
        echo -e "$FORBIDDEN_FILES"
        echo ""
        echo "許可対象: .ps1 ファイル、ci/ ディレクトリ内"
        exit 1
    fi

    echo "  変更ファイル:"
    echo "$CHANGED_FILES" | while read -r f; do
        echo "    - $f"
    done
else
    echo "  [INFO] 変更ファイルなし"
fi

# ==============================================================================
# 結果
# ==============================================================================
echo ""
echo "=== 全ガードチェック通過 ==="
echo "  試行回数: ${ATTEMPT}/${MAX_ATTEMPTS}"
echo "  差分行数: ${DIFF_LINES}行"
echo "  ステータス: PASS"
