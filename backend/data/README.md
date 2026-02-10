# backend/data/ ディレクトリ

## 📋 概要

このディレクトリは**開発環境専用**のJSONデータストレージです。

## 🎯 用途

- **開発環境**: JSON形式でデータを保存（簡易セットアップ）
- **本番環境**: PostgreSQL 16.11を使用（このディレクトリは未使用）

## 📁 ファイル構成

```
backend/data/
├── .gitkeep           # Gitトラッキング用
├── README.md          # このファイル
├── users.json         # ユーザーデータ（開発環境のみ）
├── knowledge.json     # ナレッジデータ（開発環境のみ）
├── audit_logs.json    # 監査ログ（開発環境のみ）
└── ...                # その他のデータファイル
```

**重要**: `*.json` ファイルは `.gitignore` で除外されています。

## 🔧 初期化方法

### 開発環境起動時

```bash
cd backend
export MKS_ENV=development
python3 app_v2.py
```

初回起動時に以下のファイルが自動生成されます：
- `users.json` - デモユーザー（admin@example.com等）
- `knowledge.json` - サンプルナレッジデータ
- その他必要なデータファイル

### データリセット

```bash
# 開発データを削除（再生成される）
rm -f backend/data/*.json
python3 backend/app_v2.py
```

## 🔐 セキュリティ

### ⚠️ 絶対に含めないファイル

以下のファイルは**絶対にGitにコミットしない**：
- `*.json` - ユーザーデータ、パスワードハッシュ等
- `.env` - 環境変数、秘密鍵
- `*.db` - SQLiteデータベース

### ✅ Gitignore設定

`.gitignore` に以下が設定されています：
```
backend/data/*.json
backend/data/*.db
backend/data/*.sqlite
!backend/data/.gitkeep
!backend/data/README.md
```

## 🚀 本番環境

本番環境では**PostgreSQL 16.11**を使用します：
- **データベース名**: mirai_knowledge_production
- **接続**: Unix socket `/var/run/postgresql/`
- **ユーザー**: mirai_user
- **移行ツール**: Alembic

このディレクトリは本番環境では使用されません。

## 📊 データ移行

### 開発環境 → 本番環境

```bash
# JSON → PostgreSQL移行
python3 backend/migrate_json_to_postgres.py

# 移行確認
python3 backend/scripts/validate_migration.py
```

## 🔗 関連ドキュメント

- `docs/deployment/DATABASE_MIGRATION_GUIDE.md` - データベース移行ガイド
- `backend/models.py` - データモデル定義
- `backend/database.py` - データベース接続
- `.claude/CLAUDE.md` - プロジェクト全体の設定

## 📅 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-02-10 | 初版作成 - 開発環境整備 |

---

**注意**: このディレクトリのファイルは機密情報を含む可能性があるため、取り扱いには注意してください。
