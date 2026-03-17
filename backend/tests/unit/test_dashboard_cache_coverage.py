"""
blueprints/dashboard.py - キャッシュヒットパス・例外パスのカバレッジテスト

対象: dashboard_bp の cache_get 返却パスと except 再raise パス
NOTE: blueprintは from app_helpers import cache_get, load_data しているため、
      パッチ先は blueprints.dashboard モジュール名前空間。
"""

import pytest


class TestDashboardCacheHitPaths:
    """dashboard.py のキャッシュヒットパスをカバーするテスト群"""

    def test_get_sop_cache_hit(self, client, auth_headers, monkeypatch):
        """get_sop: キャッシュヒット時にキャッシュデータを返す (lines 48-49)"""
        import blueprints.dashboard as mod

        cached_data = {
            "success": True,
            "data": [{"id": 1, "title": "Cached SOP"}],
            "pagination": {"total_items": 1},
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/sop", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"][0]["title"] == "Cached SOP"

    def test_get_sop_exception(self, client, auth_headers, monkeypatch):
        """get_sop: 例外発生時にre-raiseする (lines 61-63)"""
        import blueprints.dashboard as mod

        def raise_error(filename):
            raise RuntimeError("test load_data error")

        monkeypatch.setattr(mod, "load_data", raise_error)

        resp = client.get("/api/v1/sop", headers=auth_headers)
        assert resp.status_code == 500

    def test_get_related_sop_cache_hit(self, client, auth_headers, monkeypatch):
        """get_related_sop: キャッシュヒット時にキャッシュデータを返す (lines 106-107)"""
        import blueprints.dashboard as mod

        cached_data = {
            "success": True,
            "data": {
                "target_id": 1,
                "related_items": [{"id": 2, "title": "Related SOP"}],
                "algorithm": "hybrid",
                "count": 1,
            },
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/sop/1/related", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["target_id"] == 1
        assert len(data["data"]["related_items"]) == 1

    def test_get_dashboard_stats_cache_hit(self, client, auth_headers, monkeypatch):
        """get_dashboard_stats: キャッシュヒット時にキャッシュデータを返す (line 178)"""
        import blueprints.dashboard as mod

        cached_data = {
            "success": True,
            "data": {
                "kpis": {"knowledge_reuse_rate": 80},
                "counts": {"total_knowledge": 42},
            },
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["kpis"]["knowledge_reuse_rate"] == 80
