#!/bin/bash
# scripts/health-check.sh - ヘルスチェックスクリプト

echo "=== ヘルスチェック ==="

# サービスステータス確認
echo "サービスステータス:"
systemctl status mks-backend --no-pager -l | head -10

# ポート確認
echo ""
echo "ポート確認:"
netstat -tlnp | grep 5100 || echo "ポート5100が使用されていません"

# APIエンドポイント確認
echo ""
echo "APIヘルスチェック:"
if curl -f -s http://localhost:5100/api/v1/health > /dev/null; then
    echo "✅ APIヘルスチェック成功"
else
    echo "❌ APIヘルスチェック失敗"
    exit 1
fi

# データベース接続確認
echo ""
echo "データベース接続確認:"
if [ -n "$USE_POSTGRESQL" ] && [ "$USE_POSTGRESQL" = "true" ]; then
    if psql -U mks_user -d mks_db -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✅ PostgreSQL接続成功"
    else
        echo "❌ PostgreSQL接続失敗"
        exit 1
    fi
else
    if [ -f "/opt/mks/backend/dev.db" ]; then
        echo "✅ SQLiteファイル存在確認"
    else
        echo "❌ SQLiteファイルが見つかりません"
        exit 1
    fi
fi

# ディスク容量確認
echo ""
echo "ディスク容量確認:"
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "❌ ディスク使用率が高すぎます: ${DISK_USAGE}%"
    exit 1
else
    echo "✅ ディスク使用率: ${DISK_USAGE}%"
fi

# メモリ確認
echo ""
echo "メモリ確認:"
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "❌ メモリ使用率が高すぎます: ${MEM_USAGE}%"
    exit 1
else
    echo "✅ メモリ使用率: ${MEM_USAGE}%"
fi

# プロセス確認
echo ""
echo "プロセス確認:"
GUNICORN_PROCESSES=$(ps aux | grep gunicorn | grep -v grep | wc -l)
if [ $GUNICORN_PROCESSES -gt 0 ]; then
    echo "✅ Gunicornプロセス実行中: ${GUNICORN_PROCESSES}プロセス"
else
    echo "❌ Gunicornプロセスが見つかりません"
    exit 1
fi

echo ""
echo "=== ヘルスチェック完了 ==="</content>
<parameter name="filePath">scripts/health-check.sh