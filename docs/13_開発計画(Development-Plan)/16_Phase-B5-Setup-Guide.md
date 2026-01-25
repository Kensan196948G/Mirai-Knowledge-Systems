# Phase B-5 セットアップガイド

## PostgreSQLセットアップ（2つの方法）

### 方法1: Docker Composeを使用（推奨）

Dockerがインストールされている場合、最も簡単です。

```bash
# プロジェクトルートで実行
docker-compose up -d

# PostgreSQLが起動したか確認
docker-compose ps

# ログ確認
docker-compose logs postgres
```

PostgreSQLは `localhost:5432` で利用可能になります。

### 方法2: ローカルにPostgreSQLをインストール

#### Windows
1. [PostgreSQL公式サイト](https://www.postgresql.org/download/windows/)からインストーラーをダウンロード
2. インストール時の設定:
   - ポート: 5432
   - パスワード: password（または任意）
   - ロケール: Japanese, Japan

3. pgAdminまたはpsqlで接続確認:
```bash
psql -U postgres
```

4. データベース作成:
```sql
CREATE DATABASE mirai_knowledge_db;
```

## パッケージインストール

```bash
cd backend
pip install -r requirements.txt
```

## データベース初期化

### スキーマとテーブル作成

```bash
cd backend
python seed_data.py
```

実行すると以下が作成されます:
- スキーマ（public, auth, audit）
- 全15テーブル
- 役割（7種類）
- 権限（16種類）
- デモユーザー（3名）

### デモユーザー

| ユーザー名 | パスワード | 役割 | 部門 |
|-----------|----------|------|------|
| admin | admin123 | 管理者 | システム管理部 |
| yamada | yamada123 | 施工管理 | 施工管理 |
| suzuki | suzuki123 | 品質保証 | 品質保証 |

## 動作確認

### 1. データベース接続確認

```bash
# Windowsの場合
psql -U postgres -d mirai_knowledge_db

# 接続後
\dt public.*     # publicスキーマのテーブル一覧
\dt auth.*       # authスキーマのテーブル一覧
\dt audit.*      # auditスキーマのテーブル一覧
```

### 2. デモデータ確認

```sql
-- ユーザー確認
SELECT id, username, full_name, department FROM auth.users;

-- 役割確認
SELECT * FROM auth.roles;

-- 権限確認
SELECT r.name as role, p.name as permission 
FROM auth.role_permissions rp
JOIN auth.roles r ON r.id = rp.role_id
JOIN auth.permissions p ON p.id = rp.permission_id
ORDER BY r.name, p.name;
```

## JSONデータの移行

既存のJSONデータをPostgreSQLに移行する場合:

```bash
cd backend
python migrate_json_to_postgres.py
```

このスクリプトは以下を移行します:
- `data/knowledge.json` → `public.knowledge`
- `data/sop.json` → `public.sop`
- `data/regulations.json` → `public.regulations`
- `data/incidents.json` → `public.incidents`
- `data/consultations.json` → `public.consultations`
- `data/approvals.json` → `public.approvals`

## トラブルシューティング

### エラー: "could not connect to server"

**原因**: PostgreSQLが起動していない

**解決方法**:
```bash
# Docker Composeの場合
docker-compose up -d

# ローカルインストールの場合（Windows）
# サービスから PostgreSQL を起動
```

### エラー: "password authentication failed"

**原因**: パスワードが間違っている

**解決方法**:
- `backend/.env` の `DATABASE_URL` を確認
- PostgreSQLのパスワードと一致させる

### エラー: "database does not exist"

**原因**: データベースが作成されていない

**解決方法**:
```bash
# psqlで接続
psql -U postgres

# データベース作成
CREATE DATABASE mirai_knowledge_db;
```

### エラー: "schema does not exist"

**原因**: スキーマが作成されていない

**解決方法**:
```bash
python seed_data.py
```

## 次のステップ

データベースセットアップが完了したら、Phase B-5の実装を続けます:

1. ✅ PostgreSQLセットアップ
2. ✅ パッケージインストール
3. ✅ データベース初期化
4. ⬜ JWT認証の統合 → 次の作業
5. ⬜ APIのPostgreSQL対応
6. ⬜ 既存データの移行

---

**準備完了！** 次は `app.py` をPostgreSQL対応にアップグレードします。
