# データ移行ツール - 使用ガイド

## 概要
このディレクトリには、既存データをMirai Knowledge Systemsにインポートするためのサンプルデータとツールが含まれています。

## ファイル構成
```
sample_data/
├── README.md                        # このファイル
├── knowledge_import_template.csv    # ナレッジインポート用CSVテンプレート
└── sop_import_template.csv         # SOPインポート用CSVテンプレート
```

## 1. CSVテンプレートの使い方

### ナレッジインポート用テンプレート (knowledge_import_template.csv)

#### 必須フィールド
- `title` - ナレッジのタイトル（最大500文字）
- `summary` - 概要（最大2000文字）
- `category` - カテゴリ（以下から選択）
  - 施工計画
  - 品質管理
  - 安全衛生
  - 環境対策
  - 原価管理
  - 出来形管理
  - その他
- `owner` - 作成者名

#### オプションフィールド
- `content` - 詳細な内容（Markdown形式推奨）
- `tags` - タグ（カンマ区切り、最大20個）
- `status` - ステータス（draft/pending/approved/archived、デフォルト: draft）
- `priority` - 優先度（low/medium/high、デフォルト: medium）
- `project` - プロジェクト名

#### CSVフォーマットの注意点
- エンコーディング: UTF-8
- 改行を含む場合は、セルをダブルクォートで囲む
- ダブルクォートを含む場合は、2つ重ねる（""）

### SOPインポート用テンプレート (sop_import_template.csv)

#### 必須フィールド
- `title` - SOPタイトル（最大500文字）
- `category` - カテゴリ
- `version` - バージョン番号（例: 1.0, 2.1）
- `revision_date` - 改訂日（YYYY-MM-DD形式）
- `content` - 手順内容

#### オプションフィールド
- `target` - 対象者（例: 現場監督・施工管理者）
- `tags` - タグ（カンマ区切り）
- `status` - ステータス（active/draft/archived、デフォルト: active）

## 2. データ移行ツールの使い方

### 基本コマンド

#### ナレッジのインポート
```bash
# プレビューモード（実際にはインポートしない）
python tools/data_migration.py import-knowledge \
  --file tools/sample_data/knowledge_import_template.csv \
  --preview

# 実際にインポート
python tools/data_migration.py import-knowledge \
  --file tools/sample_data/knowledge_import_template.csv

# バックアップを作成せずにインポート
python tools/data_migration.py import-knowledge \
  --file tools/sample_data/knowledge_import_template.csv \
  --no-backup
```

#### SOPのインポート
```bash
# プレビューモード
python tools/data_migration.py import-sop \
  --file tools/sample_data/sop_import_template.csv \
  --preview

# 実際にインポート
python tools/data_migration.py import-sop \
  --file tools/sample_data/sop_import_template.csv
```

#### バックアップの確認
```bash
# バックアップ一覧を表示
python tools/data_migration.py list-backups
```

#### ロールバック（復元）
```bash
# バックアップから復元
python tools/data_migration.py rollback \
  --backup-id 20250127_123456
```

## 3. JSONファイルからの一括インポート

### JSONフォーマット例
```json
{
  "knowledge": [
    {
      "title": "サンプルナレッジ",
      "summary": "これはサンプルです",
      "content": "詳細な内容",
      "category": "施工計画",
      "tags": ["タグ1", "タグ2"],
      "status": "approved",
      "priority": "high",
      "owner": "山田太郎"
    }
  ],
  "sop": [
    {
      "title": "サンプルSOP",
      "category": "施工計画",
      "version": "1.0",
      "revision_date": "2025-01-27",
      "content": "手順内容",
      "status": "active"
    }
  ]
}
```

### インポートコマンド
```bash
# プレビュー
python tools/data_migration.py import-json \
  --file data/import_data.json \
  --preview

# 実際にインポート
python tools/data_migration.py import-json \
  --file data/import_data.json
```

## 4. エラー対処

### よくあるエラー

#### 1. 必須フィールドが未入力
```
エラー: 必須フィールド 'title' が未入力です
対処: CSVファイルで該当行のtitleフィールドに値を入力してください
```

#### 2. カテゴリが不正
```
エラー: カテゴリは [...] のいずれかを指定してください
対処: 有効なカテゴリを指定してください
```

#### 3. 日付フォーマットが不正
```
エラー: revision_dateは YYYY-MM-DD 形式で指定してください
対処: 例: 2025-01-27 の形式で入力してください
```

#### 4. 重複データ
```
警告: 重複データをスキップ
対処: 同じタイトル・カテゴリのデータが既に存在します
       必要に応じて既存データを削除してから再インポートしてください
```

## 5. ベストプラクティス

### インポート前の推奨手順
1. **必ずプレビューモードで確認**
   ```bash
   python tools/data_migration.py import-knowledge --file data.csv --preview
   ```

2. **エラーがある場合は修正**
   - エラー詳細を確認
   - CSVファイルを修正
   - 再度プレビュー

3. **本番インポート実施**
   ```bash
   python tools/data_migration.py import-knowledge --file data.csv
   ```

4. **結果の確認**
   - 成功件数を確認
   - エラー件数を確認
   - 必要に応じてデータベースを直接確認

### バックアップの活用
- デフォルトで自動バックアップが作成されます
- バックアップIDは必ず記録してください
- 問題が発生した場合は、すぐにロールバックできます

### 大量データのインポート
- 一度に大量のデータをインポートする場合は、段階的に実施
- 例: 100件ずつに分割してインポート
- 各段階でプレビューと検証を実施

## 6. データ準備のヒント

### Excelからの変換
1. Excelで表形式のデータを作成
2. 「名前を付けて保存」→「CSV UTF-8（コンマ区切り）」を選択
3. 保存したCSVファイルをテキストエディタで開き、文字化けがないか確認

### Markdown形式の活用
contentフィールドには、Markdown形式で記述することを推奨します。

```markdown
# 見出し1
## 見出し2
- 箇条書き
1. 番号付きリスト
**太字**
*斜体*
```

### タグの付け方
- 検索性を高めるために適切なタグを付ける
- 一般的なキーワード + 専門用語の組み合わせ
- 例: "コンクリート,打設,品質管理,施工管理"

## 7. トラブルシューティング

### データベース接続エラー
```
エラー: データベースに接続できません
対処:
1. PostgreSQLが起動しているか確認
2. DATABASE_URL環境変数が正しく設定されているか確認
3. データベースの接続情報を確認
```

### メモリ不足エラー
```
エラー: メモリ不足
対処:
1. インポートするデータを分割
2. 不要なアプリケーションを終了
```

### 文字化け
```
対処:
1. CSVファイルのエンコーディングをUTF-8に変更
2. BOM付きUTF-8の場合は、BOMなしUTF-8に変換
```

## 8. サポート

問題が解決しない場合は、以下の情報を添えてお問い合わせください:

- エラーメッセージ
- 使用したコマンド
- CSVファイルの該当行（個人情報を除く）
- 環境情報（OS、Pythonバージョン）

## 9. 更新履歴

- 2025-01-27: 初版作成
