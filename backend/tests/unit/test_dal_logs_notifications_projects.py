"""dal/logs.py, dal/notifications.py, dal/projects.py ユニットテスト（JSONモード）"""

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
# アクセスログ（LogsMixin）
# ─────────────────────────────────────────────

SAMPLE_LOGS = [
    {
        "id": 1,
        "user_id": 10,
        "username": "yamada",
        "action": "login",
        "resource": "auth",
        "resource_id": None,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "created_at": "2026-02-01T09:00:00",
    },
    {
        "id": 2,
        "user_id": 20,
        "username": "suzuki",
        "action": "view",
        "resource": "knowledge",
        "resource_id": 5,
        "ip_address": "192.168.1.2",
        "user_agent": "Mozilla/5.0",
        "created_at": "2026-02-02T10:00:00",
    },
    {
        "id": 3,
        "user_id": 10,
        "username": "yamada",
        "action": "edit",
        "resource": "knowledge",
        "resource_id": 3,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "created_at": "2026-02-03T11:00:00",
    },
]


def write_logs(tmp_path, data=None):
    (tmp_path / "access_logs.json").write_text(
        json.dumps(data if data is not None else SAMPLE_LOGS, ensure_ascii=False),
        encoding="utf-8",
    )


class TestGetAccessLogs:
    def test_returns_all_without_filter(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.get_access_logs()
        assert len(result) == 3

    def test_filter_by_user_id(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.get_access_logs(filters={"user_id": 10})
        assert len(result) == 2
        assert all(log["user_id"] == 10 for log in result)

    def test_filter_by_action(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.get_access_logs(filters={"action": "login"})
        assert len(result) == 1
        assert result[0]["username"] == "yamada"

    def test_filter_by_resource(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.get_access_logs(filters={"resource": "knowledge"})
        assert len(result) == 2

    def test_sorted_by_created_at_desc(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.get_access_logs()
        assert result[0]["id"] == 3  # 最新
        assert result[-1]["id"] == 1  # 最古

    def test_limit_filter(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.get_access_logs(filters={"limit": 2})
        assert len(result) == 2

    def test_empty_logs(self, dal, tmp_path):
        write_logs(tmp_path, [])
        result = dal.get_access_logs()
        assert result == []

    def test_no_filter_arg(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.get_access_logs(filters=None)
        assert isinstance(result, list)
        assert len(result) == 3


class TestCreateAccessLog:
    def test_creates_log_entry(self, dal, tmp_path):
        write_logs(tmp_path, [])
        new_log = {
            "user_id": 1,
            "username": "admin",
            "action": "create",
            "resource": "knowledge",
            "resource_id": 10,
            "ip_address": "127.0.0.1",
            "user_agent": "TestAgent",
        }
        result = dal.create_access_log(new_log)
        assert result["id"] == 1
        assert result["action"] == "create"

    def test_persists_to_json(self, dal, tmp_path):
        write_logs(tmp_path, [])
        dal.create_access_log({"action": "test", "user_id": 1, "username": "u"})
        saved = json.loads((tmp_path / "access_logs.json").read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["action"] == "test"

    def test_auto_assigns_id(self, dal, tmp_path):
        write_logs(tmp_path)
        result = dal.create_access_log({"action": "delete", "user_id": 99, "username": "admin"})
        assert result["id"] == 4  # max(1,2,3)+1

    def test_has_created_at_timestamp(self, dal, tmp_path):
        write_logs(tmp_path, [])
        result = dal.create_access_log({"action": "login", "user_id": 1, "username": "u"})
        assert "created_at" in result


# ─────────────────────────────────────────────
# 通知（NotificationMixin）
# ─────────────────────────────────────────────

SAMPLE_NOTIFICATIONS = [
    {
        "id": 1,
        "title": "システムメンテナンス",
        "message": "明日メンテナンスを実施します",
        "type": "system",
        "target_users": [10, 20, 30],
        "target_roles": [],
        "priority": "high",
        "status": "sent",
        "created_at": "2026-02-01T08:00:00",
    },
    {
        "id": 2,
        "title": "ナレッジ更新通知",
        "message": "新しいナレッジが追加されました",
        "type": "knowledge",
        "target_users": [20],
        "target_roles": ["admin"],
        "priority": "medium",
        "status": "sent",
        "created_at": "2026-02-02T09:00:00",
    },
    {
        "id": 3,
        "title": "承認依頼",
        "message": "承認が必要です",
        "type": "approval",
        "target_users": [30],
        "target_roles": [],
        "priority": "urgent",
        "status": "sent",
        "created_at": "2026-02-03T10:00:00",
    },
]


def write_notifications(tmp_path, data=None):
    (tmp_path / "notifications.json").write_text(
        json.dumps(
            data if data is not None else SAMPLE_NOTIFICATIONS, ensure_ascii=False
        ),
        encoding="utf-8",
    )


class TestGetNotifications:
    def test_returns_all_without_user_id(self, dal, tmp_path):
        write_notifications(tmp_path)
        result = dal.get_notifications()
        assert len(result) == 3

    def test_filter_by_user_id(self, dal, tmp_path):
        write_notifications(tmp_path)
        result = dal.get_notifications(user_id=20)
        assert len(result) == 2  # id=1(target_users=[10,20,30]) と id=2(target_users=[20])
        ids = [n["id"] for n in result]
        assert 1 in ids
        assert 2 in ids

    def test_user_id_not_in_any(self, dal, tmp_path):
        write_notifications(tmp_path)
        result = dal.get_notifications(user_id=99)
        assert result == []

    def test_sorted_by_created_at_desc(self, dal, tmp_path):
        write_notifications(tmp_path)
        result = dal.get_notifications()
        assert result[0]["id"] == 3  # 最新

    def test_empty_notifications(self, dal, tmp_path):
        write_notifications(tmp_path, [])
        result = dal.get_notifications()
        assert result == []


class TestCreateNotification:
    def test_creates_notification(self, dal, tmp_path):
        write_notifications(tmp_path, [])
        new_n = {
            "title": "テスト通知",
            "message": "テストメッセージ",
            "type": "info",
            "target_users": [1, 2],
        }
        result = dal.create_notification(new_n)
        assert result["id"] == 1
        assert result["title"] == "テスト通知"
        assert result["status"] == "sent"

    def test_default_priority_medium(self, dal, tmp_path):
        write_notifications(tmp_path, [])
        result = dal.create_notification(
            {"title": "T", "message": "M", "type": "info"}
        )
        assert result["priority"] == "medium"

    def test_persists_to_json(self, dal, tmp_path):
        write_notifications(tmp_path, [])
        dal.create_notification({"title": "T", "message": "M", "type": "info"})
        saved = json.loads(
            (tmp_path / "notifications.json").read_text(encoding="utf-8")
        )
        assert len(saved) == 1

    def test_auto_assigns_id(self, dal, tmp_path):
        write_notifications(tmp_path)
        result = dal.create_notification(
            {"title": "New", "message": "Msg", "type": "system"}
        )
        assert result["id"] == 4  # max(1,2,3)+1

    def test_has_read_by_empty_list(self, dal, tmp_path):
        write_notifications(tmp_path, [])
        result = dal.create_notification(
            {"title": "T", "message": "M", "type": "info"}
        )
        assert result["read_by"] == []


# ─────────────────────────────────────────────
# プロジェクト（ProjectsMixin）
# ─────────────────────────────────────────────

SAMPLE_PROJECTS = [
    {
        "id": 1,
        "name": "橋梁架け替え工事",
        "code": "BRG-001",
        "type": "civil",
        "status": "active",
        "budget": 50000000,
        "location": "東京都",
        "manager_id": 10,
        "progress_percentage": 45,
        "created_at": "2026-01-01T00:00:00",
    },
    {
        "id": 2,
        "name": "マンション建設",
        "code": "BLD-002",
        "type": "building",
        "status": "active",
        "budget": 120000000,
        "location": "大阪府",
        "manager_id": 20,
        "progress_percentage": 70,
        "created_at": "2026-01-05T00:00:00",
    },
    {
        "id": 3,
        "name": "道路修繕工事",
        "code": "RD-003",
        "type": "civil",
        "status": "completed",
        "budget": 8000000,
        "location": "愛知県",
        "manager_id": 10,
        "progress_percentage": 100,
        "created_at": "2026-01-10T00:00:00",
    },
]

SAMPLE_TASKS = [
    {"id": 1, "project_id": 1, "title": "基礎工事", "status": "completed"},
    {"id": 2, "project_id": 1, "title": "鋼材設置", "status": "in_progress"},
    {"id": 3, "project_id": 1, "title": "コンクリート打設", "status": "pending"},
    {"id": 4, "project_id": 1, "title": "検査", "status": "completed"},
    {"id": 5, "project_id": 2, "title": "基礎", "status": "completed"},
]


def write_projects(tmp_path, data=None):
    (tmp_path / "projects.json").write_text(
        json.dumps(data if data is not None else SAMPLE_PROJECTS, ensure_ascii=False),
        encoding="utf-8",
    )


def write_tasks(tmp_path, data=None):
    (tmp_path / "project_tasks.json").write_text(
        json.dumps(data if data is not None else SAMPLE_TASKS, ensure_ascii=False),
        encoding="utf-8",
    )


class TestGetProjectsList:
    def test_returns_all_without_filter(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_projects_list()
        assert len(result) == 3

    def test_filter_by_type(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_projects_list(filters={"type": "civil"})
        assert len(result) == 2
        assert all(p["type"] == "civil" for p in result)

    def test_filter_by_status(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_projects_list(filters={"status": "active"})
        assert len(result) == 2

    def test_combined_filters(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_projects_list(filters={"type": "civil", "status": "completed"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_no_filter_returns_all(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_projects_list(filters=None)
        assert len(result) == 3

    def test_empty_projects(self, dal, tmp_path):
        write_projects(tmp_path, [])
        result = dal.get_projects_list()
        assert result == []


class TestGetProjectById:
    def test_returns_project_when_found(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_project_by_id(1)
        assert result is not None
        assert result["name"] == "橋梁架け替え工事"

    def test_returns_none_when_not_found(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_project_by_id(9999)
        assert result is None

    def test_returns_correct_item(self, dal, tmp_path):
        write_projects(tmp_path)
        result = dal.get_project_by_id(2)
        assert result["code"] == "BLD-002"
        assert result["location"] == "大阪府"


class TestGetProjectProgress:
    def test_calculates_progress_correctly(self, dal, tmp_path):
        write_projects(tmp_path)
        write_tasks(tmp_path)
        # project_id=1 は 4タスク中 2完了
        result = dal.get_project_progress(1)
        assert result["project_id"] == 1
        assert result["total_tasks"] == 4
        assert result["tasks_completed"] == 2
        assert result["progress_percentage"] == 50

    def test_returns_zero_when_no_tasks(self, dal, tmp_path):
        write_projects(tmp_path)
        write_tasks(tmp_path, [])
        result = dal.get_project_progress(1)
        assert result["progress_percentage"] == 0
        assert result["total_tasks"] == 0
        assert result["tasks_completed"] == 0

    def test_project_with_no_matching_tasks(self, dal, tmp_path):
        write_projects(tmp_path)
        write_tasks(tmp_path, SAMPLE_TASKS)
        # project_id=3 のタスクはSAMPLE_TAASKSに存在しない
        result = dal.get_project_progress(3)
        assert result["total_tasks"] == 0
        assert result["progress_percentage"] == 0

    def test_full_completion(self, dal, tmp_path):
        write_projects(tmp_path)
        tasks = [
            {"id": 1, "project_id": 10, "title": "A", "status": "completed"},
            {"id": 2, "project_id": 10, "title": "B", "status": "completed"},
        ]
        write_tasks(tmp_path, tasks)
        result = dal.get_project_progress(10)
        assert result["progress_percentage"] == 100

    def test_has_required_keys(self, dal, tmp_path):
        write_projects(tmp_path)
        write_tasks(tmp_path)
        result = dal.get_project_progress(1)
        assert "project_id" in result
        assert "progress_percentage" in result
        assert "tasks_completed" in result
        assert "total_tasks" in result
