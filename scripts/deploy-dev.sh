#!/bin/bash
# scripts/deploy-dev.sh - 開発環境デプロイスクリプト

set -e  # エラー発生時に停止

echo "=== 開発環境デプロイ開始 ==="

# 環境変数設定
export FLASK_ENV=development
export DATABASE_URL="sqlite:///dev.db"

# 作業ディレクトリ移動
cd /opt/mks/backend

# 依存関係更新
echo "依存関係更新..."
pip install -r requirements.txt

# データベースマイグレーション
echo "データベースマイグレーション..."
alembic upgrade head

# 静的ファイル収集（必要な場合）
echo "静的ファイル処理..."
# flask collect static files if needed

# サービス再起動
echo "サービス再起動..."
sudo systemctl restart mks-backend-dev

# ヘルスチェック
echo "ヘルスチェック..."
sleep 10
curl -f http://localhost:5100/api/v1/health || exit 1

echo "=== 開発環境デプロイ完了 ==="

# ログ出力
echo "デプロイログ:"
tail -20 /var/log/mks-backend/dev.log</content>
<parameter name="filePath">scripts/deploy-dev.sh