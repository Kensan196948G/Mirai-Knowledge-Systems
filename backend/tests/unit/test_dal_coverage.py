"""
DALカバレッジ向上のためのユニットテスト

対象:
- dal/base.py       (BaseDAL)
- dal/knowledge.py  (KnowledgeMixin)
- dal/experts.py    (ExpertsMixin)
- dal/operations.py (OperationsMixin)
- dal/projects.py   (ProjectsMixin)
- dal/logs.py       (LogsMixin)
- dal/notifications.py (NotificationMixin)
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
    """JSONモード(use_postgresql=False)のDALインスタンスを返す"""
    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)
    return dal


def write_json(tmp_path, filename, data):
    """tmp_path 配下にJSONファイルを書き込む"""
    (tmp_path / filename).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ============================================================
# BaseDAL テスト (dal/base.py)
# ============================================================


class TestBaseDAL:
    """BaseDALのインフラメソッドをテスト"""

    def test_init_use_postgresql_false(self, tmp_path):
        """use_postgresql=False で初期化できる"""
        dal = make_dal(tmp_path)
        assert dal.use_postgresql is False

    def test_use_postgresql_returns_false_when_disabled(self, tmp_path):
        """_use_postgresql() は False を返す（JSONモード）"""
        dal = make_dal(tmp_path)
        assert dal._use_postgresql() is False

    def test_get_json_path(self, tmp_path):
        """_get_json_path が正しいパスを返す"""
        dal = make_dal(tmp_path)
        path = dal._get_json_path("knowledge.json")
        assert path == os.path.join(str(tmp_path), "knowledge.json")

    def test_load_json_returns_empty_list_when_file_missing(self, tmp_path):
        """ファイルが存在しない場合は空リストを返す"""
        dal = make_dal(tmp_path)
        result = dal._load_json("nonexistent.json")
        assert result == []

    def test_load_json_returns_data(self, tmp_path):
        """JSONファイルが存在する場合はデータを返す"""
        data = [{"id": 1, "value": "test"}]
        write_json(tmp_path, "test.json", data)
        dal = make_dal(tmp_path)
        result = dal._load_json("test.json")
        assert result == data

    def test_load_json_returns_empty_list_on_invalid_json(self, tmp_path):
        """不正なJSONの場合は空リストを返す"""
        (tmp_path / "bad.json").write_text("NOT_VALID_JSON", encoding="utf-8")
        dal = make_dal(tmp_path)
        result = dal._load_json("bad.json")
        assert result == []

    def test_load_json_returns_empty_list_when_not_array(self, tmp_path):
        """JSONがリストでない場合は空リストを返す"""
        (tmp_path / "obj.json").write_text('{"key": "value"}', encoding="utf-8")
        dal = make_dal(tmp_path)
        result = dal._load_json("obj.json")
        assert result == []

    def test_load_json_filters_non_dict_items(self, tmp_path):
        """リスト内の非dict要素はフィルタリングされる"""
        (tmp_path / "mixed.json").write_text(
            '[{"id": 1}, "string", 42, null]', encoding="utf-8"
        )
        dal = make_dal(tmp_path)
        result = dal._load_json("mixed.json")
        assert len(result) == 1
        assert result[0] == {"id": 1}

    def test_save_json_creates_file(self, tmp_path):
        """_save_json がファイルを作成する"""
        dal = make_dal(tmp_path)
        data = [{"id": 1, "name": "test"}]
        dal._save_json("output.json", data)
        saved = json.loads((tmp_path / "output.json").read_text(encoding="utf-8"))
        assert saved == data

    def test_save_json_creates_directories(self, tmp_path):
        """存在しないディレクトリも自動作成する"""
        dal = make_dal(tmp_path)
        dal.data_dir = str(tmp_path / "subdir" / "nested")
        data = [{"id": 99}]
        dal._save_json("file.json", data)
        saved_path = tmp_path / "subdir" / "nested" / "file.json"
        assert saved_path.exists()
        assert json.loads(saved_path.read_text(encoding="utf-8")) == data


# ============================================================
# KnowledgeMixin テスト (dal/knowledge.py)
# ============================================================


class TestKnowledgeMixin:
    """ナレッジCRUD操作テスト"""

    def _setup_knowledge(self, tmp_path, items=None):
        if items is None:
            items = [
                {
                    "id": 1,
                    "title": "安全対策マニュアル",
                    "summary": "建設現場の安全対策",
                    "content": "詳細な安全手順を記述",
                    "category": "safety",
                    "tags": ["安全", "現場"],
                    "status": "approved",
                    "priority": "high",
                    "owner": "admin",
                },
                {
                    "id": 2,
                    "title": "品質管理ガイド",
                    "summary": "品質管理の基本",
                    "content": "品質管理手順の詳細",
                    "category": "quality",
                    "tags": ["品質", "管理"],
                    "status": "draft",
                    "priority": "medium",
                    "owner": "user1",
                },
            ]
        write_json(tmp_path, "knowledge.json", items)
        return make_dal(tmp_path)

    def test_get_knowledge_list_returns_all(self, tmp_path):
        """フィルタなしで全ナレッジを返す"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_list()
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_knowledge_list_empty_json(self, tmp_path):
        """空のJSONファイルで空リストを返す"""
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list()
        assert result == []

    def test_get_knowledge_list_no_file(self, tmp_path):
        """ファイルが存在しない場合は空リストを返す"""
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list()
        assert result == []

    def test_get_knowledge_list_filter_by_category(self, tmp_path):
        """カテゴリフィルタが機能する"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"category": "safety"})
        assert len(result) == 1
        assert result[0]["category"] == "safety"

    def test_get_knowledge_list_filter_by_category_no_match(self, tmp_path):
        """マッチしないカテゴリは空リストを返す"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"category": "nonexistent"})
        assert result == []

    def test_get_knowledge_list_filter_by_search_title(self, tmp_path):
        """タイトル検索が機能する"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "安全"})
        assert len(result) == 1
        assert "安全" in result[0]["title"]

    def test_get_knowledge_list_filter_by_search_summary(self, tmp_path):
        """サマリー検索が機能する"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "品質管理の基本"})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_get_knowledge_list_filter_by_search_content(self, tmp_path):
        """コンテンツ検索が機能する"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "安全手順"})
        assert len(result) == 1

    def test_get_knowledge_list_search_case_insensitive(self, tmp_path):
        """検索は大文字小文字を区別しない"""
        items = [
            {
                "id": 1,
                "title": "ABC Safety",
                "summary": "test",
                "content": "test",
                "category": "safety",
            }
        ]
        write_json(tmp_path, "knowledge.json", items)
        dal = make_dal(tmp_path)
        result = dal.get_knowledge_list(filters={"search": "abc safety"})
        assert len(result) == 1

    def test_get_knowledge_by_id_found(self, tmp_path):
        """存在するIDでナレッジを取得できる"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "安全対策マニュアル"

    def test_get_knowledge_by_id_not_found(self, tmp_path):
        """存在しないIDはNoneを返す"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.get_knowledge_by_id(9999)
        assert result is None

    def test_create_knowledge_basic(self, tmp_path):
        """ナレッジが作成される"""
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        new_data = {
            "title": "新しいナレッジ",
            "summary": "概要",
            "content": "詳細",
            "category": "safety",
            "owner": "admin",
        }
        result = dal.create_knowledge(new_data)
        assert result["id"] == 1
        assert result["title"] == "新しいナレッジ"
        assert result["category"] == "safety"
        assert result["status"] == "draft"  # デフォルト値
        assert result["priority"] == "medium"  # デフォルト値

    def test_create_knowledge_increments_id(self, tmp_path):
        """IDが自動インクリメントされる"""
        existing = [
            {
                "id": 5,
                "title": "既存",
                "summary": "x",
                "category": "safety",
                "owner": "a",
            }
        ]
        write_json(tmp_path, "knowledge.json", existing)
        dal = make_dal(tmp_path)
        result = dal.create_knowledge(
            {
                "title": "新規",
                "summary": "x",
                "category": "quality",
                "owner": "b",
            }
        )
        assert result["id"] == 6

    def test_create_knowledge_persists_to_file(self, tmp_path):
        """作成したナレッジがJSONに永続化される"""
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        dal.create_knowledge(
            {
                "title": "永続化テスト",
                "summary": "test",
                "category": "safety",
                "owner": "admin",
            }
        )
        saved = json.loads((tmp_path / "knowledge.json").read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["title"] == "永続化テスト"

    def test_create_knowledge_with_tags(self, tmp_path):
        """タグ付きナレッジが作成できる"""
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_knowledge(
            {
                "title": "タグ付きナレッジ",
                "summary": "test",
                "category": "safety",
                "tags": ["tag1", "tag2"],
                "owner": "admin",
            }
        )
        assert result["tags"] == ["tag1", "tag2"]

    def test_create_knowledge_custom_status(self, tmp_path):
        """カスタムステータスでナレッジを作成できる"""
        write_json(tmp_path, "knowledge.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_knowledge(
            {
                "title": "承認済み",
                "summary": "test",
                "category": "safety",
                "owner": "admin",
                "status": "approved",
            }
        )
        assert result["status"] == "approved"

    def test_update_knowledge_success(self, tmp_path):
        """ナレッジが更新される"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.update_knowledge(1, {"title": "更新されたタイトル"})
        assert result is not None
        assert result["title"] == "更新されたタイトル"

    def test_update_knowledge_not_found(self, tmp_path):
        """存在しないIDはNoneを返す"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.update_knowledge(9999, {"title": "更新"})
        assert result is None

    def test_update_knowledge_persists(self, tmp_path):
        """更新がJSONファイルに反映される"""
        dal = self._setup_knowledge(tmp_path)
        dal.update_knowledge(1, {"summary": "更新されたサマリー"})
        saved = json.loads((tmp_path / "knowledge.json").read_text(encoding="utf-8"))
        item = next(k for k in saved if k["id"] == 1)
        assert item["summary"] == "更新されたサマリー"

    def test_update_knowledge_does_not_change_id(self, tmp_path):
        """IDは更新されない"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.update_knowledge(1, {"id": 999, "title": "テスト"})
        assert result["id"] == 1

    def test_delete_knowledge_success(self, tmp_path):
        """ナレッジが削除される"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.delete_knowledge(1)
        assert result is True

    def test_delete_knowledge_reduces_count(self, tmp_path):
        """削除後にJSONのアイテム数が減る"""
        dal = self._setup_knowledge(tmp_path)
        dal.delete_knowledge(1)
        saved = json.loads((tmp_path / "knowledge.json").read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert all(k["id"] != 1 for k in saved)

    def test_delete_knowledge_not_found(self, tmp_path):
        """存在しないIDはFalseを返す"""
        dal = self._setup_knowledge(tmp_path)
        result = dal.delete_knowledge(9999)
        assert result is False

    def test_get_related_knowledge_by_tags_basic(self, tmp_path):
        """タグが一致するナレッジが返される"""
        items = [
            {
                "id": 1,
                "title": "A",
                "tags": ["安全", "現場"],
                "status": "approved",
                "updated_at": "2024-01-02",
            },
            {
                "id": 2,
                "title": "B",
                "tags": ["品質"],
                "status": "approved",
                "updated_at": "2024-01-01",
            },
            {
                "id": 3,
                "title": "C",
                "tags": ["安全"],
                "status": "approved",
                "updated_at": "2024-01-03",
            },
        ]
        write_json(tmp_path, "knowledge.json", items)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["安全"])
        ids = [r["id"] for r in result]
        assert 1 in ids
        assert 3 in ids
        assert 2 not in ids

    def test_get_related_knowledge_excludes_self(self, tmp_path):
        """exclude_id で自分自身が除外される"""
        items = [
            {
                "id": 1,
                "title": "Self",
                "tags": ["安全"],
                "updated_at": "2024-01-01",
            },
            {
                "id": 2,
                "title": "Other",
                "tags": ["安全"],
                "updated_at": "2024-01-02",
            },
        ]
        write_json(tmp_path, "knowledge.json", items)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["安全"], exclude_id=1)
        ids = [r["id"] for r in result]
        assert 1 not in ids
        assert 2 in ids

    def test_get_related_knowledge_limit(self, tmp_path):
        """limit パラメータが機能する"""
        items = [
            {"id": i, "title": f"K{i}", "tags": ["共通"], "updated_at": f"2024-01-{i:02d}"}
            for i in range(1, 11)
        ]
        write_json(tmp_path, "knowledge.json", items)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["共通"], limit=3)
        assert len(result) <= 3

    def test_get_related_knowledge_no_tags_returns_recent(self, tmp_path):
        """タグが空のとき最近のナレッジを返す"""
        items = [
            {"id": 1, "title": "A", "tags": [], "updated_at": "2024-01-01"},
            {"id": 2, "title": "B", "tags": [], "updated_at": "2024-01-02"},
        ]
        write_json(tmp_path, "knowledge.json", items)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags([])
        assert len(result) > 0

    def test_get_related_knowledge_tag_match_priority(self, tmp_path):
        """タグ一致数が多い順にソートされる"""
        items = [
            {
                "id": 1,
                "title": "One Match",
                "tags": ["A"],
                "updated_at": "2024-01-01",
            },
            {
                "id": 2,
                "title": "Two Matches",
                "tags": ["A", "B"],
                "updated_at": "2024-01-01",
            },
        ]
        write_json(tmp_path, "knowledge.json", items)
        dal = make_dal(tmp_path)
        result = dal.get_related_knowledge_by_tags(["A", "B"], limit=5)
        # ID=2 が先に来る（2タグ一致）
        assert result[0]["id"] == 2


# ============================================================
# ExpertsMixin テスト (dal/experts.py)
# ============================================================


class TestExpertsMixin:
    """専門家CRUD・統計操作テスト"""

    def _setup_experts(self, tmp_path):
        experts = [
            {
                "id": 1,
                "name": "田中太郎",
                "user_id": 10,
                "specialization": "基礎工事",
                "experience_years": 15,
                "is_available": True,
                "consultation_count": 30,
                "response_time_avg": 45,
                "certifications": ["施工管理技士"],
                "rating": 4.2,
            },
            {
                "id": 2,
                "name": "佐藤花子",
                "user_id": 11,
                "specialization": "安全管理",
                "experience_years": 8,
                "is_available": False,
                "consultation_count": 12,
                "response_time_avg": 90,
                "certifications": [],
                "rating": 3.8,
            },
        ]
        write_json(tmp_path, "experts.json", experts)
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        return make_dal(tmp_path)

    def test_get_experts_list_returns_all(self, tmp_path):
        """フィルタなしで全専門家を返す"""
        dal = self._setup_experts(tmp_path)
        result = dal.get_experts_list()
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_experts_list_empty(self, tmp_path):
        """空のJSONで空リストを返す"""
        write_json(tmp_path, "experts.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_experts_list()
        assert result == []

    def test_get_experts_list_filter_by_specialization(self, tmp_path):
        """専門化フィルタが機能する"""
        dal = self._setup_experts(tmp_path)
        result = dal.get_experts_list(filters={"specialization": "基礎工事"})
        assert len(result) == 1
        assert result[0]["specialization"] == "基礎工事"

    def test_get_experts_list_filter_by_is_available_true(self, tmp_path):
        """is_available=True フィルタが機能する"""
        dal = self._setup_experts(tmp_path)
        result = dal.get_experts_list(filters={"is_available": True})
        assert len(result) == 1
        assert result[0]["is_available"] is True

    def test_get_experts_list_filter_by_is_available_false(self, tmp_path):
        """is_available=False フィルタが機能する"""
        dal = self._setup_experts(tmp_path)
        result = dal.get_experts_list(filters={"is_available": False})
        assert len(result) == 1
        assert result[0]["is_available"] is False

    def test_get_expert_by_id_found(self, tmp_path):
        """存在するIDで専門家を取得できる"""
        dal = self._setup_experts(tmp_path)
        result = dal.get_expert_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "田中太郎"

    def test_get_expert_by_id_not_found(self, tmp_path):
        """存在しないIDはNoneを返す"""
        dal = self._setup_experts(tmp_path)
        result = dal.get_expert_by_id(9999)
        assert result is None

    def test_get_expert_stats_single_expert(self, tmp_path):
        """特定の専門家の統計が返される"""
        experts = [
            {
                "id": 1,
                "user_id": 10,
                "specialization": "基礎工事",
                "experience_years": 15,
                "is_available": True,
                "consultation_count": 5,
            }
        ]
        ratings = [
            {"id": 1, "expert_id": 1, "rating": 4},
            {"id": 2, "expert_id": 1, "rating": 5},
        ]
        consultations = [
            {"id": 1, "expert_id": 10},
            {"id": 2, "expert_id": 10},
        ]
        write_json(tmp_path, "experts.json", experts)
        write_json(tmp_path, "expert_ratings.json", ratings)
        write_json(tmp_path, "consultations.json", consultations)
        dal = make_dal(tmp_path)

        result = dal.get_expert_stats(expert_id=1)
        assert result["expert_id"] == 1
        assert result["average_rating"] == 4.5
        assert result["total_ratings"] == 2
        assert result["consultation_count"] == 2

    def test_get_expert_stats_not_found(self, tmp_path):
        """存在しない専門家IDは空辞書を返す"""
        write_json(tmp_path, "experts.json", [])
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_expert_stats(expert_id=9999)
        assert result == {}

    def test_get_expert_stats_all_experts(self, tmp_path):
        """全専門家の統計が辞書形式で返される"""
        dal = self._setup_experts(tmp_path)
        result = dal.get_expert_stats()
        assert "experts" in result
        assert isinstance(result["experts"], list)
        assert len(result["experts"]) == 2

    def test_get_expert_stats_no_ratings(self, tmp_path):
        """評価なしの場合average_ratingは0"""
        experts = [
            {
                "id": 1,
                "user_id": 10,
                "specialization": "基礎工事",
                "experience_years": 5,
                "is_available": True,
            }
        ]
        write_json(tmp_path, "experts.json", experts)
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_expert_stats(expert_id=1)
        assert result["average_rating"] == 0

    def test_calculate_expert_rating_basic(self, tmp_path):
        """専門家評価が計算される（0以上5以下）"""
        experts = [
            {
                "id": 1,
                "consultation_count": 25,
                "response_time_avg": 60,
                "experience_years": 10,
            }
        ]
        ratings = [{"id": 1, "expert_id": 1, "rating": 4}]
        write_json(tmp_path, "experts.json", experts)
        write_json(tmp_path, "expert_ratings.json", ratings)
        dal = make_dal(tmp_path)
        result = dal.calculate_expert_rating(1)
        assert isinstance(result, float)
        assert 0.0 <= result <= 5.0

    def test_calculate_expert_rating_not_found(self, tmp_path):
        """存在しない専門家IDは0.0を返す"""
        write_json(tmp_path, "experts.json", [])
        write_json(tmp_path, "expert_ratings.json", [])
        dal = make_dal(tmp_path)
        result = dal.calculate_expert_rating(9999)
        assert result == 0.0

    def test_calculate_expert_rating_no_ratings_defaults(self, tmp_path):
        """評価なしでもデフォルト値で計算される"""
        experts = [
            {
                "id": 1,
                "consultation_count": 0,
                "response_time_avg": 60,
                "experience_years": 0,
            }
        ]
        write_json(tmp_path, "experts.json", experts)
        write_json(tmp_path, "expert_ratings.json", [])
        dal = make_dal(tmp_path)
        result = dal.calculate_expert_rating(1)
        # デフォルトuser_rating_avg=3.0 * 0.4 = 1.2 + bonuses
        assert result >= 0.0


# ============================================================
# OperationsMixin テスト (dal/operations.py)
# ============================================================


class TestOperationsMixin:
    """SOP・インシデント・承認・法令のCRUDテスト"""

    # --- SOP ---

    def test_get_sop_list_returns_all(self, tmp_path):
        """SOPリストが全件返される"""
        sops = [
            {"id": 1, "title": "高所作業手順", "category": "safety", "status": "active"},
            {"id": 2, "title": "コンクリート打設", "category": "construction", "status": "draft"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list()
        assert len(result) == 2

    def test_get_sop_list_empty(self, tmp_path):
        """空のJSONで空リストを返す"""
        write_json(tmp_path, "sop.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_sop_list()
        assert result == []

    def test_get_sop_list_filter_by_category(self, tmp_path):
        """カテゴリフィルタが機能する"""
        sops = [
            {"id": 1, "title": "A", "category": "safety"},
            {"id": 2, "title": "B", "category": "construction"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"category": "safety"})
        assert len(result) == 1
        assert result[0]["category"] == "safety"

    def test_get_sop_list_filter_by_status(self, tmp_path):
        """ステータスフィルタが機能する"""
        sops = [
            {"id": 1, "title": "A", "status": "active"},
            {"id": 2, "title": "B", "status": "draft"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"status": "active"})
        assert len(result) == 1
        assert result[0]["status"] == "active"

    def test_get_sop_list_filter_by_search(self, tmp_path):
        """検索フィルタが機能する"""
        sops = [
            {"id": 1, "title": "高所作業手順", "content": "詳細説明"},
            {"id": 2, "title": "コンクリート", "content": "他の説明"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"search": "高所"})
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_get_sop_by_id_found(self, tmp_path):
        """存在するIDでSOPを取得できる"""
        sops = [{"id": 1, "title": "手順A"}, {"id": 2, "title": "手順B"}]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(1)
        assert result is not None
        assert result["title"] == "手順A"

    def test_get_sop_by_id_not_found(self, tmp_path):
        """存在しないIDはNoneを返す"""
        write_json(tmp_path, "sop.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(9999)
        assert result is None

    # --- Incidents ---

    def test_get_incidents_list_returns_all(self, tmp_path):
        """インシデントリストが全件返される"""
        incidents = [
            {
                "id": 1,
                "title": "転倒事故",
                "severity": "high",
                "status": "open",
                "incident_date": "2024-01-15",
            },
            {
                "id": 2,
                "title": "ヒヤリハット",
                "severity": "low",
                "status": "closed",
                "incident_date": "2024-01-10",
            },
        ]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list()
        assert len(result) == 2

    def test_get_incidents_list_sorted_by_date(self, tmp_path):
        """日付降順でソートされる"""
        incidents = [
            {"id": 1, "title": "古いインシデント", "incident_date": "2024-01-01"},
            {"id": 2, "title": "新しいインシデント", "incident_date": "2024-01-20"},
        ]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list()
        assert result[0]["id"] == 2

    def test_get_incidents_list_filter_by_severity(self, tmp_path):
        """重大度フィルタが機能する"""
        incidents = [
            {"id": 1, "title": "A", "severity": "high", "incident_date": "2024-01-01"},
            {"id": 2, "title": "B", "severity": "low", "incident_date": "2024-01-01"},
        ]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"severity": "high"})
        assert len(result) == 1
        assert result[0]["severity"] == "high"

    def test_get_incidents_list_filter_by_status(self, tmp_path):
        """ステータスフィルタが機能する"""
        incidents = [
            {"id": 1, "title": "A", "status": "open", "incident_date": "2024-01-01"},
            {"id": 2, "title": "B", "status": "closed", "incident_date": "2024-01-01"},
        ]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"status": "open"})
        assert len(result) == 1

    def test_get_incidents_list_filter_by_project(self, tmp_path):
        """プロジェクトフィルタが機能する"""
        incidents = [
            {"id": 1, "title": "A", "project": "proj-A", "incident_date": "2024-01-01"},
            {"id": 2, "title": "B", "project": "proj-B", "incident_date": "2024-01-01"},
        ]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"project": "proj-A"})
        assert len(result) == 1
        assert result[0]["project"] == "proj-A"

    def test_get_incidents_list_filter_by_search(self, tmp_path):
        """検索フィルタが機能する"""
        incidents = [
            {
                "id": 1,
                "title": "転倒事故",
                "description": "足場で転倒",
                "incident_date": "2024-01-01",
            },
            {
                "id": 2,
                "title": "落下事故",
                "description": "資材落下",
                "incident_date": "2024-01-01",
            },
        ]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"search": "転倒"})
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_get_incident_by_id_found(self, tmp_path):
        """存在するIDでインシデントを取得できる"""
        incidents = [{"id": 1, "title": "事故A"}, {"id": 2, "title": "事故B"}]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(1)
        assert result is not None
        assert result["title"] == "事故A"

    def test_get_incident_by_id_not_found(self, tmp_path):
        """存在しないIDはNoneを返す"""
        write_json(tmp_path, "incidents.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(9999)
        assert result is None

    # --- Approvals ---

    def test_get_approvals_list_returns_all(self, tmp_path):
        """承認リストが全件返される"""
        approvals = [
            {"id": 1, "title": "設計変更申請", "status": "pending", "created_at": "2024-01-02"},
            {"id": 2, "title": "予算変更申請", "status": "approved", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "approvals.json", approvals)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list()
        assert len(result) == 2

    def test_get_approvals_list_sorted_by_created_at(self, tmp_path):
        """作成日時降順でソートされる"""
        approvals = [
            {"id": 1, "title": "古い申請", "created_at": "2024-01-01"},
            {"id": 2, "title": "新しい申請", "created_at": "2024-01-20"},
        ]
        write_json(tmp_path, "approvals.json", approvals)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list()
        assert result[0]["id"] == 2

    def test_get_approvals_list_filter_by_status(self, tmp_path):
        """ステータスフィルタが機能する"""
        approvals = [
            {"id": 1, "status": "pending", "created_at": "2024-01-01"},
            {"id": 2, "status": "approved", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "approvals.json", approvals)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"status": "pending"})
        assert len(result) == 1
        assert result[0]["status"] == "pending"

    def test_get_approvals_list_filter_by_type(self, tmp_path):
        """タイプフィルタが機能する"""
        approvals = [
            {"id": 1, "type": "budget", "created_at": "2024-01-01"},
            {"id": 2, "type": "design", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "approvals.json", approvals)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"type": "budget"})
        assert len(result) == 1
        assert result[0]["type"] == "budget"

    def test_get_approvals_list_filter_by_requester_id(self, tmp_path):
        """申請者IDフィルタが機能する"""
        approvals = [
            {"id": 1, "requester_id": 1, "created_at": "2024-01-01"},
            {"id": 2, "requester_id": 2, "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "approvals.json", approvals)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"requester_id": 1})
        assert len(result) == 1
        assert result[0]["requester_id"] == 1

    def test_get_approvals_list_filter_by_priority(self, tmp_path):
        """優先度フィルタが機能する"""
        approvals = [
            {"id": 1, "priority": "high", "created_at": "2024-01-01"},
            {"id": 2, "priority": "low", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "approvals.json", approvals)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"priority": "high"})
        assert len(result) == 1
        assert result[0]["priority"] == "high"

    # --- Regulations ---

    def test_get_regulation_by_id_found(self, tmp_path):
        """存在するIDで法令を取得できる"""
        regulations = [
            {"id": 1, "title": "建設業法"},
            {"id": 2, "title": "労働安全衛生法"},
        ]
        write_json(tmp_path, "regulations.json", regulations)
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(1)
        assert result is not None
        assert result["title"] == "建設業法"

    def test_get_regulation_by_id_not_found(self, tmp_path):
        """存在しないIDはNoneを返す"""
        write_json(tmp_path, "regulations.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(9999)
        assert result is None


# ============================================================
# ProjectsMixin テスト (dal/projects.py)
# ============================================================


class TestProjectsMixin:
    """プロジェクトCRUD・進捗テスト"""

    def _setup_projects(self, tmp_path):
        projects = [
            {
                "id": 1,
                "name": "橋梁建設A",
                "code": "PROJ-001",
                "type": "construction",
                "status": "active",
            },
            {
                "id": 2,
                "name": "道路改修B",
                "code": "PROJ-002",
                "type": "renovation",
                "status": "completed",
            },
        ]
        write_json(tmp_path, "projects.json", projects)
        write_json(tmp_path, "project_tasks.json", [])
        return make_dal(tmp_path)

    def test_get_projects_list_returns_all(self, tmp_path):
        """全プロジェクトが返される"""
        dal = self._setup_projects(tmp_path)
        result = dal.get_projects_list()
        assert len(result) == 2

    def test_get_projects_list_empty(self, tmp_path):
        """空のJSONで空リストを返す"""
        write_json(tmp_path, "projects.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_projects_list()
        assert result == []

    def test_get_projects_list_filter_by_type(self, tmp_path):
        """タイプフィルタが機能する"""
        dal = self._setup_projects(tmp_path)
        result = dal.get_projects_list(filters={"type": "construction"})
        assert len(result) == 1
        assert result[0]["type"] == "construction"

    def test_get_projects_list_filter_by_status(self, tmp_path):
        """ステータスフィルタが機能する"""
        dal = self._setup_projects(tmp_path)
        result = dal.get_projects_list(filters={"status": "active"})
        assert len(result) == 1
        assert result[0]["status"] == "active"

    def test_get_project_by_id_found(self, tmp_path):
        """存在するIDでプロジェクトを取得できる"""
        dal = self._setup_projects(tmp_path)
        result = dal.get_project_by_id(1)
        assert result is not None
        assert result["name"] == "橋梁建設A"

    def test_get_project_by_id_not_found(self, tmp_path):
        """存在しないIDはNoneを返す"""
        dal = self._setup_projects(tmp_path)
        result = dal.get_project_by_id(9999)
        assert result is None

    def test_get_project_progress_no_tasks(self, tmp_path):
        """タスクなしの場合、進捗0%を返す"""
        write_json(tmp_path, "projects.json", [{"id": 1, "name": "ProjA"}])
        write_json(tmp_path, "project_tasks.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_project_progress(1)
        assert result["progress_percentage"] == 0
        assert result["total_tasks"] == 0
        assert result["tasks_completed"] == 0

    def test_get_project_progress_all_completed(self, tmp_path):
        """全タスク完了時に100%を返す"""
        write_json(tmp_path, "projects.json", [{"id": 1, "name": "ProjA"}])
        tasks = [
            {"id": 1, "project_id": 1, "status": "completed"},
            {"id": 2, "project_id": 1, "status": "completed"},
        ]
        write_json(tmp_path, "project_tasks.json", tasks)
        dal = make_dal(tmp_path)
        result = dal.get_project_progress(1)
        assert result["progress_percentage"] == 100
        assert result["tasks_completed"] == 2
        assert result["total_tasks"] == 2

    def test_get_project_progress_partial(self, tmp_path):
        """一部完了タスクで正しい進捗が計算される"""
        write_json(tmp_path, "projects.json", [{"id": 1, "name": "ProjA"}])
        tasks = [
            {"id": 1, "project_id": 1, "status": "completed"},
            {"id": 2, "project_id": 1, "status": "in_progress"},
            {"id": 3, "project_id": 1, "status": "pending"},
            {"id": 4, "project_id": 1, "status": "completed"},
        ]
        write_json(tmp_path, "project_tasks.json", tasks)
        dal = make_dal(tmp_path)
        result = dal.get_project_progress(1)
        assert result["progress_percentage"] == 50
        assert result["tasks_completed"] == 2
        assert result["total_tasks"] == 4

    def test_get_project_progress_project_id_in_result(self, tmp_path):
        """返り値に project_id が含まれる"""
        write_json(tmp_path, "projects.json", [{"id": 42, "name": "ProjX"}])
        write_json(tmp_path, "project_tasks.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_project_progress(42)
        assert result["project_id"] == 42


# ============================================================
# LogsMixin テスト (dal/logs.py)
# ============================================================


class TestLogsMixin:
    """アクセスログCRUDテスト"""

    def test_get_access_logs_empty(self, tmp_path):
        """空のJSONで空リストを返す"""
        write_json(tmp_path, "access_logs.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_access_logs()
        assert result == []

    def test_get_access_logs_returns_all(self, tmp_path):
        """全ログが返される"""
        logs = [
            {"id": 1, "action": "login", "user_id": 1, "created_at": "2024-01-01T10:00:00"},
            {"id": 2, "action": "logout", "user_id": 1, "created_at": "2024-01-01T11:00:00"},
        ]
        write_json(tmp_path, "access_logs.json", logs)
        dal = make_dal(tmp_path)
        result = dal.get_access_logs()
        assert len(result) == 2

    def test_get_access_logs_sorted_descending(self, tmp_path):
        """作成日時降順でソートされる"""
        logs = [
            {"id": 1, "action": "login", "created_at": "2024-01-01T09:00:00"},
            {"id": 2, "action": "view", "created_at": "2024-01-01T12:00:00"},
        ]
        write_json(tmp_path, "access_logs.json", logs)
        dal = make_dal(tmp_path)
        result = dal.get_access_logs()
        assert result[0]["id"] == 2

    def test_get_access_logs_filter_by_user_id(self, tmp_path):
        """ユーザーIDフィルタが機能する"""
        logs = [
            {"id": 1, "user_id": 1, "action": "login", "created_at": "2024-01-01"},
            {"id": 2, "user_id": 2, "action": "login", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "access_logs.json", logs)
        dal = make_dal(tmp_path)
        result = dal.get_access_logs(filters={"user_id": 1})
        assert len(result) == 1
        assert result[0]["user_id"] == 1

    def test_get_access_logs_filter_by_action(self, tmp_path):
        """アクションフィルタが機能する"""
        logs = [
            {"id": 1, "action": "login", "created_at": "2024-01-01"},
            {"id": 2, "action": "logout", "created_at": "2024-01-01"},
            {"id": 3, "action": "login", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "access_logs.json", logs)
        dal = make_dal(tmp_path)
        result = dal.get_access_logs(filters={"action": "login"})
        assert len(result) == 2

    def test_get_access_logs_filter_by_resource(self, tmp_path):
        """リソースフィルタが機能する"""
        logs = [
            {"id": 1, "resource": "knowledge", "action": "view", "created_at": "2024-01-01"},
            {"id": 2, "resource": "sop", "action": "view", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "access_logs.json", logs)
        dal = make_dal(tmp_path)
        result = dal.get_access_logs(filters={"resource": "knowledge"})
        assert len(result) == 1
        assert result[0]["resource"] == "knowledge"

    def test_get_access_logs_filter_by_limit(self, tmp_path):
        """limitフィルタが機能する"""
        logs = [
            {"id": i, "action": "view", "created_at": f"2024-01-{i:02d}"}
            for i in range(1, 11)
        ]
        write_json(tmp_path, "access_logs.json", logs)
        dal = make_dal(tmp_path)
        result = dal.get_access_logs(filters={"limit": 3})
        assert len(result) == 3

    def test_create_access_log_basic(self, tmp_path):
        """アクセスログが作成される"""
        write_json(tmp_path, "access_logs.json", [])
        dal = make_dal(tmp_path)
        log_data = {
            "action": "login",
            "user_id": 1,
            "username": "admin",
            "resource": "auth",
        }
        result = dal.create_access_log(log_data)
        assert result["id"] == 1
        assert result["action"] == "login"
        assert result["user_id"] == 1

    def test_create_access_log_increments_id(self, tmp_path):
        """IDが自動インクリメントされる"""
        existing = [{"id": 10, "action": "login", "created_at": "2024-01-01"}]
        write_json(tmp_path, "access_logs.json", existing)
        dal = make_dal(tmp_path)
        result = dal.create_access_log({"action": "logout"})
        assert result["id"] == 11

    def test_create_access_log_persists(self, tmp_path):
        """作成ログがJSONに永続化される"""
        write_json(tmp_path, "access_logs.json", [])
        dal = make_dal(tmp_path)
        dal.create_access_log({"action": "create", "resource": "knowledge"})
        saved = json.loads((tmp_path / "access_logs.json").read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["action"] == "create"

    def test_create_access_log_optional_fields(self, tmp_path):
        """オプションフィールドなしでログが作成できる"""
        write_json(tmp_path, "access_logs.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_access_log({"action": "minimal_action"})
        assert result["id"] == 1
        assert result["action"] == "minimal_action"
        assert result["user_id"] is None
        assert result["username"] is None

    def test_create_access_log_has_created_at(self, tmp_path):
        """作成ログにcreated_atが設定される"""
        write_json(tmp_path, "access_logs.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_access_log({"action": "test"})
        assert "created_at" in result
        assert result["created_at"] is not None


# ============================================================
# NotificationMixin テスト (dal/notifications.py)
# ============================================================


class TestNotificationMixin:
    """通知CRUDテスト"""

    def test_get_notifications_empty(self, tmp_path):
        """空のJSONで空リストを返す"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert result == []

    def test_get_notifications_returns_all_without_user_id(self, tmp_path):
        """user_id未指定で全通知を返す"""
        notifications = [
            {
                "id": 1,
                "title": "通知A",
                "target_users": [1, 2],
                "created_at": "2024-01-02",
            },
            {
                "id": 2,
                "title": "通知B",
                "target_users": [3],
                "created_at": "2024-01-01",
            },
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert len(result) == 2

    def test_get_notifications_filter_by_user_id(self, tmp_path):
        """user_id指定でそのユーザー向けの通知のみ返す"""
        notifications = [
            {"id": 1, "title": "通知A", "target_users": [1, 2], "created_at": "2024-01-02"},
            {"id": 2, "title": "通知B", "target_users": [3], "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=1)
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_get_notifications_user_not_in_target(self, tmp_path):
        """対象ユーザーでない場合は空リストを返す"""
        notifications = [
            {"id": 1, "title": "通知A", "target_users": [2, 3], "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=999)
        assert result == []

    def test_get_notifications_sorted_descending(self, tmp_path):
        """作成日時降順でソートされる"""
        notifications = [
            {"id": 1, "title": "古い通知", "target_users": [], "created_at": "2024-01-01"},
            {"id": 2, "title": "新しい通知", "target_users": [], "created_at": "2024-01-20"},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert result[0]["id"] == 2

    def test_create_notification_basic(self, tmp_path):
        """通知が作成される"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        notif_data = {
            "title": "新規通知",
            "message": "メッセージ内容",
            "type": "info",
            "target_users": [1, 2],
        }
        result = dal.create_notification(notif_data)
        assert result["id"] == 1
        assert result["title"] == "新規通知"
        assert result["type"] == "info"
        assert result["status"] == "sent"

    def test_create_notification_default_priority(self, tmp_path):
        """優先度のデフォルト値は medium"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "テスト", "message": "msg", "type": "info"}
        )
        assert result["priority"] == "medium"

    def test_create_notification_custom_priority(self, tmp_path):
        """カスタム優先度が設定できる"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {
                "title": "緊急通知",
                "message": "msg",
                "type": "alert",
                "priority": "high",
            }
        )
        assert result["priority"] == "high"

    def test_create_notification_increments_id(self, tmp_path):
        """IDが自動インクリメントされる"""
        existing = [{"id": 5, "title": "既存"}]
        write_json(tmp_path, "notifications.json", existing)
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "新規", "message": "msg", "type": "info"}
        )
        assert result["id"] == 6

    def test_create_notification_persists(self, tmp_path):
        """作成された通知がJSONに永続化される"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        dal.create_notification({"title": "永続化テスト", "message": "msg", "type": "info"})
        saved = json.loads((tmp_path / "notifications.json").read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["title"] == "永続化テスト"

    def test_create_notification_empty_target_users(self, tmp_path):
        """target_usersが空リストでも作成できる"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {
                "title": "ブロードキャスト",
                "message": "全員向け",
                "type": "broadcast",
                "target_users": [],
            }
        )
        assert result["target_users"] == []

    def test_create_notification_with_related_entity(self, tmp_path):
        """related_entity情報付きで通知が作成される"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {
                "title": "ナレッジ更新通知",
                "message": "ナレッジが更新されました",
                "type": "info",
                "related_entity_type": "knowledge",
                "related_entity_id": 42,
            }
        )
        assert result["related_entity_type"] == "knowledge"
        assert result["related_entity_id"] == 42

    def test_create_notification_has_created_at(self, tmp_path):
        """作成された通知にcreated_atが設定される"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "テスト", "message": "msg", "type": "info"}
        )
        assert "created_at" in result
        assert result["created_at"] is not None
