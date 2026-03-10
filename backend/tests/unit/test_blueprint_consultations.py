"""
consultations Blueprint ユニットテスト (Phase J-2)

/api/v1/consultations/* エンドポイントのテスト。
conftest.py の client / auth_headers / expert_auth_headers フィクスチャを活用。
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


@pytest.fixture()
def consultation_client(tmp_path, monkeypatch):
    """相談データを含むテスト用クライアント"""
    import app_v2
    import app_helpers

    monkeypatch.setattr(app_helpers, "CACHE_ENABLED", False)
    monkeypatch.setattr(Config, "DATA_DIR", str(tmp_path))

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
            "full_name": "管理者 太郎",
            "department": "総務部",
            "roles": ["admin"],
        },
        {
            "id": 2,
            "username": "expert",
            "password_hash": app_v2.hash_password("expert123"),
            "full_name": "専門家 花子",
            "department": "技術部",
            "roles": ["expert"],
        },
    ]

    consultations = [
        {
            "id": 1,
            "title": "テスト相談",
            "question": "テスト質問内容",
            "category": "safety",
            "priority": "通常",
            "status": "pending",
            "requester_id": 1,
            "requester": "管理者 太郎",
            "expert_id": None,
            "expert": None,
            "project": None,
            "tags": ["test"],
            "views": 0,
            "follower_count": 0,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
            "answered_at": None,
        }
    ]

    def _write(path, data):
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    _write(tmp_path / "users.json", users)
    _write(tmp_path / "consultations.json", consultations)
    _write(tmp_path / "access_logs.json", [])
    _write(tmp_path / "notifications.json", [])
    _write(tmp_path / "knowledge.json", [])
    _write(tmp_path / "sop.json", [])

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def admin_headers(consultation_client):
    """admin ユーザーの JWT 認証ヘッダー"""
    resp = consultation_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def expert_headers(consultation_client):
    """expert ユーザーの JWT 認証ヘッダー"""
    resp = consultation_client.post(
        "/api/v1/auth/login",
        json={"username": "expert", "password": "expert123"},
    )
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# GET /api/v1/consultations
# ============================================================


class TestGetConsultations:
    """相談一覧取得"""

    def test_list_success(self, consultation_client, admin_headers):
        """認証済みで相談一覧を取得できる"""
        resp = consultation_client.get(
            "/api/v1/consultations", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "pagination" in data

    def test_list_requires_auth(self, consultation_client):
        """認証なしでは 401"""
        resp = consultation_client.get("/api/v1/consultations")
        assert resp.status_code == 401

    def test_list_contains_seeded_item(self, consultation_client, admin_headers):
        """初期データの相談が含まれる"""
        resp = consultation_client.get(
            "/api/v1/consultations", headers=admin_headers
        )
        data = resp.get_json()
        titles = [c["title"] for c in data["data"]]
        assert "テスト相談" in titles

    def test_list_filter_by_category(self, consultation_client, admin_headers):
        """カテゴリフィルタが機能する"""
        resp = consultation_client.get(
            "/api/v1/consultations?category=safety", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert all(c["category"] == "safety" for c in data["data"])

    def test_list_filter_nonexistent_category(
        self, consultation_client, admin_headers
    ):
        """存在しないカテゴリでは空リスト"""
        resp = consultation_client.get(
            "/api/v1/consultations?category=nonexistent",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []

    def test_list_filter_by_status(self, consultation_client, admin_headers):
        """ステータスフィルタが機能する"""
        resp = consultation_client.get(
            "/api/v1/consultations?status=pending", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert all(c["status"] == "pending" for c in data["data"])

    def test_list_pagination_structure(self, consultation_client, admin_headers):
        """ページネーション情報が返される"""
        resp = consultation_client.get(
            "/api/v1/consultations?page=1&per_page=10", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        pagination = data["pagination"]
        assert "total_items" in pagination
        assert "total_pages" in pagination
        assert "current_page" in pagination
        assert "per_page" in pagination


# ============================================================
# GET /api/v1/consultations/<id>
# ============================================================


class TestGetConsultationDetail:
    """相談詳細取得"""

    def test_detail_success(self, consultation_client, admin_headers):
        """存在する相談の詳細を取得できる"""
        resp = consultation_client.get(
            "/api/v1/consultations/1", headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1

    def test_detail_not_found(self, consultation_client, admin_headers):
        """存在しない相談は 404"""
        resp = consultation_client.get(
            "/api/v1/consultations/9999", headers=admin_headers
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_detail_increments_views(self, consultation_client, admin_headers):
        """詳細取得で閲覧数がインクリメントされる"""
        resp1 = consultation_client.get(
            "/api/v1/consultations/1", headers=admin_headers
        )
        views_before = resp1.get_json()["data"]["views"]

        resp2 = consultation_client.get(
            "/api/v1/consultations/1", headers=admin_headers
        )
        views_after = resp2.get_json()["data"]["views"]

        assert views_after == views_before + 1

    def test_detail_requires_auth(self, consultation_client):
        """認証なしでは 401"""
        resp = consultation_client.get("/api/v1/consultations/1")
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/consultations
# ============================================================


class TestCreateConsultation:
    """相談作成"""

    def test_create_success(self, consultation_client, admin_headers):
        """相談を新規作成できる"""
        resp = consultation_client.post(
            "/api/v1/consultations",
            json={
                "title": "新しい相談",
                "question": "新しい質問内容の詳細説明をここに記載します",
                "category": "品質管理",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "新しい相談"
        assert data["data"]["status"] == "pending"

    def test_create_requires_auth(self, consultation_client):
        """認証なしでは 401"""
        resp = consultation_client.post(
            "/api/v1/consultations",
            json={"title": "相談", "question": "質問", "category": "safety"},
        )
        assert resp.status_code == 401

    def test_create_sets_requester_id(self, consultation_client, admin_headers):
        """作成者の requester_id が設定される"""
        resp = consultation_client.post(
            "/api/v1/consultations",
            json={
                "title": "相談タイトル",
                "question": "相談内容の詳細説明をここに記入してください",
                "category": "安全対策",
            },
            headers=admin_headers,
        )
        data = resp.get_json()
        assert data["data"]["requester_id"] == 1

    def test_create_auto_increments_id(self, consultation_client, admin_headers):
        """新規相談の ID が自動採番される"""
        resp = consultation_client.post(
            "/api/v1/consultations",
            json={"title": "相談2", "question": "質問内容の詳細はここに記入します", "category": "技術相談"},
            headers=admin_headers,
        )
        data = resp.get_json()
        assert data["data"]["id"] == 2  # 既存 id=1 の次


# ============================================================
# PUT /api/v1/consultations/<id>
# ============================================================


class TestUpdateConsultation:
    """相談更新"""

    def test_update_success_by_owner(self, consultation_client, admin_headers):
        """相談投稿者が更新できる"""
        resp = consultation_client.put(
            "/api/v1/consultations/1",
            json={"title": "更新後タイトル"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["title"] == "更新後タイトル"

    def test_update_not_found(self, consultation_client, admin_headers):
        """存在しない相談は 404"""
        resp = consultation_client.put(
            "/api/v1/consultations/9999",
            json={"title": "タイトル"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_update_forbidden_by_non_owner(
        self, consultation_client, expert_headers
    ):
        """非所有者（管理者でない）は 403"""
        resp = consultation_client.put(
            "/api/v1/consultations/1",
            json={"title": "不正更新"},
            headers=expert_headers,
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "FORBIDDEN"

    def test_update_empty_body_returns_400(
        self, consultation_client, admin_headers
    ):
        """リクエストボディなしは 400"""
        resp = consultation_client.put(
            "/api/v1/consultations/1",
            data="",
            content_type="application/json",
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_update_requires_auth(self, consultation_client):
        """認証なしでは 401"""
        resp = consultation_client.put(
            "/api/v1/consultations/1", json={"title": "test"}
        )
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/consultations/<id>/answers
# ============================================================


class TestPostConsultationAnswer:
    """回答投稿"""

    def test_answer_success(self, consultation_client, expert_headers):
        """回答を投稿できる"""
        resp = consultation_client.post(
            "/api/v1/consultations/1/answers",
            json={"content": "回答内容の詳細説明をここに記載します"},
            headers=expert_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["content"] == "回答内容の詳細説明をここに記載します"

    def test_answer_not_found(self, consultation_client, expert_headers):
        """存在しない相談に回答は 404"""
        resp = consultation_client.post(
            "/api/v1/consultations/9999/answers",
            json={"content": "存在しない相談への回答テスト"},
            headers=expert_headers,
        )
        assert resp.status_code == 404

    def test_answer_updates_status_to_answered(
        self, consultation_client, expert_headers, admin_headers
    ):
        """回答投稿で相談ステータスが answered になる"""
        consultation_client.post(
            "/api/v1/consultations/1/answers",
            json={"content": "回答内容の詳細説明をここに記載します"},
            headers=expert_headers,
        )
        detail_resp = consultation_client.get(
            "/api/v1/consultations/1", headers=admin_headers
        )
        assert detail_resp.get_json()["data"]["status"] == "answered"

    def test_answer_requires_auth(self, consultation_client):
        """認証なしでは 401"""
        resp = consultation_client.post(
            "/api/v1/consultations/1/answers",
            json={"content": "回答"},
        )
        assert resp.status_code == 401

    def test_answer_sets_expert_info(self, consultation_client, expert_headers):
        """回答者の情報が設定される"""
        resp = consultation_client.post(
            "/api/v1/consultations/1/answers",
            json={"content": "詳細な回答内容をここに記載します（専門的な知見）"},
            headers=expert_headers,
        )
        data = resp.get_json()
        assert data["data"]["expert"] == "専門家 花子"
        assert data["data"]["expert_id"] == 2
