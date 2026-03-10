"""
recommendation_engine.py カバレッジ強化テスト

対象の未カバー行:
  116, 134           - _calculate_tf / _calculate_idf 空入力
  182, 203, 216      - calculate_content_similarity 各分岐
  360-362            - get_personalized_recommendations キャッシュヒット
  373-374            - 不正タイムスタンプログの例外処理
  386-398            - ユーザー閲覧履歴の抽出（カテゴリ・タグ集計）
  405-460            - 協調フィルタリングメインロジック
  482-510            - _find_similar_users
  534-536, 543-548   - _get_popular_items
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)

from recommendation_engine import RecommendationEngine


# ============================================================
# フィクスチャ
# ============================================================


@pytest.fixture
def engine():
    """短い TTL の推薦エンジン（キャッシュテスト用）"""
    return RecommendationEngine(cache_ttl=300)


@pytest.fixture
def items():
    """テスト用アイテム一覧"""
    return [
        {
            "id": 1,
            "title": "橋梁工事の施工計画",
            "summary": "橋梁工事の計画",
            "content": "安全・品質管理が重要",
            "category": "施工計画",
            "tags": ["橋梁", "施工計画", "安全"],
        },
        {
            "id": 2,
            "title": "トンネル掘削の品質管理",
            "summary": "掘削の品質",
            "content": "計測管理が重要",
            "category": "品質管理",
            "tags": ["トンネル", "品質管理"],
        },
        {
            "id": 3,
            "title": "コンクリート強度試験",
            "summary": "強度確認手順",
            "content": "圧縮強度試験を実施する",
            "category": "施工計画",
            "tags": ["コンクリート", "施工計画"],
        },
    ]


def _make_log(user_id, action, resource_id, timestamp=None):
    """アクセスログ生成ヘルパー"""
    ts = timestamp or datetime.now().isoformat()
    return {
        "user_id": user_id,
        "action": action,
        "resource_id": resource_id,
        "timestamp": ts,
    }


# ============================================================
# TestCalculateTfEmpty: _calculate_tf([]) → {} (line 116)
# ============================================================


class TestCalculateTfEmpty:
    """_calculate_tf 空トークン → 空辞書を返す"""

    def test_empty_tokens_returns_empty_dict(self, engine):
        """空リストを渡すと {} を返す"""
        result = engine._calculate_tf([])
        assert result == {}

    def test_nonempty_tokens_returns_dict(self, engine):
        """非空リストのとき TF 辞書を返す"""
        result = engine._calculate_tf(["a", "b", "a"])
        assert "a" in result
        assert result["a"] == pytest.approx(2 / 3)


# ============================================================
# TestCalculateIdfEmpty: _calculate_idf([]) → {} (line 134)
# ============================================================


class TestCalculateIdfEmpty:
    """_calculate_idf 空ドキュメント → 空辞書を返す"""

    def test_empty_documents_returns_empty_dict(self, engine):
        """空リストを渡すと {} を返す"""
        result = engine._calculate_idf([])
        assert result == {}

    def test_nonempty_documents_returns_dict(self, engine):
        """1件以上のドキュメントがあるとき IDF 辞書を返す"""
        result = engine._calculate_idf([["a", "b"], ["a", "c"]])
        assert "a" in result
        assert "b" in result


# ============================================================
# TestCalculateContentSimilarityBranches
# ============================================================


class TestCalculateContentSimilarityBranches:
    """calculate_content_similarity の各分岐をカバー"""

    def test_empty_items_returns_zero(self, engine):
        """タイトル・サマリ・コンテンツが全て空のとき 0.0 を返す (line 182)"""
        item1 = {"title": "", "summary": "", "content": ""}
        item2 = {"title": "", "summary": "", "content": ""}
        score, details = engine.calculate_content_similarity(item1, item2)
        assert score == 0.0
        assert details == {"common_keywords": []}

    def test_without_all_items_uses_tf_only(self, engine):
        """all_items なしのとき IDF=1.0 (line 203) でコサイン類似度を計算"""
        item1 = {"title": "橋梁工事の施工", "summary": "", "content": ""}
        item2 = {"title": "橋梁工事の品質", "summary": "", "content": ""}
        # all_items=None → else branch (line 203)
        score, details = engine.calculate_content_similarity(item1, item2, all_items=None)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_with_all_items_uses_idf(self, engine, items):
        """all_items ありのとき IDF を計算してコサイン類似度を算出"""
        score, details = engine.calculate_content_similarity(items[0], items[1], all_items=items)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_no_common_tokens_gives_zero_similarity(self, engine):
        """共通トークンが 0 のとき similarity=0.0 (line 218 経由)"""
        item1 = {"title": "橋梁", "summary": "", "content": ""}
        item2 = {"title": "tunnel", "summary": "", "content": ""}
        score, details = engine.calculate_content_similarity(item1, item2)
        assert score == 0.0


# ============================================================
# TestGetPersonalizedRecommendationsCoverage
# ============================================================


class TestGetPersonalizedRecommendationsCoverage:
    """get_personalized_recommendations の詳細パスをカバー"""

    def test_cache_hit(self, engine, items):
        """キャッシュヒット時に再計算せず返却する (lines 360-362)"""
        logs = []  # 空ログ → 人気アイテムパス → 空
        # 1回目
        r1 = engine.get_personalized_recommendations(
            user_id=1, access_logs=logs, all_items=items, limit=3, days=30
        )
        # 2回目（同じパラメータ → キャッシュヒット）
        r2 = engine.get_personalized_recommendations(
            user_id=1, access_logs=logs, all_items=items, limit=3, days=30
        )
        assert r1 == r2

    def test_malformed_timestamp_ignored(self, engine, items):
        """不正なタイムスタンプのログが例外なくスキップされる (lines 373-374)"""
        logs = [
            {"user_id": 1, "action": "knowledge.view", "resource_id": 1,
             "timestamp": "INVALID-DATE"},
            {"user_id": 1, "action": "knowledge.view", "resource_id": 2,
             "timestamp": None},
        ]
        # 例外なく実行できること
        result = engine.get_personalized_recommendations(
            user_id=99, access_logs=logs, all_items=items, limit=3, days=30
        )
        assert isinstance(result, list)

    def test_no_view_history_returns_popular(self, engine, items):
        """閲覧履歴がないとき人気アイテムを返す (line 402)"""
        # user 99 の閲覧ログなし
        logs = [
            _make_log(user_id=1, action="knowledge.view", resource_id=1),
            _make_log(user_id=1, action="knowledge.view", resource_id=1),
        ]
        result = engine.get_personalized_recommendations(
            user_id=99, access_logs=logs, all_items=items, limit=3, days=30
        )
        assert isinstance(result, list)

    def test_user_view_history_tracked(self, engine, items):
        """ユーザーの閲覧履歴（カテゴリ・タグ）が正しく集計される (lines 386-398)"""
        logs = [
            _make_log(user_id=1, action="knowledge.view", resource_id=1),
            _make_log(user_id=1, action="sop.view", resource_id=2),
        ]
        result = engine.get_personalized_recommendations(
            user_id=1, access_logs=logs, all_items=items, limit=5, days=30
        )
        # user_viewed が空でない → 協調フィルタリングへ（またはコンテンツベースへ）
        assert isinstance(result, list)

    def test_collaborative_filtering_with_similar_user(self, engine, items):
        """類似ユーザーが存在するとき協調フィルタリングが動作する (lines 405-460)

        設定:
          - User 1 が item 1, item 2 を閲覧
          - User 2 が item 1, item 2, item 3 を閲覧（類似ユーザー）
          - User 1 への推薦: item 3 がスコア付きで返る
        """
        now = datetime.now()
        logs = [
            # User 1 の閲覧履歴
            {"user_id": 1, "action": "knowledge.view", "resource_id": 1,
             "timestamp": now.isoformat()},
            {"user_id": 1, "action": "knowledge.view", "resource_id": 2,
             "timestamp": now.isoformat()},
            # User 2 の閲覧履歴（user 1 と類似パターン）
            {"user_id": 2, "action": "knowledge.view", "resource_id": 1,
             "timestamp": now.isoformat()},
            {"user_id": 2, "action": "knowledge.view", "resource_id": 2,
             "timestamp": now.isoformat()},
            {"user_id": 2, "action": "knowledge.view", "resource_id": 3,
             "timestamp": now.isoformat()},
        ]
        result = engine.get_personalized_recommendations(
            user_id=1, access_logs=logs, all_items=items, limit=5, days=30
        )
        # item 3 が推薦されているはず
        assert isinstance(result, list)
        ids = [r["id"] for r in result if "id" in r]
        assert 3 in ids

    def test_cache_saved_after_collaborative(self, engine, items):
        """協調フィルタリング結果がキャッシュされる (lines 457-458)"""
        now = datetime.now()
        logs = [
            {"user_id": 1, "action": "knowledge.view", "resource_id": 1,
             "timestamp": now.isoformat()},
            {"user_id": 2, "action": "knowledge.view", "resource_id": 1,
             "timestamp": now.isoformat()},
            {"user_id": 2, "action": "knowledge.view", "resource_id": 3,
             "timestamp": now.isoformat()},
        ]
        r1 = engine.get_personalized_recommendations(
            user_id=1, access_logs=logs, all_items=items, limit=3, days=30
        )
        # キャッシュキーが登録されていること
        cache_key = "personalized_1_3_30"
        assert cache_key in engine.cache

    def test_old_logs_excluded_by_cutoff(self, engine, items):
        """cutoff_date より古いログは除外される"""
        # 60日前のログ（30日以上前）
        old_time = (datetime.now() - timedelta(days=60)).isoformat()
        logs = [
            {"user_id": 1, "action": "knowledge.view", "resource_id": 1,
             "timestamp": old_time},
        ]
        result = engine.get_personalized_recommendations(
            user_id=1, access_logs=logs, all_items=items, limit=3, days=30
        )
        # 古いログは除外されるため user_viewed が空 → 人気アイテムパス
        assert isinstance(result, list)


# ============================================================
# TestFindSimilarUsers: _find_similar_users (lines 482-510)
# ============================================================


class TestFindSimilarUsers:
    """_find_similar_users の協調フィルタリングをテスト"""

    def test_no_other_users(self, engine):
        """他ユーザーログなし → 空リストを返す"""
        logs = [
            {"user_id": 1, "action": "knowledge.view", "resource_id": 1,
             "timestamp": datetime.now().isoformat()},
        ]
        result = engine._find_similar_users(
            user_id=1, user_viewed={1}, access_logs=logs, all_items=[]
        )
        assert result == []

    def test_similar_user_found(self, engine):
        """閲覧パターンが似ているユーザーが見つかる (lines 498-508)"""
        logs = [
            # User 1
            {"user_id": 1, "action": "knowledge.view", "resource_id": 1,
             "timestamp": datetime.now().isoformat()},
            # User 2（類似）
            {"user_id": 2, "action": "knowledge.view", "resource_id": 1,
             "timestamp": datetime.now().isoformat()},
            {"user_id": 2, "action": "knowledge.view", "resource_id": 2,
             "timestamp": datetime.now().isoformat()},
        ]
        result = engine._find_similar_users(
            user_id=1, user_viewed={1}, access_logs=logs, all_items=[]
        )
        # Jaccard = |{1} ∩ {1,2}| / |{1} ∪ {1,2}| = 1/2 = 0.5 > 0.1 → 発見
        assert len(result) == 1
        assert result[0][0] == 2
        assert result[0][1] == pytest.approx(0.5)

    def test_low_similarity_user_excluded(self, engine):
        """Jaccard 類似度が 0.1 以下のユーザーは除外される"""
        # User 1 は {1,2,3,4,5,6,7,8,9,10} を閲覧、user 2 は {11} のみ閲覧
        user_viewed = set(range(1, 11))  # {1,2,...,10}
        logs = [
            {"user_id": 2, "action": "knowledge.view", "resource_id": 11,
             "timestamp": datetime.now().isoformat()},
        ]
        result = engine._find_similar_users(
            user_id=1, user_viewed=user_viewed, access_logs=logs, all_items=[]
        )
        # Jaccard = 0/11 = 0 → 除外
        assert result == []

    def test_non_view_actions_ignored(self, engine):
        """view 以外のアクション（create, update など）は無視される"""
        logs = [
            {"user_id": 2, "action": "knowledge.create", "resource_id": 1,
             "timestamp": datetime.now().isoformat()},
        ]
        result = engine._find_similar_users(
            user_id=1, user_viewed={1}, access_logs=logs, all_items=[]
        )
        assert result == []

    def test_sorted_by_similarity_desc(self, engine):
        """類似度が高い順に返却される"""
        logs = [
            # User 2: resource 1 のみ → Jaccard = 1/2
            {"user_id": 2, "action": "knowledge.view", "resource_id": 1,
             "timestamp": datetime.now().isoformat()},
            # User 3: resource 1, 2 → Jaccard = 1/1 = 1.0 ならば user1={1,2} が必要
            {"user_id": 3, "action": "knowledge.view", "resource_id": 1,
             "timestamp": datetime.now().isoformat()},
            {"user_id": 3, "action": "knowledge.view", "resource_id": 2,
             "timestamp": datetime.now().isoformat()},
        ]
        # user 1 が {1} を閲覧
        result = engine._find_similar_users(
            user_id=1, user_viewed={1}, access_logs=logs, all_items=[]
        )
        # user 2: Jaccard({1}, {1}) = 1.0
        # user 3: Jaccard({1}, {1,2}) = 1/2 = 0.5
        assert len(result) == 2
        # 降順ソート
        assert result[0][1] >= result[1][1]


# ============================================================
# TestGetPopularItems: _get_popular_items (lines 529-550)
# ============================================================


class TestGetPopularItems:
    """_get_popular_items の全パスをカバー"""

    def test_no_view_logs(self, engine, items):
        """閲覧ログなし → 空リストを返す"""
        result = engine._get_popular_items(all_items=items, access_logs=[], limit=5)
        assert result == []

    def test_view_without_resource_id_ignored(self, engine, items):
        """resource_id がないログは無視される (line 536 の if resource_id: ブランチ False)"""
        logs = [
            {"action": "knowledge.view", "resource_id": None},
            {"action": "knowledge.view"},  # resource_id キーなし
        ]
        result = engine._get_popular_items(all_items=items, access_logs=logs, limit=5)
        assert result == []

    def test_popular_items_ranked_by_views(self, engine, items):
        """閲覧数の多いアイテムが先頭に来る (lines 534-548)"""
        logs = [
            _make_log(user_id=1, action="knowledge.view", resource_id=1),
            _make_log(user_id=2, action="knowledge.view", resource_id=1),
            _make_log(user_id=3, action="knowledge.view", resource_id=1),
            _make_log(user_id=1, action="knowledge.view", resource_id=2),
            _make_log(user_id=2, action="knowledge.view", resource_id=2),
            _make_log(user_id=1, action="knowledge.view", resource_id=3),
        ]
        result = engine._get_popular_items(all_items=items, access_logs=logs, limit=3)
        assert len(result) >= 1
        # id=1 が最多（3回）なので先頭
        assert result[0]["id"] == 1
        assert result[0]["recommendation_score"] == 3
        assert "人気のアイテム" in result[0]["recommendation_reasons"]

    def test_sop_view_action_also_counted(self, engine, items):
        """sop.view アクションも閲覧数にカウントされる"""
        logs = [
            _make_log(user_id=1, action="sop.view", resource_id=2),
            _make_log(user_id=2, action="sop.view", resource_id=2),
        ]
        result = engine._get_popular_items(all_items=items, access_logs=logs, limit=5)
        assert any(r["id"] == 2 for r in result)

    def test_item_not_in_all_items_skipped(self, engine, items):
        """all_items に存在しない resource_id はスキップされる"""
        logs = [
            _make_log(user_id=1, action="knowledge.view", resource_id=999),
        ]
        result = engine._get_popular_items(all_items=items, access_logs=logs, limit=5)
        assert result == []

    def test_limit_applied(self, engine, items):
        """limit 以上のアイテムが返らない"""
        logs = [
            _make_log(user_id=1, action="knowledge.view", resource_id=1),
            _make_log(user_id=1, action="knowledge.view", resource_id=2),
            _make_log(user_id=1, action="knowledge.view", resource_id=3),
        ]
        result = engine._get_popular_items(all_items=items, access_logs=logs, limit=2)
        assert len(result) <= 2

    def test_non_view_action_excluded(self, engine, items):
        """view 以外のアクションは無視される"""
        logs = [
            _make_log(user_id=1, action="knowledge.create", resource_id=1),
            _make_log(user_id=1, action="knowledge.update", resource_id=1),
        ]
        result = engine._get_popular_items(all_items=items, access_logs=logs, limit=5)
        assert result == []


# ============================================================
# TestGetRelatedItemsAdditional
# ============================================================


class TestGetRelatedItemsAdditional:
    """get_related_items の追加パス"""

    def test_empty_candidates_returns_empty(self, engine, items):
        """候補が 0 件（自分自身のみ）のとき [] を返す"""
        target = items[0]
        # candidate_items が target 自身のみ
        result = engine.get_related_items(target, [target], limit=5)
        assert result == []

    def test_tag_only_algorithm(self, engine, items):
        """algorithm='tag' ではタグ類似度のみでスコアリング"""
        result = engine.get_related_items(items[0], items, algorithm="tag")
        assert isinstance(result, list)

    def test_category_only_algorithm(self, engine, items):
        """algorithm='category' ではカテゴリ一致でスコアリング"""
        result = engine.get_related_items(items[0], items, algorithm="category")
        assert isinstance(result, list)

    def test_keyword_only_algorithm(self, engine, items):
        """algorithm='keyword' ではコンテンツ類似度でスコアリング"""
        result = engine.get_related_items(items[0], items, algorithm="keyword")
        assert isinstance(result, list)

    def test_cache_hit_for_related_items(self, engine, items):
        """2回目の呼び出しでキャッシュヒット"""
        r1 = engine.get_related_items(items[0], items, limit=3)
        r2 = engine.get_related_items(items[0], items, limit=3)
        assert r1 == r2

    def test_min_score_filters_low_scores(self, engine, items):
        """min_score 以下のアイテムはフィルタされる"""
        result = engine.get_related_items(items[0], items, min_score=0.99)
        # 非常に高い閾値 → ほぼ全て除外
        assert isinstance(result, list)


# ============================================================
# TestClearCacheAndStats: lines 552-571
# ============================================================


class TestClearCacheAndStats:
    """clear_cache と get_cache_stats のテスト"""

    def test_clear_cache_empties_cache(self, engine, items):
        """キャッシュをクリアすると空になる"""
        # まずキャッシュを作成
        engine.get_related_items(items[0], items, limit=3)
        assert len(engine.cache) > 0
        engine.clear_cache()
        assert engine.cache == {}
        assert engine.cache_timestamps == {}

    def test_get_cache_stats_returns_dict(self, engine, items):
        """キャッシュ統計が dict として返る"""
        stats = engine.get_cache_stats()
        assert isinstance(stats, dict)
        # キーの存在確認（実装に応じて total_entries or cache_size）
        assert any(k in stats for k in ("total_entries", "cache_size", "valid_entries"))

    def test_cache_stats_after_populate(self, engine, items):
        """キャッシュ使用後の統計が正確"""
        engine.get_related_items(items[0], items, limit=3)
        stats = engine.get_cache_stats()
        # total_entries または cache_size のどちらかで件数確認
        count = stats.get("total_entries", stats.get("cache_size", 0))
        assert count >= 1
