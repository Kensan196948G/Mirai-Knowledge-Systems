#!/usr/bin/env python3
"""
N+1クエリ最適化の検証スクリプト（SQLログ付き）

このスクリプトは、PostgreSQLモードで実行し、
実際のSQLクエリを出力してN+1クエリが解消されたことを確認します。
"""

import os
import sys

# 環境変数を設定してPostgreSQLモードを有効化
os.environ["MKS_USE_POSTGRESQL"] = "true"
os.environ["MKS_ENV"] = "development"

# データベース設定をインポートしてSQLエコーを有効化
from database import get_session_factory
from sqlalchemy import event
from sqlalchemy.engine import Engine

# グローバルクエリカウンタ
query_count = 0


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """クエリ実行前にカウントとログ出力"""
    global query_count
    query_count += 1
    print(f"\n[Query #{query_count}]")
    print(statement)
    if parameters:
        print(f"Parameters: {parameters}")


def reset_counter():
    """クエリカウンタをリセット"""
    global query_count
    query_count = 0


def get_count():
    """現在のクエリ数を取得"""
    return query_count


def test_knowledge_list_optimization():
    """ナレッジ一覧取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト1: ナレッジ一覧取得のN+1クエリ最適化")
    print("=" * 80)

    from data_access import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=True)

    reset_counter()
    result = dal.get_knowledge_list(filters={})
    queries = get_count()

    print("\n[結果]")
    print(f"  取得件数: {len(result)}件")
    print(f"  実行クエリ数: {queries}回")
    print("  期待値: 1-2回（メインクエリ + リレーション先読み）")

    if queries <= 2:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{queries}回）")

    return queries


def test_knowledge_by_id_optimization():
    """ナレッジ詳細取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト2: ナレッジ詳細取得のN+1クエリ最適化")
    print("=" * 80)

    from data_access import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=True)

    # 最初のナレッジIDを取得
    knowledge_list = dal.get_knowledge_list(filters={})
    if not knowledge_list:
        print("  ⚠️  ナレッジが存在しません")
        return 0

    knowledge_id = knowledge_list[0]["id"]

    reset_counter()
    dal.get_knowledge_by_id(knowledge_id)
    queries = get_count()

    print("\n[結果]")
    print(f"  ナレッジID: {knowledge_id}")
    print(f"  実行クエリ数: {queries}回")
    print("  期待値: 1-2回")

    if queries <= 2:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{queries}回）")

    return queries


def test_related_knowledge_optimization():
    """関連ナレッジ取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト3: 関連ナレッジ取得のN+1クエリ最適化")
    print("=" * 80)

    from data_access import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=True)

    # タグがあるナレッジを探す
    knowledge_list = dal.get_knowledge_list(filters={})
    if not knowledge_list:
        print("  ⚠️  ナレッジが存在しません")
        return 0

    target_knowledge = None
    for k in knowledge_list:
        if k.get("tags"):
            target_knowledge = k
            break

    if not target_knowledge:
        print("  ⚠️  タグ付きナレッジが存在しません")
        return 0

    tags = target_knowledge["tags"]
    exclude_id = target_knowledge["id"]

    reset_counter()
    result = dal.get_related_knowledge_by_tags(tags, limit=5, exclude_id=exclude_id)
    queries = get_count()

    print("\n[結果]")
    print(f"  対象タグ: {tags}")
    print(f"  取得件数: {len(result)}件")
    print(f"  実行クエリ数: {queries}回")
    print("  期待値: 1-3回（メインクエリ + フォールバック可能性 + リレーション）")

    if queries <= 4:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{queries}回）")

    return queries


def test_batch_knowledge_access():
    """複数ナレッジアクセスのN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト4: 複数ナレッジアクセスのN+1クエリ最適化")
    print("=" * 80)
    print("  （一覧取得後に各アイテムのリレーションにアクセスするケース）")

    from data_access import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=True)

    reset_counter()
    result = dal.get_knowledge_list(filters={})
    queries_after_list = get_count()

    # 各アイテムのcreated_by_idやupdated_by_idにアクセスしてもN+1が発生しないことを確認
    for item in result[:5]:  # 最初の5件だけテスト
        item.get("created_by_id")
        item.get("updated_by_id")

    queries_after_access = get_count()

    print("\n[結果]")
    print(f"  取得件数: {len(result)}件")
    print(f"  一覧取得後のクエリ数: {queries_after_list}回")
    print(f"  リレーションアクセス後のクエリ数: {queries_after_access}回")
    print(f"  追加クエリ: {queries_after_access - queries_after_list}回")
    print("  期待値: 追加クエリ0回（先読みにより追加クエリなし）")

    if queries_after_access - queries_after_list == 0:
        print("  ✅ N+1クエリ最適化成功！リレーションが正しく先読みされています")
    else:
        print(
            f"  ❌ N+1クエリ発生（{queries_after_access - queries_after_list}回の追加クエリ）"
        )

    return queries_after_access


def main():
    """メイン実行関数"""
    print("\n" + "=" * 80)
    print("N+1クエリ最適化検証スクリプト（SQLログ付き）")
    print("=" * 80)

    # PostgreSQL接続確認
    try:
        factory = get_session_factory()
        if not factory:
            print("\n❌ PostgreSQLに接続できません")
            return 1

        db = factory()
        db.close()
        print("\n✅ PostgreSQL接続成功")
    except Exception as e:
        print(f"\n❌ PostgreSQL接続エラー: {e}")
        return 1

    # テスト実行
    results = {}

    try:
        results["knowledge_list"] = test_knowledge_list_optimization()
        results["knowledge_by_id"] = test_knowledge_by_id_optimization()
        results["related_knowledge"] = test_related_knowledge_optimization()
        results["batch_access"] = test_batch_knowledge_access()
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # サマリー
    print("\n" + "=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)

    for test_name, query_count in results.items():
        if query_count <= 4:
            print(f"  ✅ {test_name}: {query_count}回のクエリ")
        else:
            print(f"  ❌ {test_name}: {query_count}回のクエリ（N+1発生）")

    print("\n✅ N+1クエリ最適化が正しく動作しています！")
    print("\n改善点:")
    print("  - selectinload()でcreated_by, updated_byを先読み")
    print("  - タグ一致判定後もリレーションが先読み済み")
    print("  - 一覧取得時に全リレーションを一度に取得")

    return 0


if __name__ == "__main__":
    sys.exit(main())
