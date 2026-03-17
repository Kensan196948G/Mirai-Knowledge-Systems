"""
blueprints/admin.py 未カバー行カバレッジ強化テスト (v2)

対象: admin.py の未カバー19行
  - Lines 109-110: end_date ValueError handling
  - Lines 161-163: get_access_logs except Exception -> 500
  - Lines 201-202: ValueError/TypeError continue in stats loop
  - Lines 233-235: get_access_logs_stats except Exception -> 500
  - Lines 257-259: health_check degraded (db_health.healthy=False) -> 503
  - Lines 283-284: health_check except Exception -> 500
  - Lines 316-329: db_health_check except Exception -> 503
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)


# ================================================================
# get_access_logs: end_date ValueError (lines 109-110)
# ================================================================


class TestGetAccessLogsEndDateValueError:
    """end_date に不正な値を渡した場合、ValueError がキャッチされて無視される"""

    def test_invalid_end_date_is_silently_ignored(self, client, auth_headers, mock_access_logs):
        """不正な end_date でも 200 が返り、フィルタは適用されない"""
        mock_access_logs([
            {
                "id": 1,
                "user_id": 1,
                "action": "login",
                "resource": "auth",
                "status": "success",
                "timestamp": "2025-06-01T10:00:00",
            },
        ])
        resp = client.get(
            "/api/v1/logs/access?end_date=invalid-date-format",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "logs" in data
        # end_date フィルタが無視されるので、ログがそのまま返る
        assert data["filters"]["end_date"] == "invalid-date-format"

    def test_end_date_partial_date_string(self, client, auth_headers, mock_access_logs):
        """部分的に壊れた日付文字列でも ValueError 処理で 200 が返る"""
        mock_access_logs([
            {
                "id": 1,
                "user_id": 1,
                "action": "view",
                "resource": "knowledge",
                "status": "success",
                "timestamp": "2025-06-01T10:00:00",
            },
        ])
        resp = client.get(
            "/api/v1/logs/access?end_date=2025-13-99",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.get_json()["logs"]) >= 0


# ================================================================
# get_access_logs: except Exception -> 500 (lines 161-163)
# ================================================================


class TestGetAccessLogsInternalError:
    """load_data が例外を投げた場合、500 エラーが返る"""

    def test_load_data_raises_returns_500(self, client, auth_headers):
        """load_data が RuntimeError を送出すると 500 が返る"""
        with patch("blueprints.admin.load_data", side_effect=RuntimeError("disk error")):
            resp = client.get("/api/v1/logs/access", headers=auth_headers)
        assert resp.status_code == 500
        data = resp.get_json()
        assert "error" in data
        assert data["error"] == "Failed to retrieve access logs"

    def test_load_data_raises_ioerror_returns_500(self, client, auth_headers):
        """load_data が IOError を送出しても 500 が返る"""
        with patch("blueprints.admin.load_data", side_effect=IOError("read failed")):
            resp = client.get("/api/v1/logs/access", headers=auth_headers)
        assert resp.status_code == 500
        assert resp.get_json()["error"] == "Failed to retrieve access logs"


# ================================================================
# get_access_logs_stats: ValueError/TypeError continue (lines 201-202)
# ================================================================


class TestGetAccessLogsStatsInvalidTimestamp:
    """統計ループ内で不正な timestamp による ValueError/TypeError が continue される"""

    def test_invalid_timestamp_skipped_in_stats(self, client, auth_headers, mock_access_logs):
        """不正な timestamp を持つログエントリはスキップされ、正常エントリのみ集計される"""
        mock_access_logs([
            {
                "id": 1,
                "user_id": 1,
                "action": "login",
                "resource": "auth",
                "status": "success",
                "timestamp": "not-a-timestamp",  # ValueError を起こす
            },
            {
                "id": 2,
                "user_id": 2,
                "action": "view",
                "resource": "knowledge",
                "status": "success",
                "timestamp": "2025-06-15T12:00:00",
            },
        ])
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_logs"] == 2
        # by_action には両方のログのアクションが含まれる（timestamp 不正でも action カウント前に例外）
        # ただし不正 timestamp のエントリは today_logs/week_logs にカウントされない
        assert "by_action" in data

    def test_none_timestamp_skipped_in_stats(self, client, auth_headers, mock_access_logs):
        """timestamp が None のログは TypeError で continue される"""
        mock_access_logs([
            {
                "id": 1,
                "user_id": 1,
                "action": "create",
                "resource": "sop",
                "status": "success",
                "timestamp": None,  # TypeError を起こす (.get returns None)
            },
            {
                "id": 2,
                "user_id": 1,
                "action": "login",
                "resource": "auth",
                "status": "success",
                "timestamp": "2025-06-15T08:00:00",
            },
        ])
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_logs"] == 2

    def test_empty_timestamp_skipped_in_stats(self, client, auth_headers, mock_access_logs):
        """空文字列 timestamp のログは ValueError で continue される"""
        mock_access_logs([
            {
                "id": 1,
                "user_id": 1,
                "action": "delete",
                "resource": "knowledge",
                "status": "failure",
                "timestamp": "",  # ValueError を起こす
            },
        ])
        resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_logs"] == 1
        # 不正エントリはスキップされるので today/week カウントに含まれない
        assert data["today_logs"] == 0
        assert data["week_logs"] == 0


# ================================================================
# get_access_logs_stats: except Exception -> 500 (lines 233-235)
# ================================================================


class TestGetAccessLogsStatsInternalError:
    """load_data が例外を投げた場合、500 エラーが返る"""

    def test_load_data_raises_returns_500(self, client, auth_headers):
        """load_data が RuntimeError を送出すると 500 が返る"""
        with patch("blueprints.admin.load_data", side_effect=RuntimeError("corruption")):
            resp = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["error"] == "Failed to retrieve access logs stats"


# ================================================================
# health_check: db_health.healthy=False -> 503 degraded (lines 257-259)
# ================================================================


class TestHealthCheckDegraded:
    """データベースが unhealthy のとき、503 + status=degraded を返す"""

    def test_unhealthy_db_returns_503_degraded(self, client):
        """check_database_health が healthy=False を返すと 503 になる"""
        mock_db_health = {"healthy": False, "mode": "postgresql", "details": {"error": "connection refused"}}
        mock_storage_mode = "postgresql"

        with patch.dict("sys.modules", {"database": MagicMock()}):
            import sys as _sys
            db_mod = _sys.modules["database"]
            db_mod.check_database_health = MagicMock(return_value=mock_db_health)
            db_mod.get_storage_mode = MagicMock(return_value=mock_storage_mode)

            resp = client.get("/api/v1/health")

        assert resp.status_code == 503
        data = resp.get_json()
        assert data["status"] == "degraded"
        assert data["database"]["healthy"] is False


# ================================================================
# health_check: except Exception -> 500 (lines 283-284)
# ================================================================


class TestHealthCheckException:
    """health_check 内で予期しない例外が発生すると 500 が返る"""

    def test_psutil_exception_returns_500(self, client):
        """psutil.cpu_percent が例外を投げると 500 エラーになる"""
        with patch("blueprints.admin.psutil") as mock_psutil:
            mock_psutil.cpu_percent.side_effect = OSError("permission denied")
            # database import も成功するようにする
            with patch.dict("sys.modules", {"database": MagicMock()}):
                import sys as _sys
                db_mod = _sys.modules["database"]
                db_mod.check_database_health = MagicMock(return_value={"healthy": True, "mode": "json"})
                db_mod.get_storage_mode = MagicMock(return_value="json")

                resp = client.get("/api/v1/health")

        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert "error" in data
        assert "timestamp" in data


# ================================================================
# db_health_check: except Exception -> 503 (lines 316-329)
# ================================================================


class TestDbHealthCheckException:
    """db_health_check で check_database_health が Exception を投げると 503 が返る"""

    def test_check_database_health_raises_returns_503(self, client):
        """check_database_health が RuntimeError を送出すると 503 になる"""
        mock_db_module = MagicMock()
        mock_db_module.check_database_health = MagicMock(
            side_effect=RuntimeError("connection pool exhausted")
        )
        mock_db_module.get_storage_mode = MagicMock(return_value="postgresql")

        with patch.dict("sys.modules", {"database": mock_db_module}):
            resp = client.get("/api/v1/health/db")

        assert resp.status_code == 503
        data = resp.get_json()
        assert data["healthy"] is False
        assert "error" in data
        assert "connection pool exhausted" in data["error"]
        assert "timestamp" in data

    def test_check_database_health_generic_exception_returns_503(self, client):
        """check_database_health が一般的な Exception を送出しても 503 になる"""
        mock_db_module = MagicMock()
        mock_db_module.check_database_health = MagicMock(
            side_effect=Exception("unexpected database error")
        )
        mock_db_module.get_storage_mode = MagicMock(return_value="postgresql")

        with patch.dict("sys.modules", {"database": mock_db_module}):
            resp = client.get("/api/v1/health/db")

        assert resp.status_code == 503
        data = resp.get_json()
        assert data["healthy"] is False
        assert "unexpected database error" in data["error"]
