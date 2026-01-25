# SSL/TLS 証明書設定ガイド

本番環境でHTTPS通信を有効にするための証明書設定手順を説明します。

## 目次

1. [Let's Encrypt証明書の取得](#1-lets-encrypt証明書の取得推奨)
2. [自己署名証明書の作成](#2-自己署名証明書の作成開発テスト用)
3. [証明書ファイルの配置](#3-証明書ファイルの配置)
4. [証明書の更新](#4-証明書の更新)

---

## 1. Let's Encrypt証明書の取得（推奨）

### 前提条件

- 有効なドメイン名（例: `api.example.com`）
- ドメインのDNS設定がサーバーのIPアドレスを指していること
- ポート80（HTTP）と443（HTTPS）が開放されていること

### Certbotのインストール

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo dnf install epel-release
sudo dnf install certbot python3-certbot-nginx
```

### 証明書の取得（スタンドアロンモード）

Nginx設定前に証明書を取得する場合:

```bash
# ポート80を使用して検証
sudo certbot certonly --standalone -d api.example.com

# 証明書は以下に保存される:
# /etc/letsencrypt/live/api.example.com/fullchain.pem
# /etc/letsencrypt/live/api.example.com/privkey.pem
```

### 証明書の取得（Nginxプラグインモード）

Nginxが既に稼働している場合:

```bash
sudo certbot --nginx -d api.example.com
```

### 自動更新の設定

Let's Encrypt証明書は90日で期限切れになります。自動更新を設定:

```bash
# 更新テスト
sudo certbot renew --dry-run

# cronまたはsystemdタイマーで自動更新（通常は自動設定済み）
# 手動でcron設定する場合:
echo "0 0,12 * * * root certbot renew --quiet" | sudo tee /etc/cron.d/certbot-renew
```

---

## 2. 自己署名証明書の作成（開発・テスト用）

**注意**: 自己署名証明書はブラウザで警告が表示されます。本番環境では使用しないでください。

### OpenSSLによる証明書生成

```bash
# このディレクトリに移動
cd /path/to/backend/ssl

# 秘密鍵と証明書を一括生成（有効期限365日）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout server.key \
    -out server.crt \
    -subj "/C=JP/ST=Tokyo/L=Chiyoda/O=Development/CN=localhost"

# SAN（Subject Alternative Name）付きで生成する場合
# 設定ファイルを作成
cat > openssl.cnf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
C = JP
ST = Tokyo
L = Chiyoda
O = Development
CN = localhost

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# SAN付き証明書を生成
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout server.key \
    -out server.crt \
    -config openssl.cnf
```

### 証明書の確認

```bash
# 証明書の内容を確認
openssl x509 -in server.crt -text -noout

# 有効期限の確認
openssl x509 -in server.crt -enddate -noout
```

### 開発環境でのGunicorn起動（自己署名証明書使用）

```bash
gunicorn --certfile=ssl/server.crt --keyfile=ssl/server.key \
    --bind 0.0.0.0:5000 app_v2:app
```

---

## 3. 証明書ファイルの配置

### 推奨ディレクトリ構成

```
backend/
├── ssl/
│   ├── README.md          # このファイル
│   ├── server.crt         # 証明書（自己署名の場合）
│   ├── server.key         # 秘密鍵（自己署名の場合）
│   └── openssl.cnf        # OpenSSL設定（オプション）
├── config/
│   ├── production.py      # 本番環境設定
│   └── nginx.conf.example # Nginx設定例
└── ...
```

### Let's Encrypt証明書へのシンボリックリンク作成

```bash
# 本番環境での証明書リンク（root権限が必要）
sudo ln -sf /etc/letsencrypt/live/api.example.com/fullchain.pem ssl/server.crt
sudo ln -sf /etc/letsencrypt/live/api.example.com/privkey.pem ssl/server.key
```

### ファイル権限の設定

```bash
# 秘密鍵の権限を制限
chmod 600 ssl/server.key
chmod 644 ssl/server.crt

# 所有者をアプリケーションユーザーに変更
sudo chown www-data:www-data ssl/server.key ssl/server.crt
```

---

## 4. 証明書の更新

### Let's Encrypt証明書の手動更新

```bash
# 証明書の更新
sudo certbot renew

# Nginxの設定リロード
sudo systemctl reload nginx
```

### 更新後のアプリケーション再起動

```bash
# Gunicornプロセスの再起動
sudo systemctl restart mirai-knowledge-api
```

### 証明書期限の監視

```bash
# 期限確認スクリプト例
#!/bin/bash
CERT_FILE="/etc/letsencrypt/live/api.example.com/fullchain.pem"
EXPIRE_DATE=$(openssl x509 -in "$CERT_FILE" -enddate -noout | cut -d= -f2)
EXPIRE_EPOCH=$(date -d "$EXPIRE_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRE_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "WARNING: Certificate expires in $DAYS_LEFT days"
fi
```

---

## セキュリティベストプラクティス

1. **秘密鍵の保護**
   - 秘密鍵は常に600（rw-------）のパーミッションで保護
   - Gitリポジトリに秘密鍵をコミットしない（.gitignoreに追加済み）

2. **証明書チェーンの確認**
   - 中間証明書が正しく含まれているか確認
   - `openssl s_client -connect api.example.com:443 -servername api.example.com`

3. **強力な暗号スイートの使用**
   - Nginx設定で推奨される暗号スイートを指定（nginx.conf.example参照）

4. **HSTS（HTTP Strict Transport Security）の有効化**
   - 本番環境ではHSTSヘッダーを追加

---

## トラブルシューティング

### よくある問題

1. **証明書と秘密鍵が一致しない**
   ```bash
   # 証明書と秘密鍵のモジュラスを比較
   openssl x509 -noout -modulus -in server.crt | openssl md5
   openssl rsa -noout -modulus -in server.key | openssl md5
   # 同じハッシュ値であれば一致
   ```

2. **証明書チェーンが不完全**
   ```bash
   # 証明書チェーンを検証
   openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt server.crt
   ```

3. **ポート443へのアクセスがブロック**
   ```bash
   # ファイアウォール設定確認（Ubuntu）
   sudo ufw status
   sudo ufw allow 443/tcp
   ```

---

## 参考リンク

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Instructions](https://certbot.eff.org/instructions)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
