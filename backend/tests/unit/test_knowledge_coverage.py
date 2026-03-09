"""
ナレッジBlueprint 補完テスト (Phase I-5 カバレッジ強化)

test_blueprint_knowledge.py と重複しないテストケースを追加する。
- /api/v1/ping レスポンス詳細
- GET /knowledge のレスポンス構造（pagination）
- GET /knowledge/popular・/recent・/tags の正常系と認証チェック
- GET /knowledge/{id} の具体的なフィールド確認
- POST /knowledge の作成後状態確認
- GET /knowledge/search の動作確認
- GET /knowledge/{nonexistent} の 404 確認
- 各エンドポイントの認証なし 401 確認（重複しないもの）
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestPingEndpoint:
    """GET /api/v1/ping - ヘルスチェック詳細"""

    def test_ping_timestamp_is_present(self, client):
        """timestamp フィールドが存在する"""
        resp = client.get("/api/v1/ping")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)
        assert len(data["timestamp"]) > 0

    def test_ping_blueprint_name_is_knowledge(self, client):
        """blueprint_name が 'knowledge' である"""
        resp = client.get("/api/v1/ping")
        data = resp.get_json()
        assert data["blueprint_name"] == "knowledge"

    def test_ping_response_is_json(self, client):
        """レスポンスが JSON 形式"""
        resp = client.get("/api/v1/ping")
        assert resp.content_type.startswith("application/json")

    def test_ping_no_auth_required(self, client):
        """認証なしでアクセスできる（401 でない）"""
        resp = client.get("/api/v1/ping")
        assert resp.status_code != 401


class TestKnowledgeListPagination:
    """GET /api/v1/knowledge - ページネーション詳細"""

    def test_get_knowledge_list_has_pagination_info(self, client, auth_headers):
        """レスポンスに pagination フィールドが含まれる"""
        resp = client.get("/api/v1/knowledge", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pagination" in data
        pagination = data["pagination"]
        assert "total_items" in pagination
        assert "total_pages" in pagination
        assert "current_page" in pagination
        assert "per_page" in pagination

    def test_get_knowledge_list_pagination_values_are_integers(self, client, auth_headers):
        """ページネーション値は整数"""
        resp = client.get("/api/v1/knowledge", headers=auth_headers)
        pagination = resp.get_json()["pagination"]
        assert isinstance(pagination["total_items"], int)
        assert isinstance(pagination["total_pages"], int)
        assert isinstance(pagination["current_page"], int)
        assert isinstance(pagination["per_page"], int)

    def test_get_knowledge_default_page_is_1(self, client, auth_headers):
        """デフォルトページは 1"""
        resp = client.get("/api/v1/knowledge", headers=auth_headers)
        pagination = resp.get_json()["pagination"]
        assert pagination["current_page"] == 1

    def test_get_knowledge_total_items_matches_data_length(self, client, auth_headers):
        """total_items はデータ件数と一致する（フィルタなし）"""
        resp = client.get("/api/v1/knowledge", headers=auth_headers)
        data = resp.get_json()
        # conftest には1件のナレッジがある
        assert data["pagination"]["total_items"] >= 1
        assert len(data["data"]) == data["pagination"]["total_items"]

    def test_get_knowledge_with_per_page_param(self, client, auth_headers):
        """per_page パラメータがレスポンスに反映される"""
        resp = client.get("/api/v1/knowledge?per_page=5", headers=auth_headers)
        assert resp.status_code == 200
        pagination = resp.get_json()["pagination"]
        assert pagination["per_page"] == 5

    def test_get_knowledge_page_2_when_only_1_item(self, client, auth_headers):
        """存在しないページ番号では空データが返る"""
        resp = client.get("/api/v1/knowledge?page=999&per_page=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []

    def test_get_knowledge_search_query_filters_results(self, client, auth_headers):
        """search クエリパラメータで絞り込みができる"""
        # conftest のナレッジタイトルに含まれる文字列で検索
        resp = client.get("/api/v1/knowledge?search=Test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) >= 1

    def test_get_knowledge_search_no_match_returns_empty(self, client, auth_headers):
        """マッチしない検索クエリでは空リスト"""
        resp = client.get(
            "/api/v1/knowledge?search=xyzzynonexistentkeyword",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []


class TestPopularKnowledge:
    """GET /api/v1/knowledge/popular"""

    def test_get_popular_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/popular")
        assert resp.status_code == 401

    def test_get_popular_returns_200_with_auth(self, client, auth_headers):
        """認証済みで 200 を返す"""
        resp = client.get("/api/v1/knowledge/popular", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_popular_response_structure(self, client, auth_headers):
        """レスポンス構造が正しい"""
        resp = client.get("/api/v1/knowledge/popular", headers=auth_headers)
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_popular_with_limit_param(self, client, auth_headers):
        """limit パラメータを受け付ける"""
        resp = client.get("/api/v1/knowledge/popular?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        # データが5件以下であることを確認
        assert len(data["data"]) <= 5

    def test_get_popular_with_partner_user(self, client, partner_auth_headers):
        """協力会社ユーザーも人気ナレッジを取得できる"""
        resp = client.get("/api/v1/knowledge/popular", headers=partner_auth_headers)
        assert resp.status_code == 200

    def test_get_popular_limit_capped_at_50(self, client, auth_headers):
        """limit が 50 以上でも 50 件以下で返る"""
        resp = client.get("/api/v1/knowledge/popular?limit=1000", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) <= 50


class TestRecentKnowledge:
    """GET /api/v1/knowledge/recent"""

    def test_get_recent_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/recent")
        assert resp.status_code == 401

    def test_get_recent_returns_200_with_auth(self, client, auth_headers):
        """認証済みで 200 を返す"""
        resp = client.get("/api/v1/knowledge/recent", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_recent_response_structure(self, client, auth_headers):
        """レスポンス構造が正しい"""
        resp = client.get("/api/v1/knowledge/recent", headers=auth_headers)
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_recent_with_limit_param(self, client, auth_headers):
        """limit パラメータを受け付ける"""
        resp = client.get("/api/v1/knowledge/recent?limit=3", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) <= 3

    def test_get_recent_with_days_param(self, client, auth_headers):
        """days パラメータを受け付ける"""
        resp = client.get("/api/v1/knowledge/recent?days=30", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_recent_with_partner_user(self, client, partner_auth_headers):
        """協力会社ユーザーも最近のナレッジを取得できる"""
        resp = client.get("/api/v1/knowledge/recent", headers=partner_auth_headers)
        assert resp.status_code == 200


class TestKnowledgeTags:
    """GET /api/v1/knowledge/tags"""

    def test_get_tags_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/tags")
        assert resp.status_code == 401

    def test_get_tags_returns_200_with_auth(self, client, auth_headers):
        """認証済みで 200 を返す"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_tags_response_structure(self, client, auth_headers):
        """レスポンス構造が正しい"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_tags_has_test_tag(self, client, auth_headers):
        """conftest に登録されている 'test' タグが含まれる"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        tag_names = [item["name"] for item in data["data"]]
        assert "test" in tag_names

    def test_get_tags_items_have_required_fields(self, client, auth_headers):
        """各タグアイテムに name, count, size フィールドが含まれる"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        if data["data"]:  # タグが存在する場合のみチェック
            tag_item = data["data"][0]
            assert "name" in tag_item
            assert "count" in tag_item
            assert "size" in tag_item

    def test_get_tags_count_is_positive_integer(self, client, auth_headers):
        """タグの count は正の整数"""
        resp = client.get("/api/v1/knowledge/tags", headers=auth_headers)
        data = resp.get_json()
        for tag_item in data["data"]:
            assert isinstance(tag_item["count"], int)
            assert tag_item["count"] > 0

    def test_get_tags_with_partner_user(self, client, partner_auth_headers):
        """協力会社ユーザーもタグ一覧を取得できる"""
        resp = client.get("/api/v1/knowledge/tags", headers=partner_auth_headers)
        assert resp.status_code == 200


class TestKnowledgeDetailAdditional:
    """GET /api/v1/knowledge/{id} - 詳細な内容確認"""

    def test_get_detail_contains_title(self, client, auth_headers):
        """詳細レスポンスに title が含まれる"""
        resp = client.get("/api/v1/knowledge/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["title"] == "Test Knowledge"

    def test_get_detail_contains_summary(self, client, auth_headers):
        """詳細レスポンスに summary が含まれる"""
        resp = client.get("/api/v1/knowledge/1", headers=auth_headers)
        data = resp.get_json()
        assert "summary" in data["data"]
        assert data["data"]["summary"] == "Test summary"

    def test_get_detail_contains_content(self, client, auth_headers):
        """詳細レスポンスに content が含まれる"""
        resp = client.get("/api/v1/knowledge/1", headers=auth_headers)
        data = resp.get_json()
        assert "content" in data["data"]

    def test_get_detail_contains_category(self, client, auth_headers):
        """詳細レスポンスに category が含まれる"""
        resp = client.get("/api/v1/knowledge/1", headers=auth_headers)
        data = resp.get_json()
        assert "category" in data["data"]

    def test_get_detail_contains_tags(self, client, auth_headers):
        """詳細レスポンスに tags が含まれる（リスト型）"""
        resp = client.get("/api/v1/knowledge/1", headers=auth_headers)
        data = resp.get_json()
        assert "tags" in data["data"]
        assert isinstance(data["data"]["tags"], list)

    def test_get_nonexistent_id_large_number(self, client, auth_headers):
        """非常に大きな ID では 404 を返す"""
        resp = client.get("/api/v1/knowledge/9999999", headers=auth_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_get_detail_error_response_has_error_field(self, client, auth_headers):
        """404 レスポンスに error フィールドが含まれる"""
        resp = client.get("/api/v1/knowledge/9999", headers=auth_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data


class TestCreateKnowledgeAdditional:
    """POST /api/v1/knowledge - 作成後の状態確認"""

    def test_create_knowledge_has_created_at(self, client, auth_headers):
        """作成後のレスポンスに created_at が含まれる"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "タイムスタンプテスト",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "created_at" in data["data"]
        assert isinstance(data["data"]["created_at"], str)

    def test_create_knowledge_has_status_draft(self, client, auth_headers):
        """作成直後のステータスは draft"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "ステータステスト",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "品質管理",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["status"] == "draft"

    def test_create_knowledge_with_tags(self, client, auth_headers):
        """tags フィールドを指定して作成できる"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "タグ付きナレッジ",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
                "tags": ["tag1", "tag2"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["tags"] == ["tag1", "tag2"]

    def test_create_knowledge_response_has_updated_at(self, client, auth_headers):
        """作成後のレスポンスに updated_at が含まれる"""
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "更新日時テスト",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "updated_at" in data["data"]

    def test_create_knowledge_id_auto_increments(self, client, auth_headers):
        """2件作成すると ID が異なる"""
        resp1 = client.post(
            "/api/v1/knowledge",
            json={
                "title": "1件目",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        resp2 = client.post(
            "/api/v1/knowledge",
            json={
                "title": "2件目",
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "品質管理",
            },
            headers=auth_headers,
        )
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        id1 = resp1.get_json()["data"]["id"]
        id2 = resp2.get_json()["data"]["id"]
        assert id1 != id2
        assert id2 > id1

    def test_create_knowledge_appears_in_list(self, client, auth_headers):
        """作成したナレッジが一覧に反映される"""
        unique_title = "ユニーク検索テスト 12345"
        client.post(
            "/api/v1/knowledge",
            json={
                "title": unique_title,
                "summary": "サマリー",
                "content": "コンテンツ",
                "category": "安全衛生",
            },
            headers=auth_headers,
        )
        list_resp = client.get("/api/v1/knowledge", headers=auth_headers)
        titles = [item["title"] for item in list_resp.get_json()["data"]]
        assert unique_title in titles


class TestKnowledgeSearch:
    """GET /api/v1/knowledge/search - 検索エンドポイント"""

    def test_search_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/search?query=test")
        assert resp.status_code == 401

    def test_search_without_query_param_returns_400(self, client, auth_headers):
        """query パラメータなしでは 400"""
        resp = client.get("/api/v1/knowledge/search", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_QUERY"

    def test_search_with_empty_query_returns_400(self, client, auth_headers):
        """空の query パラメータで 400"""
        resp = client.get("/api/v1/knowledge/search?query=", headers=auth_headers)
        assert resp.status_code == 400

    def test_search_with_matching_query_returns_results(self, client, auth_headers):
        """マッチするキーワードで結果が返る"""
        # conftest のナレッジ: title="Test Knowledge"
        resp = client.get("/api/v1/knowledge/search?query=Test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1

    def test_search_response_structure(self, client, auth_headers):
        """検索レスポンス構造が正しい"""
        resp = client.get("/api/v1/knowledge/search?query=test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "data" in data
        search_data = data["data"]
        assert "results" in search_data
        assert "total" in search_data
        assert "page" in search_data
        assert "per_page" in search_data
        assert "pages" in search_data
        assert "query" in search_data

    def test_search_results_is_list(self, client, auth_headers):
        """results は リスト型"""
        resp = client.get("/api/v1/knowledge/search?query=test", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["data"]["results"], list)

    def test_search_no_match_returns_empty_results(self, client, auth_headers):
        """マッチしないキーワードでは空の results"""
        resp = client.get(
            "/api/v1/knowledge/search?query=xyzzy_no_match_at_all",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["total"] == 0
        assert data["data"]["results"] == []

    def test_search_with_pagination_params(self, client, auth_headers):
        """ページネーションパラメータを受け付ける"""
        resp = client.get(
            "/api/v1/knowledge/search?query=test&page=1&per_page=5",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["page"] == 1
        assert data["data"]["per_page"] == 5

    def test_search_query_is_reflected_in_response(self, client, auth_headers):
        """検索クエリがレスポンスに反映される"""
        resp = client.get(
            "/api/v1/knowledge/search?query=TestKeyword",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["query"] == "TestKeyword"


class TestKnowledgeFavorites:
    """GET /api/v1/knowledge/favorites - お気に入りナレッジ"""

    def test_get_favorites_requires_auth(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/knowledge/favorites")
        assert resp.status_code == 401

    def test_get_favorites_returns_200_with_auth(self, client, auth_headers):
        """認証済みで 200 を返す"""
        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_favorites_response_structure(self, client, auth_headers):
        """レスポンス構造が正しい"""
        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_favorites_empty_for_new_user(self, client, auth_headers):
        """新規ユーザーのお気に入りは空リスト"""
        resp = client.get("/api/v1/knowledge/favorites", headers=auth_headers)
        data = resp.get_json()
        # conftest では users_favorites.json を作成していないため空
        assert data["data"] == []


class TestKnowledgeUnauthorizedAccess:
    """各エンドポイントの認証なしアクセス確認（既存テストと重複しないもの）"""

    def test_knowledge_popular_without_auth(self, client):
        """GET /knowledge/popular - 認証なしで 401"""
        resp = client.get("/api/v1/knowledge/popular")
        assert resp.status_code == 401

    def test_knowledge_recent_without_auth(self, client):
        """GET /knowledge/recent - 認証なしで 401"""
        resp = client.get("/api/v1/knowledge/recent")
        assert resp.status_code == 401

    def test_knowledge_tags_without_auth(self, client):
        """GET /knowledge/tags - 認証なしで 401"""
        resp = client.get("/api/v1/knowledge/tags")
        assert resp.status_code == 401

    def test_knowledge_favorites_without_auth(self, client):
        """GET /knowledge/favorites - 認証なしで 401"""
        resp = client.get("/api/v1/knowledge/favorites")
        assert resp.status_code == 401

    def test_knowledge_search_without_auth(self, client):
        """GET /knowledge/search - 認証なしで 401"""
        resp = client.get("/api/v1/knowledge/search?query=test")
        assert resp.status_code == 401

    def test_knowledge_put_without_auth(self, client):
        """PUT /knowledge/1 - 認証なしで 401"""
        resp = client.put("/api/v1/knowledge/1", json={"title": "テスト"})
        assert resp.status_code == 401

    def test_knowledge_delete_without_auth(self, client):
        """DELETE /knowledge/1 - 認証なしで 401"""
        resp = client.delete("/api/v1/knowledge/1")
        assert resp.status_code == 401


class TestUpdateKnowledgeAdditional:
    """PUT /api/v1/knowledge/{id} - 更新後の状態確認"""

    def test_update_knowledge_title_reflected(self, client, auth_headers):
        """更新後に title がレスポンスに反映される"""
        resp = client.put(
            "/api/v1/knowledge/1",
            json={"title": "更新後タイトル確認"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["title"] == "更新後タイトル確認"

    def test_update_knowledge_response_has_updated_at(self, client, auth_headers):
        """更新後のレスポンスに updated_at が含まれる"""
        resp = client.put(
            "/api/v1/knowledge/1",
            json={"title": "更新日時確認"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "updated_at" in data["data"]

    def test_update_knowledge_multiple_fields(self, client, auth_headers):
        """複数フィールドを同時に更新できる"""
        resp = client.put(
            "/api/v1/knowledge/1",
            json={
                "title": "複合更新タイトル",
                "summary": "複合更新サマリー",
                "status": "published",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["title"] == "複合更新タイトル"
        assert data["summary"] == "複合更新サマリー"
        assert data["status"] == "published"


class TestDeleteKnowledgeAdditional:
    """DELETE /api/v1/knowledge/{id} - 削除後の状態確認"""

    def test_delete_knowledge_returns_deleted_data(self, client, auth_headers):
        """削除後のレスポンスに削除されたデータが含まれる"""
        resp = client.delete("/api/v1/knowledge/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        # 削除されたナレッジデータが返る
        assert "data" in data
        assert data["data"]["id"] == 1

    def test_delete_knowledge_disappears_from_list(self, client, auth_headers):
        """削除したナレッジが一覧から消える"""
        # 削除実行
        client.delete("/api/v1/knowledge/1", headers=auth_headers)
        # 一覧取得
        list_resp = client.get("/api/v1/knowledge", headers=auth_headers)
        items = list_resp.get_json()["data"]
        ids = [item["id"] for item in items]
        assert 1 not in ids

    def test_delete_knowledge_double_delete_returns_404(self, client, auth_headers):
        """同じナレッジを2回削除すると2回目は 404"""
        client.delete("/api/v1/knowledge/1", headers=auth_headers)
        resp = client.delete("/api/v1/knowledge/1", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_knowledge_response_has_message(self, client, auth_headers):
        """削除レスポンスに message フィールドが含まれる"""
        resp = client.delete("/api/v1/knowledge/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "message" in data
