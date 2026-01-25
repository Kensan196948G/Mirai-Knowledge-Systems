# 本番環境移行チェックリスト

## 概要

このドキュメントは、建設土木ナレッジシステムを開発環境から本番環境へ移行する際の包括的なチェックリストです。各項目を順番に確認し、安全かつ確実に本番環境を構築してください。

## 移行前の準備

### 1. サーバー環境の確認

- [ ] **OS環境**
  - Ubuntu 20.04 LTS以上、またはDebian 11以上
  - 最新のセキュリティパッチが適用されている
  - タイムゾーンが正しく設定されている（JST推奨）

- [ ] **ハードウェアリソース**
  - CPU: 2コア以上
  - メモリ: 4GB以上（推奨: 8GB）
  - ディスク: 20GB以上の空き容量
  - ネットワーク: 固定IPアドレスまたはドメイン名

- [ ] **必要なソフトウェア**
  - Python 3.9以上
  - Nginx 1.18以上
  - Git
  - certbot（Let's Encrypt用）

### 2. ドメイン・DNS設定

- [ ] **ドメイン取得**
  - 本番用ドメイン名の取得完了
  - APIサブドメイン設定（例: api.example.com）

- [ ] **DNS設定**
  - Aレコード設定（ドメイン → サーバーIP）
  - DNS伝播の確認（`nslookup api.example.com`）
  - TTL設定の確認（移行時は短めに設定）

### 3. セキュリティ準備

- [ ] **秘密鍵の生成**
  ```bash
  # アプリケーション秘密鍵
  python3 -c "import secrets; print(secrets.token_hex(32))"

  # JWT秘密鍵
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] **SSH設定**
  - SSH公開鍵認証の設定
  - パスワード認証の無効化
  - ポート番号の変更（オプション）

- [ ] **ファイアウォール設定**
  ```bash
  sudo ufw allow 22/tcp    # SSH
  sudo ufw allow 80/tcp    # HTTP
  sudo ufw allow 443/tcp   # HTTPS
  sudo ufw enable
  ```

## 環境構築フェーズ

### 4. アプリケーションのデプロイ

- [ ] **リポジトリのクローン**
  ```bash
  cd /opt
  sudo git clone https://github.com/your-org/mirai-knowledge-systems.git
  cd mirai-knowledge-systems/backend
  ```

- [ ] **Python仮想環境の作成**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- [ ] **ディレクトリ作成**
  ```bash
  sudo mkdir -p /var/lib/mirai-knowledge-system/data
  sudo mkdir -p /var/log/mirai-knowledge-system
  sudo chown -R $USER:$USER /var/lib/mirai-knowledge-system
  sudo chown -R $USER:$USER /var/log/mirai-knowledge-system
  ```

### 5. 環境変数設定

- [ ] **.env.production ファイルの作成**
  ```bash
  cp .env.production.example .env.production
  chmod 600 .env.production
  ```

- [ ] **必須環境変数の設定**
  - `MKS_SECRET_KEY`: 生成した秘密鍵
  - `MKS_JWT_SECRET_KEY`: 生成したJWT秘密鍵
  - `MKS_CORS_ORIGINS`: フロントエンドのURL（https://example.com）
  - `MKS_FORCE_HTTPS`: true
  - `MKS_TRUST_PROXY_HEADERS`: true（Nginx経由の場合）

- [ ] **オプション環境変数の確認**
  - `MKS_GUNICORN_WORKERS`: CPUコア数 * 2 + 1
  - `MKS_GUNICORN_THREADS`: 2
  - `MKS_GUNICORN_BIND`: 127.0.0.1:8000
  - `MKS_LOG_LEVEL`: INFO

- [ ] **環境変数の検証**
  ```bash
  ./run_production.sh check
  ```

### 6. SSL証明書のセットアップ

- [ ] **Certbotのインストール**
  ```bash
  sudo apt update
  sudo apt install certbot python3-certbot-nginx
  ```

- [ ] **Let's Encrypt証明書の取得**
  ```bash
  sudo certbot certonly --nginx \
    -d api.example.com \
    --email admin@example.com \
    --agree-tos \
    --non-interactive
  ```

- [ ] **証明書の確認**
  ```bash
  sudo ls -la /etc/letsencrypt/live/api.example.com/
  # fullchain.pem と privkey.pem が存在することを確認
  ```

- [ ] **自動更新の設定**
  ```bash
  sudo certbot renew --dry-run
  # エラーが出ないことを確認
  ```

### 7. Nginx設定

- [ ] **Nginx設定ファイルの作成**
  ```bash
  sudo nano /etc/nginx/sites-available/mirai-knowledge-system
  ```

- [ ] **設定内容の記述**（下記のテンプレート参照）

- [ ] **シンボリックリンクの作成**
  ```bash
  sudo ln -s /etc/nginx/sites-available/mirai-knowledge-system \
             /etc/nginx/sites-enabled/
  ```

- [ ] **デフォルト設定の無効化**
  ```bash
  sudo rm /etc/nginx/sites-enabled/default
  ```

- [ ] **設定の検証**
  ```bash
  sudo nginx -t
  ```

- [ ] **Nginxの再起動**
  ```bash
  sudo systemctl restart nginx
  ```

#### Nginx設定テンプレート

```nginx
# HTTP → HTTPS リダイレクト
server {
    listen 80;
    listen [::]:80;
    server_name api.example.com;

    # Let's Encrypt証明書検証用
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # すべてのHTTPリクエストをHTTPSにリダイレクト
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS メインサーバー
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.example.com;

    # SSL証明書
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # SSL設定（Mozilla Modern Configuration）
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS（HTTP Strict Transport Security）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # ログ
    access_log /var/log/nginx/mirai-knowledge-system-access.log;
    error_log /var/log/nginx/mirai-knowledge-system-error.log;

    # リクエストサイズ制限
    client_max_body_size 10M;

    # Gunicornへプロキシ
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # タイムアウト設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # バッファリング設定
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # 静的ファイル（オプション）
    location /static/ {
        alias /opt/mirai-knowledge-systems/backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 8. データベース移行（オプション）

PostgreSQLを使用する場合:

- [ ] **PostgreSQLのインストール**
  ```bash
  sudo apt install postgresql postgresql-contrib
  ```

- [ ] **データベースとユーザーの作成**
  ```sql
  sudo -u postgres psql
  CREATE DATABASE mirai_knowledge;
  CREATE USER mks_user WITH PASSWORD 'secure_password';
  GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge TO mks_user;
  \q
  ```

- [ ] **環境変数の設定**
  ```bash
  # .env.production に追加
  MKS_DATABASE_URL=postgresql://mks_user:secure_password@localhost:5432/mirai_knowledge
  ```

- [ ] **初期データの移行**
  ```bash
  source venv/bin/activate
  python migrate_json_to_postgres.py
  ```

### 9. アプリケーションの起動

- [ ] **起動スクリプトの実行権限付与**
  ```bash
  chmod +x run_production.sh
  ```

- [ ] **設定チェック**
  ```bash
  ./run_production.sh check
  ```

- [ ] **アプリケーション起動**
  ```bash
  ./run_production.sh start
  ```

- [ ] **起動確認**
  ```bash
  ./run_production.sh status
  ```

- [ ] **ログ確認**
  ```bash
  tail -f logs/error.log
  tail -f logs/access.log
  ```

### 10. Systemdサービス化（オプション）

- [ ] **サービスファイルの作成**
  ```bash
  sudo nano /etc/systemd/system/mirai-knowledge-system.service
  ```

  ```ini
  [Unit]
  Description=Mirai Knowledge System API
  After=network.target

  [Service]
  Type=forking
  User=your-user
  Group=your-group
  WorkingDirectory=/opt/mirai-knowledge-systems/backend
  Environment="PATH=/opt/mirai-knowledge-systems/backend/venv/bin"
  EnvironmentFile=/opt/mirai-knowledge-systems/backend/.env.production
  ExecStart=/opt/mirai-knowledge-systems/backend/run_production.sh start
  ExecStop=/opt/mirai-knowledge-systems/backend/run_production.sh stop
  ExecReload=/opt/mirai-knowledge-systems/backend/run_production.sh reload
  PIDFile=/opt/mirai-knowledge-systems/backend/gunicorn.pid
  Restart=on-failure
  RestartSec=10

  [Install]
  WantedBy=multi-user.target
  ```

- [ ] **サービスの有効化と起動**
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable mirai-knowledge-system
  sudo systemctl start mirai-knowledge-system
  sudo systemctl status mirai-knowledge-system
  ```

## 動作確認フェーズ

### 11. エンドポイント疎通確認

- [ ] **ヘルスチェック**
  ```bash
  curl https://api.example.com/
  # 期待される応答: HTMLまたはJSON
  ```

- [ ] **ログイン機能**
  ```bash
  curl -X POST https://api.example.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"your-password"}'
  # 期待される応答: {"access_token": "...", "refresh_token": "..."}
  ```

- [ ] **認証付きエンドポイント**
  ```bash
  TOKEN="取得したアクセストークン"
  curl https://api.example.com/api/v1/auth/me \
    -H "Authorization: Bearer $TOKEN"
  # 期待される応答: ユーザー情報
  ```

- [ ] **知識記事取得**
  ```bash
  curl https://api.example.com/api/v1/knowledge \
    -H "Authorization: Bearer $TOKEN"
  # 期待される応答: 知識記事リスト
  ```

### 12. セキュリティ確認

- [ ] **HTTPS確認**
  ```bash
  curl -I http://api.example.com
  # 301リダイレクトが返ることを確認
  ```

- [ ] **SSL証明書の確認**
  ```bash
  openssl s_client -connect api.example.com:443 -servername api.example.com
  # 証明書チェーンが正しいことを確認
  ```

- [ ] **セキュリティヘッダーの確認**
  ```bash
  curl -I https://api.example.com
  # 以下のヘッダーが含まれることを確認:
  # - Strict-Transport-Security
  # - X-Frame-Options
  # - X-Content-Type-Options
  # - X-XSS-Protection
  ```

- [ ] **SSL Labs テスト**
  - https://www.ssllabs.com/ssltest/ でA以上の評価を確認

### 13. パフォーマンス確認

- [ ] **レスポンスタイム測定**
  ```bash
  time curl https://api.example.com/api/v1/knowledge \
    -H "Authorization: Bearer $TOKEN"
  # 2秒以内のレスポンスを確認
  ```

- [ ] **同時接続テスト**
  ```bash
  ab -n 100 -c 10 https://api.example.com/
  # エラーが発生しないことを確認
  ```

- [ ] **メモリ使用量確認**
  ```bash
  ./run_production.sh status
  # メモリ使用量が想定範囲内であることを確認
  ```

### 14. ログとモニタリング

- [ ] **アクセスログの確認**
  ```bash
  tail -f /var/log/nginx/mirai-knowledge-system-access.log
  ```

- [ ] **エラーログの確認**
  ```bash
  tail -f /var/log/nginx/mirai-knowledge-system-error.log
  tail -f /var/log/mirai-knowledge-system/app.log
  ```

- [ ] **ログローテーション設定**
  ```bash
  sudo nano /etc/logrotate.d/mirai-knowledge-system
  ```

  ```
  /var/log/mirai-knowledge-system/*.log {
      daily
      rotate 30
      compress
      delaycompress
      notifempty
      create 0640 your-user your-group
      sharedscripts
      postrotate
          systemctl reload mirai-knowledge-system > /dev/null 2>&1 || true
      endscript
  }
  ```

## 監視システム起動

### 15. 基本的な監視設定

- [ ] **Cronジョブによるヘルスチェック**
  ```bash
  crontab -e

  # 5分ごとにヘルスチェック
  */5 * * * * curl -f https://api.example.com/ || echo "Health check failed" | mail -s "API Down" admin@example.com
  ```

- [ ] **ディスク使用量監視**
  ```bash
  # 1日1回ディスク使用量を確認
  0 9 * * * df -h | grep -E '^/dev/' | awk '$5 > "80%" {print}' | mail -s "Disk Usage Alert" admin@example.com
  ```

- [ ] **SSL証明書有効期限監視**
  ```bash
  # 週1回証明書の有効期限を確認
  0 9 * * 1 certbot certificates | grep -A2 "Expiry Date" | mail -s "SSL Certificate Status" admin@example.com
  ```

### 16. オプション: Prometheusモニタリング

詳細は別途「運用マニュアル」を参照してください。

## バックアップ設定

### 17. データバックアップ

- [ ] **バックアップディレクトリの作成**
  ```bash
  sudo mkdir -p /var/backups/mirai-knowledge-system
  sudo chown $USER:$USER /var/backups/mirai-knowledge-system
  ```

- [ ] **バックアップスクリプトの作成**
  ```bash
  nano /opt/mirai-knowledge-systems/backend/backup.sh
  ```

  ```bash
  #!/bin/bash
  BACKUP_DIR="/var/backups/mirai-knowledge-system"
  DATA_DIR="/var/lib/mirai-knowledge-system/data"
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)

  # データディレクトリのバックアップ
  tar -czf "$BACKUP_DIR/data_$TIMESTAMP.tar.gz" -C "$DATA_DIR" .

  # PostgreSQLバックアップ（使用している場合）
  # pg_dump mirai_knowledge > "$BACKUP_DIR/db_$TIMESTAMP.sql"

  # 30日以前のバックアップを削除
  find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
  find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
  ```

- [ ] **スクリプトの実行権限付与**
  ```bash
  chmod +x /opt/mirai-knowledge-systems/backend/backup.sh
  ```

- [ ] **Cronジョブの設定**
  ```bash
  crontab -e

  # 毎日午前3時にバックアップ
  0 3 * * * /opt/mirai-knowledge-systems/backend/backup.sh
  ```

## 最終確認

### 18. チェックリスト総括

- [ ] すべてのエンドポイントが正常に動作している
- [ ] HTTPSが正しく機能し、HTTPはリダイレクトされる
- [ ] SSL証明書が有効で、自動更新が設定されている
- [ ] セキュリティヘッダーが適切に設定されている
- [ ] ログが正常に出力されている
- [ ] バックアップが正常に実行される
- [ ] 監視スクリプトが動作している
- [ ] 環境変数ファイル（.env.production）の権限が適切（600）
- [ ] サービスが自動起動するように設定されている

### 19. ドキュメント整備

- [ ] 本番環境の構成図を作成
- [ ] 環境変数一覧を別途安全に保管
- [ ] 緊急連絡先リストを作成
- [ ] 運用マニュアルを最新化

### 20. ロールバック計画

- [ ] 旧環境を一定期間保持（推奨: 1週間）
- [ ] ロールバック手順書の作成
- [ ] データベースの復元手順の確認
- [ ] DNS切り戻し手順の確認

## トラブルシューティング

### よくある問題と解決方法

#### 1. アプリケーションが起動しない

**症状**: `./run_production.sh start` でエラーが発生

**確認事項**:
- [ ] Python仮想環境が有効化されているか
- [ ] 必要なパッケージがすべてインストールされているか
- [ ] 環境変数が正しく設定されているか
- [ ] ポート8000が既に使用されていないか

**対処方法**:
```bash
# 仮想環境の確認
source venv/bin/activate
pip list

# ポート使用状況の確認
sudo lsof -i :8000

# 設定チェック
./run_production.sh check
```

#### 2. Nginxエラー（502 Bad Gateway）

**症状**: HTTPSでアクセスすると502エラー

**確認事項**:
- [ ] Gunicornが起動しているか
- [ ] Nginxの設定が正しいか
- [ ] ファイアウォールで8000番ポートがブロックされていないか

**対処方法**:
```bash
# Gunicornの状態確認
./run_production.sh status

# Nginxエラーログ確認
sudo tail -f /var/log/nginx/mirai-knowledge-system-error.log

# Nginx設定テスト
sudo nginx -t
```

#### 3. SSL証明書エラー

**症状**: HTTPSアクセス時に証明書エラー

**確認事項**:
- [ ] 証明書ファイルが存在するか
- [ ] Nginx設定の証明書パスが正しいか
- [ ] DNS設定が正しく伝播しているか

**対処方法**:
```bash
# 証明書の確認
sudo certbot certificates

# DNS確認
nslookup api.example.com

# 証明書の再取得
sudo certbot certonly --nginx -d api.example.com
```

#### 4. CORS エラー

**症状**: フロントエンドからのリクエストがCORSエラー

**確認事項**:
- [ ] `MKS_CORS_ORIGINS` に正しいURLが設定されているか
- [ ] HTTPSでアクセスしているか
- [ ] Nginxがプロキシヘッダーを正しく転送しているか

**対処方法**:
```bash
# 環境変数の確認
grep CORS_ORIGINS .env.production

# アプリケーションの再起動
./run_production.sh restart
```

## 付録

### A. 推奨されるサーバースペック

| 用途 | CPU | メモリ | ディスク |
|------|-----|--------|----------|
| 小規模（〜50ユーザー） | 2コア | 4GB | 20GB |
| 中規模（〜200ユーザー） | 4コア | 8GB | 50GB |
| 大規模（200ユーザー〜） | 8コア以上 | 16GB以上 | 100GB以上 |

### B. 関連ドキュメント

- [HTTPS移行ガイド](./05_HTTPS-Migration-Guide.md)
- [API仕様書](../08_API連携(Integrations)/03_API-Reference-Complete.md)
- [運用マニュアル](../11_運用(Operations)/01_Operations-Manual.md)

### C. 参考リンク

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Flask Production Best Practices](https://flask.palletsprojects.com/en/latest/deploying/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)

---

**最終更新日**: 2024年12月27日
**バージョン**: 1.0.0
