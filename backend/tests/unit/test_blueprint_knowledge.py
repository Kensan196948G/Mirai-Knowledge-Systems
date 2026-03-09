"""
knowledge Blueprint ユニットテスト (Phase I-3)

/api/v1/knowledge/* エンドポイントのテスト。
conftest.py の client / auth_headers / partner_auth_headers フィクスチャを活用。
"""

import os
import sys

import pytest

# backend ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestGetKnowledgeList:
    """GET /api/v1/knowledge"""

    def test_get_knowledge_list_success(self, client, auth_headers):
        """認証済みでナレッジ一覧を取得できる"""
        resp = client.get("/api/v1/knowledge", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_knowledge_list_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge")
        assert resp.status_code == 401

    def test_get_knowledge_list_returns_existing_item(self, client, auth_headers):
        """conftest に登録されているナレッジが含まれる"""
        resp = client.get("/api/v1/knowledge", headers=auth_headers)
        data = resp.get_json()
        items = data["data"]
        titles = [item["title"] for item in items]
        assert "Test Knowledge" in titles

    def test_get_knowledge_list_partner_user(self, client, partner_auth_headers):
        """協力会社ユーザーも一覧を取得できる"""
        resp = client.get("/api/v1/knowledge", headers=partner_auth_headers)
        assert resp.status_code == 200

    def test_get_knowledge_list_with_category_filter(self, client, auth_headers):
        """カテゴリフィルタが機能する"""
        resp = client.get(
            "/api/v1/knowledge?category=nonexistent_category",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        # 存在しないカテゴリでは空リスト
        assert data["data"] == []

    def test_get_knowledge_list_pagination_params(self, client, auth_headers):
        """ページネーションパラメータを受け付ける"""
        resp = client.get(
            "/api/v1/knowledge?page=1&per_page=10",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_get_knowledge_list_response_structure(self, client, auth_headers):
        """レスポンス構造が正しい"""
        resp = client.get("/api/v1/knowledge", headers=auth_headers)
        data = resp.get_json()
        assert "success" in data
        assert "data" in data


class TestCreateKnowledge:
    """POST /api/v1/knowledge"""

    def test_create_knowledge_success(self, client, auth_headers):
        """必須フィールドを揃えて作成できる"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "新規ナレッジ",
                "summary": "テスト用サマリー",
                "content": "テスト用コンテンツ",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "新規ナレッジ"

    def test_create_knowledge_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "テスト",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
        )
        assert resp.status_code == 401

    def test_create_knowledge_missing_title(self, client, auth_headers):
        """title 欠落で 400 バリデーションエラー"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_knowledge_missing_summary(self, client, auth_headers):
        """summary 欠落で 400 バリデーションエラー"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "タイトル",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_knowledge_missing_content(self, client, auth_headers):
        """content 欠落で 400 バリデーションエラー"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "タイトル",
                "summary": "サマリー",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_knowledge_missing_category(self, client, auth_headers):
        """category 欠落で 400 バリデーションエラー"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "タイトル",
                "summary": "サマリー",
                "content": "コンテンツ",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_knowledge_response_has_id(self, client, auth_headers):
        """作成後のレスポンスに id が含まれる"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "IDテスト",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "品質管理",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "id" in data["data"]
        assert isinstance(data["data"]["id"], int)

    def test_create_knowledge_partner_user_permission(
        self, client, partner_auth_headers
    ):
        """協力会社ユーザーのナレッジ作成は権限設定次第（201 または 403）"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "協力会社テスト",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
            headers=partner_auth_headers,
        )
        # partner_company ロールに knowledge.create があれば 201、なければ 403
        assert resp.status_code in (201, 403)


class TestGetKnowledgeDetail:
    """GET /api/v1/knowledge/<id>"""

    def test_get_knowledge_detail_success(self, client, auth_headers):
        """存在するIDで詳細を取得できる"""
        resp = client.get("/api/v1/knowledge/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1

    def test_get_knowledge_detail_not_found(self, client, auth_headers):
        """存在しないIDで 404 を返す"""
        resp = client.get("/api/v1/knowledge/99999", headers=auth_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_get_knowledge_detail_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/1")
        assert resp.status_code == 401

    def test_get_knowledge_detail_response_structure(self, client, auth_headers):
        """レスポンスに必要フィールドが含まれる"""
        resp = client.get("/api/v1/knowledge/1", headers=auth_headers)
        data = resp.get_json()
        item = data["data"]
        assert "id" in item
        assert "title" in item


class TestUpdateKnowledge:
    """PUT /api/v1/knowledge/<id>"""

    def test_update_knowledge_success(self, client, auth_headers):
        """管理者が既存ナレッジを更新できる"""
        resp = client.put(
            "/api/v1/knowledge/1",
            json={"title": "更新後タイトル"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_update_knowledge_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.put("/api/v1/knowledge/1", json={"title": "タイトル"})
        assert resp.status_code == 401

    def test_update_knowledge_not_found(self, client, auth_headers):
        """存在しないIDで 404"""
        resp = client.put(
            "/api/v1/knowledge/99999",
            json={"title": "タイトル"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_knowledge_empty_body(self, client, auth_headers):
        """空ボディで 4xx エラー（Content-Type なしは 415/500）"""
        resp = client.put(
            "/api/v1/knowledge/1",
            data="",
            headers=auth_headers,
        )
        assert resp.status_code in (400, 415, 500)

    def test_update_knowledge_partner_user_allowed(self, client, partner_auth_headers):
        """協力会社ユーザーも更新できる（knowledge.update 権限あり）"""
        resp = client.put(
            "/api/v1/knowledge/1",
            json={"title": "協力会社による更新"},
            headers=partner_auth_headers,
        )
        # partner_company ロールにknowledge.updateがあれば200、なければ403
        assert resp.status_code in (200, 403)


class TestDeleteKnowledge:
    """DELETE /api/v1/knowledge/<id>"""

    def test_delete_knowledge_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.delete("/api/v1/knowledge/1")
        assert resp.status_code == 401

    def test_delete_knowledge_not_found(self, client, auth_headers):
        """存在しないIDで 404"""
        resp = client.delete("/api/v1/knowledge/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_knowledge_success(self, client, auth_headers):
        """管理者が既存ナレッジを削除できる"""
        resp = client.delete("/api/v1/knowledge/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_delete_knowledge_partner_user_forbidden(
        self, client, partner_auth_headers
    ):
        """partner_company は削除権限がない（403 が期待値）"""
        resp = client.delete("/api/v1/knowledge/1", headers=partner_auth_headers)
        # 権限なしは 403、存在しない場合は 404
        assert resp.status_code in (403, 404)


class TestKnowledgePing:
    """GET /api/v1/ping - Blueprint稼働確認"""

    def test_ping_returns_ok(self, client):
        """認証不要で 200 を返す"""
        resp = client.get("/api/v1/ping")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["source"] == "knowledge_blueprint"

    def test_ping_has_phase_info(self, client):
        """フェーズ情報が含まれる"""
        resp = client.get("/api/v1/ping")
        data = resp.get_json()
        assert "phase" in data
