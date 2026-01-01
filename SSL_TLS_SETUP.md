# SSL/TLS証明書セットアップガイド

**対象**: Mirai Knowledge System の本番環境HTTPS化
**目的**: Let's Encrypt無料SSL証明書の設定

---

## 📋 目次

1. [前提条件](#前提条件)
2. [Let's Encrypt証明書取得](#lets-encrypt証明書取得)
3. [Nginx設定](#nginx設定)
4. [自動更新設定](#自動更新設定)
5. [開発環境用自己署名証明書](#開発環境用自己署名証明書)
6. [トラブルシューティング](#トラブルシューティング)

---

## 📌 前提条件

### 必須要件

- ✅ ドメイン名（例: your-domain.com）
- ✅ DNSレコード設定（ドメインがサーバーIPを指している）
- ✅ ポート80, 443が開放されている
- ✅ Nginxがインストールされている

### 確認方法

```bash
# ドメインがサーバーIPを指しているか確認
nslookup your-domain.com

# ポート80, 443が開放されているか確認
sudo ss -tlnp | grep -E ':80|:443'

# Nginxがインストールされているか確認
nginx -v
```

---

## 🔐 Let's Encrypt証明書取得

### 1. Certbotのインストール

**Ubuntu/Debian**:
```bash
# snapdをインストール（まだの場合）
sudo apt update
sudo apt install -y snapd
sudo snap install core
sudo snap refresh core

# Certbotをインストール
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

**RHEL/CentOS/Rocky Linux**:
```bash
sudo dnf install -y epel-release
sudo dnf install -y certbot python3-certbot-nginx
```

### 2. Webルートディレクトリの作成

```bash
# Let's EncryptのACMEチャレンジ用ディレクトリ
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot
```

### 3. 一時的なNginx設定（証明書取得用）

証明書取得前に、最小限のNginx設定を作成：

```bash
sudo nano /etc/nginx/sites-available/mirai-temp
```

以下の内容を記述：

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 "Certbot verification in progress...";
        add_header Content-Type text/plain;
    }
}
```

**your-domain.com** を実際のドメインに置き換えてください。

```bash
# シンボリックリンクを作成
sudo ln -s /etc/nginx/sites-available/mirai-temp /etc/nginx/sites-enabled/

# Nginx設定テスト
sudo nginx -t

# Nginxを再起動
sudo systemctl restart nginx
```

### 4. Let's Encrypt証明書を取得

```bash
# 証明書取得（webrootモード）
sudo certbot certonly --webroot -w /var/www/certbot \
    -d your-domain.com \
    -d www.your-domain.com \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email
```

**重要**: 以下を実際の値に置き換えてください：
- `your-domain.com` → 実際のドメイン名
- `your-email@example.com` → 実際のメールアドレス

**期待される出力**:
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/your-domain.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 5. 証明書の確認

```bash
# 証明書ファイルが作成されたか確認
sudo ls -l /etc/letsencrypt/live/your-domain.com/

# 証明書の有効期限を確認
sudo certbot certificates
```

---

## ⚙️ Nginx設定

### 1. 一時設定を削除

```bash
# 一時的な設定を無効化
sudo rm /etc/nginx/sites-enabled/mirai-temp

# Nginxをリロード
sudo systemctl reload nginx
```

### 2. 本番用Nginx設定をコピー

```bash
# プロジェクトのNginx設定をコピー
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/nginx.conf.example \
    /etc/nginx/sites-available/mirai-knowledge-system

# エディタで編集
sudo nano /etc/nginx/sites-available/mirai-knowledge-system
```

### 3. ドメイン名を置き換え

以下の箇所を実際のドメイン名に置き換えてください：

```nginx
server_name your-domain.com www.your-domain.com;

ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/your-domain.com/chain.pem;
```

### 4. シンボリックリンクを作成

```bash
# 設定を有効化
sudo ln -s /etc/nginx/sites-available/mirai-knowledge-system \
    /etc/nginx/sites-enabled/

# 設定テスト
sudo nginx -t

# Nginxを再起動
sudo systemctl restart nginx
```

### 5. HTTPSアクセス確認

```
https://your-domain.com
```

ブラウザで緑の鍵マークが表示されればOK！

---

## 🔄 自動更新設定

Let's Encrypt証明書は90日間有効です。自動更新を設定します。

### 1. 自動更新テスト

```bash
# ドライラン（実際には更新しない）
sudo certbot renew --dry-run
```

### 2. systemdタイマーの確認

Certbotはsnapdインストール時に自動更新が設定されます：

```bash
# タイマーの状態確認
sudo systemctl list-timers | grep certbot

# 手動で更新を実行
sudo certbot renew
```

### 3. 更新後のNginxリロード

Certbotは証明書更新後、自動的にNginxをリロードします。以下のフックが設定されていることを確認：

```bash
# フックの確認
sudo ls /etc/letsencrypt/renewal-hooks/deploy/
```

フックがない場合、手動で作成：

```bash
sudo nano /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

内容：
```bash
#!/bin/bash
systemctl reload nginx
```

実行権限を付与：
```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

---

## 🔧 開発環境用自己署名証明書

本番環境でない場合や、テスト用に自己署名証明書を使用できます。

### 1. 自己署名証明書の生成

```bash
# SSL証明書ディレクトリを作成
sudo mkdir -p /etc/nginx/ssl
cd /etc/nginx/ssl

# 秘密鍵と証明書を生成（有効期限365日）
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/mirai-selfsigned.key \
    -out /etc/nginx/ssl/mirai-selfsigned.crt \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=MiraiKnowledge/CN=localhost"
```

### 2. Nginx設定を更新

```nginx
ssl_certificate /etc/nginx/ssl/mirai-selfsigned.crt;
ssl_certificate_key /etc/nginx/ssl/mirai-selfsigned.key;
```

### 3. ブラウザ警告について

自己署名証明書の場合、ブラウザで「安全でない」警告が表示されますが、開発環境では問題ありません。

---

## 🐛 トラブルシューティング

### エラー: "Failed authorization procedure"

**原因**: ドメインがサーバーIPを指していない、またはポート80が開放されていない

**解決**:
```bash
# DNSレコードを確認
nslookup your-domain.com

# ポート80が開放されているか確認
sudo ss -tlnp | grep :80

# ファイアウォールを確認（UFWの場合）
sudo ufw status

# ポート80, 443を開放
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### エラー: "too many certificates already issued"

**原因**: Let's Encryptのレート制限（週5回まで）

**解決**: 1週間待つか、`--staging`フラグでテスト証明書を取得

```bash
sudo certbot certonly --webroot --staging -w /var/www/certbot \
    -d your-domain.com
```

### エラー: "nginx: [emerg] cannot load certificate"

**原因**: 証明書ファイルのパスが間違っている

**解決**:
```bash
# 証明書のパスを確認
sudo certbot certificates

# Nginx設定のパスを修正
sudo nano /etc/nginx/sites-available/mirai-knowledge-system
```

### エラー: "Connection refused" (HTTPS)

**原因**: Nginxがポート443で待ち受けていない

**解決**:
```bash
# Nginxの状態確認
sudo systemctl status nginx

# エラーログを確認
sudo tail -f /var/log/nginx/error.log

# Nginx設定テスト
sudo nginx -t

# Nginxを再起動
sudo systemctl restart nginx
```

---

## 🔐 セキュリティベストプラクティス

### 1. SSL Labsでスコア確認

```
https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

A+評価を目指しましょう！

### 2. HTTPSのみでアクセス可能にする

Nginx設定で、HTTPからHTTPSへの自動リダイレクトを確認：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. HSTSヘッダーの確認

```bash
curl -I https://your-domain.com | grep Strict-Transport-Security
```

出力例：
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

---

## ✅ チェックリスト

SSL/TLS設定完了時の確認項目：

- [ ] Let's Encrypt証明書が取得されている
- [ ] Nginx設定が正しく適用されている
- [ ] HTTPSでアクセスできる（緑の鍵マーク表示）
- [ ] HTTPからHTTPSへ自動リダイレクトされる
- [ ] 証明書の自動更新が設定されている
- [ ] SSL Labs評価がA以上
- [ ] HSTSヘッダーが設定されている
- [ ] ログインページが正常に表示される
- [ ] API通信がHTTPSで動作する

---

## 📞 次のステップ

SSL/TLS設定が完了したら、以下を確認してください：

1. **app_v2.pyの環境変数を更新**:
   ```bash
   MKS_ENV=production
   MKS_FORCE_HTTPS=true
   ```

2. **systemdサービスを再起動**:
   ```bash
   sudo systemctl restart mirai-knowledge-system.service
   ```

3. **全機能のテスト**:
   - ログイン
   - ダッシュボード表示
   - API通信
   - データ取得

---

**作成日**: 2026-01-01
**バージョン**: v1.0
