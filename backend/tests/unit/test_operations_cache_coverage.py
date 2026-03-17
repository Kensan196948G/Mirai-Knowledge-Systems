"""
blueprints/operations.py - キャッシュヒットパス・例外パスのカバレッジテスト

対象: operations_bp の cache_get 返却パスと except 再raise パス
NOTE: blueprintは from app_helpers import cache_get, load_data しているため、
      パッチ先は blueprints.operations モジュール名前空間。
"""

import pytest


class TestOperationsCacheHitPaths:
    """operations.py のキャッシュヒットパスをカバーするテスト群"""

    def test_get_incidents_cache_hit(self, client, auth_headers, monkeypatch):
        """get_incidents: キャッシュヒット時にキャッシュデータを返す (line 62)"""
        import blueprints.operations as mod

        cached_data = {
            "success": True,
            "data": [{"id": 1, "title": "Cached Incident"}],
            "pagination": {"total_items": 1},
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/incidents", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"][0]["title"] == "Cached Incident"

    def test_get_incidents_exception(self, client, auth_headers, monkeypatch):
        """get_incidents: 例外発生時にre-raiseする (lines 73-74)"""
        import blueprints.operations as mod

        def raise_error(filename):
            raise RuntimeError("test load_data error")

        monkeypatch.setattr(mod, "load_data", raise_error)

        resp = client.get("/api/v1/incidents", headers=auth_headers)
        assert resp.status_code == 500

    def test_get_approvals_exception(self, client, auth_headers, monkeypatch):
        """get_approvals: 例外発生時にre-raiseする (lines 112-113)"""
        import blueprints.operations as mod

        def raise_error(filename):
            raise RuntimeError("test load_data error")

        monkeypatch.setattr(mod, "load_data", raise_error)

        resp = client.get("/api/v1/approvals", headers=auth_headers)
        assert resp.status_code == 500

    def test_get_regulation_detail_cache_hit(self, client, auth_headers, monkeypatch):
        """get_regulation_detail: キャッシュヒット時にキャッシュデータを返す (lines 182-183)"""
        import blueprints.operations as mod

        cached_data = {
            "success": True,
            "data": {"id": 1, "title": "Cached Regulation"},
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/regulations/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "Cached Regulation"

    def test_get_projects_cache_hit(self, client, auth_headers, monkeypatch):
        """get_projects: キャッシュヒット時にキャッシュデータを返す (lines 215-216)"""
        import blueprints.operations as mod

        cached_data = {
            "success": True,
            "data": [{"id": 1, "name": "Cached Project"}],
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"][0]["name"] == "Cached Project"

    def test_get_project_detail_cache_hit(self, client, auth_headers, monkeypatch):
        """get_project_detail: キャッシュヒット時にキャッシュデータを返す (lines 245-246)"""
        import blueprints.operations as mod

        cached_data = {
            "success": True,
            "data": {"id": 1, "name": "Cached Project Detail"},
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/projects/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "Cached Project Detail"

    def test_get_experts_cache_hit(self, client, auth_headers, monkeypatch):
        """get_experts: キャッシュヒット時にキャッシュデータを返す (lines 278-279)"""
        import blueprints.operations as mod

        cached_data = {
            "success": True,
            "data": [{"id": 1, "name": "Cached Expert"}],
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/experts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"][0]["name"] == "Cached Expert"

    def test_get_expert_detail_cache_hit(self, client, auth_headers, monkeypatch):
        """get_expert_detail: キャッシュヒット時にキャッシュデータを返す (lines 309-310)"""
        import blueprints.operations as mod

        cached_data = {
            "success": True,
            "data": {"id": 1, "name": "Cached Expert Detail"},
        }
        monkeypatch.setattr(mod, "cache_get", lambda key: cached_data)

        resp = client.get("/api/v1/experts/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "Cached Expert Detail"
