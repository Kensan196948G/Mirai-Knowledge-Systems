#!/usr/bin/env bash
# ==============================================================================
# Claude Code CI Repairer (PowerShell専門)
# ==============================================================================
# 役割: CI修理工（PowerShellビルドエラー自動修復）
# 制約: .ps1ファイルのみ修正、差分最小化、設計変更禁止
# ==============================================================================

set -e

echo "=== Claude Code CI Repairer (PowerShell) ==="
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ビルドログの存在確認
if [ ! -f "build.log" ]; then
    echo "[ERROR] build.log が見つかりません"
    exit 1
fi

# ログサイズ確認（大きすぎる場合は末尾のみ使用）
LOG_SIZE=$(wc -l < build.log)
if [ "$LOG_SIZE" -gt 200 ]; then
    echo "[INFO] ログが大きいため末尾200行を使用"
    BUILD_LOG=$(tail -200 build.log)
else
    BUILD_LOG=$(cat build.log)
fi

# Claude Code 呼び出し
claude << EOF
You are a CI repair agent specialized in PowerShell.

Here is a failed build log:
---
${BUILD_LOG}
---

## Rules (STRICT - DO NOT VIOLATE):
- Only modify .ps1 files
- Do not modify any other file types unless explicitly instructed
- Keep diffs minimal (prefer 1-5 lines)
- Do not refactor unrelated logic
- Do not change architecture or design
- Do not introduce new dependencies
- If the failure is in CI scripts or YAML, report it but do not fix it
- Do not add comments explaining your changes

## Task:
Fix the root cause so that pwsh ./build.ps1 passes.
Apply only the minimal change required.
Do not output explanations - just make the fix.
EOF

echo ""
echo "=== Claude Code 修復完了 ==="
