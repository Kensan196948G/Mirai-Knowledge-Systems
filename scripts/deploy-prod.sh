#!/bin/bash
# scripts/deploy-prod.sh - 本番環境デプロイスクリプト

set -e  # エラー発生時に停止

echo "=== 本番環境デプロイ開始 ==="

# 環境変数設定
export FLASK_ENV=production
export DATABASE_URL="postgresql://mks_user:password@localhost:5432/mks_db"

# 作業ディレクトリ移動
cd /opt/mks/backend

# Gitプル（CI/CDから呼ばれる場合を想定）
echo "コード更新..."
git pull origin main

# 依存関係更新
echo "依存関係更新..."
pip install -r requirements.txt

# データベースマイグレーション
echo "データベースマイグレーション..."
alembic upgrade head

# 静的ファイル収集
echo "静的ファイル処理..."
# Collect static files if needed

# テスト実行（オプション）
echo "テスト実行..."
python -m pytest tests/ -v --tb=short || exit 1

# サービス再起動
echo "サービス再起動..."
sudo systemctl stop mks-backend
sudo systemctl start mks-backend

# ヘルスチェック
echo "ヘルスチェック..."
sleep 30
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:5100/api/v1/health > /dev/null 2>&1; then
        echo "ヘルスチェック成功"
        break
    else
        echo "ヘルスチェック失敗、再試行..."
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: ヘルスチェック失敗、デプロイ中止"
    exit 1
fi

# Nginx再読み込み
echo "Nginx再読み込み..."
sudo nginx -t && sudo systemctl reload nginx

echo "=== 本番環境デプロイ完了 ==="

# デプロイスラック通知（オプション）
# curl -X POST -H 'Content-type: application/json' \
#   --data '{"text":"Production deployment completed successfully"}' \
#   $SLACK_WEBHOOK_URL</content>
<parameter name="filePath">scripts/deploy-prod.sh