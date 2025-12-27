# データ移行ツール - クイックスタートガイド

## 目次
1. [はじめに](#はじめに)
2. [セットアップ](#セットアップ)
3. [基本的な使い方](#基本的な使い方)
4. [よくある使用例](#よくある使用例)
5. [トラブルシューティング](#トラブルシューティング)

## はじめに

このツールを使用すると、既存のCSV、Excel、JSONファイルから、Mirai Knowledge Systemsにデータをインポートできます。

### 主な機能
- CSVファイルからのナレッジインポート
- CSV/ExcelファイルからのSOPインポート
- JSONファイルからの一括インポート
- プレビュー機能（ドライラン）
- 自動バックアップとロールバック

## セットアップ

### 1. 必要な環境
```bash
# Python 3.8以降
python3 --version

# PostgreSQLが起動していることを確認
sudo systemctl status postgresql
```

### 2. データベース準備
```bash
# データベースが初期化されていない場合
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python3 -c "from database import init_db; init_db()"
```

### 3. 依存パッケージの確認
```bash
pip3 install -r requirements.txt
```

## 基本的な使い方

### ステップ1: プレビューモードで確認

**重要**: 実際のインポート前に、必ずプレビューモードで内容を確認してください。

```bash
# ナレッジのプレビュー
python3 tools/data_migration.py import-knowledge \
  --file tools/sample_data/knowledge_import_template.csv \
  --preview

# SOPのプレビュー
python3 tools/data_migration.py import-sop \
  --file tools/sample_data/sop_import_template.csv \
  --preview
```

### ステップ2: エラーチェック

プレビュー結果で以下を確認:
- エラー件数が0であること
- 成功予定件数が期待値と一致すること
- スキップ件数（重複データ）を確認

### ステップ3: 本番インポート実行

```bash
# ナレッジのインポート（自動バックアップ付き）
python3 tools/data_migration.py import-knowledge \
  --file tools/sample_data/knowledge_import_template.csv

# SOPのインポート
python3 tools/data_migration.py import-sop \
  --file tools/sample_data/sop_import_template.csv
```

### ステップ4: 結果確認

インポート後、以下が表示されます:
```
============================================================
インポート結果サマリー
============================================================
成功: 5 件
エラー: 0 件
スキップ: 0 件
合計: 5 件

バックアップID: 20250127_123456
============================================================
```

**重要**: バックアップIDを必ず記録してください！

## よくある使用例

### 例1: 既存のExcelデータをインポート

#### 手順:
1. ExcelファイルをCSV形式で保存
   - ファイル → 名前を付けて保存 → CSV UTF-8（コンマ区切り）

2. CSVファイルのヘッダーを確認
   ```
   title,summary,content,category,tags,status,priority,project,owner
   ```

3. プレビューで確認
   ```bash
   python3 tools/data_migration.py import-knowledge \
     --file /path/to/your/data.csv \
     --preview
   ```

4. 本番インポート
   ```bash
   python3 tools/data_migration.py import-knowledge \
     --file /path/to/your/data.csv
   ```

### 例2: 大量データを段階的にインポート

大量のデータがある場合、ファイルを分割してインポートすることを推奨します。

```bash
# 1回目: 1-100件目
python3 tools/data_migration.py import-knowledge \
  --file data_part1.csv

# 2回目: 101-200件目
python3 tools/data_migration.py import-knowledge \
  --file data_part2.csv

# 3回目: 201-300件目
python3 tools/data_migration.py import-knowledge \
  --file data_part3.csv
```

### 例3: JSONファイルから一括インポート

複数の種類のデータを一度にインポートする場合:

```bash
# data.json ファイルの準備
cat > data.json << 'EOF'
{
  "knowledge": [
    {
      "title": "サンプル1",
      "summary": "概要1",
      "content": "内容1",
      "category": "施工計画",
      "owner": "山田太郎"
    }
  ],
  "sop": [
    {
      "title": "手順1",
      "category": "施工計画",
      "version": "1.0",
      "revision_date": "2025-01-27",
      "content": "手順内容"
    }
  ]
}
EOF

# インポート
python3 tools/data_migration.py import-json \
  --file data.json \
  --preview

python3 tools/data_migration.py import-json \
  --file data.json
```

### 例4: バックアップとロールバック

```bash
# バックアップ一覧を確認
python3 tools/data_migration.py list-backups

# 出力例:
# 利用可能なバックアップ:
# ============================================================
# ID: 20250127_143022
#   作成日時: 2025-01-27 14:30:22
#   サイズ: 45.32 KB
#
# ID: 20250127_123456
#   作成日時: 2025-01-27 12:34:56
#   サイズ: 38.21 KB
# ============================================================

# 特定のバックアップから復元
python3 tools/data_migration.py rollback \
  --backup-id 20250127_123456
```

### 例5: バックアップなしでインポート（テスト環境）

テスト環境などでバックアップが不要な場合:

```bash
python3 tools/data_migration.py import-knowledge \
  --file test_data.csv \
  --no-backup
```

## トラブルシューティング

### Q1: データベース接続エラーが出る

```
エラー: connection to server at "localhost", port 5432 failed
```

**対処法:**
```bash
# PostgreSQLが起動しているか確認
sudo systemctl status postgresql

# 起動していない場合
sudo systemctl start postgresql

# 接続情報を確認
echo $DATABASE_URL
```

### Q2: 必須フィールドエラー

```
エラー: 必須フィールド 'title' が未入力です
```

**対処法:**
- CSVファイルで該当行を確認
- 必須フィールドに値を入力
- 空白セルがないか確認

必須フィールド:
- **ナレッジ**: title, summary, category, owner
- **SOP**: title, category, version, revision_date, content

### Q3: カテゴリエラー

```
エラー: カテゴリは [...] のいずれかを指定してください
```

**対処法:**
以下のカテゴリから選択:
- 施工計画
- 品質管理
- 安全衛生
- 環境対策
- 原価管理
- 出来形管理
- その他

### Q4: 日付フォーマットエラー

```
エラー: revision_dateは YYYY-MM-DD 形式で指定してください
```

**対処法:**
- 正しい形式: `2025-01-27`
- 間違った形式: `27/01/2025`, `2025/01/27`, `Jan 27, 2025`

### Q5: 文字化けする

**対処法:**
```bash
# CSVファイルのエンコーディングを確認
file -i your_file.csv

# UTF-8に変換（必要な場合）
iconv -f SHIFT-JIS -t UTF-8 input.csv > output.csv
```

### Q6: 重複データがスキップされる

```
警告: 重複データをスキップ - タイトル: XXX
```

**これは正常な動作です。**
- 同じタイトル・カテゴリの組み合わせは1つだけ保存されます
- 既存データを更新したい場合は、先に削除してから再インポート

### Q7: メモリ不足エラー

**対処法:**
- データを小さなファイルに分割
- 一度にインポートする件数を減らす（100件程度ずつ推奨）

## 便利なコマンド集

### CSVファイルの行数を確認
```bash
wc -l your_file.csv
```

### CSVファイルの最初の5行を表示
```bash
head -5 your_file.csv
```

### CSVファイルのヘッダーのみ表示
```bash
head -1 your_file.csv
```

### 特定のカテゴリだけを抽出
```bash
grep "品質管理" your_file.csv > quality_only.csv
```

### バックアップディレクトリのサイズを確認
```bash
du -sh tools/backups/
```

### 古いバックアップを削除（30日以上前）
```bash
find tools/backups/ -name "backup_*.json" -mtime +30 -delete
```

## ベストプラクティス

### 1. インポート前チェックリスト
- [ ] データベースが起動している
- [ ] CSVファイルのエンコーディングがUTF-8
- [ ] 必須フィールドがすべて入力されている
- [ ] プレビューモードで確認済み
- [ ] バックアップIDを記録する準備ができている

### 2. 安全な運用
- 本番環境では必ずバックアップを取る
- 大量データは段階的にインポート
- インポート後は必ず動作確認
- 問題があればすぐにロールバック

### 3. データ品質向上
- カテゴリは統一する
- タグは検索しやすいキーワードを使用
- Markdown形式でcontentを記述
- プロジェクト名は正式名称を使用

## さらに詳しい情報

詳細なドキュメントは以下を参照してください:
- [sample_data/README.md](sample_data/README.md) - データフォーマットとテンプレート
- [data_migration.py](data_migration.py) - ソースコード

---

**質問やサポートが必要な場合は、開発チームまでお問い合わせください。**
