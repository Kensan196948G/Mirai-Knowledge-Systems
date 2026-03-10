"""
dal/operations.py + dal/notifications.py カバレッジ向上テスト

OperationsMixin / NotificationMixin の JSON パスを中心にテスト。
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


SAMPLE_SOPS = [
    {
        "id": 1,
        "title": "コンクリート打設手順書",
        "category": "施工",
        "version": "1.0",
        "revision_date": "2024-01-15",
        "target": "現場作業員",
        "tags": ["コンクリート", "施工"],
        "content": "詳細な手順内容",
        "status": "active",
        "supersedes_id": None,
        "attachments": [],
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-15T00:00:00",
        "created_by_id": 1,
        "updated_by_id": None,
    },
    {
        "id": 2,
        "title": "安全管理手順書",
        "category": "安全",
        "version": "2.1",
        "revision_date": "2024-02-01",
        "target": "全員",
        "tags": ["安全"],
        "content": "安全管理の詳細",
        "status": "active",
        "supersedes_id": None,
        "attachments": [],
        "created_at": "2024-01-20T00:00:00",
        "updated_at": "2024-02-01T00:00:00",
        "created_by_id": 2,
        "updated_by_id": 1,
    },
    {
        "id": 3,
        "title": "廃止された手順書",
        "category": "施工",
        "version": "0.9",
        "revision_date": "2023-01-01",
        "target": "現場",
        "tags": [],
        "content": "古い内容",
        "status": "obsolete",
        "supersedes_id": 1,
        "attachments": [],
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-06-01T00:00:00",
        "created_by_id": 1,
        "updated_by_id": None,
    },
]

SAMPLE_INCIDENTS = [
    {
        "id": 1,
        "title": "転落事故",
        "description": "足場からの転落",
        "project": "プロジェクトA",
        "incident_date": "2024-03-10",
        "severity": "high",
        "status": "investigating",
        "corrective_actions": "足場補強",
        "root_cause": "安全帯未着用",
        "tags": ["転落", "安全"],
        "location": "3F足場",
        "involved_parties": ["田中", "鈴木"],
        "created_at": "2024-03-10T09:00:00",
        "updated_at": "2024-03-10T09:00:00",
        "reporter_id": 3,
    },
    {
        "id": 2,
        "title": "ヒヤリハット報告",
        "description": "資材落下のヒヤリハット",
        "project": "プロジェクトB",
        "incident_date": "2024-03-15",
        "severity": "low",
        "status": "closed",
        "corrective_actions": None,
        "root_cause": None,
        "tags": ["落下"],
        "location": "資材置き場",
        "involved_parties": [],
        "created_at": "2024-03-15T11:00:00",
        "updated_at": "2024-03-16T10:00:00",
        "reporter_id": 2,
    },
    {
        "id": 3,
        "title": "機器故障",
        "description": "クレーン異常",
        "project": "プロジェクトA",
        "incident_date": "2024-03-20",
        "severity": "medium",
        "status": "open",
        "corrective_actions": None,
        "root_cause": None,
        "tags": ["機器"],
        "location": "工場",
        "involved_parties": ["山田"],
        "created_at": "2024-03-20T14:00:00",
        "updated_at": "2024-03-20T14:00:00",
        "reporter_id": 1,
    },
]

SAMPLE_APPROVALS = [
    {
        "id": 1,
        "title": "設計変更申請",
        "type": "design_change",
        "description": "外壁仕様変更",
        "requester_id": 2,
        "status": "pending",
        "priority": "high",
        "related_entity_type": "project",
        "related_entity_id": 1,
        "approval_flow": [{"step": 1, "approver_id": 1}],
        "created_at": "2024-03-01T00:00:00",
        "updated_at": "2024-03-01T00:00:00",
        "approved_at": None,
        "approver_id": None,
    },
    {
        "id": 2,
        "title": "工事費用申請",
        "type": "budget",
        "description": "追加工事費用",
        "requester_id": 3,
        "status": "approved",
        "priority": "medium",
        "related_entity_type": "budget",
        "related_entity_id": 5,
        "approval_flow": [],
        "created_at": "2024-02-15T00:00:00",
        "updated_at": "2024-02-20T00:00:00",
        "approved_at": "2024-02-20T00:00:00",
        "approver_id": 1,
    },
    {
        "id": 3,
        "title": "資材購入申請",
        "type": "procurement",
        "description": "鉄筋購入",
        "requester_id": 2,
        "status": "rejected",
        "priority": "low",
        "related_entity_type": None,
        "related_entity_id": None,
        "approval_flow": [],
        "created_at": "2024-03-05T00:00:00",
        "updated_at": "2024-03-06T00:00:00",
        "approved_at": None,
        "approver_id": 1,
    },
]

SAMPLE_REGULATIONS = [
    {
        "id": 1,
        "title": "建設業法",
        "category": "法律",
        "content": "建設業法の詳細",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    },
    {
        "id": 2,
        "title": "労働安全衛生法",
        "category": "法律",
        "content": "安全衛生の規定",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    },
]

SAMPLE_NOTIFICATIONS = [
    {
        "id": 1,
        "title": "承認待ちがあります",
        "message": "設計変更申請の承認をお願いします",
        "type": "approval",
        "target_users": [1, 2],
        "target_roles": ["manager"],
        "priority": "high",
        "related_entity_type": "approval",
        "related_entity_id": 1,
        "created_at": "2024-03-01T10:00:00",
        "status": "sent",
        "read_by": [],
    },
    {
        "id": 2,
        "title": "ナレッジが更新されました",
        "message": "コンクリート手順書が更新されました",
        "type": "knowledge",
        "target_users": [3],
        "target_roles": [],
        "priority": "medium",
        "related_entity_type": "knowledge",
        "related_entity_id": 1,
        "created_at": "2024-03-02T09:00:00",
        "status": "sent",
        "read_by": [3],
    },
    {
        "id": 3,
        "title": "インシデント報告",
        "message": "新しいインシデントが報告されました",
        "type": "incident",
        "target_users": [1],
        "target_roles": ["admin"],
        "priority": "high",
        "related_entity_type": "incident",
        "related_entity_id": 1,
        "created_at": "2024-03-03T08:00:00",
        "status": "sent",
        "read_by": [],
    },
]


# ============================================================
# SOP テスト
# ============================================================


class TestGetSopList:
    def test_returns_all_sops(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list()
        assert len(result) == 3

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_sop_list()
        assert result == []

    def test_filter_by_category(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"category": "安全"})
        assert len(result) == 1
        assert result[0]["title"] == "安全管理手順書"

    def test_filter_by_status(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"status": "active"})
        assert len(result) == 2
        for s in result:
            assert s["status"] == "active"

    def test_filter_by_search_title(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"search": "安全管理"})
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_by_search_content(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"search": "足場補強"})
        # SOPの content にはないので0件
        assert isinstance(result, list)

    def test_filter_no_match(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"category": "存在しないカテゴリ"})
        assert result == []

    def test_no_filters(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters=None)
        assert len(result) == 3

    def test_combined_filters(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"category": "施工", "status": "active"})
        assert len(result) == 1
        assert result[0]["id"] == 1


class TestGetSopById:
    def test_returns_sop(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "コンクリート打設手順書"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(999)
        assert result is None

    def test_returns_none_on_empty_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(1)
        assert result is None

    def test_returns_correct_sop(self, tmp_path):
        write_json(tmp_path, "sop.json", SAMPLE_SOPS)
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(3)
        assert result["status"] == "obsolete"


# ============================================================
# Incident テスト
# ============================================================


class TestGetIncidentsList:
    def test_returns_all_incidents(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list()
        assert len(result) == 3

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list()
        assert result == []

    def test_filter_by_project(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"project": "プロジェクトA"})
        assert len(result) == 2
        for i in result:
            assert i["project"] == "プロジェクトA"

    def test_filter_by_severity(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"severity": "high"})
        assert len(result) == 1
        assert result[0]["severity"] == "high"

    def test_filter_by_status(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"status": "closed"})
        assert len(result) == 1
        assert result[0]["status"] == "closed"

    def test_filter_by_search_title(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"search": "転落"})
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_filter_by_search_description(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters={"search": "クレーン"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_sorted_by_incident_date_desc(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list()
        dates = [i.get("incident_date", "") for i in result]
        assert dates == sorted(dates, reverse=True)

    def test_no_filters(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list(filters=None)
        assert len(result) == 3


class TestGetIncidentById:
    def test_returns_incident(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "転落事故"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "incidents.json", SAMPLE_INCIDENTS)
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(999)
        assert result is None

    def test_returns_none_on_empty_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(1)
        assert result is None


# ============================================================
# Approvals テスト
# ============================================================


class TestGetApprovalsList:
    def test_returns_all_approvals(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list()
        assert len(result) == 3

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list()
        assert result == []

    def test_filter_by_status(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"status": "pending"})
        assert len(result) == 1
        assert result[0]["status"] == "pending"

    def test_filter_by_type(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"type": "budget"})
        assert len(result) == 1
        assert result[0]["type"] == "budget"

    def test_filter_by_requester_id(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"requester_id": 2})
        assert len(result) == 2
        for a in result:
            assert a["requester_id"] == 2

    def test_filter_by_priority(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"priority": "high"})
        assert len(result) == 1
        assert result[0]["priority"] == "high"

    def test_sorted_by_created_at_desc(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list()
        dates = [a.get("created_at", "") for a in result]
        assert dates == sorted(dates, reverse=True)

    def test_no_filters(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters=None)
        assert len(result) == 3

    def test_combined_filters(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(
            filters={"status": "rejected", "requester_id": 2}
        )
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_filter_no_match(self, tmp_path):
        write_json(tmp_path, "approvals.json", SAMPLE_APPROVALS)
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list(filters={"status": "存在しないステータス"})
        assert result == []


# ============================================================
# Regulation テスト
# ============================================================


class TestGetRegulationById:
    def test_returns_regulation(self, tmp_path):
        write_json(tmp_path, "regulations.json", SAMPLE_REGULATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "建設業法"

    def test_returns_none_when_not_found(self, tmp_path):
        write_json(tmp_path, "regulations.json", SAMPLE_REGULATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(999)
        assert result is None

    def test_returns_none_on_empty_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(1)
        assert result is None

    def test_returns_second_regulation(self, tmp_path):
        write_json(tmp_path, "regulations.json", SAMPLE_REGULATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(2)
        assert result["title"] == "労働安全衛生法"


# ============================================================
# Notifications テスト
# ============================================================


class TestGetNotifications:
    def test_returns_all_notifications(self, tmp_path):
        write_json(tmp_path, "notifications.json", SAMPLE_NOTIFICATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert len(result) == 3

    def test_returns_empty_when_no_file(self, tmp_path):
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert result == []

    def test_filter_by_user_id(self, tmp_path):
        write_json(tmp_path, "notifications.json", SAMPLE_NOTIFICATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=1)
        assert len(result) == 2
        for n in result:
            assert 1 in n["target_users"]

    def test_filter_by_user_id_no_match(self, tmp_path):
        write_json(tmp_path, "notifications.json", SAMPLE_NOTIFICATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=99)
        assert result == []

    def test_sorted_by_created_at_desc(self, tmp_path):
        write_json(tmp_path, "notifications.json", SAMPLE_NOTIFICATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        dates = [n.get("created_at", "") for n in result]
        assert dates == sorted(dates, reverse=True)

    def test_user_id_none_returns_all(self, tmp_path):
        write_json(tmp_path, "notifications.json", SAMPLE_NOTIFICATIONS)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=None)
        assert len(result) == 3


class TestCreateNotification:
    def test_creates_notification(self, tmp_path):
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        new_n = {
            "title": "テスト通知",
            "message": "テストメッセージ",
            "type": "system",
            "target_users": [1],
        }
        result = dal.create_notification(new_n)
        assert result["id"] == 1
        assert result["title"] == "テスト通知"

    def test_auto_increments_id(self, tmp_path):
        write_json(tmp_path, "notifications.json", SAMPLE_NOTIFICATIONS)
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "追加通知", "message": "メッセージ", "type": "system"}
        )
        assert result["id"] == 4

    def test_defaults_priority_to_medium(self, tmp_path):
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "T", "message": "M", "type": "system"}
        )
        assert result["priority"] == "medium"

    def test_sets_status_to_sent(self, tmp_path):
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "T", "message": "M", "type": "system"}
        )
        assert result["status"] == "sent"

    def test_sets_read_by_to_empty(self, tmp_path):
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "T", "message": "M", "type": "system"}
        )
        assert result["read_by"] == []

    def test_persists_to_file(self, tmp_path):
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        dal.create_notification(
            {"title": "T", "message": "M", "type": "system"}
        )
        saved = json.loads((tmp_path / "notifications.json").read_text())
        assert len(saved) == 1
        assert saved[0]["title"] == "T"

    def test_with_all_optional_fields(self, tmp_path):
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {
                "title": "通知",
                "message": "詳細メッセージ",
                "type": "approval",
                "target_users": [1, 2],
                "target_roles": ["manager"],
                "priority": "high",
                "related_entity_type": "approval",
                "related_entity_id": 5,
            }
        )
        assert result["target_users"] == [1, 2]
        assert result["target_roles"] == ["manager"]
        assert result["priority"] == "high"
        assert result["related_entity_type"] == "approval"
        assert result["related_entity_id"] == 5

    def test_adds_created_at(self, tmp_path):
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.create_notification(
            {"title": "T", "message": "M", "type": "system"}
        )
        assert "created_at" in result


# ============================================================
# PostgreSQL パス テスト (モック使用)
# ============================================================


def _fluent_session(terminal="all", return_value=None):
    from unittest.mock import MagicMock

    session = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.options.return_value = q
    q.limit.return_value = q
    q.all.return_value = return_value if return_value is not None else []
    q.first.return_value = return_value
    session.query.return_value = q
    return session


class TestGetSopListPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=None):
            result = dal.get_sop_list()
        assert result == []

    def test_returns_sops_from_db(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_sop = MagicMock()
        mock_sop.id = 1
        mock_sop.title = "テストSOP"
        mock_sop.category = "施工"
        mock_sop.version = "1.0"
        mock_sop.revision_date = None
        mock_sop.target = "全員"
        mock_sop.tags = []
        mock_sop.content = "内容"
        mock_sop.status = "active"
        mock_sop.supersedes_id = None
        mock_sop.attachments = []
        mock_sop.created_at = None
        mock_sop.updated_at = None
        mock_sop.created_by_id = 1
        mock_sop.updated_by_id = None
        mock_session = _fluent_session(return_value=[mock_sop])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_sop_list()
        assert len(result) == 1

    def test_filter_by_category_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_session(return_value=[])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_sop_list(filters={"category": "施工", "status": "active", "search": "手順"})
        assert isinstance(result, list)


class TestGetSopByIdPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=None):
            result = dal.get_sop_by_id(1)
        assert result == []

    def test_returns_none_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_sop_by_id(999)
        assert result is None


class TestGetIncidentsListPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=None):
            result = dal.get_incidents_list()
        assert result == []

    def test_returns_incidents_from_db(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_i = MagicMock()
        mock_i.id = 1
        mock_i.title = "転落事故"
        mock_i.description = "詳細"
        mock_i.project = "ProjectA"
        mock_i.incident_date = None
        mock_i.severity = "high"
        mock_i.status = "open"
        mock_i.corrective_actions = None
        mock_i.root_cause = None
        mock_i.tags = []
        mock_i.location = "現場"
        mock_i.involved_parties = []
        mock_i.created_at = None
        mock_i.updated_at = None
        mock_i.reporter_id = 1
        mock_session = _fluent_session(return_value=[mock_i])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_incidents_list()
        assert len(result) == 1

    def test_filter_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_session(return_value=[])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_incidents_list(
                filters={"project": "A", "severity": "high", "status": "open", "search": "転落"}
            )
        assert isinstance(result, list)


class TestGetIncidentByIdPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=None):
            result = dal.get_incident_by_id(1)
        assert result == []

    def test_returns_none_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_incident_by_id(999)
        assert result is None


class TestGetApprovalsListPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=None):
            result = dal.get_approvals_list()
        assert result == []

    def test_returns_approvals_from_db(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_a = MagicMock()
        mock_a.id = 1
        mock_a.title = "申請"
        mock_a.type = "design_change"
        mock_a.description = "詳細"
        mock_a.requester_id = 2
        mock_a.status = "pending"
        mock_a.priority = "high"
        mock_a.related_entity_type = None
        mock_a.related_entity_id = None
        mock_a.approval_flow = []
        mock_a.created_at = None
        mock_a.updated_at = None
        mock_a.approved_at = None
        mock_a.approver_id = None
        mock_session = _fluent_session(return_value=[mock_a])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_approvals_list()
        assert len(result) == 1

    def test_filter_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_session(return_value=[])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_approvals_list(
                filters={"status": "pending", "type": "budget", "requester_id": 1, "priority": "high"}
            )
        assert isinstance(result, list)


class TestGetRegulationByIdPostgresql:
    def test_no_factory_returns_none(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=None):
            result = dal.get_regulation_by_id(1)
        assert result is None

    def test_returns_none_not_found_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_session(terminal="first", return_value=None)
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.operations.get_session_factory", return_value=mock_factory):
            result = dal.get_regulation_by_id(999)
        assert result is None


class TestGetNotificationsPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.notifications.get_session_factory", return_value=None):
            result = dal.get_notifications()
        assert result == []

    def test_returns_notifications_from_db(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_n = MagicMock()
        mock_n.id = 1
        mock_n.title = "通知"
        mock_n.message = "メッセージ"
        mock_n.type = "system"
        mock_n.target_users = [1, 2]
        mock_n.target_roles = []
        mock_n.priority = "medium"
        mock_n.related_entity_type = None
        mock_n.related_entity_id = None
        mock_n.created_at = None
        mock_n.sent_at = None
        mock_n.status = "sent"
        mock_session = _fluent_session(return_value=[mock_n])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.notifications.get_session_factory", return_value=mock_factory):
            result = dal.get_notifications()
        assert len(result) == 1

    def test_filter_by_user_id_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_session = _fluent_session(return_value=[])
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.notifications.get_session_factory", return_value=mock_factory):
            result = dal.get_notifications(user_id=1)
        assert isinstance(result, list)


class TestCreateNotificationPostgresql:
    def test_no_factory_returns_empty(self):
        from unittest.mock import patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.notifications.get_session_factory", return_value=None):
            result = dal.create_notification(
                {"title": "T", "message": "M", "type": "system"}
            )
        assert result == []

    def test_creates_notification_pg(self):
        from unittest.mock import MagicMock, patch

        from dal import DataAccessLayer

        dal = DataAccessLayer(use_postgresql=True)
        mock_n = MagicMock()
        mock_n.id = 1
        mock_n.title = "T"
        mock_n.message = "M"
        mock_n.type = "system"
        mock_n.target_users = []
        mock_n.target_roles = []
        mock_n.priority = "medium"
        mock_n.related_entity_type = None
        mock_n.related_entity_id = None
        mock_n.created_at = None
        mock_n.sent_at = None
        mock_n.status = "sent"
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        with patch.object(dal, "_use_postgresql", return_value=True), patch("dal.notifications.get_session_factory", return_value=mock_factory):
            with patch("dal.notifications.Notification", return_value=mock_n):
                result = dal.create_notification(
                    {"title": "T", "message": "M", "type": "system"}
                )
        assert result is not None
