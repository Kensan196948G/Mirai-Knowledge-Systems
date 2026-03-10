"""dal/ パッケージ分割後のユニットテスト"""

import os
import sys

import pytest
from unittest.mock import patch, MagicMock

# backend ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def test_dal_import():
    """dal パッケージから DataAccessLayer がインポートできる"""
    from dal import DataAccessLayer

    assert DataAccessLayer is not None


def test_data_access_compatibility():
    """data_access.py 互換性ファサードが動作する"""
    from data_access import DataAccessLayer

    assert DataAccessLayer is not None


def test_dal_instance_creation():
    """DataAccessLayer インスタンスが生成できる"""
    from dal import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=False)
    assert dal is not None
    assert not dal.use_postgresql


def test_dal_has_knowledge_methods():
    """知識関連メソッドが存在する"""
    from dal import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=False)
    assert hasattr(dal, "get_knowledge_list")
    assert hasattr(dal, "get_knowledge_by_id")
    assert hasattr(dal, "create_knowledge")
    assert hasattr(dal, "update_knowledge")
    assert hasattr(dal, "delete_knowledge")


def test_dal_has_ms365_methods():
    """MS365関連メソッドが存在する"""
    from dal import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=False)
    assert hasattr(dal, "get_all_ms365_sync_configs")
    assert hasattr(dal, "create_ms365_sync_config")
    assert hasattr(dal, "update_ms365_sync_config")


def test_dal_method_count():
    """公開メソッド数が期待値以上"""
    from dal import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=False)
    methods = [m for m in dir(dal) if not m.startswith("_")]
    assert len(methods) >= 30  # 最低30メソッド


def test_dal_use_postgresql_false_does_not_use_db():
    """use_postgresql=False のとき _use_postgresql() が False を返す"""
    from dal import DataAccessLayer

    dal = DataAccessLayer(use_postgresql=False)
    assert not dal._use_postgresql()


def test_dal_knowledge_get_list_returns_list(tmp_path):
    """JSON モードで get_knowledge_list がリストを返す"""
    import json

    from dal import DataAccessLayer

    knowledge_data = [
        {
            "id": 1,
            "title": "テスト",
            "summary": "サマリー",
            "content": "内容",
            "category": "safety",
        }
    ]
    (tmp_path / "knowledge.json").write_text(
        json.dumps(knowledge_data, ensure_ascii=False), encoding="utf-8"
    )

    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)

    result = dal.get_knowledge_list()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["title"] == "テスト"


def test_dal_knowledge_get_list_with_category_filter(tmp_path):
    """カテゴリフィルタが機能する"""
    import json

    from dal import DataAccessLayer

    knowledge_data = [
        {"id": 1, "title": "A", "category": "safety"},
        {"id": 2, "title": "B", "category": "quality"},
    ]
    (tmp_path / "knowledge.json").write_text(
        json.dumps(knowledge_data, ensure_ascii=False), encoding="utf-8"
    )

    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)

    result = dal.get_knowledge_list(filters={"category": "safety"})
    assert len(result) == 1
    assert result[0]["title"] == "A"


def test_dal_knowledge_get_by_id_existing(tmp_path):
    """存在するIDでナレッジを取得できる"""
    import json

    from dal import DataAccessLayer

    knowledge_data = [{"id": 1, "title": "存在するナレッジ", "category": "safety"}]
    (tmp_path / "knowledge.json").write_text(
        json.dumps(knowledge_data, ensure_ascii=False), encoding="utf-8"
    )

    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)

    result = dal.get_knowledge_by_id(1)
    assert result is not None
    assert result["title"] == "存在するナレッジ"


def test_dal_knowledge_get_by_id_not_found(tmp_path):
    """存在しないIDでは None を返す"""
    import json

    from dal import DataAccessLayer

    knowledge_data = [{"id": 1, "title": "テスト"}]
    (tmp_path / "knowledge.json").write_text(
        json.dumps(knowledge_data, ensure_ascii=False), encoding="utf-8"
    )

    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)

    result = dal.get_knowledge_by_id(9999)
    assert result is None


def test_dal_ms365_get_all_configs_empty(tmp_path):
    """MS365設定が空のとき空リストを返す"""
    import json

    from dal import DataAccessLayer

    (tmp_path / "ms365_sync_configs.json").write_text(
        json.dumps([], ensure_ascii=False), encoding="utf-8"
    )

    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)

    result = dal.get_all_ms365_sync_configs()
    assert result == []


def test_dal_mixin_inheritance():
    """DataAccessLayer が全 Mixin を継承している"""
    from dal import DataAccessLayer
    from dal.knowledge import KnowledgeMixin
    from dal.notifications import NotificationMixin
    from dal.operations import OperationsMixin
    from dal.projects import ProjectsMixin
    from dal.experts import ExpertsMixin
    from dal.logs import LogsMixin
    from dal.ms365 import MS365Mixin

    assert issubclass(DataAccessLayer, KnowledgeMixin)
    assert issubclass(DataAccessLayer, NotificationMixin)
    assert issubclass(DataAccessLayer, OperationsMixin)
    assert issubclass(DataAccessLayer, ProjectsMixin)
    assert issubclass(DataAccessLayer, ExpertsMixin)
    assert issubclass(DataAccessLayer, LogsMixin)
    assert issubclass(DataAccessLayer, MS365Mixin)
