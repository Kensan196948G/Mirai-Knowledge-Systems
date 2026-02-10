#!/bin/bash
# .claude/hooks/user-prompt-submit.sh
# UserPromptSubmit Hook - ユーザープロンプト送信時に実行

set -e

# プロンプト内容のセキュリティチェック（簡易版）
# 実運用では、より詳細なチェックを実装

# 環境変数確認
if [ -f ".env" ]; then
    # .envファイルが存在する場合、秘密情報の漏洩を警告
    if [ ! -z "$PROMPT_CONTENT" ]; then
        # プロンプトに.envの内容が含まれていないか簡易チェック
        # （実装は今後の拡張）
        :
    fi
fi

# ログ記録（オプション）
# LOG_FILE=".claude/logs/prompt-history.log"
# mkdir -p "$(dirname $LOG_FILE)"
# echo "[$(date '+%Y-%m-%d %H:%M:%S')] UserPromptSubmit Hook実行" >> "$LOG_FILE"

# 正常終了
exit 0
