# データベースマイグレーション（Alembic）ガイド

## 概要

このプロジェクトでは、データベーススキーマの変更を管理するために**Alembic**を使用しています。Alembicは、SQLAlchemyベースのデータベースマイグレーションツールです。

## セットアップ状況

✅ Alembicがインストール済み（`requirements.txt`に含まれています）
✅ マイグレーションディレクトリが初期化済み（`backend/migrations/`）
✅ `env.py`が設定済み（`models.py`からメタデータを自動取得）
✅ 初期マイグレーションテンプレートが作成済み

## ディレクトリ構造

```
backend/
├── alembic.ini                    # Alembic設定ファイル
├── migrations/                    # マイグレーションディレクトリ
│   ├── env.py                     # マイグレーション環境設定
│   ├── script.py.mako             # マイグレーションテンプレート
│   ├── README                     # Alembic README
│   └── versions/                  # マイグレーションバージョンファイル
│       └── c1104acd2fa6_initial_database_schema.py
└── models.py                      # データベースモデル
```

## 使用方法

### 1. データベース準備

PostgreSQLサーバーを起動し、データベースを作成します：

```bash
# PostgreSQLサービス起動（Linuxの場合）
sudo systemctl start postgresql

# データベース作成
sudo -u postgres psql
CREATE DATABASE mirai_knowledge_db;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE mirai_knowledge_db TO postgres;
\q
```

### 2. 環境変数設定

`backend/.env`ファイルにデータベースURLを設定：

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/mirai_knowledge_db
MKS_USE_POSTGRESQL=true
```

### 3. マイグレーションの作成

#### 自動生成（推奨）

`models.py`の変更を自動検出してマイグレーションを生成：

```bash
cd backend
python3 -m alembic revision --autogenerate -m "変更内容の説明"
```

**例**:
```bash
python3 -m alembic revision --autogenerate -m "Add email field to User model"
```

#### 手動作成

```bash
cd backend
python3 -m alembic revision -m "変更内容の説明"
```

生成されたファイル（`migrations/versions/xxxxx_変更内容の説明.py`）を編集して、`upgrade()`と`downgrade()`関数を実装します。

### 4. マイグレーションの適用

最新バージョンまでマイグレーション：

```bash
cd backend
python3 -m alembic upgrade head
```

特定のバージョンまでマイグレーション：

```bash
python3 -m alembic upgrade <revision_id>
```

### 5. マイグレーションの取り消し

1つ前のバージョンに戻す：

```bash
cd backend
python3 -m alembic downgrade -1
```

特定のバージョンに戻す：

```bash
python3 -m alembic downgrade <revision_id>
```

すべてのマイグレーションを取り消す：

```bash
python3 -m alembic downgrade base
```

### 6. マイグレーション履歴の確認

現在のバージョンを確認：

```bash
cd backend
python3 -m alembic current
```

マイグレーション履歴を表示：

```bash
python3 -m alembic history --verbose
```

## 一般的なワークフロー

### 新しいテーブルを追加する場合

1. `backend/models.py`に新しいモデルクラスを追加：

```python
class NewTable(Base):
    __tablename__ = 'new_table'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

2. マイグレーションを自動生成：

```bash
python3 -m alembic revision --autogenerate -m "Add new_table"
```

3. 生成されたマイグレーションファイルを確認：

```bash
cat migrations/versions/xxxxx_add_new_table.py
```

4. マイグレーションを適用：

```bash
python3 -m alembic upgrade head
```

### カラムを追加する場合

1. `backend/models.py`の既存モデルに新しいカラムを追加：

```python
class User(Base):
    # ... 既存のカラム ...
    email = Column(String(255), unique=True)  # 新規追加
```

2. マイグレーションを自動生成：

```bash
python3 -m alembic revision --autogenerate -m "Add email to User model"
```

3. マイグレーションを適用：

```bash
python3 -m alembic upgrade head
```

## トラブルシューティング

### エラー: "connection refused"

**原因**: PostgreSQLサーバーが起動していない

**解決策**:
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

### エラー: "Target database is not up to date"

**原因**: データベースが最新のマイグレーションまで適用されていない

**解決策**:
```bash
python3 -m alembic upgrade head
```

### エラー: "Can't locate revision identified by 'xxxxx'"

**原因**: マイグレーションファイルが削除されたか、移動された

**解決策**:
1. `migrations/versions/`ディレクトリを確認
2. 削除したマイグレーションを復元するか、データベースをリセット：

```bash
# データベースをリセット（注意: すべてのデータが削除されます）
python3 -m alembic downgrade base
python3 -m alembic upgrade head
```

### マイグレーションの競合

複数のブランチで同時にマイグレーションを作成した場合、マージ時に競合が発生する可能性があります。

**解決策**:
```bash
# マイグレーション履歴をマージ
python3 -m alembic merge heads -m "Merge migrations"
python3 -m alembic upgrade head
```

## ベストプラクティス

1. **マイグレーションの確認**: 自動生成されたマイグレーションは必ず確認してから適用する
2. **テスト環境で検証**: 本番環境に適用する前に、テスト環境で動作確認する
3. **バックアップ**: マイグレーション適用前に必ずデータベースをバックアップする
4. **コミット分離**: マイグレーションファイルは専用のコミットにする
5. **downgrade実装**: `upgrade()`だけでなく`downgrade()`も適切に実装する

## 本番環境でのマイグレーション

### ステップ1: バックアップ

```bash
pg_dump -U postgres mirai_knowledge_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### ステップ2: アプリケーション停止

```bash
sudo systemctl stop mirai-knowledge-production.service
```

### ステップ3: マイグレーション適用

```bash
cd /path/to/Mirai-Knowledge-Systems/backend
source venv/bin/activate
python3 -m alembic upgrade head
```

### ステップ4: アプリケーション再起動

```bash
sudo systemctl start mirai-knowledge-production.service
sudo systemctl status mirai-knowledge-production.service
```

### ステップ5: 動作確認

```bash
curl http://localhost:8000/health
```

## 参考リンク

- [Alembic公式ドキュメント](https://alembic.sqlalchemy.org/)
- [SQLAlchemy公式ドキュメント](https://www.sqlalchemy.org/)
- [PostgreSQLセットアップガイド](./POSTGRESQL_SETUP.md)
