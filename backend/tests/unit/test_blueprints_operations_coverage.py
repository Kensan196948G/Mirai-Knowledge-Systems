"""
blueprints/operations.py カバレッジ向上テスト

incidents / approvals / regulations / projects / experts / notifications
各エンドポイントの正常系・エラー系をテスト。
"""

import json
import os
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)


# ============================================================
# Fixtures
# ============================================================

SAMPLE_INCIDENTS = [
    {
        "id": 1,
        "title": "足場崩落事故",
        "category": "fall",
        "severity": "high",
        "status": "open",
        "description": "3階足場が崩落",
        "created_at": "2024-01-10T09:00:00",
    },
    {
        "id": 2,
        "title": "ヒヤリハット",
        "category": "near_miss",
        "severity": "low",
        "status": "closed",
        "description": "資材落下ヒヤリハット",
        "created_at": "2024-02-01T14:00:00",
    },
]

SAMPLE_APPROVALS = [
    {
        "id": 1,
        "title": "設計変更承認",
        "status": "pending",
        "requester_id": 2,
        "created_at": "2024-01-15T10:00:00",
    },
    {
        "id": 2,
        "title": "追加工事承認",
        "status": "pending",
        "requester_id": 2,
        "created_at": "2024-01-20T11:00:00",
    },
]

SAMPLE_NOTIFICATIONS = [
    {
        "id": 1,
        "title": "新しいナレッジが追加されました",
        "message": "Test notification",
        "target_users": [1],
        "target_roles": [],
        "read_by": [],
        "created_at": "2024-03-01T10:00:00",
    },
    {
        "id": 2,
        "title": "システムメンテナンス通知",
        "message": "Maintenance",
        "target_users": [],
        "target_roles": ["admin"],
        "read_by": [],
        "created_at": "2024-03-02T08:00:00",
    },
]


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def ops_client(tmp_path, monkeypatch):
    """operations テスト用クライアント"""
    import app_v2
    import app_helpers

    app = app_v2.app
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(tmp_path)
    app.config["JWT_SECRET_KEY"] = "test-secret-key-longer-than-20"
    monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app_helpers, "CACHE_ENABLED", False)
    app_v2.limiter.enabled = False

    users = [
        {
            "id": 1,
            "username": "admin",
            "password_hash": app_v2.hash_password("admin123"),
            "full_name": "Admin User",
            "department": "Admin",
            "roles": ["admin"],
        },
        {
            "id": 2,
            "username": "partner",
            "password_hash": app_v2.hash_password("partner123"),
            "full_name": "Partner User",
            "department": "Partner",
            "roles": ["partner_company"],
        },
    ]

    _write_json(tmp_path / "users.json", users)
    _write_json(tmp_path / "knowledge.json", [])
    _write_json(tmp_path / "access_logs.json", [])
    _write_json(tmp_path / "sop.json", [])
    _write_json(tmp_path / "incidents.json", SAMPLE_INCIDENTS)
    _write_json(tmp_path / "approvals.json", SAMPLE_APPROVALS)
    _write_json(tmp_path / "notifications.json", SAMPLE_NOTIFICATIONS)

    with app.test_client() as c:
        yield c


@pytest.fixture()
def ops_token(ops_client):
    resp = ops_client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    )
    return resp.get_json()["data"]["access_token"]


@pytest.fixture()
def ops_headers(ops_token):
    return {"Authorization": f"Bearer {ops_token}"}


# ============================================================
# 事故レポート API
# ============================================================


class TestGetIncidents:
    """GET /api/v1/incidents"""

    def test_list_incidents_success(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/incidents", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_list_incidents_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/incidents")
        assert resp.status_code == 401

    def test_list_incidents_pagination_key(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/incidents", headers=ops_headers)
        data = resp.get_json()
        assert "pagination" in data
        assert data["pagination"]["total_items"] == 2

    def test_list_incidents_empty(self, ops_client, ops_headers, tmp_path, monkeypatch):
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))
        _write_json(tmp_path / "incidents.json", [])
        resp = ops_client.get("/api/v1/incidents", headers=ops_headers)
        assert resp.status_code == 200


class TestGetIncidentDetail:
    """GET /api/v1/incidents/<id>"""

    def test_get_incident_found(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/incidents/1", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1

    def test_get_incident_not_found(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/incidents/9999", headers=ops_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_get_incident_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/incidents/1")
        assert resp.status_code == 401


# ============================================================
# 承認フロー API
# ============================================================


class TestGetApprovals:
    """GET /api/v1/approvals"""

    def test_list_approvals_success(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/approvals", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_list_approvals_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/approvals")
        assert resp.status_code == 401


class TestApproveApproval:
    """POST /api/v1/approvals/<id>/approve"""

    def test_approve_success(self, ops_client, ops_headers):
        resp = ops_client.post("/api/v1/approvals/1/approve", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "approved"

    def test_approve_not_found(self, ops_client, ops_headers):
        resp = ops_client.post("/api/v1/approvals/9999/approve", headers=ops_headers)
        assert resp.status_code == 404

    def test_approve_requires_auth(self, ops_client):
        resp = ops_client.post("/api/v1/approvals/1/approve")
        assert resp.status_code == 401


class TestRejectApproval:
    """POST /api/v1/approvals/<id>/reject"""

    def test_reject_success(self, ops_client, ops_headers):
        resp = ops_client.post(
            "/api/v1/approvals/1/reject",
            json={"reason": "予算超過のため"},
            headers=ops_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "rejected"

    def test_reject_no_reason(self, ops_client, ops_headers):
        resp = ops_client.post(
            "/api/v1/approvals/1/reject",
            json={},
            headers=ops_headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_reject_not_found(self, ops_client, ops_headers):
        resp = ops_client.post(
            "/api/v1/approvals/9999/reject",
            json={"reason": "理由"},
            headers=ops_headers,
        )
        assert resp.status_code == 404

    def test_reject_requires_auth(self, ops_client):
        resp = ops_client.post("/api/v1/approvals/1/reject")
        assert resp.status_code == 401


# ============================================================
# 法令 API
# ============================================================


class TestGetRegulationDetail:
    """GET /api/v1/regulations/<id>"""

    def test_get_regulation_not_found(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/regulations/9999", headers=ops_headers)
        assert resp.status_code == 404

    def test_get_regulation_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/regulations/1")
        assert resp.status_code == 401

    def test_get_regulation_with_mock(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_regulation_by_id = lambda reg_id: {
            "id": reg_id,
            "title": "建設業法",
            "category": "labor",
        }
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/regulations/1", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True


# ============================================================
# プロジェクト API
# ============================================================


class TestGetProjects:
    """GET /api/v1/projects"""

    def test_list_projects_success(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_projects_list = lambda filters=None: [
            {"id": 1, "name": "橋梁工事A"},
            {"id": 2, "name": "ビル建設B"},
        ]
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/projects", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_list_projects_with_filter(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_projects_list = lambda filters=None: []
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get(
            "/api/v1/projects?type=bridge&status=active", headers=ops_headers
        )
        assert resp.status_code == 200

    def test_list_projects_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/projects")
        assert resp.status_code == 401

    def test_list_projects_exception_returns_empty(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()

        def raise_error(filters=None):
            raise RuntimeError("DB error")

        mock_dal.get_projects_list = raise_error
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/projects", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []


class TestGetProjectDetail:
    """GET /api/v1/projects/<id>"""

    def test_get_project_found(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_project_by_id = lambda pid: {"id": pid, "name": "橋梁工事A"}
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/projects/1", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["id"] == 1

    def test_get_project_not_found(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_project_by_id = lambda pid: None
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/projects/9999", headers=ops_headers)
        assert resp.status_code == 404

    def test_get_project_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/projects/1")
        assert resp.status_code == 401


# ============================================================
# 専門家 API
# ============================================================


class TestGetExperts:
    """GET /api/v1/experts"""

    def test_list_experts_success(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_experts_list = lambda filters=None: [
            {"id": 1, "name": "田中一郎", "specialization": "構造"},
        ]
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/experts", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_list_experts_with_filters(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_experts_list = lambda filters=None: []
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get(
            "/api/v1/experts?specialization=構造&available=true", headers=ops_headers
        )
        assert resp.status_code == 200

    def test_list_experts_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/experts")
        assert resp.status_code == 401

    def test_list_experts_exception_returns_empty(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()

        def raise_error(filters=None):
            raise RuntimeError("DB error")

        mock_dal.get_experts_list = raise_error
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/experts", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []


class TestGetExpertDetail:
    """GET /api/v1/experts/<id>"""

    def test_get_expert_found(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_expert_by_id = lambda eid: {"id": eid, "name": "田中一郎"}
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/experts/1", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["id"] == 1

    def test_get_expert_not_found(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()
        mock_dal.get_expert_by_id = lambda eid: None
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/experts/9999", headers=ops_headers)
        assert resp.status_code == 404

    def test_get_expert_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/experts/1")
        assert resp.status_code == 401

    def test_get_expert_exception_returns_404(self, ops_client, ops_headers, monkeypatch):
        import blueprints.operations as ops_bp_mod

        mock_dal = type("MockDAL", (), {})()

        def raise_error(eid):
            raise RuntimeError("DB error")

        mock_dal.get_expert_by_id = raise_error
        monkeypatch.setattr(ops_bp_mod, "get_dal", lambda: mock_dal)
        resp = ops_client.get("/api/v1/experts/1", headers=ops_headers)
        assert resp.status_code == 404


# ============================================================
# 通知 API
# ============================================================


class TestGetNotifications:
    """GET /api/v1/notifications"""

    def test_list_notifications_admin(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/notifications", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_notifications_include_role_targeted(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/notifications", headers=ops_headers)
        data = resp.get_json()
        # admin should see both (one target_users=[1], one target_roles=["admin"])
        assert len(data["data"]) == 2

    def test_notifications_unread_count_in_pagination(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/notifications", headers=ops_headers)
        data = resp.get_json()
        assert "unread_count" in data["pagination"]

    def test_list_notifications_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/notifications")
        assert resp.status_code == 401

    def test_list_notifications_user_not_found(self, ops_client, monkeypatch):
        import blueprints.operations as ops_bp_mod

        monkeypatch.setattr(ops_bp_mod, "load_users", lambda: [])
        resp = ops_client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = resp.get_json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = ops_client.get("/api/v1/notifications", headers=headers)
        assert resp2.status_code == 404


class TestMarkNotificationRead:
    """PUT /api/v1/notifications/<id>/read"""

    def test_mark_read_success(self, ops_client, ops_headers):
        resp = ops_client.put("/api/v1/notifications/1/read", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["is_read"] is True

    def test_mark_read_not_found(self, ops_client, ops_headers):
        resp = ops_client.put("/api/v1/notifications/9999/read", headers=ops_headers)
        assert resp.status_code == 404

    def test_mark_read_requires_auth(self, ops_client):
        resp = ops_client.put("/api/v1/notifications/1/read")
        assert resp.status_code == 401

    def test_mark_read_idempotent(self, ops_client, ops_headers):
        ops_client.put("/api/v1/notifications/1/read", headers=ops_headers)
        resp = ops_client.put("/api/v1/notifications/1/read", headers=ops_headers)
        assert resp.status_code == 200


class TestGetUnreadCount:
    """GET /api/v1/notifications/unread/count"""

    def test_unread_count_success(self, ops_client, ops_headers):
        resp = ops_client.get("/api/v1/notifications/unread/count", headers=ops_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "unread_count" in data["data"]

    def test_unread_count_requires_auth(self, ops_client):
        resp = ops_client.get("/api/v1/notifications/unread/count")
        assert resp.status_code == 401

    def test_unread_count_user_not_found(self, ops_client, monkeypatch):
        import blueprints.operations as ops_bp_mod

        monkeypatch.setattr(ops_bp_mod, "load_users", lambda: [])
        resp = ops_client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = resp.get_json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp2 = ops_client.get("/api/v1/notifications/unread/count", headers=headers)
        assert resp2.status_code == 404
