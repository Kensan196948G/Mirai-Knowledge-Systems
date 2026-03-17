"""
dal/experts.py, dal/knowledge.py - キャッシュヒットパスのカバレッジテスト

対象:
  - dal/experts.py  line 64  (get_experts_list cache hit)
  - dal/experts.py  line 373 (calculate_expert_rating cache hit)
  - dal/knowledge.py line 69  (get_knowledge_list cache hit)
"""

import pytest

from dal import DataAccessLayer


class TestExpertsDALCacheHitPaths:
    """experts.py の DAL キャッシュヒットパスをカバーするテスト群"""

    def test_get_experts_list_cache_hit(self, monkeypatch):
        """get_experts_list: cache_get が値を返す場合にそのまま返す (line 64)"""
        import app_helpers

        monkeypatch.setattr(app_helpers, "CACHE_ENABLED", True)

        cached_experts = [{"id": 1, "name": "Expert A"}, {"id": 2, "name": "Expert B"}]
        monkeypatch.setattr(app_helpers, "cache_get", lambda key: cached_experts)
        monkeypatch.setattr(app_helpers, "cache_set", lambda key, val, ttl=None: None)

        dal = DataAccessLayer(use_postgresql=False)
        result = dal.get_experts_list()
        assert result == cached_experts

    def test_get_experts_list_cache_hit_with_filters(self, monkeypatch):
        """get_experts_list: フィルタ付きでもキャッシュヒットする (line 64)"""
        import app_helpers

        monkeypatch.setattr(app_helpers, "CACHE_ENABLED", True)

        cached_experts = [{"id": 1, "name": "Expert A", "specialization": "safety"}]
        monkeypatch.setattr(app_helpers, "cache_get", lambda key: cached_experts)
        monkeypatch.setattr(app_helpers, "cache_set", lambda key, val, ttl=None: None)

        dal = DataAccessLayer(use_postgresql=False)
        result = dal.get_experts_list(filters={"specialization": "safety"})
        assert result == cached_experts

    def test_calculate_expert_rating_cache_hit(self, monkeypatch):
        """calculate_expert_rating: cache_get が値を返す場合にそのまま返す (line 373)"""
        import app_helpers

        monkeypatch.setattr(app_helpers, "CACHE_ENABLED", True)

        cached_rating = 4.2
        monkeypatch.setattr(app_helpers, "cache_get", lambda key: cached_rating)
        monkeypatch.setattr(app_helpers, "cache_set", lambda key, val, ttl=None: None)

        dal = DataAccessLayer(use_postgresql=False)
        result = dal.calculate_expert_rating(expert_id=1)
        assert result == 4.2


class TestKnowledgeDALCacheHitPaths:
    """knowledge.py の DAL キャッシュヒットパスをカバーするテスト群"""

    def test_get_knowledge_list_cache_hit(self, monkeypatch):
        """get_knowledge_list: cache_get が値を返す場合にそのまま返す (line 69)"""
        import app_helpers

        monkeypatch.setattr(app_helpers, "CACHE_ENABLED", True)

        cached_knowledge = [
            {"id": 1, "title": "Knowledge A"},
            {"id": 2, "title": "Knowledge B"},
        ]
        monkeypatch.setattr(app_helpers, "cache_get", lambda key: cached_knowledge)
        monkeypatch.setattr(app_helpers, "cache_set", lambda key, val, ttl=None: None)

        dal = DataAccessLayer(use_postgresql=False)
        result = dal.get_knowledge_list()
        assert result == cached_knowledge

    def test_get_knowledge_list_cache_hit_with_filters(self, monkeypatch):
        """get_knowledge_list: フィルタ付きでもキャッシュヒットする (line 69)"""
        import app_helpers

        monkeypatch.setattr(app_helpers, "CACHE_ENABLED", True)

        cached_knowledge = [{"id": 1, "title": "Safety Doc", "category": "safety"}]
        monkeypatch.setattr(app_helpers, "cache_get", lambda key: cached_knowledge)
        monkeypatch.setattr(app_helpers, "cache_set", lambda key, val, ttl=None: None)

        dal = DataAccessLayer(use_postgresql=False)
        result = dal.get_knowledge_list(filters={"category": "safety"})
        assert result == cached_knowledge
