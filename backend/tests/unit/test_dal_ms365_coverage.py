"""
dal/ms365.py カバレッジ向上テスト

MS365Mixin の JSON パスを中心に CRUD + エッジケースをテスト。
"""

import json
import os
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)

from dal import DataAccessLayer


# ============================================================
# ヘルパー
# ============================================================


def make_dal(tmp_path):
    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)
    return dal


def write_json(tmp_path, filename, data):
    (tmp_path / filename).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


SAMPLE_CONFIGS = [
    {
        "id": 1,
        "name": "設計図書同期",
        "description": "SharePointの設計図書フォルダを同期",
        "site_id": "site-001",
        "drive_id": "drive-001",
        "folder_path": "/設計図書",
        "file_extensions": [".pdf", ".dwg"],
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
        "description": "仕様書フォルダの同期",
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
        "created_by_id": 2,
        "updated_by_id": None,
    },
]

SAMPLE_HISTORIES = [
    {
        "id": 1,
        "config_id": 1,
        "sync_started_at": "2024-03-01T02:00:00",
        "sync_completed_at": "2024-03-01T02:05:00",
        "status": "success",
        "files_processed": 10,
        "files_created": 5,
        "files_updated": 3,
        "files_skipped": 2,
        "files_failed": 0,
        "error_message": None,
        "error_details": None,
        "execution_time_seconds": 300,
        "triggered_by": "scheduler",
        "triggered_by_user_id": None,
        "created_at": "2024-03-01T02:00:00",
    },
    {
        "id": 2,
        "config_id": 1,
        "sync_started_at": "2024-03-02T02:00:00",
        "sync_completed_at": "2024-03-02T02:03:00",
        "status": "success",
        "files_processed": 3,
        "files_created": 1,
        "files_updated": 2,
        "files_skipped": 0,
        "files_failed": 0,
        "error_message": None,
        "error_details": None,
        "execution_time_seconds": 180,
        "triggered_by": "manual",
        "triggered_by_user_id": 1,
        "created_at": "2024-03-02T02:00:00",
    },
    {
        "id": 3,
        "config_id": 2,
        "sync_started_at": "2024-03-01T03:00:00",
        "sync_completed_at": None,
        "status": "failed",
        "files_processed": 0,
        "files_created": 0,
        "files_updated": 0,
        "files_skipped": 0,
        "files_failed": 1,
        "error_message": "接続エラー",
        "error_details": {"code": 401},
        "execution_time_seconds": None,
        "triggered_by": "scheduler",
        "triggered_by_user_id": None,
        "created_at": "2024-03-01T03:00:00",
    },
]

SAMPLE_MAPPINGS = [
    {
        "id": 1,
        "config_id": 1,
        "sharepoint_file_id": "sp-file-001",
        "sharepoint_file_name": "設計図A.pdf",
        "sharepoint_file_path": "/設計図書/設計図A.pdf",
        "sharepoint_modified_at": "2024-02-01T10:00:00",
        "sharepoint_size_bytes": 1024000,
        "knowledge_id": 10,
        "sync_status": "synced",
        "last_synced_at": "2024-03-01T02:04:00",
        "checksum": "abc123",
        "file_metadata": {},
        "error_message": None,
        "created_at": "2024-03-01T02:00:00",
        "updated_at": "2024-03-01T02:04:00",
    },
    {
        "id": 2,
        "config_id": 1,
        "sharepoint_file_id": "sp-file-002",
        "sharepoint_file_name": "仕様書B.docx",
        "sharepoint_file_path": "/設計図書/仕様書B.docx",
        "sharepoint_modified_at": "2024-02-15T10:00:00",
        "sharepoint_size_bytes": 204800,
        "knowledge_id": 11,
        "sync_status": "pending",
        "last_synced_at": None,
        "checksum": None,
        "file_metadata": {},
        "error_message": None,
        "created_at": "2024-03-01T02:00:00",
        "updated_at": "2024-03-01T02:00:00",
    },
    {
        "id": 3,
        "config_id": 2,
        "sharepoint_file_id": "sp-file-003",
        "sharepoint_file_name": "仕様書C.docx",
        "sharepoint_file_path": "/仕様書/仕様書C.docx",
        "sharepoint_modified_at": "2024-02-20T10:00:00",
        "sharepoint_size_bytes": 102400,
        "knowledge_id": None,
        "sync_status": "failed",
        "last_synced_at": None,
        "checksum": None,
        "file_metadata": {},
        "error_message": "変換エラー",
        "created_at": "2024-03-01T03:00:00",
        "updated_at": "2024-03-01T03:00:00",
    },
]


# ============================================================
# MS365 同期設定 テスト
# ============================================================


class TestGetAllMs365SyncConfigs:
    def test_returns_all_configs(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.get_all_ms365_sync_configs()
        assert len(result) == 2

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_all_ms365_sync_configs()
        assert result == []

    def test_returns_empty_list_when_empty_file(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_all_ms365_sync_configs()
        assert result == []


class TestGetMs365SyncConfig:
    def test_returns_config_by_id(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_config(1)
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "設計図書同期"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_config(999)
        assert result is None

    def test_returns_none_on_empty(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_config(1)
        assert result is None


class TestCreateMs365SyncConfig:
    def test_creates_config(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", [])
        dal = make_dal(tmp_path)
        new_config = {
            "name": "新設定",
            "site_id": "site-new",
            "drive_id": "drive-new",
        }
        result = dal.create_ms365_sync_config(new_config)
        assert result["id"] == 1
        assert result["name"] == "新設定"

    def test_auto_increments_id(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.create_ms365_sync_config({"name": "追加設定"})
        assert result["id"] == 3

    def test_persists_to_file(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", [])
        dal = make_dal(tmp_path)
        dal.create_ms365_sync_config({"name": "テスト設定"})
        saved = json.loads((tmp_path / "ms365_sync_configs.json").read_text())
        assert len(saved) == 1
        assert saved[0]["name"] == "テスト設定"

    def test_adds_created_at(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_ms365_sync_config({"name": "設定"})
        assert "created_at" in result


class TestUpdateMs365SyncConfig:
    def test_updates_config(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_sync_config(1, {"name": "更新設定名"})
        assert result is not None
        assert result["name"] == "更新設定名"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_sync_config(999, {"name": "更新"})
        assert result is None

    def test_persists_changes(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        dal.update_ms365_sync_config(2, {"is_enabled": True})
        saved = json.loads((tmp_path / "ms365_sync_configs.json").read_text())
        updated = next(c for c in saved if c["id"] == 2)
        assert updated["is_enabled"] is True

    def test_adds_updated_at(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_sync_config(1, {"name": "更新"})
        assert "updated_at" in result


class TestDeleteMs365SyncConfig:
    def test_deletes_config(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.delete_ms365_sync_config(1)
        assert result is True

    def test_removes_from_file(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        dal.delete_ms365_sync_config(1)
        saved = json.loads((tmp_path / "ms365_sync_configs.json").read_text())
        ids = [c["id"] for c in saved]
        assert 1 not in ids

    def test_returns_false_when_not_found(self, tmp_path):
        write_json(tmp_path, "ms365_sync_configs.json", SAMPLE_CONFIGS)
        dal = make_dal(tmp_path)
        result = dal.delete_ms365_sync_config(999)
        assert result is False


# ============================================================
# MS365 同期履歴 テスト
# ============================================================


class TestCreateMs365SyncHistory:
    def test_creates_history(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", [])
        dal = make_dal(tmp_path)
        new_history = {
            "config_id": 1,
            "status": "in_progress",
            "triggered_by": "manual",
        }
        result = dal.create_ms365_sync_history(new_history)
        assert result["id"] == 1
        assert result["config_id"] == 1

    def test_auto_increments_id(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.create_ms365_sync_history({"config_id": 1, "status": "running"})
        assert result["id"] == 4

    def test_adds_created_at(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_ms365_sync_history({"config_id": 1})
        assert "created_at" in result

    def test_persists_to_file(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", [])
        dal = make_dal(tmp_path)
        dal.create_ms365_sync_history({"config_id": 1, "status": "success"})
        saved = json.loads((tmp_path / "ms365_sync_histories.json").read_text())
        assert len(saved) == 1


class TestUpdateMs365SyncHistory:
    def test_updates_history(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_sync_history(1, {"status": "completed"})
        assert result is not None
        assert result["status"] == "completed"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_sync_history(999, {"status": "completed"})
        assert result is None

    def test_persists_changes(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        dal.update_ms365_sync_history(3, {"status": "completed", "files_processed": 5})
        saved = json.loads((tmp_path / "ms365_sync_histories.json").read_text())
        updated = next(h for h in saved if h["id"] == 3)
        assert updated["status"] == "completed"


class TestGetMs365SyncHistoriesByConfig:
    def test_returns_histories_for_config(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_histories_by_config(1)
        assert len(result) == 2
        for h in result:
            assert h["config_id"] == 1

    def test_returns_empty_for_unknown_config(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_histories_by_config(999)
        assert result == []

    def test_respects_limit(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_histories_by_config(1, limit=1)
        assert len(result) == 1

    def test_sorted_by_sync_started_at_desc(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_histories_by_config(1)
        dates = [h["sync_started_at"] for h in result]
        assert dates == sorted(dates, reverse=True)

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_ms365_sync_histories_by_config(1)
        assert result == []


class TestGetRecentMs365SyncHistories:
    def test_returns_recent_for_multiple_configs(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_recent_ms365_sync_histories([1, 2])
        assert isinstance(result, list)
        assert len(result) > 0

    def test_returns_empty_for_empty_config_ids(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_recent_ms365_sync_histories([])
        assert result == []

    def test_respects_limit_per_config(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_recent_ms365_sync_histories([1], limit_per_config=1)
        config1_results = [h for h in result if h["config_id"] == 1]
        assert len(config1_results) == 1

    def test_filters_to_matching_config_ids(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_recent_ms365_sync_histories([1])
        for h in result:
            assert h["config_id"] == 1

    def test_handles_unknown_config_ids(self, tmp_path):
        write_json(tmp_path, "ms365_sync_histories.json", SAMPLE_HISTORIES)
        dal = make_dal(tmp_path)
        result = dal.get_recent_ms365_sync_histories([999])
        assert result == []


# ============================================================
# MS365 ファイルマッピング テスト
# ============================================================


class TestGetMs365FileMappingsByConfig:
    def test_returns_mappings_for_config(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_file_mappings_by_config(1)
        assert len(result) == 2
        for m in result:
            assert m["config_id"] == 1

    def test_returns_empty_for_unknown_config(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_file_mappings_by_config(999)
        assert result == []

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_ms365_file_mappings_by_config(1)
        assert result == []


class TestGetMs365FileMappingBySpId:
    def test_returns_mapping(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_file_mapping_by_sp_id("sp-file-001")
        assert result is not None
        assert result["sharepoint_file_id"] == "sp-file-001"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.get_ms365_file_mapping_by_sp_id("non-existent")
        assert result is None

    def test_returns_none_on_empty(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_ms365_file_mapping_by_sp_id("sp-file-001")
        assert result is None


class TestCreateMs365FileMapping:
    def test_creates_mapping(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", [])
        dal = make_dal(tmp_path)
        new_mapping = {
            "config_id": 1,
            "sharepoint_file_id": "sp-new",
            "sharepoint_file_name": "新ファイル.pdf",
        }
        result = dal.create_ms365_file_mapping(new_mapping)
        assert result["id"] == 1
        assert result["sharepoint_file_id"] == "sp-new"

    def test_auto_increments_id(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.create_ms365_file_mapping(
            {"config_id": 1, "sharepoint_file_id": "sp-new"}
        )
        assert result["id"] == 4

    def test_adds_created_at(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_ms365_file_mapping({"config_id": 1})
        assert "created_at" in result

    def test_persists_to_file(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", [])
        dal = make_dal(tmp_path)
        dal.create_ms365_file_mapping(
            {"config_id": 1, "sharepoint_file_id": "sp-001"}
        )
        saved = json.loads((tmp_path / "ms365_file_mappings.json").read_text())
        assert len(saved) == 1


class TestUpdateMs365FileMapping:
    def test_updates_mapping(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_file_mapping(1, {"sync_status": "updated"})
        assert result is not None
        assert result["sync_status"] == "updated"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_file_mapping(999, {"sync_status": "updated"})
        assert result is None

    def test_persists_changes(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        dal.update_ms365_file_mapping(2, {"sync_status": "synced", "checksum": "xyz"})
        saved = json.loads((tmp_path / "ms365_file_mappings.json").read_text())
        updated = next(m for m in saved if m["id"] == 2)
        assert updated["sync_status"] == "synced"

    def test_adds_updated_at(self, tmp_path):
        write_json(tmp_path, "ms365_file_mappings.json", SAMPLE_MAPPINGS)
        dal = make_dal(tmp_path)
        result = dal.update_ms365_file_mapping(1, {"sync_status": "done"})
        assert "updated_at" in result


# ============================================================
# PostgreSQL パス テスト (モック使用)
# ============================================================


def _fluent_mock_session(terminal="all", return_value=None):
    """SQLAlchemy fluent chain をシミュレートするモックセッション"""
    from unittest.mock import MagicMock

    session = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.subquery.return_value = q
    q.join.return_value = q
    q.all.return_value = return_value if return_value is not None else []
    q.first.return_value = return_value
    session.query.return_value = q
    return session


class TestGetAllMs365SyncConfigsPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.get_all_ms365_sync_configs()
        assert result == []

    def test_returns_configs_from_db(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.name = "設定1"
        mock_config.description = None
        mock_config.site_id = "site-001"
        mock_config.drive_id = "drive-001"
        mock_config.folder_path = "/path"
        mock_config.file_extensions = [".pdf"]
        mock_config.sync_schedule = "0 2 * * *"
        mock_config.is_enabled = True
        mock_config.last_sync_at = None
        mock_config.next_sync_at = None
        mock_config.sync_strategy = "incremental"
        mock_config.metadata_mapping = {}
        mock_config.created_at = None
        mock_config.updated_at = None
        mock_config.created_by_id = 1
        mock_config.updated_by_id = None
        mock_session = _fluent_mock_session(return_value=[mock_config])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            result = dal.get_all_ms365_sync_configs()
        assert len(result) == 1


class TestGetMs365SyncConfigPostgresql:
    def test_no_factory_returns_none(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.get_ms365_sync_config(1)
        assert result is None

    def test_returns_none_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_mock_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            result = dal.get_ms365_sync_config(999)
        assert result is None


class TestCreateMs365SyncConfigPostgresql:
    def test_raises_when_no_factory(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            with pytest.raises(Exception):
                dal.create_ms365_sync_config({"name": "設定"})

    def test_creates_config_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.name = "新設定"
        mock_config.description = None
        mock_config.site_id = "s"
        mock_config.drive_id = "d"
        mock_config.folder_path = "/"
        mock_config.file_extensions = []
        mock_config.sync_schedule = None
        mock_config.is_enabled = True
        mock_config.last_sync_at = None
        mock_config.next_sync_at = None
        mock_config.sync_strategy = None
        mock_config.metadata_mapping = {}
        mock_config.created_at = None
        mock_config.updated_at = None
        mock_config.created_by_id = None
        mock_config.updated_by_id = None
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            with patch("dal.ms365.MS365SyncConfig", return_value=mock_config):
                result = dal.create_ms365_sync_config({"name": "新設定"})
        assert result is not None


class TestUpdateMs365SyncConfigPostgresql:
    def test_no_factory_returns_none(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.update_ms365_sync_config(1, {"name": "更新"})
        assert result is None

    def test_returns_none_when_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_mock_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            result = dal.update_ms365_sync_config(999, {"name": "更新"})
        assert result is None


class TestDeleteMs365SyncConfigPostgresql:
    def test_no_factory_returns_false(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.delete_ms365_sync_config(1)
        assert result is False

    def test_returns_false_when_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_mock_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            result = dal.delete_ms365_sync_config(999)
        assert result is False


class TestCreateMs365SyncHistoryPostgresql:
    def test_raises_when_no_factory(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            with pytest.raises(Exception):
                dal.create_ms365_sync_history({"config_id": 1})

    def test_creates_history_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_h = MagicMock()
        mock_h.id = 1
        mock_h.config_id = 1
        mock_h.sync_started_at = None
        mock_h.sync_completed_at = None
        mock_h.status = "in_progress"
        mock_h.files_processed = 0
        mock_h.files_created = 0
        mock_h.files_updated = 0
        mock_h.files_skipped = 0
        mock_h.files_failed = 0
        mock_h.error_message = None
        mock_h.error_details = None
        mock_h.execution_time_seconds = None
        mock_h.triggered_by = "manual"
        mock_h.triggered_by_user_id = None
        mock_h.created_at = None
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            with patch("dal.ms365.MS365SyncHistory", return_value=mock_h):
                result = dal.create_ms365_sync_history({"config_id": 1})
        assert result is not None


class TestUpdateMs365SyncHistoryPostgresql:
    def test_no_factory_returns_none(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.update_ms365_sync_history(1, {"status": "done"})
        assert result is None

    def test_returns_none_when_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_mock_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            result = dal.update_ms365_sync_history(999, {"status": "done"})
        assert result is None


class TestGetMs365SyncHistoriesByConfigPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.get_ms365_sync_histories_by_config(1)
        assert result == []

    def test_returns_histories_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_h = MagicMock()
        mock_h.id = 1
        mock_h.config_id = 1
        mock_h.sync_started_at = None
        mock_h.sync_completed_at = None
        mock_h.status = "success"
        mock_h.files_processed = 5
        mock_h.files_created = 2
        mock_h.files_updated = 3
        mock_h.files_skipped = 0
        mock_h.files_failed = 0
        mock_h.error_message = None
        mock_h.error_details = None
        mock_h.execution_time_seconds = 120
        mock_h.triggered_by = "scheduler"
        mock_h.triggered_by_user_id = None
        mock_h.created_at = None
        mock_session = _fluent_mock_session(return_value=[mock_h])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            result = dal.get_ms365_sync_histories_by_config(1)
        assert len(result) == 1


class TestGetRecentMs365SyncHistoriesPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.get_recent_ms365_sync_histories([1, 2])
        assert result == []

    def test_empty_config_ids_returns_empty(self):
        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        result = dal.get_recent_ms365_sync_histories([])
        assert result == []


class TestGetMs365FileMappingsByConfigPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.get_ms365_file_mappings_by_config(1)
        assert result == []


class TestGetMs365FileMappingBySpIdPostgresql:
    def test_no_factory_returns_none(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.get_ms365_file_mapping_by_sp_id("sp-001")
        assert result is None


class TestCreateMs365FileMappingPostgresql:
    def test_raises_when_no_factory(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            with pytest.raises(Exception):
                dal.create_ms365_file_mapping({"config_id": 1})


class TestUpdateMs365FileMappingPostgresql:
    def test_no_factory_returns_none(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=None):
            result = dal.update_ms365_file_mapping(1, {"sync_status": "done"})
        assert result is None

    def test_returns_none_when_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_mock_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.ms365.get_session_factory", return_value=mock_factory):
            result = dal.update_ms365_file_mapping(999, {"sync_status": "done"})
        assert result is None
