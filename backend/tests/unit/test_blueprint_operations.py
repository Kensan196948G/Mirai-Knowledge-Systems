"""
blueprints/operations.py Blueprint ユニットテスト

テスト対象エンドポイント:
  GET  /api/v1/incidents               - 事故レポート一覧
  GET  /api/v1/incidents/<id>          - 事故レポート詳細
  GET  /api/v1/approvals               - 承認フロー一覧
  POST /api/v1/approvals/<id>/approve  - 承認処理
  POST /api/v1/approvals/<id>/reject   - 却下処理
  GET  /api/v1/regulations/<id>        - 法令詳細
  GET  /api/v1/projects                - プロジェクト一覧
  GET  /api/v1/projects/<id>           - プロジェクト詳細
  GET  /api/v1/experts                 - 専門家一覧
  GET  /api/v1/experts/<id>            - 専門家詳細
  GET  /api/v1/notifications           - 通知一覧
  PUT  /api/v1/notifications/<id>/read - 既読処理
  GET  /api/v1/notifications/unread/count - 未読数取得
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import Config

# ============================================================
# テストデータ
# ============================================================

SAMPLE_INCIDENTS = [
    {
        "id": 1,
        "title": "高所落下ヒヤリ",
        "description": "3階部分での落下危険事象",
        "project": "プロジェクトA",
        "severity": "high",
        "status": "open",
        "created_at": "2026-02-01T09:00:00",
    },
    {
        "id": 2,
        "title": "挟まれ事故",
        "description": "重機との接触",
        "project": "プロジェクトB",
        "severity": "critical",
        "status": "closed",
        "created_at": "2026-02-10T10:00:00",
    },
]

SAMPLE_APPROVALS = [
    {
        "id": 1,
        "title": "設計変更承認",
        "type": "design_change",
        "status": "pending",
        "requester_id": 1,
        "priority": "high",
        "created_at": "2026-02-01T00:00:00",
    },
    {
        "id": 2,
        "title": "予算追加申請",
        "type": "budget",
        "status": "approved",
        "requester_id": 2,
        "priority": "medium",
        "created_at": "2026-02-05T00:00:00",
    },
]

SAMPLE_REGULATIONS = [
    {
        "id": 1,
        "title": "建設業法",
        "issuer": "国土交通省",
        "category": "law",
        "status": "effective",
    },
]

SAMPLE_PROJECTS = [
    {
        "id": 1,
        "name": "橋梁架け替え工事",
        "code": "BRG-001",
        "type": "civil",
        "status": "active",
        "budget": 50000000,
    },
    {
        "id": 2,
        "name": "マンション建設",
        "code": "BLD-002",
        "type": "building",
        "status": "active",
        "budget": 120000000,
    },
]

SAMPLE_EXPERTS = [
    {
        "id": 1,
        "user_id": 101,
        "name": "山田太郎",
        "specialization": "コンクリート工学",
        "is_available": True,
    },
    {
        "id": 2,
        "user_id": 102,
        "name": "鈴木花子",
        "specialization": "足場安全",
        "is_available": False,
    },
]

SAMPLE_NOTIFICATIONS = [
    {
        "id": 1,
        "title": "システムメンテ",
        "message": "明日メンテを実施",
        "type": "system",
        "target_users": [1],
        "target_roles": [],
        "read_by": [],
        "created_at": "2026-02-01T08:00:00",
    },
    {
        "id": 2,
        "title": "ナレッジ更新",
        "message": "新ナレッジ追加",
        "type": "knowledge",
        "target_users": [],
        "target_roles": ["admin"],
        "read_by": [],
        "created_at": "2026-02-02T09:00:00",
    },
]


# ============================================================
# テスト用フィクスチャ
# ============================================================


@pytest.fixture()
def ops_client(tmp_path, monkeypatch):
    """Operations Blueprint テスト用クライアント"""
    import app_v2
    import app_helpers

    monkeypatch.setattr(app_helpers, "CACHE_ENABLED", False)
    monkeypatch.setattr(Config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app_helpers, "_dal", None)  # DALシングルトンをリセット

    app = app_v2.app
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(tmp_path)
    app.config["JWT_SECRET_KEY"] = "test-secret-key-longer-than-20"
    monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))
    app_v2.limiter.enabled = False

    users = [
        {
            "id": 1,
            "username": "admin",
            "password_hash": app_v2.hash_password("admin123"),
            "full_name": "管理者",
            "department": "総務部",
            "roles": ["admin"],
        },
        {
            "id": 2,
            "username": "manager",
            "password_hash": app_v2.hash_password("manager123"),
            "full_name": "現場監督",
            "department": "現場",
            "roles": ["manager"],
        },
    ]

    def _write(path, data):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _write(tmp_path / "users.json", users)
    _write(tmp_path / "incidents.json", SAMPLE_INCIDENTS)
    _write(tmp_path / "approvals.json", SAMPLE_APPROVALS)
    _write(tmp_path / "regulations.json", SAMPLE_REGULATIONS)
    _write(tmp_path / "projects.json", SAMPLE_PROJECTS)
    _write(tmp_path / "project_tasks.json", [])
    _write(tmp_path / "experts.json", SAMPLE_EXPERTS)
    _write(tmp_path / "expert_ratings.json", [])
    _write(tmp_path / "consultations.json", [])
    _write(tmp_path / "notifications.json", SAMPLE_NOTIFICATIONS)
    _write(tmp_path / "access_logs.json", [])
    _write(tmp_path / "knowledge.json", [])
    _write(tmp_path / "sop.json", [])

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def admin_token(ops_client):
    resp = ops_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def manager_token(ops_client):
    resp = ops_client.post(
        "/api/v1/auth/login",
        json={"username": "manager", "password": "manager123"},
    )
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# GET /api/v1/incidents
# ============================================================


class TestGetIncidents:
    def test_list_success(self, ops_client, admin_token):
        """認証済みで事故レポート一覧を取得できる"""
        resp = ops_client.get("/api/v1/incidents", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert "pagination" in data

    def test_list_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/incidents")
        assert resp.status_code == 401

    def test_empty_incidents(self, ops_client, admin_token, tmp_path):
        """事故レポートが空の場合は空配列"""
        (tmp_path / "incidents.json").write_text("[]", encoding="utf-8")
        resp = ops_client.get("/api/v1/incidents", headers=admin_token)
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []


class TestGetIncidentDetail:
    def test_detail_found(self, ops_client, admin_token):
        """存在する事故レポートを取得できる"""
        resp = ops_client.get("/api/v1/incidents/1", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "高所落下ヒヤリ"

    def test_detail_not_found(self, ops_client, admin_token):
        """存在しない事故レポートは404"""
        resp = ops_client.get("/api/v1/incidents/9999", headers=admin_token)
        assert resp.status_code == 404

    def test_detail_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/incidents/1")
        assert resp.status_code == 401


# ============================================================
# GET /api/v1/approvals
# ============================================================


class TestGetApprovals:
    def test_list_success(self, ops_client, admin_token):
        """認証済みで承認フロー一覧を取得できる"""
        resp = ops_client.get("/api/v1/approvals", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_list_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/approvals")
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/approvals/<id>/approve
# ============================================================


class TestApproveApproval:
    def test_approve_success(self, ops_client, admin_token, tmp_path):
        """管理者が承認処理できる"""
        resp = ops_client.post(
            "/api/v1/approvals/1/approve", headers=admin_token
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "approved"

    def test_approve_not_found(self, ops_client, admin_token):
        """存在しない承認IDは404"""
        resp = ops_client.post(
            "/api/v1/approvals/9999/approve", headers=admin_token
        )
        assert resp.status_code == 404

    def test_approve_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.post("/api/v1/approvals/1/approve")
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/approvals/<id>/reject
# ============================================================


class TestRejectApproval:
    def test_reject_success(self, ops_client, admin_token):
        """管理者が却下処理できる（理由あり）"""
        resp = ops_client.post(
            "/api/v1/approvals/1/reject",
            headers=admin_token,
            json={"reason": "予算超過のため却下"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "rejected"
        assert data["data"]["rejection_reason"] == "予算超過のため却下"

    def test_reject_no_reason(self, ops_client, admin_token):
        """却下理由なしは400"""
        resp = ops_client.post(
            "/api/v1/approvals/1/reject",
            headers=admin_token,
            json={},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_reject_not_found(self, ops_client, admin_token):
        """存在しない承認IDは404"""
        resp = ops_client.post(
            "/api/v1/approvals/9999/reject",
            headers=admin_token,
            json={"reason": "却下"},
        )
        assert resp.status_code == 404


# ============================================================
# GET /api/v1/regulations/<id>
# ============================================================


class TestGetRegulation:
    def test_detail_found(self, ops_client, admin_token):
        """存在する法令を取得できる"""
        resp = ops_client.get("/api/v1/regulations/1", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "建設業法"

    def test_detail_not_found(self, ops_client, admin_token):
        """存在しない法令は404"""
        resp = ops_client.get("/api/v1/regulations/9999", headers=admin_token)
        assert resp.status_code == 404

    def test_detail_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/regulations/1")
        assert resp.status_code == 401


# ============================================================
# GET /api/v1/projects
# ============================================================


class TestGetProjects:
    def test_list_success(self, ops_client, admin_token):
        """プロジェクト一覧を取得できる"""
        resp = ops_client.get("/api/v1/projects", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_list_filter_by_type(self, ops_client, admin_token):
        """typeフィルタが機能する"""
        resp = ops_client.get(
            "/api/v1/projects?type=civil", headers=admin_token
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert all(p["type"] == "civil" for p in data["data"])

    def test_list_filter_by_status(self, ops_client, admin_token):
        """statusフィルタが機能する"""
        resp = ops_client.get(
            "/api/v1/projects?status=active", headers=admin_token
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert all(p["status"] == "active" for p in data["data"])

    def test_list_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/projects")
        assert resp.status_code == 401


class TestGetProjectDetail:
    def test_detail_found(self, ops_client, admin_token):
        """存在するプロジェクトを取得できる"""
        resp = ops_client.get("/api/v1/projects/1", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "橋梁架け替え工事"

    def test_detail_not_found(self, ops_client, admin_token):
        """存在しないプロジェクトは404"""
        resp = ops_client.get("/api/v1/projects/9999", headers=admin_token)
        assert resp.status_code == 404

    def test_detail_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/projects/1")
        assert resp.status_code == 401


# ============================================================
# GET /api/v1/experts
# ============================================================


class TestGetExperts:
    def test_list_success(self, ops_client, admin_token):
        """専門家一覧を取得できる"""
        resp = ops_client.get("/api/v1/experts", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_list_filter_by_specialization(self, ops_client, admin_token):
        """specializationフィルタが機能する"""
        resp = ops_client.get(
            "/api/v1/experts?specialization=コンクリート工学", headers=admin_token
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert all(e["specialization"] == "コンクリート工学" for e in data["data"])

    def test_list_filter_by_available(self, ops_client, admin_token):
        """availableフィルタが機能する"""
        resp = ops_client.get(
            "/api/v1/experts?available=true", headers=admin_token
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert all(e["is_available"] is True for e in data["data"])

    def test_list_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/experts")
        assert resp.status_code == 401


class TestGetExpertDetail:
    def test_detail_found(self, ops_client, admin_token):
        """存在する専門家を取得できる"""
        resp = ops_client.get("/api/v1/experts/1", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "山田太郎"

    def test_detail_not_found(self, ops_client, admin_token):
        """存在しない専門家は404"""
        resp = ops_client.get("/api/v1/experts/9999", headers=admin_token)
        assert resp.status_code == 404

    def test_detail_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/experts/1")
        assert resp.status_code == 401


# ============================================================
# GET /api/v1/notifications
# ============================================================


class TestGetNotifications:
    def test_list_success(self, ops_client, admin_token):
        """adminは自分向け通知（target_roles: ["admin"]）を受け取る"""
        resp = ops_client.get("/api/v1/notifications", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # admin(id=1)は id=1(target_users=[1]) と id=2(target_roles=["admin"])
        assert len(data["data"]) == 2

    def test_list_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/notifications")
        assert resp.status_code == 401

    def test_list_has_is_read_field(self, ops_client, admin_token):
        """各通知に is_read フィールドが存在する"""
        resp = ops_client.get("/api/v1/notifications", headers=admin_token)
        data = resp.get_json()
        for n in data["data"]:
            assert "is_read" in n

    def test_list_has_unread_count(self, ops_client, admin_token):
        """未読数がpaginationに含まれる"""
        resp = ops_client.get("/api/v1/notifications", headers=admin_token)
        data = resp.get_json()
        assert "unread_count" in data["pagination"]


# ============================================================
# PUT /api/v1/notifications/<id>/read
# ============================================================


class TestMarkNotificationRead:
    def test_mark_read_success(self, ops_client, admin_token):
        """通知を既読にできる"""
        resp = ops_client.put(
            "/api/v1/notifications/1/read", headers=admin_token
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["is_read"] is True

    def test_mark_read_not_found(self, ops_client, admin_token):
        """存在しない通知IDは404"""
        resp = ops_client.put(
            "/api/v1/notifications/9999/read", headers=admin_token
        )
        assert resp.status_code == 404

    def test_mark_read_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.put("/api/v1/notifications/1/read")
        assert resp.status_code == 401


# ============================================================
# GET /api/v1/notifications/unread/count
# ============================================================


class TestGetUnreadCount:
    def test_unread_count_success(self, ops_client, admin_token):
        """未読通知数を取得できる"""
        resp = ops_client.get(
            "/api/v1/notifications/unread/count", headers=admin_token
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "unread_count" in data["data"]

    def test_unread_count_requires_auth(self, ops_client):
        """認証なしでは401"""
        resp = ops_client.get("/api/v1/notifications/unread/count")
        assert resp.status_code == 401

    def test_unread_count_is_integer(self, ops_client, admin_token):
        """未読数は整数"""
        resp = ops_client.get(
            "/api/v1/notifications/unread/count", headers=admin_token
        )
        data = resp.get_json()
        assert isinstance(data["data"]["unread_count"], int)
