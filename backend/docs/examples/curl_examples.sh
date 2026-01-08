#!/bin/bash

# Mirai Knowledge System API - cURL使用例
#
# このシェルスクリプトは、cURLを使用したMKS APIの基本的な使用方法を示します。
#
# 使用方法:
#   1. このファイルを実行可能にする: chmod +x curl_examples.sh
#   2. 実行: ./curl_examples.sh
#

# APIのベースURL
BASE_URL="http://localhost:5100"

# カラー出力用
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ヘッダー出力
print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

# ============================================================
# 1. ログイン
# ============================================================

print_header "1. ログイン"

LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

echo "$LOGIN_RESPONSE" | jq .

# アクセストークンを抽出
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.access_token')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.refresh_token')

echo ""
echo -e "${YELLOW}Access Token: ${ACCESS_TOKEN:0:50}...${NC}"
echo ""

# ============================================================
# 2. 現在のユーザー情報取得
# ============================================================

print_header "2. 現在のユーザー情報取得"

curl -s -X GET "${BASE_URL}/api/v1/auth/me" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq .

echo ""

# ============================================================
# 3. ナレッジ一覧取得
# ============================================================

print_header "3. ナレッジ一覧取得"

curl -s -X GET "${BASE_URL}/api/v1/knowledge" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq '.data | length'

echo " 件のナレッジがあります"
echo ""

# ============================================================
# 4. カテゴリでフィルタ
# ============================================================

print_header "4. 品質管理カテゴリのナレッジ取得"

curl -s -X GET "${BASE_URL}/api/v1/knowledge?category=品質管理" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq '.data[] | {id, title, category}'

echo ""

# ============================================================
# 5. キーワード検索
# ============================================================

print_header "5. キーワード検索（コンクリート）"

curl -s -X GET "${BASE_URL}/api/v1/knowledge?search=コンクリート" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq '.data[] | {id, title}'

echo ""

# ============================================================
# 6. 新規ナレッジ作成
# ============================================================

print_header "6. 新規ナレッジ作成"

CREATE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/knowledge" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "鉄筋配筋検査のチェックポイント",
    "summary": "配筋検査における重要確認項目",
    "content": "## 配筋検査の目的\n- 設計図書との整合性確認\n- 施工精度の確認\n\n## 主要チェック項目\n1. 鉄筋径・鉄筋種別の確認\n2. 配筋間隔の確認\n3. かぶり厚さの確認",
    "category": "品質管理",
    "tags": ["鉄筋工事", "配筋検査", "品質管理"],
    "priority": "high",
    "owner": "山田太郎",
    "project": "東京タワー建設プロジェクト"
  }')

echo "$CREATE_RESPONSE" | jq .

NEW_KNOWLEDGE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.data.id')
echo ""
echo -e "${YELLOW}作成されたナレッジID: ${NEW_KNOWLEDGE_ID}${NC}"
echo ""

# ============================================================
# 7. ナレッジ詳細取得
# ============================================================

print_header "7. ナレッジ詳細取得（ID: ${NEW_KNOWLEDGE_ID}）"

curl -s -X GET "${BASE_URL}/api/v1/knowledge/${NEW_KNOWLEDGE_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq .

echo ""

# ============================================================
# 8. 横断検索
# ============================================================

print_header "8. 横断検索（基礎工事）"

curl -s -X GET "${BASE_URL}/api/v1/search/unified?q=基礎工事&types=knowledge,sop&highlight=true" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq '{query, total_results, data: .data | to_entries | map({type: .key, count: .value.count})}'

echo ""

# ============================================================
# 9. 通知一覧取得
# ============================================================

print_header "9. 通知一覧取得"

NOTIFICATIONS=$(curl -s -X GET "${BASE_URL}/api/v1/notifications" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

echo "$NOTIFICATIONS" | jq '{total: .pagination.total_items, unread: .pagination.unread_count, notifications: .data[:3] | map({id, title, type, is_read})}'

echo ""

# ============================================================
# 10. 未読通知数取得
# ============================================================

print_header "10. 未読通知数取得"

curl -s -X GET "${BASE_URL}/api/v1/notifications/unread/count" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq .

echo ""

# ============================================================
# 11. 通知を既読にする
# ============================================================

# 最初の未読通知を取得
FIRST_UNREAD_ID=$(echo "$NOTIFICATIONS" | jq -r '.data[] | select(.is_read == false) | .id' | head -1)

if [ -n "$FIRST_UNREAD_ID" ] && [ "$FIRST_UNREAD_ID" != "null" ]; then
    print_header "11. 通知を既読にする（ID: ${FIRST_UNREAD_ID}）"

    curl -s -X PUT "${BASE_URL}/api/v1/notifications/${FIRST_UNREAD_ID}/read" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq .

    echo ""
fi

# ============================================================
# 12. ダッシュボード統計取得
# ============================================================

print_header "12. ダッシュボード統計取得"

curl -s -X GET "${BASE_URL}/api/v1/dashboard/stats" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq .

echo ""

# ============================================================
# 13. SOP一覧取得
# ============================================================

print_header "13. SOP一覧取得"

curl -s -X GET "${BASE_URL}/api/v1/sop" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq '.data[:3] | map({id, title, version, category})'

echo ""

# ============================================================
# 14. トークンリフレッシュ
# ============================================================

print_header "14. トークンリフレッシュ"

REFRESH_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/refresh" \
  -H "Authorization: Bearer ${REFRESH_TOKEN}")

echo "$REFRESH_RESPONSE" | jq .

NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.data.access_token')
echo ""
echo -e "${YELLOW}新しいAccess Token: ${NEW_ACCESS_TOKEN:0:50}...${NC}"
echo ""

# ============================================================
# 15. メトリクス取得
# ============================================================

print_header "15. メトリクスサマリー取得"

curl -s -X GET "${BASE_URL}/api/metrics/summary" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq .

echo ""

# ============================================================
# エラーハンドリング例
# ============================================================

print_header "16. エラーハンドリング例"

echo "16-1. 無効なトークン"
curl -s -X GET "${BASE_URL}/api/v1/knowledge" \
  -H "Authorization: Bearer invalid_token" | jq .

echo ""

echo "16-2. 存在しないリソース"
curl -s -X GET "${BASE_URL}/api/v1/knowledge/999999" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq .

echo ""

echo "16-3. バリデーションエラー"
curl -s -X POST "${BASE_URL}/api/v1/knowledge" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "",
    "summary": "テスト",
    "category": "無効なカテゴリ"
  }' | jq .

echo ""

print_header "完了"
echo -e "${GREEN}すべてのAPI呼び出しが完了しました！${NC}"
echo ""
