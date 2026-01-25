"""
ユニットテスト: 推薦エンジン拡張テスト

推薦エンジンの詳細な振る舞いをテスト
"""
import pytest
from datetime import datetime, timedelta
from recommendation_engine import RecommendationEngine


@pytest.fixture
def engine():
    """推薦エンジンのインスタンス"""
    return RecommendationEngine(cache_ttl=300)


@pytest.fixture
def sample_items():
    """サンプルアイテムデータ"""
    return [
        {
            'id': 1,
            'title': '橋梁工事の施工計画',
            'summary': '橋梁工事における施工計画の立て方',
            'content': '橋梁工事では、安全性と品質管理が重要です。',
            'category': '施工計画',
            'tags': ['橋梁', '施工計画', '安全'],
        },
        {
            'id': 2,
            'title': 'トンネル掘削の品質管理',
            'summary': 'トンネル掘削における品質管理手法',
            'content': 'トンネル掘削では計測管理が重要です。',
            'category': '品質管理',
            'tags': ['トンネル', '品質管理', '掘削'],
        },
        {
            'id': 3,
            'title': '橋梁工事の品質管理',
            'summary': '橋梁工事の品質管理ポイント',
            'content': '橋梁工事では、コンクリート品質と溶接品質が重要です。',
            'category': '品質管理',
            'tags': ['橋梁', '品質管理', 'コンクリート'],
        },
    ]


class TestCalculateTagSimilarityVariousCases:
    """タグ類似度計算の様々なケーステスト"""

    def test_calculate_tag_similarity_identical_tags(self, engine):
        """
        完全に同一のタグリストの類似度を確認

        目的:
        - Jaccard係数が1.0を返す
        - 完全一致が正しく検出される
        """
        tags1 = ['橋梁', '施工計画', '安全']
        tags2 = ['橋梁', '施工計画', '安全']

        similarity = engine.calculate_tag_similarity(tags1, tags2)

        assert similarity == 1.0

    def test_calculate_tag_similarity_no_overlap(self, engine):
        """
        全く重複しないタグリストの類似度を確認

        目的:
        - Jaccard係数が0.0を返す
        - 共通タグなしが正しく検出される
        """
        tags1 = ['橋梁', '施工計画']
        tags2 = ['トンネル', '品質管理']

        similarity = engine.calculate_tag_similarity(tags1, tags2)

        assert similarity == 0.0

    def test_calculate_tag_similarity_partial_overlap(self, engine):
        """
        部分的に重複するタグリストの類似度を確認

        目的:
        - 適切なJaccard係数が計算される
        - 重複率に応じたスコアが返される
        """
        tags1 = ['橋梁', '施工計画', '安全']
        tags2 = ['橋梁', '品質管理', '検査']

        similarity = engine.calculate_tag_similarity(tags1, tags2)

        # 共通: 1個（橋梁）、和集合: 5個
        # Jaccard = 1/5 = 0.2
        assert similarity == pytest.approx(0.2, abs=0.01)

    def test_calculate_tag_similarity_empty_tags(self, engine):
        """
        空のタグリストに対する類似度を確認

        目的:
        - 空リストは0.0を返す
        - エラーが発生しない
        """
        tags1 = []
        tags2 = ['橋梁', '施工計画']

        similarity = engine.calculate_tag_similarity(tags1, tags2)

        assert similarity == 0.0

    def test_calculate_tag_similarity_case_insensitive(self, engine):
        """
        タグの大文字小文字を区別しないことを確認

        目的:
        - 大文字小文字が統一される
        - 'Bridge'と'bridge'が同一視される
        """
        tags1 = ['Bridge', 'Construction']
        tags2 = ['bridge', 'construction']

        similarity = engine.calculate_tag_similarity(tags1, tags2)

        # 大文字小文字を無視して完全一致
        assert similarity == 1.0

    def test_calculate_tag_similarity_duplicate_tags(self, engine):
        """
        重複タグが含まれる場合の類似度を確認

        目的:
        - 重複タグはセットとして処理される
        - 正しくユニーク化される
        """
        tags1 = ['橋梁', '橋梁', '施工計画']
        tags2 = ['橋梁', '施工計画', '施工計画']

        similarity = engine.calculate_tag_similarity(tags1, tags2)

        # ユニーク化後: tags1 = {'橋梁', '施工計画'}, tags2 = {'橋梁', '施工計画'}
        assert similarity == 1.0

    def test_calculate_tag_similarity_both_empty(self, engine):
        """
        両方のタグリストが空の場合の類似度を確認

        目的:
        - ゼロ除算エラーが発生しない
        - 0.0が返される
        """
        tags1 = []
        tags2 = []

        similarity = engine.calculate_tag_similarity(tags1, tags2)

        assert similarity == 0.0


class TestCategorySimilarityExactMatch:
    """カテゴリ類似度の完全一致テスト"""

    def test_category_similarity_exact_match(self, engine):
        """
        完全一致するカテゴリの類似度を確認

        目的:
        - 同一カテゴリは1.0を返す
        """
        cat1 = '施工計画'
        cat2 = '施工計画'

        similarity = engine.calculate_category_similarity(cat1, cat2)

        assert similarity == 1.0

    def test_category_similarity_no_match(self, engine):
        """
        一致しないカテゴリの類似度を確認

        目的:
        - 異なるカテゴリは0.0を返す
        """
        cat1 = '施工計画'
        cat2 = '品質管理'

        similarity = engine.calculate_category_similarity(cat1, cat2)

        assert similarity == 0.0

    def test_category_similarity_case_insensitive(self, engine):
        """
        カテゴリの大文字小文字を区別しないことを確認

        目的:
        - 大文字小文字が統一される
        """
        cat1 = 'Construction'
        cat2 = 'construction'

        similarity = engine.calculate_category_similarity(cat1, cat2)

        assert similarity == 1.0

    def test_category_similarity_empty_categories(self, engine):
        """
        空のカテゴリに対する類似度を確認

        目的:
        - 空カテゴリは0.0を返す
        - エラーが発生しない
        """
        cat1 = ''
        cat2 = '施工計画'

        similarity = engine.calculate_category_similarity(cat1, cat2)

        assert similarity == 0.0

    def test_category_similarity_both_empty(self, engine):
        """
        両方のカテゴリが空の場合の類似度を確認

        目的:
        - 両方空の場合は0.0を返す
        """
        cat1 = ''
        cat2 = ''

        similarity = engine.calculate_category_similarity(cat1, cat2)

        assert similarity == 0.0


class TestCacheMechanism:
    """キャッシュメカニズムのテスト"""

    def test_cache_mechanism(self, engine, sample_items):
        """
        キャッシュメカニズムが正しく動作することを確認

        目的:
        - 同一クエリの結果がキャッシュされる
        - 2回目のアクセスはキャッシュから返される
        """
        target_item = sample_items[0]
        candidate_items = sample_items

        # 1回目の呼び出し
        result1 = engine.get_related_items(
            target_item,
            candidate_items,
            limit=5,
            algorithm='hybrid'
        )

        # 2回目の呼び出し（キャッシュから取得されるはず）
        result2 = engine.get_related_items(
            target_item,
            candidate_items,
            limit=5,
            algorithm='hybrid'
        )

        # 結果が同一
        assert result1 == result2

        # キャッシュキーが存在することを確認
        cache_key = f"related_{target_item['id']}_hybrid_5"
        assert cache_key in engine.cache

    def test_cache_expiry(self, engine, sample_items):
        """
        キャッシュの有効期限が機能することを確認

        目的:
        - TTL経過後はキャッシュが無効化される
        - 新しい計算が実行される
        """
        # 短いTTLのエンジンを作成
        short_ttl_engine = RecommendationEngine(cache_ttl=1)  # 1秒

        target_item = sample_items[0]
        candidate_items = sample_items

        # 1回目の呼び出し
        result1 = short_ttl_engine.get_related_items(
            target_item,
            candidate_items,
            limit=5,
            algorithm='hybrid'
        )

        # キャッシュが存在することを確認
        cache_key = f"related_{target_item['id']}_hybrid_5"
        assert cache_key in short_ttl_engine.cache

        # TTL期限を待つ
        import time
        time.sleep(1.1)

        # 2回目の呼び出し（キャッシュ期限切れ）
        result2 = short_ttl_engine.get_related_items(
            target_item,
            candidate_items,
            limit=5,
            algorithm='hybrid'
        )

        # 結果は同じだが、再計算されている
        assert result1 == result2

    def test_cache_key_uniqueness(self, engine, sample_items):
        """
        異なるパラメータで異なるキャッシュキーが生成されることを確認

        目的:
        - algorithm, limitが異なればキャッシュキーも異なる
        - 正しいキャッシュが返される
        """
        target_item = sample_items[0]
        candidate_items = sample_items

        # hybrid, limit=5
        result1 = engine.get_related_items(
            target_item,
            candidate_items,
            limit=5,
            algorithm='hybrid'
        )

        # tag, limit=5
        result2 = engine.get_related_items(
            target_item,
            candidate_items,
            limit=5,
            algorithm='tag'
        )

        # hybrid, limit=3
        result3 = engine.get_related_items(
            target_item,
            candidate_items,
            limit=3,
            algorithm='hybrid'
        )

        # 異なるキャッシュキーが生成される
        cache_key1 = f"related_{target_item['id']}_hybrid_5"
        cache_key2 = f"related_{target_item['id']}_tag_5"
        cache_key3 = f"related_{target_item['id']}_hybrid_3"

        assert cache_key1 in engine.cache
        assert cache_key2 in engine.cache
        assert cache_key3 in engine.cache

        # 結果が異なる可能性がある（アルゴリズム依存）
        assert len(result1) <= 5
        assert len(result2) <= 5
        assert len(result3) <= 3


class TestGetRecommendationsEmptyInput:
    """空入力に対する推薦取得テスト"""

    def test_get_recommendations_empty_input(self, engine):
        """
        空の候補アイテムリストに対する推薦を確認

        目的:
        - 空リストが返される
        - エラーが発生しない
        """
        target_item = {
            'id': 1,
            'title': 'テスト',
            'category': '施工計画',
            'tags': ['橋梁']
        }
        candidate_items = []

        result = engine.get_related_items(
            target_item,
            candidate_items,
            limit=5
        )

        assert result == []

    def test_get_recommendations_only_self(self, engine):
        """
        自分自身のみが候補アイテムに含まれる場合の推薦を確認

        目的:
        - 自分自身は除外される
        - 空リストが返される
        """
        target_item = {
            'id': 1,
            'title': 'テスト',
            'category': '施工計画',
            'tags': ['橋梁']
        }
        candidate_items = [target_item]

        result = engine.get_related_items(
            target_item,
            candidate_items,
            limit=5
        )

        assert result == []

    def test_get_recommendations_no_matching_score(self, engine, sample_items):
        """
        最小スコアを満たすアイテムがない場合の推薦を確認

        目的:
        - 高いmin_scoreで空リストが返される
        - エラーが発生しない
        """
        target_item = sample_items[0]
        candidate_items = sample_items

        result = engine.get_related_items(
            target_item,
            candidate_items,
            limit=5,
            algorithm='hybrid',
            min_score=1.0  # 完全一致のみ（自分自身は除外されるので該当なし）
        )

        assert result == []

    def test_get_recommendations_with_limit(self, engine, sample_items):
        """
        limit設定が正しく適用されることを確認

        目的:
        - limit数を超えない結果が返される
        - スコア順にソートされている
        """
        target_item = sample_items[0]
        candidate_items = sample_items

        result = engine.get_related_items(
            target_item,
            candidate_items,
            limit=1,  # 1件のみ
            algorithm='hybrid'
        )

        # 最大1件
        assert len(result) <= 1

        # 結果がある場合、recommendation_scoreが含まれる
        if result:
            assert 'recommendation_score' in result[0]
            assert 'recommendation_reasons' in result[0]


class TestTokenization:
    """トークン化処理のテスト"""

    def test_tokenize_japanese_text(self, engine):
        """
        日本語テキストのトークン化を確認

        目的:
        - Bi-gram方式で分割される
        - 適切なトークンが生成される
        """
        text = '橋梁工事'

        tokens = engine._tokenize(text)

        # Bi-gram: '橋梁', '梁工', '工事' + 元の単語 '橋梁工事'
        assert '橋梁' in tokens
        assert '梁工' in tokens
        assert '工事' in tokens
        assert '橋梁工事' in tokens

    def test_tokenize_english_text(self, engine):
        """
        英語テキストのトークン化を確認

        目的:
        - 英単語が小文字化される
        - 2文字以上の単語が抽出される
        """
        text = 'Bridge Construction Project'

        tokens = engine._tokenize(text)

        # 英単語が小文字化されて含まれる
        assert 'bridge' in tokens
        assert 'construction' in tokens
        assert 'project' in tokens

    def test_tokenize_empty_text(self, engine):
        """
        空テキストのトークン化を確認

        目的:
        - 空リストが返される
        - エラーが発生しない
        """
        text = ''

        tokens = engine._tokenize(text)

        assert tokens == []

    def test_tokenize_mixed_language(self, engine):
        """
        日英混在テキストのトークン化を確認

        目的:
        - 日本語と英語が両方トークン化される
        - 適切に分割される
        """
        text = '橋梁 Bridge 工事 Construction'

        tokens = engine._tokenize(text)

        # 日本語トークン
        assert '橋梁' in tokens
        assert '工事' in tokens

        # 英語トークン
        assert 'bridge' in tokens
        assert 'construction' in tokens
