"""
blueprints/recommendations.py カバレッジ強化テスト

対象エンドポイント:
  GET  /api/v1/recommendations/personalized   - パーソナライズ推薦
  GET  /api/v1/recommendations/cache/stats    - キャッシュ統計（管理者のみ）
  POST /api/v1/recommendations/cache/clear    - キャッシュクリア（管理者のみ）
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestGetPersonalizedRecommendations:
    """GET /api/v1/recommendations/personalized"""

    def test_returns_200(self, client, auth_headers):
        """推薦一覧を取得できる"""
        resp = client.get(
            "/api/v1/recommendations/personalized", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_default_type_all(self, client, auth_headers):
        """デフォルト type は all → knowledge と sop の両方が含まれる"""
        resp = client.get(
            "/api/v1/recommendations/personalized", headers=auth_headers
        )
        assert resp.status_code == 200
        result = resp.get_json()["data"]
        assert "knowledge" in result
        assert "sop" in result
        assert "parameters" in result

    def test_type_knowledge(self, client, auth_headers):
        """type=knowledge → knowledge のみ返る"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=knowledge",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        result = resp.get_json()["data"]
        assert "knowledge" in result
        assert "sop" not in result

    def test_type_sop(self, client, auth_headers):
        """type=sop → sop のみ返る"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=sop",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        result = resp.get_json()["data"]
        assert "sop" in result
        assert "knowledge" not in result

    def test_invalid_type_returns_400(self, client, auth_headers):
        """無効な type は 400"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=invalid",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_TYPE"

    def test_limit_param(self, client, auth_headers):
        """limit パラメータが parameters に反映される"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=3",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        params = resp.get_json()["data"]["parameters"]
        assert params["limit"] == 3

    def test_invalid_limit_zero_returns_400(self, client, auth_headers):
        """limit=0 は 400"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=0",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_LIMIT"

    def test_invalid_limit_too_large_returns_400(self, client, auth_headers):
        """limit=21 は 400"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=21",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_LIMIT"

    def test_days_param(self, client, auth_headers):
        """days パラメータが parameters に反映される"""
        resp = client.get(
            "/api/v1/recommendations/personalized?days=7",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["parameters"]["days"] == 7

    def test_invalid_days_zero_returns_400(self, client, auth_headers):
        """days=0 は 400"""
        resp = client.get(
            "/api/v1/recommendations/personalized?days=0",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_DAYS"

    def test_invalid_days_too_large_returns_400(self, client, auth_headers):
        """days=366 は 400"""
        resp = client.get(
            "/api/v1/recommendations/personalized?days=366",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_DAYS"

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/recommendations/personalized")
        assert resp.status_code == 401

    def test_partner_can_get_recommendations(self, client, partner_auth_headers):
        """協力会社ユーザーも推薦を取得できる"""
        resp = client.get(
            "/api/v1/recommendations/personalized",
            headers=partner_auth_headers,
        )
        assert resp.status_code == 200

    def test_result_count_respects_limit(self, client, auth_headers):
        """各カテゴリの件数は limit 以下"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=5",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        if "knowledge" in data:
            assert data["knowledge"]["count"] <= 5
        if "sop" in data:
            assert data["sop"]["count"] <= 5


class TestRecommendationCacheStats:
    """GET /api/v1/recommendations/cache/stats"""

    def test_admin_can_get_stats(self, client, auth_headers):
        """管理者はキャッシュ統計を取得できる"""
        resp = client.get(
            "/api/v1/recommendations/cache/stats", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_partner_cannot_get_stats(self, client, partner_auth_headers):
        """管理者以外は 403"""
        resp = client.get(
            "/api/v1/recommendations/cache/stats", headers=partner_auth_headers
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/recommendations/cache/stats")
        assert resp.status_code == 401


class TestRecommendationCacheClear:
    """POST /api/v1/recommendations/cache/clear"""

    def test_admin_can_clear_cache(self, client, auth_headers):
        """管理者はキャッシュをクリアできる"""
        resp = client.post(
            "/api/v1/recommendations/cache/clear", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "message" in data

    def test_partner_cannot_clear_cache(self, client, partner_auth_headers):
        """管理者以外は 403"""
        resp = client.post(
            "/api/v1/recommendations/cache/clear", headers=partner_auth_headers
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.post("/api/v1/recommendations/cache/clear")
        assert resp.status_code == 401
