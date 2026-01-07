# 本番環境デプロイガイド - Mirai Knowledge System

**対象**: 本番環境への完全デプロイ
**所要時間**: 約2-3時間

---

## 📋 目次

1. [概要](#概要)
2. [デプロイアーキテクチャ](#デプロイアーキテクチャ)
3. [前提条件](#前提条件)
4. [ステップ1: PostgreSQL環境構築](#ステップ1-postgresql環境構築)
5. [ステップ2: Gunicornインストール](#ステップ2-gunicornインストール)
6. [ステップ3: Nginx設定](#ステップ3-nginx設定)
7. [ステップ4: SSL/TLS証明書設定](#ステップ4-ssltls証明書設定)
8. [ステップ5: systemdサービス更新](#ステップ5-systemdサービス更新)
9. [ステップ6: 動作確認](#ステップ6-動作確認)
10. [トラブルシューティング](#トラブルシューティング)
11. [運用・保守](#運用保守)

---

## 📖 概要

このガイドでは、Mirai Knowledge Systemを以下の構成で本番環境にデプロイします：

**開発環境（現在）**:
- Flask組み込みサーバー（ポート5100）
- JSONファイルストレージ
- HTTP通信
- MKS_ENV=development

**本番環境（デプロイ後）**:
- Gunicorn（WSGIサーバー、ポート8000）
- PostgreSQL（データベース）
- Nginx（リバースプロキシ、ポート80/443）
- HTTPS通信（Let's Encrypt）
- MKS_ENV=production

---

## 🏗️ デプロイアーキテクチャ

```
インターネット
     ↓
  [Nginx]
   ↓ (reverse proxy)
   ↓ SSL/TLS終端
   ↓ ポート80/443
   ↓
[Gunicorn]
   ↓ WSGIサーバー
   ↓ ポート8000
   ↓
[Flask App (app_v2.py)]
   ↓
[PostgreSQL]
   ↓ ポート5432
[データベース]
```

---

## ✅ 前提条件

### システム要件
- **OS**: Linux (Ubuntu 20.04+ / Rocky Linux 8+ 推奨)
- **CPU**: 2コア以上
- **RAM**: 4GB以上
- **ディスク**: 20GB以上の空き容量

### 必要なソフトウェア
- [ ] Python 3.8以上
- [ ] PostgreSQL 12以上
- [ ] Nginx
- [ ] systemd
- [ ] sudo権限

### 必要な情報（本番環境）
- [ ] ドメイン名（例: your-domain.com）
- [ ] DNSレコード設定済み
- [ ] メールアドレス（Let's Encrypt用）
- [ ] PostgreSQLパスワード

---

## 📊 デプロイ手順概要

| ステップ | 作業内容 | 所要時間 |
|---------|---------|----------|
| 1 | PostgreSQL環境構築 | 30分 |
| 2 | Gunicornインストール | 10分 |
| 3 | Nginx設定 | 20分 |
| 4 | SSL/TLS証明書設定 | 30分 |
| 5 | systemdサービス更新 | 15分 |
| 6 | 動作確認 | 15分 |

**合計**: 約2時間

## 自動化スクリプト（任意）

手順を簡略化したい場合は、以下のスクリプトを使用できます。

```bash
./setup-production.sh
```

手動でGunicornを起動したい場合は `backend/run_production.sh` を利用できます。

---

## ステップ1: PostgreSQL環境構築

詳細は [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) を参照してください。

### 1.0 Dockerで簡易構築（任意）

開発/検証用途で簡易に起動する場合は `docker-compose.yml` を使用できます。

```bash
cd /path/to/Mirai-Knowledge-Systems
docker-compose up -d
```

### 1.1 PostgreSQLインストール

```bash
# Ubuntu/Debianの場合
sudo apt update
sudo apt install -y postgresql-16 postgresql-contrib-16

# PostgreSQLを起動
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 1.2 データベース作成

```bash
# PostgreSQLユーザーに切り替え
sudo -u postgres psql

# 以下をPostgreSQLプロンプトで実行
CREATE USER mirai_user WITH PASSWORD 'your-secure-password-here';
CREATE DATABASE mirai_knowledge_db OWNER mirai_user;
GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge_db TO mirai_user;
\c mirai_knowledge_db
GRANT ALL ON SCHEMA public TO mirai_user;
\q
```

### 1.3 環境変数設定

```bash
cd /path/to/Mirai-Knowledge-Systems/backend
nano .env
```

以下を追加/更新：
```bash
MKS_USE_POSTGRESQL=true
DATABASE_URL=postgresql://mirai_user:your-secure-password-here@localhost:5432/mirai_knowledge_db
```

### 1.4 データマイグレーション

```bash
cd /path/to/Mirai-Knowledge-Systems/backend
source ../venv_linux/bin/activate

# スキーマ作成
python3 << EOF
from database import engine, Base
Base.metadata.create_all(bind=engine)
print("✅ スキーマ作成完了")
EOF

# データ移行
python3 migrate_json_to_postgres.py
```

**期待される出力**:
```
✅ 全データの移行が完了しました！
総移行件数: 110件
```

---

## ステップ2: Gunicornインストール

### 2.1 Gunicornインストール

```bash
cd /path/to/Mirai-Knowledge-Systems/backend
source ../venv_linux/bin/activate

# Gunicornをインストール
pip install gunicorn==21.2.0
```

### 2.2 動作確認（テスト起動）

```bash
# 開発サーバーを停止（起動中の場合）
sudo systemctl stop mirai-knowledge-system.service

# Gunicornでテスト起動
gunicorn --config gunicorn.conf.py app_v2:app
```

別のターミナルで確認：
```bash
curl http://127.0.0.1:8000/api/v1/knowledge
```

データが返ってくればOK！（Ctrl+Cで停止）

---

## ステップ3: Nginx設定

### 3.1 Nginxインストール

```bash
# Ubuntu/Debianの場合
sudo apt update
sudo apt install -y nginx

# Nginxを起動
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 3.2 Nginx設定ファイルのコピー

```bash
# サンプル設定をコピー
sudo cp /path/to/Mirai-Knowledge-Systems/nginx.conf.example \
    /etc/nginx/sites-available/mirai-knowledge-system

# エディタで開く
sudo nano /etc/nginx/sites-available/mirai-knowledge-system
```

### 3.3 ドメイン名の置き換え

以下の箇所を実際のドメイン名に置き換えてください：

```nginx
server_name your-domain.com www.your-domain.com;
```

**例**: `server_name mirai.example.com;`

### 3.4 一時的に無効化（SSL証明書取得まで）

SSL証明書取得前は、HTTPS部分をコメントアウトします。

---

## ステップ4: SSL/TLS証明書設定

詳細は [SSL_TLS_SETUP.md](SSL_TLS_SETUP.md) を参照してください。

### 4.1 Certbotインストール

```bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### 4.2 証明書取得

```bash
# Webルートディレクトリ作成
sudo mkdir -p /var/www/certbot

# 証明書取得
sudo certbot certonly --webroot -w /var/www/certbot \
    -d your-domain.com \
    -d www.your-domain.com \
    --email your-email@example.com \
    --agree-tos
```

### 4.3 Nginx設定を有効化

```bash
# シンボリックリンク作成
sudo ln -s /etc/nginx/sites-available/mirai-knowledge-system \
    /etc/nginx/sites-enabled/

# 設定テスト
sudo nginx -t

# Nginx再起動
sudo systemctl restart nginx
```

---

## ステップ5: systemdサービス更新

### 5.1 Gunicorn対応サービスファイルのコピー

```bash
# 本番用サービスファイルをコピー
sudo cp /path/to/Mirai-Knowledge-Systems/mirai-knowledge-production.service \
    /etc/systemd/system/

# パーミッション設定
sudo chmod 644 /etc/systemd/system/mirai-knowledge-production.service
```

### 5.2 旧サービスの停止

```bash
# 開発用サービスを停止・無効化
sudo systemctl stop mirai-knowledge-system.service
sudo systemctl disable mirai-knowledge-system.service
```

### 5.3 本番サービスの有効化

```bash
# systemdデーモンを再読み込み
sudo systemctl daemon-reload

# 本番サービスを有効化
sudo systemctl enable mirai-knowledge-production.service

# 本番サービスを起動
sudo systemctl start mirai-knowledge-production.service

# ステータス確認
sudo systemctl status mirai-knowledge-production.service
```

**期待される出力**:
```
● mirai-knowledge-production.service - Mirai Knowledge System (Production)
     Loaded: loaded
     Active: active (running)
```

---

## ステップ6: 動作確認

### 6.1 サービス状態確認

```bash
# Gunicornが起動しているか確認
sudo systemctl status mirai-knowledge-production.service

# Nginxが起動しているか確認
sudo systemctl status nginx

# PostgreSQLが起動しているか確認
sudo systemctl status postgresql
```

### 6.2 ポート確認

```bash
# ポート8000（Gunicorn）が待ち受けているか確認
sudo ss -tlnp | grep :8000

# ポート80, 443（Nginx）が待ち受けているか確認
sudo ss -tlnp | grep -E ':80|:443'
```

### 6.3 ログ確認

```bash
# Gunicornログ
sudo journalctl -u mirai-knowledge-production.service -n 50

# Nginxアクセスログ
sudo tail -f /var/log/nginx/mirai-knowledge-access.log

# Nginxエラーログ
sudo tail -f /var/log/nginx/mirai-knowledge-error.log
```

### 6.4 HTTPSアクセステスト

ブラウザで以下のURLにアクセス：

```
https://<your-domain>/login.html
```

- ✅ 緑の鍵マークが表示される
- ✅ ログインページが表示される
- ✅ デモアカウント（admin / admin123）でログインできる
- ✅ ダッシュボードが正常に表示される

### 6.5 API動作確認

```bash
# ナレッジ一覧を取得
curl -k https://<your-domain>/api/v1/knowledge | jq '.data | length'

# ヘルスチェック
curl -k https://<your-domain>/api/v1/health
```

---

## 🐛 トラブルシューティング

### エラー: "502 Bad Gateway"

**原因**: Gunicornが起動していない、またはNginxがGunicornに接続できない

**解決**:
```bash
# Gunicornの状態確認
sudo systemctl status mirai-knowledge-production.service

# エラーログ確認
sudo journalctl -u mirai-knowledge-production.service -n 100

# Gunicornが8000番ポートで待ち受けているか確認
sudo ss -tlnp | grep :8000

# Gunicornを再起動
sudo systemctl restart mirai-knowledge-production.service
```

### エラー: "Permission denied" (PostgreSQL)

**原因**: PostgreSQLの認証設定が不適切

**解決**:
```bash
# pg_hba.confを編集
sudo nano /etc/postgresql/16/main/pg_hba.conf

# 以下を追加:
host    mirai_knowledge_db    mirai_user    127.0.0.1/32    md5

# PostgreSQL再起動
sudo systemctl restart postgresql
```

### エラー: "SSL certificate problem"

**原因**: SSL証明書のパスが間違っている

**解決**:
```bash
# 証明書のパスを確認
sudo certbot certificates

# Nginx設定のパスを修正
sudo nano /etc/nginx/sites-available/mirai-knowledge-system

# Nginx再起動
sudo systemctl restart nginx
```

---

## 🔧 運用・保守

### ログローテーション

Gunicornログの自動ローテーション設定：

```bash
sudo nano /etc/logrotate.d/mirai-knowledge
```

内容：
```
/var/log/mirai-knowledge/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 kensan kensan
    sharedscripts
    postrotate
        systemctl reload mirai-knowledge-production.service > /dev/null
    endscript
}
```

### バックアップ設定

PostgreSQLの自動バックアップ：

```bash
sudo nano /usr/local/bin/backup-mirai-db.sh
```

内容：
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/mirai-knowledge"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U mirai_user mirai_knowledge_db | gzip > $BACKUP_DIR/mirai_$DATE.sql.gz
find $BACKUP_DIR -name "mirai_*.sql.gz" -mtime +7 -delete
```

実行権限を付与：
```bash
sudo chmod +x /usr/local/bin/backup-mirai-db.sh
```

cronで毎日実行：
```bash
sudo crontab -e

# 以下を追加（毎日午前2時に実行）
0 2 * * * /usr/local/bin/backup-mirai-db.sh
```

### モニタリング

システムヘルスチェック：

```bash
# CPU使用率
top -bn1 | grep "Cpu(s)"

# メモリ使用率
free -h

# ディスク使用率
df -h

# Gunicornプロセス数
ps aux | grep gunicorn | wc -l

# PostgreSQL接続数
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='mirai_knowledge_db';"
```

---

## ✅ デプロイ完了チェックリスト

### データベース
- [ ] PostgreSQLがインストールされている
- [ ] mirai_knowledge_dbが作成されている
- [ ] データマイグレーションが完了している
- [ ] PostgreSQLが自動起動設定されている

### アプリケーション
- [ ] Gunicornがインストールされている
- [ ] gunicorn.conf.pyが設定されている
- [ ] .envファイルにMKS_USE_POSTGRESQL=trueが設定されている
- [ ] MKS_ENV=productionが設定されている

### Webサーバー
- [ ] Nginxがインストールされている
- [ ] Nginx設定ファイルが正しく配置されている
- [ ] ドメイン名が正しく設定されている

### SSL/TLS
- [ ] Let's Encrypt証明書が取得されている
- [ ] HTTPSでアクセスできる
- [ ] HTTPからHTTPSへ自動リダイレクトされる
- [ ] 証明書の自動更新が設定されている

### systemd
- [ ] mirai-knowledge-production.serviceが起動している
- [ ] 自動起動が有効化されている
- [ ] ログが正常に出力されている

### 動作確認
- [ ] https://<your-domain>/login.htmlにアクセスできる
- [ ] ログインできる
- [ ] ダッシュボードが表示される
- [ ] APIが正常に応答する
- [ ] データが正しく表示される

---

## 📞 次のステップ

デプロイ完了後、以下を実施してください：

1. **受入テストの実施**: 全機能の動作確認
2. **パフォーマンステスト**: 負荷テストの実施
3. **セキュリティ監査**: OWASP ZAPなどでスキャン
4. **ユーザートレーニング**: エンドユーザー向け研修
5. **運用手順書の整備**: インシデント対応手順の作成

---

**作成日**: 2026-01-01
**バージョン**: v1.0
**最終更新**: 2026-01-01
