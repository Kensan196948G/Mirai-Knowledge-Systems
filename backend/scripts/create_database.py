#!/usr/bin/env python3
"""
PostgreSQLデータベースとテーブルを作成するスクリプト

使用方法:
    python backend/scripts/create_database.py

環境変数:
    DATABASE_URL: PostgreSQL接続URL（例: postgresql://user:pass@localhost:5432/dbname）
"""

import os
import sys

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse

from database import DATABASE_URL, engine
from models import Base
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError


def create_schemas():
    """スキーマを作成"""
    print("=" * 60)
    print("スキーマ作成")
    print("=" * 60)

    schemas = ["public", "auth", "audit"]

    with engine.connect() as conn:
        for schema in schemas:
            try:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                print(f"✅ スキーマ '{schema}' を作成しました")
            except ProgrammingError as e:
                print(f"⚠️  スキーマ '{schema}' の作成に失敗しました: {e}")

        conn.commit()

    print()


def create_tables(drop_existing=False):
    """テーブルを作成"""
    print("=" * 60)
    print("テーブル作成")
    print("=" * 60)

    if drop_existing:
        print("⚠️  警告: 既存のテーブルを削除します...")
        response = input("本当に削除しますか? (yes/no): ")
        if response.lower() != "yes":
            print("キャンセルしました")
            return

        Base.metadata.drop_all(bind=engine)
        print("✅ 既存のテーブルを削除しました")

    # テーブル作成
    Base.metadata.create_all(bind=engine)
    print("✅ 全テーブルを作成しました")
    print()

    # 作成されたテーブルを表示
    print("作成されたテーブル:")
    print("-" * 60)
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    print()


def verify_database():
    """データベース接続を確認"""
    print("=" * 60)
    print("データベース接続確認")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL バージョン: {version}")

            # データベース名を取得
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"✅ データベース名: {db_name}")

            # スキーマ一覧を取得
            result = conn.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('public', 'auth', 'audit')
                ORDER BY schema_name
            """))
            schemas = [row[0] for row in result]
            print(f"✅ スキーマ: {', '.join(schemas)}")

            print()
            return True
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        print()
        print("以下を確認してください:")
        print("  1. PostgreSQLサーバーが起動しているか")
        print("  2. DATABASE_URL環境変数が正しく設定されているか")
        print(f"     現在の設定: {DATABASE_URL}")
        print("  3. データベースが作成されているか")
        print()
        return False


def show_next_steps():
    """次のステップを表示"""
    print("=" * 60)
    print("次のステップ")
    print("=" * 60)
    print()
    print("1. データのマイグレーション:")
    print("   python backend/migrate_json_to_postgres.py")
    print()
    print("2. マイグレーションの検証:")
    print("   python backend/scripts/verify_migration.py")
    print()
    print("3. PostgreSQLモードでアプリケーションを起動:")
    print("   export MKS_USE_POSTGRESQL=true")
    print("   python backend/app_v2.py")
    print()


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="PostgreSQLデータベースとテーブルを作成"
    )
    parser.add_argument(
        "--drop", action="store_true", help="既存のテーブルを削除してから作成"
    )
    parser.add_argument("--skip-verify", action="store_true", help="接続確認をスキップ")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("Mirai Knowledge System - データベース作成")
    print("=" * 60)
    print()
    print(f"接続URL: {DATABASE_URL}")
    print()

    # データベース接続確認
    if not args.skip_verify:
        if not verify_database():
            sys.exit(1)

    # スキーマ作成
    create_schemas()

    # テーブル作成
    create_tables(drop_existing=args.drop)

    # 次のステップを表示
    show_next_steps()

    print("=" * 60)
    print("完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
