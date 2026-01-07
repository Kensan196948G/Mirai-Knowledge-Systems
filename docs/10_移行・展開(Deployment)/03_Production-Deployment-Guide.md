# 本番環境構築ガイド

建設土木ナレッジシステムを本番環境に展開するための詳細な手順書です。

## 目次

1. [前提条件](#1-前提条件)
2. [サーバー準備](#2-サーバー準備)
3. [アプリケーションセットアップ](#3-アプリケーションセットアップ)
4. [SSL証明書取得](#4-ssl証明書取得)
5. [Nginx設定](#5-nginx設定)
6. [Gunicorn設定](#6-gunicorn設定)
7. [systemdサービス設定](#7-systemdサービス設定)
8. [動作確認](#8-動作確認)
9. [セキュリティチェックリスト](#9-セキュリティチェックリスト)
10. [運用手順](#10-運用手順)
11. [トラブルシューティング](#11-トラブルシューティング)
12. [パフォーマンスチューニング](#12-パフォーマンスチューニング)

---

## 1. 前提条件

### 1.1 サーバー要件

#### ハードウェア要件

| 項目 | 最小要件 | 推奨 |
|------|----------|------|
| CPU | 2コア | 4コア以上 |
| メモリ | 4GB | 8GB以上 |
| ストレージ | 20GB SSD | 50GB SSD以上 |
| ネットワーク | 100Mbps | 1Gbps |

#### ソフトウェア要件

- OS: Ubuntu 22.04 LTS / 24.04 LTS（推奨）または CentOS Stream 9
- Python: 3.10以上
- Nginx: 1.24以上
- Git: 2.34以上

### 1.2 ネットワーク要件

- 有効なドメイン名（例: `api.example.com`）
- DNSレコードの設定権限
- 開放が必要なポート:
  - `80/tcp` (HTTP) - Let's Encrypt証明書検証用
  - `443/tcp` (HTTPS) - 本番API提供用
  - `22/tcp` (SSH) - サーバー管理用

### 1.3 必要な権限

- `sudo` 権限のあるユーザーアカウント
- ファイアウォール設定権限
- systemdサービス管理権限

### 1.4 事前準備

以下の情報を用意してください:

- [ ] ドメイン名
- [ ] サーバーのIPアドレス
- [ ] SSH鍵ペア
- [ ] 強力な秘密鍵（32文字以上のランダム文字列）×2
  - アプリケーション秘密鍵（MKS_SECRET_KEY）
  - JWT秘密鍵（MKS_JWT_SECRET_KEY）

#### 秘密鍵の生成方法

```bash
# 安全な秘密鍵を生成（各自で実行）
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 1.5 自動化スクリプト（任意）

手順を簡略化したい場合は、ルートの自動セットアップスクリプトを利用できます。

```bash
cd /path/to/Mirai-Knowledge-Systems
./setup-production.sh
```

Gunicornのみを手動で起動する場合は `backend/run_production.sh` を使用します。

---

## 2. サーバー準備

### 2.1 システムアップデート

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo dnf update -y
```

### 2.2 必要なパッケージのインストール

```bash
# Ubuntu/Debian
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nginx \
    git \
    curl \
    ufw \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev

# CentOS/RHEL
sudo dnf install -y \
    python3.10 \
    python3-pip \
    nginx \
    git \
    curl \
    firewalld \
    gcc \
    python3-devel \
    openssl-devel
```

### 2.3 アプリケーションユーザー作成

セキュリティのため、専用ユーザーでアプリケーションを実行します。

```bash
# アプリケーション用ユーザー作成
sudo useradd -m -s /bin/bash -U mks

# 必要なディレクトリの作成
sudo mkdir -p /var/www/mirai-knowledge-system
sudo mkdir -p /var/lib/mirai-knowledge-system/data
sudo mkdir -p /var/log/mirai-knowledge-system

# 所有権の設定
sudo chown -R mks:mks /var/www/mirai-knowledge-system
sudo chown -R mks:mks /var/lib/mirai-knowledge-system
sudo chown -R mks:mks /var/log/mirai-knowledge-system
```

### 2.4 ファイアウォール設定

```bash
# Ubuntu (ufw)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 3. アプリケーションセットアップ

### 3.1 リポジトリのクローン

```bash
# mksユーザーに切り替え
sudo su - mks

# アプリケーションディレクトリに移動
cd /var/www/mirai-knowledge-system

# リポジトリをクローン
git clone https://github.com/your-org/Mirai-Knowledge-Systems.git .

# バックエンドディレクトリに移動
cd backend
```

### 3.2 Python仮想環境の構築

```bash
# 仮想環境を作成
python3.10 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip setuptools wheel
```

### 3.3 依存関係のインストール

```bash
# 本番環境用パッケージをインストール
pip install -r requirements.txt

# Gunicornのインストール（本番環境必須）
pip install gunicorn

# オプション: パフォーマンス向上用
pip install gevent  # 非同期ワーカー用
```

### 3.4 環境変数設定

```bash
# .env.productionファイルを作成
cat > .env.production << 'EOF'
# ==========================================================
# 本番環境設定
# ==========================================================

# 環境設定
MKS_ENV=production

# セキュリティ: 秘密鍵（必ず変更してください！）
MKS_SECRET_KEY="YOUR-VERY-SECURE-SECRET-KEY-HERE"
MKS_JWT_SECRET_KEY="YOUR-VERY-SECURE-JWT-SECRET-KEY-HERE"

# CORS設定（許可するオリジンをカンマ区切りで指定）
MKS_CORS_ORIGINS="https://example.com,https://www.example.com"

# データディレクトリ
MKS_DATA_DIR="/var/lib/mirai-knowledge-system/data"

# ログ設定
MKS_LOG_FILE="/var/log/mirai-knowledge-system/app.log"
MKS_LOG_LEVEL="INFO"

# HTTPS設定（Nginx経由の場合）
MKS_FORCE_HTTPS="true"
MKS_TRUST_PROXY_HEADERS="true"

# SSL証明書パス（Gunicornで直接SSL使用時）
# MKS_USE_SSL="false"  # Nginx経由の場合はfalse
# MKS_SSL_CERT_PATH="/etc/letsencrypt/live/api.example.com/fullchain.pem"
# MKS_SSL_KEY_PATH="/etc/letsencrypt/live/api.example.com/privkey.pem"

# HSTS設定
MKS_HSTS_ENABLED="true"
MKS_HSTS_MAX_AGE="31536000"
MKS_HSTS_INCLUDE_SUBDOMAINS="true"
MKS_HSTS_PRELOAD="false"

# JWT設定
MKS_JWT_ACCESS_TOKEN_HOURS="1"
MKS_JWT_REFRESH_TOKEN_DAYS="7"

# Gunicorn設定
MKS_GUNICORN_WORKERS="4"
MKS_GUNICORN_THREADS="2"
MKS_GUNICORN_BIND="127.0.0.1:8000"
MKS_GUNICORN_TIMEOUT="30"
MKS_GUNICORN_WORKER_CLASS="sync"
MKS_GUNICORN_GRACEFUL_TIMEOUT="30"
MKS_GUNICORN_KEEPALIVE="5"

# レート制限（オプション: Redisを使用する場合）
# MKS_REDIS_URL="redis://localhost:6379/0"

# データベース（オプション: PostgreSQLを使用する場合）
# MKS_DATABASE_URL="postgresql://user:password@localhost:5432/mks"
EOF

# ファイル権限を制限（重要！）
chmod 600 .env.production
```

**重要**: `.env.production` の秘密鍵を必ず変更してください。

```bash
# 安全な秘密鍵を生成
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 秘密鍵を表示（コピーして.env.productionに設定）
echo "MKS_SECRET_KEY=\"$SECRET_KEY\""
echo "MKS_JWT_SECRET_KEY=\"$JWT_SECRET\""
```

### 3.5 データディレクトリの初期化

```bash
# mksユーザーで実行
mkdir -p /var/lib/mirai-knowledge-system/data/{knowledge,analysis,users}

# 必要なファイルの作成
touch /var/lib/mirai-knowledge-system/data/users/users.json
touch /var/lib/mirai-knowledge-system/data/access_logs.json

# 初期データ設定（空のJSONオブジェクト）
echo '{}' > /var/lib/mirai-knowledge-system/data/users/users.json
echo '[]' > /var/lib/mirai-knowledge-system/data/access_logs.json

# 権限設定
chmod 700 /var/lib/mirai-knowledge-system/data
chmod 600 /var/lib/mirai-knowledge-system/data/users/users.json
```

---

## 4. SSL証明書取得

### 4.1 Let's Encryptのインストール

```bash
# 元のユーザーに戻る
exit

# Certbotのインストール（Ubuntu）
sudo apt install certbot python3-certbot-nginx

# Certbotのインストール（CentOS/RHEL）
sudo dnf install certbot python3-certbot-nginx
```

### 4.2 証明書の取得（スタンドアロンモード）

Nginx設定前に証明書を取得する方法:

```bash
# Nginxが起動している場合は停止
sudo systemctl stop nginx

# 証明書の取得
sudo certbot certonly --standalone \
    -d api.example.com \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email

# 証明書の保存場所:
# /etc/letsencrypt/live/api.example.com/fullchain.pem
# /etc/letsencrypt/live/api.example.com/privkey.pem
```

### 4.3 証明書の取得（Nginxプラグインモード）

Nginx設定後に証明書を取得する方法:

```bash
sudo certbot --nginx -d api.example.com
```

### 4.4 自動更新の設定

```bash
# 更新のテスト
sudo certbot renew --dry-run

# cronジョブの確認（通常は自動設定済み）
sudo systemctl status certbot.timer

# 手動でcronを設定する場合:
echo "0 0,12 * * * root certbot renew --quiet --post-hook 'systemctl reload nginx'" | \
    sudo tee /etc/cron.d/certbot-renew
```

### 4.5 DHパラメータの生成

強力な鍵交換のためにDHパラメータを生成します（5-10分程度かかります）。

```bash
sudo openssl dhparam -out /etc/nginx/dhparam.pem 4096
```

---

## 5. Nginx設定

### 5.1 Nginx設定ファイルの作成

```bash
# 設定ファイルを作成
sudo nano /etc/nginx/sites-available/mirai-knowledge-system
```

以下の内容をコピー（`backend/config/nginx.conf.example` をベースに編集）:

```nginx
# レート制限ゾーン定義（httpブロック内に記述）
# /etc/nginx/nginx.conf に以下を追加:
#
# limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
# limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;

# アップストリーム定義
upstream mirai_knowledge_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP -> HTTPS リダイレクト
server {
    listen 80;
    listen [::]:80;
    server_name api.example.com;

    # Let's Encrypt認証用
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # その他全てのリクエストをHTTPSにリダイレクト
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS設定
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.example.com;

    # SSL証明書設定
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    ssl_dhparam /etc/nginx/dhparam.pem;

    # SSL/TLSセキュリティ設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # SSLセッション設定
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests" always;

    # 基本設定
    server_tokens off;
    client_max_body_size 10M;

    # タイムアウト設定
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # ログ設定
    access_log /var/log/nginx/mirai-knowledge-access.log combined;
    error_log /var/log/nginx/mirai-knowledge-error.log warn;

    # 静的ファイル配信（オプション）
    location /static/ {
        alias /var/www/mirai-knowledge-system/webui/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript application/json;
    }

    # APIプロキシ設定
    location /api/ {
        proxy_pass http://mirai_knowledge_backend;

        # プロキシヘッダー
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # HTTP Keep-Alive
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # キャッシュ無効化
        add_header Cache-Control "no-store, no-cache, must-revalidate" always;
        add_header Pragma "no-cache" always;
        expires off;
    }

    # ログインエンドポイントのレート制限
    location /api/v1/auth/login {
        limit_req zone=login_limit burst=5 nodelay;

        proxy_pass http://mirai_knowledge_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # フロントエンド配信
    location / {
        proxy_pass http://mirai_knowledge_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ヘルスチェック
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # セキュリティ: 不要なリクエストを拒否
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~* \.(env|ini|conf|config|yml|yaml)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### 5.2 nginx.confにレート制限設定を追加

```bash
# nginx.confを編集
sudo nano /etc/nginx/nginx.conf
```

`http` ブロック内に以下を追加:

```nginx
http {
    # ... 既存の設定 ...

    # レート制限ゾーン定義
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;

    # GZip圧縮
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml;

    # ... 残りの設定 ...
}
```

### 5.3 Nginx設定の有効化

```bash
# シンボリックリンクを作成
sudo ln -s /etc/nginx/sites-available/mirai-knowledge-system /etc/nginx/sites-enabled/

# デフォルト設定を無効化（必要に応じて）
sudo rm -f /etc/nginx/sites-enabled/default

# 設定ファイルのテスト
sudo nginx -t

# Nginxを起動
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## 6. Gunicorn設定

### 6.1 Gunicorn設定ファイルの作成

```bash
# mksユーザーに切り替え
sudo su - mks
cd /var/www/mirai-knowledge-system/backend

# Gunicorn設定ファイルを作成
cat > gunicorn_config.py << 'EOF'
"""
Gunicorn設定ファイル（本番環境用）
"""
import os
import multiprocessing

# サーバーソケット
bind = os.environ.get('MKS_GUNICORN_BIND', '127.0.0.1:8000')
backlog = 2048

# ワーカープロセス
workers = int(os.environ.get('MKS_GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get('MKS_GUNICORN_WORKER_CLASS', 'sync')
threads = int(os.environ.get('MKS_GUNICORN_THREADS', 2))
worker_connections = 1000
max_requests = 1000  # メモリリーク対策
max_requests_jitter = 50
timeout = int(os.environ.get('MKS_GUNICORN_TIMEOUT', 30))
graceful_timeout = int(os.environ.get('MKS_GUNICORN_GRACEFUL_TIMEOUT', 30))
keepalive = int(os.environ.get('MKS_GUNICORN_KEEPALIVE', 5))

# プロセス名
proc_name = 'mirai-knowledge-system'

# ログ
accesslog = '/var/log/mirai-knowledge-system/access.log'
errorlog = '/var/log/mirai-knowledge-system/error.log'
loglevel = os.environ.get('MKS_LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# セキュリティ
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# デーモンモード（systemdで管理する場合はFalse）
daemon = False
pidfile = '/var/run/mirai-knowledge-system/gunicorn.pid'
user = 'mks'
group = 'mks'
umask = 0o007

# SSL（Nginx経由の場合は不要）
# certfile = os.environ.get('MKS_SSL_CERT_PATH')
# keyfile = os.environ.get('MKS_SSL_KEY_PATH')

# ワーカープロセスのフック
def on_starting(server):
    """サーバー起動時"""
    server.log.info("Gunicorn starting...")

def on_reload(server):
    """リロード時"""
    server.log.info("Gunicorn reloading...")

def when_ready(server):
    """準備完了時"""
    server.log.info("Gunicorn ready. Listening on: %s", bind)

def worker_int(worker):
    """ワーカー中断時"""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """ワーカー異常終了時"""
    worker.log.info("Worker received SIGABRT signal")
EOF
```

### 6.2 Gunicorn動作確認

```bash
# 仮想環境を有効化
source venv/bin/activate

# 環境変数を読み込み
set -a
source .env.production
set +a

# Gunicornを起動（テスト）
gunicorn --config gunicorn_config.py app_v2:app

# 別のターミナルで動作確認
# curl http://127.0.0.1:8000/api/v1/health

# Ctrl+Cで停止
```

---

## 7. systemdサービス設定

### 7.1 PIDファイル用ディレクトリの作成

```bash
# 元のユーザーに戻る
exit

# ランタイムディレクトリを作成
sudo mkdir -p /var/run/mirai-knowledge-system
sudo chown mks:mks /var/run/mirai-knowledge-system
```

### 7.2 systemdサービスファイルの作成

```bash
sudo nano /etc/systemd/system/mirai-knowledge-system.service
```

以下の内容を記述:

```ini
[Unit]
Description=Mirai Knowledge System - 建設土木ナレッジシステム
After=network.target

[Service]
Type=notify
User=mks
Group=mks
WorkingDirectory=/var/www/mirai-knowledge-system/backend
Environment="PATH=/var/www/mirai-knowledge-system/backend/venv/bin"
EnvironmentFile=/var/www/mirai-knowledge-system/backend/.env.production

# Gunicorn起動コマンド
ExecStart=/var/www/mirai-knowledge-system/backend/venv/bin/gunicorn \
    --config /var/www/mirai-knowledge-system/backend/gunicorn_config.py \
    app_v2:app

# リロード時
ExecReload=/bin/kill -s HUP $MAINPID

# グレースフルシャットダウン
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

# 再起動設定
Restart=on-failure
RestartSec=10
StartLimitInterval=600
StartLimitBurst=5

# セキュリティ設定
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/mirai-knowledge-system /var/log/mirai-knowledge-system /var/run/mirai-knowledge-system
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictNamespaces=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# リソース制限
LimitNOFILE=65535
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### 7.3 systemdサービスの有効化

```bash
# systemdデーモンをリロード
sudo systemctl daemon-reload

# サービスを有効化（自動起動）
sudo systemctl enable mirai-knowledge-system.service

# サービスを起動
sudo systemctl start mirai-knowledge-system.service

# ステータス確認
sudo systemctl status mirai-knowledge-system.service
```

### 7.4 tmpfilesの設定（再起動時のディレクトリ復元）

```bash
sudo nano /etc/tmpfiles.d/mirai-knowledge-system.conf
```

以下の内容を記述:

```
d /var/run/mirai-knowledge-system 0755 mks mks -
```

---

## 8. 動作確認

### 8.1 ヘルスチェック

```bash
# ローカルからの確認
curl http://127.0.0.1:8000/api/v1/health

# Nginx経由での確認
curl http://localhost/health

# HTTPS経由での確認
curl https://api.example.com/health
```

### 8.2 API動作確認

```bash
# ログイン機能のテスト
curl -X POST https://api.example.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"your-password"}'

# ヘルスチェックエンドポイント
curl https://api.example.com/api/v1/health
```

### 8.3 ログ確認

```bash
# アプリケーションログ
sudo tail -f /var/log/mirai-knowledge-system/app.log

# Gunicorn アクセスログ
sudo tail -f /var/log/mirai-knowledge-system/access.log

# Gunicorn エラーログ
sudo tail -f /var/log/mirai-knowledge-system/error.log

# Nginx アクセスログ
sudo tail -f /var/log/nginx/mirai-knowledge-access.log

# Nginx エラーログ
sudo tail -f /var/log/nginx/mirai-knowledge-error.log

# systemdジャーナル
sudo journalctl -u mirai-knowledge-system.service -f
```

### 8.4 SSL証明書の確認

```bash
# 証明書情報の表示
openssl s_client -connect api.example.com:443 -servername api.example.com < /dev/null

# 証明書の有効期限確認
echo | openssl s_client -connect api.example.com:443 -servername api.example.com 2>/dev/null | \
    openssl x509 -noout -dates
```

### 8.5 SSL Labsでのテスト

ブラウザで以下のURLにアクセスし、SSL設定を検証:

```
https://www.ssllabs.com/ssltest/analyze.html?d=api.example.com
```

目標: A+評価

---

## 9. セキュリティチェックリスト

### 9.1 秘密鍵の保護

- [ ] `.env.production` のパーミッションが `600` になっている
- [ ] `.env.production` が Git に含まれていない（`.gitignore` で除外）
- [ ] 強力な秘密鍵（32文字以上）を使用している
- [ ] SSL証明書の秘密鍵のパーミッションが `600` になっている
- [ ] 秘密鍵がバックアップされている（安全な場所に）

```bash
# 確認コマンド
ls -la /var/www/mirai-knowledge-system/backend/.env.production
ls -la /etc/letsencrypt/live/api.example.com/privkey.pem
```

### 9.2 ファイアウォール設定

- [ ] 必要なポートのみ開放されている（22, 80, 443）
- [ ] SSH接続が鍵認証のみになっている
- [ ] rootログインが無効化されている
- [ ] fail2banがインストール・設定されている

```bash
# UFW確認
sudo ufw status verbose

# fail2banのインストール（推奨）
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 9.3 HTTPS強制

- [ ] HTTPからHTTPSへのリダイレクトが機能している
- [ ] HSTS ヘッダーが有効になっている
- [ ] SSL/TLS バージョンが TLS 1.2 以上のみ
- [ ] 弱い暗号スイートが無効化されている

```bash
# HTTPSリダイレクトのテスト
curl -I http://api.example.com

# HSTSヘッダーの確認
curl -I https://api.example.com | grep Strict-Transport-Security
```

### 9.4 セキュリティヘッダー確認

```bash
# セキュリティヘッダーの確認
curl -I https://api.example.com/api/v1/health

# 必須ヘッダー:
# - Strict-Transport-Security
# - X-Frame-Options: DENY
# - X-Content-Type-Options: nosniff
# - X-XSS-Protection: 1; mode=block
# - Referrer-Policy
# - Content-Security-Policy
# - Permissions-Policy
```

オンラインツールでの確認:
- [Security Headers](https://securityheaders.com/?q=api.example.com)
- 目標: A+評価

### 9.5 アプリケーションセキュリティ

- [ ] CORS設定が適切（必要なオリジンのみ許可）
- [ ] レート制限が有効になっている
- [ ] JWT トークンの有効期限が適切（1時間以内）
- [ ] CSRF保護が有効になっている
- [ ] SQLインジェクション対策がされている
- [ ] XSS対策がされている

### 9.6 システムセキュリティ

- [ ] OS とパッケージが最新状態
- [ ] 不要なサービスが停止されている
- [ ] SELinux または AppArmor が有効（推奨）
- [ ] 定期的なセキュリティアップデートが設定されている

```bash
# 自動セキュリティアップデートの設定（Ubuntu）
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 10. 運用手順

### 10.1 サーバー起動/停止/再起動

```bash
# サービスの起動
sudo systemctl start mirai-knowledge-system

# サービスの停止
sudo systemctl stop mirai-knowledge-system

# サービスの再起動
sudo systemctl restart mirai-knowledge-system

# 設定のリロード（ダウンタイムなし）
sudo systemctl reload mirai-knowledge-system

# サービスのステータス確認
sudo systemctl status mirai-knowledge-system
```

### 10.2 Nginx起動/停止/再起動

```bash
# Nginxの起動
sudo systemctl start nginx

# Nginxの停止
sudo systemctl stop nginx

# Nginxの再起動
sudo systemctl restart nginx

# 設定のリロード（ダウンタイムなし）
sudo systemctl reload nginx

# 設定テスト
sudo nginx -t
```

### 10.3 ログ確認

```bash
# アプリケーションログ（リアルタイム）
sudo journalctl -u mirai-knowledge-system -f

# アプリケーションログ（直近100行）
sudo journalctl -u mirai-knowledge-system -n 100

# 期間指定でログ確認
sudo journalctl -u mirai-knowledge-system --since "2025-01-01" --until "2025-01-02"

# エラーのみ表示
sudo journalctl -u mirai-knowledge-system -p err

# Gunicornログ
sudo tail -f /var/log/mirai-knowledge-system/error.log

# Nginxログ
sudo tail -f /var/log/nginx/mirai-knowledge-error.log
```

### 10.4 SSL証明書更新

```bash
# 証明書の更新（自動）
sudo certbot renew

# 証明書の更新（強制）
sudo certbot renew --force-renewal

# 更新後のNginxリロード
sudo systemctl reload nginx

# 証明書の有効期限確認
sudo certbot certificates
```

### 10.5 アプリケーション更新

```bash
# mksユーザーに切り替え
sudo su - mks
cd /var/www/mirai-knowledge-system/backend

# 仮想環境を有効化
source venv/bin/activate

# 最新コードを取得
git pull origin main

# 依存関係を更新
pip install -r requirements.txt --upgrade

# 元のユーザーに戻る
exit

# サービスを再起動
sudo systemctl restart mirai-knowledge-system

# ステータス確認
sudo systemctl status mirai-knowledge-system
```

### 10.6 バックアップ

#### データベース・ファイルのバックアップ

```bash
# バックアップスクリプトの作成
sudo nano /usr/local/bin/backup-mks.sh
```

```bash
#!/bin/bash
# 建設土木ナレッジシステム バックアップスクリプト

BACKUP_DIR="/var/backups/mirai-knowledge-system"
DATE=$(date +%Y%m%d_%H%M%S)
DATA_DIR="/var/lib/mirai-knowledge-system/data"

# バックアップディレクトリの作成
mkdir -p "$BACKUP_DIR"

# データディレクトリのバックアップ
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" -C "$DATA_DIR" .

# 環境変数のバックアップ（秘密鍵を含むので注意）
cp /var/www/mirai-knowledge-system/backend/.env.production \
   "$BACKUP_DIR/env_$DATE.backup"

# 古いバックアップを削除（30日以上前）
find "$BACKUP_DIR" -name "data_*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "env_*.backup" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# 実行権限を付与
sudo chmod +x /usr/local/bin/backup-mks.sh

# cronで定期バックアップ（毎日深夜2時）
echo "0 2 * * * root /usr/local/bin/backup-mks.sh" | sudo tee /etc/cron.d/mks-backup

# バックアップディレクトリの権限設定
sudo chmod 700 /var/backups/mirai-knowledge-system
```

#### 復元手順

```bash
# データの復元
sudo tar -xzf /var/backups/mirai-knowledge-system/data_YYYYMMDD_HHMMSS.tar.gz \
    -C /var/lib/mirai-knowledge-system/data/

# 権限の修正
sudo chown -R mks:mks /var/lib/mirai-knowledge-system/data

# サービスの再起動
sudo systemctl restart mirai-knowledge-system
```

### 10.7 監視設定

#### ヘルスチェック監視

```bash
# 簡易監視スクリプト
cat > /usr/local/bin/check-mks-health.sh << 'EOF'
#!/bin/bash
ENDPOINT="https://api.example.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$ENDPOINT")

if [ "$RESPONSE" != "200" ]; then
    echo "MKS Health Check Failed: HTTP $RESPONSE"
    # アラート送信（メール、Slackなど）
    # mail -s "MKS Health Check Failed" admin@example.com
    exit 1
else
    echo "MKS Health Check OK"
    exit 0
fi
EOF

sudo chmod +x /usr/local/bin/check-mks-health.sh

# cronで5分ごとにチェック
echo "*/5 * * * * root /usr/local/bin/check-mks-health.sh" | sudo tee /etc/cron.d/mks-health-check
```

---

## 11. トラブルシューティング

### 11.1 サービスが起動しない

#### 症状
```bash
sudo systemctl status mirai-knowledge-system
# Status: failed
```

#### 確認手順

```bash
# 1. ログを確認
sudo journalctl -u mirai-knowledge-system -n 50

# 2. 環境変数を確認
sudo -u mks bash -c 'source /var/www/mirai-knowledge-system/backend/.env.production && env | grep MKS_'

# 3. Pythonアプリケーションを手動起動
sudo su - mks
cd /var/www/mirai-knowledge-system/backend
source venv/bin/activate
source .env.production
python3 app_v2.py  # エラーメッセージを確認
```

#### よくある原因

1. **環境変数が設定されていない**
   ```bash
   # .env.production を確認
   cat /var/www/mirai-knowledge-system/backend/.env.production
   ```

2. **依存関係が不足**
   ```bash
   sudo su - mks
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **ファイルパーミッションの問題**
   ```bash
   sudo chown -R mks:mks /var/www/mirai-knowledge-system
   sudo chown -R mks:mks /var/lib/mirai-knowledge-system
   sudo chown -R mks:mks /var/log/mirai-knowledge-system
   ```

### 11.2 502 Bad Gateway エラー

#### 症状
ブラウザで「502 Bad Gateway」が表示される

#### 確認手順

```bash
# 1. Gunicornが起動しているか確認
sudo systemctl status mirai-knowledge-system

# 2. ポート8000でリスニングしているか確認
sudo ss -tlnp | grep 8000

# 3. Nginxエラーログを確認
sudo tail -f /var/log/nginx/mirai-knowledge-error.log

# 4. upstream接続を確認
curl http://127.0.0.1:8000/api/v1/health
```

#### 解決方法

```bash
# Gunicornを再起動
sudo systemctl restart mirai-knowledge-system

# Nginxを再起動
sudo systemctl restart nginx
```

### 11.3 SSL証明書エラー

#### 症状
ブラウザで「この接続ではプライバシーが保護されません」と表示される

#### 確認手順

```bash
# 証明書の確認
sudo certbot certificates

# 証明書ファイルの存在確認
ls -la /etc/letsencrypt/live/api.example.com/

# 証明書の有効期限確認
openssl x509 -in /etc/letsencrypt/live/api.example.com/fullchain.pem -noout -dates

# Nginx設定の確認
sudo nginx -t
```

#### 解決方法

```bash
# 証明書の更新
sudo certbot renew --force-renewal

# Nginxのリロード
sudo systemctl reload nginx
```

### 11.4 認証エラー（401 Unauthorized）

#### 症状
APIリクエストで401エラーが返される

#### 確認手順

```bash
# JWTトークンの確認
# ブラウザの開発者ツールで Authorization ヘッダーを確認

# ログでエラーを確認
sudo journalctl -u mirai-knowledge-system | grep -i auth

# 環境変数を確認
sudo -u mks bash -c 'source .env.production && echo $MKS_JWT_SECRET_KEY'
```

#### 解決方法

1. JWTトークンの再発行
2. 秘密鍵の確認と修正
3. サービスの再起動

### 11.5 パフォーマンス問題

#### 症状
応答が遅い、タイムアウトが発生する

#### 確認手順

```bash
# CPU使用率確認
top -u mks

# メモリ使用量確認
free -h
ps aux | grep gunicorn

# ディスクI/O確認
iostat -x 1

# アクセスログで遅いリクエストを確認
sudo cat /var/log/mirai-knowledge-system/access.log | awk '{if ($NF > 1000) print}'
```

#### 解決方法

「12. パフォーマンスチューニング」を参照

---

## 12. パフォーマンスチューニング

### 12.1 Gunicornワーカー設定

```bash
# 推奨ワーカー数の計算
# ワーカー数 = (2 × CPUコア数) + 1

# CPUコア数を確認
nproc

# 例: 4コアの場合
# ワーカー数 = (2 × 4) + 1 = 9
```

`.env.production` を編集:

```bash
MKS_GUNICORN_WORKERS=9
MKS_GUNICORN_WORKER_CLASS=sync  # またはgevent
MKS_GUNICORN_THREADS=2
```

### 12.2 非同期ワーカーの使用

I/O待ちが多い場合は非同期ワーカーを使用:

```bash
# geventのインストール
sudo su - mks
source venv/bin/activate
pip install gevent

# .env.production を編集
MKS_GUNICORN_WORKER_CLASS=gevent
MKS_GUNICORN_WORKERS=4
```

### 12.3 Nginx接続プーリング

`nginx.conf` の upstream ブロックに追加:

```nginx
upstream mirai_knowledge_backend {
    server 127.0.0.1:8000;
    keepalive 64;  # 接続プールサイズを増やす
}
```

### 12.4 GZip圧縮の最適化

`/etc/nginx/nginx.conf` を編集:

```nginx
http {
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;  # 圧縮レベル（1-9、推奨: 6）
    gzip_min_length 1000;
    gzip_types
        text/plain
        text/css
        text/xml
        application/json
        application/javascript
        application/xml+rss
        application/rss+xml
        application/atom+xml
        image/svg+xml
        text/javascript;
}
```

### 12.5 静的ファイルキャッシュ

`nginx.conf` のサーバーブロックに追加:

```nginx
location /static/ {
    alias /var/www/mirai-knowledge-system/webui/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";

    # Open File Cache
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

### 12.6 カーネルパラメータのチューニング

```bash
# /etc/sysctl.conf を編集
sudo nano /etc/sysctl.conf
```

以下を追加:

```
# ネットワークパフォーマンス
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30

# ファイルディスクリプタ
fs.file-max = 65535
```

設定を反映:

```bash
sudo sysctl -p
```

### 12.7 ファイルディスクリプタ制限の引き上げ

```bash
# /etc/security/limits.conf を編集
sudo nano /etc/security/limits.conf
```

以下を追加:

```
mks soft nofile 65535
mks hard nofile 65535
```

### 12.8 Redis導入（レート制限用）

```bash
# Redisのインストール
sudo apt install redis-server

# Redisの起動
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Pythonクライアントのインストール
sudo su - mks
source venv/bin/activate
pip install redis

# .env.production を編集
MKS_REDIS_URL="redis://localhost:6379/0"
```

### 12.9 ログローテーション設定

```bash
# ログローテーション設定
sudo nano /etc/logrotate.d/mirai-knowledge-system
```

以下を記述:

```
/var/log/mirai-knowledge-system/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 mks mks
    sharedscripts
    postrotate
        systemctl reload mirai-knowledge-system > /dev/null 2>&1 || true
    endscript
}
```

### 12.10 パフォーマンス監視

```bash
# リアルタイムパフォーマンス監視
htop

# Gunicornプロセスの確認
ps aux | grep gunicorn

# リクエスト/秒の確認
tail -f /var/log/mirai-knowledge-system/access.log | pv -l -i 1 > /dev/null

# 応答時間の統計
awk '{print $NF}' /var/log/mirai-knowledge-system/access.log | \
    awk '{s+=$1; c++} END {print "Avg:", s/c "ms"}'
```

---

## 付録

### A. 環境変数一覧

| 環境変数 | 必須 | デフォルト | 説明 |
|----------|------|-----------|------|
| `MKS_ENV` | Yes | - | 環境（production/development） |
| `MKS_SECRET_KEY` | Yes | - | アプリケーション秘密鍵 |
| `MKS_JWT_SECRET_KEY` | Yes | - | JWT秘密鍵 |
| `MKS_CORS_ORIGINS` | Yes | - | 許可オリジン（カンマ区切り） |
| `MKS_DATA_DIR` | No | /var/lib/mirai-knowledge-system/data | データディレクトリ |
| `MKS_LOG_FILE` | No | /var/log/mirai-knowledge-system/app.log | ログファイルパス |
| `MKS_LOG_LEVEL` | No | INFO | ログレベル |
| `MKS_GUNICORN_WORKERS` | No | CPU×2+1 | ワーカー数 |
| `MKS_GUNICORN_BIND` | No | 127.0.0.1:8000 | バインドアドレス |

### B. ポート一覧

| ポート | プロトコル | 用途 | 公開 |
|--------|-----------|------|------|
| 22 | TCP | SSH | 外部 |
| 80 | TCP | HTTP（リダイレクト用） | 外部 |
| 443 | TCP | HTTPS | 外部 |
| 8000 | TCP | Gunicorn（内部） | 内部のみ |

### C. ディレクトリ構造

```
/var/www/mirai-knowledge-system/
├── backend/
│   ├── venv/                          # Python仮想環境
│   ├── app_v2.py                      # アプリケーションエントリーポイント
│   ├── .env.production                # 本番環境設定（権限: 600）
│   ├── gunicorn_config.py             # Gunicorn設定
│   └── requirements.txt               # Python依存関係

/var/lib/mirai-knowledge-system/
└── data/                              # アプリケーションデータ
    ├── knowledge/
    ├── analysis/
    └── users/

/var/log/mirai-knowledge-system/
├── app.log                            # アプリケーションログ
├── access.log                         # Gunicornアクセスログ
└── error.log                          # Gunicornエラーログ

/etc/nginx/
├── sites-available/
│   └── mirai-knowledge-system         # Nginx設定
└── sites-enabled/
    └── mirai-knowledge-system -> ../sites-available/mirai-knowledge-system

/etc/letsencrypt/live/api.example.com/
├── fullchain.pem                      # SSL証明書
└── privkey.pem                        # SSL秘密鍵（権限: 600）
```

### D. 参考リンク

- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
- [systemd Documentation](https://www.freedesktop.org/software/systemd/man/)

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2025-12-27 | 1.0.0 | 初版作成 |

---

**注意事項**:
- 本番環境への展開前に、必ずテスト環境で動作確認を行ってください
- 秘密鍵は絶対にGitリポジトリにコミットしないでください
- セキュリティパッチは定期的に適用してください
- バックアップは定期的に取得し、復元テストも実施してください
