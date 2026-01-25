# 本番環境クイックセットアップガイド

**目標**: 5分で本番環境を起動する

## ⚡ 前提条件

- Ubuntu 20.04+ / Rocky Linux 8+
- PostgreSQL 15+ インストール済み
- Nginx インストール済み
- Python 3.8+ と venv インストール済み

## 🚀 セットアップ手順（5ステップ）

### 1. 秘密鍵の生成と設定（1分）

```bash
cd /path/to/Mirai-Knowledge-Systems/backend

# .envファイルを作成
cp .env.example .env

# 秘密鍵を生成して.envに追記
python3 -c "import secrets; print('MKS_SECRET_KEY=' + secrets.token_urlsafe(64))" >> .env
python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(64))" >> .env

# .envファイルを編集
nano .env
```

**.envファイル必須設定項目**:

```bash
# 環境モード
MKS_ENV=production
MKS_DEBUG=false

# データベース（PostgreSQLパスワードを設定）
MKS_USE_POSTGRESQL=true
DATABASE_URL=postgresql://postgres:YOUR_STRONG_PASSWORD@localhost:5432/mirai_knowledge_db

# CORS設定（本番環境のIPアドレスまたはドメイン）
MKS_CORS_ORIGINS=https://192.168.0.187:8445

# HTTPS強制
MKS_FORCE_HTTPS=true
MKS_TRUST_PROXY_HEADERS=true

# HSTS有効化
MKS_HSTS_ENABLED=true
MKS_HSTS_MAX_AGE=31536000
```

**.envファイルの権限を制限（重要）**:

```bash
chmod 600 .env
```

### 2. SSL証明書の設定（2分）

#### オプションA: 自己署名証明書（開発・検証用）

```bash
# SSL証明書ディレクトリ作成
sudo mkdir -p /etc/ssl/mks

# 自己署名証明書を生成（365日有効）
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/mks/mks.key \
  -out /etc/ssl/mks/mks.crt \
  -subj "/C=JP/ST=Tokyo/L=Chiyoda/O=YourCompany/CN=192.168.0.187"

# 権限設定
sudo chmod 600 /etc/ssl/mks/mks.key
sudo chmod 644 /etc/ssl/mks/mks.crt
```

#### オプションB: Let's Encrypt（本番推奨・ドメイン必須）

```bash
# Certbotインストール
sudo apt install certbot python3-certbot-nginx -y

# SSL証明書取得（example.comを実際のドメインに置き換え）
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自動更新の確認
sudo certbot renew --dry-run
```

### 3. Nginx設定（1分）

```bash
# Nginx設定ファイルをコピー
sudo cp /path/to/Mirai-Knowledge-Systems/config/nginx-production.conf \
  /etc/nginx/sites-available/mirai-knowledge-production

# SSL証明書パスを編集（Let's Encryptの場合）
sudo nano /etc/nginx/sites-available/mirai-knowledge-production

# Let's Encryptを使う場合は以下に変更:
# ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# シンボリックリンク作成
sudo ln -sf /etc/nginx/sites-available/mirai-knowledge-production \
  /etc/nginx/sites-enabled/

# デフォルト設定を無効化（必要に応じて）
sudo rm -f /etc/nginx/sites-enabled/default

# 設定テスト
sudo nginx -t

# Nginxをリロード
sudo systemctl reload nginx
```

### 4. systemdサービスの設定（1分）

```bash
# サービスファイルを編集
cd /path/to/Mirai-Knowledge-Systems
nano mirai-knowledge-app.service
```

**編集箇所（3箇所のみ）**:

```ini
[Service]
# 1. WorkingDirectoryを実際のパスに変更
WorkingDirectory=/actual/path/to/Mirai-Knowledge-Systems

# 2. ExecStartを実際のパスに変更（venv_linuxのPythonを使用）
ExecStart=/actual/path/to/Mirai-Knowledge-Systems/venv_linux/bin/gunicorn \
  --config /actual/path/to/Mirai-Knowledge-Systems/backend/gunicorn.conf.py \
  --chdir /actual/path/to/Mirai-Knowledge-Systems/backend \
  app_v2:app

# 3. 環境変数（MKS_SECRET_KEYとMKS_JWT_SECRET_KEYを.envから取得した値に置き換え）
Environment=MKS_SECRET_KEY=your-generated-secret-key-here
Environment=MKS_JWT_SECRET_KEY=your-generated-jwt-secret-key-here
Environment=MKS_CORS_ORIGINS=https://192.168.0.187:8445
```

**サービス登録と起動**:

```bash
# サービスファイルをコピー
sudo cp mirai-knowledge-app.service /etc/systemd/system/

# systemdをリロード
sudo systemctl daemon-reload

# サービスを有効化（起動時に自動起動）
sudo systemctl enable mirai-knowledge-app

# サービスを起動
sudo systemctl start mirai-knowledge-app

# 状態確認
sudo systemctl status mirai-knowledge-app
```

### 5. データベース初期化とログディレクトリ作成（30秒）

```bash
# PostgreSQLデータベース作成
sudo -u postgres psql << EOF
CREATE DATABASE mirai_knowledge_db;
CREATE USER mks_user WITH PASSWORD 'YOUR_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge_db TO mks_user;
\q
EOF

# ログディレクトリ作成
sudo mkdir -p /var/log/mirai-knowledge
sudo chown $USER:$USER /var/log/mirai-knowledge
sudo chmod 755 /var/log/mirai-knowledge

# データベースマイグレーション実行
cd /path/to/Mirai-Knowledge-Systems/backend
source venv_linux/bin/activate
export $(cat .env | xargs)
alembic upgrade head

# サービス再起動
sudo systemctl restart mirai-knowledge-app
```

## ✅ 初回起動チェックリスト

起動後、以下を確認してください:

- [ ] **1. サービス稼働確認**: `sudo systemctl status mirai-knowledge-app` が `active (running)`
- [ ] **2. ログ確認**: `tail -f /var/log/mirai-knowledge/error.log` にエラーがない
- [ ] **3. ポート確認**: `sudo netstat -tlnp | grep 5100` でGunicornが5100番ポートでリッスン
- [ ] **4. Nginx確認**: `sudo systemctl status nginx` が `active (running)`
- [ ] **5. PostgreSQL接続**: `psql -U postgres -d mirai_knowledge_db -c "SELECT version();"` が成功
- [ ] **6. ヘルスチェック**: `curl -k https://localhost:8445/api/v1/health` が200応答
- [ ] **7. WebUIアクセス**: ブラウザで `https://192.168.0.187:8445` にアクセス可能
- [ ] **8. ログイン**: 管理者アカウント（admin/admin123）でログイン成功
- [ ] **9. HTTPS強制**: `http://192.168.0.187` が自動的に `https://192.168.0.187:8445` にリダイレクト
- [ ] **10. SSL証明書**: ブラウザでSSL証明書警告が表示される（自己署名の場合は正常）

## 🔧 コマンドリファレンス

### サービス操作

```bash
# サービス起動
sudo systemctl start mirai-knowledge-app

# サービス停止
sudo systemctl stop mirai-knowledge-app

# サービス再起動
sudo systemctl restart mirai-knowledge-app

# サービス状態確認
sudo systemctl status mirai-knowledge-app

# ログをリアルタイム監視
sudo journalctl -u mirai-knowledge-app -f

# 最新50行のログを表示
sudo journalctl -u mirai-knowledge-app -n 50
```

### Nginx操作

```bash
# Nginx設定テスト
sudo nginx -t

# Nginxリロード（設定反映）
sudo systemctl reload nginx

# Nginx再起動
sudo systemctl restart nginx

# Nginxログ確認
tail -f /var/log/nginx/mirai-knowledge-access.log
tail -f /var/log/nginx/mirai-knowledge-error.log
```

### データベース操作

```bash
# PostgreSQL接続
sudo -u postgres psql -d mirai_knowledge_db

# データベースバックアップ
sudo -u postgres pg_dump mirai_knowledge_db > backup_$(date +%Y%m%d).sql

# データベースリストア
sudo -u postgres psql mirai_knowledge_db < backup_20260117.sql
```

## 🐛 トラブルシューティング

### 1. サービスが起動しない

**症状**: `systemctl status mirai-knowledge-app` が `failed`

**確認ポイント**:

```bash
# エラーログを確認
sudo journalctl -u mirai-knowledge-app -n 50

# よくある原因:
# - .envファイルの秘密鍵が未設定
# - DATABASE_URLが間違っている
# - venv_linux/binのパスが間違っている
# - ログディレクトリの権限不足

# .envファイルを確認
cat backend/.env | grep -E 'MKS_SECRET_KEY|MKS_JWT_SECRET_KEY|DATABASE_URL'

# ログディレクトリの権限確認
ls -ld /var/log/mirai-knowledge
```

**解決策**:

```bash
# .envを再設定
cd backend
python3 -c "import secrets; print('MKS_SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
# 上記で生成された値を.envに設定

# ログディレクトリを作成
sudo mkdir -p /var/log/mirai-knowledge
sudo chown $USER:$USER /var/log/mirai-knowledge

# サービス再起動
sudo systemctl restart mirai-knowledge-app
```

### 2. データベース接続エラー

**症状**: ログに `FATAL: password authentication failed for user "postgres"`

**解決策**:

```bash
# PostgreSQLパスワードを変更
sudo -u postgres psql
ALTER USER postgres WITH PASSWORD 'new_strong_password';
\q

# .envのDATABASE_URLを更新
nano backend/.env
# DATABASE_URL=postgresql://postgres:new_strong_password@localhost:5432/mirai_knowledge_db

# サービス再起動
sudo systemctl restart mirai-knowledge-app
```

### 3. Nginx 502 Bad Gateway

**症状**: ブラウザで `502 Bad Gateway` エラー

**確認ポイント**:

```bash
# バックエンドが起動しているか確認
sudo systemctl status mirai-knowledge-app

# ポート5100がリッスンしているか確認
sudo netstat -tlnp | grep 5100

# Nginxエラーログを確認
sudo tail -f /var/log/nginx/mirai-knowledge-error.log
```

**解決策**:

```bash
# バックエンドが停止している場合
sudo systemctl start mirai-knowledge-app

# ファイアウォールで5100がブロックされている場合
sudo ufw allow 5100/tcp  # UFWの場合
sudo iptables -A INPUT -p tcp --dport 5100 -j ACCEPT  # iptablesの場合
```

### 4. SSL証明書エラー

**症状**: ブラウザで「この接続ではプライバシーが保護されません」

**自己署名証明書の場合（正常）**:

- ブラウザで「詳細設定」→「サイトにアクセスする（安全ではありません）」をクリック
- これは自己署名証明書の正常な動作です

**Let's Encrypt証明書の場合（要確認）**:

```bash
# 証明書の有効期限確認
sudo certbot certificates

# 証明書更新
sudo certbot renew

# Nginx再起動
sudo systemctl reload nginx
```

### 5. CORS エラー

**症状**: ブラウザコンソールに `Access to XMLHttpRequest has been blocked by CORS policy`

**解決策**:

```bash
# .envのCORS設定を確認・修正
nano backend/.env

# 正しい形式:
# MKS_CORS_ORIGINS=https://192.168.0.187:8445,https://yourdomain.com

# サービス再起動
sudo systemctl restart mirai-knowledge-app
```

## 📊 本番環境監視

### ヘルスチェックエンドポイント

```bash
# API稼働確認
curl -k https://localhost:8445/api/v1/health

# 期待される応答:
# {"status":"healthy","database":"connected","timestamp":"2026-01-17T09:30:00"}
```

### Prometheusメトリクス

```bash
# メトリクス取得（ローカルネットワークからのみアクセス可能）
curl http://localhost:5100/metrics
```

### ログローテーション

```bash
# logrotateの設定例（/etc/logrotate.d/mirai-knowledge）
/var/log/mirai-knowledge/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 kensan kensan
    sharedscripts
    postrotate
        sudo systemctl reload mirai-knowledge-app > /dev/null 2>&1 || true
    endscript
}
```

## 🔐 セキュリティ推奨事項

1. **秘密鍵の管理**
   - `.env`ファイルを絶対にGitにコミットしない
   - 権限を`600`に設定（`chmod 600 backend/.env`）

2. **PostgreSQLパスワード**
   - 強力なパスワードを使用（最低16文字、英数字記号混在）
   - デフォルトの`postgres`ユーザーではなく専用ユーザーを作成

3. **ファイアウォール**
   - 外部からの5100番ポートへの直接アクセスをブロック
   - 8445番ポート（HTTPS）のみ許可

4. **SSL証明書**
   - 本番環境では必ずLet's Encryptまたは商用証明書を使用
   - 自己署名証明書は開発・検証環境のみで使用

5. **定期バックアップ**
   - データベースを毎日自動バックアップ
   - バックアップスクリプトをcronで定期実行

## 🎯 次のステップ

本番環境が起動したら:

1. 管理者パスワードを変更（デフォルトのadmin/admin123から）
2. バックアップ設定の確認と定期実行
3. 監視ダッシュボードのセットアップ（Grafana + Prometheus推奨）
4. アラート通知の設定
5. ユーザー向けマニュアルの作成

## 📚 関連ドキュメント

- [詳細デプロイメントチェックリスト](PRODUCTION_CHECKLIST.md)
- [セットアップガイド](../setup/SETUP.md)
- [運用手順書](../../runbook/)

---

**作成日**: 2026-01-17
**バージョン**: 1.0.0
**対象**: Phase C - 本番運用開始
