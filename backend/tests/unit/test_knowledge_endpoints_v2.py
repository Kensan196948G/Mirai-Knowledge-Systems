"""
knowledge Blueprint カバレッジ補完テスト v2

target missing lines (from coverage report):
  blueprints/knowledge.py:
    64-73    _get_knowledge_list (Redis cache hit via g)
    134-135  get_knowledge cache hit
    141      category filter
    158-160  highlight mode
    172-173  tags filter
    209-211  get_knowledge exception re-raise
    228-229  get_popular cache hit
    244-246  get_popular exception re-raise
    267-268  get_recent cache hit
    276      get_recent item with None
    279-286  get_recent date parsing
    303-305  get_recent exception re-raise
    326-332  get_favorites with matching favorites
    349-350  get_tags cache hit
    357      get_tags None item
    374-376  get_tags exception re-raise
    408-473  get_related_knowledge
    534, 548 update_knowledge no-body / not found
    606      delete_knowledge forbidden
    638-651  remove_favorite
    690      search_knowledge cache hit
    738-868  unified_search

This file does NOT duplicate existing tests in:
  - test_knowledge_coverage.py
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ============================================================
# Helper: create favorites file
# ============================================================


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# GET /knowledge - category / tags / highlight filters
# ============================================================


class TestGetKnowledgeFilters:
    """GET /api/v1/knowledge - filter paths (lines 141, 158-160, 172-173)"""

    def test_category_filter_returns_matching(self, client, auth_headers):
        """category パラメータで safety カテゴリのみフィルタ (line 141)"""
        # conftest seed data has category='safety'
        resp = client.get("/api/v1/knowledge?category=safety", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        for item in data["data"]:
            assert item["category"] == "safety"

    def test_category_filter_no_match_returns_empty(self, client, auth_headers):
        """マッチしない category で空リスト"""
        resp = client.get(
            "/api/v1/knowledge?category=nonexistent_category_xyz", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []

    def test_highlight_mode_returns_results(self, client, auth_headers):
        """highlight=true でハイライト付き検索 (lines 158-160)"""
        resp = client.get(
            "/api/v1/knowledge?search=Test&highlight=true", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_tags_filter_returns_matching(self, client, auth_headers):
        """tags パラメータで絞り込み (lines 172-173)"""
        # conftest seed data has tags=['test']
        resp = client.get("/api/v1/knowledge?tags=test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        for item in data["data"]:
            assert "test" in item.get("tags", [])

    def test_tags_filter_multiple_tags(self, client, auth_headers):
        """複数タグのカンマ区切りフィルタ"""
        resp = client.get(
            "/api/v1/knowledge?tags=test,nonexistent", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_tags_no_match_returns_empty(self, client, auth_headers):
        """マッチしない tags で空リスト"""
        resp = client.get(
            "/api/v1/knowledge?tags=nonexistent_tag_xyz", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []

    def test_sort_by_views_asc(self, client, auth_headers):
        """sort=views&order=asc でソート (lines 179-185)"""
        resp = client.get(
            "/api/v1/knowledge?sort=views&order=asc", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_sort_by_updated_at_desc(self, client, auth_headers):
        """sort=updated_at&order=desc でソート"""
        resp = client.get(
            "/api/v1/knowledge?sort=updated_at&order=desc", headers=auth_headers
        )
        assert resp.status_code == 200


# ============================================================
# GET /knowledge/popular - additional coverage
# ============================================================


class TestGetPopularKnowledgeAdditional:
    """GET /api/v1/knowledge/popular - exception path and edge cases"""

    def test_popular_returns_at_most_limit(self, client, auth_headers):
        """limit=1 で最大1件 (line 237)"""
        resp = client.get("/api/v1/knowledge/popular?limit=1", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.get_json()["data"]) <= 1

    def test_popular_zero_limit_handled(self, client, auth_headers):
        """limit=0 (0件) でも正常レスポンス"""
        resp = client.get("/api/v1/knowledge/popular?limit=0", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.get_json()["data"]) == 0


# ============================================================
# GET /knowledge/recent - date parsing path (lines 279-286)
# ============================================================


class TestGetRecentKnowledgeDateParsing:
    """GET /api/v1/knowledge/recent - date filtering paths"""

    def test_recent_with_created_at_iso_format(self, client, auth_headers, tmp_path, monkeypatch):
        """ISO 形式の created_at をもつナレッジが recent に含まれる (lines 279-286)"""
        from datetime import datetime, timedelta

        import app_helpers

        now = datetime.now()
        recent_ts = (now - timedelta(days=1)).isoformat()
        old_ts = (now - timedelta(days=30)).isoformat()

        knowledge_data = [
            {
                "id": 10,
                "title": "Recent Item",
                "summary": "s",
                "content": "c",
                "category": "safety",
                "tags": [],
                "created_at": recent_ts,
            },
            {
                "id": 11,
                "title": "Old Item",
                "summary": "s",
                "content": "c",
                "category": "safety",
                "tags": [],
                "created_at": old_ts,
            },
        ]
        _write_json(tmp_path / "knowledge.json", knowledge_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get("/api/v1/knowledge/recent?days=7", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        ids = [item["id"] for item in data["data"]]
        assert 10 in ids
        assert 11 not in ids

    def test_recent_with_invalid_created_at_skips(self, client, auth_headers, tmp_path, monkeypatch):
        """不正な created_at フォーマットはスキップされる (lines 285-290)"""
        knowledge_data = [
            {
                "id": 20,
                "title": "Invalid Date Item",
                "summary": "s",
                "content": "c",
                "category": "safety",
                "tags": [],
                "created_at": "not-a-date",
            },
        ]
        _write_json(tmp_path / "knowledge.json", knowledge_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get("/api/v1/knowledge/recent?days=7", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        # Item with invalid date is excluded
        assert 20 not in [item["id"] for item in data["data"]]

    def test_recent_item_without_created_at_skips(self, client, auth_headers, tmp_path, monkeypatch):
        """created_at のないナレッジはスキップ (line 278)"""
        knowledge_data = [
            {
                "id": 30,
                "title": "No Date Item",
                "summary": "s",
                "content": "c",
                "category": "safety",
                "tags": [],
                # no created_at
            },
        ]
        _write_json(tmp_path / "knowledge.json", knowledge_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get("/api/v1/knowledge/recent?days=7", headers=auth_headers)
        assert resp.status_code == 200
        assert 30 not in [item["id"] for item in resp.get_json()["data"]]


# ============================================================
# GET /knowledge/favorites - with matching data (lines 326-332)
# ============================================================


class TestGetFavoritesWithData:
    """GET /api/v1/knowledge/favorites - with actual favorite data (lines 326-332)"""

    def test_favorites_returns_matching_knowledge(self, client, auth_headers, tmp_path, monkeypatch):
        """お気に入り登録済みのナレッジが返る (lines 326-329)"""
        favorites_data = [
            {"user_id": 1, "knowledge_id": 1},
        ]
        _write_json(tmp_path / "users_favorites.json", favorites_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        ids = [item["id"] for item in data["data"]]
        assert 1 in ids

    def test_favorites_with_different_user_returns_empty(self, client, auth_headers, tmp_path, monkeypatch):
        """別ユーザーのお気に入りは返らない"""
        favorites_data = [
            {"user_id": 999, "knowledge_id": 1},
        ]
        _write_json(tmp_path / "users_favorites.json", favorites_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []


# ============================================================
# GET /knowledge/tags - additional paths (line 357)
# ============================================================


class TestGetKnowledgeTagsAdditional:
    """GET /api/v1/knowledge/tags - edge cases"""

    def test_tags_none_item_skipped(self, client, auth_headers, tmp_path, monkeypatch):
        """tags が None のナレッジはスキップ (line 358-360)"""
        knowledge_data = [
            {
                "id": 1,
                "title": "No Tags",
                "summary": "s",
                "content": "c",
                "category": "safety",
                "tags": None,  # None tags
            },
            {
                "id": 2,
                "title": "Empty Tags",
                "summary": "s",
                "content": "c",
                "category": "safety",
                "tags": [],  # empty list
            },
            {
                "id": 3,
                "title": "With Tags",
                "summary": "s",
                "content": "c",
                "category": "safety",
                "tags": ["alpha", "beta"],
            },
        ]
        _write_json(tmp_path / "knowledge.json", knowledge_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        tag_names = [t["name"] for t in data["data"]]
        assert "alpha" in tag_names
        assert "beta" in tag_names


# ============================================================
# GET /knowledge/<id>/related (lines 408-473)
# ============================================================


class TestGetRelatedKnowledge:
    """GET /api/v1/knowledge/<id>/related - all paths"""

    def test_related_returns_200(self, client, auth_headers):
        """関連ナレッジ取得 200"""
        resp = client.get("/api/v1/knowledge/1/related", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "related_items" in data["data"]
        assert "target_id" in data["data"]
        assert data["data"]["target_id"] == 1

    def test_related_structure(self, client, auth_headers):
        """レスポンス構造確認"""
        resp = client.get("/api/v1/knowledge/1/related", headers=auth_headers)
        data = resp.get_json()
        assert "algorithm" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["related_items"], list)

    def test_related_nonexistent_id_returns_404(self, client, auth_headers):
        """存在しない ID で 404"""
        resp = client.get("/api/v1/knowledge/9999/related", headers=auth_headers)
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_related_invalid_limit_returns_400(self, client, auth_headers):
        """limit が範囲外 (0) で 400 INVALID_LIMIT"""
        resp = client.get(
            "/api/v1/knowledge/1/related?limit=0", headers=auth_headers
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_LIMIT"

    def test_related_limit_too_large_returns_400(self, client, auth_headers):
        """limit が 21 で 400"""
        resp = client.get(
            "/api/v1/knowledge/1/related?limit=21", headers=auth_headers
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_LIMIT"

    def test_related_invalid_algorithm_returns_400(self, client, auth_headers):
        """不正な algorithm で 400 INVALID_ALGORITHM"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=invalid_algo", headers=auth_headers
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_ALGORITHM"

    def test_related_tag_algorithm(self, client, auth_headers):
        """algorithm=tag で正常動作"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=tag", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["algorithm"] == "tag"

    def test_related_category_algorithm(self, client, auth_headers):
        """algorithm=category で正常動作"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=category", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["algorithm"] == "category"

    def test_related_keyword_algorithm(self, client, auth_headers):
        """algorithm=keyword で正常動作"""
        resp = client.get(
            "/api/v1/knowledge/1/related?algorithm=keyword", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_related_with_limit(self, client, auth_headers):
        """limit パラメータが結果に反映される"""
        resp = client.get(
            "/api/v1/knowledge/1/related?limit=3", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["related_items"]) <= 3

    def test_related_with_min_score(self, client, auth_headers):
        """min_score パラメータが受け付けられる"""
        resp = client.get(
            "/api/v1/knowledge/1/related?min_score=0.5", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_related_requires_auth(self, client):
        """認証なしで 401"""
        resp = client.get("/api/v1/knowledge/1/related")
        assert resp.status_code == 401


# ============================================================
# PUT /knowledge/<id> - no body / not found (lines 534, 548)
# ============================================================


class TestUpdateKnowledgeEdgeCases:
    """PUT /api/v1/knowledge/<id> - error paths"""

    def test_update_no_body_returns_400(self, client, auth_headers):
        """ボディなしで 400 INVALID_INPUT (line 534)

        get_json() が None / falsy を返す場合: {} は Python で falsy なので INVALID_INPUT。
        """
        # Empty JSON object {} is falsy in Python → triggers INVALID_INPUT (line 534)
        resp = client.put(
            "/api/v1/knowledge/1",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_update_nonexistent_id_returns_404(self, client, auth_headers):
        """存在しない ID で 404 NOT_FOUND (line 548)"""
        resp = client.put(
            "/api/v1/knowledge/99999",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


# ============================================================
# DELETE /knowledge/<id> - forbidden (line 606)
# ============================================================


class TestDeleteKnowledgeForbidden:
    """DELETE /api/v1/knowledge/<id> - FORBIDDEN for non-owner (line 606)"""

    def test_partner_cannot_delete_admin_knowledge(
        self, client, partner_auth_headers, auth_headers
    ):
        """partner ユーザーが admin 作成のナレッジを削除すると 403 FORBIDDEN

        conftest の knowledge.json seed (id=1) は owned by admin (created_by_id なし).
        partner ユーザーは admin でも owner でもないため FORBIDDEN になる。
        """
        # First, create knowledge owned by admin
        create_resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "Admin Created",
                "summary": "s",
                "content": "c",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        knowledge_id = create_resp.get_json()["data"]["id"]

        # Partner tries to delete admin's knowledge
        resp = client.delete(
            f"/api/v1/knowledge/{knowledge_id}",
            headers=partner_auth_headers,
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_admin_can_delete_any_knowledge(self, client, auth_headers):
        """admin (wildcard permission) は任意ナレッジを削除できる"""
        # Create then delete
        create_resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "To Delete",
                "summary": "s",
                "content": "c",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        knowledge_id = create_resp.get_json()["data"]["id"]
        resp = client.delete(
            f"/api/v1/knowledge/{knowledge_id}", headers=auth_headers
        )
        assert resp.status_code == 200


# ============================================================
# DELETE /favorites/<id> - remove favorite (lines 638-651)
# ============================================================


class TestRemoveFavorite:
    """DELETE /api/v1/favorites/<id> - お気に入り削除"""

    def test_remove_favorite_returns_200(self, client, auth_headers, tmp_path, monkeypatch):
        """お気に入り削除で 200"""
        favorites_data = [
            {"user_id": 1, "knowledge_id": 1},
            {"user_id": 1, "knowledge_id": 2},
        ]
        _write_json(tmp_path / "users_favorites.json", favorites_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.delete("/api/v1/favorites/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["knowledge_id"] == 1

    def test_remove_favorite_response_has_message(self, client, auth_headers):
        """削除レスポンスに message が含まれる"""
        resp = client.delete("/api/v1/favorites/999", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "message" in data

    def test_remove_favorite_removes_from_list(self, client, auth_headers, tmp_path, monkeypatch):
        """削除後にお気に入りリストから消える"""
        favorites_data = [
            {"user_id": 1, "knowledge_id": 5},
            {"user_id": 2, "knowledge_id": 5},  # different user
        ]
        _write_json(tmp_path / "users_favorites.json", favorites_data)
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        # Delete user_id=1's favorite for knowledge_id=5
        client.delete("/api/v1/favorites/5", headers=auth_headers)

        # Get favorites - should be empty for user 1
        get_resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.get_json()
        fav_ids = [item["id"] for item in data["data"]]
        assert 5 not in fav_ids

    def test_remove_favorite_requires_auth(self, client):
        """認証なしで 401"""
        resp = client.delete("/api/v1/favorites/1")
        assert resp.status_code == 401

    def test_remove_nonexistent_favorite_returns_200(self, client, auth_headers):
        """存在しないお気に入りを削除しても 200"""
        resp = client.delete("/api/v1/favorites/99999", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True


# ============================================================
# GET /search/unified (lines 738-868)
# ============================================================


class TestUnifiedSearch:
    """GET /api/v1/search/unified - 横断検索"""

    def test_unified_search_requires_auth(self, client):
        """認証なしで 401"""
        resp = client.get("/api/v1/search/unified?q=test")
        assert resp.status_code == 401

    def test_unified_search_missing_q_returns_400(self, client, auth_headers):
        """q パラメータなしで 400 MISSING_QUERY"""
        resp = client.get("/api/v1/search/unified", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_QUERY"

    def test_unified_search_blank_q_returns_400(self, client, auth_headers):
        """空の q で 400"""
        resp = client.get("/api/v1/search/unified?q=   ", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_QUERY"

    def test_unified_search_returns_200(self, client, auth_headers):
        """q があれば 200"""
        resp = client.get("/api/v1/search/unified?q=test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_unified_search_response_structure(self, client, auth_headers):
        """レスポンス構造確認"""
        resp = client.get("/api/v1/search/unified?q=test", headers=auth_headers)
        data = resp.get_json()
        assert "data" in data
        assert "total_results" in data
        assert "query" in data

    def test_unified_search_knowledge_type(self, client, auth_headers):
        """types=knowledge で knowledge のみ検索"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "knowledge" in data["data"]

    def test_unified_search_knowledge_result_structure(self, client, auth_headers):
        """knowledge 検索結果に items, count が含まれる"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge", headers=auth_headers
        )
        data = resp.get_json()
        k_data = data["data"]["knowledge"]
        assert "items" in k_data
        assert "count" in k_data
        assert isinstance(k_data["items"], list)

    def test_unified_search_with_highlight(self, client, auth_headers):
        """highlight=true でハイライト付き検索 (lines 787-790)"""
        resp = client.get(
            "/api/v1/search/unified?q=Test&types=knowledge&highlight=true",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_unified_search_without_highlight(self, client, auth_headers):
        """highlight=false でハイライトなし"""
        resp = client.get(
            "/api/v1/search/unified?q=Test&types=knowledge&highlight=false",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_unified_search_sop_type(self, client, auth_headers):
        """types=sop で sop も検索 (lines 825-837)"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=sop", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sop" in data["data"]

    def test_unified_search_incidents_type(self, client, auth_headers, tmp_path, monkeypatch):
        """types=incidents で incidents も検索 (lines 840-855)"""
        # Create incidents.json
        _write_json(tmp_path / "incidents.json", [])
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get(
            "/api/v1/search/unified?q=test&types=incidents", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "incidents" in data["data"]

    def test_unified_search_sort_by_updated_at(self, client, auth_headers):
        """sort_by=updated_at でソート (lines 801-804)"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge&sort_by=updated_at",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_unified_search_sort_by_created_at(self, client, auth_headers):
        """sort_by=created_at でソート (lines 805-808)"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge&sort_by=created_at",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_unified_search_pagination(self, client, auth_headers):
        """ページネーションパラメータが受け付けられる"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge&page=1&page_size=5",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        k_data = data["data"]["knowledge"]
        assert k_data["page_size"] == 5
        assert k_data["page"] == 1

    def test_unified_search_no_match_returns_empty(self, client, auth_headers):
        """マッチしないキーワードで total_results=0"""
        resp = client.get(
            "/api/v1/search/unified?q=xyzzy_impossible_match_string_12345",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_results"] == 0

    def test_unified_search_multiple_types(self, client, auth_headers, tmp_path, monkeypatch):
        """複数タイプの横断検索"""
        _write_json(tmp_path / "incidents.json", [])
        monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))

        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge,sop,incidents",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        # All three types should be in results
        assert "knowledge" in data["data"]
        assert "sop" in data["data"]
        assert "incidents" in data["data"]

    def test_unified_search_order_asc(self, client, auth_headers):
        """order=asc でソート"""
        resp = client.get(
            "/api/v1/search/unified?q=test&types=knowledge&order=asc",
            headers=auth_headers,
        )
        assert resp.status_code == 200
