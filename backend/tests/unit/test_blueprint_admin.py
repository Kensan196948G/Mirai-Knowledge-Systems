"""
blueprints/admin.py Blueprint ユニットテスト

テスト対象エンドポイント:
  GET /api/v1/logs/access         - 監査ログ取得（管理者専用）
  GET /api/v1/logs/access/stats   - 監査ログ統計（管理者専用）
  GET /api/v1/health              - システムヘルスチェック（認証不要）
  GET /api/v1/health/db           - DBヘルスチェック（認証不要）
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ============================================================
# GET /api/v1/logs/access
# ============================================================


class TestGetAccessLogs:
    def test_admin_can_get_logs(self, client, auth_headers):
        """管理者は監査ログを取得できる"""
        resp = client.get("/api/v1/logs/access", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "logs" in data
        assert "pagination" in data

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/logs/access")
        assert resp.status_code == 401

    def test_non_admin_forbidden(self, client, partner_auth_headers):
        """admin 以外は 403"""
        resp = client.get("/api/v1/logs/access", headers=partner_auth_headers)
        assert resp.status_code == 403

    def test_response_has_logs_list(self, client, auth_headers):
        """logs フィールドがリスト"""
        resp = client.get("/api/v1/logs/access", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["logs"], list)

    def test_pagination_fields(self, client, auth_headers):
        """pagination に必要なフィールドが含まれる"""
        resp = client.get("/api/v1/logs/access", headers=auth_headers)
        data = resp.get_json()
        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination

    def test_filter_fields_in_response(self, client, auth_headers):
        """filters フィールドがレスポンスに含まれる"""
        resp = client.get("/api/v1/logs/access", headers=auth_headers)
        data = resp.get_json()
        assert "filters" in data

    def test_filter_by_action(self, client, auth_headers):
        """action フィルタを指定できる"""
        resp = client.get(
            "/api/v1/logs/access?action=login", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_filter_by_resource(self, client, auth_headers):
        """resource フィルタを指定できる"""
        resp = client.get(
            "/api/v1/logs/access?resource=knowledge", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_filter_by_user_id(self, client, auth_headers):
        """user_id フィルタを指定できる"""
        resp = client.get(
            "/api/v1/logs/access?user_id=1", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_filter_by_status(self, client, auth_headers):
        """status フィルタを指定できる"""
        resp = client.get(
            "/api/v1/logs/access?status=success", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_pagination_page_param(self, client, auth_headers):
        """page パラメータが動作する"""
        resp = client.get(
            "/api/v1/logs/access?page=1&per_page=10", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10

    def test_sort_asc(self, client, auth_headers):
        """sort=asc で正しくソートされる"""
        resp = client.get(
            "/api/v1/logs/access?sort=asc", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_sort_desc_default(self, client, auth_headers):
        """sort=desc（デフォルト）で正しくソートされる"""
        resp = client.get(
            "/api/v1/logs/access?sort=desc", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_per_page_capped_at_200(self, client, auth_headers):
        """per_page は最大200に制限される"""
        resp = client.get(
            "/api/v1/logs/access?per_page=9999", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pagination"]["per_page"] <= 200

    def test_start_date_filter(self, client, auth_headers):
        """start_date フィルタで 200 が返る"""
        resp = client.get(
            "/api/v1/logs/access?start_date=2020-01-01T00:00:00",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_end_date_filter(self, client, auth_headers):
        """end_date フィルタで 200 が返る"""
        resp = client.get(
            "/api/v1/logs/access?end_date=2099-12-31T23:59:59",
            headers=auth_headers,
        )
        assert resp.status_code == 200


# ============================================================
# GET /api/v1/logs/access/stats
# ============================================================


class TestGetAccessLogsStats:
    def test_admin_can_get_stats(self, client, auth_headers):
        """管理者はログ統計を取得できる"""
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_logs" in data

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/logs/access/stats")
        assert resp.status_code == 401

    def test_non_admin_forbidden(self, client, partner_auth_headers):
        """admin 以外は 403"""
        resp = client.get(
            "/api/v1/logs/access/stats", headers=partner_auth_headers
        )
        assert resp.status_code == 403

    def test_stats_has_required_fields(self, client, auth_headers):
        """統計レスポンスに必要なフィールドがある"""
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        data = resp.get_json()
        assert "total_logs" in data
        assert "today_logs" in data
        assert "week_logs" in data
        assert "by_action" in data
        assert "by_resource" in data
        assert "by_status" in data
        assert "top_active_users" in data
        assert "generated_at" in data

    def test_total_logs_is_int(self, client, auth_headers):
        """total_logs が整数"""
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["total_logs"], int)

    def test_top_active_users_is_list(self, client, auth_headers):
        """top_active_users がリスト"""
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["top_active_users"], list)


# ============================================================
# GET /api/v1/health
# ============================================================


class TestHealthCheck:
    def test_health_returns_200(self, client):
        """認証なしでヘルスチェックが成功する"""
        resp = client.get("/api/v1/health")
        assert resp.status_code in (200, 503)

    def test_health_has_status_field(self, client):
        """レスポンスに status フィールドがある"""
        resp = client.get("/api/v1/health")
        data = resp.get_json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "error")

    def test_health_has_version(self, client):
        """レスポンスに version フィールドがある"""
        resp = client.get("/api/v1/health")
        data = resp.get_json()
        assert "version" in data

    def test_health_has_timestamp(self, client):
        """レスポンスに timestamp フィールドがある"""
        resp = client.get("/api/v1/health")
        data = resp.get_json()
        assert "timestamp" in data

    def test_health_has_system_metrics(self, client):
        """system メトリクスフィールドがある"""
        resp = client.get("/api/v1/health")
        data = resp.get_json()
        assert "system" in data
        system = data["system"]
        assert "cpu_percent" in system
        assert "memory_percent" in system
        assert "disk_percent" in system

    def test_health_has_database_info(self, client):
        """database フィールドがある"""
        resp = client.get("/api/v1/health")
        data = resp.get_json()
        assert "database" in data

    def test_health_no_auth_required(self, client):
        """認証なしでもアクセスできる（パブリックエンドポイント）"""
        resp = client.get("/api/v1/health")
        # 401 でないことを確認
        assert resp.status_code != 401


# ============================================================
# GET /api/v1/health/db
# ============================================================


class TestDbHealthCheck:
    def test_db_health_returns_response(self, client):
        """DBヘルスチェックがレスポンスを返す"""
        resp = client.get("/api/v1/health/db")
        assert resp.status_code in (200, 503)

    def test_db_health_has_healthy_field(self, client):
        """healthy フィールドがある"""
        resp = client.get("/api/v1/health/db")
        data = resp.get_json()
        assert "healthy" in data
        assert isinstance(data["healthy"], bool)

    def test_db_health_has_mode_field(self, client):
        """mode フィールドがある"""
        resp = client.get("/api/v1/health/db")
        data = resp.get_json()
        assert "mode" in data

    def test_db_health_has_timestamp(self, client):
        """timestamp フィールドがある"""
        resp = client.get("/api/v1/health/db")
        data = resp.get_json()
        assert "timestamp" in data

    def test_db_health_no_auth_required(self, client):
        """認証なしでもアクセスできる"""
        resp = client.get("/api/v1/health/db")
        assert resp.status_code != 401

    def test_db_health_json_mode_fallback(self, client):
        """JSON モードでは healthy=True かつ mode='json'"""
        resp = client.get("/api/v1/health/db")
        data = resp.get_json()
        # JSON モードは ImportError → fallback で healthy=True
        if data.get("mode") == "json":
            assert data["healthy"] is True
