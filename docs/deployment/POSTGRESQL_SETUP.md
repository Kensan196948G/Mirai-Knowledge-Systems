# PostgreSQL セットアップガイド

**対象**: Mirai Knowledge System の本番環境移行
**目的**: JSONストレージからPostgreSQLへの移行

---

## 📋 目次

1. [PostgreSQLインストール](#postgresqlインストール)
2. [データベース作成](#データベース作成)
3. [環境変数設定](#環境変数設定)
4. [データマイグレーション](#データマイグレーション)
5. [動作確認](#動作確認)
6. [トラブルシューティング](#トラブルシューティング)

---

## 🐳 簡易セットアップ（任意）

開発・検証用途では `docker-compose.yml` を使ってPostgreSQLを起動できます。

```bash
cd /path/to/Mirai-Knowledge-Systems
docker-compose up -d
```

Linux環境での初期化を自動化する場合は `backend/scripts/setup_postgres.sh` を利用できます。

---

## 🔧 PostgreSQLインストール

### Ubuntu/Debian

```bash
# 1. PostgreSQLリポジトリを追加
sudo apt update
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# 2. PostgreSQL 16をインストール
sudo apt update
sudo apt install -y postgresql-16 postgresql-contrib-16

# 3. PostgreSQLサービスの起動と自動起動設定
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 4. バージョン確認
psql --version
# 出力例: psql (PostgreSQL) 16.1
```

### その他のLinuxディストリビューション

**RHEL/CentOS/Rocky Linux**:
```bash
sudo dnf install -y postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Arch Linux**:
```bash
sudo pacman -S postgresql
sudo -u postgres initdb -D /var/lib/postgres/data
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

## 🗄️ データベース作成

### 1. PostgreSQLユーザーに切り替え

```bash
sudo -u postgres psql
```

### 2. データベースとユーザーを作成

PostgreSQLプロンプトで以下を実行：

```sql
-- データベースユーザーを作成（パスワードは変更してください）
CREATE USER mirai_user WITH PASSWORD 'your-secure-password-here';

-- データベースを作成
CREATE DATABASE mirai_knowledge_db OWNER mirai_user;

-- 権限を付与
GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge_db TO mirai_user;

-- スキーマ作成権限を付与
\c mirai_knowledge_db
GRANT ALL ON SCHEMA public TO mirai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mirai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mirai_user;

-- 終了
\q
```

### 3. 接続テスト

```bash
# mirai_userでデータベースに接続できるか確認
psql -U mirai_user -d mirai_knowledge_db -h localhost

# パスワードを入力してログインできればOK
# 終了: \q
```

---

## ⚙️ 環境変数設定

### .envファイルの更新

`backend/.env` ファイルを編集：

```bash
cd /path/to/Mirai-Knowledge-Systems/backend
nano .env
```

以下の設定を追加/更新：

```bash
# PostgreSQL使用フラグ
MKS_USE_POSTGRESQL=true

# PostgreSQL接続URL
# 形式: postgresql://[user]:[password]@[host]:[port]/[database]
DATABASE_URL=postgresql://mirai_user:your-secure-password-here@localhost:5432/mirai_knowledge_db

# PostgreSQL接続プール設定
MKS_DB_POOL_SIZE=10
MKS_DB_MAX_OVERFLOW=20
MKS_DB_POOL_TIMEOUT=30
MKS_DB_POOL_RECYCLE=3600
MKS_DB_ECHO=false
```

**重要**: `your-secure-password-here` を実際に設定したパスワードに置き換えてください。

### 設定の確認

```bash
# .envファイルの内容を確認
grep -E "MKS_USE_POSTGRESQL|DATABASE_URL" .env
```

---

## 🔄 データマイグレーション

### 1. 依存パッケージの確認

```bash
cd /path/to/Mirai-Knowledge-Systems/backend

# 仮想環境をアクティベート
source ../venv_linux/bin/activate

# psycopg2がインストールされているか確認
pip list | grep psycopg2

# なければインストール
pip install psycopg2-binary
```

### 2. データベーススキーマの作成

```bash
# Pythonインタープリターを起動
python3

# 以下をPythonプロンプトで実行
>>> from database import engine, Base
>>> Base.metadata.create_all(bind=engine)
>>> print("✅ スキーマ作成完了")
>>> exit()
```

成功すれば、全テーブルが作成されます。

### 3. JSONデータの移行

```bash
# マイグレーションスクリプトを実行
python3 migrate_json_to_postgres.py
```

**期待される出力**:
```
============================================================
JSON → PostgreSQL データ移行
============================================================
📊 ナレッジ: 45件 移行完了
📋 SOP: 20件 移行完了
📜 法令: 15件 移行完了
🚨 事故レポート: 12件 移行完了
💬 専門家相談: 8件 移行完了
✅ 承認フロー: 10件 移行完了
============================================================
✅ 全データの移行が完了しました！
総移行件数: 110件
============================================================
```

### 4. データ確認

```bash
# PostgreSQLに接続
psql -U mirai_user -d mirai_knowledge_db -h localhost
```

PostgreSQLプロンプトで以下を実行：

```sql
-- テーブル一覧を表示
\dt

-- ナレッジ件数を確認
SELECT COUNT(*) FROM knowledge;

-- SOP件数を確認
SELECT COUNT(*) FROM sop;

-- サンプルデータを表示
SELECT id, title, category FROM knowledge LIMIT 5;

-- 終了
\q
```

---

## ✅ 動作確認

### 1. サービスの停止（起動中の場合）

```bash
sudo systemctl stop mirai-knowledge-system.service
```

### 2. 手動起動でテスト

```bash
cd /path/to/Mirai-Knowledge-Systems/backend
source ../venv_linux/bin/activate
python3 app_v2.py
```

**期待される出力**:
```
[INIT] PostgreSQL接続: OK
[INIT] データベース準備完了
============================================================
建設土木ナレッジシステム - サーバー起動中
============================================================
環境モード: development
データベース: PostgreSQL
アクセスURL: http://localhost:5100
============================================================
```

### 3. API動作確認

別のターミナルで以下を実行：

```bash
# ナレッジ一覧を取得
curl http://localhost:5100/api/v1/knowledge | jq '.data | length'

# 出力: 移行したナレッジ件数が表示される
```

### 4. ブラウザで確認

```
http://<server-ip>:5100/login.html
```

ログインしてダッシュボードが正常に表示されればOK！

---

## 🐛 トラブルシューティング

### エラー: "role \"mirai_user\" does not exist"

**原因**: データベースユーザーが作成されていない

**解決**:
```bash
sudo -u postgres psql
CREATE USER mirai_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge_db TO mirai_user;
\q
```

### エラー: "database \"mirai_knowledge_db\" does not exist"

**原因**: データベースが作成されていない

**解決**:
```bash
sudo -u postgres psql
CREATE DATABASE mirai_knowledge_db OWNER mirai_user;
\q
```

### エラー: "FATAL: Peer authentication failed for user \"mirai_user\""

**原因**: PostgreSQLの認証設定が不適切

**解決**:
```bash
# pg_hba.confを編集
sudo nano /etc/postgresql/16/main/pg_hba.conf

# 以下の行を探して変更:
# local   all             all                                     peer
# ↓ これに変更:
local   all             all                                     md5

# IPv4 local connectionsセクションに以下を追加:
host    all             all             127.0.0.1/32            md5
host    all             all             0.0.0.0/0               md5

# PostgreSQLを再起動
sudo systemctl restart postgresql
```

### エラー: "could not connect to server: Connection refused"

**原因**: PostgreSQLサービスが起動していない

**解決**:
```bash
# PostgreSQLの起動
sudo systemctl start postgresql

# ステータス確認
sudo systemctl status postgresql

# 自動起動設定
sudo systemctl enable postgresql
```

### エラー: "relation \"knowledge\" does not exist"

**原因**: データベーススキーマが作成されていない

**解決**:
```bash
cd /path/to/Mirai-Knowledge-Systems/backend
source ../venv_linux/bin/activate
python3 << EOF
from database import engine, Base
Base.metadata.create_all(bind=engine)
print("✅ スキーマ作成完了")
EOF
```

### マイグレーションが途中で失敗した場合

**全データをリセットして再実行**:
```bash
# PostgreSQLに接続
sudo -u postgres psql

# 既存のデータベースを削除して再作成
DROP DATABASE IF EXISTS mirai_knowledge_db;
CREATE DATABASE mirai_knowledge_db OWNER mirai_user;
\q

# スキーマ作成とマイグレーションを再実行
cd /path/to/Mirai-Knowledge-Systems/backend
python3 << EOF
from database import engine, Base
Base.metadata.create_all(bind=engine)
print("✅ スキーマ作成完了")
EOF

python3 migrate_json_to_postgres.py
```

---

## 🔒 セキュリティ設定

### パスワードの安全な保存

**.envファイルのパーミッション設定**:
```bash
chmod 600 /path/to/Mirai-Knowledge-Systems/backend/.env
```

### 外部アクセスの制限（本番環境）

```bash
# pg_hba.confを編集
sudo nano /etc/postgresql/16/main/pg_hba.conf

# ローカルホストのみ許可（本番環境推奨）
host    mirai_knowledge_db    mirai_user    127.0.0.1/32    md5

# 特定IPのみ許可する場合
# host    mirai_knowledge_db    mirai_user    192.168.0.0/24    md5

# PostgreSQLを再起動
sudo systemctl restart postgresql
```

---

## 📊 パフォーマンス確認

### クエリ性能の確認

```bash
psql -U mirai_user -d mirai_knowledge_db -h localhost
```

```sql
-- EXPLAIN ANALYZEで実行計画を確認
EXPLAIN ANALYZE
SELECT * FROM knowledge
WHERE category = '施工計画'
ORDER BY updated_at DESC
LIMIT 10;

-- インデックスの使用状況を確認
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### データベースサイズの確認

```sql
-- データベースサイズ
SELECT pg_size_pretty(pg_database_size('mirai_knowledge_db'));

-- テーブル別サイズ
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🔄 ロールバック手順

PostgreSQL移行後に問題が発生した場合、JSON方式に戻す方法：

### 1. .envファイルを更新

```bash
# MKS_USE_POSTGRESQLをfalseに変更
sed -i 's/MKS_USE_POSTGRESQL=true/MKS_USE_POSTGRESQL=false/' backend/.env
```

### 2. サービスを再起動

```bash
sudo systemctl restart mirai-knowledge-system.service
```

これでJSON方式に戻ります。

---

## ✅ チェックリスト

PostgreSQL移行完了時の確認項目：

- [ ] PostgreSQL 16がインストールされている
- [ ] PostgreSQLサービスが起動している
- [ ] mirai_knowledge_dbデータベースが作成されている
- [ ] mirai_userユーザーが作成されている
- [ ] .envファイルにDATABASE_URLが設定されている
- [ ] MKS_USE_POSTGRESQL=trueが設定されている
- [ ] スキーマ（テーブル）が作成されている
- [ ] JSONデータが全てマイグレーションされている
- [ ] app_v2.pyが正常に起動する
- [ ] APIが正常に応答する
- [ ] WebUIが正常に動作する
- [ ] 全テストが合格する

---

## 📞 次のステップ

PostgreSQL移行が完了したら、次は本番環境デプロイ設定に進みます：

1. **Gunicorn設定** - 本番用WSGIサーバー
2. **Nginx設定** - リバースプロキシとSSL/TLS
3. **systemd更新** - Gunicorn対応サービス

詳細は次のセクションで説明します。

---

**作成日**: 2026-01-01
**バージョン**: v1.0
