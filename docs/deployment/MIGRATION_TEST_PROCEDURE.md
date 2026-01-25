# データ移行テスト実行手順書

## 📋 概要

本ドキュメントは、開発環境（JSON）から本番環境（PostgreSQL）へのデータ移行テスト手順を定義します。

---

## 🔧 前提条件

### 環境要件

- Python 3.10+
- PostgreSQL 16.x
- 開発環境JSONデータ（backend/data/）
- 本番環境データベース接続情報

### 必要なパッケージ

```bash
pip install psycopg2-binary sqlalchemy
```

---

## 🚀 テスト実行手順

### Step 1: テスト環境の準備

```bash
# 1. プロジェクトディレクトリに移動
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend

# 2. 環境変数の設定
export MKS_USE_POSTGRESQL=true
export DATABASE_URL="postgresql://postgres:ELzion1969@localhost/mirai_knowledge_db"

# 3. 現在のデータ件数を確認
psql -U postgres -d mirai_knowledge_db -c "
SELECT 'knowledge' as table_name, COUNT(*) as count FROM knowledge
UNION ALL
SELECT 'sop', COUNT(*) FROM sop
UNION ALL
SELECT 'incidents', COUNT(*) FROM incidents
UNION ALL
SELECT 'projects', COUNT(*) FROM projects
UNION ALL
SELECT 'experts', COUNT(*) FROM experts;
"
```

### Step 2: バックアップ取得

```bash
# PostgreSQLバックアップ
./scripts/backup-postgresql.sh

# JSONデータバックアップ
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/
```

### Step 3: 移行スクリプト実行（ドライラン）

```bash
# ドライランモード（実際には書き込まない）
python migrate_json_to_postgres.py --dry-run

# 出力例：
# [DRY-RUN] ナレッジ: 15件を移行予定
# [DRY-RUN] SOP: 8件を移行予定
# [DRY-RUN] インシデント: 12件を移行予定
```

### Step 4: 移行スクリプト実行（本番）

```bash
# 実際の移行
python migrate_json_to_postgres.py

# 出力例：
# ✅ ナレッジ: 15件を移行しました
# ✅ SOP: 8件を移行しました
# ✅ インシデント: 12件を移行しました
# ✅ プロジェクト: 5件を移行しました
# ✅ 専門家: 10件を移行しました
```

### Step 5: 移行検証

```bash
# 自動検証スクリプト実行
python scripts/validate_migration.py

# 出力例：
# ========================================
#  データ移行検証
# ========================================
# [1] データ件数検証
#   ✓ ナレッジ: JSON=15, DB=15 [OK]
#   ✓ SOP: JSON=8, DB=8 [OK]
#   ✓ インシデント: JSON=12, DB=12 [OK]
# [2] サンプルデータ確認
#   ✓ ナレッジ: サンプルデータ確認
#   ✓ SOP: サンプルデータ確認
# ========================================
# ✓ 移行検証完了 - すべてのチェックに合格
```

### Step 6: 手動検証

```bash
# 1. データベース直接確認
psql -U postgres -d mirai_knowledge_db

# 2. サンプルデータ表示
SELECT id, title, category, status FROM knowledge LIMIT 5;
SELECT id, title, version FROM sop LIMIT 5;

# 3. 検索テスト
SELECT * FROM knowledge WHERE title LIKE '%コンクリート%';
```

### Step 7: API動作確認

```bash
# サービス起動
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python app_v2.py &

# ヘルスチェック
curl http://localhost:8100/api/v1/health

# ログイン（トークン取得）
TOKEN=$(curl -s -X POST http://localhost:8100/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}' | jq -r '.access_token')

# ナレッジ一覧取得
curl -H "Authorization: Bearer $TOKEN" http://localhost:8100/api/v1/knowledge

# SOP一覧取得
curl -H "Authorization: Bearer $TOKEN" http://localhost:8100/api/v1/sop
```

---

## ✅ 検証チェックリスト

### データ件数検証

- [ ] ナレッジ: JSON件数 = DB件数
- [ ] SOP: JSON件数 = DB件数
- [ ] インシデント: JSON件数 = DB件数
- [ ] プロジェクト: JSON件数 = DB件数
- [ ] 専門家: JSON件数 = DB件数

### データ内容検証

- [ ] 日本語文字列が正しく保存されている
- [ ] 日付形式が正しい
- [ ] 配列データ（tags）が正しく保存されている
- [ ] NULL許容フィールドが正しく処理されている

### API動作検証

- [ ] GET /api/v1/knowledge - 一覧取得成功
- [ ] GET /api/v1/sop - 一覧取得成功
- [ ] GET /api/v1/incidents - 一覧取得成功
- [ ] POST /api/v1/knowledge - 新規作成成功
- [ ] PUT /api/v1/knowledge/{id} - 更新成功

### パフォーマンス検証

- [ ] 一覧取得 < 500ms
- [ ] 検索 < 1000ms
- [ ] 詳細取得 < 200ms

---

## 🔄 ロールバック手順

移行に問題が発生した場合：

```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge-app

# 2. PostgreSQLバックアップからリストア
./scripts/restore-postgresql.sh /var/backups/mirai-knowledge/postgresql/db_YYYYMMDD_HHMMSS.sql.gz

# 3. サービス再開
sudo systemctl start mirai-knowledge-app

# 4. 動作確認
curl http://localhost:8100/api/v1/health
```

---

## 📊 テスト結果記録

| テスト項目 | 期待値 | 実績値 | 結果 | 備考 |
|-----------|--------|--------|------|------|
| ナレッジ件数 | | | | |
| SOP件数 | | | | |
| インシデント件数 | | | | |
| API応答時間 | <500ms | | | |
| 日本語表示 | 正常 | | | |

**テスト実施日**: _______________
**テスト実施者**: _______________
**結果判定**: □ 合格 / □ 不合格

---

**作成日**: 2026-01-25
**バージョン**: 1.0.0
**Phase**: C-2-3 移行テスト実行
