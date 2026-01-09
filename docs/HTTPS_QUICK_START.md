# HTTPS設定クイックスタート

## Mirai Knowledge System - 5分でHTTPS完全実装

**対象者**: システム管理者、DevOpsエンジニア
**所要時間**: 約5分
**前提条件**: sudoアクセス権限

---

## 🚀 クイックスタート（3ステップ）

### ステップ1: SSL証明書確認

証明書は既に生成済みです：

```bash
ls -la /mnt/LinuxHDD/Mirai-Knowledge-Systems/ssl/
# server.crt, server.key が存在することを確認
```

**証明書詳細**:
- 有効期限: 10年間（2026-01-09 〜 2036-01-07）
- 暗号化: RSA 4096bit
- SubjectAltName: IPアドレス対応

### ステップ2: Nginx設定適用（最適化版）

```bash
# 設定ファイルコピー
sudo cp /mnt/LinuxHDD/Mirai-Knowledge-Systems/config/nginx-https-optimized.conf \
        /etc/nginx/sites-available/mirai-knowledge-https

# シンボリックリンク作成（既存設定削除）
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/mirai-knowledge-https \
            /etc/nginx/sites-enabled/

# 構文チェック
sudo nginx -t

# Nginx再起動
sudo systemctl reload nginx
```

### ステップ3: 動作確認

```bash
# 自動テスト実行
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
./scripts/test-https-redirect.sh
```

**期待結果**: 17項目中14項目以上が成功

---

## ✅ 簡易確認コマンド

### HTTPリダイレクト確認

```bash
curl -I http://192.168.0.187/
# 期待: HTTP/1.1 301 Moved Permanently
# 期待: Location: https://192.168.0.187/
```

### HTTPS接続確認

```bash
curl -I -k https://192.168.0.187/
# 期待: HTTP/2 200
```

### セキュリティヘッダー確認

```bash
curl -I -k https://192.168.0.187/ | grep -i "security\|frame\|content-type"
```

---

## 🔧 トラブルシューティング（1分以内）

### 問題: リダイレクトしない

```bash
sudo systemctl restart nginx
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 問題: 証明書エラー

ブラウザで「詳細設定」→「安全でないページに進む」

---

## 📚 詳細ドキュメント

完全なドキュメント: [`docs/HTTPS_SETUP_COMPLETE.md`](./HTTPS_SETUP_COMPLETE.md)

---

## 🆘 よくある質問

**Q: 自己署名証明書で本番運用できますか？**
A: 社内イントラネットでは可能。インターネット公開にはLet's Encrypt推奨。

**Q: Let's Encryptへの移行は？**
A: ドメイン取得後、`sudo certbot --nginx -d yourdomain.com`で自動設定可能。

**Q: 証明書の有効期限は？**
A: 10年間。`./scripts/check-ssl-expiry.sh`で確認可能。

---

**所要時間まとめ**:
- ステップ1: 30秒
- ステップ2: 2分
- ステップ3: 2分
- 合計: 約5分

**次のステップ**: 本番環境デプロイ → [`docs/HTTPS_SETUP_COMPLETE.md`](./HTTPS_SETUP_COMPLETE.md)
