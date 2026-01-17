#!/bin/bash
# scripts/new-feature-maintenance.sh

echo "=== 新機能データメンテナンス ==="

# データクリーンアップ
psql -U mks_user -d mks_db << EOF
DELETE FROM new_feature_logs WHERE timestamp < NOW() - INTERVAL '90 days';
VACUUM ANALYZE new_feature_table;
EOF

# 統計情報更新
psql -U mks_user -d mks_db -c "ANALYZE new_feature_table;"

echo "=== 新機能データメンテナンス完了 ==="