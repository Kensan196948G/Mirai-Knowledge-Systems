"""
dal/experts.py カバレッジ向上テスト

ExpertsMixin の JSON パスを中心に CRUD + 統計 + エッジケースをテスト。
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


SAMPLE_EXPERTS = [
    {
        "id": 1,
        "user_id": 10,
        "name": "田中一郎",
        "specialization": "構造",
        "experience_years": 15,
        "is_available": True,
        "rating": 4.5,
        "bio": "構造専門家",
        "contact_email": "tanaka@example.com",
        "created_at": "2024-01-01T00:00:00",
    },
    {
        "id": 2,
        "user_id": 11,
        "name": "鈴木花子",
        "specialization": "安全衛生",
        "experience_years": 10,
        "is_available": False,
        "rating": 4.8,
        "bio": "安全衛生専門家",
        "contact_email": "suzuki@example.com",
        "created_at": "2024-02-01T00:00:00",
    },
    {
        "id": 3,
        "user_id": 12,
        "name": "山田次郎",
        "specialization": "構造",
        "experience_years": 5,
        "is_available": True,
        "rating": 3.9,
        "bio": "若手構造専門家",
        "contact_email": "yamada@example.com",
        "created_at": "2024-03-01T00:00:00",
    },
]

SAMPLE_EXPERT_RATINGS = [
    {"id": 1, "expert_id": 1, "rating": 5.0, "comment": "非常に助かりました"},
    {"id": 2, "expert_id": 1, "rating": 4.0, "comment": "良い回答"},
    {"id": 3, "expert_id": 2, "rating": 4.8, "comment": "迅速な対応"},
]

SAMPLE_CONSULTATIONS = [
    {
        "id": 1,
        "expert_id": 10,
        "requester_id": 1,
        "topic": "基礎設計について",
        "status": "completed",
    },
    {
        "id": 2,
        "expert_id": 10,
        "requester_id": 2,
        "topic": "耐震補強",
        "status": "in_progress",
    },
    {
        "id": 3,
        "expert_id": 11,
        "requester_id": 1,
        "topic": "安全管理",
        "status": "completed",
    },
]


# ============================================================
# get_experts_list テスト
# ============================================================


class TestGetExpertsList:
    def test_list_all_experts(self, tmp_path):
        """フィルタなしで全専門家を取得"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_experts_list()
        assert len(result) == 3

    def test_list_no_experts_empty_file(self, tmp_path):
        """空ファイルで空リストを返す"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", [])
        result = dal.get_experts_list()
        assert result == []

    def test_list_experts_missing_file(self, tmp_path):
        """ファイルなしで空リストを返す"""
        dal = make_dal(tmp_path)
        result = dal.get_experts_list()
        assert result == []

    def test_filter_by_specialization(self, tmp_path):
        """specialization フィルタが機能する"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_experts_list({"specialization": "構造"})
        assert len(result) == 2
        for e in result:
            assert e["specialization"] == "構造"

    def test_filter_by_specialization_no_match(self, tmp_path):
        """存在しない specialization では空リスト"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_experts_list({"specialization": "存在しない"})
        assert result == []

    def test_filter_by_is_available_true(self, tmp_path):
        """is_available=True フィルタ"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_experts_list({"is_available": True})
        assert len(result) == 2
        for e in result:
            assert e["is_available"] is True

    def test_filter_by_is_available_false(self, tmp_path):
        """is_available=False フィルタ"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_experts_list({"is_available": False})
        assert len(result) == 1
        assert result[0]["name"] == "鈴木花子"

    def test_combined_filters(self, tmp_path):
        """複数フィルタの組み合わせ"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_experts_list({"specialization": "構造", "is_available": True})
        assert len(result) == 2
        for e in result:
            assert e["specialization"] == "構造"
            assert e["is_available"] is True

    def test_filters_none(self, tmp_path):
        """filters=None で全件取得"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_experts_list(None)
        assert len(result) == 3


# ============================================================
# get_expert_by_id テスト
# ============================================================


class TestGetExpertById:
    def test_get_existing_expert(self, tmp_path):
        """存在する専門家を取得"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_expert_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "田中一郎"

    def test_get_expert_by_id_2(self, tmp_path):
        """2番目の専門家を取得"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_expert_by_id(2)
        assert result is not None
        assert result["specialization"] == "安全衛生"

    def test_get_nonexistent_expert(self, tmp_path):
        """存在しないIDでNoneを返す"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        result = dal.get_expert_by_id(9999)
        assert result is None

    def test_get_expert_empty_list(self, tmp_path):
        """空リストではNoneを返す"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", [])
        result = dal.get_expert_by_id(1)
        assert result is None

    def test_get_expert_missing_file(self, tmp_path):
        """ファイルなしではNoneを返す"""
        dal = make_dal(tmp_path)
        result = dal.get_expert_by_id(1)
        assert result is None


# ============================================================
# get_expert_stats テスト
# ============================================================


class TestGetExpertStats:
    def test_stats_specific_expert(self, tmp_path):
        """特定専門家の統計を取得"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        write_json(tmp_path, "expert_ratings.json", SAMPLE_EXPERT_RATINGS)
        write_json(tmp_path, "consultations.json", SAMPLE_CONSULTATIONS)
        result = dal.get_expert_stats(expert_id=1)
        assert result["expert_id"] == 1
        assert result["total_ratings"] == 2
        assert result["consultation_count"] == 2

    def test_stats_specific_expert_no_ratings(self, tmp_path):
        """評価なし専門家の統計"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        result = dal.get_expert_stats(expert_id=1)
        assert result["average_rating"] == 0
        assert result["consultation_count"] == 0

    def test_stats_nonexistent_expert(self, tmp_path):
        """存在しない専門家では空辞書を返す"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        result = dal.get_expert_stats(expert_id=9999)
        assert result == {}

    def test_stats_all_experts(self, tmp_path):
        """全専門家の統計を取得"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        write_json(tmp_path, "expert_ratings.json", SAMPLE_EXPERT_RATINGS)
        write_json(tmp_path, "consultations.json", SAMPLE_CONSULTATIONS)
        result = dal.get_expert_stats()
        assert "experts" in result
        assert len(result["experts"]) == 3

    def test_stats_all_experts_empty(self, tmp_path):
        """専門家が0件のとき"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", [])
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        result = dal.get_expert_stats()
        assert result["experts"] == []

    def test_stats_expert_none_arg(self, tmp_path):
        """expert_id=None で全件統計"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        result = dal.get_expert_stats(expert_id=None)
        assert "experts" in result

    def test_stats_rating_average_calculation(self, tmp_path):
        """評価平均の計算が正確"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        ratings = [
            {"id": 1, "expert_id": 1, "rating": 4.0},
            {"id": 2, "expert_id": 1, "rating": 2.0},
        ]
        write_json(tmp_path, "expert_ratings.json", ratings)
        write_json(tmp_path, "consultations.json", [])
        result = dal.get_expert_stats(expert_id=1)
        assert result["average_rating"] == 3.0


# ============================================================
# calculate_expert_rating テスト
# ============================================================


class TestCalculateExpertRating:
    def test_calculate_with_data(self, tmp_path):
        """評価データありで数値を返す"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        write_json(tmp_path, "expert_ratings.json", SAMPLE_EXPERT_RATINGS)
        write_json(tmp_path, "consultations.json", SAMPLE_CONSULTATIONS)
        result = dal.calculate_expert_rating(1)
        assert isinstance(result, float)
        assert 0.0 <= result <= 5.0

    def test_calculate_no_data(self, tmp_path):
        """データなしで0.0を返す"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", SAMPLE_EXPERTS)
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        result = dal.calculate_expert_rating(1)
        assert isinstance(result, float)

    def test_calculate_nonexistent_expert(self, tmp_path):
        """存在しない専門家では0.0を返す"""
        dal = make_dal(tmp_path)
        write_json(tmp_path, "experts.json", [])
        write_json(tmp_path, "expert_ratings.json", [])
        write_json(tmp_path, "consultations.json", [])
        result = dal.calculate_expert_rating(9999)
        assert result == 0.0


# ============================================================
# _expert_to_dict テスト (静的メソッド)
# ============================================================


class TestExpertToDict:
    def test_expert_to_dict_none(self, tmp_path):
        """Noneを渡すとNoneを返す"""
        from dal import DataAccessLayer
        result = DataAccessLayer._expert_to_dict(None)
        assert result is None

    def test_expert_to_dict_with_object(self, tmp_path):
        """Expertオブジェクトを辞書に変換"""
        from datetime import datetime
        from dal import DataAccessLayer

        class MockExpert:
            id = 1
            user_id = 10
            specialization = "構造"
            experience_years = 15
            certifications = ["技術士"]
            rating = 4.5
            consultation_count = 20
            response_time_avg = 30
            is_available = True
            bio = "構造専門家"
            created_at = datetime(2024, 1, 1)
            updated_at = datetime(2024, 6, 1)

        result = DataAccessLayer._expert_to_dict(MockExpert())
        assert result is not None
        assert result["id"] == 1
        assert result["specialization"] == "構造"
        assert result["certifications"] == ["技術士"]

    def test_expert_to_dict_no_dates(self, tmp_path):
        """日付がNoneでもエラーが起きない"""
        from dal import DataAccessLayer

        class MockExpert:
            id = 2
            user_id = 11
            specialization = "安全"
            experience_years = 5
            certifications = None
            rating = 3.0
            consultation_count = 0
            response_time_avg = None
            is_available = False
            bio = None
            created_at = None
            updated_at = None

        result = DataAccessLayer._expert_to_dict(MockExpert())
        assert result is not None
        assert result["id"] == 2
        assert result["certifications"] == []
        assert result["created_at"] is None
