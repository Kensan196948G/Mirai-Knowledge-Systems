"""
app_helpers.py 未カバー行の追加カバレッジテスト (v3)

対象セクション:
  1. CacheInvalidator クラス (lines 192-273) — 5つの static method
  2. _flush_access_logs (lines 502-519) — キュー一括書き込み
  3. load_data PostgreSQL パス (lines 590-606) — DAL 透過切り替え
  4. load_data エラーパス (lines 642-650) — PermissionError / UnicodeDecodeError
  5. save_data エラーパス (lines 661-691) — makedirs失敗、書き込みエラー、tmpファイル後始末

テスト方針:
  - unittest.mock.patch / MagicMock で外部依存を差し替え
  - CacheInvalidator は app_helpers.redis_client を直接パッチ
  - _flush_access_logs は app_helpers._access_log_queue を直接操作
  - load_data PostgreSQL は app_helpers.get_dal をパッチ
  - save_data はtempfile.TemporaryDirectory でファイルシステムテスト
"""

import json
import os
import stat
import sys
import tempfile

import pytest

os.environ.setdefault(
    "MKS_JWT_SECRET_KEY",
    "test-only-secret-key-for-pytest-minimum-32-chars",
)
os.environ.setdefault("TESTING", "true")

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)

from unittest.mock import MagicMock, patch

import app_helpers
from app_helpers import (
    CacheInvalidator,
    _flush_access_logs,
    load_data,
    save_data,
)


# ============================================================
# 1. CacheInvalidator テスト
# ============================================================


class TestCacheInvalidatorKnowledge:
    """CacheInvalidator.invalidate_knowledge の正常系・例外系"""

    def test_invalidate_knowledge_no_id(self):
        """knowledge_id=None で全パターン走査"""
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = [b"knowledge_list:page1", b"knowledge_tags"]
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_knowledge()
        assert mock_redis.scan_iter.call_count == 4  # 4 patterns
        # scan_iter returns same 2 keys for each of the 4 patterns = 8 deletes
        assert mock_redis.delete.call_count == 8

    def test_invalidate_knowledge_with_id(self):
        """knowledge_id指定で追加パターン走査"""
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_knowledge(knowledge_id="42")
        # 4 base patterns + 1 for knowledge_related:42:*
        assert mock_redis.scan_iter.call_count == 5

    def test_invalidate_knowledge_with_keys_deleted(self):
        """走査で見つかったキーが全て削除されることを確認"""
        mock_redis = MagicMock()
        keys_map = {
            "knowledge_list:*": [b"knowledge_list:1", b"knowledge_list:2"],
            "knowledge_popular:*": [b"knowledge_popular:all"],
            "knowledge_tags": [],
            "knowledge_recent:*": [],
        }
        mock_redis.scan_iter.side_effect = lambda p: keys_map.get(p, [])
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_knowledge()
        assert mock_redis.delete.call_count == 3

    def test_invalidate_knowledge_exception(self):
        """Redis例外時にwarningログが出力されクラッシュしない"""
        mock_redis = MagicMock()
        mock_redis.scan_iter.side_effect = ConnectionError("Redis down")
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_knowledge()  # should not raise

    def test_invalidate_knowledge_redis_none(self):
        """redis_client=None の場合は即return"""
        with patch.object(app_helpers, "redis_client", None):
            CacheInvalidator.invalidate_knowledge()  # no error


class TestCacheInvalidatorProjects:
    """CacheInvalidator.invalidate_projects"""

    def test_invalidate_projects_no_id(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_projects()
        assert mock_redis.scan_iter.call_count == 1  # projects_list:*

    def test_invalidate_projects_with_id(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_projects(project_id="7")
        # projects_list:*, projects_detail:7, projects_progress:7
        assert mock_redis.scan_iter.call_count == 3

    def test_invalidate_projects_exception(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.side_effect = RuntimeError("fail")
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_projects()

    def test_invalidate_projects_redis_none(self):
        with patch.object(app_helpers, "redis_client", None):
            CacheInvalidator.invalidate_projects()


class TestCacheInvalidatorExperts:
    """CacheInvalidator.invalidate_experts"""

    def test_invalidate_experts_no_id(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_experts()
        # experts_list:*, experts_stats
        assert mock_redis.scan_iter.call_count == 2

    def test_invalidate_experts_with_id(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_experts(expert_id="99")
        # experts_list:*, experts_stats, experts_detail:99
        assert mock_redis.scan_iter.call_count == 3

    def test_invalidate_experts_exception(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.side_effect = Exception("oops")
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_experts()

    def test_invalidate_experts_redis_none(self):
        with patch.object(app_helpers, "redis_client", None):
            CacheInvalidator.invalidate_experts()


class TestCacheInvalidatorRegulations:
    """CacheInvalidator.invalidate_regulations"""

    def test_invalidate_regulations_no_id(self):
        """reg_id=None: patterns は空リストなのでscan_iterは呼ばれない"""
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_regulations()
        assert mock_redis.scan_iter.call_count == 0

    def test_invalidate_regulations_with_id(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = [b"regulations_detail:5"]
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_regulations(reg_id="5")
        assert mock_redis.scan_iter.call_count == 1
        mock_redis.delete.assert_called_once_with(b"regulations_detail:5")

    def test_invalidate_regulations_exception(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.side_effect = TimeoutError("timeout")
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_regulations(reg_id="1")

    def test_invalidate_regulations_redis_none(self):
        with patch.object(app_helpers, "redis_client", None):
            CacheInvalidator.invalidate_regulations()


class TestCacheInvalidatorSop:
    """CacheInvalidator.invalidate_sop"""

    def test_invalidate_sop_no_id(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = [b"sop_list"]
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_sop()
        assert mock_redis.scan_iter.call_count == 1  # sop_list
        mock_redis.delete.assert_called_once()

    def test_invalidate_sop_with_id(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = []
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_sop(sop_id="10")
        # sop_list, sop_related:10:*
        assert mock_redis.scan_iter.call_count == 2

    def test_invalidate_sop_exception(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.side_effect = ValueError("bad")
        with patch.object(app_helpers, "redis_client", mock_redis):
            CacheInvalidator.invalidate_sop()

    def test_invalidate_sop_redis_none(self):
        with patch.object(app_helpers, "redis_client", None):
            CacheInvalidator.invalidate_sop()


# ============================================================
# 2. _flush_access_logs テスト
# ============================================================


class TestFlushAccessLogs:
    """_flush_access_logs() の正常系・空キュー・例外系"""

    def test_flush_empty_queue_returns_immediately(self):
        """キューが空なら何もしない"""
        app_helpers._access_log_queue = []
        with patch.object(app_helpers, "load_data") as mock_load:
            _flush_access_logs()
            mock_load.assert_not_called()

    def test_flush_writes_entries_to_file(self):
        """キューにエントリがある場合、load_data→save_dataが呼ばれる"""
        entries = [
            {"user_id": 1, "action": "login"},
            {"user_id": 2, "action": "view"},
        ]
        app_helpers._access_log_queue = entries[:]
        existing_logs = [{"id": 1, "action": "old"}]

        with patch.object(app_helpers, "load_data", return_value=existing_logs[:]) as mock_load, \
             patch.object(app_helpers, "save_data") as mock_save:
            _flush_access_logs()

            mock_load.assert_called_once_with("access_logs.json")
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][1]
            # existing 1 + 2 new entries = 3
            assert len(saved_data) == 3
            # IDs should be sequential: existing has 1, new get 2 and 3
            assert saved_data[1]["id"] == 2
            assert saved_data[2]["id"] == 3

        # Queue should be cleared after flush
        assert app_helpers._access_log_queue == []

    def test_flush_clears_queue_before_write(self):
        """フラッシュ後にキューが空であることを確認"""
        app_helpers._access_log_queue = [{"user_id": 1, "action": "test"}]
        with patch.object(app_helpers, "load_data", return_value=[]), \
             patch.object(app_helpers, "save_data"):
            _flush_access_logs()
        assert app_helpers._access_log_queue == []

    def test_flush_exception_does_not_crash(self):
        """save_data例外時にクラッシュしない"""
        app_helpers._access_log_queue = [{"user_id": 1, "action": "test"}]
        with patch.object(app_helpers, "load_data", side_effect=IOError("disk full")):
            _flush_access_logs()  # should not raise

    def test_flush_exception_from_save_data(self):
        """save_data がExceptionを投げた場合"""
        app_helpers._access_log_queue = [{"user_id": 1, "action": "test"}]
        with patch.object(app_helpers, "load_data", return_value=[]), \
             patch.object(app_helpers, "save_data", side_effect=PermissionError("denied")):
            _flush_access_logs()  # should not raise


# ============================================================
# 3. load_data PostgreSQL パス テスト
# ============================================================


class TestLoadDataPostgreSQL:
    """load_data() の PostgreSQL 透過切り替えパス"""

    def _make_pg_dal(self, **method_returns):
        """use_postgresql=True の DAL モックを作成"""
        mock_dal = MagicMock()
        mock_dal.use_postgresql = True
        for method_name, return_value in method_returns.items():
            getattr(mock_dal, method_name).return_value = return_value
        return mock_dal

    def test_load_knowledge_from_postgresql(self):
        data = [{"id": 1, "title": "test"}]
        mock_dal = self._make_pg_dal(get_knowledge_list=data)
        with patch.object(app_helpers, "get_dal", return_value=mock_dal):
            result = load_data("knowledge.json")
        assert result == data
        mock_dal.get_knowledge_list.assert_called_once()

    def test_load_sop_from_postgresql(self):
        data = [{"id": 1, "name": "SOP-1"}]
        mock_dal = self._make_pg_dal(get_sop_list=data)
        with patch.object(app_helpers, "get_dal", return_value=mock_dal):
            result = load_data("sop.json")
        assert result == data

    def test_load_incidents_from_postgresql(self):
        data = [{"id": 1, "type": "incident"}]
        mock_dal = self._make_pg_dal(get_incidents_list=data)
        with patch.object(app_helpers, "get_dal", return_value=mock_dal):
            result = load_data("incidents.json")
        assert result == data

    def test_load_approvals_from_postgresql(self):
        data = [{"id": 1, "status": "pending"}]
        mock_dal = self._make_pg_dal(get_approvals_list=data)
        with patch.object(app_helpers, "get_dal", return_value=mock_dal):
            result = load_data("approvals.json")
        assert result == data

    def test_load_notifications_from_postgresql(self):
        data = [{"id": 1, "title": "notify"}]
        mock_dal = self._make_pg_dal(get_notifications=data)
        with patch.object(app_helpers, "get_dal", return_value=mock_dal):
            result = load_data("notifications.json")
        assert result == data

    def test_load_access_logs_from_postgresql(self):
        data = [{"id": 1, "action": "login"}]
        mock_dal = self._make_pg_dal(get_access_logs=data)
        with patch.object(app_helpers, "get_dal", return_value=mock_dal):
            result = load_data("access_logs.json")
        assert result == data

    def test_postgresql_exception_falls_back_to_json(self):
        """PostgreSQL例外時にJSON fallback"""
        mock_dal = MagicMock()
        mock_dal.use_postgresql = True
        mock_dal.get_knowledge_list.side_effect = RuntimeError("DB connection lost")

        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                # Write a valid JSON file for fallback
                filepath = os.path.join(tmpdir, "knowledge.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump([{"id": 1, "title": "fallback"}], f)

                result = load_data("knowledge.json")
                assert len(result) == 1
                assert result[0]["title"] == "fallback"

    def test_postgresql_unknown_filename_falls_through(self):
        """PostgreSQLモードでも未知のファイル名はJSON読み込みへ"""
        mock_dal = MagicMock()
        mock_dal.use_postgresql = True

        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "custom.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump([{"id": 99}], f)

                result = load_data("custom.json")
                assert len(result) == 1
                assert result[0]["id"] == 99


# ============================================================
# 4. load_data エラーパス テスト
# ============================================================


class TestLoadDataErrorPaths:
    """load_data() の PermissionError / UnicodeDecodeError パス"""

    def _make_json_dal(self):
        """use_postgresql=False の DAL モック"""
        mock_dal = MagicMock()
        mock_dal.use_postgresql = False
        return mock_dal

    def test_permission_error_returns_empty_list(self):
        """PermissionError 時に空リストを返す"""
        mock_dal = self._make_json_dal()

        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "test.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump([{"id": 1}], f)

                # Make file unreadable
                original_mode = os.stat(filepath).st_mode
                os.chmod(filepath, 0o000)
                try:
                    result = load_data("test.json")
                    assert result == []
                finally:
                    os.chmod(filepath, original_mode)

    def test_unicode_decode_error_returns_empty_list(self):
        """UnicodeDecodeError 時に空リストを返す"""
        mock_dal = self._make_json_dal()

        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "bad_encoding.json")
                # Write binary data that cannot be decoded as UTF-8
                with open(filepath, "wb") as f:
                    f.write(b'\xff\xfe' + b'\x00' * 100)

                result = load_data("bad_encoding.json")
                assert result == []

    def test_permission_error_via_mock(self):
        """open()をモックしてPermissionErrorを発生させる"""
        mock_dal = self._make_json_dal()

        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "perm.json")
                with open(filepath, "w") as f:
                    f.write("[]")

                with patch("builtins.open", side_effect=PermissionError("no access")):
                    result = load_data("perm.json")
                    assert result == []

    def test_unicode_decode_error_via_mock(self):
        """open()をモックしてUnicodeDecodeErrorを発生させる"""
        mock_dal = self._make_json_dal()

        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "unic.json")
                with open(filepath, "w") as f:
                    f.write("[]")

                with patch(
                    "builtins.open",
                    side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
                ):
                    result = load_data("unic.json")
                    assert result == []


# ============================================================
# 5. save_data エラーパス テスト
# ============================================================


class TestSaveDataErrorPaths:
    """save_data() のエラーハンドリングパス"""

    def test_makedirs_failure_raises(self):
        """os.makedirs 失敗時にExceptionがre-raiseされる"""
        with patch.object(app_helpers, "get_data_dir", return_value="/nonexistent/deep/path"), \
             patch("os.makedirs", side_effect=OSError("cannot create dir")):
            with pytest.raises(OSError, match="cannot create dir"):
                save_data("test.json", [{"id": 1}])

    def test_permission_error_on_write_raises(self):
        """書き込み時のPermissionError がre-raiseされる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(app_helpers, "get_data_dir", return_value=tmpdir), \
                 patch("tempfile.mkstemp", side_effect=PermissionError("no write")):
                with pytest.raises(PermissionError, match="no write"):
                    save_data("test.json", [])

    def test_os_error_on_write_raises(self):
        """書き込み時のOSError がre-raiseされる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(app_helpers, "get_data_dir", return_value=tmpdir), \
                 patch("tempfile.mkstemp", side_effect=OSError("disk error")):
                with pytest.raises(OSError, match="disk error"):
                    save_data("test.json", [])

    def test_unexpected_exception_on_write_raises(self):
        """書き込み時の予期しないException がre-raiseされる"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(app_helpers, "get_data_dir", return_value=tmpdir), \
                 patch("tempfile.mkstemp", side_effect=TypeError("unexpected")):
                with pytest.raises(TypeError, match="unexpected"):
                    save_data("test.json", [])

    def test_tmp_file_cleanup_on_replace_failure(self):
        """os.replace失敗時にtmpファイルが後始末される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(app_helpers, "get_data_dir", return_value=tmpdir):
                # We need to let mkstemp succeed but os.replace fail
                real_mkstemp = tempfile.mkstemp

                def fake_mkstemp(**kwargs):
                    fd, path = real_mkstemp(**kwargs)
                    return fd, path

                with patch("os.replace", side_effect=OSError("replace failed")):
                    with pytest.raises(OSError, match="replace failed"):
                        save_data("test.json", [{"id": 1}])

                # Verify no stale temp files remain
                remaining = [f for f in os.listdir(tmpdir) if f.startswith(".test.json.")]
                assert remaining == []

    def test_tmp_file_cleanup_failure_does_not_crash(self):
        """tmpファイル削除失敗時にもクラッシュしない（finallyブロック）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(app_helpers, "get_data_dir", return_value=tmpdir):
                original_replace = os.replace
                original_remove = os.remove

                call_log = {"replace_called": False, "remove_called": False}

                def mock_replace(src, dst):
                    call_log["replace_called"] = True
                    raise OSError("replace failed")

                def mock_remove(path):
                    call_log["remove_called"] = True
                    raise OSError("remove also failed")

                with patch("os.replace", side_effect=mock_replace), \
                     patch("os.remove", side_effect=mock_remove):
                    with pytest.raises(OSError, match="replace failed"):
                        save_data("cleanup_test.json", [{"data": "test"}])

    def test_save_data_normal_write_succeeds(self):
        """正常書き込みが成功することを確認（回帰テスト）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(app_helpers, "get_data_dir", return_value=tmpdir):
                test_data = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]
                save_data("normal.json", test_data)

                filepath = os.path.join(tmpdir, "normal.json")
                assert os.path.exists(filepath)
                with open(filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                assert loaded == test_data

    def test_save_data_creates_subdirectory(self):
        """データディレクトリが存在しない場合に自動作成される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "subdir")
            with patch.object(app_helpers, "get_data_dir", return_value=subdir):
                save_data("sub.json", [{"id": 1}])
                filepath = os.path.join(subdir, "sub.json")
                assert os.path.exists(filepath)


# ============================================================
# 6. load_data 追加エラーパス（JSONDecodeError, 非リスト, 非dictアイテム）
# ============================================================


class TestLoadDataAdditionalPaths:
    """load_data() の追加カバレッジ（JSON不正、非リスト、非dictフィルタ）"""

    def _make_json_dal(self):
        mock_dal = MagicMock()
        mock_dal.use_postgresql = False
        return mock_dal

    def test_json_decode_error_returns_empty(self):
        """不正なJSON時に空リストを返す"""
        mock_dal = self._make_json_dal()
        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "bad.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("{not valid json")
                result = load_data("bad.json")
                assert result == []

    def test_non_list_data_returns_empty(self):
        """JSONがリストでない場合に空リストを返す"""
        mock_dal = self._make_json_dal()
        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "dict.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump({"key": "value"}, f)
                result = load_data("dict.json")
                assert result == []

    def test_non_dict_items_filtered(self):
        """リスト内の非dictアイテムがフィルタされる"""
        mock_dal = self._make_json_dal()
        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "mixed.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump([{"id": 1}, "string", 42, {"id": 2}], f)
                result = load_data("mixed.json")
                assert len(result) == 2
                assert result[0]["id"] == 1
                assert result[1]["id"] == 2

    def test_file_not_found_returns_empty(self):
        """ファイルが存在しない場合に空リストを返す"""
        mock_dal = self._make_json_dal()
        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                result = load_data("nonexistent.json")
                assert result == []

    def test_generic_exception_returns_empty(self):
        """予期しないException時に空リストを返す"""
        mock_dal = self._make_json_dal()
        with patch.object(app_helpers, "get_dal", return_value=mock_dal), \
             patch.object(app_helpers, "get_data_dir") as mock_dir:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_dir.return_value = tmpdir
                filepath = os.path.join(tmpdir, "err.json")
                with open(filepath, "w") as f:
                    f.write("[]")
                # Patch open to raise a generic exception after os.path.exists passes
                with patch("builtins.open", side_effect=RuntimeError("unexpected")):
                    result = load_data("err.json")
                    assert result == []
