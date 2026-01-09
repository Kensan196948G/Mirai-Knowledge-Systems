# HTTPS設定完了ガイド

## Mirai Knowledge System - HTTPS自動リダイレクト完全実装

**作成日**: 2026-01-09
**バージョン**: 1.0.0
**ステータス**: ✅ 実装完了

---

## 📋 実装内容サマリー

### ✅ 完了項目

1. **自己署名SSL証明書作成**
   - RSA 4096bit（10年有効）
   - SubjectAltName (SAN) 対応
   - 証明書パス: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/`

2. **HTTP→HTTPS自動リダイレクト**
   - 全HTTPトラフィックを301リダイレクト
   - IPアドレス・localhostの両方対応

3. **TLS/SSL最適化設定**
   - TLS 1.2/1.3のみ許可（TLS 1.0/1.1無効化）
   - HTTP/2サポート
   - Forward Secrecy対応暗号スイート

4. **セキュリティヘッダー実装**
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: 1; mode=block
   - Referrer-Policy: strict-origin-when-cross-origin

5. **テストスクリプト作成**
   - 自動化された包括的テストスイート
   - 17項目のセキュリティチェック

---

## 🔐 SSL証明書情報

### 証明書詳細

```plaintext
場所: /mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/
  - server.crt (証明書)
  - server.key (秘密鍵)

有効期限: 2026-01-09 ~ 2036-01-07 (10年間)
発行者: Mirai Knowledge Systems
Subject: C=JP, ST=Tokyo, L=Tokyo, O=Mirai Knowledge Systems, CN=192.168.0.187

SubjectAltName (SAN):
  - IP Address: 192.168.0.187
  - IP Address: 127.0.0.1
  - DNS: localhost
```

### 証明書更新手順

#### 自己署名証明書の更新（10年後）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl

# バックアップ
cp server.crt server.crt.bak
cp server.key server.key.bak

# 新しい証明書生成（10年有効）
openssl req -x509 -nodes -days 3650 \
  -newkey rsa:4096 \
  -keyout server.key \
  -out server.crt \
  -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai Knowledge Systems/OU=IT/CN=192.168.0.187" \
  -addext "subjectAltName = IP:192.168.0.187,IP:127.0.0.1,DNS:localhost"

# 権限設定
chmod 644 server.crt
chmod 600 server.key

# Nginxリロード（sudoが必要）
sudo systemctl reload nginx
```

#### Let's Encrypt証明書への移行（ドメイン取得後）

**前提条件**: 独自ドメイン（例: mks.example.com）が必要

```bash
# 1. Certbotインストール
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 2. ドメインのDNS設定
# A/AAAAレコードでサーバーIPアドレスを設定

# 3. 証明書取得
sudo certbot --nginx -d mks.example.com

# 4. 自動更新設定確認
sudo systemctl status certbot.timer

# 5. 更新テスト（ドライラン）
sudo certbot renew --dry-run

# 6. Nginx設定更新（最適化版を使用）
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/config/nginx-https-optimized.conf \
        /etc/nginx/sites-available/mirai-knowledge-https

# 証明書パスを編集（コメント解除）
sudo nano /etc/nginx/sites-available/mirai-knowledge-https
# ssl_certificate /etc/letsencrypt/live/mks.example.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/mks.example.com/privkey.pem;

# 7. 設定反映
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🛠️ Nginx設定ファイル

### 現在の設定ファイル構成

```plaintext
/mnt/LinuxHDD/Mirai-Knowledge-Systems/config/
├── nginx-production.conf          # 現在の本番設定
├── nginx-https-optimized.conf     # 最適化版（推奨）
└── nginx-security-headers.conf    # セキュリティヘッダーテンプレート
```

### 最適化版への切り替え手順

**最適化版の改善点**:
- HSTS（HTTP Strict Transport Security）有効化
- Content-Security-Policy (CSP) 強化
- Cross-Origin-* ヘッダー追加
- OCSP Stapling対応準備
- Let's Encrypt証明書対応準備

```bash
# 1. 設定ファイルコピー（sudoが必要）
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/config/nginx-https-optimized.conf \
        /etc/nginx/sites-available/mirai-knowledge-https

# 2. シンボリックリンク作成（既存設定がある場合は削除）
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/mirai-knowledge-production
sudo ln -sf /etc/nginx/sites-available/mirai-knowledge-https \
            /etc/nginx/sites-enabled/

# 3. 構文チェック
sudo nginx -t

# 4. Nginxリロード
sudo systemctl reload nginx

# 5. 設定確認
curl -I https://192.168.0.187/ | grep -i "strict-transport-security"
```

---

## 🧪 テストとバリデーション

### 自動テストスクリプト実行

```bash
# テストスクリプト実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
./scripts/test-https-redirect.sh
```

**テスト項目** (17項目):
1. HTTP→HTTPSリダイレクト（IPアドレス）
2. HTTP→HTTPSリダイレクト（localhost）
3. HTTPSアクセス確認
4. HTTP/2サポート確認
5. HSTS（Strict-Transport-Security）
6. X-Frame-Options
7. X-Content-Type-Options
8. Content-Security-Policy
9. Referrer-Policy
10. TLSバージョン確認（1.2/1.3のみ）
11. 暗号スイート確認
12. 証明書ファイル存在確認
13. 証明書読み取り確認
14. 証明書有効期限確認
15. SubjectAltName (SAN) 確認
16. APIヘルスチェック
17. 全体サマリー

### 手動テスト

#### 1. HTTPリダイレクトテスト

```bash
# IPアドレス
curl -I http://192.168.0.187/

# 期待結果:
# HTTP/1.1 301 Moved Permanently
# Location: https://192.168.0.187/
```

#### 2. HTTPSアクセステスト

```bash
# 自己署名証明書のため -k オプション使用
curl -I -k https://192.168.0.187/

# 期待結果:
# HTTP/2 200
# strict-transport-security: max-age=31536000; includeSubDomains
```

#### 3. TLS設定確認

```bash
# TLSバージョンと暗号スイート確認
echo "Q" | openssl s_client -connect 192.168.0.187:443 -servername 192.168.0.187 2>&1 | grep -E "Protocol|Cipher"

# 期待結果:
# Protocol  : TLSv1.3
# Cipher    : TLS_AES_256_GCM_SHA384
```

#### 4. セキュリティヘッダー確認

```bash
curl -I -k https://192.168.0.187/ | grep -i "security\|frame\|content-type\|xss"
```

### 外部評価ツール（本番環境のみ）

**注意**: 外部からアクセス可能なドメインが必要

1. **SSL Labs**
   https://www.ssllabs.com/ssltest/
   期待評価: A+ (Let's Encrypt証明書使用時)

2. **Security Headers**
   https://securityheaders.com/
   期待評価: A (最適化版設定使用時)

3. **Mozilla Observatory**
   https://observatory.mozilla.org/
   期待評価: A+ (CSP完全実装時)

---

## 🔧 トラブルシューティング

### 問題1: HTTPリダイレクトが動作しない

**症状**: HTTP接続時にHTTPSにリダイレクトされない

**診断**:
```bash
# Nginxステータス確認
sudo systemctl status nginx

# 設定ファイル構文チェック
sudo nginx -t

# エラーログ確認
sudo tail -f /var/log/nginx/error.log

# ポート80がリッスン中か確認
sudo netstat -tlnp | grep :80
```

**解決策**:
```bash
# Nginx再起動
sudo systemctl restart nginx

# ファイアウォール確認（必要に応じて）
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

### 問題2: HTTPS接続時に証明書エラー

**症状**: ブラウザで「接続がプライベートではありません」エラー

**原因**: 自己署名証明書の使用

**解決策**:

#### 開発・テスト環境
1. ブラウザで「詳細設定」→「安全でないページに進む」
2. Chrome: `chrome://flags/#allow-insecure-localhost` を有効化

#### 本番環境
1. Let's Encrypt証明書に移行（上記手順参照）
2. または、自己署名証明書をクライアントの信頼ストアに追加

**証明書をクライアントに追加**:
```bash
# Windowsの場合
1. server.crt をダウンロード
2. ダブルクリック→「証明書のインストール」
3. 「信頼されたルート証明機関」に配置

# Linux/Macの場合
sudo cp server.crt /usr/local/share/ca-certificates/mks.crt
sudo update-ca-certificates
```

---

### 問題3: セキュリティヘッダーが表示されない

**症状**: `curl -I` でHSTSやCSPヘッダーが表示されない

**診断**:
```bash
# 現在の設定ファイル確認
sudo nginx -T | grep -A 5 "add_header"

# 有効な設定ファイル確認
ls -la /etc/nginx/sites-enabled/
```

**解決策**:
```bash
# 最適化版設定ファイルに切り替え
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/config/nginx-https-optimized.conf \
        /etc/nginx/sites-available/mirai-knowledge-https

sudo ln -sf /etc/nginx/sites-available/mirai-knowledge-https \
            /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl reload nginx
```

---

### 問題4: HTTP/2が有効化されない

**症状**: `curl -I` で `HTTP/1.1` と表示される

**診断**:
```bash
# HTTP/2サポート確認
curl -I -k --http2 https://192.168.0.187/

# Nginxバージョン確認（1.9.5以降必要）
nginx -v
```

**解決策**:
```bash
# Nginx設定で http2 指定確認
# listen 443 ssl http2; ← http2 が必要

sudo nano /etc/nginx/sites-available/mirai-knowledge-https
sudo nginx -t
sudo systemctl reload nginx
```

---

### 問題5: 証明書の有効期限切れ

**症状**: HTTPS接続時に「証明書の有効期限が切れています」エラー

**診断**:
```bash
# 証明書有効期限確認
openssl x509 -in /mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/server.crt \
  -noout -dates

# 現在日時との比較
date
```

**解決策**:
```bash
# 証明書更新（上記「証明書更新手順」参照）
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl
# ... 証明書生成コマンド実行 ...

sudo systemctl reload nginx
```

---

## 📊 セキュリティ監視

### 証明書有効期限の監視

**スクリプト**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/check-ssl-expiry.sh`

```bash
#!/bin/bash
# SSL証明書有効期限チェック

CERT_FILE="/mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/server.crt"
EXPIRY_DATE=$(openssl x509 -in "$CERT_FILE" -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

echo "SSL証明書有効期限: $DAYS_LEFT 日後"

# 30日以内に期限切れの場合、警告
if [ $DAYS_LEFT -lt 30 ]; then
    echo "⚠️  警告: SSL証明書の有効期限が近づいています"
    echo "更新を推奨: $EXPIRY_DATE"
fi

exit 0
```

**cron設定例** (毎週月曜 9:00実行):
```bash
0 9 * * 1 /mnt/LinuxHDD/Mirai-Knowledge-Systems/scripts/check-ssl-expiry.sh | mail -s "SSL証明書チェック" admin@example.com
```

### Nginxログ監視

```bash
# アクセスログリアルタイム監視
sudo tail -f /var/log/nginx/mirai-knowledge-access.log

# エラーログリアルタイム監視
sudo tail -f /var/log/nginx/mirai-knowledge-error.log

# HTTPアクセス統計（リダイレクト確認）
sudo grep "301" /var/log/nginx/mirai-knowledge-access.log | wc -l

# HTTPSアクセス統計
sudo grep "200" /var/log/nginx/mirai-knowledge-access.log | wc -l
```

---

## 🚀 パフォーマンス最適化

### DHパラメータ生成（任意、強化版）

```bash
# 2048bit DHパラメータ生成（数分かかる）
sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048

# Nginx設定に追加
sudo nano /etc/nginx/sites-available/mirai-knowledge-https
# ssl_dhparam /etc/nginx/dhparam.pem; のコメント解除

sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLSセッションキャッシュ最適化

現在の設定:
```nginx
ssl_session_cache shared:MKS_SSL:10m;  # 約40,000セッション
ssl_session_timeout 10m;
```

大規模トラフィック時の調整:
```nginx
ssl_session_cache shared:MKS_SSL:50m;  # 約200,000セッション
ssl_session_timeout 4h;
```

---

## 📚 参考資料

### 公式ドキュメント

- [Nginx SSL/TLS設定](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)

### セキュリティベストプラクティス

- [CIS Nginx Benchmark](https://www.cisecurity.org/benchmark/nginx)
- [SSL/TLS Deployment Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)

---

## 📝 変更履歴

| 日付 | バージョン | 内容 |
|------|-----------|------|
| 2026-01-09 | 1.0.0 | 初版作成 - HTTPS自動リダイレクト完全実装 |

---

## ✅ チェックリスト

本番環境デプロイ前の最終確認:

- [ ] SSL証明書が正しく生成されている
- [ ] HTTP→HTTPSリダイレクトが動作する
- [ ] HTTPSアクセスが正常に動作する
- [ ] TLS 1.2/1.3のみ有効
- [ ] HTTP/2が有効化されている
- [ ] セキュリティヘッダーが設定されている
  - [ ] HSTS
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Content-Security-Policy
  - [ ] Referrer-Policy
- [ ] 自動テストスクリプトが全テストパス
- [ ] ログファイルにエラーがない
- [ ] 証明書有効期限が十分に残っている
- [ ] バックアップが取得されている

---

## 🆘 サポート

問題が解決しない場合:

1. **ログ確認**
   ```bash
   sudo tail -100 /var/log/nginx/error.log
   ```

2. **設定検証**
   ```bash
   sudo nginx -T | less
   ```

3. **テストスクリプト実行**
   ```bash
   ./scripts/test-https-redirect.sh
   ```

4. **GitHub Issue作成**
   問題の詳細、ログ、テスト結果を含めて報告

---

**ドキュメント作成者**: Claude Code (Anthropic)
**最終更新**: 2026-01-09
