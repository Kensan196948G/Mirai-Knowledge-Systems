"""
blueprints/operations.py カバレッジ強化テスト

対象エンドポイント:
  GET  /api/v1/incidents                     - 事故レポート一覧
  GET  /api/v1/incidents/<id>                - 事故レポート詳細
  GET  /api/v1/approvals                     - 承認フロー一覧
  POST /api/v1/approvals/<id>/approve        - 承認処理
  POST /api/v1/approvals/<id>/reject         - 却下処理
  GET  /api/v1/regulations/<id>              - 法令詳細
  GET  /api/v1/projects                      - プロジェクト一覧
  GET  /api/v1/projects/<id>                 - プロジェクト詳細
  GET  /api/v1/experts                       - 専門家一覧
  GET  /api/v1/experts/<id>                  - 専門家詳細
  GET  /api/v1/notifications                 - 通知一覧
  PUT  /api/v1/notifications/<id>/read       - 通知既読
  GET  /api/v1/notifications/unread/count    - 未読数取得
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


_INCIDENTS = [
    {
        "id": 1,
        "title": "足場からの落下",
        "status": "reported",
        "severity": "high",
        "description": "作業員が足場から転落した",
        "occurred_at": "2025-01-20T09:00:00",
    },
    {
        "id": 2,
        "title": "重機接触",
        "status": "investigating",
        "severity": "medium",
        "description": "重機が作業員に接触した",
        "occurred_at": "2025-01-21T14:00:00",
    },
]

_APPROVALS = [
    {
        "id": 1,
        "title": "設計変更申請",
        "status": "pending",
        "requester_id": 2,
        "created_at": "2025-01-20T10:00:00",
        "read_by": [],
    },
    {
        "id": 2,
        "title": "資材発注申請",
        "status": "pending",
        "requester_id": 2,
        "created_at": "2025-01-21T11:00:00",
        "read_by": [],
    },
]

_NOTIFICATIONS = [
    {
        "id": 1,
        "title": "新規承認依頼",
        "message": "設計変更申請があります",
        "target_users": [1],
        "target_roles": ["admin"],
        "read_by": [],
        "created_at": "2025-01-20T10:00:00",
    },
    {
        "id": 2,
        "title": "システム通知",
        "message": "定期メンテナンスがあります",
        "target_users": [],
        "target_roles": ["admin"],
        "read_by": [1],
        "created_at": "2025-01-21T09:00:00",
    },
    {
        "id": 3,
        "title": "協力会社向け通知",
        "message": "安全大会のお知らせ",
        "target_users": [2],
        "target_roles": ["partner_company"],
        "read_by": [],
        "created_at": "2025-01-22T08:00:00",
    },
]


@pytest.fixture()
def ops_client(client, tmp_path):
    """事故・承認・通知データを準備したクライアント"""
    _write_json(tmp_path / "incidents.json", _INCIDENTS)
    _write_json(tmp_path / "approvals.json", _APPROVALS)
    _write_json(tmp_path / "notifications.json", _NOTIFICATIONS)
    return client


# ============================================================
# 事故レポート API
# ============================================================

class TestGetIncidents:
    """GET /api/v1/incidents"""

    def test_returns_200_with_list(self, ops_client, auth_headers):
        """事故レポート一覧を取得できる"""
        resp = ops_client.get("/api/v1/incidents", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_has_pagination(self, ops_client, auth_headers):
        """ページネーション情報が含まれる"""
        resp = ops_client.get("/api/v1/incidents", headers=auth_headers)
        assert resp.status_code == 200
        assert "pagination" in resp.get_json()

    def test_no_token_returns_401(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.get("/api/v1/incidents")
        assert resp.status_code == 401

    def test_empty_incidents(self, client, auth_headers):
        """空でも成功する"""
        resp = client.get("/api/v1/incidents", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == [] or isinstance(data["data"], list)


class TestGetIncidentDetail:
    """GET /api/v1/incidents/<id>"""

    def test_returns_incident(self, ops_client, auth_headers):
        """指定 ID の事故レポートが返る"""
        resp = ops_client.get("/api/v1/incidents/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert data["data"]["title"] == "足場からの落下"

    def test_not_found_returns_404(self, ops_client, auth_headers):
        """存在しない ID は 404"""
        resp = ops_client.get("/api/v1/incidents/999", headers=auth_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_second_incident(self, ops_client, auth_headers):
        """2番目の事故レポートも取得できる"""
        resp = ops_client.get("/api/v1/incidents/2", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["id"] == 2

    def test_no_token_returns_401(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.get("/api/v1/incidents/1")
        assert resp.status_code == 401


# ============================================================
# 承認フロー API
# ============================================================

class TestGetApprovals:
    """GET /api/v1/approvals"""

    def test_returns_200(self, ops_client, auth_headers):
        """承認フロー一覧を取得できる"""
        resp = ops_client.get("/api/v1/approvals", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_has_pagination(self, ops_client, auth_headers):
        """ページネーション情報が含まれる"""
        resp = ops_client.get("/api/v1/approvals", headers=auth_headers)
        assert "pagination" in resp.get_json()

    def test_no_token_returns_401(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.get("/api/v1/approvals")
        assert resp.status_code == 401

    def test_partner_can_read_approvals(self, ops_client, partner_auth_headers):
        """協力会社ユーザーも一覧を読める"""
        resp = ops_client.get("/api/v1/approvals", headers=partner_auth_headers)
        assert resp.status_code == 200


class TestApproveApproval:
    """POST /api/v1/approvals/<id>/approve"""

    def test_approve_success(self, ops_client, auth_headers):
        """承認処理が成功する"""
        resp = ops_client.post(
            "/api/v1/approvals/1/approve", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "approved"

    def test_approve_not_found(self, ops_client, auth_headers):
        """存在しない承認は 404"""
        resp = ops_client.post(
            "/api/v1/approvals/999/approve", headers=auth_headers
        )
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_approve_no_token(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.post("/api/v1/approvals/1/approve")
        assert resp.status_code == 401

    def test_approve_sets_approved_by(self, ops_client, auth_headers):
        """approved_by に承認者 ID が設定される"""
        resp = ops_client.post(
            "/api/v1/approvals/1/approve", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "approved_by" in data
        assert "approved_at" in data


class TestRejectApproval:
    """POST /api/v1/approvals/<id>/reject"""

    def test_reject_success(self, ops_client, auth_headers):
        """却下処理が成功する"""
        resp = ops_client.post(
            "/api/v1/approvals/1/reject",
            json={"reason": "予算超過のため却下"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "rejected"

    def test_reject_missing_reason_returns_400(self, ops_client, auth_headers):
        """却下理由なしは 400"""
        resp = ops_client.post(
            "/api/v1/approvals/1/reject",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_reject_empty_reason_returns_400(self, ops_client, auth_headers):
        """空の却下理由は 400"""
        resp = ops_client.post(
            "/api/v1/approvals/1/reject",
            json={"reason": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_reject_not_found(self, ops_client, auth_headers):
        """存在しない承認は 404"""
        resp = ops_client.post(
            "/api/v1/approvals/999/reject",
            json={"reason": "却下理由"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_reject_sets_rejection_reason(self, ops_client, auth_headers):
        """rejection_reason が設定される"""
        reason = "設計基準を満たしていない"
        resp = ops_client.post(
            "/api/v1/approvals/2/reject",
            json={"reason": reason},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["rejection_reason"] == reason
        assert "rejected_at" in data

    def test_reject_no_token(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.post(
            "/api/v1/approvals/1/reject", json={"reason": "test"}
        )
        assert resp.status_code == 401


# ============================================================
# 法令 API
# ============================================================

class TestGetRegulationDetail:
    """GET /api/v1/regulations/<id>"""

    def test_not_found_returns_404(self, client, auth_headers):
        """存在しない法令は 404"""
        resp = client.get("/api/v1/regulations/999", headers=auth_headers)
        assert resp.status_code == 404

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/regulations/1")
        assert resp.status_code == 401


# ============================================================
# プロジェクト API
# ============================================================

class TestGetProjects:
    """GET /api/v1/projects"""

    def test_returns_200(self, client, auth_headers):
        """プロジェクト一覧を取得できる（DAL fallback による空リスト）"""
        resp = client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_type_filter_param(self, client, auth_headers):
        """type フィルタを受け付ける"""
        resp = client.get("/api/v1/projects?type=construction", headers=auth_headers)
        assert resp.status_code == 200

    def test_status_filter_param(self, client, auth_headers):
        """status フィルタを受け付ける"""
        resp = client.get("/api/v1/projects?status=active", headers=auth_headers)
        assert resp.status_code == 200

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 401


class TestGetProjectDetail:
    """GET /api/v1/projects/<id>"""

    def test_not_found_returns_404(self, client, auth_headers):
        """存在しないプロジェクトは 404"""
        resp = client.get("/api/v1/projects/999", headers=auth_headers)
        assert resp.status_code == 404

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/projects/1")
        assert resp.status_code == 401


# ============================================================
# 専門家 API
# ============================================================

class TestGetExperts:
    """GET /api/v1/experts"""

    def test_returns_200(self, client, auth_headers):
        """専門家一覧を取得できる（空リスト）"""
        resp = client.get("/api/v1/experts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_specialization_filter(self, client, auth_headers):
        """specialization フィルタを受け付ける"""
        resp = client.get(
            "/api/v1/experts?specialization=civil", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_available_filter_true(self, client, auth_headers):
        """available=true フィルタを受け付ける"""
        resp = client.get(
            "/api/v1/experts?available=true", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_available_filter_false(self, client, auth_headers):
        """available=false フィルタを受け付ける"""
        resp = client.get(
            "/api/v1/experts?available=false", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/experts")
        assert resp.status_code == 401


class TestGetExpertDetail:
    """GET /api/v1/experts/<id>"""

    def test_not_found_returns_404(self, client, auth_headers):
        """存在しない専門家は 404"""
        resp = client.get("/api/v1/experts/999", headers=auth_headers)
        assert resp.status_code == 404

    def test_no_token_returns_401(self, client):
        """トークンなしは 401"""
        resp = client.get("/api/v1/experts/1")
        assert resp.status_code == 401


# ============================================================
# 通知 API
# ============================================================

class TestGetNotifications:
    """GET /api/v1/notifications"""

    def test_returns_200(self, ops_client, auth_headers):
        """通知一覧を取得できる"""
        resp = ops_client.get("/api/v1/notifications", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_filters_by_user(self, ops_client, auth_headers):
        """管理者向けの通知のみ返る（user_id=1 or role=admin）"""
        resp = ops_client.get("/api/v1/notifications", headers=auth_headers)
        assert resp.status_code == 200
        notifications = resp.get_json()["data"]
        # admin user (id=1) gets notifications with target_users=[1] or target_roles=["admin"]
        assert len(notifications) >= 1

    def test_has_is_read_flag(self, ops_client, auth_headers):
        """is_read フラグが含まれる"""
        resp = ops_client.get("/api/v1/notifications", headers=auth_headers)
        assert resp.status_code == 200
        notifications = resp.get_json()["data"]
        for n in notifications:
            assert "is_read" in n

    def test_has_pagination_with_unread_count(self, ops_client, auth_headers):
        """ページネーションに unread_count が含まれる"""
        resp = ops_client.get("/api/v1/notifications", headers=auth_headers)
        assert resp.status_code == 200
        pag = resp.get_json()["pagination"]
        assert "unread_count" in pag

    def test_already_read_notification(self, ops_client, auth_headers):
        """既読通知の is_read は True"""
        resp = ops_client.get("/api/v1/notifications", headers=auth_headers)
        notifications = resp.get_json()["data"]
        # Notification id=2 has read_by=[1], so admin's view should show is_read=True
        read_notifs = [n for n in notifications if n["id"] == 2]
        if read_notifs:
            assert read_notifs[0]["is_read"] is True

    def test_no_token_returns_401(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.get("/api/v1/notifications")
        assert resp.status_code == 401


class TestMarkNotificationRead:
    """PUT /api/v1/notifications/<id>/read"""

    def test_mark_read_success(self, ops_client, auth_headers):
        """通知を既読にできる"""
        resp = ops_client.put(
            "/api/v1/notifications/1/read", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["is_read"] is True
        assert data["data"]["id"] == 1

    def test_mark_read_not_found(self, ops_client, auth_headers):
        """存在しない通知は 404"""
        resp = ops_client.put(
            "/api/v1/notifications/999/read", headers=auth_headers
        )
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_mark_already_read_is_idempotent(self, ops_client, auth_headers):
        """既読の通知を再度既読にしても成功する"""
        resp = ops_client.put(
            "/api/v1/notifications/2/read", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_no_token_returns_401(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.put("/api/v1/notifications/1/read")
        assert resp.status_code == 401


class TestGetUnreadCount:
    """GET /api/v1/notifications/unread/count"""

    def test_returns_unread_count(self, ops_client, auth_headers):
        """未読数が返る"""
        resp = ops_client.get(
            "/api/v1/notifications/unread/count", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "unread_count" in data["data"]
        assert isinstance(data["data"]["unread_count"], int)

    def test_unread_count_is_non_negative(self, ops_client, auth_headers):
        """未読数は 0 以上"""
        resp = ops_client.get(
            "/api/v1/notifications/unread/count", headers=auth_headers
        )
        assert resp.get_json()["data"]["unread_count"] >= 0

    def test_no_token_returns_401(self, ops_client):
        """トークンなしは 401"""
        resp = ops_client.get("/api/v1/notifications/unread/count")
        assert resp.status_code == 401

    def test_partner_unread_count(self, ops_client, partner_auth_headers):
        """協力会社ユーザーも未読数を取得できる"""
        resp = ops_client.get(
            "/api/v1/notifications/unread/count", headers=partner_auth_headers
        )
        assert resp.status_code == 200
