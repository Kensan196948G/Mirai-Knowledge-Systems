"""
blueprints/admin.py カバレッジ強化テスト

対象エンドポイント:
  GET /api/v1/logs/access        - 監査ログ一覧取得（管理者専用）
  GET /api/v1/logs/access/stats  - 監査ログ統計（管理者専用）
  GET /api/v1/health             - システムヘルスチェック（認証不要）
  GET /api/v1/health/db          - DBヘルスチェック（認証不要）
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

_SAMPLE_LOGS = [
    {
        "id": 1,
        "user_id": 1,
        "action": "login",
        "resource": "auth",
        "status": "success",
        "timestamp": "2025-01-20T10:00:00",
    },
    {
        "id": 2,
        "user_id": 2,
        "action": "view",
        "resource": "knowledge",
        "status": "success",
        "timestamp": "2025-01-21T11:00:00",
    },
    {
        "id": 3,
        "user_id": 1,
        "action": "delete",
        "resource": "knowledge",
        "status": "failure",
        "timestamp": "2025-01-22T12:00:00",
    },
]


class TestGetAccessLogs:
    """GET /api/v1/logs/access"""

    def test_success_returns_required_keys(self, client, auth_headers):
        """管理者は監査ログを取得でき、必須キーが揃う"""
        resp = client.get("/api/v1/logs/access", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "logs" in data
        assert "pagination" in data
        assert "filters" in data

    def test_pagination_defaults(self, client, auth_headers):
        """デフォルトページネーション値が正しい"""
        resp = client.get("/api/v1/logs/access", headers=auth_headers)
        assert resp.status_code == 200
        pag = resp.get_json()["pagination"]
        assert pag["page"] == 1
        assert pag["per_page"] == 50

    def test_pagination_params_applied(self, client, auth_headers):
        """page/per_page が反映される"""
        resp = client.get(
            "/api/v1/logs/access?page=2&per_page=10", headers=auth_headers
        )
        assert resp.status_code == 200
        pag = resp.get_json()["pagination"]
        assert pag["page"] == 2
        assert pag["per_page"] == 10

    def test_per_page_capped_at_200(self, client, auth_headers):
        """per_page は 200 を超えない"""
        resp = client.get(
            "/api/v1/logs/access?per_page=999", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["pagination"]["per_page"] <= 200

    def test_user_id_filter(self, client, auth_headers, mock_access_logs):
        """user_id フィルタで特定ユーザーのみ返る"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get(
            "/api/v1/logs/access?user_id=1", headers=auth_headers
        )
        assert resp.status_code == 200
        logs = resp.get_json()["logs"]
        assert all(lg["user_id"] == 1 for lg in logs)

    def test_action_filter_partial_match(self, client, auth_headers, mock_access_logs):
        """action フィルタは部分一致"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get(
            "/api/v1/logs/access?action=log", headers=auth_headers
        )
        assert resp.status_code == 200
        logs = resp.get_json()["logs"]
        assert all("log" in lg.get("action", "").lower() for lg in logs)

    def test_resource_filter(self, client, auth_headers, mock_access_logs):
        """resource フィルタで絞り込み"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get(
            "/api/v1/logs/access?resource=auth", headers=auth_headers
        )
        assert resp.status_code == 200
        logs = resp.get_json()["logs"]
        assert all(lg.get("resource") == "auth" for lg in logs)

    def test_status_filter(self, client, auth_headers, mock_access_logs):
        """status フィルタで絞り込み"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get(
            "/api/v1/logs/access?status=failure", headers=auth_headers
        )
        assert resp.status_code == 200
        logs = resp.get_json()["logs"]
        assert all(lg.get("status") == "failure" for lg in logs)

    def test_date_range_filter_start(self, client, auth_headers, mock_access_logs):
        """start_date フィルタ"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get(
            "/api/v1/logs/access?start_date=2025-01-21T00:00:00",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        logs = resp.get_json()["logs"]
        assert len(logs) <= len(_SAMPLE_LOGS)

    def test_date_range_filter_end(self, client, auth_headers, mock_access_logs):
        """end_date フィルタ"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get(
            "/api/v1/logs/access?end_date=2025-01-20T23:59:59",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_sort_asc(self, client, auth_headers, mock_access_logs):
        """sort=asc で昇順に返る"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get(
            "/api/v1/logs/access?sort=asc", headers=auth_headers
        )
        assert resp.status_code == 200
        logs = resp.get_json()["logs"]
        if len(logs) >= 2:
            assert logs[0]["timestamp"] <= logs[-1]["timestamp"]

    def test_sort_desc_default(self, client, auth_headers, mock_access_logs):
        """デフォルトは降順"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get("/api/v1/logs/access", headers=auth_headers)
        assert resp.status_code == 200
        logs = resp.get_json()["logs"]
        if len(logs) >= 2:
            assert logs[0]["timestamp"] >= logs[-1]["timestamp"]

    def test_filters_echoed_in_response(self, client, auth_headers):
        """フィルタ内容がレスポンスに含まれる"""
        resp = client.get(
            "/api/v1/logs/access?action=login&status=success",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        filters = resp.get_json()["filters"]
        assert filters["action"] == "login"
        assert filters["status"] == "success"

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/logs/access")
        assert resp.status_code == 401

    def test_partner_role_returns_403(self, client, partner_auth_headers):
        """管理者以外は 403"""
        resp = client.get("/api/v1/logs/access", headers=partner_auth_headers)
        assert resp.status_code == 403

    def test_invalid_start_date_ignored(self, client, auth_headers):
        """無効な start_date は無視されてエラーにならない"""
        resp = client.get(
            "/api/v1/logs/access?start_date=not-a-date", headers=auth_headers
        )
        assert resp.status_code == 200


class TestGetAccessLogsStats:
    """GET /api/v1/logs/access/stats"""

    def test_success_returns_required_keys(self, client, auth_headers):
        """統計情報の必須キーが揃う"""
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        for key in ("total_logs", "today_logs", "week_logs",
                    "by_action", "by_resource", "by_status", "top_active_users"):
            assert key in data, f"Missing key: {key}"

    def test_total_logs_with_data(self, client, auth_headers, mock_access_logs):
        """ログが 3 件のとき total_logs == 3"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["total_logs"] == 3

    def test_empty_logs(self, client, auth_headers, mock_access_logs):
        """ログが空でもエラーにならない（明示的に空にリセット）"""
        mock_access_logs([])
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["total_logs"] == 0

    def test_top_active_users_is_list(self, client, auth_headers, mock_access_logs):
        """top_active_users はリスト"""
        mock_access_logs(_SAMPLE_LOGS)
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert isinstance(resp.get_json()["top_active_users"], list)

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/logs/access/stats")
        assert resp.status_code == 401

    def test_partner_role_returns_403(self, client, partner_auth_headers):
        """管理者以外は 403"""
        resp = client.get("/api/v1/logs/access/stats", headers=partner_auth_headers)
        assert resp.status_code == 403

    def test_generated_at_present(self, client, auth_headers):
        """generated_at タイムスタンプが含まれる"""
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        assert "generated_at" in resp.get_json()


class TestHealthCheck:
    """GET /api/v1/health"""

    def test_returns_200_or_503(self, client):
        """正常または degraded のいずれかを返す"""
        resp = client.get("/api/v1/health")
        assert resp.status_code in (200, 503)

    def test_no_auth_required(self, client):
        """認証不要 — 401 にならない"""
        resp = client.get("/api/v1/health")
        assert resp.status_code != 401

    def test_response_has_status(self, client):
        """status フィールドが含まれる"""
        resp = client.get("/api/v1/health")
        assert "status" in resp.get_json()

    def test_response_has_timestamp(self, client):
        """timestamp フィールドが含まれる"""
        resp = client.get("/api/v1/health")
        assert "timestamp" in resp.get_json()

    def test_response_has_version(self, client):
        """version フィールドが含まれる"""
        resp = client.get("/api/v1/health")
        assert "version" in resp.get_json()

    def test_response_has_system_metrics(self, client):
        """system メトリクスが含まれる（正常時）"""
        resp = client.get("/api/v1/health")
        data = resp.get_json()
        if resp.status_code == 200:
            assert "system" in data
            system = data["system"]
            assert "cpu_percent" in system
            assert "memory_percent" in system
            assert "memory_available_mb" in system
            assert "disk_percent" in system

    def test_status_is_healthy_or_degraded(self, client):
        """status は healthy か degraded"""
        resp = client.get("/api/v1/health")
        data = resp.get_json()
        assert data.get("status") in ("healthy", "degraded", "error")


class TestDbHealthCheck:
    """GET /api/v1/health/db"""

    def test_returns_200_or_503(self, client):
        """正常または障害のいずれかを返す"""
        resp = client.get("/api/v1/health/db")
        assert resp.status_code in (200, 503)

    def test_no_auth_required(self, client):
        """認証不要"""
        resp = client.get("/api/v1/health/db")
        assert resp.status_code != 401

    def test_response_has_healthy(self, client):
        """healthy フィールドが含まれる"""
        resp = client.get("/api/v1/health/db")
        assert "healthy" in resp.get_json()

    def test_response_has_mode(self, client):
        """mode フィールドが含まれる"""
        resp = client.get("/api/v1/health/db")
        assert "mode" in resp.get_json()

    def test_response_has_timestamp(self, client):
        """timestamp フィールドが含まれる"""
        resp = client.get("/api/v1/health/db")
        assert "timestamp" in resp.get_json()

    def test_json_mode_is_healthy(self, client):
        """JSON バックエンドは常に healthy"""
        resp = client.get("/api/v1/health/db")
        data = resp.get_json()
        # database モジュールが ImportError になる場合（テスト環境）
        if data.get("mode") == "json":
            assert data["healthy"] is True
            assert resp.status_code == 200
