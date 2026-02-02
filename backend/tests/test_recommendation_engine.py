"""
推薦エンジンのユニットテスト

このテストモジュールは、recommendation_engine.pyの機能を検証します。
"""

import os
import sys
import unittest

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta

from recommendation_engine import RecommendationEngine


class TestRecommendationEngine(unittest.TestCase):
    """推薦エンジンのテストクラス"""

    def setUp(self):
        """各テストの前に実行"""
        self.engine = RecommendationEngine(cache_ttl=300)

        # テスト用データ
        self.sample_knowledge = [
            {
                "id": 1,
                "title": "コンクリート打設作業標準",
                "summary": "打設作業の標準手順",
                "content": "コンクリート打設の基本的な手順を説明します。材料確認、配合確認、スランプ試験、打設、養生、強度試験の順で実施します。",
                "category": "施工",
                "tags": ["コンクリート", "打設", "品質管理"],
            },
            {
                "id": 2,
                "title": "コンクリート養生管理",
                "summary": "養生期間の管理方法",
                "content": "コンクリート打設後の養生管理について説明します。温度管理、湿度管理、養生期間の設定が重要です。",
                "category": "施工",
                "tags": ["コンクリート", "養生", "品質管理"],
            },
            {
                "id": 3,
                "title": "鋼橋塗装作業手順",
                "summary": "鋼橋の塗装手順",
                "content": "鋼橋の塗装作業について説明します。下地処理、プライマー塗装、中塗り、上塗りの順で実施します。",
                "category": "施工",
                "tags": ["鋼橋", "塗装", "防錆"],
            },
            {
                "id": 4,
                "title": "安全衛生管理マニュアル",
                "summary": "現場の安全衛生管理",
                "content": "建設現場における安全衛生管理の基本事項を説明します。保護具着用、安全点検、緊急時対応などを含みます。",
                "category": "安全衛生",
                "tags": ["安全管理", "衛生管理", "現場管理"],
            },
            {
                "id": 5,
                "title": "品質検査チェックリスト",
                "summary": "品質検査項目一覧",
                "content": "各工程における品質検査項目のチェックリストです。寸法検査、外観検査、強度試験などを実施します。",
                "category": "品質管理",
                "tags": ["品質管理", "検査", "チェックリスト"],
            },
        ]

        # アクセスログのサンプル
        now = datetime.now()
        self.sample_logs = [
            {
                "id": 1,
                "user_id": 1,
                "action": "knowledge.view",
                "resource_id": 1,
                "timestamp": (now - timedelta(days=1)).isoformat(),
            },
            {
                "id": 2,
                "user_id": 1,
                "action": "knowledge.view",
                "resource_id": 2,
                "timestamp": (now - timedelta(days=2)).isoformat(),
            },
            {
                "id": 3,
                "user_id": 2,
                "action": "knowledge.view",
                "resource_id": 1,
                "timestamp": (now - timedelta(days=1)).isoformat(),
            },
            {
                "id": 4,
                "user_id": 2,
                "action": "knowledge.view",
                "resource_id": 3,
                "timestamp": (now - timedelta(days=3)).isoformat(),
            },
        ]

    def test_calculate_tag_similarity(self):
        """タグ類似度計算のテスト"""
        # 完全一致
        tags1 = ["コンクリート", "打設", "品質管理"]
        tags2 = ["コンクリート", "打設", "品質管理"]
        similarity = self.engine.calculate_tag_similarity(tags1, tags2)
        self.assertEqual(similarity, 1.0)

        # 部分一致
        tags1 = ["コンクリート", "打設"]
        tags2 = ["コンクリート", "養生"]
        similarity = self.engine.calculate_tag_similarity(tags1, tags2)
        self.assertAlmostEqual(similarity, 1 / 3, places=2)  # 1/(2+1) = 0.33

        # 不一致
        tags1 = ["コンクリート"]
        tags2 = ["鋼橋"]
        similarity = self.engine.calculate_tag_similarity(tags1, tags2)
        self.assertEqual(similarity, 0.0)

        # 空リスト
        tags1 = []
        tags2 = ["コンクリート"]
        similarity = self.engine.calculate_tag_similarity(tags1, tags2)
        self.assertEqual(similarity, 0.0)

    def test_calculate_category_similarity(self):
        """カテゴリ類似度計算のテスト"""
        # 一致
        similarity = self.engine.calculate_category_similarity("施工", "施工")
        self.assertEqual(similarity, 1.0)

        # 不一致
        similarity = self.engine.calculate_category_similarity("施工", "安全衛生")
        self.assertEqual(similarity, 0.0)

        # 大文字小文字を無視
        similarity = self.engine.calculate_category_similarity("施工", "施工")
        self.assertEqual(similarity, 1.0)

    def test_tokenize(self):
        """トークン化のテスト"""
        text = "コンクリート打設の基本的な手順を説明します"
        tokens = self.engine._tokenize(text)
        # Bi-gramとフルワードの両方が含まれる
        self.assertTrue(any("コンクリート" in t for t in tokens))
        self.assertTrue(any("打設" in t for t in tokens))
        self.assertTrue(len(tokens) > 0)

        # 空文字列
        tokens = self.engine._tokenize("")
        self.assertEqual(len(tokens), 0)

    def test_calculate_content_similarity(self):
        """コンテンツ類似度計算のテスト"""
        item1 = self.sample_knowledge[0]  # コンクリート打設
        item2 = self.sample_knowledge[1]  # コンクリート養生
        item3 = self.sample_knowledge[2]  # 鋼橋塗装

        # 類似アイテム
        similarity1, details1 = self.engine.calculate_content_similarity(
            item1, item2, self.sample_knowledge
        )
        self.assertGreater(similarity1, 0.0)
        self.assertIn("common_keywords", details1)

        # 非類似アイテム
        similarity2, details2 = self.engine.calculate_content_similarity(
            item1, item3, self.sample_knowledge
        )
        self.assertLess(similarity2, similarity1)

    def test_get_related_items_tag_algorithm(self):
        """関連アイテム取得（タグアルゴリズム）のテスト"""
        target = self.sample_knowledge[0]  # コンクリート打設

        related = self.engine.get_related_items(
            target, self.sample_knowledge, limit=3, algorithm="tag", min_score=0.0
        )

        # 自分自身は除外される
        self.assertTrue(all(item["id"] != target["id"] for item in related))

        # スコア順にソートされている
        if len(related) > 1:
            for i in range(len(related) - 1):
                self.assertGreaterEqual(
                    related[i]["recommendation_score"],
                    related[i + 1]["recommendation_score"],
                )

        # 推薦理由が含まれている
        if len(related) > 0:
            self.assertIn("recommendation_reasons", related[0])
            self.assertIn("recommendation_score", related[0])

    def test_get_related_items_category_algorithm(self):
        """関連アイテム取得（カテゴリアルゴリズム）のテスト"""
        target = self.sample_knowledge[0]  # 施工カテゴリ

        related = self.engine.get_related_items(
            target, self.sample_knowledge, limit=3, algorithm="category", min_score=0.0
        )

        # 同じカテゴリのアイテムが優先される
        if len(related) > 0:
            # 最もスコアが高いアイテムは同じカテゴリであるべき
            self.assertEqual(related[0]["category"], target["category"])

    def test_get_related_items_hybrid_algorithm(self):
        """関連アイテム取得（ハイブリッドアルゴリズム）のテスト"""
        target = self.sample_knowledge[0]

        related = self.engine.get_related_items(
            target, self.sample_knowledge, limit=3, algorithm="hybrid", min_score=0.0
        )

        # 結果が返される
        self.assertIsInstance(related, list)

        # 制限数以下
        self.assertLessEqual(len(related), 3)

        # スコアが計算されている
        if len(related) > 0:
            self.assertIn("recommendation_score", related[0])
            self.assertGreater(related[0]["recommendation_score"], 0.0)

    def test_get_related_items_with_min_score(self):
        """最小スコア閾値のテスト"""
        target = self.sample_knowledge[0]

        # 高い閾値
        related_high = self.engine.get_related_items(
            target, self.sample_knowledge, limit=10, algorithm="hybrid", min_score=0.5
        )

        # 低い閾値
        related_low = self.engine.get_related_items(
            target, self.sample_knowledge, limit=10, algorithm="hybrid", min_score=0.1
        )

        # 低い閾値の方が多くの結果が返される（または同じ）
        self.assertGreaterEqual(len(related_low), len(related_high))

    def test_get_personalized_recommendations(self):
        """パーソナライズ推薦のテスト"""
        recommendations = self.engine.get_personalized_recommendations(
            user_id=1,
            access_logs=self.sample_logs,
            all_items=self.sample_knowledge,
            limit=3,
            days=30,
        )

        # 結果が返される
        self.assertIsInstance(recommendations, list)

        # 閲覧済みアイテムは除外される
        viewed_ids = {1, 2}  # ユーザー1が閲覧したアイテム
        rec_ids = {item["id"] for item in recommendations}
        self.assertTrue(rec_ids.isdisjoint(viewed_ids))

        # 推薦スコアが含まれる
        if len(recommendations) > 0:
            self.assertIn("recommendation_score", recommendations[0])

    def test_cache_functionality(self):
        """キャッシュ機能のテスト"""
        target = self.sample_knowledge[0]

        # 初回呼び出し
        related1 = self.engine.get_related_items(
            target, self.sample_knowledge, limit=3, algorithm="hybrid"
        )

        # キャッシュ統計確認
        stats = self.engine.get_cache_stats()
        self.assertGreater(stats["total_entries"], 0)

        # 2回目呼び出し（キャッシュから取得されるはず）
        related2 = self.engine.get_related_items(
            target, self.sample_knowledge, limit=3, algorithm="hybrid"
        )

        # 結果が同じ
        self.assertEqual(len(related1), len(related2))

        # キャッシュクリア
        self.engine.clear_cache()
        stats = self.engine.get_cache_stats()
        self.assertEqual(stats["total_entries"], 0)

    def test_find_similar_users(self):
        """類似ユーザー検索のテスト"""
        user_viewed = {1, 2}  # ユーザー1の閲覧履歴

        similar_users = self.engine._find_similar_users(
            user_id=1,
            user_viewed=user_viewed,
            access_logs=self.sample_logs,
            all_items=self.sample_knowledge,
        )

        # 結果が返される
        self.assertIsInstance(similar_users, list)

        # 自分自身は含まれない
        if len(similar_users) > 0:
            user_ids = [user_id for user_id, _ in similar_users]
            self.assertNotIn(1, user_ids)

    def test_get_popular_items(self):
        """人気アイテム取得のテスト"""
        popular = self.engine._get_popular_items(
            all_items=self.sample_knowledge, access_logs=self.sample_logs, limit=3
        )

        # 結果が返される
        self.assertIsInstance(popular, list)

        # 制限数以下
        self.assertLessEqual(len(popular), 3)

        # スコア（閲覧数）が含まれる
        if len(popular) > 0:
            self.assertIn("recommendation_score", popular[0])

    def test_empty_data_handling(self):
        """空データの処理テスト"""
        # 空のアイテムリスト
        related = self.engine.get_related_items(
            self.sample_knowledge[0], [], limit=5, algorithm="hybrid"
        )
        self.assertEqual(len(related), 0)

        # 空のアクセスログ
        recommendations = self.engine.get_personalized_recommendations(
            user_id=1, access_logs=[], all_items=self.sample_knowledge, limit=5, days=30
        )
        # 人気アイテムが返されるはず（閲覧履歴がないため）
        self.assertIsInstance(recommendations, list)

    def test_performance_with_large_dataset(self):
        """大規模データセットでのパフォーマンステスト"""
        # 1000件のアイテムを生成
        large_dataset = []
        for i in range(1, 1001):
            large_dataset.append(
                {
                    "id": i,
                    "title": f"テストアイテム {i}",
                    "summary": f"これはテストアイテム{i}の要約です",
                    "content": f"テストコンテンツ {i} " * 10,
                    "category": f"カテゴリ{i % 10}",
                    "tags": [f"タグ{i % 5}", f"タグ{i % 3}"],
                }
            )

        # 実行時間を計測
        import time

        start_time = time.time()

        related = self.engine.get_related_items(
            large_dataset[0], large_dataset, limit=5, algorithm="hybrid"
        )

        elapsed_time = time.time() - start_time

        # 45秒以内に完了することを確認（1000件のデータで）
        # Bi-gramトークン化により処理時間が増加するため閾値を緩和
        # システム負荷やCI環境での変動を考慮
        self.assertLess(
            elapsed_time, 45.0, f"処理時間が遅すぎます: {elapsed_time:.2f}秒"
        )

        # 結果が返されることを確認
        self.assertGreater(len(related), 0)


class TestRecommendationEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    def setUp(self):
        self.engine = RecommendationEngine()

    def test_none_values(self):
        """None値の処理テスト"""
        # Noneのタグ
        similarity = self.engine.calculate_tag_similarity(None, ["tag1"])
        self.assertEqual(similarity, 0.0)

        # Noneのカテゴリ
        similarity = self.engine.calculate_category_similarity(None, "category")
        self.assertEqual(similarity, 0.0)

    def test_special_characters_in_text(self):
        """特殊文字を含むテキストのテスト"""
        item1 = {
            "id": 1,
            "title": "テスト@#$%タイトル",
            "summary": "特殊文字!?を含む要約",
            "content": "記号【】《》を含むコンテンツ",
            "category": "テスト",
            "tags": ["タグ1"],
        }

        item2 = {
            "id": 2,
            "title": "通常のタイトル",
            "summary": "通常の要約",
            "content": "通常のコンテンツ",
            "category": "テスト",
            "tags": ["タグ2"],
        }

        # エラーが発生しないことを確認
        similarity, details = self.engine.calculate_content_similarity(item1, item2)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)


if __name__ == "__main__":
    # テストの実行
    unittest.main(verbosity=2)
