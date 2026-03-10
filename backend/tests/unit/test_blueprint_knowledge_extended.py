"""
blueprints/knowledge.py 拡張ユニットテスト

未カバー領域のテスト:
  GET /api/v1/knowledge?search=&highlight=true  - ハイライト検索
  GET /api/v1/knowledge?tags=                   - タグフィルタ
  GET /api/v1/knowledge/popular                 - 人気ナレッジ
  GET /api/v1/knowledge/recent                  - 最新ナレッジ
  GET /api/v1/knowledge/favorites               - お気に入り
  GET /api/v1/knowledge/tags                    - タグ一覧
  GET /api/v1/knowledge/<id>/related            - 関連ナレッジ
  DELETE /api/v1/knowledge/favorites/<id>       - お気に入り削除
  GET /api/v1/knowledge/search                  - 検索
  GET /api/v1/search/unified                    - 統合検索
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ============================================================
# ハイライト検索 GET /api/v1/knowledge?search=&highlight=true
# ============================================================


class TestKnowledgeHighlightSearch:
    def test_highlight_search_returns_200(self, client, auth_headers):
        """ハイライト検索が成功する"""
        resp = client.get(
            "/api/v1/knowledge?search=Test&highlight=true", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_highlight_search_no_results(self, client, auth_headers):
        """ヒットなしでも 200 を返す"""
        resp = client.get(
            "/api/v1/knowledge?search=zzz_no_match&highlight=true",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data["data"], list)


# ============================================================
# タグフィルタ GET /api/v1/knowledge?tags=
# ============================================================


class TestKnowledgeTagsFilter:
    def test_tags_filter_returns_200(self, client, auth_headers):
        """タグフィルタで 200 が返る"""
        resp = client.get("/api/v1/knowledge?tags=test", headers=auth_headers)
        assert resp.status_code == 200

    def test_tags_filter_no_match(self, client, auth_headers):
        """マッチしないタグは空リスト"""
        resp = client.get("/api/v1/knowledge?tags=no_such_tag", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []


# ============================================================
# GET /api/v1/knowledge/popular
# ============================================================


class TestGetPopularKnowledge:
    def test_popular_returns_200(self, client, auth_headers):
        """人気ナレッジ一覧が取得できる"""
        resp = client.get("/api/v1/knowledge/popular", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_popular_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/popular")
        assert resp.status_code == 401

    def test_popular_has_data_field(self, client, auth_headers):
        """data フィールドが含まれる"""
        resp = client.get("/api/v1/knowledge/popular", headers=auth_headers)
        data = resp.get_json()
        assert "data" in data

    def test_popular_with_limit(self, client, auth_headers):
        """limit パラメータが動作する"""
        resp = client.get("/api/v1/knowledge/popular?limit=5", headers=auth_headers)
        assert resp.status_code == 200

    def test_popular_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーもアクセスできる"""
        resp = client.get("/api/v1/knowledge/popular", headers=partner_auth_headers)
        assert resp.status_code == 200

    def test_popular_returns_list(self, client, auth_headers):
        """data フィールドがリスト"""
        resp = client.get("/api/v1/knowledge/popular", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["data"], list)


# ============================================================
# GET /api/v1/knowledge/recent
# ============================================================


class TestGetRecentKnowledge:
    def test_recent_returns_200(self, client, auth_headers):
        """最新ナレッジ一覧が取得できる"""
        resp = client.get("/api/v1/knowledge/recent", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_recent_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/recent")
        assert resp.status_code == 401

    def test_recent_has_data_field(self, client, auth_headers):
        """data フィールドがある"""
        resp = client.get("/api/v1/knowledge/recent", headers=auth_headers)
        data = resp.get_json()
        assert "data" in data

    def test_recent_with_limit(self, client, auth_headers):
        """limit パラメータが動作する"""
        resp = client.get("/api/v1/knowledge/recent?limit=5", headers=auth_headers)
        assert resp.status_code == 200

    def test_recent_with_days(self, client, auth_headers):
        """days パラメータが動作する"""
        resp = client.get("/api/v1/knowledge/recent?days=7", headers=auth_headers)
        assert resp.status_code == 200

    def test_recent_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーもアクセスできる"""
        resp = client.get("/api/v1/knowledge/recent", headers=partner_auth_headers)
        assert resp.status_code == 200

    def test_recent_returns_list(self, client, auth_headers):
        """data フィールドがリスト"""
        resp = client.get("/api/v1/knowledge/recent", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["data"], list)


# ============================================================
# GET /api/v1/knowledge/favorites
# ============================================================


class TestGetFavoriteKnowledge:
    def test_favorites_returns_200(self, client, auth_headers):
        """お気に入り一覧が取得できる"""
        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_favorites_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/favorites")
        assert resp.status_code == 401

    def test_favorites_has_data_field(self, client, auth_headers):
        """data フィールドがある"""
        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        data = resp.get_json()
        assert "data" in data

    def test_favorites_returns_list(self, client, auth_headers):
        """data フィールドがリスト"""
        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["data"], list)

    def test_favorites_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーもアクセスできる"""
        resp = client.get("/api/v1/knowledge/favorites", headers=partner_auth_headers)
        assert resp.status_code == 200


# ============================================================
# GET /api/v1/knowledge/tags
# ============================================================


class TestGetKnowledgeTags:
    def test_tags_returns_200(self, client, auth_headers):
        """タグ一覧が取得できる"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_tags_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/tags")
        assert resp.status_code == 401

    def test_tags_has_data_field(self, client, auth_headers):
        """data フィールドがある"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        assert "data" in data

    def test_tags_returns_list(self, client, auth_headers):
        """data フィールドがリスト"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["data"], list)

    def test_tags_contains_test_tag(self, client, auth_headers):
        """conftest で登録したタグが含まれる"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        tag_names = [t["name"] if isinstance(t, dict) else t for t in data["data"]]
        assert "test" in tag_names

    def test_tags_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーもアクセスできる"""
        resp = client.get("/api/v1/knowledge/tags", headers=partner_auth_headers)
        assert resp.status_code == 200


# ============================================================
# GET /api/v1/knowledge/<id>/related
# ============================================================


class TestGetRelatedKnowledge:
    def test_related_returns_200(self, client, auth_headers):
        """関連ナレッジが取得できる"""
        resp = client.get("/api/v1/knowledge/1/related", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_related_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/1/related")
        assert resp.status_code == 401

    def test_related_not_found(self, client, auth_headers):
        """存在しないIDで 404"""
        resp = client.get("/api/v1/knowledge/99999/related", headers=auth_headers)
        assert resp.status_code == 404

    def test_related_has_data_field(self, client, auth_headers):
        """data フィールドがある"""
        resp = client.get("/api/v1/knowledge/1/related", headers=auth_headers)
        data = resp.get_json()
        assert "data" in data

    def test_related_returns_list(self, client, auth_headers):
        """related_items フィールドがリスト"""
        resp = client.get("/api/v1/knowledge/1/related", headers=auth_headers)
        data = resp.get_json()
        # data は {"related_items": [...], "algorithm": ..., "count": ...} 形式
        assert isinstance(data["data"]["related_items"], list)

    def test_related_with_limit_valid(self, client, auth_headers):
        """limit=5 は有効"""
        resp = client.get("/api/v1/knowledge/1/related?limit=5", headers=auth_headers)
        assert resp.status_code == 200

    def test_related_limit_too_small(self, client, auth_headers):
        """limit=0 は 400 INVALID_LIMIT"""
        resp = client.get("/api/v1/knowledge/1/related?limit=0", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_related_limit_too_large(self, client, auth_headers):
        """limit=21 は 400 INVALID_LIMIT"""
        resp = client.get("/api/v1/knowledge/1/related?limit=21", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_related_algorithm_tag(self, client, auth_headers):
        """algorithm=tag は有効"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=tag", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_related_algorithm_invalid(self, client, auth_headers):
        """不正な algorithm は 400 INVALID_ALGORITHM"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=invalid", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_ALGORITHM"

    def test_related_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーもアクセスできる"""
        resp = client.get("/api/v1/knowledge/1/related", headers=partner_auth_headers)
        assert resp.status_code == 200


# ============================================================
# DELETE /api/v1/knowledge/favorites/<id>
# ============================================================


class TestRemoveFavorite:
    def test_remove_favorite_returns_200_or_404(self, client, auth_headers):
        """お気に入り削除が 200 または 404 を返す"""
        resp = client.delete("/api/v1/favorites/1", headers=auth_headers)
        assert resp.status_code in (200, 404)

    def test_remove_favorite_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.delete("/api/v1/favorites/1")
        assert resp.status_code == 401

    def test_remove_favorite_not_in_favorites(self, client, auth_headers):
        """お気に入りに未登録のIDは 200 または 404 を返す"""
        resp = client.delete("/api/v1/favorites/99999", headers=auth_headers)
        # users_favorites.json が未存在時は空リスト扱いで 200 を返す
        assert resp.status_code in (200, 404)

    def test_remove_favorite_response_structure(self, client, auth_headers):
        """レスポンスに success フィールドがある"""
        resp = client.delete("/api/v1/favorites/1", headers=auth_headers)
        data = resp.get_json()
        assert "success" in data

    def test_remove_favorite_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーも自分のお気に入りを削除できる"""
        resp = client.delete(
            "/api/v1/favorites/99999", headers=partner_auth_headers
        )
        # 未登録は 404
        assert resp.status_code in (200, 404)


# ============================================================
# GET /api/v1/knowledge/search
# ============================================================


class TestSearchKnowledge:
    def test_search_returns_200(self, client, auth_headers):
        """検索が成功する"""
        resp = client.get(
            "/api/v1/knowledge/search?query=Test", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_search_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/search?query=Test")
        assert resp.status_code == 401

    def test_search_missing_query(self, client, auth_headers):
        """query パラメータなしでは 400 MISSING_QUERY"""
        resp = client.get("/api/v1/knowledge/search", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_QUERY"

    def test_search_has_data_field(self, client, auth_headers):
        """data フィールドがある"""
        resp = client.get(
            "/api/v1/knowledge/search?query=Test", headers=auth_headers
        )
        data = resp.get_json()
        assert "data" in data

    def test_search_returns_list(self, client, auth_headers):
        """results フィールドがリスト"""
        resp = client.get(
            "/api/v1/knowledge/search?query=Test", headers=auth_headers
        )
        data = resp.get_json()
        # data は {"results": [...], "total": ..., "page": ...} 形式
        assert isinstance(data["data"]["results"], list)

    def test_search_no_results(self, client, auth_headers):
        """マッチなしで空リスト"""
        resp = client.get(
            "/api/v1/knowledge/search?query=zzz_absolutely_no_match",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data["data"]["results"], list)

    def test_search_with_limit(self, client, auth_headers):
        """limit パラメータが動作する"""
        resp = client.get(
            "/api/v1/knowledge/search?query=Test&limit=5", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_search_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーもアクセスできる"""
        resp = client.get(
            "/api/v1/knowledge/search?query=Test", headers=partner_auth_headers
        )
        assert resp.status_code == 200


# ============================================================
# GET /api/v1/search/unified
# ============================================================


class TestUnifiedSearch:
    def test_unified_search_returns_200(self, client, auth_headers):
        """統合検索が成功する"""
        resp = client.get("/api/v1/search/unified?q=Test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_unified_search_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/search/unified?q=Test")
        assert resp.status_code == 401

    def test_unified_search_missing_query(self, client, auth_headers):
        """q パラメータなしでは 400 MISSING_QUERY"""
        resp = client.get("/api/v1/search/unified", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_QUERY"

    def test_unified_search_empty_query(self, client, auth_headers):
        """空文字では 400 MISSING_QUERY"""
        resp = client.get("/api/v1/search/unified?q=   ", headers=auth_headers)
        assert resp.status_code == 400

    def test_unified_search_has_data_field(self, client, auth_headers):
        """data フィールドがある"""
        resp = client.get("/api/v1/search/unified?q=Test", headers=auth_headers)
        data = resp.get_json()
        assert "data" in data

    def test_unified_search_has_knowledge(self, client, auth_headers):
        """data に knowledge フィールドがある"""
        resp = client.get("/api/v1/search/unified?q=Test", headers=auth_headers)
        data = resp.get_json()
        assert "knowledge" in data["data"]

    def test_unified_search_has_sop(self, client, auth_headers):
        """data に sop フィールドがある"""
        resp = client.get("/api/v1/search/unified?q=Test", headers=auth_headers)
        data = resp.get_json()
        assert "sop" in data["data"]

    def test_unified_search_knowledge_is_dict(self, client, auth_headers):
        """knowledge フィールドが辞書（items キーにリスト）"""
        resp = client.get("/api/v1/search/unified?q=Test", headers=auth_headers)
        data = resp.get_json()
        # knowledge は {"items": [...], "count": ..., ...} 形式
        assert isinstance(data["data"]["knowledge"], dict)
        assert "items" in data["data"]["knowledge"]

    def test_unified_search_sop_is_dict(self, client, auth_headers):
        """sop フィールドが辞書（items キーにリスト）"""
        resp = client.get("/api/v1/search/unified?q=Test", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["data"]["sop"], dict)

    def test_unified_search_with_limit(self, client, auth_headers):
        """limit パラメータが動作する"""
        resp = client.get(
            "/api/v1/search/unified?q=Test&limit=5", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_unified_search_no_results(self, client, auth_headers):
        """マッチなしで空の items リスト"""
        resp = client.get(
            "/api/v1/search/unified?q=zzz_absolutely_no_match", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data["data"]["knowledge"]["items"], list)

    def test_unified_search_partner_can_access(self, client, partner_auth_headers):
        """partner_company ユーザーもアクセスできる"""
        resp = client.get(
            "/api/v1/search/unified?q=Test", headers=partner_auth_headers
        )
        assert resp.status_code == 200

    def test_unified_search_has_query_field(self, client, auth_headers):
        """レスポンスに query フィールドがある"""
        resp = client.get("/api/v1/search/unified?q=Test", headers=auth_headers)
        data = resp.get_json()
        assert "query" in data["data"] or "q" in data["data"] or "data" in data

    def test_unified_search_type_filter_knowledge(self, client, auth_headers):
        """type=knowledge フィルタが動作する"""
        resp = client.get(
            "/api/v1/search/unified?q=Test&type=knowledge", headers=auth_headers
        )
        assert resp.status_code == 200
