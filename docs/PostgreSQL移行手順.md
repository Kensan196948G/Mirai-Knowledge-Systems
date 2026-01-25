# PostgreSQL移行手順書

Mirai Knowledge SystemsのデータストレージをJSONベースからPostgreSQLに移行する手順を説明します。

## 目次

1. [移行の概要](#移行の概要)
2. [前提条件](#前提条件)
3. [移行手順](#移行手順)
4. [検証手順](#検証手順)
5. [ロールバック手順](#ロールバック手順)
6. [トラブルシューティング](#トラブルシューティング)

---

## 移行の概要

### 移行の目的

- **スケーラビリティ**: JSONファイルベースの限界を超え、大量データの管理を可能にする
- **パフォーマンス**: インデックスとクエリ最適化により、検索・集計処理を高速化
- **データ整合性**: トランザクション管理と外部キー制約により、データの整合性を保証
- **同時実行性**: 複数ユーザーの同時アクセスに対応

### 移行方式

本移行では**デュアルモード対応**を採用し、段階的な移行を可能にします：

- **フェーズ1**: PostgreSQL環境構築とテーブル作成
- **フェーズ2**: JSONデータのマイグレーション
- **フェーズ3**: PostgreSQLモードでの動作検証
- **フェーズ4**: 本番切り替え

### アーキテクチャ

```
┌─────────────────────────────────────────┐
│         アプリケーション層               │
│           (app_v2.py)                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      データアクセスレイヤー              │
│        (data_access.py)                 │
│                                         │
│  環境変数: MKS_USE_POSTGRESQL           │
│    ├─ true  → PostgreSQL                │
│    └─ false → JSON Files                │
└──────┬───────────────────┬──────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐    ┌──────────────┐
│ PostgreSQL  │    │  JSON Files  │
│   Database  │    │ (backend/    │
│             │    │   data/)     │
└─────────────┘    └──────────────┘
```

---

## 前提条件

### 必須ソフトウェア

1. **PostgreSQL 12以上**
   ```bash
   # バージョン確認
   psql --version
   ```

2. **Python 3.8以上**
   ```bash
   python3 --version
   ```

3. **必要なPythonパッケージ**
   ```bash
   pip install -r backend/requirements.txt
   ```

### 必須パッケージ

以下のパッケージが`requirements.txt`に含まれていることを確認してください：

```
Flask>=2.3.0
SQLAlchemy>=2.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

### 環境変数設定

`.env`ファイルを作成し、PostgreSQL接続情報を設定：

```bash
cp backend/.env.example backend/.env
```

`backend/.env`を編集：

```bash
# PostgreSQL接続URL
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/mirai_knowledge_db

# PostgreSQL使用フラグ（移行完了後にtrueに変更）
MKS_USE_POSTGRESQL=false

# データベース接続プール設定
MKS_DB_POOL_SIZE=10
MKS_DB_MAX_OVERFLOW=20
MKS_DB_POOL_TIMEOUT=30
MKS_DB_POOL_RECYCLE=3600
```

---

## 移行手順

### ステップ1: PostgreSQLデータベースの作成

#### 1.1 PostgreSQLサーバーの起動確認

```bash
# PostgreSQL起動確認
sudo systemctl status postgresql

# 未起動の場合は起動
sudo systemctl start postgresql
```

#### 1.2 データベース作成

```bash
# PostgreSQLにログイン
sudo -u postgres psql

# データベース作成
CREATE DATABASE mirai_knowledge_db;

# ユーザー作成（オプション）
CREATE USER mirai_user WITH PASSWORD 'secure_password';

# 権限付与
GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge_db TO mirai_user;

# 終了
\q
```

#### 1.3 接続確認

```bash
# 接続テスト
psql -U postgres -d mirai_knowledge_db -c "SELECT version();"
```

### ステップ2: テーブルとスキーマの作成

#### 2.1 データベース初期化スクリプトの実行

```bash
cd /path/to/Mirai-Knowledge-Systems

# テーブル作成
python3 backend/scripts/create_database.py
```

**出力例:**
```
============================================================
Mirai Knowledge System - データベース作成
============================================================

接続URL: postgresql://postgres:***@localhost:5432/mirai_knowledge_db

============================================================
データベース接続確認
============================================================
✅ PostgreSQL バージョン: PostgreSQL 14.x
✅ データベース名: mirai_knowledge_db
✅ スキーマ: audit, auth, public

============================================================
スキーマ作成
============================================================
✅ スキーマ 'public' を作成しました
✅ スキーマ 'auth' を作成しました
✅ スキーマ 'audit' を作成しました

============================================================
テーブル作成
============================================================
✅ 全テーブルを作成しました

作成されたテーブル:
------------------------------------------------------------
  - auth.users
  - auth.roles
  - auth.permissions
  - auth.user_roles
  - auth.role_permissions
  - public.knowledge
  - public.sop
  - public.regulations
  - public.incidents
  - public.consultations
  - public.approvals
  - public.notifications
  - public.notification_reads
  - audit.access_logs
  - audit.change_logs
  - audit.distribution_logs
```

#### 2.2 テーブル構造の確認

```bash
# PostgreSQLに接続
psql -U postgres -d mirai_knowledge_db

# テーブル一覧表示
\dt public.*
\dt auth.*
\dt audit.*

# Knowledgeテーブルの構造確認
\d public.knowledge

# インデックス確認
\di public.knowledge*

# 終了
\q
```

### ステップ3: JSONデータのマイグレーション

#### 3.1 既存データのバックアップ

**重要**: 移行前に必ずバックアップを作成してください。

```bash
# データディレクトリのバックアップ
cd /path/to/Mirai-Knowledge-Systems
cp -r backend/data backend/data.backup.$(date +%Y%m%d_%H%M%S)
```

#### 3.2 マイグレーション実行

```bash
# マイグレーションスクリプトを実行
python3 backend/migrate_json_to_postgres.py
```

**出力例:**
```
============================================================
JSONデータをPostgreSQLに移行
============================================================

✅ ナレッジ: 45件を移行しました
✅ SOP: 23件を移行しました
✅ 規格・法令: 12件を移行しました
✅ インシデント: 8件を移行しました
✅ 相談: 15件を移行しました
✅ 承認: 6件を移行しました
✅ 通知: 32件を移行しました

============================================================
移行完了
============================================================
合計: 141件のレコードを移行しました
```

#### 3.3 マイグレーションエラーの対処

エラーが発生した場合：

```bash
# エラーログの確認
python3 backend/migrate_json_to_postgres.py 2>&1 | tee migration.log

# データベースのロールバック（必要な場合）
python3 backend/scripts/create_database.py --drop
```

---

## 検証手順

### ステップ4: マイグレーション結果の検証

#### 4.1 自動検証スクリプトの実行

```bash
# 検証スクリプトを実行
python3 backend/scripts/verify_migration.py
```

**出力例:**
```
============================================================
PostgreSQL マイグレーション検証
============================================================

レコード数検証:
------------------------------------------------------------
✅ ナレッジ: 45件 (JSON) = 45件 (DB)
✅ SOP: 23件 (JSON) = 23件 (DB)
✅ インシデント: 8件 (JSON) = 8件 (DB)
✅ 相談: 15件 (JSON) = 15件 (DB)
✅ 承認: 6件 (JSON) = 6件 (DB)
✅ 通知: 32件 (JSON) = 32件 (DB)
✅ ユーザー: 3件 (JSON) = 3件 (DB)

合計: 132件 (JSON) vs 132件 (DB)

ナレッジのデータ整合性チェック（サンプル5件）:
------------------------------------------------------------
✅ ID=1: タイトル一致
✅ ID=2: タイトル一致
✅ ID=3: タイトル一致
✅ ID=4: タイトル一致
✅ ID=5: タイトル一致

インデックス検証:
------------------------------------------------------------
✅ knowledge.idx_knowledge_category
✅ knowledge.idx_knowledge_status
✅ knowledge.idx_knowledge_updated
✅ knowledge.idx_knowledge_title
✅ knowledge.idx_knowledge_owner
✅ knowledge.idx_knowledge_project
✅ sop.idx_sop_category
✅ sop.idx_sop_status
✅ sop.idx_sop_title
✅ sop.idx_sop_version

外部キー検証:
------------------------------------------------------------
✅ knowledge: 2個の外部キー
   - knowledge_created_by_id_fkey: created_by_id -> users.id
   - knowledge_updated_by_id_fkey: updated_by_id -> users.id

============================================================
検証結果サマリー
============================================================

✅ すべての検証に合格しました

============================================================
検証完了
============================================================
```

#### 4.2 手動検証

PostgreSQLで直接データを確認：

```bash
psql -U postgres -d mirai_knowledge_db

-- ナレッジ件数確認
SELECT COUNT(*) FROM public.knowledge;

-- カテゴリ別件数
SELECT category, COUNT(*) FROM public.knowledge GROUP BY category;

-- 最新5件
SELECT id, title, category, created_at FROM public.knowledge ORDER BY created_at DESC LIMIT 5;

-- ユーザー一覧
SELECT id, username, full_name, department FROM auth.users;
```

### ステップ5: PostgreSQLモードでの動作確認

#### 5.1 環境変数の変更

`backend/.env`を編集：

```bash
# PostgreSQLモードに切り替え
MKS_USE_POSTGRESQL=true
```

#### 5.2 アプリケーションの起動

```bash
# アプリケーション起動
cd /path/to/Mirai-Knowledge-Systems
python3 backend/app_v2.py
```

**起動確認:**
```
============================================================
建設土木ナレッジシステム - サーバー起動中
============================================================
環境モード: development
[DEVELOPMENT] 開発環境設定が有効です
[OK] デモユーザーを作成しました
   - admin / admin123 (管理者)
   - yamada / yamada123 (施工管理)
   - partner / partner123 (協力会社)
アクセスURL: http://localhost:5100
============================================================
```

#### 5.3 APIエンドポイントのテスト

別のターミナルでAPIをテスト：

```bash
# ログインテスト
curl -X POST http://localhost:5100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# レスポンス例:
# {"success":true,"data":{"access_token":"eyJ...","user":{...}}}

# トークンを環境変数に保存
export TOKEN="eyJ..."

# ナレッジ一覧取得テスト
curl -X GET http://localhost:5100/api/v1/knowledge \
  -H "Authorization: Bearer $TOKEN"

# 検索テスト
curl -X GET "http://localhost:5100/api/v1/knowledge?search=安全" \
  -H "Authorization: Bearer $TOKEN"

# ナレッジ作成テスト
curl -X POST http://localhost:5100/api/v1/knowledge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "テストナレッジ",
    "summary": "PostgreSQL移行後のテスト",
    "content": "データベース移行が正常に完了しました",
    "category": "technology",
    "owner": "admin",
    "tags": ["test", "migration"]
  }'
```

#### 5.4 WebUIでの動作確認

ブラウザで`http://localhost:5100`にアクセスし、以下を確認：

1. ログイン機能
2. ナレッジ一覧表示
3. 検索機能
4. ナレッジ作成
5. ダッシュボード統計

---

## ロールバック手順

問題が発生した場合、以下の手順でJSONモードに戻すことができます。

### 緊急ロールバック（即座にJSONモードに戻す）

```bash
# 1. 環境変数を変更
# backend/.env
MKS_USE_POSTGRESQL=false

# 2. アプリケーションを再起動
# （既存のJSONファイルがそのまま使用されます）
```

### 完全ロールバック（PostgreSQLデータベースを削除）

```bash
# 1. PostgreSQLデータベース削除
sudo -u postgres psql -c "DROP DATABASE mirai_knowledge_db;"

# 2. バックアップから復元（必要な場合）
cp -r backend/data.backup.YYYYMMDD_HHMMSS/* backend/data/

# 3. 環境変数を元に戻す
# backend/.env
MKS_USE_POSTGRESQL=false
```

---

## トラブルシューティング

### 問題1: PostgreSQL接続エラー

**症状:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解決策:**

```bash
# 1. PostgreSQLサービスの確認
sudo systemctl status postgresql

# 2. 未起動の場合は起動
sudo systemctl start postgresql

# 3. 接続設定の確認
# backend/.env の DATABASE_URL が正しいか確認

# 4. ファイアウォール確認（リモート接続の場合）
sudo ufw status
sudo ufw allow 5432/tcp
```

### 問題2: マイグレーションでデータ型エラー

**症状:**
```
psycopg2.errors.InvalidTextRepresentation: invalid input syntax for type date
```

**解決策:**

```bash
# 1. JSONデータの日付形式を確認
# 正しい形式: "2024-01-15" または "2024-01-15T10:30:00"

# 2. migrate_json_to_postgres.py の parse_datetime 関数を確認

# 3. 問題のあるレコードを特定
grep -n "date" backend/data/*.json

# 4. 修正後、再度マイグレーション
python3 backend/scripts/create_database.py --drop
python3 backend/migrate_json_to_postgres.py
```

### 問題3: インデックスが作成されない

**症状:**
検証スクリプトで「インデックス未作成」の警告

**解決策:**

```bash
# PostgreSQLで手動作成
psql -U postgres -d mirai_knowledge_db

CREATE INDEX idx_knowledge_title ON public.knowledge(title);
CREATE INDEX idx_knowledge_owner ON public.knowledge(owner);
CREATE INDEX idx_knowledge_project ON public.knowledge(project);

# 確認
\di public.knowledge*
```

### 問題4: パフォーマンス低下

**症状:**
検索・一覧表示が遅い

**解決策:**

```bash
# 1. VACUUM ANALYZE実行（統計情報更新）
psql -U postgres -d mirai_knowledge_db -c "VACUUM ANALYZE;"

# 2. 接続プール設定の調整（backend/.env）
MKS_DB_POOL_SIZE=20
MKS_DB_MAX_OVERFLOW=40

# 3. クエリプランの確認
psql -U postgres -d mirai_knowledge_db

EXPLAIN ANALYZE SELECT * FROM public.knowledge WHERE category = 'technology';

# 4. インデックスの追加確認
\di public.knowledge*
```

### 問題5: 文字化け

**症状:**
日本語が正しく表示されない

**解決策:**

```bash
# データベースのエンコーディング確認
psql -U postgres -d mirai_knowledge_db -c "\l"

# UTF8でない場合は再作成
sudo -u postgres psql
DROP DATABASE mirai_knowledge_db;
CREATE DATABASE mirai_knowledge_db WITH ENCODING 'UTF8' LC_COLLATE='ja_JP.UTF-8' LC_CTYPE='ja_JP.UTF-8';
```

---

## パフォーマンスチューニング（オプション）

### インデックスの追加

よく使用される検索条件に対してインデックスを追加：

```sql
-- 複合インデックス（カテゴリ + ステータス）
CREATE INDEX idx_knowledge_cat_status ON public.knowledge(category, status);

-- 全文検索用インデックス（日本語対応）
CREATE INDEX idx_knowledge_title_gin ON public.knowledge USING gin(to_tsvector('simple', title));
CREATE INDEX idx_knowledge_content_gin ON public.knowledge USING gin(to_tsvector('simple', content));
```

### 定期メンテナンス

cron等で定期的にVACUUM/ANALYZEを実行：

```bash
# crontab -e
0 2 * * * psql -U postgres -d mirai_knowledge_db -c "VACUUM ANALYZE;"
```

---

## まとめ

この手順書に従うことで、Mirai Knowledge SystemsをJSONベースからPostgreSQLに段階的に移行できます。

### チェックリスト

- [ ] PostgreSQLインストール完了
- [ ] データベース作成完了
- [ ] テーブル・スキーマ作成完了
- [ ] JSONデータバックアップ完了
- [ ] データマイグレーション完了
- [ ] 検証スクリプト実行完了（エラーなし）
- [ ] PostgreSQLモードでの動作確認完了
- [ ] WebUI動作確認完了
- [ ] パフォーマンステスト完了
- [ ] ロールバック手順の理解

### サポート

問題が発生した場合は、以下を確認してください：

1. ログファイル: `backend/logs/app.log`
2. PostgreSQLログ: `/var/log/postgresql/`
3. マイグレーションログ: `migration.log`

---

**作成日**: 2025-12-30
**バージョン**: 1.0
**作成者**: Mirai Knowledge Systems Development Team
