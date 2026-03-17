"""
blueprints/ms365.py カバレッジ向上テスト

MS365 Blueprint (sync configs / sync status / stats / integration status) のテスト。
外部API依存はモックで回避。
"""

import json
import os
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)


# ============================================================
# Fixtures
# ============================================================

SAMPLE_SYNC_CONFIGS = [
    {
        "id": 1,
        "name": "設計図書同期",
        "site_id": "site-001",
        "drive_id": "drive-001",
        "folder_path": "/設計図書",
        "file_extensions": [".pdf"],
        "sync_schedule": "0 2 * * *",
        "is_enabled": True,
        "last_sync_at": None,
        "next_sync_at": None,
        "sync_strategy": "incremental",
        "metadata_mapping": {},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "created_by_id": 1,
        "updated_by_id": None,
    },
    {
        "id": 2,
        "name": "仕様書同期",
        "site_id": "site-002",
        "drive_id": "drive-002",
        "folder_path": "/仕様書",
        "file_extensions": [".docx"],
        "sync_schedule": "0 3 * * *",
        "is_enabled": False,
        "last_sync_at": None,
        "next_sync_at": None,
        "sync_strategy": "full",
        "metadata_mapping": {},
        "created_at": "2024-02-01T00:00:00",
        "updated_at": "2024-02-01T00:00:00",
        "created_by_id": 1,
        "updated_by_id": None,
    },
]

SAMPLE_SYNC_HISTORIES = [
    {
        "id": 1,
        "config_id": 1,
        "sync_started_at": "2024-03-01T02:00:00",
        "sync_completed_at": "2024-03-01T02:05:00",
        "status": "completed",
        "files_processed": 10,
        "files_created": 5,
        "files_updated": 3,
        "files_skipped": 2,
        "files_failed": 0,
        "error_message": None,
        "execution_time_seconds": 300,
        "triggered_by": "scheduler",
        "created_at": "2024-03-01T02:00:00",
    },
]


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def ms365_client(tmp_path, monkeypatch):
    """MS365 テスト用クライアント"""
    import app_v2
    import app_helpers

    app = app_v2.app
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(tmp_path)
    app.config["JWT_SECRET_KEY"] = "test-secret-key-longer-than-20"
    monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app_helpers, "CACHE_ENABLED", False)
    app_v2.limiter.enabled = False

    users = [
        {
            "id": 1,
            "username": "admin",
            "password_hash": app_v2.hash_password("admin123"),
            "full_name": "Admin User",
            "department": "Admin",
            "roles": ["admin"],
        },
    ]

    _write_json(tmp_path / "users.json", users)
    _write_json(tmp_path / "knowledge.json", [])
    _write_json(tmp_path / "access_logs.json", [])
    _write_json(tmp_path / "sop.json", [])
    _write_json(tmp_path / "notifications.json", [])
    _write_json(tmp_path / "ms365_sync_configs.json", SAMPLE_SYNC_CONFIGS)
    _write_json(tmp_path / "ms365_sync_history.json", SAMPLE_SYNC_HISTORIES)

    with app.test_client() as c:
        yield c


@pytest.fixture()
def ms365_token(ms365_client):
    resp = ms365_client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    )
    return resp.get_json()["data"]["access_token"]


@pytest.fixture()
def ms365_headers(ms365_token):
    return {"Authorization": f"Bearer {ms365_token}"}


def _make_dal_mock(get_all=None, get_one=None, create=None, update=None, delete=None, get_hist=None):
    """DALモックを生成するヘルパー"""
    mock = type("MockDAL", (), {})()
    if get_all is not None:
        mock.get_all_ms365_sync_configs = get_all
    if get_one is not None:
        mock.get_ms365_sync_config = get_one
    if create is not None:
        mock.create_ms365_sync_config = create
    if update is not None:
        mock.update_ms365_sync_config = update
    if delete is not None:
        mock.delete_ms365_sync_config = delete
    if get_hist is not None:
        mock.get_ms365_sync_history = get_hist
        mock.get_recent_ms365_sync_histories = lambda cids, limit_per_config=5: []
    return mock


# ============================================================
# MS365 Sync Configs API
# ============================================================


class TestMs365SyncConfigsList:
    """GET /api/v1/ms365/sync/configs"""

    def test_list_configs_success(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_all=lambda: SAMPLE_SYNC_CONFIGS)
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get("/api/v1/ms365/sync/configs", headers=ms365_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_list_configs_requires_auth(self, ms365_client):
        resp = ms365_client.get("/api/v1/ms365/sync/configs")
        assert resp.status_code == 401

    def test_list_configs_empty(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_all=lambda: [])
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get("/api/v1/ms365/sync/configs", headers=ms365_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []


class TestMs365SyncConfigsCreate:
    """POST /api/v1/ms365/sync/configs"""

    def test_create_config_success(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(
            create=lambda d: {"id": 3, "name": d.get("name", "新規"), **d}
        )
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={
                "name": "新規同期",
                "site_id": "site-003",
                "drive_id": "drive-003",
                "folder_path": "/資料",
            },
            headers=ms365_headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.get_json()
        assert data["success"] is True

    def test_create_config_requires_auth(self, ms365_client):
        resp = ms365_client.post("/api/v1/ms365/sync/configs", json={"name": "test"})
        assert resp.status_code == 401

    def test_create_config_missing_required_field(self, ms365_client, ms365_headers):
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={},
            headers=ms365_headers,
        )
        assert resp.status_code in (400, 422, 500)


class TestMs365SyncConfigsGet:
    """GET /api/v1/ms365/sync/configs/<id>"""

    def test_get_config_success(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_one=lambda cid: {"id": cid, "name": "設計図書同期"})
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get("/api/v1/ms365/sync/configs/1", headers=ms365_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["id"] == 1

    def test_get_config_not_found(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_one=lambda cid: None)
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get("/api/v1/ms365/sync/configs/9999", headers=ms365_headers)
        assert resp.status_code == 404

    def test_get_config_requires_auth(self, ms365_client):
        resp = ms365_client.get("/api/v1/ms365/sync/configs/1")
        assert resp.status_code == 401


class TestMs365SyncConfigsUpdate:
    """PUT /api/v1/ms365/sync/configs/<id>"""

    def test_update_config_success(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(
            get_one=lambda cid: {"id": cid, "name": "旧名"},
            update=lambda cid, d: {"id": cid, "name": d.get("name", "旧名")},
        )
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.put(
            "/api/v1/ms365/sync/configs/1",
            json={"name": "更新後の名前"},
            headers=ms365_headers,
        )
        assert resp.status_code == 200

    def test_update_config_not_found(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_one=lambda cid: None)
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.put(
            "/api/v1/ms365/sync/configs/9999",
            json={"name": "test"},
            headers=ms365_headers,
        )
        assert resp.status_code == 404

    def test_update_config_requires_auth(self, ms365_client):
        resp = ms365_client.put(
            "/api/v1/ms365/sync/configs/1", json={"name": "test"}
        )
        assert resp.status_code == 401


class TestMs365SyncConfigsDelete:
    """DELETE /api/v1/ms365/sync/configs/<id>"""

    def test_delete_config_success(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(
            get_one=lambda cid: {"id": cid, "name": "設計図書同期"},
            delete=lambda cid: True,
        )
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.delete(
            "/api/v1/ms365/sync/configs/1", headers=ms365_headers
        )
        assert resp.status_code == 200

    def test_delete_config_not_found(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_one=lambda cid: None)
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.delete(
            "/api/v1/ms365/sync/configs/9999", headers=ms365_headers
        )
        assert resp.status_code == 404

    def test_delete_config_requires_auth(self, ms365_client):
        resp = ms365_client.delete("/api/v1/ms365/sync/configs/1")
        assert resp.status_code == 401


class TestMs365SyncConfigsHistory:
    """GET /api/v1/ms365/sync/configs/<id>/history"""

    def test_get_history_success(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_one=lambda cid: {"id": cid})
        mock_dal.get_ms365_sync_histories_by_config = lambda cid: []
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs/1/history", headers=ms365_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_get_history_config_not_found(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_one=lambda cid: None)
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs/9999/history", headers=ms365_headers
        )
        assert resp.status_code == 404

    def test_get_history_requires_auth(self, ms365_client):
        resp = ms365_client.get("/api/v1/ms365/sync/configs/1/history")
        assert resp.status_code == 401


# ============================================================
# MS365 Sync Stats/Status
# ============================================================


class TestMs365SyncStats:
    """GET /api/v1/ms365/sync/stats"""

    def test_get_stats_success(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(
            get_all=lambda: SAMPLE_SYNC_CONFIGS,
            get_hist=lambda cids, limit_per_config=5: SAMPLE_SYNC_HISTORIES,
        )
        mock_dal.get_recent_ms365_sync_histories = lambda cids, limit_per_config=5: SAMPLE_SYNC_HISTORIES
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get("/api/v1/ms365/sync/stats", headers=ms365_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "total_configs" in data["data"]

    def test_get_stats_empty_configs(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_all=lambda: [])
        mock_dal.get_recent_ms365_sync_histories = lambda cids, limit_per_config=5: []
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.get("/api/v1/ms365/sync/stats", headers=ms365_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["total_configs"] == 0

    def test_get_stats_requires_auth(self, ms365_client):
        resp = ms365_client.get("/api/v1/ms365/sync/stats")
        assert resp.status_code == 401


class TestMs365SyncStatus:
    """GET /api/v1/ms365/sync/status"""

    def test_get_status_no_services(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        monkeypatch.setattr(bp, "_get_sync_service", lambda: None)
        monkeypatch.setattr(bp, "_get_scheduler_service", lambda: None)
        resp = ms365_client.get("/api/v1/ms365/sync/status", headers=ms365_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["sync_service_available"] is False

    def test_get_status_with_scheduler(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        class MockScheduler:
            def is_running(self):
                return True

            def get_scheduled_jobs(self):
                return [{"id": "job1"}]

        class MockSync:
            pass

        monkeypatch.setattr(bp, "_get_sync_service", lambda: MockSync())
        monkeypatch.setattr(bp, "_get_scheduler_service", lambda: MockScheduler())
        resp = ms365_client.get("/api/v1/ms365/sync/status", headers=ms365_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["scheduler_running"] is True

    def test_get_status_requires_auth(self, ms365_client):
        resp = ms365_client.get("/api/v1/ms365/sync/status")
        assert resp.status_code == 401


# ============================================================
# MS365 Integration Status (prefix: /api/v1/integrations/microsoft365)
# ============================================================


class TestMs365IntegrationStatus:
    """GET /api/v1/integrations/microsoft365/status"""

    def test_status_not_configured(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365_integration as bp_integration

        monkeypatch.setattr(bp_integration, "get_ms_graph_client", lambda: None)
        resp = ms365_client.get(
            "/api/v1/integrations/microsoft365/status", headers=ms365_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["configured"] is False

    def test_status_configured_connected(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365_integration as bp_integration

        class MockGraph:
            def test_connection(self):
                return {"configured": True, "connected": True}

            def is_configured(self):
                return True

        monkeypatch.setattr(bp_integration, "get_ms_graph_client", lambda: MockGraph())
        resp = ms365_client.get(
            "/api/v1/integrations/microsoft365/status", headers=ms365_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["connected"] is True

    def test_status_configured_connection_error(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365_integration as bp_integration

        class MockGraph:
            def test_connection(self):
                raise ConnectionError("Token expired")

            def is_configured(self):
                return True

        monkeypatch.setattr(bp_integration, "get_ms_graph_client", lambda: MockGraph())
        resp = ms365_client.get(
            "/api/v1/integrations/microsoft365/status", headers=ms365_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["connected"] is False

    def test_status_requires_auth(self, ms365_client):
        resp = ms365_client.get("/api/v1/integrations/microsoft365/status")
        assert resp.status_code == 401


class TestMs365Sites:
    """GET /api/v1/integrations/microsoft365/sites"""

    def test_sites_not_configured(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365_integration as bp_integration

        monkeypatch.setattr(bp_integration, "get_ms_graph_client", lambda: None)
        resp = ms365_client.get(
            "/api/v1/integrations/microsoft365/sites", headers=ms365_headers
        )
        assert resp.status_code in (400, 503)

    def test_sites_with_mock_client(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365_integration as bp_integration

        class MockGraph:
            def is_configured(self):
                return True

            def get_sharepoint_sites(self, search_query=""):
                return [{"id": "site-1", "name": "サイト1"}]

        monkeypatch.setattr(bp_integration, "get_ms_graph_client", lambda: MockGraph())
        resp = ms365_client.get(
            "/api/v1/integrations/microsoft365/sites", headers=ms365_headers
        )
        assert resp.status_code == 200

    def test_sites_requires_auth(self, ms365_client):
        resp = ms365_client.get("/api/v1/integrations/microsoft365/sites")
        assert resp.status_code == 401


class TestMs365SyncConfigsExecute:
    """POST /api/v1/ms365/sync/configs/<id>/execute"""

    def test_execute_config_not_found(self, ms365_client, ms365_headers, monkeypatch):
        import blueprints.ms365 as bp

        mock_dal = _make_dal_mock(get_one=lambda cid: None)
        monkeypatch.setattr(bp, "get_dal", lambda: mock_dal)
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs/9999/execute", headers=ms365_headers
        )
        assert resp.status_code == 404

    def test_execute_requires_auth(self, ms365_client):
        resp = ms365_client.post("/api/v1/ms365/sync/configs/1/execute")
        assert resp.status_code == 401
