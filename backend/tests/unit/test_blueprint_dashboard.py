"""
blueprints/dashboard.py Blueprint ユニットテスト

テスト対象エンドポイント:
  GET /api/v1/sop                  - SOP一覧
  GET /api/v1/sop/<id>             - SOP詳細
  GET /api/v1/sop/<id>/related     - 関連SOP
  GET /api/v1/dashboard/stats      - ダッシュボード統計
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import Config


# ============================================================
# テスト用フィクスチャ
# ============================================================

SAMPLE_SOP = [
    {
        "id": 1,
        "title": "コンクリート打設手順",
        "category": "concrete",
        "version": "1.0",
        "content": "打設前の準備",
        "status": "active",
        "tags": ["concrete", "safety"],
    },
    {
        "id": 2,
        "title": "足場組立手順",
        "category": "scaffold",
        "version": "2.0",
        "content": "足場の組立方法",
        "status": "active",
        "tags": ["scaffold"],
    },
]

SAMPLE_KNOWLEDGE = [
    {"id": 1, "title": "知識1", "status": "published"},
    {"id": 2, "title": "知識2", "status": "published"},
]

SAMPLE_INCIDENTS = [
    {"id": 1, "title": "ヒヤリ1", "status": "reported"},
    {"id": 2, "title": "事故1", "status": "closed"},
]

SAMPLE_APPROVALS = [
    {"id": 1, "title": "承認1", "status": "pending"},
    {"id": 2, "title": "承認2", "status": "approved"},
]


def _write_all(tmp_path, sop=None, knowledge=None, incidents=None, approvals=None):
    def _write(path, data):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _write(tmp_path / "sop.json", sop if sop is not None else SAMPLE_SOP)
    _write(tmp_path / "knowledge.json", knowledge if knowledge is not None else SAMPLE_KNOWLEDGE)
    _write(tmp_path / "incidents.json", incidents if incidents is not None else SAMPLE_INCIDENTS)
    _write(tmp_path / "approvals.json", approvals if approvals is not None else SAMPLE_APPROVALS)
    _write(tmp_path / "access_logs.json", [])
    _write(tmp_path / "notifications.json", [])


@pytest.fixture()
def dashboard_client(tmp_path, monkeypatch):
    """ダッシュボードテスト用クライアント"""
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
            "username": "viewer",
            "password_hash": app_v2.hash_password("viewer123"),
            "full_name": "閲覧者",
            "department": "現場",
            "roles": ["viewer"],
        },
    ]
    (tmp_path / "users.json").write_text(
        json.dumps(users, ensure_ascii=False), encoding="utf-8"
    )

    _write_all(tmp_path)

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def admin_token(dashboard_client):
    """adminユーザーの認証ヘッダー"""
    resp = dashboard_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def viewer_token(dashboard_client):
    """viewerユーザーの認証ヘッダー"""
    resp = dashboard_client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "viewer123"},
    )
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# GET /api/v1/sop
# ============================================================


class TestGetSop:
    def test_list_success(self, dashboard_client, admin_token):
        """認証済みでSOP一覧を取得できる"""
        resp = dashboard_client.get("/api/v1/sop", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2
        assert "pagination" in data

    def test_list_requires_auth(self, dashboard_client):
        """認証なしでは401"""
        resp = dashboard_client.get("/api/v1/sop")
        assert resp.status_code == 401

    def test_empty_sop_list(self, dashboard_client, admin_token, tmp_path):
        """SOPが空の場合は空配列を返す"""
        (tmp_path / "sop.json").write_text("[]", encoding="utf-8")
        resp = dashboard_client.get("/api/v1/sop", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []
        assert data["pagination"]["total_items"] == 0


# ============================================================
# GET /api/v1/sop/<id>
# ============================================================


class TestGetSopDetail:
    def test_detail_found(self, dashboard_client, admin_token):
        """存在するSOPを取得できる"""
        resp = dashboard_client.get("/api/v1/sop/1", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert data["data"]["title"] == "コンクリート打設手順"

    def test_detail_not_found(self, dashboard_client, admin_token):
        """存在しないSOPは404"""
        resp = dashboard_client.get("/api/v1/sop/9999", headers=admin_token)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_detail_requires_auth(self, dashboard_client):
        """認証なしでは401"""
        resp = dashboard_client.get("/api/v1/sop/1")
        assert resp.status_code == 401

    def test_detail_second_item(self, dashboard_client, admin_token):
        """2件目のSOPも正しく取得できる"""
        resp = dashboard_client.get("/api/v1/sop/2", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["category"] == "scaffold"


# ============================================================
# GET /api/v1/sop/<id>/related
# ============================================================


class TestGetRelatedSop:
    def test_related_success(self, dashboard_client, admin_token):
        """関連SOPを取得できる"""
        resp = dashboard_client.get("/api/v1/sop/1/related", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "target_id" in data["data"]
        assert "related_items" in data["data"]
        assert data["data"]["target_id"] == 1

    def test_related_not_found_sop(self, dashboard_client, admin_token):
        """存在しないSOPは404"""
        resp = dashboard_client.get("/api/v1/sop/9999/related", headers=admin_token)
        assert resp.status_code == 404

    def test_related_invalid_limit_too_large(self, dashboard_client, admin_token):
        """limitが20を超えると400"""
        resp = dashboard_client.get(
            "/api/v1/sop/1/related?limit=99", headers=admin_token
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_related_invalid_limit_zero(self, dashboard_client, admin_token):
        """limitが0以下は400"""
        resp = dashboard_client.get(
            "/api/v1/sop/1/related?limit=0", headers=admin_token
        )
        assert resp.status_code == 400

    def test_related_invalid_algorithm(self, dashboard_client, admin_token):
        """不正なalgorithmは400"""
        resp = dashboard_client.get(
            "/api/v1/sop/1/related?algorithm=invalid", headers=admin_token
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_ALGORITHM"

    def test_related_valid_algorithm_tag(self, dashboard_client, admin_token):
        """algorithm=tagは有効"""
        resp = dashboard_client.get(
            "/api/v1/sop/1/related?algorithm=tag", headers=admin_token
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["algorithm"] == "tag"

    def test_related_requires_auth(self, dashboard_client):
        """認証なしでは401"""
        resp = dashboard_client.get("/api/v1/sop/1/related")
        assert resp.status_code == 401


# ============================================================
# GET /api/v1/dashboard/stats
# ============================================================


class TestGetDashboardStats:
    def test_stats_success(self, dashboard_client, admin_token):
        """認証済みで統計情報を取得できる"""
        resp = dashboard_client.get("/api/v1/dashboard/stats", headers=admin_token)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "kpis" in data["data"]
        assert "counts" in data["data"]

    def test_stats_requires_auth(self, dashboard_client):
        """認証なしでは401"""
        resp = dashboard_client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 401

    def test_stats_counts_correct(self, dashboard_client, admin_token):
        """カウントが正しい"""
        resp = dashboard_client.get("/api/v1/dashboard/stats", headers=admin_token)
        data = resp.get_json()
        counts = data["data"]["counts"]
        assert counts["total_knowledge"] == 2  # SAMPLE_KNOWLEDGE
        assert counts["total_sop"] == 2  # SAMPLE_SOP

    def test_stats_has_last_sync_time(self, dashboard_client, admin_token):
        """last_sync_time フィールドが存在する"""
        resp = dashboard_client.get("/api/v1/dashboard/stats", headers=admin_token)
        data = resp.get_json()
        assert "last_sync_time" in data["data"]

    def test_stats_viewer_can_access(self, dashboard_client, viewer_token):
        """viewerも統計情報にアクセスできる（jwt_required のみ）"""
        resp = dashboard_client.get("/api/v1/dashboard/stats", headers=viewer_token)
        assert resp.status_code == 200
