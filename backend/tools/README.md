# データ移行ツール

Mirai Knowledge Systemsへの既存データインポートツール

## ファイル構成

```
tools/
├── README.md                 # このファイル
├── QUICKSTART.md            # クイックスタートガイド
├── data_migration.py        # データ移行メインツール
├── test_import.sh           # テストスクリプト
├── backups/                 # バックアップ保存ディレクトリ
└── sample_data/             # サンプルデータとテンプレート
    ├── README.md
    ├── knowledge_import_template.csv
    └── sop_import_template.csv
```

## クイックスタート

### 1. サンプルデータでテスト

```bash
# 自動テストスクリプトを実行
./tools/test_import.sh
```

このスクリプトは以下を実行します:
- データベース接続確認
- プレビューモードでのインポート確認
- 実際のインポート実行
- バックアップ確認

### 2. 独自データのインポート

```bash
# ステップ1: プレビューモードで確認
python3 tools/data_migration.py import-knowledge \
  --file your_data.csv \
  --preview

# ステップ2: 実際にインポート
python3 tools/data_migration.py import-knowledge \
  --file your_data.csv
```

## 主な機能

### 1. データインポート
- **ナレッジ**: CSVファイルから施工ナレッジをインポート
- **SOP**: CSVファイルから標準施工手順をインポート
- **一括インポート**: JSONファイルから複数種類のデータを一括インポート

### 2. バリデーション
- 必須フィールドチェック
- データ型チェック
- カテゴリ・ステータスの値チェック
- 重複データチェック

### 3. 安全機能
- プレビューモード（ドライラン）
- 自動バックアップ作成
- ロールバック機能
- 詳細なエラーレポート

## コマンド一覧

### ナレッジインポート
```bash
python3 tools/data_migration.py import-knowledge \
  --file <CSVファイルパス> \
  [--preview] \
  [--no-backup]
```

### SOPインポート
```bash
python3 tools/data_migration.py import-sop \
  --file <CSVファイルパス> \
  [--preview] \
  [--no-backup]
```

### JSONインポート
```bash
python3 tools/data_migration.py import-json \
  --file <JSONファイルパス> \
  [--preview] \
  [--no-backup]
```

### バックアップ管理
```bash
# バックアップ一覧表示
python3 tools/data_migration.py list-backups

# ロールバック（復元）
python3 tools/data_migration.py rollback \
  --backup-id <バックアップID>
```

## データフォーマット

### ナレッジCSV

#### 必須フィールド
- `title` - タイトル
- `summary` - 概要
- `category` - カテゴリ（施工計画/品質管理/安全衛生/環境対策/原価管理/出来形管理/その他）
- `owner` - 作成者

#### オプションフィールド
- `content` - 詳細内容（Markdown推奨）
- `tags` - タグ（カンマ区切り）
- `status` - ステータス（draft/pending/approved/archived）
- `priority` - 優先度（low/medium/high）
- `project` - プロジェクト名

#### サンプル
```csv
title,summary,content,category,tags,status,priority,project,owner
コンクリート打設手順,打設時の品質管理,"# 詳細内容...",品質管理,"コンクリート,打設",approved,high,東京タワー改修,山田太郎
```

### SOP CSV

#### 必須フィールド
- `title` - タイトル
- `category` - カテゴリ
- `version` - バージョン番号
- `revision_date` - 改訂日（YYYY-MM-DD形式）
- `content` - 手順内容

#### オプションフィールド
- `target` - 対象者
- `tags` - タグ
- `status` - ステータス（active/draft/archived）

#### サンプル
```csv
title,category,version,revision_date,target,tags,content,status
コンクリート打設標準手順,施工計画,2.1,2025-01-15,現場監督,"コンクリート,打設","# 手順...",active
```

### JSON形式

```json
{
  "knowledge": [
    {
      "title": "タイトル",
      "summary": "概要",
      "content": "内容",
      "category": "施工計画",
      "tags": ["タグ1", "タグ2"],
      "status": "approved",
      "priority": "high",
      "owner": "山田太郎"
    }
  ],
  "sop": [
    {
      "title": "手順タイトル",
      "category": "施工計画",
      "version": "1.0",
      "revision_date": "2025-01-27",
      "content": "手順内容",
      "status": "active"
    }
  ]
}
```

## ユースケース

### ケース1: 既存Excelデータの移行

1. ExcelファイルをCSV UTF-8形式で保存
2. ヘッダー行を本ツールのフォーマットに合わせる
3. プレビューモードで確認
4. インポート実行

```bash
python3 tools/data_migration.py import-knowledge \
  --file converted_data.csv \
  --preview

python3 tools/data_migration.py import-knowledge \
  --file converted_data.csv
```

### ケース2: 段階的な大量データ移行

大量データは100件ずつに分割して段階的にインポート:

```bash
# 1回目
python3 tools/data_migration.py import-knowledge \
  --file data_part1.csv

# 2回目
python3 tools/data_migration.py import-knowledge \
  --file data_part2.csv

# 3回目
python3 tools/data_migration.py import-knowledge \
  --file data_part3.csv
```

### ケース3: エラー修正とリトライ

```bash
# 1. プレビューでエラー確認
python3 tools/data_migration.py import-knowledge \
  --file data.csv \
  --preview

# エラー詳細:
#   行 5: 必須フィールド 'category' が未入力です
#   行 12: カテゴリは [...] のいずれかを指定してください

# 2. CSVファイルを修正

# 3. 再度プレビュー
python3 tools/data_migration.py import-knowledge \
  --file data.csv \
  --preview

# 4. エラーがなければインポート
python3 tools/data_migration.py import-knowledge \
  --file data.csv
```

### ケース4: インポート後のロールバック

```bash
# インポート実行
python3 tools/data_migration.py import-knowledge \
  --file data.csv

# バックアップID: 20250127_143022

# 問題が発覚したのでロールバック
python3 tools/data_migration.py rollback \
  --backup-id 20250127_143022
```

## トラブルシューティング

### データベース接続エラー
```bash
# PostgreSQL起動確認
sudo systemctl status postgresql

# 起動
sudo systemctl start postgresql
```

### エンコーディングエラー
```bash
# ファイルのエンコーディング確認
file -i your_file.csv

# UTF-8に変換
iconv -f SHIFT-JIS -t UTF-8 input.csv > output.csv
```

### メモリ不足
- データを小さいファイルに分割
- 100件程度ずつインポート

## ベストプラクティス

1. **必ずプレビューモードで確認**
   - エラーの早期発見
   - データ確認

2. **バックアップIDを記録**
   - 問題発生時の復旧のため

3. **段階的インポート**
   - 大量データは分割
   - 各段階で動作確認

4. **データ品質の向上**
   - カテゴリの統一
   - Markdown形式でのcontent記述
   - 検索しやすいタグ設定

## 詳細ドキュメント

- [QUICKSTART.md](QUICKSTART.md) - クイックスタートガイド
- [sample_data/README.md](sample_data/README.md) - サンプルデータの詳細説明

## ライセンス

このツールはMirai Knowledge Systemsプロジェクトの一部です。

## サポート

問題が発生した場合は、開発チームまでお問い合わせください。
