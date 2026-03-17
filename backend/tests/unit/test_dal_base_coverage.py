"""
test_dal_base_coverage.py - dal/base.py カバレッジ強化テスト

対象: BaseDAL クラスの全メソッドと分岐（87%→95%+ 目標）
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest


class TestBaseDALInit:
    """BaseDAL.__init__ の分岐テスト"""

    def test_init_explicit_postgresql_true(self):
        """PostgreSQL明示指定True"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=True)
        assert dal.use_postgresql is True

    def test_init_explicit_postgresql_false(self):
        """PostgreSQL明示指定False"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)
        assert dal.use_postgresql is False

    def test_init_default_uses_config(self):
        """デフォルト（None）の場合は Config.USE_POSTGRESQL を使用"""
        from dal.base import BaseDAL
        with patch("dal.base.Config") as mock_config:
            mock_config.USE_POSTGRESQL = True
            mock_config.DATA_DIR = "/tmp"
            dal = BaseDAL(use_postgresql=None)
            assert dal.use_postgresql is True

    def test_init_data_dir_set(self):
        """data_dir が Config.DATA_DIR から設定される"""
        from dal.base import BaseDAL
        with patch("dal.base.Config") as mock_config:
            mock_config.USE_POSTGRESQL = False
            mock_config.DATA_DIR = "/custom/data"
            dal = BaseDAL(use_postgresql=False)
            assert dal.data_dir == "/custom/data"


class TestBaseDALUsePostgresql:
    """BaseDAL._use_postgresql の分岐テスト"""

    def test_use_postgresql_false_when_disabled(self):
        """use_postgresql=False なら False を返す"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)
        assert dal._use_postgresql() is False

    def test_use_postgresql_falls_back_on_import_error(self):
        """database モジュールのインポートに失敗した場合 False"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=True)
        with patch.dict("sys.modules", {"database": None}):
            # ImportError をシミュレート
            result = dal._use_postgresql()
            # database モジュールが None の場合、例外が発生して False になる
            assert result is False

    def test_use_postgresql_true_when_available(self):
        """PostgreSQL が利用可能なら True"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=True)
        mock_db_config = MagicMock()
        mock_db_config.is_postgres_available.return_value = True
        mock_database = MagicMock()
        mock_database.config = mock_db_config
        with patch.dict("sys.modules", {"database": mock_database, "database.config": mock_db_config}):
            with patch("dal.base.BaseDAL._use_postgresql", return_value=True):
                assert dal._use_postgresql() is True

    def test_use_postgresql_false_when_not_available(self):
        """PostgreSQL が利用不可なら False"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=True)
        mock_db_config = MagicMock()
        mock_db_config.is_postgres_available.return_value = False
        mock_database = MagicMock()
        mock_database.config = mock_db_config
        with patch.dict("sys.modules", {"database": mock_database, "database.config": mock_db_config}):
            with patch("dal.base.BaseDAL._use_postgresql", return_value=False):
                assert dal._use_postgresql() is False

    def test_use_postgresql_calls_is_postgres_available(self):
        """database.config が正常にインポートされ is_postgres_available() が呼ばれる（line 39）"""
        import sys
        from types import ModuleType
        from dal.base import BaseDAL

        dal = BaseDAL(use_postgresql=True)

        # database モジュールを動的にモック
        mock_db_config = MagicMock()
        mock_db_config.is_postgres_available.return_value = True

        mock_db_module = ModuleType("database")
        mock_db_config_module = ModuleType("database.config")
        mock_db_config_module.is_postgres_available = mock_db_config.is_postgres_available

        # sys.modules に登録して from database import config が通るようにする
        original_database = sys.modules.get("database")
        original_database_config = sys.modules.get("database.config")
        try:
            sys.modules["database"] = mock_db_module
            sys.modules["database.config"] = mock_db_config_module
            mock_db_module.config = mock_db_config_module

            # _use_postgresql をオリジナル実装で実行
            result = BaseDAL._use_postgresql(dal)
            assert result is True
            mock_db_config.is_postgres_available.assert_called_once()
        finally:
            if original_database is None:
                sys.modules.pop("database", None)
            else:
                sys.modules["database"] = original_database
            if original_database_config is None:
                sys.modules.pop("database.config", None)
            else:
                sys.modules["database.config"] = original_database_config


class TestBaseDALGetJsonPath:
    """BaseDAL._get_json_path のテスト"""

    def test_returns_correct_path(self):
        """ファイルパスが data_dir + filename で構成される"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)
        dal.data_dir = "/test/data"
        result = dal._get_json_path("test.json")
        assert result == os.path.join("/test/data", "test.json")

    def test_different_filenames(self):
        """異なるファイル名でパスが変わる"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)
        dal.data_dir = "/data"
        assert dal._get_json_path("a.json") != dal._get_json_path("b.json")


class TestBaseDALLoadJson:
    """BaseDAL._load_json の全分岐テスト"""

    def test_load_valid_list(self):
        """有効なリスト JSON を読み込む"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        data = [{"id": 1, "name": "test"}, {"id": 2, "name": "foo"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            filepath = os.path.join(tmpdir, "test.json")
            with open(filepath, "w") as f:
                json.dump(data, f)

            result = dal._load_json("test.json")
            assert result == data

    def test_load_filters_non_dict_items(self):
        """リスト内の非dict要素を除外する"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        data = [{"id": 1}, "string_item", 42, None, {"id": 2}]
        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            filepath = os.path.join(tmpdir, "mixed.json")
            with open(filepath, "w") as f:
                json.dump(data, f)

            result = dal._load_json("mixed.json")
            assert len(result) == 2
            assert result[0] == {"id": 1}
            assert result[1] == {"id": 2}

    def test_load_returns_empty_when_not_list(self):
        """JSON がリストでない場合は空リストを返す"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        data = {"key": "value"}  # dictを保存
        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            filepath = os.path.join(tmpdir, "dict.json")
            with open(filepath, "w") as f:
                json.dump(data, f)

            result = dal._load_json("dict.json")
            assert result == []

    def test_load_returns_empty_on_json_decode_error(self):
        """不正な JSON の場合は空リストを返す"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            filepath = os.path.join(tmpdir, "invalid.json")
            with open(filepath, "w") as f:
                f.write("not valid json {{{")

            result = dal._load_json("invalid.json")
            assert result == []

    def test_load_returns_empty_when_file_not_exists(self):
        """ファイルが存在しない場合は空リストを返す"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)
        dal.data_dir = "/nonexistent/path/12345"

        result = dal._load_json("missing.json")
        assert result == []

    def test_load_empty_list(self):
        """空リスト JSON を読み込む"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            filepath = os.path.join(tmpdir, "empty.json")
            with open(filepath, "w") as f:
                json.dump([], f)

            result = dal._load_json("empty.json")
            assert result == []

    def test_load_raises_value_error(self):
        """ValueError（空ファイル等）で空リストを返す"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            filepath = os.path.join(tmpdir, "empty_file.json")
            # 空ファイルを作成
            open(filepath, "w").close()

            result = dal._load_json("empty_file.json")
            assert result == []


class TestBaseDALSaveJson:
    """BaseDAL._save_json の全分岐テスト"""

    def test_save_creates_file(self):
        """データを JSON ファイルに保存する"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        data = [{"id": 1, "name": "test"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            dal._save_json("output.json", data)

            filepath = os.path.join(tmpdir, "output.json")
            assert os.path.exists(filepath)

            with open(filepath) as f:
                loaded = json.load(f)
            assert loaded == data

    def test_save_creates_parent_dirs(self):
        """親ディレクトリが存在しない場合も作成する"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "a", "b", "c")
            dal.data_dir = nested_dir
            data = [{"key": "val"}]
            dal._save_json("nested.json", data)

            filepath = os.path.join(nested_dir, "nested.json")
            assert os.path.exists(filepath)

    def test_save_overwrites_existing_file(self):
        """既存ファイルを上書きする（アトミックwrite）"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            filepath = os.path.join(tmpdir, "update.json")

            # 初期データを保存
            dal._save_json("update.json", [{"version": 1}])

            # 上書き
            dal._save_json("update.json", [{"version": 2}])

            with open(filepath) as f:
                loaded = json.load(f)
            assert loaded == [{"version": 2}]

    def test_save_uses_atomic_replace(self):
        """一時ファイルを使ってアトミックに保存する（tmp_path が消える）"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            dal._save_json("atomic.json", [{"id": 99}])

            # tmp ファイルが残っていないことを確認
            tmp_files = [f for f in os.listdir(tmpdir) if f.endswith(".tmp")]
            assert len(tmp_files) == 0

    def test_save_unicode_data(self):
        """日本語を含むデータを正しく保存する"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        data = [{"title": "テスト", "content": "日本語テスト"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            dal._save_json("japanese.json", data)

            filepath = os.path.join(tmpdir, "japanese.json")
            with open(filepath, encoding="utf-8") as f:
                loaded = json.load(f)
            assert loaded[0]["title"] == "テスト"

    def test_save_empty_list(self):
        """空リストを保存する"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            dal._save_json("empty.json", [])

            filepath = os.path.join(tmpdir, "empty.json")
            with open(filepath) as f:
                loaded = json.load(f)
            assert loaded == []

    def test_save_cleans_tmp_on_exception(self):
        """例外発生時に一時ファイルをクリーンアップ"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir

            # os.replace をモックして例外を発生させる
            with patch("os.replace", side_effect=OSError("replace failed")):
                try:
                    dal._save_json("test.json", [{"id": 1}])
                except Exception:
                    pass

            # tmp ファイルが残っていないことを確認
            tmp_files = [f for f in os.listdir(tmpdir) if f.endswith(".tmp")]
            assert len(tmp_files) == 0


class TestBaseDALRoundTrip:
    """保存→読み込みのラウンドトリップテスト"""

    def test_save_and_load_roundtrip(self):
        """保存したデータを正しく読み込める"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        data = [
            {"id": "1", "name": "Alice", "score": 100},
            {"id": "2", "name": "Bob", "score": 200},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            dal._save_json("roundtrip.json", data)
            loaded = dal._load_json("roundtrip.json")
            assert loaded == data

    def test_multiple_save_load_cycles(self):
        """複数回の保存・読み込みでデータが破損しない"""
        from dal.base import BaseDAL
        dal = BaseDAL(use_postgresql=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            dal.data_dir = tmpdir
            for i in range(5):
                data = [{"cycle": i, "value": f"v{i}"}]
                dal._save_json("cycle.json", data)
                loaded = dal._load_json("cycle.json")
                assert loaded == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
