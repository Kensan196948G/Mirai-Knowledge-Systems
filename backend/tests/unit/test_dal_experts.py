"""dal/experts.py ExpertsMixin ユニットテスト（JSONモード）"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@pytest.fixture
def dal(tmp_path):
    """JSON モードの DataAccessLayer インスタンス"""
    from dal import DataAccessLayer

    instance = DataAccessLayer(use_postgresql=False)
    instance.data_dir = str(tmp_path)
    return instance


SAMPLE_EXPERTS = [
    {
        "id": 1,
        "user_id": 101,
        "name": "山田太郎",
        "specialization": "コンクリート工学",
        "experience_years": 15,
        "certifications": ["コンクリート診断士"],
        "rating": 4.5,
        "consultation_count": 30,
        "response_time_avg": 45,
        "is_available": True,
        "bio": "コンクリートの専門家",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-10T00:00:00",
    },
    {
        "id": 2,
        "user_id": 102,
        "name": "鈴木花子",
        "specialization": "足場安全",
        "experience_years": 8,
        "certifications": [],
        "rating": 3.8,
        "consultation_count": 12,
        "response_time_avg": 90,
        "is_available": False,
        "bio": "足場の専門家",
        "created_at": "2026-01-02T00:00:00",
        "updated_at": "2026-01-11T00:00:00",
    },
    {
        "id": 3,
        "user_id": 103,
        "name": "田中次郎",
        "specialization": "コンクリート工学",
        "experience_years": 20,
        "certifications": ["一級建築士", "コンクリート診断士"],
        "rating": 5.0,
        "consultation_count": 60,
        "response_time_avg": 20,
        "is_available": True,
        "bio": "ベテランコンクリートエンジニア",
        "created_at": "2026-01-03T00:00:00",
        "updated_at": "2026-01-12T00:00:00",
    },
]

SAMPLE_RATINGS = [
    {"id": 1, "expert_id": 1, "rating": 4.0, "comment": "良い回答"},
    {"id": 2, "expert_id": 1, "rating": 5.0, "comment": "非常に参考になった"},
    {"id": 3, "expert_id": 2, "rating": 3.0, "comment": "普通"},
    {"id": 4, "expert_id": 3, "rating": 5.0, "comment": "完璧"},
]

SAMPLE_CONSULTATIONS = [
    {"id": 1, "expert_id": 101, "title": "相談1", "status": "closed"},
    {"id": 2, "expert_id": 101, "title": "相談2", "status": "open"},
    {"id": 3, "expert_id": 102, "title": "相談3", "status": "closed"},
]


def write_experts(tmp_path, data=None):
    (tmp_path / "experts.json").write_text(
        json.dumps(data if data is not None else SAMPLE_EXPERTS, ensure_ascii=False),
        encoding="utf-8",
    )


def write_ratings(tmp_path, data=None):
    (tmp_path / "expert_ratings.json").write_text(
        json.dumps(data if data is not None else SAMPLE_RATINGS, ensure_ascii=False),
        encoding="utf-8",
    )


def write_consultations(tmp_path, data=None):
    (tmp_path / "consultations.json").write_text(
        json.dumps(
            data if data is not None else SAMPLE_CONSULTATIONS, ensure_ascii=False
        ),
        encoding="utf-8",
    )


# ─────────────────────────────────────────────
# get_experts_list
# ─────────────────────────────────────────────


class TestGetExpertsList:
    def test_returns_all_without_filter(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_experts_list()
        assert len(result) == 3

    def test_filter_by_specialization(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_experts_list(filters={"specialization": "コンクリート工学"})
        assert len(result) == 2
        assert all(e["specialization"] == "コンクリート工学" for e in result)

    def test_filter_by_is_available_true(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_experts_list(filters={"is_available": True})
        assert len(result) == 2
        assert all(e["is_available"] is True for e in result)

    def test_filter_by_is_available_false(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_experts_list(filters={"is_available": False})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_combined_filters(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_experts_list(
            filters={"specialization": "コンクリート工学", "is_available": True}
        )
        assert len(result) == 2

    def test_no_filter_arg(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_experts_list(filters=None)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_empty_experts(self, dal, tmp_path):
        write_experts(tmp_path, [])
        result = dal.get_experts_list()
        assert result == []

    def test_filter_no_match(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_experts_list(filters={"specialization": "存在しない"})
        assert result == []


# ─────────────────────────────────────────────
# get_expert_by_id
# ─────────────────────────────────────────────


class TestGetExpertById:
    def test_returns_expert_when_found(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_expert_by_id(1)
        assert result is not None
        assert result["name"] == "山田太郎"

    def test_returns_none_when_not_found(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_expert_by_id(9999)
        assert result is None

    def test_returns_correct_item(self, dal, tmp_path):
        write_experts(tmp_path)
        result = dal.get_expert_by_id(3)
        assert result["specialization"] == "コンクリート工学"
        assert result["experience_years"] == 20


# ─────────────────────────────────────────────
# get_expert_stats
# ─────────────────────────────────────────────


class TestGetExpertStats:
    def test_stats_for_specific_expert(self, dal, tmp_path):
        write_experts(tmp_path)
        write_ratings(tmp_path)
        write_consultations(tmp_path)
        result = dal.get_expert_stats(expert_id=1)
        assert result["expert_id"] == 1
        assert result["total_ratings"] == 2
        assert result["average_rating"] == 4.5  # (4+5)/2
        assert result["consultation_count"] == 2  # expert_id=101 の相談

    def test_stats_for_expert_with_no_ratings(self, dal, tmp_path):
        experts = [
            {
                "id": 10,
                "user_id": 200,
                "name": "新人",
                "specialization": "一般",
                "experience_years": 1,
                "is_available": True,
            }
        ]
        write_experts(tmp_path, experts)
        write_ratings(tmp_path, [])
        write_consultations(tmp_path, [])
        result = dal.get_expert_stats(expert_id=10)
        assert result["average_rating"] == 0
        assert result["consultation_count"] == 0
        assert result["total_ratings"] == 0

    def test_stats_returns_empty_for_unknown_expert(self, dal, tmp_path):
        write_experts(tmp_path)
        write_ratings(tmp_path)
        write_consultations(tmp_path)
        result = dal.get_expert_stats(expert_id=9999)
        assert result == {}

    def test_stats_all_experts(self, dal, tmp_path):
        write_experts(tmp_path)
        write_ratings(tmp_path)
        write_consultations(tmp_path)
        result = dal.get_expert_stats()
        assert "experts" in result
        assert len(result["experts"]) == 3

    def test_all_experts_stats_has_required_keys(self, dal, tmp_path):
        write_experts(tmp_path)
        write_ratings(tmp_path)
        write_consultations(tmp_path)
        result = dal.get_expert_stats()
        for stat in result["experts"]:
            assert "expert_id" in stat
            assert "name" in stat
            assert "average_rating" in stat
            assert "consultation_count" in stat


# ─────────────────────────────────────────────
# calculate_expert_rating
# ─────────────────────────────────────────────


class TestCalculateExpertRating:
    def test_calculates_rating_correctly(self, dal, tmp_path):
        """加重平均 = user_rating*0.4 + consultation_bonus*0.3 + response_bonus*0.2 + exp_bonus*0.1"""
        experts = [
            {
                "id": 1,
                "experience_years": 10,
                "consultation_count": 25,  # bonus = 0.5
                "response_time_avg": 60,   # bonus = 0.5
            }
        ]
        ratings = [
            {"expert_id": 1, "rating": 4.0},
        ]
        write_experts(tmp_path, experts)
        write_ratings(tmp_path, ratings)
        result = dal.calculate_expert_rating(1)
        # user_avg=4.0, consultation_bonus=0.5, response_bonus=0.5, exp_bonus=0.5
        expected = round(4.0 * 0.4 + 0.5 * 0.3 + 0.5 * 0.2 + 0.5 * 0.1, 1)
        assert result == expected

    def test_returns_zero_for_unknown_expert(self, dal, tmp_path):
        write_experts(tmp_path)
        write_ratings(tmp_path)
        result = dal.calculate_expert_rating(9999)
        assert result == 0.0

    def test_uses_default_rating_when_no_ratings(self, dal, tmp_path):
        """評価なしの場合はデフォルト3.0を使用"""
        experts = [
            {
                "id": 5,
                "experience_years": 0,
                "consultation_count": 0,
                "response_time_avg": 60,
            }
        ]
        write_experts(tmp_path, experts)
        write_ratings(tmp_path, [])
        result = dal.calculate_expert_rating(5)
        # user_avg=3.0 (default), consultation_bonus=0, response_bonus=0.5, exp_bonus=0
        expected = round(3.0 * 0.4 + 0 * 0.3 + 0.5 * 0.2 + 0 * 0.1, 1)
        assert result == expected

    def test_clamps_to_zero_minimum(self, dal, tmp_path):
        experts = [
            {
                "id": 1,
                "experience_years": 0,
                "consultation_count": 0,
                "response_time_avg": 240,  # response_bonus = max(0, ...) = 0
            }
        ]
        write_experts(tmp_path, experts)
        write_ratings(tmp_path, [{"expert_id": 1, "rating": 0.0}])
        result = dal.calculate_expert_rating(1)
        assert result >= 0.0

    def test_clamps_to_five_maximum(self, dal, tmp_path):
        experts = [
            {
                "id": 1,
                "experience_years": 20,
                "consultation_count": 50,
                "response_time_avg": 0,
            }
        ]
        write_experts(tmp_path, experts)
        write_ratings(tmp_path, [{"expert_id": 1, "rating": 5.0}])
        result = dal.calculate_expert_rating(1)
        assert result <= 5.0
