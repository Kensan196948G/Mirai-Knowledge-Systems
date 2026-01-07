# データインポートテンプレート

## 概要

Mirai Knowledge Systemsへのデータインポート用テンプレートファイルです。
CSV形式でデータを準備し、インポートスクリプトで取り込みます。

## テンプレート一覧

| ファイル | 対象テーブル | 説明 |
|----------|-------------|------|
| `knowledge_template.csv` | knowledge | ナレッジ記事 |
| `sop_template.csv` | sop | 標準施工手順 |
| `incidents_template.csv` | incidents | 事故・ヒヤリレポート |

## 使用方法

### 1. テンプレートをコピー

```bash
cp knowledge_template.csv my_knowledge_data.csv
```

### 2. データを編集

CSVファイルを編集してデータを追加します。
- 1行目はヘッダー（変更しない）
- 2行目以降にデータを追加

### 3. インポート実行

```bash
# ドライラン（確認のみ）
python scripts/import_data.py --source data/my_knowledge_data.csv --target knowledge --dry-run

# 本番インポート
python scripts/import_data.py --source data/my_knowledge_data.csv --target knowledge
```

## フィールド説明

### knowledge (ナレッジ)

| フィールド | 必須 | 説明 | 例 |
|-----------|------|------|-----|
| title | 必須 | タイトル | コンクリート打設の注意点 |
| summary | 必須 | 要約 | コンクリート打設時の品質管理ポイント |
| category | 必須 | カテゴリ | 技術, 施工, 安全, 品質 |
| owner | 必須 | 所有者 | 山田太郎 |
| content | 任意 | 詳細内容 | 本文テキスト |
| tags | 任意 | タグ（カンマ区切り） | タグ1,タグ2,タグ3 |
| status | 任意 | ステータス | draft, published, archived |
| priority | 任意 | 優先度 | low, medium, high, critical |
| project | 任意 | プロジェクト | プロジェクトA |

### sop (標準施工手順)

| フィールド | 必須 | 説明 | 例 |
|-----------|------|------|-----|
| title | 必須 | タイトル | 型枠組立手順書 |
| category | 必須 | カテゴリ | コンクリート工, 鉄筋工 |
| version | 必須 | バージョン | 1.0, 2.1 |
| revision_date | 必須 | 改訂日 | 2026-01-01 |
| content | 必須 | 内容 | 手順の詳細 |
| target | 任意 | 対象者 | 現場作業員, 技術者 |
| tags | 任意 | タグ | 安全,品質 |
| status | 任意 | ステータス | active, deprecated |

### incidents (事故・ヒヤリ)

| フィールド | 必須 | 説明 | 例 |
|-----------|------|------|-----|
| title | 必須 | タイトル | 足場からの転落事故 |
| description | 必須 | 詳細 | 事故の詳細説明 |
| project | 必須 | プロジェクト | ○○工事 |
| incident_date | 必須 | 発生日 | 2026-01-05 |
| severity | 必須 | 重大度 | minor, moderate, major, critical |
| status | 任意 | ステータス | reported, investigating, resolved |
| root_cause | 任意 | 根本原因 | 安全確認不足 |
| location | 任意 | 発生場所 | 現場A、3階 |
| tags | 任意 | タグ | 転落,安全 |

## 日付形式

以下の形式に対応しています：
- `2026-01-07`
- `2026/01/07`
- `2026年01月07日`

## 注意事項

1. **文字コード**: UTF-8で保存してください
2. **カンマ**: データ内にカンマを含む場合は、値を"ダブルクォート"で囲む
3. **改行**: データ内に改行を含む場合は避けるか、\\n で表現
4. **バックアップ**: インポート前に既存データのバックアップを取得

## エラー対応

インポート時にエラーが発生した場合：

1. `--verbose` オプションで詳細確認
2. 必須フィールドの確認
3. 日付形式の確認
4. 文字コードの確認

```bash
python scripts/import_data.py --source data/file.csv --target knowledge --dry-run --verbose
```
