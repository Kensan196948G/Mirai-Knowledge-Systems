#!/bin/bash
# .claude/hooks/session-start.sh
# SessionStart Hook - プロジェクト初期化時に実行

set -e

echo "🚀 Mirai Knowledge Systems セッション開始"
echo "プロジェクト: $(basename $(pwd))"
echo "日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# プロジェクト状態確認
echo "📋 プロジェクト状態チェック:"

# バックエンド確認
if [ -f "backend/app_v2.py" ]; then
    echo "  ✅ バックエンド: 正常 (app_v2.py)"
    LINE_COUNT=$(wc -l < backend/app_v2.py)
    echo "     - app_v2.py: ${LINE_COUNT}行"
else
    echo "  ⚠️  バックエンド: app_v2.py が見つかりません"
fi

# フロントエンド確認
if [ -f "webui/app.js" ]; then
    echo "  ✅ フロントエンド: 正常 (app.js)"
else
    echo "  ⚠️  フロントエンド: app.js が見つかりません"
fi

# データディレクトリ確認
if [ -d "backend/data" ]; then
    echo "  ✅ データディレクトリ: 存在"
else
    echo "  ⚠️  データディレクトリ: 未作成"
fi

echo ""

# Git状態確認
if [ -d ".git" ]; then
    BRANCH=$(git branch --show-current)
    echo "📍 Gitブランチ: $BRANCH"

    # 最新コミット
    LATEST_COMMIT=$(git log -1 --oneline)
    echo "   最新コミット: $LATEST_COMMIT"

    # 変更状態
    if git diff-index --quiet HEAD --; then
        echo "   ✅ 変更なし（クリーン）"
    else
        echo "   ⚠️  未コミットの変更あり"
        git status --short | head -5
    fi
else
    echo "⚠️  Gitリポジトリではありません"
fi

echo ""

# サービス状態確認（Linux環境のみ）
if command -v systemctl &> /dev/null; then
    echo "🔧 サービス状態:"

    # 開発環境サービス
    if systemctl is-active --quiet mirai-knowledge-app-dev 2>/dev/null; then
        echo "  ✅ 開発サービス: 稼働中"
    else
        echo "  ⚠️  開発サービス: 停止中"
    fi

    # 本番環境サービス
    if systemctl is-active --quiet mirai-knowledge-app 2>/dev/null; then
        echo "  ✅ 本番サービス: 稼働中"
    else
        echo "  ⚠️  本番サービス: 停止中"
    fi

    # MS365同期デーモン
    if systemctl is-active --quiet mirai-ms365-sync 2>/dev/null; then
        echo "  ✅ MS365同期: 稼働中"
    else
        echo "  ⚠️  MS365同期: 停止中"
    fi
else
    echo "ℹ️  systemctlが利用できません（Windows環境の可能性）"
fi

echo ""
echo "✨ セッション初期化完了！"
