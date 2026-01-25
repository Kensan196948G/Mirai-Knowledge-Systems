#!/usr/bin/env bash
# ==============================================================================
# 証跡ログ保存スクリプト（ITSM準拠）
# ==============================================================================
# 機能:
#   - ビルドログの保存
#   - 差分パッチの保存
#   - 実行サマリーの保存
# ==============================================================================

set -e

echo "=== 証跡ログ保存 ==="
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 保存先ディレクトリ
EVIDENCE_DIR="ci_logs"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# ディレクトリ作成
mkdir -p "$EVIDENCE_DIR"

# ==============================================================================
# 1. ビルドログ保存
# ==============================================================================
echo "[SAVE 1/3] ビルドログ保存..."

if [ -f "build.log" ]; then
    BUILD_LOG_FILE="${EVIDENCE_DIR}/build_${TIMESTAMP}.log"
    cp build.log "$BUILD_LOG_FILE"
    echo "  保存先: ${BUILD_LOG_FILE}"
else
    echo "  [SKIP] build.log が見つかりません"
fi

# ==============================================================================
# 2. 差分パッチ保存
# ==============================================================================
echo "[SAVE 2/3] 差分パッチ保存..."

DIFF_OUTPUT=$(git diff 2>/dev/null || echo "")

if [ -n "$DIFF_OUTPUT" ]; then
    DIFF_FILE="${EVIDENCE_DIR}/diff_${TIMESTAMP}.patch"
    echo "$DIFF_OUTPUT" > "$DIFF_FILE"
    echo "  保存先: ${DIFF_FILE}"

    # 差分統計
    DIFF_STATS=$(git diff --stat 2>/dev/null | tail -1 || echo "統計なし")
    echo "  統計: ${DIFF_STATS}"
else
    echo "  [SKIP] 差分なし"
fi

# ==============================================================================
# 3. 実行サマリー保存
# ==============================================================================
echo "[SAVE 3/3] 実行サマリー保存..."

SUMMARY_FILE="${EVIDENCE_DIR}/summary_${TIMESTAMP}.md"

cat > "$SUMMARY_FILE" << EOF
# CI自動修復 実行サマリー

**実行日時**: $(date '+%Y-%m-%d %H:%M:%S')
**コミット**: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
**ブランチ**: $(git branch --show-current 2>/dev/null || echo "N/A")

## 試行情報

- 試行回数: $(cat .ci_attempt 2>/dev/null || echo "1")
- エラーハッシュ: $(cat .ci_error_hash 2>/dev/null | head -c 12 || echo "N/A")

## 変更ファイル

\`\`\`
$(git diff --name-only 2>/dev/null || echo "変更なし")
\`\`\`

## 差分統計

\`\`\`
$(git diff --stat 2>/dev/null || echo "統計なし")
\`\`\`

## 関連ファイル

- ビルドログ: build_${TIMESTAMP}.log
- 差分パッチ: diff_${TIMESTAMP}.patch
EOF

echo "  保存先: ${SUMMARY_FILE}"

# ==============================================================================
# 結果
# ==============================================================================
echo ""
echo "=== 証跡ログ保存完了 ==="
echo "  保存先ディレクトリ: ${EVIDENCE_DIR}/"
echo "  タイムスタンプ: ${TIMESTAMP}"

# 古いログのクリーンアップ（30日以上前）
find "$EVIDENCE_DIR" -type f -mtime +30 -delete 2>/dev/null || true
echo "  [INFO] 30日以上前のログをクリーンアップしました"
