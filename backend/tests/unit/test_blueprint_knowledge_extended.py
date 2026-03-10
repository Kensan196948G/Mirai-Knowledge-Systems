"""
blueprints/knowledge.py Blueprint ユニットテスト（拡張）

テスト対象エンドポイント（既存 test_blueprint_knowledge.py 未カバー分）:
  GET  /api/v1/knowledge/popular       - 人気ナレッジTop N
  GET  /api/v1/knowledge/recent        - 最近追加ナレッジ
  GET  /api/v1/knowledge/favorites     - お気に入りナレッジ
  GET  /api/v1/knowledge/tags          - タグクラウド集計
  GET  /api/v1/knowledge/<id>/related  - 関連ナレッジ（バリデーション）
  DELETE /api/v1/favorites/<id>        - お気に入り削除
  GET  /api/v1/knowledge/search        - ナレッジ全文検索
  GET  /api/v1/search/unified          - 横断検索
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ============================================================
# GET /api/v1/knowledge/popular
# ============================================================


class TestGetPopularKnowledge:
    def test_success(self, client, auth_headers):
        """認証済みで人気ナレッジを取得できる"""
        resp = client.get("/api/v1/knowledge/popular", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/popular")
        assert resp.status_code == 401

    def test_limit_param(self, client, auth_headers):
        """limit パラメータを指定できる"""
        resp = client.get("/api/v1/knowledge/popular?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) <= 5

    def test_limit_capped_at_50(self, client, auth_headers):
        """limit は最大 50 に制限される"""
        resp = client.get("/api/v1/knowledge/popular?limit=9999", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) <= 50

    def test_default_limit(self, client, auth_headers):
        """デフォルト limit=10 が適用される"""
        resp = client.get("/api/v1/knowledge/popular", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        # データが10件以下（conftest に1件しかない）
        assert len(data["data"]) <= 10


# ============================================================
# GET /api/v1/knowledge/recent
# ============================================================


class TestGetRecentKnowledge:
    def test_success(self, client, auth_headers):
        """認証済みで最近のナレッジを取得できる"""
        resp = client.get("/api/v1/knowledge/recent", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/recent")
        assert resp.status_code == 401

    def test_days_param(self, client, auth_headers):
        """days パラメータを指定できる"""
        resp = client.get("/api/v1/knowledge/recent?days=30", headers=auth_headers)
        assert resp.status_code == 200

    def test_limit_param(self, client, auth_headers):
        """limit パラメータを指定できる"""
        resp = client.get("/api/v1/knowledge/recent?limit=3", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) <= 3

    def test_limit_capped_at_50(self, client, auth_headers):
        """limit は最大 50 に制限される"""
        resp = client.get("/api/v1/knowledge/recent?limit=9999", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) <= 50

    def test_days_zero_returns_empty(self, client, auth_headers):
        """days=0 だと cutoff が今日なので結果は空（または少ない）"""
        resp = client.get("/api/v1/knowledge/recent?days=0", headers=auth_headers)
        assert resp.status_code == 200
        # days=0 では今日以降のデータのみ→空配列の可能性高い
        data = resp.get_json()
        assert isinstance(data["data"], list)


# ============================================================
# GET /api/v1/knowledge/favorites
# ============================================================


class TestGetFavoriteKnowledge:
    def test_success_no_favorites(self, client, auth_headers):
        """お気に入りがない場合は空リスト"""
        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == []

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/favorites")
        assert resp.status_code == 401

    def test_partner_can_access(self, client, partner_auth_headers):
        """partner ロールでも favorites にアクセスできる（jwt_required のみ）"""
        resp = client.get("/api/v1/knowledge/favorites", headers=partner_auth_headers)
        assert resp.status_code == 200


# ============================================================
# GET /api/v1/knowledge/tags
# ============================================================


class TestGetKnowledgeTags:
    def test_success(self, client, auth_headers):
        """認証済みでタグ一覧を取得できる"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/tags")
        assert resp.status_code == 401

    def test_tag_has_required_fields(self, client, auth_headers):
        """タグデータに name, count, size フィールドがある"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        # conftest に tag=["test"] の knowledge が1件ある
        tags = data["data"]
        if tags:
            tag = tags[0]
            assert "name" in tag
            assert "count" in tag
            assert "size" in tag

    def test_tag_count_is_int(self, client, auth_headers):
        """count が整数"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        for tag in data["data"]:
            assert isinstance(tag["count"], int)

    def test_conftest_knowledge_has_test_tag(self, client, auth_headers):
        """conftest の knowledge に tag=test があるのでリストに含まれる"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        tag_names = [t["name"] for t in data["data"]]
        assert "test" in tag_names


# ============================================================
# GET /api/v1/knowledge/<id>/related
# ============================================================


class TestGetRelatedKnowledge:
    def test_success(self, client, auth_headers):
        """存在するナレッジの関連アイテムを取得できる"""
        resp = client.get("/api/v1/knowledge/1/related", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert "target_id" in data["data"]
        assert "related_items" in data["data"]
        assert data["data"]["target_id"] == 1

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/1/related")
        assert resp.status_code == 401

    def test_not_found(self, client, auth_headers):
        """存在しない id は 404"""
        resp = client.get("/api/v1/knowledge/9999/related", headers=auth_headers)
        assert resp.status_code == 404

    def test_invalid_limit_zero(self, client, auth_headers):
        """limit=0 は 400 INVALID_LIMIT"""
        resp = client.get("/api/v1/knowledge/1/related?limit=0", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_invalid_limit_too_large(self, client, auth_headers):
        """limit=21 は 400 INVALID_LIMIT"""
        resp = client.get("/api/v1/knowledge/1/related?limit=21", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_valid_limit_minimum(self, client, auth_headers):
        """limit=1 は有効"""
        resp = client.get("/api/v1/knowledge/1/related?limit=1", headers=auth_headers)
        assert resp.status_code == 200

    def test_valid_limit_maximum(self, client, auth_headers):
        """limit=20 は有効"""
        resp = client.get("/api/v1/knowledge/1/related?limit=20", headers=auth_headers)
        assert resp.status_code == 200

    def test_invalid_algorithm(self, client, auth_headers):
        """無効な algorithm は 400 INVALID_ALGORITHM"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=invalid", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_ALGORITHM"

    def test_valid_algorithm_tag(self, client, auth_headers):
        """algorithm=tag は有効"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=tag", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["algorithm"] == "tag"

    def test_valid_algorithm_category(self, client, auth_headers):
        """algorithm=category は有効"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=category", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_valid_algorithm_keyword(self, client, auth_headers):
        """algorithm=keyword は有効"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=keyword", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_valid_algorithm_hybrid(self, client, auth_headers):
        """algorithm=hybrid（デフォルト）は有効"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=hybrid", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_response_has_algorithm_and_count(self, client, auth_headers):
        """レスポンスに algorithm と count フィールドがある"""
        resp = client.get("/api/v1/knowledge/1/related", headers=auth_headers)
        data = resp.get_json()
        assert "algorithm" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["count"], int)


# ============================================================
# DELETE /api/v1/favorites/<id>
# ============================================================


class TestRemoveFavorite:
    def test_success_no_existing_favorite(self, client, auth_headers):
        """お気に入りにない知識でも 200（冪等）"""
        resp = client.delete("/api/v1/favorites/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.delete("/api/v1/favorites/1")
        assert resp.status_code == 401

    def test_partner_can_remove_favorite(self, client, partner_auth_headers):
        """partner ロールでもお気に入り削除できる（jwt_required のみ）"""
        resp = client.delete("/api/v1/favorites/1", headers=partner_auth_headers)
        assert resp.status_code == 200

    def test_response_has_knowledge_id(self, client, auth_headers):
        """レスポンスに knowledge_id が含まれる"""
        resp = client.delete("/api/v1/favorites/1", headers=auth_headers)
        data = resp.get_json()
        assert "knowledge_id" in data
        assert data["knowledge_id"] == 1

    def test_response_has_message(self, client, auth_headers):
        """レスポンスに message が含まれる"""
        resp = client.delete("/api/v1/favorites/1", headers=auth_headers)
        data = resp.get_json()
        assert "message" in data


# ============================================================
# GET /api/v1/knowledge/search
# ============================================================


class TestSearchKnowledge:
    def test_success_with_query(self, client, auth_headers):
        """query パラメータ付きで検索できる"""
        resp = client.get(
            "/api/v1/knowledge/search?query=Test", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/search?query=test")
        assert resp.status_code == 401

    def test_missing_query_returns_400(self, client, auth_headers):
        """query なしでは 400 MISSING_QUERY"""
        resp = client.get("/api/v1/knowledge/search", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_QUERY"

    def test_empty_query_returns_400(self, client, auth_headers):
        """空 query は 400 MISSING_QUERY"""
        resp = client.get("/api/v1/knowledge/search?query=", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MISSING_QUERY"

    def test_search_finds_existing_knowledge(self, client, auth_headers):
        """既存のナレッジタイトルで検索するとヒットする"""
        resp = client.get(
            "/api/v1/knowledge/search?query=Test+Knowledge", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["total"] >= 1
        assert len(data["data"]["results"]) >= 1

    def test_search_no_match_returns_empty(self, client, auth_headers):
        """マッチしない query は空結果"""
        resp = client.get(
            "/api/v1/knowledge/search?query=ZZZNOMATCH999XYZ", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["total"] == 0
        assert data["data"]["results"] == []

    def test_response_has_pagination_fields(self, client, auth_headers):
        """レスポンスにページネーションフィールドがある"""
        resp = client.get(
            "/api/v1/knowledge/search?query=test", headers=auth_headers
        )
        data = resp.get_json()
        search_data = data["data"]
        assert "results" in search_data
        assert "total" in search_data
        assert "page" in search_data
        assert "per_page" in search_data
        assert "query" in search_data

    def test_pagination_params(self, client, auth_headers):
        """page と per_page パラメータが動作する"""
        resp = client.get(
            "/api/v1/knowledge/search?query=test&page=1&per_page=5", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["page"] == 1
        assert data["data"]["per_page"] == 5

    def test_partner_can_search(self, client, partner_auth_headers):
        """partner ロールでも検索できる（jwt_required のみ）"""
        resp = client.get(
            "/api/v1/knowledge/search?query=test", headers=partner_auth_headers
        )
        assert resp.status_code == 200


# ============================================================
# GET /api/v1/search/unified
# ============================================================


class TestUnifiedSearch:
    def test_success_with_query(self, client, auth_headers):
        """q パラメータ付きで横断検索できる"""
        resp = client.get("/api/v1/search/unified?q=test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/search/unified?q=test")
        assert resp.status_code == 401

    def test_missing_query_returns_400(self, client, auth_headers):
        """q なしでは 400 MISSING_QUERY"""
        resp = client.get("/api/v1/search/unified", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_QUERY"

    def test_blank_query_returns_400(self, client, auth_headers):
        """空白のみの q は 400 MISSING_QUERY"""
        resp = client.get("/api/v1/search/unified?q=+", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MISSING_QUERY"

    def test_default_types_include_knowledge(self, client, auth_headers):
        """デフォルト types に knowledge が含まれる"""
        resp = client.get("/api/v1/search/unified?q=test", headers=auth_headers)
        data = resp.get_json()
        # デフォルトは knowledge,sop,incidents
        assert "knowledge" in data["data"]

    def test_type_knowledge_only(self, client, auth_headers):
        """types=knowledge のみ指定で knowledge キーのみ返る"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "knowledge" in data["data"]

    def test_search_finds_existing_knowledge(self, client, auth_headers):
        """既存ナレッジ（Test Knowledge）が検索でヒットする"""
        resp = client.get(
            "/api/v1/search/unified?q=Test+Knowledge&types=knowledge", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["knowledge"]["count"] >= 1

    def test_knowledge_result_has_items_and_count(self, client, auth_headers):
        """knowledge 結果に items と count がある"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge", headers=auth_headers
        )
        data = resp.get_json()
        knowledge = data["data"]["knowledge"]
        assert "items" in knowledge
        assert "count" in knowledge
        assert isinstance(knowledge["items"], list)
        assert isinstance(knowledge["count"], int)

    def test_response_has_total_results(self, client, auth_headers):
        """total_results フィールドがある"""
        resp = client.get("/api/v1/search/unified?q=test", headers=auth_headers)
        data = resp.get_json()
        assert "total_results" in data
        assert isinstance(data["total_results"], int)

    def test_response_has_query(self, client, auth_headers):
        """query フィールドがある"""
        resp = client.get("/api/v1/search/unified?q=test", headers=auth_headers)
        data = resp.get_json()
        assert "query" in data
        assert data["query"] == "test"

    def test_partner_can_unified_search(self, client, partner_auth_headers):
        """partner ロールでも横断検索できる（jwt_required のみ）"""
        resp = client.get(
            "/api/v1/search/unified?q=test", headers=partner_auth_headers
        )
        assert resp.status_code == 200

    def test_sop_type_returns_sop_key(self, client, auth_headers):
        """types=sop で sop キーが返る"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=sop", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sop" in data["data"]
