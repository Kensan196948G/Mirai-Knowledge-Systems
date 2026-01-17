#!/usr/bin/env python3
"""
Microsoft 365からデータをエクスポート

環境変数:
    MS365_TENANT_ID: Azure AD Tenant ID
    MS365_CLIENT_ID: Application (client) ID
    MS365_CLIENT_SECRET: Client secret value
    MS365_SITE_ID: SharePoint Site ID (オプション)
    MS365_DRIVE_ID: Drive ID (オプション)

使用例:
    export MS365_TENANT_ID="your-tenant-id"
    export MS365_CLIENT_ID="your-client-id"
    export MS365_CLIENT_SECRET="your-client-secret"
    python scripts/export_from_ms365.py --output ms365_export.json
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from pathlib import Path

# パッケージのインポート確認
try:
    from azure.identity import ClientSecretCredential
    from msgraph import GraphServiceClient
except ImportError:
    print("❌ 必要なパッケージがインストールされていません")
    print("以下のコマンドを実行してください:")
    print("  pip install azure-identity msgraph-sdk")
    sys.exit(1)


class MS365Exporter:
    """Microsoft 365データエクスポーター"""

    def __init__(self, tenant_id, client_id, client_secret):
        """初期化"""
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret

        # 認証
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

        self.client = GraphServiceClient(credentials=self.credential)
        print("✅ Microsoft Graph API認証成功")

    async def get_sites(self):
        """SharePointサイト一覧を取得"""
        try:
            result = await self.client.sites.get()
            sites = []

            for site in result.value:
                sites.append({
                    'id': site.id,
                    'name': site.display_name,
                    'url': site.web_url
                })

            print(f"✅ SharePointサイト: {len(sites)}件")
            return sites
        except Exception as e:
            print(f"❌ サイト取得エラー: {e}")
            return []

    async def get_documents(self, site_id, drive_id):
        """SharePointドキュメントを取得"""
        try:
            result = await self.client.drives.by_drive_id(drive_id).root.children.get()
            documents = []

            for item in result.value:
                if item.file:  # ファイルの場合
                    doc = {
                        'id': item.id,
                        'name': item.name,
                        'description': item.description or '',
                        'path': item.parent_reference.path if item.parent_reference else '',
                        'size': item.size,
                        'created_by': item.created_by.user.display_name if item.created_by and item.created_by.user else '',
                        'created_at': item.created_date_time.isoformat() if item.created_date_time else '',
                        'updated_at': item.last_modified_date_time.isoformat() if item.last_modified_date_time else '',
                        'web_url': item.web_url
                    }
                    documents.append(doc)

            print(f"✅ ドキュメント: {len(documents)}件")
            return documents
        except Exception as e:
            print(f"❌ ドキュメント取得エラー: {e}")
            return []

    def convert_to_knowledge_format(self, documents):
        """MS365形式 → Knowledge形式に変換"""
        knowledge_list = []
        id_counter = 1

        for doc in documents:
            knowledge = {
                'id': id_counter,
                'title': doc['name'],
                'summary': doc['description'] or doc['name'],
                'content': '',  # ファイル内容は別途取得が必要
                'category': self._parse_category(doc['path']),
                'tags': self._extract_tags(doc),
                'status': 'approved',
                'priority': 'medium',
                'project': '',
                'owner': doc['created_by'] or '技術部',
                'created_at': doc['created_at'] or datetime.now().isoformat(),
                'updated_at': doc['updated_at'] or datetime.now().isoformat()
            }
            knowledge_list.append(knowledge)
            id_counter += 1

        return knowledge_list

    def _parse_category(self, path):
        """パスからカテゴリを推測"""
        if '/施工/' in path or '/construction/' in path.lower():
            return '施工計画'
        elif '/品質/' in path or '/quality/' in path.lower():
            return '品質管理'
        elif '/安全/' in path or '/safety/' in path.lower():
            return '安全衛生'
        elif '/環境/' in path or '/environment/' in path.lower():
            return '環境対策'
        else:
            return '未分類'

    def _extract_tags(self, doc):
        """ドキュメントからタグを抽出"""
        tags = []
        name_lower = doc['name'].lower()

        # ファイル名からキーワード抽出
        keywords = ['コンクリート', '鉄筋', '型枠', '足場', '測量', '安全', '品質']
        for keyword in keywords:
            if keyword in doc['name']:
                tags.append(keyword)

        return tags


async def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='Microsoft 365からデータをエクスポート')
    parser.add_argument('--output', default='ms365_export.json', help='出力JSONファイル')
    parser.add_argument('--site-id', help='SharePoint Site ID')
    parser.add_argument('--drive-id', help='Drive ID')
    args = parser.parse_args()

    # 環境変数チェック
    tenant_id = os.environ.get('MS365_TENANT_ID')
    client_id = os.environ.get('MS365_CLIENT_ID')
    client_secret = os.environ.get('MS365_CLIENT_SECRET')

    if not all([tenant_id, client_id, client_secret]):
        print("❌ 環境変数が設定されていません")
        print("必須環境変数:")
        print("  MS365_TENANT_ID")
        print("  MS365_CLIENT_ID")
        print("  MS365_CLIENT_SECRET")
        sys.exit(1)

    print("=" * 60)
    print("Microsoft 365 データエクスポート")
    print("=" * 60)
    print()

    # エクスポーター初期化
    exporter = MS365Exporter(tenant_id, client_id, client_secret)

    # サイトID未指定の場合は一覧表示
    if not args.site_id:
        sites = await exporter.get_sites()
        if sites:
            print("\n利用可能なSharePointサイト:")
            for site in sites:
                print(f"  - {site['name']} (ID: {site['id']})")
            print("\n--site-id オプションでサイトIDを指定してください")
        return

    # ドキュメント取得
    site_id = args.site_id
    drive_id = args.drive_id or os.environ.get('MS365_DRIVE_ID')

    if not drive_id:
        print("❌ Drive IDが指定されていません")
        print("--drive-id オプションまたはMS365_DRIVE_ID環境変数を設定してください")
        sys.exit(1)

    documents = await exporter.get_documents(site_id, drive_id)

    # Knowledge形式に変換
    knowledge_list = exporter.convert_to_knowledge_format(documents)

    # JSON出力
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(knowledge_list, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print(f"✅ エクスポート完了: {args.output}")
    print(f"   データ件数: {len(knowledge_list)}件")
    print("=" * 60)
    print()
    print("次のステップ:")
    print(f"  1. データ検証: python scripts/validate_migration_data.py {args.output}")
    print(f"  2. PostgreSQL投入: python migrate_json_to_postgres.py --input {args.output}")


if __name__ == '__main__':
    asyncio.run(main())
