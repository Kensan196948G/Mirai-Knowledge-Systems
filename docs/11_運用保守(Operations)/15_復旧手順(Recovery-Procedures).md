# 復旧手順 (Recovery Procedures)

## 概要
システム障害からの復旧手順とデータ復旧手順を定義します。迅速かつ安全な復旧を目的とします。

## 復旧レベル定義

| レベル | 説明 | 復旧時間目標 | データ損失許容 |
|--------|------|-------------|---------------|
| RTO-1 | 1時間以内の復旧 | 1時間以内 | 最小限 |
| RTO-4 | 4時間以内の復旧 | 4時間以内 | 1時間分 |
| RTO-24 | 24時間以内の復旧 | 24時間以内 | 1日分 |

## サービス復旧手順

### 1. バックエンドサービス復旧
**対象**: Flask + Gunicorn サービス

#### 自動復旧
```bash
# systemdによる自動再起動確認
systemctl status mks-backend

# ログ確認
journalctl -u mks-backend --since "1 hour ago" --no-pager | tail -20
```

#### 手動復旧
```bash
# サービス停止
sudo systemctl stop mks-backend

# プロセス確認（残っている場合）
ps aux | grep gunicorn
kill -9 <PID>  # 強制終了が必要な場合

# サービス起動
sudo systemctl start mks-backend

# 起動確認
systemctl status mks-backend
curl -f http://localhost:5100/api/v1/health
```

#### 設定確認
```bash
# 設定ファイル確認
cat /etc/systemd/system/mks-backend.service

# 環境変数確認
cat /etc/mks/config.yml

# ポート確認
netstat -tlnp | grep 5100
```

### 2. データベース復旧
**対象**: PostgreSQL データベース

#### 接続確認
```bash
# PostgreSQLサービス確認
systemctl status postgresql

# データベース接続テスト
psql -U mks_user -d mks_db -c "SELECT 1;"

# アクティブ接続確認
psql -U mks_user -d mks_db -c "SELECT count(*) FROM pg_stat_activity;"
```

#### 再起動手順
```bash
# PostgreSQL再起動
sudo systemctl restart postgresql

# ログ確認
tail -f /var/log/postgresql/postgresql-13-main.log

# 接続テスト
psql -U postgres -c "SELECT version();"
```

#### 設定確認
```bash
# PostgreSQL設定確認
cat /etc/postgresql/13/main/postgresql.conf | grep -E "(listen|port|max_connections)"

# ユーザー権限確認
psql -U postgres -c "SELECT usename, usecreatedb, usesuper FROM pg_user WHERE usename = 'mks_user';"
```

### 3. Webサーバー復旧
**対象**: Nginx リバースプロキシ

#### 設定確認
```bash
# Nginx設定テスト
sudo nginx -t

# 設定ファイル確認
cat /etc/nginx/sites-available/mks
```

#### 再起動手順
```bash
# Nginx再読み込み
sudo systemctl reload nginx

# または完全再起動
sudo systemctl restart nginx

# ステータス確認
systemctl status nginx
```

#### SSL証明書確認
```bash
# 証明書期限確認
openssl x509 -in /etc/letsencrypt/live/example.com/cert.pem -text | grep "Not After"

# 証明書更新（期限が近い場合）
certbot renew --quiet
sudo systemctl reload nginx
```

## データ復旧手順

### 1. データベースバックアップからの復旧

#### 最新バックアップ確認
```bash
# バックアップファイル一覧
ls -la /backup/mks/db_*.dump

# 最新バックアップ選択
LATEST_BACKUP=$(ls -t /backup/mks/db_*.dump | head -1)
echo "Using backup: $LATEST_BACKUP"
```

#### リストア実行
```bash
# データベース停止
sudo systemctl stop mks-backend

# 既存データバックアップ（念のため）
pg_dump -U mks_user -d mks_db > /tmp/mks_pre_restore.dump

# データベース削除・再作成
psql -U postgres -c "DROP DATABASE IF EXISTS mks_db;"
psql -U postgres -c "CREATE DATABASE mks_db OWNER mks_user;"

# リストア実行
pg_restore -U mks_user -d mks_db --clean --if-exists $LATEST_BACKUP

# 権限再設定
psql -U postgres -d mks_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mks_user;"
psql -U postgres -d mks_db -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mks_user;"
```

#### リストア確認
```bash
# データ確認
psql -U mks_user -d mks_db -c "SELECT COUNT(*) FROM projects;"
psql -U mks_user -d mks_db -c "SELECT COUNT(*) FROM users;"

# 制約確認
psql -U mks_user -d mks_db -c "\d projects"
```

### 2. アップロードファイル復旧

#### バックアップ確認
```bash
# アップロードバックアップ一覧
ls -la /backup/mks/uploads_*.tar.gz

# 最新バックアップ選択
LATEST_UPLOADS=$(ls -t /backup/mks/uploads_*.tar.gz | head -1)
echo "Using uploads backup: $LATEST_UPLOADS"
```

#### リストア実行
```bash
# 現在のアップロードディレクトリバックアップ
tar -czf /tmp/uploads_pre_restore.tar.gz /opt/mks/uploads/

# アップロードディレクトリクリア
rm -rf /opt/mks/uploads/*

# リストア実行
tar -xzf $LATEST_UPLOADS -C /

# 権限設定
chown -R mks:mks /opt/mks/uploads/
chmod -R 755 /opt/mks/uploads/
```

#### ファイル確認
```bash
# ファイル数確認
find /opt/mks/uploads/ -type f | wc -l

# ファイルサイズ確認
du -sh /opt/mks/uploads/

# サンプルファイル確認
ls -la /opt/mks/uploads/ | head -10
```

### 3. 設定ファイル復旧

#### Gitからの復旧
```bash
# 設定ディレクトリへ移動
cd /opt/mks/backend

# 最新コミット確認
git log --oneline -5

# 設定ファイル復旧
git checkout HEAD -- config/production.yml
git checkout HEAD -- alembic.ini
```

#### 手動バックアップからの復旧
```bash
# 設定バックアップ確認
ls -la /backup/mks/config_*.tar.gz

# リストア実行
tar -xzf /backup/mks/config_$(date +%Y%m%d).tar.gz -C /
```

## 完全システム復旧

### 1. 新規サーバーへの移行復旧
**対象**: サーバー故障時の完全移行

#### 準備
```bash
# 新規サーバー準備
# OSインストール
# 基本設定（ホスト名、ネットワーク、SSH）

# 必要なパッケージインストール
apt update
apt install -y postgresql nginx python3-pip git
```

#### アプリケーション復旧
```bash
# コードデプロイ
cd /opt
git clone https://github.com/your-org/mirai-knowledge-systems.git mks
cd mks/backend

# Python環境設定
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# データベース設定
sudo -u postgres createuser mks_user
sudo -u postgres createdb mks_db -O mks_user
```

#### データ復旧
```bash
# バックアップ転送
scp user@old-server:/backup/mks/latest.dump /tmp/
scp user@old-server:/backup/mks/uploads_latest.tar.gz /tmp/

# データベースリストア
pg_restore -U mks_user -d mks_db /tmp/latest.dump

# アップロードファイルリストア
tar -xzf /tmp/uploads_latest.tar.gz -C /
```

### 2. ポイントインタイムリカバリ
**対象**: 特定の時点へのデータ復旧

#### WALアーカイブ確認
```bash
# WALアーカイブ場所確認
ls -la /var/lib/postgresql/13/main/pg_wal/

# アーカイブ設定確認
cat /etc/postgresql/13/main/postgresql.conf | grep archive
```

#### PITR実行
```bash
# リカバリ設定ファイル作成
cat > /var/lib/postgresql/13/main/recovery.conf << EOF
restore_command = 'cp /backup/mks/wal/%f %p'
recovery_target_time = '2024-01-09 10:00:00+09'
recovery_target_action = 'promote'
EOF

# PostgreSQL再起動
sudo systemctl restart postgresql

# リカバリ完了確認
tail -f /var/log/postgresql/postgresql-13-main.log
```

## 復旧後の確認手順

### 1. 機能テスト
```bash
# APIヘルスチェック
curl -f http://localhost:5100/api/v1/health

# 認証テスト
TOKEN=$(curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.token')

# データアクセステスト
curl -X GET http://localhost:5100/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# ファイルアップロードテスト
curl -X POST http://localhost:5100/api/v1/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf"
```

### 2. パフォーマンス確認
```bash
# レスポンスタイム測定
time curl -s http://localhost:5100/api/v1/health > /dev/null

# データベースパフォーマンス
psql -U mks_user -d mks_db -c "SELECT * FROM pg_stat_activity;"

# システムリソース
top -b -n1 | head -10
```

### 3. データ整合性確認
```bash
# レコード数確認
psql -U mks_user -d mks_db -c "
SELECT 'projects' as table_name, COUNT(*) as count FROM projects
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'documents', COUNT(*) FROM documents;
"

# 外部キー制約確認
psql -U mks_user -d mks_db -c "
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f';
"

# データ整合性チェック
psql -U mks_user -d mks_db -c "
-- プロジェクトに紐づくドキュメント確認
SELECT p.name, COUNT(d.id) as doc_count
FROM projects p
LEFT JOIN documents d ON p.id = d.project_id
GROUP BY p.id, p.name;
"
```

## 復旧自動化スクリプト

### 自動復旧スクリプト
```bash
#!/bin/bash
# scripts/auto-recovery.sh

SERVICE="mks-backend"
MAX_ATTEMPTS=3
ATTEMPT=1

echo "=== Auto Recovery Started ==="

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT of $MAX_ATTEMPTS"
    
    # サービスチェック
    if systemctl is-active --quiet $SERVICE; then
        echo "Service is running"
        exit 0
    fi
    
    # 復旧実行
    echo "Attempting recovery..."
    systemctl restart $SERVICE
    sleep 30
    
    # ヘルスチェック
    if curl -f http://localhost:5100/api/v1/health > /dev/null 2>&1; then
        echo "Recovery successful"
        exit 0
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
done

echo "Auto recovery failed, manual intervention required"
# アラート送信
```

### 完全復旧スクリプト
```bash
#!/bin/bash
# scripts/full-recovery.sh

echo "=== Full System Recovery Started ==="

# バックアップ確認
if [ ! -f "/backup/mks/latest.dump" ]; then
    echo "ERROR: No database backup found"
    exit 1
fi

# サービス停止
systemctl stop mks-backend nginx

# データベース復旧
echo "Restoring database..."
dropdb -U mks_user mks_db
createdb -U mks_user mks_db
pg_restore -U mks_user -d mks_db /backup/mks/latest.dump

# アップロードファイル復旧
echo "Restoring uploads..."
rm -rf /opt/mks/uploads/*
tar -xzf /backup/mks/uploads_latest.tar.gz -C /

# サービス起動
echo "Starting services..."
systemctl start postgresql
systemctl start mks-backend
systemctl start nginx

# 確認
echo "Running health checks..."
curl -f http://localhost:5100/api/v1/health

echo "=== Full System Recovery Completed ==="
```

## 復旧テスト

### 定期復旧テスト
- **毎四半期**: 完全復旧テスト
- **毎月**: コンポーネント復旧テスト
- **毎週**: 自動復旧テスト

### テストシナリオ
1. **サービス停止テスト**: サービス停止からの自動復旧
2. **データベース復旧テスト**: バックアップからのデータ復旧
3. **完全システムテスト**: 新規環境への完全移行

### テスト手順
```bash
# テスト環境準備
cp -r /opt/mks /opt/mks_test
createdb mks_test

# テスト実行
bash scripts/test-recovery.sh

# 結果確認
curl -f http://localhost:5100/api/v1/health
```

## 復旧後のフォローアップ

### 1. 原因分析
- 障害原因の詳細分析
- 復旧プロセスの改善点特定
- 予防策の検討

### 2. ドキュメント更新
- 復旧手順の更新
- 新しい障害パターンの追加
- 自動化スクリプトの改善

### 3. チームレビュー
- 復旧プロセスの振り返り
- コミュニケーションの改善
- トレーニングの実施

### 4. レポート作成
```markdown
## 復旧レポート: REC-2024-001

### 障害概要
- **発生日時**: 2024-01-09 10:00
- **復旧日時**: 2024-01-09 10:30
- **復旧時間**: 30分
- **データ損失**: なし

### 復旧手順
1. サービス停止検知
2. ログ分析
3. 設定確認
4. サービス再起動
5. 機能テスト

### 改善点
- 自動復旧スクリプトの改善
- 監視アラートの調整
- バックアップ頻度の見直し
```</content>
<parameter name="filePath">docs/11_運用保守(Operations)/15_復旧手順(Recovery-Procedures).md