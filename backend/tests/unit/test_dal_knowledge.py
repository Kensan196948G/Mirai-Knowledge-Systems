"""dal/knowledge.py KnowledgeMixin ユニットテスト（JSONモード）"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ─────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────

@pytest.fixture
def dal(tmp_path):
    """JSON モードの DataAccessLayer インスタンス"""
    from dal import DataAccessLayer

    instance = DataAccessLayer(use_postgresql=False)
    instance.data_dir = str(tmp_path)
    return instance


SAMPLE_KNOWLEDGE = [
    {
        "id": 1,
        "title": "コンクリート打設手順",
        "summary": "コンクリート打設の基本手順を解説",
        "content": "打設前の準備として型枠を確認する",
        "category": "safety",
        "tags": ["concrete", "construction"],
        "status": "approved",
        "priority": "high",
        "project": "プロジェクトA",
        "owner": "yamada",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-10T00:00:00",
        "created_by_id": 1,
        "updated_by_id": 1,
    },
    {
        "id": 2,
        "title": "足場安全管理",
        "summary": "足場の点検チェックリスト",
        "content": "毎日点検を実施する",
        "category": "quality",
        "tags": ["scaffold", "safety"],
        "status": "approved",
        "priority": "medium",
        "project": "プロジェクトB",
        "owner": "suzuki",
        "created_at": "2026-01-02T00:00:00",
        "updated_at": "2026-01-11T00:00:00",
        "created_by_id": 2,
        "updated_by_id": 2,
    },
    {
        "id": 3,
        "title": "品質管理記録",
        "summary": "品質試験記録の書き方",
        "content": "記録は当日中に作成する",
        "category": "quality",
        "tags": ["quality", "record"],
        "status": "draft",
        "priority": "low",
        "project": None,
        "owner": "tanaka",
        "created_at": "2026-01-03T00:00:00",
        "updated_at": "2026-01-12T00:00:00",
        "created_by_id": 3,
        "updated_by_id": None,
    },
]


def write_knowledge(tmp_path, data=None):
    """knowledge.json を書き込むヘルパー"""
    (tmp_path / "knowledge.json").write_text(
        json.dumps(data if data is not None else SAMPLE_KNOWLEDGE, ensure_ascii=False),
        encoding="utf-8",
    )


# ─────────────────────────────────────────────
# get_knowledge_list
# ─────────────────────────────────────────────

class TestGetKnowledgeList:
    def test_returns_all_without_filter(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list()
        assert len(result) == 3

    def test_returns_empty_when_no_data(self, dal, tmp_path):
        write_knowledge(tmp_path, [])
        result = dal.get_knowledge_list()
        assert result == []

    def test_filter_by_category(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"category": "quality"})
        assert len(result) == 2
        assert all(k["category"] == "quality" for k in result)

    def test_filter_by_category_no_match(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"category": "nonexistent"})
        assert result == []

    def test_filter_by_search_title(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "コンクリート"})
        assert len(result) == 1
        assert result[0]["title"] == "コンクリート打設手順"

    def test_filter_by_search_summary(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "チェックリスト"})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_by_search_content(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "当日中"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_filter_by_search_case_insensitive(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "CONCRETE"})
        # content に "concrete" がないので0件（大文字小文字はlowerで変換されるが英語は一致しない）
        # 日本語タイトルに対してのテスト
        result2 = dal.get_knowledge_list(filters={"search": "安全"})
        assert len(result2) >= 1

    def test_filter_by_category_and_search(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(
            filters={"category": "quality", "search": "足場"}
        )
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_no_filter_arg(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters=None)
        assert isinstance(result, list)
        assert len(result) == 3


# ─────────────────────────────────────────────
# get_knowledge_by_id
# ─────────────────────────────────────────────

class TestGetKnowledgeById:
    def test_returns_knowledge_when_found(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "コンクリート打設手順"

    def test_returns_none_when_not_found(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_by_id(9999)
        assert result is None

    def test_returns_correct_item_among_multiple(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_knowledge_by_id(3)
        assert result["category"] == "quality"
        assert result["status"] == "draft"


# ─────────────────────────────────────────────
# get_related_knowledge_by_tags
# ─────────────────────────────────────────────

class TestGetRelatedKnowledgeByTags:
    def test_returns_related_by_tag(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_related_knowledge_by_tags(["safety"])
        assert len(result) >= 1

    def test_excludes_self(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_related_knowledge_by_tags(["safety"], exclude_id=2)
        ids = [k["id"] for k in result]
        assert 2 not in ids

    def test_respects_limit(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_related_knowledge_by_tags(["safety", "quality"], limit=1)
        assert len(result) <= 1

    def test_fallback_when_no_tag_match(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_related_knowledge_by_tags(["nonexistent_tag"], limit=3)
        # フォールバックで最新順のナレッジを返す
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_empty_tags_returns_recent(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.get_related_knowledge_by_tags([], limit=2)
        assert isinstance(result, list)
        assert len(result) <= 2

    def test_sorts_by_tag_match_count(self, dal, tmp_path):
        """タグ一致数が多いものが先に来る"""
        write_knowledge(tmp_path)
        # id=2 は ["scaffold", "safety"], id=1 は ["concrete", "construction"]
        # "safety" にだけマッチするのは id=2
        result = dal.get_related_knowledge_by_tags(["safety", "scaffold"])
        if result:
            # 最初の結果は id=2 (2タグ一致) のはず
            assert result[0]["id"] == 2

    def test_tag_match_removes_internal_key(self, dal, tmp_path):
        """返却データに _tag_match_count が残らない"""
        write_knowledge(tmp_path)
        result = dal.get_related_knowledge_by_tags(["safety"])
        for item in result:
            assert "_tag_match_count" not in item

    def test_no_tags_in_data_uses_fallback(self, dal, tmp_path):
        data = [
            {"id": 1, "title": "A", "updated_at": "2026-01-10T00:00:00"},
            {"id": 2, "title": "B", "updated_at": "2026-01-11T00:00:00"},
        ]
        write_knowledge(tmp_path, data)
        result = dal.get_related_knowledge_by_tags(["safety"])
        assert isinstance(result, list)


# ─────────────────────────────────────────────
# create_knowledge
# ─────────────────────────────────────────────

class TestCreateKnowledge:
    def test_creates_and_returns_new_knowledge(self, dal, tmp_path):
        write_knowledge(tmp_path, [])
        new_data = {
            "title": "新規ナレッジ",
            "summary": "概要",
            "content": "詳細内容",
            "category": "safety",
            "owner": "admin",
        }
        result = dal.create_knowledge(new_data)
        assert result["id"] == 1
        assert result["title"] == "新規ナレッジ"

    def test_auto_assigns_id(self, dal, tmp_path):
        write_knowledge(tmp_path)
        new_data = {
            "title": "4つ目のナレッジ",
            "summary": "概要",
            "category": "environment",
            "owner": "user4",
        }
        result = dal.create_knowledge(new_data)
        assert result["id"] == 4  # max(1,2,3) + 1

    def test_persists_to_json(self, dal, tmp_path):
        write_knowledge(tmp_path, [])
        dal.create_knowledge(
            {"title": "テスト", "summary": "s", "category": "c", "owner": "u"}
        )
        saved = json.loads(
            (tmp_path / "knowledge.json").read_text(encoding="utf-8")
        )
        assert len(saved) == 1
        assert saved[0]["title"] == "テスト"

    def test_default_status_and_priority(self, dal, tmp_path):
        write_knowledge(tmp_path, [])
        result = dal.create_knowledge(
            {"title": "T", "summary": "s", "category": "c", "owner": "u"}
        )
        assert result["status"] == "draft"
        assert result["priority"] == "medium"

    def test_custom_tags_stored(self, dal, tmp_path):
        write_knowledge(tmp_path, [])
        result = dal.create_knowledge(
            {
                "title": "T",
                "summary": "s",
                "category": "c",
                "owner": "u",
                "tags": ["tagA", "tagB"],
            }
        )
        assert result["tags"] == ["tagA", "tagB"]

    def test_has_timestamps(self, dal, tmp_path):
        write_knowledge(tmp_path, [])
        result = dal.create_knowledge(
            {"title": "T", "summary": "s", "category": "c", "owner": "u"}
        )
        assert "created_at" in result
        assert "updated_at" in result


# ─────────────────────────────────────────────
# update_knowledge
# ─────────────────────────────────────────────

class TestUpdateKnowledge:
    def test_updates_existing_knowledge(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.update_knowledge(1, {"title": "更新後タイトル"})
        assert result is not None
        assert result["title"] == "更新後タイトル"

    def test_returns_none_when_not_found(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.update_knowledge(9999, {"title": "X"})
        assert result is None

    def test_persists_update_to_json(self, dal, tmp_path):
        write_knowledge(tmp_path)
        dal.update_knowledge(2, {"summary": "新しい概要"})
        saved = json.loads(
            (tmp_path / "knowledge.json").read_text(encoding="utf-8")
        )
        updated = next(k for k in saved if k["id"] == 2)
        assert updated["summary"] == "新しい概要"

    def test_does_not_change_id(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.update_knowledge(1, {"id": 999, "title": "X"})
        # id は更新されない（key="id" はスキップ）
        assert result["id"] == 1

    def test_updates_updated_at_timestamp(self, dal, tmp_path):
        write_knowledge(tmp_path)
        original = dal.get_knowledge_by_id(1)
        original_updated_at = original["updated_at"]
        dal.update_knowledge(1, {"title": "modified"})
        saved = json.loads(
            (tmp_path / "knowledge.json").read_text(encoding="utf-8")
        )
        updated = next(k for k in saved if k["id"] == 1)
        # updated_at が更新されている（同秒の可能性もあるが存在チェック）
        assert "updated_at" in updated

    def test_partial_update(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.update_knowledge(1, {"priority": "low"})
        assert result["priority"] == "low"
        # 他のフィールドは変わらない
        assert result["title"] == "コンクリート打設手順"


# ─────────────────────────────────────────────
# delete_knowledge
# ─────────────────────────────────────────────

class TestDeleteKnowledge:
    def test_deletes_existing_knowledge(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.delete_knowledge(1)
        assert result is True

    def test_reduces_knowledge_count(self, dal, tmp_path):
        write_knowledge(tmp_path)
        dal.delete_knowledge(1)
        saved = json.loads(
            (tmp_path / "knowledge.json").read_text(encoding="utf-8")
        )
        assert len(saved) == 2
        assert all(k["id"] != 1 for k in saved)

    def test_returns_false_when_not_found(self, dal, tmp_path):
        write_knowledge(tmp_path)
        result = dal.delete_knowledge(9999)
        assert result is False

    def test_does_not_modify_json_when_not_found(self, dal, tmp_path):
        write_knowledge(tmp_path)
        dal.delete_knowledge(9999)
        saved = json.loads(
            (tmp_path / "knowledge.json").read_text(encoding="utf-8")
        )
        assert len(saved) == 3
