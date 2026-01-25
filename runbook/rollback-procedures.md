# 切り戻し手順 (Rollback Procedures)

## 概要
デプロイ失敗時や障害発生時の迅速なサービス復旧を目的とした切り戻し手順です。

## 切り戻し実行条件

### 自動切り戻し
- **デプロイスクリプト失敗**: CI/CDパイプラインで検知
- **ヘルスチェック失敗**: デプロイ後5分以内の異常
- **アラート閾値超過**: 監視メトリクス異常

### 手動切り戻し
- **機能障害**: デプロイ後ユーザー影響確認
- **パフォーマンス劣化**: レスポンスタイム大幅低下
- **データ不整合**: デプロイ後のデータ異常

## デプロイ失敗時の切り戻し

### 1. デプロイバージョン確認
```bash
# カレントディレクトリ確認
pwd
# /opt/mks/backend

# コミット履歴確認
git log --oneline -10

# 現在のブランチ確認
git branch --show-current

# 変更ファイル確認
git status
```

### 2. 前の安定バージョンへ戻す
```bash
# 前のコミットへ戻す（ソフトリセット）
git reset --soft HEAD~1

# または特定のコミットへ
git reset --soft <stable-commit-hash>

# 変更をコミット
git add .
git commit -m "Rollback: Revert to stable version"
```

### 3. サービス再起動
```bash
# Gunicorn再起動
sudo systemctl restart mks-backend

# Nginx再読み込み（設定変更時）
sudo systemctl reload nginx
```

### 4. ヘルスチェック
```bash
# 基本ヘルスチェック
curl -f http://localhost:5100/api/v1/health

# API機能確認
curl -X GET http://localhost:5100/api/v1/projects | head -5

# データベース接続確認
psql -U mks_user -d mks_db -c "SELECT COUNT(*) FROM projects;"
```

## データベースマイグレーション失敗時

### 1. マイグレーション履歴確認
```bash
# Alembic履歴確認
cd /opt/mks/backend
alembic history

# 現在のリビジョン確認
alembic current
```

### 2. マイグレーションをロールバック
```bash
# 直前のマイグレーションをロールバック
alembic downgrade -1

# または特定のバージョンへ
alembic downgrade <revision-id>
```

### 3. データベース状態確認
```bash
# テーブル構造確認
psql -U mks_user -d mks_db -c "\dt"

# データ整合性確認
psql -U mks_user -d mks_db -c "SELECT COUNT(*) FROM projects;"

# 外部キー制約確認
psql -U mks_user -d mks_db -c "\d projects"
```

### 4. マイグレーション再実行（修正後）
```bash
# 修正したマイグレーションを再実行
alembic upgrade head
```

## GitHub Actions 失敗時

### 1. ログ確認
```bash
# GitHub CLIでログ確認
gh run view <run-id> --log

# またはWeb UIで確認
# https://github.com/owner/repo/actions/runs/<run-id>
```

### 2. ローカルで再現
```bash
# 最新コード取得
git pull origin main

# テスト実行
python -m pytest tests/ -v

# リンター実行
flake8 backend/
black --check backend/
```

### 3. 修正してプッシュ
```bash
# 修正
vim backend/app.py  # 例

# コミット
git add .
git commit -m "Fix CI failure: [description]"

# プッシュ
git push origin main
```

### 4. CI で再実行
```bash
# 手動再実行
gh run rerun <run-id>

# またはWeb UIから
```

## 設定変更時の切り戻し

### Nginx設定変更
```bash
# バックアップから復元
sudo cp /etc/nginx/sites-available/mks.backup /etc/nginx/sites-available/mks

# 設定テスト
sudo nginx -t

# リロード
sudo systemctl reload nginx
```

### systemd設定変更
```bash
# バックアップから復元
sudo cp /etc/systemd/system/mks-backend.service.backup /etc/systemd/system/mks-backend.service

# 設定リロード
sudo systemctl daemon-reload

# サービス再起動
sudo systemctl restart mks-backend
```

## バックアップからのリストア

### 1. バックアップ確認
```bash
# バックアップファイル確認
ls -la /backup/mks/
# db_20240109_020000.dump
# uploads_20240109_020000.tar.gz

# バックアップ整合性確認
pg_restore --list /backup/mks/db_20240109_020000.dump | head -10
```

### 2. リストア実行
```bash
# データベースリストア
pg_restore -U mks_user -d mks_db --clean --if-exists /backup/mks/db_20240109_020000.dump

# アップロードファイルリストア
cd /opt/mks
tar -xzf /backup/mks/uploads_20240109_020000.tar.gz
```

### 3. サービス再起動
```bash
sudo systemctl restart mks-backend
sudo systemctl restart nginx
```

## 切り戻し後の確認

### 機能テスト
```bash
# ログインAPIテスト
curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# プロジェクト一覧取得
curl -X GET http://localhost:5100/api/v1/projects \
  -H "Authorization: Bearer <token>"
```

### パフォーマンス確認
```bash
# レスポンスタイム測定
time curl -s http://localhost:5100/api/v1/health > /dev/null

# メモリ使用量確認
ps aux | grep gunicorn | grep -v grep
```

### ログ確認
```bash
# エラーログ確認
tail -f /var/log/mks-backend/error.log

# アクセスログ確認
tail -f /var/log/nginx/access.log
```

## 自動化スクリプト

### ロールバックスクリプト
```bash
#!/bin/bash
# scripts/rollback.sh

echo "=== ロールバック開始 ==="

# バージョン確認
echo "現在のコミット:"
git log --oneline -3

# ロールバック実行
git reset --soft HEAD~1

# サービス再起動
sudo systemctl restart mks-backend

# ヘルスチェック
sleep 10
curl -f http://localhost:5100/api/v1/health

echo "=== ロールバック完了 ==="
```

### 自動切り戻し設定
```yaml
# .github/workflows/deploy.yml
- name: Health Check
  run: |
    curl -f http://localhost:5100/api/v1/health || exit 1

- name: Rollback on Failure
  if: failure()
  run: |
    bash scripts/rollback.sh
```

## 事後作業

### 1. 原因調査
- デプロイログ分析
- コードレビュー
- 設定確認

### 2. 修正プラン作成
- バグ修正
- テスト追加
- プロセス改善

### 3. 再デプロイ計画
- 修正完了確認
- テスト実行
- デプロイスケジュール

### 4. ドキュメント更新
- Runbook更新
- 変更履歴記録
- チーム共有

## 定期メンテナンス

### 毎週
- [ ] バックアップファイル確認
- [ ] ロールバックスクリプトテスト
- [ ] 復旧時間測定

### 毎月
- [ ] フルリストアテスト
- [ ] 切り戻し訓練
- [ ] ドキュメント更新</content>
<parameter name="filePath">runbook/rollback-procedures.md