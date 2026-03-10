"""
N+1クエリ最適化テスト

関連ナレッジ取得において、同一リクエスト内での load_data 呼び出し回数を
最小化するリクエストスコープキャッシュ（g._knowledge_list_cache）の効果を検証。
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@pytest.fixture()
def client(tmp_path):
    """テストクライアント"""
    import app_v2

    app = app_v2.app
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(tmp_path)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app_v2.limiter.enabled = False

    users = [
        {
            "id": 1,
            "username": "admin",
            "password_hash": app_v2.hash_password("admin123"),
            "full_name": "Admin User",
            "department": "Admin",
            "roles": ["admin"],
        }
    ]
    (tmp_path / "users.json").write_text(
        json.dumps(users, ensure_ascii=False), encoding="utf-8"
    )

    knowledge_data = [
        {
            "id": i + 1,
            "title": f"ナレッジ{i+1}",
            "summary": f"要約{i+1}",
            "content": f"内容{i+1}" + "テスト" * 20,
            "category": "施工管理",
            "tags": [f"tag{j}" for j in range(3)],
            "status": "published",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "created_by": 1,
            "views": i * 5,
        }
        for i in range(50)
    ]
    (tmp_path / "knowledge.json").write_text(
        json.dumps(knowledge_data, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "access_logs.json").write_text("[]", encoding="utf-8")
    (tmp_path / "notifications.json").write_text("[]", encoding="utf-8")

    with app.test_client() as test_client:
        yield test_client


def _login(client):
    resp = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    )
    return resp.get_json()["data"]["access_token"]


class TestN1Optimization:
    """N+1クエリ最適化の検証テスト"""

    def test_related_knowledge_single_load_data_call(self, client):
        """
        get_related_knowledge は同一リクエスト内で load_data を1回のみ呼ぶ

        g._knowledge_list_cache によってリクエストスコープキャッシュが機能しているか確認。
        """
        token = _login(client)

        from app_helpers import load_data as original_load_data

        call_count = {"n": 0}

        def counting_load_data(filename):
            if filename == "knowledge.json":
                call_count["n"] += 1
            return original_load_data(filename)

        with patch("blueprints.knowledge.load_data", side_effect=counting_load_data):
            response = client.get(
                "/api/v1/knowledge/1/related",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        # リクエストスコープキャッシュにより knowledge.json の読み込みは1回のみ
        assert call_count["n"] <= 1, (
            f"knowledge.json が {call_count['n']} 回読み込まれました（期待: 1回以下）"
        )

    def test_knowledge_search_uses_load_data_once(self, client):
        """
        /knowledge/search は knowledge.json を1回だけ読み込む
        """
        token = _login(client)

        from app_helpers import load_data as original_load_data

        call_count = {"n": 0}

        def counting_load_data(filename):
            if filename == "knowledge.json":
                call_count["n"] += 1
            return original_load_data(filename)

        with patch("blueprints.knowledge.load_data", side_effect=counting_load_data):
            response = client.get(
                "/api/v1/knowledge/search?query=テスト",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["total"] > 0
        assert call_count["n"] == 1, (
            f"knowledge.json が {call_count['n']} 回読み込まれました（期待: 1回）"
        )

    def test_search_returns_correct_results(self, client):
        """
        検索結果が正しく返されること（content に「テスト」が含まれるので全件マッチ）
        """
        token = _login(client)
        response = client.get(
            "/api/v1/knowledge/search?query=テスト",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["total"] == 50
        assert len(data["data"]["results"]) == 20  # デフォルト per_page=20

    def test_search_pagination(self, client):
        """ページネーションが正しく動作すること"""
        token = _login(client)

        resp1 = client.get(
            "/api/v1/knowledge/search?query=テスト&page=1&per_page=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp2 = client.get(
            "/api/v1/knowledge/search?query=テスト&page=2&per_page=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        ids1 = {k["id"] for k in resp1.get_json()["data"]["results"]}
        ids2 = {k["id"] for k in resp2.get_json()["data"]["results"]}

        # ページ間でデータが重複しない
        assert ids1.isdisjoint(ids2), "ページ1とページ2でIDが重複しています"

    def test_search_empty_query_returns_400(self, client):
        """空クエリは 400 を返すこと"""
        token = _login(client)
        response = client.get(
            "/api/v1/knowledge/search",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    def test_search_whitespace_query_returns_400(self, client):
        """空白のみクエリは 400 を返すこと"""
        token = _login(client)
        response = client.get(
            "/api/v1/knowledge/search?query=%20%20%20",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
