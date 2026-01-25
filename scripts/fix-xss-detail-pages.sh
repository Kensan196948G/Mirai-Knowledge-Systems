#!/bin/bash

# ============================================================
# detail-pages.js XSS脆弱性修正スクリプト
#
# このスクリプトは手動修正の補助として使用されます
# ============================================================

echo "XSS脆弱性修正のための分析を開始します..."
echo ""

FILE="/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/detail-pages.js"
BACKUP="/mnt/LinuxHDD/Mirai-Knowledge-Systems/webui/detail-pages.js.xss-backup"

# バックアップを作成
echo "[1] バックアップを作成中..."
cp "$FILE" "$BACKUP"
echo "✓ バックアップ作成完了: $BACKUP"
echo ""

# innerHTML使用箇所を分析
echo "[2] innerHTML使用箇所の分析..."
echo "全innerHTML使用箇所: $(grep -c 'innerHTML' "$FILE")箇所"
echo "変数展開を含むinnerHTML: $(grep -c 'innerHTML.*\${' "$FILE")箇所"
echo ""

# 危険な箇所をリストアップ
echo "[3] XSS脆弱性の危険度が高い箇所:"
echo ""
grep -n 'innerHTML.*\${' "$FILE" | head -20
echo ""

echo "修正が必要な主要パターン:"
echo "  - タグ表示: tagsEl.innerHTML = data.tags.map(tag => ...)"
echo "  - コメント表示: commentListEl.innerHTML = comments.map(comment => ...)"
echo "  - コンテンツ表示: contentEl.innerHTML = data.content"
echo "  - テーブル生成: tableEl.innerHTML = items.map(item => ...)"
echo ""

echo "推奨修正方法:"
echo "  1. textContent を使用 (テキストのみの場合)"
echo "  2. createElement + appendChild を使用 (複雑な構造の場合)"
echo "  3. セキュアなヘルパー関数を使用 (dom-helpers.js)"
echo ""

echo "✓ 分析完了"
echo "手動での修正が必要です。"
