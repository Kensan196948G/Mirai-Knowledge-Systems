#!/bin/bash
# scripts/new-feature-health-check.sh

echo "=== 新機能ヘルスチェック ==="

# APIエンドポイント確認
curl -f http://localhost:5100/api/v1/new-feature/health || exit 1

# データベース接続確認
psql -U mks_user -d mks_db -c "SELECT COUNT(*) FROM new_feature_table;" > /dev/null || exit 1

# パフォーマンスチェック
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:5100/api/v1/new-feature/test)
if (( $(echo "$RESPONSE_TIME > 3.0" | bc -l) )); then
    echo "WARNING: レスポンスタイムが遅いです: ${RESPONSE_TIME}s"
    exit 1
fi

echo "=== 新機能ヘルスチェック完了 ==="