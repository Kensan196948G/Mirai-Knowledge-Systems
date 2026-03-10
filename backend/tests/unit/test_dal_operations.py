"""dal/operations.py OperationsMixin ユニットテスト（JSONモード）"""

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


# ─────────────────────────────────────────────
# SOP（標準施工手順）
# ─────────────────────────────────────────────

SAMPLE_SOP = [
    {
        "id": 1,
        "title": "コンクリート打設手順",
        "category": "concrete",
        "version": "1.0",
        "content": "打設前の準備",
        "status": "active",
        "tags": ["concrete", "safety"],
        "revision_date": "2026-01-01",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-10T00:00:00",
    },
    {
        "id": 2,
        "title": "足場組立手順",
        "category": "scaffold",
        "version": "2.0",
        "content": "足場の組立方法",
        "status": "active",
        "tags": ["scaffold"],
        "revision_date": "2026-01-05",
        "created_at": "2026-01-02T00:00:00",
        "updated_at": "2026-01-11T00:00:00",
    },
    {
        "id": 3,
        "title": "旧手順書",
        "category": "concrete",
        "version": "0.5",
        "content": "古い手順",
        "status": "archived",
        "tags": [],
        "revision_date": None,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-06-01T00:00:00",
    },
]


class TestGetSopList:
    def test_returns_all_without_filter(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_list()
        assert len(result) == 3

    def test_filter_by_category(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_list(filters={"category": "concrete"})
        assert len(result) == 2
        assert all(s["category"] == "concrete" for s in result)

    def test_filter_by_status(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_list(filters={"status": "archived"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_filter_by_search_title(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_list(filters={"search": "足場"})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_by_search_content(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_list(filters={"search": "古い"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_no_filter_returns_list(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps([], ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_list()
        assert result == []

    def test_multiple_filters(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_list(filters={"category": "concrete", "status": "active"})
        assert len(result) == 1
        assert result[0]["id"] == 1


class TestGetSopById:
    def test_returns_sop_when_found(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_by_id(2)
        assert result is not None
        assert result["title"] == "足場組立手順"

    def test_returns_none_when_not_found(self, dal, tmp_path):
        (tmp_path / "sop.json").write_text(
            json.dumps(SAMPLE_SOP, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_sop_by_id(9999)
        assert result is None


# ─────────────────────────────────────────────
# Incident（事故・ヒヤリレポート）
# ─────────────────────────────────────────────

SAMPLE_INCIDENTS = [
    {
        "id": 1,
        "title": "高所落下ヒヤリ",
        "description": "3階部分での落下危険事象",
        "project": "プロジェクトA",
        "incident_date": "2026-02-01",
        "severity": "high",
        "status": "open",
        "tags": ["fall", "height"],
        "created_at": "2026-02-01T09:00:00",
        "updated_at": "2026-02-01T09:00:00",
    },
    {
        "id": 2,
        "title": "挟まれ事故",
        "description": "重機との接触事故",
        "project": "プロジェクトB",
        "incident_date": "2026-02-10",
        "severity": "critical",
        "status": "closed",
        "tags": ["machinery"],
        "created_at": "2026-02-10T10:00:00",
        "updated_at": "2026-02-12T10:00:00",
    },
    {
        "id": 3,
        "title": "転倒ヒヤリ",
        "description": "資材置き場での転倒",
        "project": "プロジェクトA",
        "incident_date": "2026-02-15",
        "severity": "low",
        "status": "open",
        "tags": [],
        "created_at": "2026-02-15T08:00:00",
        "updated_at": "2026-02-15T08:00:00",
    },
]


class TestGetIncidentsList:
    def test_returns_all_without_filter(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list()
        assert len(result) == 3

    def test_filter_by_project(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list(filters={"project": "プロジェクトA"})
        assert len(result) == 2
        assert all(i["project"] == "プロジェクトA" for i in result)

    def test_filter_by_severity(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list(filters={"severity": "critical"})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_by_status(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list(filters={"status": "open"})
        assert len(result) == 2

    def test_filter_by_search_title(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list(filters={"search": "転倒"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_filter_by_search_description(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list(filters={"search": "重機"})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_sorted_by_incident_date_desc(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list()
        # 日付降順: 2026-02-15 > 2026-02-10 > 2026-02-01
        assert result[0]["id"] == 3
        assert result[-1]["id"] == 1

    def test_empty_incidents_returns_empty_list(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps([], ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incidents_list()
        assert result == []


class TestGetIncidentById:
    def test_returns_incident_when_found(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incident_by_id(1)
        assert result is not None
        assert result["title"] == "高所落下ヒヤリ"

    def test_returns_none_when_not_found(self, dal, tmp_path):
        (tmp_path / "incidents.json").write_text(
            json.dumps(SAMPLE_INCIDENTS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_incident_by_id(9999)
        assert result is None


# ─────────────────────────────────────────────
# Approval（承認フロー）
# ─────────────────────────────────────────────

SAMPLE_APPROVALS = [
    {
        "id": 1,
        "title": "設計変更承認",
        "type": "design_change",
        "description": "基礎設計の変更申請",
        "requester_id": 10,
        "status": "pending",
        "priority": "high",
        "created_at": "2026-02-01T00:00:00",
        "updated_at": "2026-02-01T00:00:00",
    },
    {
        "id": 2,
        "title": "予算追加申請",
        "type": "budget",
        "description": "資材費の追加",
        "requester_id": 20,
        "status": "approved",
        "priority": "medium",
        "created_at": "2026-02-05T00:00:00",
        "updated_at": "2026-02-07T00:00:00",
    },
    {
        "id": 3,
        "title": "工程変更申請",
        "type": "schedule",
        "description": "工期延長の申請",
        "requester_id": 10,
        "status": "pending",
        "priority": "low",
        "created_at": "2026-02-10T00:00:00",
        "updated_at": "2026-02-10T00:00:00",
    },
]


class TestGetApprovalsList:
    def test_returns_all_without_filter(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps(SAMPLE_APPROVALS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list()
        assert len(result) == 3

    def test_filter_by_status(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps(SAMPLE_APPROVALS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list(filters={"status": "pending"})
        assert len(result) == 2
        assert all(a["status"] == "pending" for a in result)

    def test_filter_by_type(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps(SAMPLE_APPROVALS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list(filters={"type": "budget"})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_by_requester_id(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps(SAMPLE_APPROVALS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list(filters={"requester_id": 10})
        assert len(result) == 2
        assert all(a["requester_id"] == 10 for a in result)

    def test_filter_by_priority(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps(SAMPLE_APPROVALS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list(filters={"priority": "high"})
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_sorted_by_created_at_desc(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps(SAMPLE_APPROVALS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list()
        # 作成日降順: id=3 (2026-02-10) > id=2 (2026-02-05) > id=1 (2026-02-01)
        assert result[0]["id"] == 3
        assert result[-1]["id"] == 1

    def test_empty_approvals_returns_empty_list(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps([], ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list()
        assert result == []

    def test_no_filter_arg_works(self, dal, tmp_path):
        (tmp_path / "approvals.json").write_text(
            json.dumps(SAMPLE_APPROVALS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_approvals_list(filters=None)
        assert isinstance(result, list)


# ─────────────────────────────────────────────
# Regulation（法令・規格）
# ─────────────────────────────────────────────

SAMPLE_REGULATIONS = [
    {
        "id": 1,
        "title": "建設業法",
        "issuer": "国土交通省",
        "category": "law",
        "status": "effective",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    },
    {
        "id": 2,
        "title": "労働安全衛生法",
        "issuer": "厚生労働省",
        "category": "safety",
        "status": "effective",
        "created_at": "2026-01-02T00:00:00",
        "updated_at": "2026-01-02T00:00:00",
    },
]


class TestGetRegulationById:
    def test_returns_regulation_when_found(self, dal, tmp_path):
        (tmp_path / "regulations.json").write_text(
            json.dumps(SAMPLE_REGULATIONS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_regulation_by_id(1)
        assert result is not None
        assert result["title"] == "建設業法"

    def test_returns_none_when_not_found(self, dal, tmp_path):
        (tmp_path / "regulations.json").write_text(
            json.dumps(SAMPLE_REGULATIONS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_regulation_by_id(9999)
        assert result is None

    def test_returns_correct_item(self, dal, tmp_path):
        (tmp_path / "regulations.json").write_text(
            json.dumps(SAMPLE_REGULATIONS, ensure_ascii=False), encoding="utf-8"
        )
        result = dal.get_regulation_by_id(2)
        assert result["issuer"] == "厚生労働省"
        assert result["category"] == "safety"
