"""
blueprints/recommendations.py Blueprint ユニットテスト

テスト対象エンドポイント:
  GET /api/v1/recommendations/personalized   - パーソナライズ推薦
  GET /api/v1/recommendations/cache/stats    - キャッシュ統計（admin専用）
  POST /api/v1/recommendations/cache/clear   - キャッシュクリア（admin専用）
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ============================================================
# GET /api/v1/recommendations/personalized
# ============================================================


class TestGetPersonalizedRecommendations:
    def test_success_default_params(self, client, auth_headers):
        """認証済みでデフォルトパラメータのリクエストが成功する"""
        resp = client.get(
            "/api/v1/recommendations/personalized", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/recommendations/personalized")
        assert resp.status_code == 401

    def test_response_has_parameters(self, client, auth_headers):
        """レスポンスに parameters フィールドが含まれる"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=5&days=30&type=all",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        params = data["data"]["parameters"]
        assert params["limit"] == 5
        assert params["days"] == 30
        assert params["type"] == "all"

    def test_limit_too_small(self, client, auth_headers):
        """limit=0 は 400 INVALID_LIMIT"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=0", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_limit_too_large(self, client, auth_headers):
        """limit=21 は 400 INVALID_LIMIT"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=21", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_limit_minimum_valid(self, client, auth_headers):
        """limit=1 は有効"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=1", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_limit_maximum_valid(self, client, auth_headers):
        """limit=20 は有効"""
        resp = client.get(
            "/api/v1/recommendations/personalized?limit=20", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_days_too_small(self, client, auth_headers):
        """days=0 は 400 INVALID_DAYS"""
        resp = client.get(
            "/api/v1/recommendations/personalized?days=0", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_DAYS"

    def test_days_too_large(self, client, auth_headers):
        """days=366 は 400 INVALID_DAYS"""
        resp = client.get(
            "/api/v1/recommendations/personalized?days=366", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_DAYS"

    def test_days_minimum_valid(self, client, auth_headers):
        """days=1 は有効"""
        resp = client.get(
            "/api/v1/recommendations/personalized?days=1", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_days_maximum_valid(self, client, auth_headers):
        """days=365 は有効"""
        resp = client.get(
            "/api/v1/recommendations/personalized?days=365", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_invalid_type(self, client, auth_headers):
        """不正な type は 400 INVALID_TYPE"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=invalid", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_TYPE"

    def test_type_knowledge(self, client, auth_headers):
        """type=knowledge は有効で knowledge キーが返る"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=knowledge", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "knowledge" in data["data"]
        assert "sop" not in data["data"]

    def test_type_sop(self, client, auth_headers):
        """type=sop は有効で sop キーが返る"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=sop", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sop" in data["data"]
        assert "knowledge" not in data["data"]

    def test_type_all(self, client, auth_headers):
        """type=all は knowledge と sop の両方を返す"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=all", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "knowledge" in data["data"]
        assert "sop" in data["data"]

    def test_knowledge_result_has_items_and_count(self, client, auth_headers):
        """knowledge 結果に items と count フィールドがある"""
        resp = client.get(
            "/api/v1/recommendations/personalized?type=knowledge", headers=auth_headers
        )
        assert resp.status_code == 200
        knowledge = resp.get_json()["data"]["knowledge"]
        assert "items" in knowledge
        assert "count" in knowledge
        assert isinstance(knowledge["items"], list)
        assert isinstance(knowledge["count"], int)

    def test_partner_can_access(self, client, partner_auth_headers):
        """partner_company ロールでもアクセスできる（認証は jwt_required のみ）"""
        resp = client.get(
            "/api/v1/recommendations/personalized", headers=partner_auth_headers
        )
        assert resp.status_code == 200


# ============================================================
# GET /api/v1/recommendations/cache/stats
# ============================================================


class TestGetRecommendationCacheStats:
    def test_admin_can_get_stats(self, client, auth_headers):
        """管理者はキャッシュ統計を取得できる"""
        resp = client.get(
            "/api/v1/recommendations/cache/stats", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/recommendations/cache/stats")
        assert resp.status_code == 401

    def test_non_admin_forbidden(self, client, partner_auth_headers):
        """admin 以外は 403"""
        resp = client.get(
            "/api/v1/recommendations/cache/stats", headers=partner_auth_headers
        )
        assert resp.status_code == 403


# ============================================================
# POST /api/v1/recommendations/cache/clear
# ============================================================


class TestClearRecommendationCache:
    def test_admin_can_clear_cache(self, client, auth_headers):
        """管理者はキャッシュをクリアできる"""
        resp = client.post(
            "/api/v1/recommendations/cache/clear", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.post("/api/v1/recommendations/cache/clear")
        assert resp.status_code == 401

    def test_non_admin_forbidden(self, client, partner_auth_headers):
        """admin 以外は 403"""
        resp = client.post(
            "/api/v1/recommendations/cache/clear", headers=partner_auth_headers
        )
        assert resp.status_code == 403

    def test_clear_returns_success_message(self, client, auth_headers):
        """クリア成功時にメッセージが返る"""
        resp = client.post(
            "/api/v1/recommendations/cache/clear", headers=auth_headers
        )
        data = resp.get_json()
        assert "message" in data
        assert "cleared" in data["message"].lower()
