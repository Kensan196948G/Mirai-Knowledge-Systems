#!/usr/bin/env python3
"""
N+1クエリ最適化の検証スクリプト

このスクリプトは、PostgreSQLモードで実行し、
SQLAlchemyのechoを有効にしてクエリ数を確認します。
"""

import logging
import os
import sys
from datetime import datetime

# 環境変数を設定してPostgreSQLモードを有効化
os.environ["MKS_USE_POSTGRESQL"] = "true"
os.environ["MKS_ENV"] = "development"

# SQLAlchemyのクエリログを有効化
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

from data_access import DataAccessLayer
from database import get_session_factory


def count_queries(func):
    """クエリ数をカウントするデコレータ"""
    query_count = {"count": 0}

    def wrapper(*args, **kwargs):
        # クエリカウンタをリセット
        query_count["count"] = 0

        # ロギングハンドラを追加してクエリをカウント
        logger = logging.getLogger("sqlalchemy.engine")
        original_level = logger.level

        class QueryCounter(logging.Handler):
            def emit(self, record):
                if "SELECT" in record.getMessage():
                    query_count["count"] += 1

        counter = QueryCounter()
        logger.addHandler(counter)

        # 関数実行
        result = func(*args, **kwargs)

        # ハンドラを削除
        logger.removeHandler(counter)
        logger.setLevel(original_level)

        return result, query_count["count"]

    return wrapper


def test_knowledge_list_optimization():
    """ナレッジ一覧取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト1: ナレッジ一覧取得のN+1クエリ最適化")
    print("=" * 80)

    dal = DataAccessLayer(use_postgresql=True)

    @count_queries
    def get_knowledge_list():
        return dal.get_knowledge_list(filters={"search": ""})

    result, query_count = get_knowledge_list()

    print("\n結果:")
    print(f"  取得件数: {len(result)}件")
    print(f"  クエリ数: {query_count}回")
    print("  期待値: 1回（selectinloadによる先読み）")

    if query_count <= 2:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{query_count}回）")

    return query_count


def test_knowledge_by_id_optimization():
    """ナレッジ詳細取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト2: ナレッジ詳細取得のN+1クエリ最適化")
    print("=" * 80)

    dal = DataAccessLayer(use_postgresql=True)

    # まず最初のナレッジIDを取得
    knowledge_list = dal.get_knowledge_list(filters={})
    if not knowledge_list:
        print("  ⚠️  ナレッジが存在しません")
        return 0

    knowledge_id = knowledge_list[0]["id"]

    @count_queries
    def get_knowledge_by_id():
        return dal.get_knowledge_by_id(knowledge_id)

    result, query_count = get_knowledge_by_id()

    print("\n結果:")
    print(f"  ナレッジID: {knowledge_id}")
    print(f"  クエリ数: {query_count}回")
    print("  期待値: 1回（selectinloadによる先読み）")

    if query_count <= 2:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{query_count}回）")

    return query_count


def test_related_knowledge_optimization():
    """関連ナレッジ取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト3: 関連ナレッジ取得のN+1クエリ最適化")
    print("=" * 80)

    dal = DataAccessLayer(use_postgresql=True)

    # ナレッジを取得してタグを確認
    knowledge_list = dal.get_knowledge_list(filters={})
    if not knowledge_list:
        print("  ⚠️  ナレッジが存在しません")
        return 0

    # タグがあるナレッジを探す
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

    @count_queries
    def get_related_knowledge():
        return dal.get_related_knowledge_by_tags(tags, limit=5, exclude_id=exclude_id)

    result, query_count = get_related_knowledge()

    print("\n結果:")
    print(f"  対象タグ: {tags}")
    print(f"  取得件数: {len(result)}件")
    print(f"  クエリ数: {query_count}回")
    print("  期待値: 1-2回（メインクエリ + フォールバック）")

    if query_count <= 3:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{query_count}回）")

    return query_count


def test_sop_list_optimization():
    """SOP一覧取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト4: SOP一覧取得のN+1クエリ最適化")
    print("=" * 80)

    dal = DataAccessLayer(use_postgresql=True)

    @count_queries
    def get_sop_list():
        return dal.get_sop_list(filters={})

    result, query_count = get_sop_list()

    print("\n結果:")
    print(f"  取得件数: {len(result)}件")
    print(f"  クエリ数: {query_count}回")
    print("  期待値: 1回（selectinloadによる先読み）")

    if query_count <= 2:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{query_count}回）")

    return query_count


def test_incident_list_optimization():
    """インシデント一覧取得のN+1クエリ最適化検証"""
    print("\n" + "=" * 80)
    print("テスト5: インシデント一覧取得のN+1クエリ最適化")
    print("=" * 80)

    dal = DataAccessLayer(use_postgresql=True)

    @count_queries
    def get_incidents_list():
        return dal.get_incidents_list(filters={})

    result, query_count = get_incidents_list()

    print("\n結果:")
    print(f"  取得件数: {len(result)}件")
    print(f"  クエリ数: {query_count}回")
    print("  期待値: 1回（selectinloadによる先読み）")

    if query_count <= 2:
        print("  ✅ N+1クエリ最適化成功！")
    else:
        print(f"  ❌ N+1クエリ発生（{query_count}回）")

    return query_count


def main():
    """メイン実行関数"""
    print("\n" + "=" * 80)
    print("N+1クエリ最適化検証スクリプト")
    print("=" * 80)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # PostgreSQL接続確認
    try:
        factory = get_session_factory()
        if not factory:
            print("\n❌ PostgreSQLに接続できません")
            print("環境変数 MKS_USE_POSTGRESQL=true を確認してください")
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
        results["sop_list"] = test_sop_list_optimization()
        results["incident_list"] = test_incident_list_optimization()
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # サマリー
    print("\n" + "=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for count in results.values() if count <= 3)

    for test_name, query_count in results.items():
        status = "✅ PASS" if query_count <= 3 else "❌ FAIL"
        print(f"  {test_name}: {query_count}回のクエリ {status}")

    print(f"\n合計: {passed_tests}/{total_tests} テスト成功")

    if passed_tests == total_tests:
        print("\n🎉 すべてのN+1クエリ最適化が成功しました！")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests}個のテストが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
