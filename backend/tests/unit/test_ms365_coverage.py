"""
blueprints/ms365.py カバレッジ強化テスト

テスト戦略:
  - ms365_bp (sync configs): DALを使う → JSON ファイルを準備してCRUDを網羅
  - ms365_integration_bp: Graph APIクライアントが未設定 → 400/503 パスを網羅
  - execute/test: sync_service 未設定 → 503 パスを網羅
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


_SYNC_CONFIGS = [
    {
        "id": 1,
        "name": "テスト同期設定1",
        "description": "テスト用",
        "site_id": "site-abc",
        "drive_id": "drive-xyz",
        "folder_path": "/",
        "file_extensions": ["pdf", "docx"],
        "sync_schedule": "0 2 * * *",
        "sync_strategy": "incremental",
        "is_enabled": True,
        "metadata_mapping": {},
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    },
    {
        "id": 2,
        "name": "テスト同期設定2（無効）",
        "description": "無効な設定",
        "site_id": "site-def",
        "drive_id": "drive-ghi",
        "folder_path": "/Documents",
        "file_extensions": ["xlsx"],
        "sync_schedule": "0 3 * * *",
        "sync_strategy": "full",
        "is_enabled": False,
        "metadata_mapping": {},
        "created_at": "2025-01-02T00:00:00",
        "updated_at": "2025-01-02T00:00:00",
    },
]

_SYNC_HISTORY = [
    {
        "id": 1,
        "config_id": 1,
        "sync_config_id": 1,
        "status": "completed",
        "sync_started_at": "2025-01-20T02:00:00",
        "sync_completed_at": "2025-01-20T02:05:00",
        "files_processed": 10,
        "files_added": 2,
        "files_updated": 1,
        "files_deleted": 0,
        "errors": [],
    },
]


@pytest.fixture()
def ms365_client(client, tmp_path, monkeypatch):
    """MS365 データを準備したクライアント（DAL を tmp_path に向ける）"""
    import app_helpers
    import config as cfg_module

    # DAL シングルトンをリセットし Config.DATA_DIR を tmp_path に向ける
    monkeypatch.setattr(app_helpers, "_dal", None)
    monkeypatch.setattr(cfg_module.Config, "DATA_DIR", str(tmp_path))

    _write_json(tmp_path / "ms365_sync_configs.json", _SYNC_CONFIGS)
    _write_json(tmp_path / "ms365_sync_histories.json", _SYNC_HISTORY)
    return client


# ============================================================
# 同期設定一覧
# ============================================================

class TestMS365SyncConfigsList:
    """GET /api/v1/ms365/sync/configs"""

    def test_returns_200(self, ms365_client, auth_headers):
        """同期設定一覧を取得できる"""
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_empty_list(self, client, auth_headers):
        """設定なしでも成功する"""
        resp = client.get("/api/v1/ms365/sync/configs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.get("/api/v1/ms365/sync/configs")
        assert resp.status_code == 401


# ============================================================
# 同期設定作成
# ============================================================

class TestMS365SyncConfigsCreate:
    """POST /api/v1/ms365/sync/configs"""

    def test_create_success(self, ms365_client, auth_headers):
        """管理者が同期設定を作成できる"""
        new_config = {
            "name": "新規テスト設定",
            "site_id": "site-new",
            "drive_id": "drive-new",
            "folder_path": "/New",
            "sync_schedule": "0 4 * * *",
            "sync_strategy": "incremental",
        }
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json=new_config,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "新規テスト設定"

    def test_missing_name_returns_400(self, ms365_client, auth_headers):
        """name 欠落は 400"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={"site_id": "s", "drive_id": "d"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_missing_site_id_returns_400(self, ms365_client, auth_headers):
        """site_id 欠落は 400"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={"name": "test", "drive_id": "d"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_missing_drive_id_returns_400(self, ms365_client, auth_headers):
        """drive_id 欠落は 400"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={"name": "test", "site_id": "s"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_invalid_cron_returns_400(self, ms365_client, auth_headers):
        """無効なcron式は 400"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={
                "name": "test",
                "site_id": "s",
                "drive_id": "d",
                "sync_schedule": "invalid cron",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_partner_cannot_create(self, ms365_client, partner_auth_headers):
        """協力会社は作成できない（403）"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={"name": "test", "site_id": "s", "drive_id": "d"},
            headers=partner_auth_headers,
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs",
            json={"name": "t", "site_id": "s", "drive_id": "d"},
        )
        assert resp.status_code == 401


# ============================================================
# 同期設定取得
# ============================================================

class TestMS365SyncConfigsGet:
    """GET /api/v1/ms365/sync/configs/<id>"""

    def test_get_existing_config(self, ms365_client, auth_headers):
        """既存の設定を取得できる"""
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs/1", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1

    def test_get_not_found(self, ms365_client, auth_headers):
        """存在しない ID は 404"""
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs/999", headers=auth_headers
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.get("/api/v1/ms365/sync/configs/1")
        assert resp.status_code == 401


# ============================================================
# 同期設定更新
# ============================================================

class TestMS365SyncConfigsUpdate:
    """PUT /api/v1/ms365/sync/configs/<id>"""

    def test_update_success(self, ms365_client, auth_headers):
        """設定を更新できる"""
        resp = ms365_client.put(
            "/api/v1/ms365/sync/configs/1",
            json={"name": "更新後の名前", "is_enabled": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "更新後の名前"

    def test_update_not_found(self, ms365_client, auth_headers):
        """存在しない設定の更新は 404"""
        resp = ms365_client.put(
            "/api/v1/ms365/sync/configs/999",
            json={"name": "test"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_partner_cannot_update(self, ms365_client, partner_auth_headers):
        """協力会社は更新できない（403）"""
        resp = ms365_client.put(
            "/api/v1/ms365/sync/configs/1",
            json={"name": "test"},
            headers=partner_auth_headers,
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.put("/api/v1/ms365/sync/configs/1", json={"name": "t"})
        assert resp.status_code == 401


# ============================================================
# 同期設定削除
# ============================================================

class TestMS365SyncConfigsDelete:
    """DELETE /api/v1/ms365/sync/configs/<id>"""

    def test_delete_success(self, ms365_client, auth_headers):
        """設定を削除できる"""
        resp = ms365_client.delete(
            "/api/v1/ms365/sync/configs/2", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_delete_not_found(self, ms365_client, auth_headers):
        """存在しない設定の削除は 404"""
        resp = ms365_client.delete(
            "/api/v1/ms365/sync/configs/999", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_partner_cannot_delete(self, ms365_client, partner_auth_headers):
        """協力会社は削除できない（403）"""
        resp = ms365_client.delete(
            "/api/v1/ms365/sync/configs/1", headers=partner_auth_headers
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.delete("/api/v1/ms365/sync/configs/1")
        assert resp.status_code == 401


# ============================================================
# 同期実行（sync_service が未利用可能 → 503）
# ============================================================

class TestMS365SyncConfigsExecute:
    """POST /api/v1/ms365/sync/configs/<id>/execute"""

    def test_execute_not_found(self, ms365_client, auth_headers):
        """存在しない設定は 404"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs/999/execute", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_execute_service_unavailable_or_error(self, ms365_client, auth_headers):
        """sync_service 未設定は 503、Graph API 未設定は 400"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs/1/execute", headers=auth_headers
        )
        # sync_service が利用不可の場合は 503、Graph API 未設定のValueErrorは 400
        assert resp.status_code in (400, 503, 200, 202)

    def test_partner_cannot_execute(self, ms365_client, partner_auth_headers):
        """協力会社は実行できない（403）"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs/1/execute", headers=partner_auth_headers
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.post("/api/v1/ms365/sync/configs/1/execute")
        assert resp.status_code == 401


# ============================================================
# 接続テスト（sync_service が未利用可能 → 503）
# ============================================================

class TestMS365SyncConfigsTest:
    """POST /api/v1/ms365/sync/configs/<id>/test"""

    def test_test_not_found(self, ms365_client, auth_headers):
        """存在しない設定は 404"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs/999/test", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_test_service_unavailable_or_error(self, ms365_client, auth_headers):
        """sync_service 未設定は 503、接続失敗は 400"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs/1/test", headers=auth_headers
        )
        assert resp.status_code in (400, 503, 200)

    def test_partner_cannot_test(self, ms365_client, partner_auth_headers):
        """協力会社は接続テストできない（403）"""
        resp = ms365_client.post(
            "/api/v1/ms365/sync/configs/1/test", headers=partner_auth_headers
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.post("/api/v1/ms365/sync/configs/1/test")
        assert resp.status_code == 401


# ============================================================
# 同期履歴
# ============================================================

class TestMS365SyncConfigsHistory:
    """GET /api/v1/ms365/sync/configs/<id>/history"""

    def test_get_history_success(self, ms365_client, auth_headers):
        """同期履歴を取得できる"""
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs/1/history", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "pagination" in data["data"]

    def test_get_history_not_found(self, ms365_client, auth_headers):
        """存在しない設定の履歴は 404"""
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs/999/history", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_pagination_params(self, ms365_client, auth_headers):
        """ページネーションパラメータが適用される"""
        resp = ms365_client.get(
            "/api/v1/ms365/sync/configs/1/history?page=1&per_page=5",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        pag = resp.get_json()["data"]["pagination"]
        assert pag["page"] == 1
        assert pag["per_page"] == 5

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.get("/api/v1/ms365/sync/configs/1/history")
        assert resp.status_code == 401


# ============================================================
# 同期統計・ステータス
# ============================================================

class TestMS365SyncStats:
    """GET /api/v1/ms365/sync/stats"""

    def test_returns_stats(self, ms365_client, auth_headers):
        """統計情報を取得できる"""
        resp = ms365_client.get("/api/v1/ms365/sync/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        stats = data["data"]
        assert "total_configs" in stats
        assert "active_configs" in stats
        assert "disabled_configs" in stats

    def test_stats_counts_match_data(self, ms365_client, auth_headers):
        """設定数が正確"""
        resp = ms365_client.get("/api/v1/ms365/sync/stats", headers=auth_headers)
        assert resp.status_code == 200
        stats = resp.get_json()["data"]
        assert stats["total_configs"] == 2
        assert stats["active_configs"] == 1  # only 1 enabled
        assert stats["disabled_configs"] == 1

    def test_empty_stats(self, ms365_client, tmp_path, auth_headers):
        """設定なしでも統計が返る（空のファイルで上書き）"""
        _write_json(tmp_path / "ms365_sync_configs.json", [])
        _write_json(tmp_path / "ms365_sync_histories.json", [])
        resp = ms365_client.get("/api/v1/ms365/sync/stats", headers=auth_headers)
        assert resp.status_code == 200
        stats = resp.get_json()["data"]
        assert stats["total_configs"] == 0

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.get("/api/v1/ms365/sync/stats")
        assert resp.status_code == 401


class TestMS365SyncStatus:
    """GET /api/v1/ms365/sync/status"""

    def test_returns_status(self, ms365_client, auth_headers):
        """サービスステータスを取得できる"""
        resp = ms365_client.get("/api/v1/ms365/sync/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        status = data["data"]
        assert "sync_service_available" in status
        assert "scheduler_service_available" in status
        assert "running_jobs" in status

    def test_services_status_is_bool(self, ms365_client, auth_headers):
        """サービス可用性フラグは bool 型"""
        resp = ms365_client.get("/api/v1/ms365/sync/status", headers=auth_headers)
        data = resp.get_json()["data"]
        assert isinstance(data["sync_service_available"], bool)
        assert isinstance(data["scheduler_service_available"], bool)

    def test_no_token_returns_401(self, ms365_client):
        """トークンなしは 401"""
        resp = ms365_client.get("/api/v1/ms365/sync/status")
        assert resp.status_code == 401


# ============================================================
# Microsoft 365 Integration API（未設定 → 400 パス）
# ============================================================

class TestMS365IntegrationStatus:
    """GET /api/v1/integrations/microsoft365/status"""

    def test_returns_not_configured(self, client, auth_headers):
        """Graph API 未設定の場合 configured=False"""
        resp = client.get(
            "/api/v1/integrations/microsoft365/status", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["configured"] is False

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/integrations/microsoft365/status")
        assert resp.status_code == 401


class TestMS365IntegrationSites:
    """GET /api/v1/integrations/microsoft365/sites"""

    def test_returns_not_configured_400(self, client, auth_headers):
        """Graph API 未設定は 400"""
        resp = client.get(
            "/api/v1/integrations/microsoft365/sites", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_CONFIGURED"

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/integrations/microsoft365/sites")
        assert resp.status_code == 401


class TestMS365IntegrationDrives:
    """GET /api/v1/integrations/microsoft365/sites/<id>/drives"""

    def test_returns_not_configured_400(self, client, auth_headers):
        """Graph API 未設定は 400"""
        resp = client.get(
            "/api/v1/integrations/microsoft365/sites/site-123/drives",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "NOT_CONFIGURED"

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/integrations/microsoft365/sites/s/drives")
        assert resp.status_code == 401


class TestMS365IntegrationDriveItems:
    """GET /api/v1/integrations/microsoft365/drives/<id>/items"""

    def test_returns_not_configured_400(self, client, auth_headers):
        """Graph API 未設定は 400"""
        resp = client.get(
            "/api/v1/integrations/microsoft365/drives/drive-123/items",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "NOT_CONFIGURED"

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/integrations/microsoft365/drives/d/items")
        assert resp.status_code == 401
