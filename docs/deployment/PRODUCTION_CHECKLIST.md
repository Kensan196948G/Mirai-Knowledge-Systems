# 本番環境デプロイメントチェックリスト

## 📋 概要

Mirai Knowledge Systemを本番環境にデプロイする前の最終確認チェックリストです。

## ✅ 完了済み項目

### インフラストラクチャ

- ✅ **PostgreSQL 16.11** インストール・稼働中
- ✅ **Nginx** インストール・設定完了（port 8080 → 8443リダイレクト）
- ✅ **SSL/TLS証明書** 配置完了（/etc/ssl/mks/）
- ✅ **gunicorn 23.0.0** インストール済み
- ✅ **systemdサービスファイル** 準備完了
  - mirai-knowledge-system-dev.service（開発）
  - mirai-knowledge-production.service（本番）
- ✅ **ログローテーション** 設定完了（/etc/logrotate.d/）

### アプリケーション

- ✅ **Flask API** 正常稼働（port 5100）
- ✅ **データベース接続** PostgreSQL接続確認済み
- ✅ **E2Eテスト環境** Playwright設定完了
- ✅ **テストカバレッジ** 91.07%（538テスト）

## ⚠️ 要確認項目

### 1. セキュリティ設定

#### 環境変数

```bash
# 本番環境用.envファイルの作成
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
cp .env.production.example .env.production

# 必須環境変数を設定
vim .env.production
```

**必須設定項目:**

```bash
# 環境モード
MKS_ENV=production
MKS_DEBUG=false

# セキュリティキー（絶対に公開しない！）
MKS_SECRET_KEY=<新しいランダム文字列を生成>
MKS_JWT_SECRET_KEY=<新しいランダム文字列を生成>

# データベース
DATABASE_URL=postgresql://postgres:<強力なパスワード>@localhost:5432/mirai_knowledge_db

# HTTPS強制
MKS_FORCE_HTTPS=true
MKS_TRUST_PROXY_HEADERS=true

# HSTS
MKS_HSTS_ENABLED=true
MKS_HSTS_MAX_AGE=31536000

# CORS（必要に応じて）
MKS_CORS_ORIGINS=https://yourdomain.com
```

**セキュリティキー生成:**

```bash
# MKS_SECRET_KEY生成
python3 -c "import secrets; print('MKS_SECRET_KEY=' + secrets.token_urlsafe(64))"

# MKS_JWT_SECRET_KEY生成
python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
```

#### データベースセキュリティ

```bash
# PostgreSQL管理者パスワードを強力なものに変更
sudo -u postgres psql
ALTER USER postgres WITH PASSWORD '<強力なパスワード>';

# .envファイルのDATABASE_URLを更新
DATABASE_URL=postgresql://postgres:<新しいパスワード>@localhost:5432/mirai_knowledge_db
```

#### ファイル権限

```bash
# .envファイルの権限を制限（重要！）
chmod 600 backend/.env
chmod 600 backend/.env.production

# SSL秘密鍵の権限確認
ls -la /etc/ssl/mks/mks.key
# -rw------- 1 root root（600）であることを確認
```

### 2. Nginx セキュリティヘッダー

`/etc/nginx/sites-available/mirai-knowledge-system`に以下を追加（推奨）:

```nginx
server {
    listen 8443 ssl http2;
    server_name _;

    ssl_certificate /etc/ssl/mks/mks.crt;
    ssl_certificate_key /etc/ssl/mks/mks.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:MKS_SSL:10m;

    # セキュリティヘッダー（追加推奨）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    access_log /var/log/nginx/mks-access.log;
    error_log /var/log/nginx/mks-error.log;
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

変更後はNginxをリロード:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 3. systemdサービス起動

```bash
# インストールスクリプトを実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
./install-systemd-service.sh

# または手動で設定
sudo cp mirai-knowledge-production.service /etc/systemd/system/mirai-knowledge-prod.service
sudo systemctl daemon-reload
sudo systemctl enable mirai-knowledge-prod.service
sudo systemctl start mirai-knowledge-prod.service

# 状態確認
sudo systemctl status mirai-knowledge-prod.service
```

### 4. 本番ログディレクトリ作成

```bash
# ログディレクトリ作成
sudo mkdir -p /var/log/mirai-knowledge

# 権限設定
sudo chown kensan:kensan /var/log/mirai-knowledge
sudo chmod 755 /var/log/mirai-knowledge

# gunicorn設定でログパスが正しいか確認
grep "log" backend/gunicorn.conf.py
```

### 5. ファイアウォール設定

```bash
# UFWでHTTPS（8443）を許可
sudo ufw allow 8443/tcp
sudo ufw status

# または iptables
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT
```

### 6. バックアップ設定確認

```bash
# バックアップスクリプトの動作確認
ls -la backend/backups/
cat backend/logs/backup_db.log

# cronジョブ確認
crontab -l | grep backup
```

## 🔒 セキュリティ監査

### SSL/TLS設定テスト

```bash
# SSL証明書の有効期限確認
openssl x509 -in /etc/ssl/mks/mks.crt -noout -dates

# SSL/TLS設定テスト（外部ツール）
# https://www.ssllabs.com/ssltest/
```

### セキュリティスキャン

```bash
# Pythonパッケージの脆弱性スキャン
cd backend
source venv_linux/bin/activate
pip install safety
safety check

# または
pip-audit
```

### OWASP ZAP / Burp Suite

本番デプロイ前にセキュリティスキャンツールで脆弱性診断を実施することを推奨。

## 📊 パフォーマンス最適化

### データベース

```sql
-- PostgreSQL統計情報更新
ANALYZE;

-- インデックス再構築
REINDEX DATABASE mirai_knowledge_db;

-- 接続プール設定確認
SHOW max_connections;
```

### gunicorn ワーカー数調整

```python
# backend/gunicorn.conf.py
# ワーカー数 = (CPU コア数 * 2) + 1
workers = multiprocessing.cpu_count() * 2 + 1
```

現在のCPUコア数確認:

```bash
nproc
```

### キャッシュ設定（オプション）

Redis導入を検討（レート制限、セッション管理）:

```bash
sudo apt install redis-server
pip install redis
```

## 🔍 監視・アラート

### システムモニタリング

```bash
# Prometheusメトリクス確認
curl http://localhost:5100/metrics

# systemdジャーナル監視
sudo journalctl -u mirai-knowledge-prod -f

# リソース使用状況
htop
```

### ログ監視

```bash
# エラーログ監視
tail -f /var/log/mirai-knowledge/error.log

# アクセスログ監視
tail -f /var/log/mirai-knowledge/access.log
```

### アラート設定（推奨）

- **Grafana + Prometheus**: メトリクス可視化
- **Sentry**: エラートラッキング
- **Uptime Kuma**: 死活監視

## 📝 本番デプロイメント手順

### 1. 前提条件確認

```bash
# PostgreSQL稼働確認
sudo systemctl status postgresql

# Nginx稼働確認
sudo systemctl status nginx

# ディスク容量確認
df -h
```

### 2. アプリケーションデプロイ

```bash
# 1. 最新コードを取得
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
git pull origin main

# 2. Python依存関係更新
cd backend
source venv_linux/bin/activate
pip install -r requirements.txt

# 3. データベースマイグレーション
alembic upgrade head

# 4. systemdサービス起動
sudo systemctl restart mirai-knowledge-prod

# 5. 状態確認
sudo systemctl status mirai-knowledge-prod
curl -k https://localhost:8443/api/v1/health
```

### 3. 動作確認

```bash
# ヘルスチェック
curl -k https://localhost:8443/api/v1/health | jq .

# ログイン動作確認
curl -k -X POST https://localhost:8443/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# ダッシュボード統計取得
curl -k -H "Authorization: Bearer <TOKEN>" \
  https://localhost:8443/api/v1/dashboard/stats
```

## ⚠️ トラブルシューティング

### サービス起動失敗

```bash
# ログ確認
sudo journalctl -u mirai-knowledge-prod -n 50

# 設定ファイル検証
sudo systemd-analyze verify /etc/systemd/system/mirai-knowledge-prod.service
```

### データベース接続エラー

```bash
# PostgreSQL接続テスト
psql -U postgres -d mirai_knowledge_db -c "SELECT version();"

# 接続数確認
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

### SSL証明書エラー

```bash
# 証明書検証
openssl verify /etc/ssl/mks/mks.crt

# Nginx設定テスト
sudo nginx -t
```

## 🎯 本番運用開始後

- [ ] 初回バックアップ実施
- [ ] 監視ダッシュボードセットアップ
- [ ] アラート通知設定
- [ ] ユーザー向けドキュメント作成
- [ ] インシデント対応手順書作成

---

**作成日**: 2026-01-08
**バージョン**: 1.0.0
**対象環境**: Phase C - 本番運用開始
