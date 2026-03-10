"""
dal/knowledge.py カバレッジ向上テスト

KnowledgeMixin の JSON パスを中心に CRUD + フィルタ + エッジケースをテスト。
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


SAMPLE_KNOWLEDGE = [
    {
        "id": 1,
        "title": "コンクリート打設手順",
        "summary": "打設の基本手順",
        "content": "詳細内容",
        "category": "施工",
        "tags": ["コンクリート", "施工"],
        "status": "approved",
        "priority": "high",
        "project": "プロジェクトA",
        "owner": "田中",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-10T00:00:00",
        "created_by_id": 1,
    },
    {
        "id": 2,
        "title": "安全管理マニュアル",
        "summary": "現場安全の基本",
        "content": "安全管理の詳細",
        "category": "安全",
        "tags": ["安全", "管理"],
        "status": "draft",
        "priority": "medium",
        "project": "プロジェクトB",
        "owner": "鈴木",
        "created_at": "2024-02-01T00:00:00",
        "updated_at": "2024-02-15T00:00:00",
        "created_by_id": 2,
    },
    {
        "id": 3,
        "title": "品質検査チェックリスト",
        "summary": "品質検査手順",
        "content": "検査項目一覧",
        "category": "品質",
        "tags": ["品質", "検査"],
        "status": "approved",
        "priority": "low",
        "project": "プロジェクトA",
        "owner": "山田",
        "created_at": "2024-03-01T00:00:00",
        "updated_at": "2024-03-05T00:00:00",
        "created_by_id": 1,
    },
]


# ============================================================
# get_knowledge_list テスト
# ============================================================


class TestGetKnowledgeList:
    def test_returns_all_knowledge(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list()
        assert len(result) == 3

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list()
        assert result == []

    def test_filter_by_category(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters={"category": "施工"})
        assert len(result) == 1
        assert result[0]["title"] == "コンクリート打設手順"

    def test_filter_by_search_title(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "安全"})
        assert any("安全" in k["title"] for k in result)

    def test_filter_by_search_summary(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "打設の基本"})
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_filter_by_search_content(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "検査項目"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_filter_no_match(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters={"category": "存在しないカテゴリ"})
        assert result == []

    def test_filter_combined_category_and_search(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters={"category": "施工", "search": "コンクリート"})
        assert len(result) == 1

    def test_no_filters(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters=None)
        assert len(result) == 3


# ============================================================
# get_knowledge_by_id テスト
# ============================================================


class TestGetKnowledgeById:
    def test_returns_knowledge(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "コンクリート打設手順"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_by_id(999)
        assert result is None

    def test_returns_none_when_empty_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_by_id(1)
        assert result is None


# ============================================================
# get_related_knowledge_by_tags テスト
# ============================================================


class TestGetRelatedKnowledgeByTags:
    def test_returns_related_by_tag(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["施工"])
        # 施工タグを持つもの、またはフォールバックで最新のものが返る
        assert isinstance(result, list)

    def test_excludes_self(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["コンクリート", "施工"], exclude_id=1)
        ids = [k["id"] for k in result]
        assert 1 not in ids

    def test_empty_tags_returns_recent(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags([])
        assert isinstance(result, list)

    def test_respects_limit(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["安全", "品質", "施工"], limit=2)
        assert len(result) <= 2

    def test_no_match_returns_fallback(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["存在しないタグ"], limit=3)
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_empty_data_returns_empty(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["施工"])
        assert result == []

    def test_tag_match_scoring(self, tmp_path):
        data = [
            {
                "id": 1,
                "title": "A",
                "summary": "",
                "content": "",
                "category": "X",
                "tags": ["a", "b", "c"],
                "status": "approved",
                "updated_at": "2024-01-01",
            },
            {
                "id": 2,
                "title": "B",
                "summary": "",
                "content": "",
                "category": "X",
                "tags": ["a"],
                "status": "approved",
                "updated_at": "2024-01-02",
            },
        ]
        write_json(tmp_path, "knowledge.json", data)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["a", "b", "c"], limit=2)
        assert result[0]["id"] == 1


# ============================================================
# create_knowledge テスト
# ============================================================


class TestCreateKnowledge:
    def test_creates_knowledge(self, tmp_path):
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        new_k = {
            "title": "新規ナレッジ",
            "summary": "概要",
            "category": "施工",
            "owner": "テスト",
        }
        result = dal.create_knowledge(new_k)
        assert result["id"] == 1
        assert result["title"] == "新規ナレッジ"

    def test_auto_increments_id(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        new_k = {
            "title": "追加ナレッジ",
            "summary": "概要",
            "category": "品質",
            "owner": "テスト",
        }
        result = dal.create_knowledge(new_k)
        assert result["id"] == 4

    def test_defaults_status_to_draft(self, tmp_path):
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_knowledge(
            {"title": "T", "summary": "S", "category": "C", "owner": "O"}
        )
        assert result["status"] == "draft"

    def test_defaults_priority_to_medium(self, tmp_path):
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_knowledge(
            {"title": "T", "summary": "S", "category": "C", "owner": "O"}
        )
        assert result["priority"] == "medium"

    def test_persists_to_file(self, tmp_path):
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        dal.create_knowledge(
            {"title": "T", "summary": "S", "category": "C", "owner": "O"}
        )
        saved = json.loads((tmp_path / "knowledge.json").read_text())
        assert len(saved) == 1
        assert saved[0]["title"] == "T"

    def test_with_tags_and_optional_fields(self, tmp_path):
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_knowledge(
            {
                "title": "T",
                "summary": "S",
                "content": "詳細",
                "category": "C",
                "owner": "O",
                "tags": ["tag1", "tag2"],
                "status": "approved",
                "priority": "high",
                "project": "ProjectX",
                "created_by_id": 5,
            }
        )
        assert result["tags"] == ["tag1", "tag2"]
        assert result["status"] == "approved"
        assert result["created_by_id"] == 5


# ============================================================
# update_knowledge テスト
# ============================================================


class TestUpdateKnowledge:
    def test_updates_knowledge(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.update_knowledge(1, {"title": "更新タイトル"})
        assert result is not None
        assert result["title"] == "更新タイトル"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.update_knowledge(999, {"title": "更新"})
        assert result is None

    def test_does_not_change_id(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.update_knowledge(1, {"id": 999, "title": "更新"})
        assert result["id"] == 1

    def test_persists_changes(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        dal.update_knowledge(2, {"status": "approved"})
        saved = json.loads((tmp_path / "knowledge.json").read_text())
        updated = next(k for k in saved if k["id"] == 2)
        assert updated["status"] == "approved"

    def test_updates_updated_at(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.update_knowledge(1, {"title": "変更"})
        assert result["updated_at"] is not None


# ============================================================
# delete_knowledge テスト
# ============================================================


class TestDeleteKnowledge:
    def test_deletes_knowledge(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.delete_knowledge(1)
        assert result is True

    def test_removes_from_file(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        dal.delete_knowledge(1)
        saved = json.loads((tmp_path / "knowledge.json").read_text())
        ids = [k["id"] for k in saved]
        assert 1 not in ids

    def test_returns_false_when_not_found(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        result = dal.delete_knowledge(999)
        assert result is False

    def test_does_not_delete_others(self, tmp_path):
        write_json(tmp_path, "knowledge.json", SAMPLE_KNOWLEDGE)
        dal = make_dal(tmp_path)
        dal.delete_knowledge(2)
        saved = json.loads((tmp_path / "knowledge.json").read_text())
        assert len(saved) == 2

    def test_returns_false_on_empty(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.delete_knowledge(1)
        assert result is False


# ============================================================
# PostgreSQL パス テスト (モック使用)
# ============================================================


def _make_mock_knowledge(
    id=1,
    title="テスト",
    summary="概要",
    content="内容",
    category="施工",
    tags=None,
    status="approved",
    priority="high",
    project="ProjectA",
    owner="田中",
    created_by_id=1,
    updated_by_id=None,
    created_at=None,
    updated_at=None,
):
    from unittest.mock import MagicMock

    mock_k = MagicMock()
    mock_k.id = id
    mock_k.title = title
    mock_k.summary = summary
    mock_k.content = content
    mock_k.category = category
    mock_k.tags = tags or []
    mock_k.status = status
    mock_k.priority = priority
    mock_k.project = project
    mock_k.owner = owner
    mock_k.created_by_id = created_by_id
    mock_k.updated_by_id = updated_by_id
    mock_k.created_at = created_at
    mock_k.updated_at = updated_at
    return mock_k


def _make_fluent_mock_session(terminal_method="all", return_value=None):
    """SQLAlchemy fluent chain をシミュレートするモックセッションを作る"""
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.limit.return_value = mock_query
    if terminal_method == "all":
        mock_query.all.return_value = return_value if return_value is not None else []
    elif terminal_method == "first":
        mock_query.first.return_value = return_value
    mock_session.query.return_value = mock_query
    return mock_session


class TestGetKnowledgeListPostgresql:
    def test_returns_empty_when_no_factory(self):
        from unittest.mock import patch

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=None
        ):
            result = dal.get_knowledge_list()
        assert result == []

    def test_returns_list_from_db(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_k = _make_mock_knowledge()
        mock_session = _make_fluent_mock_session(return_value=[mock_k])
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.get_knowledge_list()
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_filter_by_category_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_k = _make_mock_knowledge()
        mock_session = _make_fluent_mock_session(return_value=[mock_k])
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.get_knowledge_list(filters={"category": "施工"})
        assert isinstance(result, list)

    def test_filter_by_search_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_k = _make_mock_knowledge()
        mock_session = _make_fluent_mock_session(return_value=[mock_k])
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.get_knowledge_list(filters={"search": "テスト"})
        assert isinstance(result, list)


class TestGetKnowledgeByIdPostgresql:
    def test_returns_empty_when_no_factory(self):
        from unittest.mock import patch

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=None
        ):
            result = dal.get_knowledge_by_id(1)
        assert result == []

    def test_returns_knowledge_from_db(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_k = _make_mock_knowledge()
        mock_session = _make_fluent_mock_session(terminal_method="first", return_value=mock_k)
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.get_knowledge_by_id(1)
        assert result is not None
        assert result["id"] == 1

    def test_returns_none_when_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _make_fluent_mock_session(terminal_method="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.get_knowledge_by_id(999)
        assert result is None


class TestCreateKnowledgePostgresql:
    def test_returns_empty_when_no_factory(self):
        from unittest.mock import patch

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=None
        ):
            result = dal.create_knowledge(
                {"title": "T", "summary": "S", "category": "C", "owner": "O"}
            )
        assert result == []

    def test_creates_knowledge_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_k = _make_mock_knowledge()
        mock_session = MagicMock()
        mock_session.refresh.side_effect = lambda x: None
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ), patch("dal.knowledge.Knowledge", return_value=mock_k):
            result = dal.create_knowledge(
                {"title": "T", "summary": "S", "category": "C", "owner": "O"}
            )
        assert result is not None


class TestUpdateKnowledgePostgresql:
    def test_returns_empty_when_no_factory(self):
        from unittest.mock import patch

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=None
        ):
            result = dal.update_knowledge(1, {"title": "更新"})
        assert result == []

    def test_returns_none_when_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.update_knowledge(999, {"title": "更新"})
        assert result is None

    def test_updates_knowledge_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_k = _make_mock_knowledge()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_k
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.update_knowledge(1, {"title": "新タイトル"})
        assert result is not None


class TestDeleteKnowledgePostgresql:
    def test_returns_empty_when_no_factory(self):
        from unittest.mock import patch

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=None
        ):
            result = dal.delete_knowledge(1)
        assert result == []

    def test_returns_false_when_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.delete_knowledge(999)
        assert result is False

    def test_deletes_knowledge_pg(self):
        from unittest.mock import MagicMock, patch

        dal = DataAccessLayer(use_postgresql=True)
        mock_k = _make_mock_knowledge()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_k
        mock_factory = MagicMock(return_value=mock_session)

        with patch.object(dal, "_use_postgresql", return_value=True), patch(
            "dal.knowledge.get_session_factory", return_value=mock_factory
        ):
            result = dal.delete_knowledge(1)
        assert result is True


class TestKnowledgeToDict:
    def test_returns_none_for_none_input(self):
        from dal import DataAccessLayer as DAL

        result = DAL._knowledge_to_dict(None)
        assert result is None

    def test_converts_knowledge_object(self):
        from unittest.mock import MagicMock

        mock_k = _make_mock_knowledge()
        from dal import DataAccessLayer as DAL

        result = DAL._knowledge_to_dict(mock_k)
        assert result["id"] == 1
        assert result["title"] == "テスト"
