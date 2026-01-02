#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダミーデータをクリアするスクリプト

本番環境への移行時に使用:
1. JSONファイルから全ダミーデータを削除
2. PostgreSQLから全テストデータを削除
3. 空の状態で本番データを投入する準備

使用方法:
    python scripts/clear_dummy_data.py --json        # JSONファイルのみクリア
    python scripts/clear_dummy_data.py --postgres    # PostgreSQLのみクリア
    python scripts/clear_dummy_data.py --all         # 両方クリア

注意: このスクリプトは破壊的操作です。実行前にバックアップを取得してください。
"""

import os
import sys
import json
import argparse
from datetime import datetime

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# クリア対象のJSONファイル
JSON_FILES = [
    'knowledge.json',
    'knowledge_details.json',
    'sop.json',
    'sop_details.json',
    'incidents.json',
    'incidents_details.json',
    'regulations.json',
    'consultations.json',
    'consultations_details.json',
    'approvals.json',
    'notifications.json',
    # 以下はクリアしない（設定データ）
    # 'users.json',
    # 'experts.json',
    # 'projects.json',
]

# バックアップ対象外（アクセスログ等）
SKIP_BACKUP = [
    'access_logs.json',
    'search_history.json',
]


def backup_data():
    """データをバックアップ"""
    backup_dir = os.path.join(DATA_DIR, f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    os.makedirs(backup_dir, exist_ok=True)

    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json') and filename not in SKIP_BACKUP:
            src = os.path.join(DATA_DIR, filename)
            dst = os.path.join(backup_dir, filename)
            if os.path.isfile(src):
                with open(src, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                with open(dst, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ バックアップを作成しました: {backup_dir}")
    return backup_dir


def clear_json_files():
    """JSONファイルをクリア（空の配列に置換）"""
    cleared = 0

    for filename in JSON_FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            # 空の配列で上書き
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print(f"  クリア: {filename}")
            cleared += 1
        else:
            print(f"  スキップ（ファイルなし）: {filename}")

    return cleared


def clear_postgres():
    """PostgreSQLデータをクリア"""
    try:
        from database import SessionLocal, engine
        from models import (
            Knowledge, SOP, Regulation, Incident,
            Consultation, Approval, Notification, NotificationRead,
            AccessLog, ChangeLog, DistributionLog
        )

        db = SessionLocal()

        # 削除順序（外部キー制約を考慮）
        tables = [
            (NotificationRead, 'notification_reads'),
            (DistributionLog, 'distribution_logs'),
            (Notification, 'notifications'),
            (Approval, 'approvals'),
            (Consultation, 'consultations'),
            (Incident, 'incidents'),
            (Regulation, 'regulations'),
            (SOP, 'sop'),
            (Knowledge, 'knowledge'),
            # アクセスログはクリアしない
            # (AccessLog, 'access_logs'),
            # (ChangeLog, 'change_logs'),
        ]

        cleared = 0
        for model, name in tables:
            try:
                count = db.query(model).delete()
                print(f"  クリア: {name} ({count}件)")
                cleared += count
            except Exception as e:
                print(f"  エラー: {name} - {e}")

        db.commit()
        db.close()

        print(f"\n✅ PostgreSQL: 合計 {cleared}件のレコードを削除しました")
        return cleared

    except ImportError as e:
        print(f"❌ PostgreSQL接続エラー: {e}")
        print("   MKS_USE_POSTGRESQL=true が設定されているか確認してください")
        return 0
    except Exception as e:
        print(f"❌ PostgreSQLクリアエラー: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='ダミーデータクリアスクリプト')
    parser.add_argument('--json', action='store_true', help='JSONファイルをクリア')
    parser.add_argument('--postgres', action='store_true', help='PostgreSQLをクリア')
    parser.add_argument('--all', action='store_true', help='両方クリア')
    parser.add_argument('--no-backup', action='store_true', help='バックアップをスキップ')
    parser.add_argument('--force', action='store_true', help='確認なしで実行')

    args = parser.parse_args()

    if not (args.json or args.postgres or args.all):
        parser.print_help()
        print("\n⚠️  クリア対象を指定してください: --json, --postgres, または --all")
        return

    # 確認
    if not args.force:
        print("\n⚠️  警告: この操作はデータを削除します。")
        response = input("続行しますか？ (yes/no): ")
        if response.lower() != 'yes':
            print("キャンセルしました。")
            return

    # バックアップ
    if not args.no_backup:
        print("\n📦 データをバックアップ中...")
        backup_data()

    # JSONクリア
    if args.json or args.all:
        print("\n🗑️  JSONファイルをクリア中...")
        cleared = clear_json_files()
        print(f"   {cleared}ファイルをクリアしました")

    # PostgreSQLクリア
    if args.postgres or args.all:
        print("\n🗑️  PostgreSQLをクリア中...")
        clear_postgres()

    print("\n✅ 完了しました。")
    print("   本番データをインポートする準備ができました。")
    print("\n次のステップ:")
    print("   1. 本番データをJSONファイルに配置")
    print("   2. python migrate_json_to_postgres.py を実行")
    print("   3. python scripts/verify_migration.py で検証")


if __name__ == '__main__':
    main()
