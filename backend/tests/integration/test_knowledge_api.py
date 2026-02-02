"""
ナレッジCRUD APIの統合テスト
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def _write_json(path, data):
    """JSONファイル書き込みヘルパー"""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def client(tmp_path):
    """テストクライアント（conftest.pyと同等だが独立）"""
    import app_v2

    app = app_v2.app
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(tmp_path)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app_v2.limiter.enabled = False

    # 管理者ユーザー
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
            "username": "viewer",
            "password_hash": app_v2.hash_password("viewer123"),
            "full_name": "Viewer User",
            "department": "Partner",
            "roles": ["partner_company"],
        },
    ]

    # 初期ナレッジデータ
    knowledge = [
        {
            "id": 1,
            "title": "Test Knowledge 1",
            "summary": "Test summary 1",
            "content": "Test content 1",
            "category": "safety",
            "tags": ["test", "safety"],
            "status": "approved",
        },
        {
            "id": 2,
            "title": "Test Knowledge 2",
            "summary": "Test summary 2",
            "content": "Test content 2",
            "category": "quality",
            "tags": ["quality"],
            "status": "draft",
        },
    ]

    _write_json(tmp_path / "users.json", users)
    _write_json(tmp_path / "knowledge.json", knowledge)
    _write_json(tmp_path / "access_logs.json", [])
    _write_json(tmp_path / "notifications.json", [])

    with app.test_client() as test_client:
        yield test_client


def _login(client, username="admin", password="admin123"):
    """ログインヘルパー"""
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    return response.get_json()["data"]["access_token"]


class TestKnowledgeList:
    """ナレッジ一覧取得のテスト"""

    def test_get_knowledge_list_returns_all_items(self, client):
        """全ナレッジ一覧を取得"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["pagination"]["total_items"] == 2

    def test_get_knowledge_requires_authentication(self, client):
        """認証が必要"""
        response = client.get("/api/v1/knowledge")

        assert response.status_code == 401

    def test_filter_by_category(self, client):
        """カテゴリでフィルタリング"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?category=safety",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 1
        assert data["data"][0]["category"] == "safety"

    def test_filter_by_tags(self, client):
        """タグでフィルタリング"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?tags=safety",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 1
        assert "safety" in data["data"][0]["tags"]

    def test_search_by_keyword(self, client):
        """キーワード検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?search=Knowledge 1",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 1
        assert "Knowledge 1" in data["data"][0]["title"]

    def test_search_with_highlight(self, client):
        """ハイライト付き検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?search=Test&highlight=true",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) >= 1
        # ハイライトマークが含まれる
        assert (
            "<mark>" in data["data"][0]["title"]
            or "<mark>" in data["data"][0]["summary"]
        )

    def test_search_returns_relevance_score(self, client):
        """検索結果に関連性スコアが含まれる"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?search=Test",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) >= 1
        assert "relevance_score" in data["data"][0]
        assert "matched_fields" in data["data"][0]


class TestKnowledgeDetail:
    """ナレッジ詳細取得のテスト"""

    def test_get_knowledge_detail_success(self, client):
        """ナレッジ詳細を正常に取得"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge/1", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert data["data"]["title"] == "Test Knowledge 1"

    def test_get_nonexistent_knowledge_returns_404(self, client):
        """存在しないナレッジは404を返す"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge/999", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False

    def test_get_knowledge_detail_requires_auth(self, client):
        """認証が必要"""
        response = client.get("/api/v1/knowledge/1")

        assert response.status_code == 401


class TestKnowledgeCreate:
    """ナレッジ作成のテスト"""

    def test_create_knowledge_success(self, client):
        """ナレッジ作成成功"""
        token = _login(client)

        new_knowledge = {
            "title": "新規ナレッジ",
            "summary": "新規概要",
            "content": "新規コンテンツの詳細内容",
            "category": "施工計画",
            "tags": ["new", "test"],
            "owner": "admin",
        }

        response = client.post(
            "/api/v1/knowledge",
            json=new_knowledge,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "新規ナレッジ"
        assert data["data"]["id"] == 3  # 既存が1,2なので3になる
        assert data["data"]["status"] == "draft"

    def test_create_knowledge_requires_auth(self, client):
        """認証が必要"""
        new_knowledge = {
            "title": "新規ナレッジ",
            "summary": "新規概要",
            "content": "新規コンテンツ",
            "category": "施工計画",
        }

        response = client.post("/api/v1/knowledge", json=new_knowledge)

        assert response.status_code == 401

    def test_create_knowledge_validation_error_missing_title(self, client):
        """タイトル未指定でバリデーションエラー"""
        token = _login(client)

        new_knowledge = {
            "summary": "新規概要",
            "content": "新規コンテンツ",
            "category": "施工計画",
        }

        response = client.post(
            "/api/v1/knowledge",
            json=new_knowledge,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "VALIDATION_ERROR" in data["error"]["code"]

    def test_create_knowledge_validation_error_invalid_category(self, client):
        """無効なカテゴリでバリデーションエラー"""
        token = _login(client)

        new_knowledge = {
            "title": "新規ナレッジ",
            "summary": "新規概要",
            "content": "新規コンテンツ",
            "category": "無効なカテゴリ",
        }

        response = client.post(
            "/api/v1/knowledge",
            json=new_knowledge,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_create_knowledge_sets_default_values(self, client):
        """デフォルト値が設定される"""
        token = _login(client)

        new_knowledge = {
            "title": "新規ナレッジ",
            "summary": "新規概要",
            "content": "新規コンテンツの詳細",
            "category": "施工計画",
        }

        response = client.post(
            "/api/v1/knowledge",
            json=new_knowledge,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["data"]["priority"] == "medium"
        assert data["data"]["status"] == "draft"
        assert "created_at" in data["data"]
        assert "updated_at" in data["data"]

    def test_create_knowledge_creates_notification(self, client, tmp_path):
        """ナレッジ作成時に通知が作成される"""
        token = _login(client)

        new_knowledge = {
            "title": "通知テストナレッジ",
            "summary": "通知確認用",
            "content": "通知コンテンツ",
            "category": "施工計画",
            "owner": "テスト太郎",
        }

        response = client.post(
            "/api/v1/knowledge",
            json=new_knowledge,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201

        # 通知ファイルを確認
        notifications_file = tmp_path / "notifications.json"
        with open(notifications_file, "r", encoding="utf-8") as f:
            notifications = json.load(f)

        assert len(notifications) >= 1
        assert notifications[-1]["type"] == "approval_required"


class TestKnowledgePermissions:
    """ナレッジAPIの権限テスト"""

    def test_partner_can_read_knowledge(self, client):
        """パートナー（閲覧権限のみ）でもナレッジを読める"""
        token = _login(client, "viewer", "viewer123")

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_partner_cannot_create_knowledge(self, client):
        """パートナーはナレッジを作成できない"""
        token = _login(client, "viewer", "viewer123")

        new_knowledge = {
            "title": "新規ナレッジ",
            "summary": "新規概要",
            "content": "新規コンテンツ",
            "category": "施工計画",
        }

        response = client.post(
            "/api/v1/knowledge",
            json=new_knowledge,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "FORBIDDEN" in data["error"]["code"]


class TestAccessLogging:
    """アクセスログ記録のテスト"""

    def test_list_access_is_logged(self, client, tmp_path):
        """一覧アクセスがログに記録される"""
        token = _login(client)

        client.get("/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"})

        # ログファイルを確認
        logs_file = tmp_path / "access_logs.json"
        with open(logs_file, "r", encoding="utf-8") as f:
            logs = json.load(f)

        # ログイン + ナレッジリストの2件（ログインでもlog_accessが呼ばれる）
        knowledge_logs = [l for l in logs if l["action"] == "knowledge.list"]
        assert len(knowledge_logs) >= 1
        assert knowledge_logs[0]["resource"] == "knowledge"

    def test_detail_access_is_logged(self, client, tmp_path):
        """詳細アクセスがログに記録される"""
        token = _login(client)

        client.get("/api/v1/knowledge/1", headers={"Authorization": f"Bearer {token}"})

        # ログファイルを確認
        logs_file = tmp_path / "access_logs.json"
        with open(logs_file, "r", encoding="utf-8") as f:
            logs = json.load(f)

        view_logs = [l for l in logs if l["action"] == "knowledge.view"]
        assert len(view_logs) >= 1
        assert view_logs[0]["resource_id"] == 1

    def test_create_access_is_logged(self, client, tmp_path):
        """作成アクセスがログに記録される"""
        token = _login(client)

        new_knowledge = {
            "title": "新規ナレッジ",
            "summary": "新規概要",
            "content": "新規コンテンツの詳細",
            "category": "施工計画",
        }

        client.post(
            "/api/v1/knowledge",
            json=new_knowledge,
            headers={"Authorization": f"Bearer {token}"},
        )

        # ログファイルを確認
        logs_file = tmp_path / "access_logs.json"
        with open(logs_file, "r", encoding="utf-8") as f:
            logs = json.load(f)

        create_logs = [l for l in logs if l["action"] == "knowledge.create"]
        assert len(create_logs) >= 1
