# データ移行ガイド - 本番環境対応

## 📋 概要

Mirai Knowledge Systemsへのデータ移行手順を説明します。以下の3つの移行経路に対応します：

1. **現行サーバーからの移行** - 既存システムのデータベース/ファイルから移行
2. **Microsoft 365からの移行** - SharePoint/OneDrive/Teams等から移行
3. **手動データ作成** - 新規にデータを作成

---

## 🎯 移行戦略

### 移行フェーズ

| フェーズ | 内容 | 所要時間 | 担当 |
|---------|------|---------|------|
| Phase 1 | データ棚卸・分析 | 2-3日 | データ管理者 |
| Phase 2 | 移行スクリプト開発・テスト | 3-5日 | 開発者 |
| Phase 3 | リハーサル（テスト環境） | 1-2日 | 開発者・運用者 |
| Phase 4 | 本番移行 | 4-8時間 | 全員 |
| Phase 5 | 検証・安定化 | 1-2日 | 全員 |

---

## 📁 Method 1: 現行サーバーからの移行

### 前提条件

- 現行サーバーへのアクセス権限（SSH、データベース接続）
- データ形式の把握（CSV、Excel、SQL、JSON等）
- ネットワーク帯域の確保

### ステップ1: 現行データのエクスポート

#### SQL Serverからのエクスポート

```bash
# SQL Serverデータベースからエクスポート
# 方法1: bcp コマンド
bcp "SELECT * FROM knowledge_table" queryout knowledge_export.csv -c -t, -S servername -U username -P password

# 方法2: SQL Server Management Studio (SSMS)
# タスク → データのエクスポート → フラットファイル形式

# 方法3: PowerShell
$conn = New-Object System.Data.SqlClient.SqlConnection("Server=servername;Database=dbname;User Id=username;Password=password;")
$cmd = New-Object System.Data.SqlClient.SqlCommand("SELECT * FROM knowledge_table", $conn)
$adapter = New-Object System.Data.SqlClient.SqlDataAdapter($cmd)
$dataset = New-Object System.Data.DataSet
$adapter.Fill($dataset)
$dataset.Tables[0] | Export-Csv -Path "knowledge_export.csv" -NoTypeInformation
```

#### MySQLからのエクスポート

```bash
# MySQLデータベースからエクスポート
mysqldump -u username -p --databases knowledge_db --result-file=knowledge_dump.sql

# 特定テーブルのみ
mysqldump -u username -p knowledge_db knowledge_table sop_table > tables_export.sql

# CSV形式でエクスポート
mysql -u username -p -e "SELECT * FROM knowledge_table INTO OUTFILE '/tmp/knowledge.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '\"' LINES TERMINATED BY '\n';" knowledge_db
```

#### PostgreSQLからのエクスポート

```bash
# 他のPostgreSQLサーバーから
pg_dump -h source_server -U username -d source_db -t knowledge_table -f knowledge.sql

# CSV形式
psql -h source_server -U username -d source_db -c "\COPY knowledge_table TO 'knowledge.csv' CSV HEADER"
```

#### ファイルサーバーからのエクスポート

```bash
# ファイル共有からコピー
scp user@server:/path/to/documents/*.pdf ./migration_data/documents/

# rsync（差分同期）
rsync -avz --progress user@server:/path/to/documents/ ./migration_data/documents/
```

### ステップ2: データ変換スクリプト作成

```python
#!/usr/bin/env python3
"""
現行システムデータを Mirai Knowledge Systems 形式に変換

使用例:
    python convert_legacy_data.py --input legacy_export.csv --output knowledge.json
"""

import csv
import json
from datetime import datetime

def convert_csv_to_knowledge(csv_path, output_path):
    """CSVをknowledge.json形式に変換"""
    knowledge_list = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            knowledge = {
                'id': int(row['ID']),
                'title': row['Title'],
                'summary': row['Summary'] or row['Title'][:100],
                'content': row['Content'],
                'category': map_category(row['Category']),  # カテゴリマッピング
                'tags': row['Tags'].split(',') if row.get('Tags') else [],
                'status': 'approved',
                'priority': map_priority(row.get('Priority', 'Medium')),
                'project': row.get('Project', ''),
                'owner': row.get('Owner', '技術部'),
                'created_at': parse_date(row.get('CreatedDate')),
                'updated_at': parse_date(row.get('UpdatedDate'))
            }
            knowledge_list.append(knowledge)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_list, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(knowledge_list)}件のナレッジデータを変換しました: {output_path}")

def map_category(legacy_category):
    """カテゴリマッピング"""
    mapping = {
        '施工': '施工計画',
        '品質': '品質管理',
        '安全': '安全衛生',
        'QC': '品質管理',
        'Safety': '安全衛生',
        # ... 他のマッピング
    }
    return mapping.get(legacy_category, legacy_category)

def map_priority(legacy_priority):
    """優先度マッピング"""
    mapping = {
        'High': 'high',
        'Medium': 'medium',
        'Low': 'low',
        '高': 'high',
        '中': 'medium',
        '低': 'low',
    }
    return mapping.get(legacy_priority, 'medium')

def parse_date(date_str):
    """日付文字列をISO形式に変換"""
    if not date_str:
        return datetime.now().isoformat()

    # 複数の日付形式に対応
    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
        try:
            return datetime.strptime(date_str, fmt).isoformat()
        except ValueError:
            continue

    return datetime.now().isoformat()
```

### ステップ3: Mirai Knowledge Systemsへインポート

```bash
# 1. バックアップ作成
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend
python scripts/backup.sh

# 2. 既存ダミーデータ削除
python scripts/clear_dummy_data.py --all

# 3. 変換済みデータをPostgreSQLに投入
python migrate_json_to_postgres.py

# 4. 検証
python scripts/verify_migration.py
```

---

## 🌐 Method 2: Microsoft 365からの移行

### 前提条件

- Azure ADアプリケーション登録
- Microsoft Graph APIアクセス許可設定
- Client ID、Client Secret、Tenant IDの取得

### ステップ1: Azure ADアプリケーション登録

```bash
# Azure CLIでアプリケーション登録
az ad app create --display-name "Mirai Knowledge Migration Tool"

# アプリケーションIDを取得
APP_ID=$(az ad app list --display-name "Mirai Knowledge Migration Tool" --query "[0].appId" -o tsv)

# Client Secretを作成
az ad app credential reset --id $APP_ID

# APIアクセス許可を追加
az ad app permission add --id $APP_ID --api 00000003-0000-0000-c000-000000000000 --api-permissions \
    df021288-bdef-4463-88db-98f22de89214=Role \  # Files.Read.All
    7ab1d382-f21e-4acd-a863-ba3e13f7da61=Role     # Directory.Read.All
```

### ステップ2: Microsoft Graph API経由でデータ取得

```python
#!/usr/bin/env python3
"""
Microsoft 365からデータを取得してMirai形式に変換

環境変数:
    MS365_TENANT_ID: Azure AD Tenant ID
    MS365_CLIENT_ID: Application (client) ID
    MS365_CLIENT_SECRET: Client secret value
"""

import os
import json
from datetime import datetime
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.drive_item import DriveItem

# 認証設定
TENANT_ID = os.environ['MS365_TENANT_ID']
CLIENT_ID = os.environ['MS365_CLIENT_ID']
CLIENT_SECRET = os.environ['MS365_CLIENT_SECRET']

# 非対話型認証（client_credentials フロー）
credential = ClientSecretCredential(
    tenant_id=TENANT_ID,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

client = GraphServiceClient(credentials=credential)

async def get_sharepoint_documents(site_id, drive_id):
    """SharePointからドキュメントを取得"""
    # ドライブのルートアイテムを取得
    result = await client.drives.by_drive_id(drive_id).root.children.get()

    knowledge_list = []

    for item in result.value:
        if item.file:  # ファイルの場合
            # ファイル内容を取得
            content = await client.drives.by_drive_id(drive_id).items.by_drive_item_id(item.id).content.get()

            knowledge = {
                'title': item.name,
                'summary': item.description or item.name,
                'content': content.decode('utf-8') if isinstance(content, bytes) else str(content),
                'category': parse_category_from_path(item.parent_reference.path),
                'tags': extract_tags_from_metadata(item),
                'status': 'approved',
                'owner': item.created_by.user.display_name,
                'created_at': item.created_date_time.isoformat(),
                'updated_at': item.last_modified_date_time.isoformat()
            }
            knowledge_list.append(knowledge)

    return knowledge_list

async def get_teams_wiki(team_id):
    """Microsoft TeamsのWikiページを取得"""
    # Teamsのチャネルリストを取得
    channels = await client.teams.by_team_id(team_id).channels.get()

    knowledge_list = []

    for channel in channels.value:
        # チャネルのWikiタブを取得
        tabs = await client.teams.by_team_id(team_id).channels.by_channel_id(channel.id).tabs.get()

        for tab in tabs.value:
            if tab.teamsapp.id == 'com.microsoft.teamspace.tab.wiki':
                # Wikiコンテンツを取得
                # ... 変換処理
                pass

    return knowledge_list

def parse_category_from_path(path):
    """ファイルパスからカテゴリを推測"""
    if '/施工/' in path:
        return '施工計画'
    elif '/品質/' in path:
        return '品質管理'
    elif '/安全/' in path:
        return '安全衛生'
    # ... 他のカテゴリ
    return '未分類'

def extract_tags_from_metadata(item):
    """メタデータからタグを抽出"""
    tags = []

    # SharePointのカスタムメタデータ
    if hasattr(item, 'list_item') and item.list_item:
        fields = item.list_item.fields
        if 'Tags' in fields:
            tags = fields['Tags'].split(';')

    return tags

# メイン処理
async def main():
    # SharePointサイトID（事前に取得）
    SITE_ID = "your-site-id"
    DRIVE_ID = "your-drive-id"

    # SharePointドキュメント取得
    documents = await get_sharepoint_documents(SITE_ID, DRIVE_ID)

    # JSON出力
    with open('ms365_knowledge_export.json', 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(documents)}件のドキュメントをエクスポートしました")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

### ステップ3: 必要なPythonパッケージのインストール

```bash
# Microsoft Graph API用パッケージ
pip install azure-identity msgraph-sdk

# または requirements.txt に追加済み
# azure-identity>=1.15.0
# msgraph-sdk>=1.0.0
```

### ステップ4: 実行手順

```bash
# 1. 環境変数を設定
export MS365_TENANT_ID="your-tenant-id"
export MS365_CLIENT_ID="your-client-id"
export MS365_CLIENT_SECRET="your-client-secret"

# 2. データエクスポート
python scripts/export_from_ms365.py

# 3. データ検証
python scripts/validate_migration_data.py --input ms365_knowledge_export.json

# 4. PostgreSQLに投入
python migrate_json_to_postgres.py --input ms365_knowledge_export.json

# 5. 検証
python scripts/verify_migration.py
```

---

## 🛠️ Method 3: 手動データ作成

### CSV テンプレート

`knowledge_template.csv`:

```csv
ID,Title,Summary,Content,Category,Tags,Status,Priority,Project,Owner,CreatedDate,UpdatedDate
1,"コンクリート打設手順","寒冷地での打設管理","【目的】寒冷期におけるコンクリート打設...","施工計画","コンクリート,品質管理","approved","high","橋梁補修","技術部","2026-01-01","2026-01-08"
2,"安全確認チェックリスト","日次安全確認項目","【適用範囲】全現場...","安全衛生","安全,チェックリスト","approved","high","","安全管理室","2026-01-05","2026-01-08"
```

### Excel → JSON 変換スクリプト

```python
#!/usr/bin/env python3
"""
Excel（.xlsx）をJSON形式に変換

使用例:
    python scripts/excel_to_json.py --input knowledge_data.xlsx --output knowledge.json --sheet "ナレッジ一覧"
"""

import openpyxl
import json
import argparse
from datetime import datetime

def excel_to_json(excel_path, output_path, sheet_name='Sheet1'):
    """Excel→JSON変換"""
    workbook = openpyxl.load_workbook(excel_path)
    sheet = workbook[sheet_name]

    # ヘッダー行を取得
    headers = [cell.value for cell in sheet[1]]

    knowledge_list = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        knowledge = {}
        for header, value in zip(headers, row):
            if header and value is not None:
                # 日付型の処理
                if isinstance(value, datetime):
                    knowledge[header] = value.isoformat()
                else:
                    knowledge[header] = value

        if knowledge:  # 空行をスキップ
            knowledge_list.append(knowledge)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_list, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(knowledge_list)}件のデータを変換しました")
    return knowledge_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input Excel file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--sheet', default='Sheet1', help='Sheet name')
    args = parser.parse_args()

    excel_to_json(args.input, args.output, args.sheet)
```

---

## 📊 データマッピング定義

### ナレッジ（Knowledge）フィールドマッピング

| Mirai フィールド | 現行システム | MS365 | 必須 | デフォルト値 |
|----------------|------------|-------|------|------------|
| id | ID | - | ✅ | 自動採番 |
| title | Title / タイトル | Name | ✅ | - |
| summary | Summary / 概要 | Description | ✅ | titleの先頭100文字 |
| content | Content / 本文 | File content | ☐ | summaryと同じ |
| category | Category / 分類 | Folder path | ✅ | "未分類" |
| tags | Tags / キーワード | Metadata.Tags | ☐ | [] |
| status | Status / ステータス | - | ☐ | "approved" |
| priority | Priority / 優先度 | - | ☐ | "medium" |
| project | Project / プロジェクト | Site name | ☐ | "" |
| owner | Owner / 担当者 | CreatedBy | ✅ | "技術部" |
| created_at | CreatedDate | CreatedDateTime | ☐ | 現在時刻 |
| updated_at | UpdatedDate | LastModifiedDateTime | ☐ | 現在時刻 |

### SOP（標準施工手順）フィールドマッピング

| Mirai フィールド | 現行システム | MS365 | 必須 | デフォルト値 |
|----------------|------------|-------|------|------------|
| id | ID | - | ✅ | 自動採番 |
| title | Title | Name | ✅ | - |
| category | Category | Folder | ✅ | - |
| version | Version / バージョン | VersionLabel | ✅ | "1.0" |
| revision_date | RevisionDate | LastModifiedDateTime | ✅ | 現在日付 |
| content | Content | File content | ✅ | - |
| status | Status | - | ☐ | "active" |

---

## 🔍 データ検証

### 移行前検証

```python
#!/usr/bin/env python3
"""
移行データの事前検証

チェック項目:
- 必須フィールドの存在
- データ型の妥当性
- 文字エンコーディング
- 重複ID
- 外部キー整合性
"""

import json

def validate_knowledge_data(json_path):
    """ナレッジデータの検証"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    errors = []
    warnings = []
    ids = set()

    for i, item in enumerate(data):
        # 必須フィールドチェック
        required_fields = ['title', 'summary', 'category', 'owner']
        for field in required_fields:
            if field not in item or not item[field]:
                errors.append(f"行{i+1}: 必須フィールド '{field}' が欠落")

        # ID重複チェック
        if 'id' in item:
            if item['id'] in ids:
                errors.append(f"行{i+1}: ID {item['id']} が重複")
            ids.add(item['id'])

        # タイトル長チェック
        if 'title' in item and len(item['title']) > 500:
            warnings.append(f"行{i+1}: タイトルが500文字を超過（切り詰められます）")

        # カテゴリ値チェック
        valid_categories = ['施工計画', '品質管理', '安全衛生', '環境対策', '原価管理', '出来形管理', '設計変更', '工程管理']
        if 'category' in item and item['category'] not in valid_categories:
            warnings.append(f"行{i+1}: 未知のカテゴリ '{item['category']}'")

    # レポート出力
    print(f"データ検証結果: {len(data)}件")
    print(f"  エラー: {len(errors)}件")
    print(f"  警告: {len(warnings)}件")

    if errors:
        print("\n【エラー】")
        for error in errors[:10]:  # 最初の10件のみ表示
            print(f"  - {error}")

    if warnings:
        print("\n【警告】")
        for warning in warnings[:10]:
            print(f"  - {warning}")

    return len(errors) == 0

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("使用方法: python validate_migration_data.py <json_file>")
        sys.exit(1)

    if validate_knowledge_data(sys.argv[1]):
        print("\n✅ 検証成功 - データ移行可能")
        sys.exit(0)
    else:
        print("\n❌ 検証失敗 - エラーを修正してください")
        sys.exit(1)
```

---

## 🔄 ロールバック手順

### JSONモードへの切り戻し

```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge-prod

# 2. 環境変数を変更
vim backend/.env
# MKS_USE_POSTGRESQL=false に変更

# 3. バックアップからJSONファイルをリストア
cp -r backend/data/backup_20260108_120000/* backend/data/

# 4. サービス起動
sudo systemctl start mirai-knowledge-prod

# 5. 動作確認
curl http://localhost:5100/api/v1/health
```

### PostgreSQLデータのロールバック

```bash
# Point-in-Time Recovery（PITR）
# 1. PostgreSQL停止
sudo systemctl stop postgresql

# 2. データディレクトリをバックアップ時点に復元
sudo rm -rf /var/lib/postgresql/16/main
sudo cp -r /var/backups/postgresql/20260108_backup /var/lib/postgresql/16/main
sudo chown -R postgres:postgres /var/lib/postgresql/16/main

# 3. PostgreSQL起動
sudo systemctl start postgresql

# 4. 検証
psql -U postgres -d mirai_knowledge_db -c "SELECT COUNT(*) FROM knowledge;"
```

---

## 📝 チェックリスト

### 移行前

- [ ] バックアップ取得（JSON、PostgreSQL）
- [ ] 移行データの検証完了
- [ ] テスト環境でリハーサル実施
- [ ] ロールバック手順の確認
- [ ] 関係者への事前通知
- [ ] メンテナンス時間の確保

### 移行中

- [ ] サービス停止
- [ ] データクリア実行
- [ ] データ投入実行
- [ ] エラーログ監視
- [ ] 進捗状況の記録

### 移行後

- [ ] データ件数確認
- [ ] サンプルレコードの目視確認
- [ ] API動作確認（全エンドポイント）
- [ ] フロントエンド動作確認
- [ ] パフォーマンステスト
- [ ] ログ確認（エラーがないか）

---

## 🚀 実行スクリプト一覧

| スクリプト | 用途 | 場所 |
|-----------|------|------|
| `convert_legacy_data.py` | CSV/SQL→JSON変換 | `/backend/scripts/` |
| `export_from_ms365.py` | MS365データエクスポート | `/backend/scripts/` |
| `excel_to_json.py` | Excel→JSON変換 | `/backend/scripts/` |
| `validate_migration_data.py` | データ検証 | `/backend/scripts/` |
| `clear_dummy_data.py` | ダミーデータ削除 | `/backend/scripts/` |
| `migrate_json_to_postgres.py` | JSON→PostgreSQL | `/backend/` |
| `import_detailed_data.py` | 詳細データ投入 | `/backend/` |
| `verify_migration.py` | 移行検証 | `/backend/scripts/` |

---

## 💡 ヒントとベストプラクティス

### 大量データの移行

- バッチ処理: 1000件ずつに分割して投入
- 進捗表示: tqdmライブラリで進捗バー表示
- エラーリカバリ: 失敗時に途中から再開可能にする

### 文字エンコーディング

- UTF-8に統一
- Shift_JISやEUC-JPからの変換に注意
- 文字化け発生時は`chardet`ライブラリで自動検出

### パフォーマンス最適化

- バルクインサート: `db.bulk_insert_mappings()`使用
- インデックス一時無効化: 大量投入時にインデックスを無効化
- トランザクションサイズ: 500-1000件ごとにcommit

---

## 📚 参考資料

- **Microsoft Graph API**: https://learn.microsoft.com/graph/api/overview
- **Azure AD認証**: https://learn.microsoft.com/azure/active-directory/develop/
- **PostgreSQL COPY**: https://www.postgresql.org/docs/current/sql-copy.html
- **SQLAlchemy Bulk Operations**: https://docs.sqlalchemy.org/en/14/orm/persistence_techniques.html#bulk-operations

---

**作成日**: 2026-01-08
**バージョン**: 1.0.0
**対象**: Phase C - 本番データ移行
