# Mirai Knowledge Systems - クイックスタートガイド

## 🚀 即座に実行できる手順

このガイドでは、現在の状態から本番環境を起動するまでの最短手順を説明します。

---

## ✅ 現在の状態

- ✅ PostgreSQL 16.11 稼働中
- ✅ Nginx 稼働中（HTTPS port 8443）
- ✅ Flask API 手動起動中（port 5100）
- ✅ gunicorn インストール済み
- ✅ systemdサービスファイル準備済み
- ✅ ログローテーション設定済み
- ✅ E2Eテスト環境構築済み（29件成功）

---

## 📝 systemdサービス起動（推奨）

### ステップ1: インタラクティブインストール

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems
sudo ./install-systemd-service.sh
```

プロンプトが表示されたら：
- **本番環境**: `2` を選択（gunicorn使用、推奨）
- **開発環境**: `1` を選択（python3直接実行）

### ステップ2: サービス状態確認

```bash
# 本番モードの場合
sudo systemctl status mirai-knowledge-prod

# 開発モードの場合
sudo systemctl status mirai-knowledge-system
```

### ステップ3: 動作確認

```bash
# ヘルスチェック
curl -k https://localhost:8443/api/v1/health | jq .

# アプリケーション統計
curl http://localhost:5100/api/v1/health | jq .
```

---

## 🔧 手動起動（systemd不使用の場合）

### 開発モード（現在の起動方法）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
source venv_linux/bin/activate
python3 app_v2.py
```

### 本番モード（gunicorn使用）

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
source venv_linux/bin/activate
gunicorn --config gunicorn.conf.py app_v2:app
```

---

## 🧪 テスト実行

### E2Eテスト

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems

# 全テスト実行
BASE_URL=http://localhost:5100 SKIP_WEBSERVER=true \
  npx playwright test backend/tests/e2e/ \
  --config=backend/playwright.config.js

# UIモード（インタラクティブ）
BASE_URL=http://localhost:5100 SKIP_WEBSERVER=true \
  npx playwright test backend/tests/e2e/ \
  --config=backend/playwright.config.js \
  --ui
```

### ユニットテスト

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
source venv_linux/bin/activate
pytest
```

---

## 🔒 本番環境への移行

### 1. 環境変数の設定

```bash
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend

# 本番用環境変数ファイル作成
cp .env.production.example .env.production

# セキュリティキー生成
python3 -c "import secrets; print('MKS_SECRET_KEY=' + secrets.token_urlsafe(64))"
python3 -c "import secrets; print('MKS_JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"

# .env.productionを編集して上記のキーを設定
vim .env.production
```

### 2. PostgreSQLパスワード変更

```bash
# PostgreSQLに接続
sudo -u postgres psql

# パスワード変更
ALTER USER postgres WITH PASSWORD '<強力なパスワード>';
\q

# .envファイルのDATABASE_URLを更新
vim backend/.env
```

### 3. ファイル権限の設定

```bash
# 環境変数ファイルの権限を制限
chmod 600 backend/.env
chmod 600 backend/.env.production
```

### 4. 本番ログディレクトリの作成

```bash
# ログディレクトリ作成
sudo mkdir -p /var/log/mirai-knowledge

# 権限設定
sudo chown kensan:kensan /var/log/mirai-knowledge
sudo chmod 755 /var/log/mirai-knowledge
```

### 5. Nginxセキュリティヘッダー追加（オプション）

```bash
# セキュリティヘッダー設定を追加
sudo vim /etc/nginx/sites-available/mirai-knowledge-system

# nginx-security-headers.confの内容をserverブロック内にコピー

# 設定テスト
sudo nginx -t

# Nginx再読み込み
sudo systemctl reload nginx
```

---

## 📊 ログ確認

### systemdログ

```bash
# リアルタイム監視
sudo journalctl -u mirai-knowledge-prod -f

# 最新100行
sudo journalctl -u mirai-knowledge-prod -n 100
```

### アプリケーションログ

```bash
# 開発環境
tail -f backend/logs/app_restart.log

# 本番環境
tail -f /var/log/mirai-knowledge/access.log
tail -f /var/log/mirai-knowledge/error.log
```

---

## 🚨 トラブルシューティング

### サービスが起動しない

```bash
# ログ確認
sudo journalctl -u mirai-knowledge-prod -n 50

# ポート使用状況確認
sudo lsof -i :5100

# 手動起動プロセスを停止
pkill -f "python3 app_v2.py"
```

### データベース接続エラー

```bash
# PostgreSQL稼働確認
sudo systemctl status postgresql

# 接続テスト
psql -U postgres -d mirai_knowledge_db -c "SELECT version();"
```

### HTTPS接続エラー

```bash
# SSL証明書確認
openssl x509 -in /etc/ssl/mks/mks.crt -noout -dates

# Nginx設定テスト
sudo nginx -t

# Nginx再起動
sudo systemctl restart nginx
```

---

## 📚 詳細ドキュメント

より詳細な情報は以下のドキュメントを参照してください：

- **SYSTEMD_SETUP_GUIDE.md** - systemdサービス詳細ガイド
- **LOG_MANAGEMENT_GUIDE.md** - ログ管理完全ガイド
- **PRODUCTION_CHECKLIST.md** - 本番環境チェックリスト
- **E2E_TEST_RESULTS.md** - E2Eテスト結果レポート

---

## 🎯 推奨される起動順序

1. PostgreSQL起動確認
2. Nginx起動確認
3. systemdサービスインストール・起動
4. ヘルスチェック実行
5. E2Eテスト実行（検証）

---

## 💡 よくある質問

### Q: 開発モードと本番モードの違いは？

| 項目 | 開発モード | 本番モード |
|------|----------|----------|
| 実行方法 | python3直接 | gunicorn |
| ワーカー数 | 1 | CPU数×2+1 |
| 再起動 | 手動 | 自動（systemd） |
| パフォーマンス | 低 | 高 |

### Q: 既に手動起動中のプロセスがある場合は？

systemdサービス起動前に手動プロセスを停止してください：

```bash
pkill -f "python3 app_v2.py"
```

### Q: サービスの自動起動を無効にするには？

```bash
sudo systemctl disable mirai-knowledge-prod
```

---

**作成日**: 2026-01-08
**対象バージョン**: 2.0.0
**最終更新**: 2026-01-08
