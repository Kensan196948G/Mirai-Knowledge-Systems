# HTTPS移行ガイド

## 概要

このガイドは、建設土木ナレッジシステムAPIをHTTPからHTTPSへ移行するための詳細な手順書です。Let's Encryptを使用した無料SSL証明書の取得から、Nginxでの設定、セキュリティ強化まで、本番環境でHTTPSを安全に運用するために必要なすべての手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [Let's Encrypt証明書の取得](#lets-encrypt証明書の取得)
3. [Nginxの設定](#nginxの設定)
4. [HTTPSリダイレクト設定](#httpsリダイレクト設定)
5. [セキュリティ強化](#セキュリティ強化)
6. [証明書の自動更新](#証明書の自動更新)
7. [動作確認](#動作確認)
8. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必要なもの

- [ ] Ubuntu 20.04 LTS以上、またはDebian 11以上のサーバー
- [ ] ドメイン名（例: api.example.com）
- [ ] DNSレコードが正しく設定されている（ドメイン → サーバーIP）
- [ ] ポート80と443がファイアウォールで開放されている
- [ ] rootまたはsudo権限を持つユーザー

### ドメインのDNS設定確認

移行前に、ドメインが正しくサーバーIPアドレスを指していることを確認してください。

```bash
# DNSの確認
nslookup api.example.com

# または
dig api.example.com

# 期待される結果: サーバーのIPアドレスが表示される
```

DNSが正しく設定されていない場合、Let's Encryptの検証が失敗します。DNS設定後、伝播に最大48時間かかる場合があります（通常は数分〜数時間）。

### ファイアウォール設定確認

```bash
# ファイアウォールの状態確認
sudo ufw status

# 必要なポートが開放されていることを確認
# 80/tcp  ALLOW  Anywhere
# 443/tcp ALLOW  Anywhere
```

ポートが開放されていない場合:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

---

## Let's Encrypt証明書の取得

### 1. Certbotのインストール

Certbotは、Let's Encryptから無料のSSL/TLS証明書を自動取得・更新するためのツールです。

#### Ubuntu/Debian の場合

```bash
# パッケージリストの更新
sudo apt update

# Certbotとnginxプラグインのインストール
sudo apt install certbot python3-certbot-nginx -y

# インストール確認
certbot --version
# 期待される出力: certbot 1.x.x
```

#### その他のディストリビューションの場合

```bash
# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx

# Snapを使用する場合（推奨される最新の方法）
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### 2. 証明書の取得

#### 方法1: Nginx自動設定（推奨）

Certbotがnginxの設定を自動的に更新します。

```bash
sudo certbot --nginx -d api.example.com
```

実行すると、以下の質問が表示されます:

1. **メールアドレスの入力**
   ```
   Enter email address (used for urgent renewal and security notices):
   ```
   管理者のメールアドレスを入力してください。証明書の有効期限通知などが送られます。

2. **利用規約への同意**
   ```
   Please read the Terms of Service at https://letsencrypt.org/documents/LE-SA-v1.3-September-21-2022.pdf
   (A)gree/(C)ancel:
   ```
   `A` を入力して同意します。

3. **Electronic Frontier Foundation (EFF)からのメール**
   ```
   Would you be willing to share your email address with EFF?
   (Y)es/(N)o:
   ```
   任意です。`N` で問題ありません。

4. **HTTPSリダイレクトの設定**
   ```
   Please choose whether or not to redirect HTTP traffic to HTTPS
   1: No redirect
   2: Redirect - Make all requests redirect to secure HTTPS access
   Select the appropriate number [1-2]:
   ```
   `2` を選択してHTTPSリダイレクトを有効にします（推奨）。

#### 方法2: 証明書のみ取得（手動設定）

Nginxの設定を自分で行いたい場合:

```bash
sudo certbot certonly --nginx -d api.example.com
```

または、Nginxを使わない方法:

```bash
sudo certbot certonly --standalone -d api.example.com
```

**注意**: standalone モードを使用する場合、ポート80でNginxが動作していないことを確認してください。

```bash
# Nginxを一時停止
sudo systemctl stop nginx

# 証明書取得
sudo certbot certonly --standalone -d api.example.com

# Nginxを再起動
sudo systemctl start nginx
```

#### 複数ドメインの証明書取得

複数のドメイン/サブドメインを1つの証明書でカバーする場合:

```bash
sudo certbot --nginx \
  -d api.example.com \
  -d www.api.example.com
```

### 3. 証明書ファイルの確認

証明書が正常に取得されると、以下の場所に保存されます:

```bash
# 証明書の場所を確認
sudo ls -la /etc/letsencrypt/live/api.example.com/

# 主要なファイル:
# cert.pem       - サーバー証明書
# chain.pem      - 中間証明書
# fullchain.pem  - cert.pem + chain.pem（Nginxで使用）
# privkey.pem    - 秘密鍵（厳重に保護）
```

証明書の詳細情報を確認:

```bash
sudo certbot certificates
```

出力例:
```
Certificate Name: api.example.com
  Domains: api.example.com
  Expiry Date: 2025-03-27 12:00:00+00:00 (VALID: 89 days)
  Certificate Path: /etc/letsencrypt/live/api.example.com/fullchain.pem
  Private Key Path: /etc/letsencrypt/live/api.example.com/privkey.pem
```

---

## Nginxの設定

### 1. Nginx設定ファイルの作成

Certbotが自動設定した場合でも、設定を最適化するために手動で編集することを推奨します。

```bash
# 設定ファイルを作成/編集
sudo nano /etc/nginx/sites-available/mirai-knowledge-system
```

### 2. 推奨されるNginx設定

以下の設定をコピーして、ドメイン名を実際のものに置き換えてください。

```nginx
# HTTP → HTTPS リダイレクト
server {
    listen 80;
    listen [::]:80;
    server_name api.example.com;

    # Let's Encrypt証明書検証用（ACMEチャレンジ）
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        try_files $uri =404;
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

    # ============================================================
    # SSL証明書設定
    # ============================================================

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # SSL設定（Mozilla Modern Configuration）
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # SSL セッション設定（パフォーマンス最適化）
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # OCSP Stapling（証明書検証の高速化）
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/api.example.com/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # ============================================================
    # セキュリティヘッダー
    # ============================================================

    # HSTS（HTTP Strict Transport Security）
    # ブラウザに常にHTTPSを使用するよう指示
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # クリックジャッキング対策
    add_header X-Frame-Options "SAMEORIGIN" always;

    # MIME タイプスニッフィング防止
    add_header X-Content-Type-Options "nosniff" always;

    # XSS 保護
    add_header X-XSS-Protection "1; mode=block" always;

    # リファラーポリシー
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Content Security Policy（オプション、厳しすぎる場合はコメントアウト）
    # add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # ============================================================
    # ログ設定
    # ============================================================

    access_log /var/log/nginx/mirai-knowledge-system-access.log;
    error_log /var/log/nginx/mirai-knowledge-system-error.log;

    # ============================================================
    # リクエスト設定
    # ============================================================

    # リクエストサイズ制限（10MB）
    client_max_body_size 10M;

    # タイムアウト設定
    client_body_timeout 60s;
    client_header_timeout 60s;

    # ============================================================
    # Gunicornへのプロキシ設定
    # ============================================================

    location / {
        # バックエンドサーバーへプロキシ
        proxy_pass http://127.0.0.1:8000;

        # プロキシヘッダーの設定
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # WebSocket サポート（将来的に使用する場合）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # タイムアウト設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # バッファリング設定
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;

        # エラーページ処理
        proxy_intercept_errors on;
    }

    # ============================================================
    # 静的ファイル配信（オプション）
    # ============================================================

    location /static/ {
        alias /opt/mirai-knowledge-systems/backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # ============================================================
    # エラーページ（オプション）
    # ============================================================

    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
        internal;
    }
}
```

### 3. 設定の有効化

```bash
# シンボリックリンクを作成（まだの場合）
sudo ln -s /etc/nginx/sites-available/mirai-knowledge-system \
           /etc/nginx/sites-enabled/

# デフォルト設定を無効化（重複を避けるため）
sudo rm -f /etc/nginx/sites-enabled/default

# 設定ファイルの文法チェック
sudo nginx -t

# 期待される出力:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 4. Nginxの再起動

```bash
# 設定をリロード（ダウンタイムなし）
sudo systemctl reload nginx

# または、完全再起動
sudo systemctl restart nginx

# ステータス確認
sudo systemctl status nginx
```

---

## HTTPSリダイレクト設定

### アプリケーション側の設定

Nginxだけでなく、アプリケーション側でもHTTPSを強制する設定を行います。

#### 環境変数の設定

`.env.production` ファイルを編集:

```bash
nano /opt/mirai-knowledge-systems/backend/.env.production
```

以下の変数を設定:

```bash
# HTTPS強制
MKS_FORCE_HTTPS=true

# リバースプロキシのヘッダーを信頼
MKS_TRUST_PROXY_HEADERS=true

# HSTS設定
MKS_HSTS_ENABLED=true
MKS_HSTS_MAX_AGE=31536000
MKS_HSTS_INCLUDE_SUBDOMAINS=true
MKS_HSTS_PRELOAD=false  # 慎重に使用
```

#### アプリケーションの再起動

```bash
cd /opt/mirai-knowledge-systems/backend
./run_production.sh restart
```

---

## セキュリティ強化

### 1. SSL設定の最適化

#### Diffie-Hellman パラメータの生成（セキュリティ強化）

```bash
# DHパラメータ生成（数分かかります）
sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048

# より強力な4096ビット（推奨だが生成に時間がかかる）
# sudo openssl dhparam -out /etc/nginx/dhparam.pem 4096
```

Nginx設定に追加:

```nginx
server {
    listen 443 ssl http2;
    # ... 既存の設定 ...

    # DHパラメータの指定
    ssl_dhparam /etc/nginx/dhparam.pem;
}
```

### 2. ファイアウォール設定の見直し

HTTPポート（80）は証明書更新のために開けておく必要があります:

```bash
sudo ufw status numbered

# 期待される設定:
# [1] 22/tcp     ALLOW IN    Anywhere  (SSH)
# [2] 80/tcp     ALLOW IN    Anywhere  (HTTP - 証明書更新用)
# [3] 443/tcp    ALLOW IN    Anywhere  (HTTPS)
```

### 3. セキュリティヘッダーのテスト

```bash
curl -I https://api.example.com

# 以下のヘッダーが含まれることを確認:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# X-Frame-Options: SAMEORIGIN
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
```

---

## 証明書の自動更新

Let's Encrypt証明書は90日間有効です。Certbotは自動更新機能を提供しています。

### 1. 自動更新のテスト

```bash
# ドライラン（実際には更新しない）
sudo certbot renew --dry-run

# 成功すれば以下のようなメッセージが表示される:
# Congratulations, all simulated renewals succeeded
```

### 2. 自動更新の設定確認

Certbotインストール時に、自動更新のsystemdタイマーまたはcronジョブが設定されます。

#### Systemdタイマーの確認（推奨）

```bash
# タイマーの状態確認
sudo systemctl status certbot.timer

# 有効化されていない場合
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# 次回の実行予定を確認
sudo systemctl list-timers | grep certbot
```

#### Cronジョブの確認（古い方法）

```bash
# cronジョブを確認
sudo cat /etc/cron.d/certbot

# または
sudo crontab -l
```

### 3. 更新後のNginxリロード設定

証明書更新後、Nginxをリロードする必要があります。

```bash
# 更新フックの追加
sudo nano /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

以下の内容を記述:

```bash
#!/bin/bash
systemctl reload nginx
```

実行権限を付与:

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

### 4. 手動更新

必要に応じて手動で更新することも可能です:

```bash
# すべての証明書を更新（有効期限30日未満のみ）
sudo certbot renew

# 強制更新（テスト用、本番では使用しない）
sudo certbot renew --force-renewal
```

---

## 動作確認

### 1. HTTPSアクセスの確認

```bash
# HTTPSでアクセス
curl -I https://api.example.com

# 期待される結果: HTTP/2 200 OK
```

### 2. HTTPリダイレクトの確認

```bash
# HTTPでアクセス
curl -I http://api.example.com

# 期待される結果:
# HTTP/1.1 301 Moved Permanently
# Location: https://api.example.com/
```

### 3. SSL証明書の検証

```bash
# OpenSSLでSSL証明書を確認
openssl s_client -connect api.example.com:443 -servername api.example.com

# 証明書チェーンが正しいことを確認
# Verify return code: 0 (ok)
```

### 4. オンラインツールでのテスト

#### SSL Labs SSL Server Test（推奨）

1. https://www.ssllabs.com/ssltest/ にアクセス
2. ドメイン名（api.example.com）を入力
3. テストを実行
4. 評価が **A** または **A+** であることを確認

評価が低い場合は、SSL設定を見直してください。

#### その他の便利なツール

- **SecurityHeaders.com**: セキュリティヘッダーのチェック
  https://securityheaders.com/

- **Mozilla Observatory**: 総合的なセキュリティスキャン
  https://observatory.mozilla.org/

### 5. API機能テスト

```bash
# ログインテスト
curl -X POST https://api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# 期待される結果: アクセストークンが返される
```

### 6. ブラウザでの確認

ブラウザで `https://api.example.com` にアクセスし、以下を確認:

- [ ] アドレスバーに鍵マークが表示される
- [ ] 証明書情報が正しい（発行者: Let's Encrypt）
- [ ] 有効期限が適切（約90日後）
- [ ] 証明書エラーが表示されない

---

## トラブルシューティング

### 1. 証明書取得失敗

#### エラー: "Failed authorization procedure"

**原因**: DNSが正しく設定されていない、またはポート80がブロックされている

**解決方法**:
```bash
# DNSを確認
nslookup api.example.com

# ポート80が開放されているか確認
sudo ufw status | grep 80

# Nginxが起動しているか確認
sudo systemctl status nginx

# /var/log/letsencrypt/letsencrypt.log でエラー詳細を確認
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

#### エラー: "Too many requests"

**原因**: Let's Encryptのレート制限に達した

**解決方法**:
- 1週間あたり同一ドメインで5回までの失敗が許可されています
- 制限に達した場合は1週間待つか、テスト用に `--dry-run` を使用

```bash
# テストモード（レート制限対象外）
sudo certbot --nginx -d api.example.com --dry-run
```

### 2. Nginx 502 Bad Gateway

**原因**: Gunicornが起動していない、または接続できない

**解決方法**:
```bash
# Gunicornの状態確認
/opt/mirai-knowledge-systems/backend/run_production.sh status

# ポート8000でリッスンしているか確認
sudo lsof -i :8000

# Gunicornを再起動
/opt/mirai-knowledge-systems/backend/run_production.sh restart

# Nginxエラーログを確認
sudo tail -f /var/log/nginx/mirai-knowledge-system-error.log
```

### 3. SSL証明書の警告

#### エラー: "NET::ERR_CERT_AUTHORITY_INVALID"

**原因**: 証明書チェーンが不完全、または自己署名証明書を使用している

**解決方法**:
```bash
# 証明書の確認
sudo certbot certificates

# Nginx設定で fullchain.pem を使用していることを確認
# ❌ ssl_certificate /etc/letsencrypt/live/api.example.com/cert.pem;
# ✅ ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
```

### 4. 証明書の自動更新が失敗

**症状**: 証明書が期限切れになる

**確認方法**:
```bash
# 更新ログを確認
sudo cat /var/log/letsencrypt/letsencrypt.log

# 手動で更新を試す
sudo certbot renew --dry-run
```

**解決方法**:
- ポート80が開放されていることを確認
- Nginx設定で `.well-known/acme-challenge/` へのアクセスが許可されていることを確認
- cronまたはsystemdタイマーが有効であることを確認

### 5. CORS エラー

**症状**: ブラウザのコンソールに CORS エラーが表示される

**解決方法**:
```bash
# 環境変数を確認
grep CORS /opt/mirai-knowledge-systems/backend/.env.production

# 正しいオリジンが設定されているか確認
# MKS_CORS_ORIGINS=https://example.com,https://app.example.com

# アプリケーションを再起動
/opt/mirai-knowledge-systems/backend/run_production.sh restart
```

### 6. パフォーマンス問題

**症状**: HTTPSでのレスポンスが遅い

**解決方法**:

1. SSL セッションキャッシュの有効化（既に設定済みの場合はスキップ）
```nginx
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

2. HTTP/2の確認
```bash
curl -I --http2 https://api.example.com | grep HTTP
# 期待される結果: HTTP/2 200
```

3. OCSP Staplingの確認
```bash
echo | openssl s_client -connect api.example.com:443 -status 2>&1 | grep -A 17 'OCSP response'
```

---

## HSTS Preloadについて（上級者向け）

### HSTS Preloadとは

HSTS Preloadは、ブラウザが事前にHTTPS接続のみを使用するように設定されるメカニズムです。これにより、初回アクセス時からHTTPS接続が強制されます。

### 注意事項

**警告**: HSTS Preloadを有効にすると、取り消すのが非常に困難です。以下の条件をすべて満たす場合のみ実施してください:

- [ ] ドメインとすべてのサブドメインで永続的にHTTPSを使用する
- [ ] 証明書の自動更新が確実に動作している
- [ ] HTTPへの切り戻しが不要であることを確認済み

### 有効化手順

1. Nginx設定で `preload` を追加:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

2. https://hstspreload.org/ でドメインを登録

3. ブラウザのHSTSプリロードリストに反映されるのを待つ（数週間〜数ヶ月）

---

## まとめ

このガイドに従うことで、建設土木ナレッジシステムAPIを安全なHTTPS環境で運用できます。

### チェックリスト

- [x] Let's Encrypt証明書を取得
- [x] Nginxの設定を最適化
- [x] HTTPからHTTPSへのリダイレクトを設定
- [x] セキュリティヘッダーを追加
- [x] 証明書の自動更新を設定
- [x] SSL Labs でA以上の評価を取得
- [x] API機能が正常に動作することを確認

### 定期的なメンテナンス

- **毎月**: SSL証明書の有効期限を確認
- **3ヶ月ごと**: SSL設定の見直しとセキュリティスキャン実施
- **6ヶ月ごと**: TLSプロトコルと暗号スイートの最新動向を確認

---

## 関連ドキュメント

- [本番環境移行チェックリスト](./04_Production-Migration-Checklist.md)
- [API仕様書](../08_API連携(Integrations)/03_API-Reference-Complete.md)
- [運用マニュアル](../11_運用(Operations)/01_Operations-Manual.md)

## 外部リソース

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP Transport Layer Protection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

**最終更新日**: 2024年12月27日
**バージョン**: 1.0.0
