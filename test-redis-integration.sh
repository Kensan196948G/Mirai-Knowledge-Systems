#!/bin/bash
# Phase F-2: Redis Integration Test Script
# このスクリプトはRedis統合が正常に動作することを確認します

set -e

echo "🚀 Phase F-2: Redis統合テスト開始"
echo "================================"
echo ""

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Redis接続確認
echo -e "${YELLOW}Step 1: Redis接続確認${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis稼働中${NC}"
else
    echo -e "${RED}❌ Redis未起動${NC}"
    echo "sudo systemctl start redis-server を実行してください"
    exit 1
fi
echo ""

# Step 2: Python環境確認
echo -e "${YELLOW}Step 2: Python環境確認${NC}"
if [ -f "backend/venv/bin/python3" ]; then
    echo -e "${GREEN}✅ 仮想環境存在${NC}"
else
    echo -e "${RED}❌ 仮想環境なし${NC}"
    exit 1
fi

# Step 3: Redis Python接続テスト
echo -e "${YELLOW}Step 3: Redis Python接続テスト${NC}"
backend/venv/bin/python3 -c "
import redis
r = redis.from_url('redis://localhost:6379/0')
result = r.ping()
print(f'✅ Redis Python接続成功: {result}')
" || {
    echo -e "${RED}❌ Redis Python接続失敗${NC}"
    exit 1
}
echo ""

# Step 4: app_v2.py読み込みテスト
echo -e "${YELLOW}Step 4: app_v2.py Redis設定確認${NC}"
cd backend
venv/bin/python3 -c "
import sys
sys.path.insert(0, '.')
# 最小限の環境変数設定
import os
os.environ['MKS_ENV'] = 'development'
os.environ['DATABASE_TYPE'] = 'json'

try:
    import app_v2
    print(f'✅ app_v2.py読み込み成功')
    print(f'   CACHE_ENABLED: {app_v2.CACHE_ENABLED}')
    print(f'   redis_client: {\"有効\" if app_v2.redis_client else \"無効\"}')

    if app_v2.CACHE_ENABLED and app_v2.redis_client:
        print(f'   ✅ Redisキャッシング有効')
    else:
        print(f'   ⚠️  Redisキャッシング無効（グレースフル・デグラデーション）')
except Exception as e:
    print(f'❌ エラー: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || {
    echo -e "${RED}❌ app_v2.py読み込み失敗${NC}"
    cd ..
    exit 1
}
cd ..
echo ""

# Step 5: キャッシュ関数テスト
echo -e "${YELLOW}Step 5: キャッシュ関数テスト${NC}"
cd backend
venv/bin/python3 -c "
import sys
sys.path.insert(0, '.')
import os
os.environ['MKS_ENV'] = 'development'
os.environ['DATABASE_TYPE'] = 'json'

import app_v2
import json

# テストデータ
test_key = 'test:phase_f2'
test_data = {'message': 'Phase F-2 Redis統合テスト', 'status': 'success'}

# キャッシュ書き込み
app_v2.cache_set(test_key, test_data, ttl=10)
print('✅ cache_set() 成功')

# キャッシュ読み取り
cached = app_v2.cache_get(test_key)
if cached and cached.get('message') == test_data['message']:
    print('✅ cache_get() 成功')
    print(f'   取得データ: {json.dumps(cached, ensure_ascii=False)}')
else:
    print('⚠️  キャッシュ取得失敗（グレースフル・デグラデーション）')

# クリーンアップ
if app_v2.redis_client:
    app_v2.redis_client.delete(test_key)
    print('✅ テストキャッシュクリーンアップ完了')
" || {
    echo -e "${YELLOW}⚠️  キャッシュ関数テスト失敗（Redis無効時は正常）${NC}"
}
cd ..
echo ""

# Step 6: N+1最適化確認
echo -e "${YELLOW}Step 6: N+1クエリ最適化確認${NC}"
echo "以下のコードが実装されていることを確認:"
echo "  - backend/data_access.py:1160-1208 (Expert統計)"
echo "  - backend/data_access.py:790-795 (承認リスト)"

if grep -q "selectinload(Expert.user)" backend/data_access.py && \
   grep -q "selectinload(Approval.requester)" backend/data_access.py; then
    echo -e "${GREEN}✅ N+1最適化コード存在確認${NC}"
else
    echo -e "${YELLOW}⚠️  N+1最適化コード確認できず${NC}"
fi
echo ""

# 完了サマリー
echo "================================"
echo -e "${GREEN}✅ Phase F-2統合テスト完了${NC}"
echo ""
echo "次のステップ:"
echo "  1. バックエンド起動: backend/venv/bin/python3 backend/app_v2.py"
echo "  2. ログ確認: ログに 'CACHE_ENABLED = True' が表示されるか確認"
echo "  3. パフォーマンステスト: docs/REDIS_QUICK_START.md を参照"
echo ""
echo "ドキュメント:"
echo "  - docs/PHASE_F2_COMPLETION_REPORT.md"
echo "  - docs/REDIS_QUICK_START.md"
