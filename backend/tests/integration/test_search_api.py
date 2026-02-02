"""
検索APIの統合テスト
横断検索機能のテスト
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
    """テストクライアント"""
    import app_v2

    app = app_v2.app
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(tmp_path)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app_v2.limiter.enabled = False

    # ユーザー設定
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

    # ナレッジデータ
    knowledge = [
        {
            "id": 1,
            "title": "施工計画の基礎",
            "summary": "建設プロジェクトにおける施工計画の策定方法",
            "content": "施工計画書には工程表、資材計画、安全対策が含まれます。",
            "category": "施工計画",
            "tags": ["計画", "基礎"],
        },
        {
            "id": 2,
            "title": "品質管理マニュアル",
            "summary": "コンクリート工事の品質管理手順",
            "content": "コンクリートの配合、打設、養生について詳しく説明します。",
            "category": "品質管理",
            "tags": ["品質", "コンクリート"],
        },
        {
            "id": 3,
            "title": "安全対策ガイドライン",
            "summary": "現場における安全対策の基本",
            "content": "高所作業、重機作業、火気使用時の安全対策を解説。",
            "category": "安全衛生",
            "tags": ["安全", "ガイドライン"],
        },
    ]

    # SOPデータ
    sop = [
        {
            "id": 1,
            "title": "コンクリート打設手順",
            "content": "コンクリート打設の標準作業手順。品質確保のための注意点。",
        },
        {
            "id": 2,
            "title": "安全帯使用手順",
            "content": "高所作業時の安全帯着用と使用方法。",
        },
    ]

    # インシデントデータ
    incidents = [
        {
            "id": 1,
            "title": "軽微な転倒事故",
            "description": "作業員が足場で転倒。安全対策の見直しが必要。",
        },
        {
            "id": 2,
            "title": "コンクリート打設不良",
            "description": "コンクリートの配合ミスにより品質不良が発生。",
        },
    ]

    _write_json(tmp_path / "users.json", users)
    _write_json(tmp_path / "knowledge.json", knowledge)
    _write_json(tmp_path / "sop.json", sop)
    _write_json(tmp_path / "incidents.json", incidents)
    _write_json(tmp_path / "access_logs.json", [])

    with app.test_client() as test_client:
        yield test_client


def _login(client, username="admin", password="admin123"):
    """ログインヘルパー"""
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    return response.get_json()["data"]["access_token"]


class TestUnifiedSearch:
    """横断検索のテスト"""

    def test_unified_search_requires_query(self, client):
        """クエリパラメータが必須"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "MISSING_QUERY" in data["error"]["code"]

    def test_unified_search_requires_auth(self, client):
        """認証が必要"""
        response = client.get("/api/v1/search/unified?q=test")

        assert response.status_code == 401

    def test_unified_search_returns_knowledge_results(self, client):
        """ナレッジの検索結果を返す"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=施工計画",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "knowledge" in data["data"]
        assert data["data"]["knowledge"]["count"] >= 1
        assert any(
            "施工計画" in item["title"] for item in data["data"]["knowledge"]["items"]
        )

    def test_unified_search_returns_sop_results(self, client):
        """SOPの検索結果を返す"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=コンクリート&types=sop",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "sop" in data["data"]
        assert data["data"]["sop"]["count"] >= 1

    def test_unified_search_returns_incidents_results(self, client):
        """インシデントの検索結果を返す"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=転倒&types=incidents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "incidents" in data["data"]
        assert data["data"]["incidents"]["count"] >= 1

    def test_unified_search_multiple_types(self, client):
        """複数タイプの横断検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=コンクリート&types=knowledge,sop,incidents",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # 全タイプが結果に含まれる
        assert "knowledge" in data["data"]
        assert "sop" in data["data"]
        assert "incidents" in data["data"]

    def test_unified_search_returns_total_count(self, client):
        """総件数が返される"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=コンクリート",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "total_results" in data
        assert data["total_results"] >= 1

    def test_unified_search_returns_query(self, client):
        """検索クエリが返される"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=安全",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["query"] == "安全"

    def test_unified_search_with_highlight(self, client):
        """ハイライト付き検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=品質&highlight=true",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # ハイライトマークが含まれる
        if data["data"]["knowledge"]["count"] > 0:
            items = data["data"]["knowledge"]["items"]
            has_highlight = any(
                "<mark>" in item.get("title", "") or "<mark>" in item.get("summary", "")
                for item in items
            )
            assert has_highlight

    def test_unified_search_results_have_relevance_score(self, client):
        """検索結果に関連性スコアが含まれる"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=施工",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()

        if data["data"]["knowledge"]["count"] > 0:
            for item in data["data"]["knowledge"]["items"]:
                assert "relevance_score" in item

    def test_unified_search_results_sorted_by_relevance(self, client):
        """関連性スコアで降順ソート"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=コンクリート",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()

        if data["data"]["knowledge"]["count"] > 1:
            items = data["data"]["knowledge"]["items"]
            scores = [item["relevance_score"] for item in items]
            assert scores == sorted(scores, reverse=True)

    def test_unified_search_limits_results_per_type(self, client):
        """各タイプの結果は10件まで"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=の",  # 多くヒットするクエリ
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()

        for type_key in ["knowledge", "sop", "incidents"]:
            if type_key in data["data"]:
                assert len(data["data"][type_key]["items"]) <= 10

    def test_unified_search_no_results(self, client):
        """結果がない場合"""
        token = _login(client)

        response = client.get(
            "/api/v1/search/unified?q=存在しないキーワード12345",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["total_results"] == 0


class TestSearchHelperFunctions:
    """検索ヘルパー関数のテスト"""

    def test_search_in_fields_finds_matches(self):
        """search_in_fieldsがマッチを見つける"""
        import app_v2

        item = {
            "title": "Test Title",
            "summary": "Test summary content",
            "content": "Detailed content here",
        }

        matched_fields, score = app_v2.search_in_fields(
            item, "Test", ["title", "summary", "content"]
        )

        assert "title" in matched_fields
        assert "summary" in matched_fields
        assert score > 0

    def test_search_in_fields_case_insensitive(self):
        """検索は大文字小文字を区別しない"""
        import app_v2

        item = {"title": "TEST TITLE", "summary": "Summary"}

        matched_fields, score = app_v2.search_in_fields(
            item, "test", ["title", "summary"]
        )

        assert "title" in matched_fields

    def test_search_in_fields_title_has_higher_score(self):
        """タイトルは高いスコアを持つ"""
        import app_v2

        item1 = {"title": "keyword", "summary": "other", "content": "other"}
        item2 = {"title": "other", "summary": "keyword", "content": "other"}
        item3 = {"title": "other", "summary": "other", "content": "keyword"}

        _, score1 = app_v2.search_in_fields(
            item1, "keyword", ["title", "summary", "content"]
        )
        _, score2 = app_v2.search_in_fields(
            item2, "keyword", ["title", "summary", "content"]
        )
        _, score3 = app_v2.search_in_fields(
            item3, "keyword", ["title", "summary", "content"]
        )

        # title > summary > content
        assert score1 > score2 > score3

    def test_search_in_fields_no_match_returns_empty(self):
        """マッチしない場合は空を返す"""
        import app_v2

        item = {"title": "Hello", "summary": "World"}

        matched_fields, score = app_v2.search_in_fields(
            item, "nomatch", ["title", "summary"]
        )

        assert matched_fields == []
        assert score == 0.0

    def test_highlight_text_wraps_matches(self):
        """highlight_textがマッチをマークで囲む"""
        import app_v2

        text = "This is a test string with test word"
        result = app_v2.highlight_text(text, "test")

        assert "<mark>test</mark>" in result

    def test_highlight_text_case_insensitive(self):
        """ハイライトは大文字小文字を区別しない"""
        import app_v2

        text = "TEST and test and Test"
        result = app_v2.highlight_text(text, "test")

        # 全てのケースがハイライトされる
        assert result.count("<mark>") == 3

    def test_highlight_text_handles_none(self):
        """Noneや空文字を適切に処理"""
        import app_v2

        assert app_v2.highlight_text(None, "test") is None
        assert app_v2.highlight_text("", "test") == ""
        assert app_v2.highlight_text("text", "") == "text"
        assert app_v2.highlight_text("text", None) == "text"


class TestSearchAccessLogging:
    """検索アクセスログのテスト"""

    def test_unified_search_is_logged(self, client, tmp_path):
        """横断検索がログに記録される"""
        token = _login(client)

        client.get(
            "/api/v1/search/unified?q=テスト検索",
            headers={"Authorization": f"Bearer {token}"},
        )

        # ログファイルを確認
        logs_file = tmp_path / "access_logs.json"
        with open(logs_file, "r", encoding="utf-8") as f:
            logs = json.load(f)

        search_logs = [l for l in logs if l["action"] == "search.unified"]
        assert len(search_logs) >= 1
        assert search_logs[-1]["resource"] == "search"
        assert search_logs[-1]["resource_id"] == "テスト検索"


class TestKnowledgeSearchIntegration:
    """ナレッジ検索（/api/v1/knowledge）のテスト"""

    def test_knowledge_search_basic(self, client):
        """基本的なナレッジ検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?search=品質",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # 品質管理マニュアルがヒット
        assert any(
            "品質" in item["title"] or "品質" in item.get("summary", "")
            for item in data["data"]
        )

    def test_knowledge_search_with_category_filter(self, client):
        """カテゴリフィルタ付き検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?search=施工&category=施工計画",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        for item in data["data"]:
            assert item["category"] == "施工計画"

    def test_knowledge_search_with_tags_filter(self, client):
        """タグフィルタ付き検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?tags=安全", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        for item in data["data"]:
            assert "安全" in item["tags"]

    def test_knowledge_search_multiple_tags(self, client):
        """複数タグフィルタ"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?tags=計画,基礎",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # タグのいずれかを含む
        for item in data["data"]:
            assert "計画" in item["tags"] or "基礎" in item["tags"]

    def test_knowledge_search_content_field(self, client):
        """コンテンツフィールドの検索"""
        token = _login(client)

        response = client.get(
            "/api/v1/knowledge?search=養生",  # contentにのみ含まれる
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        # 品質管理マニュアルがヒット（contentに「養生」を含む）
        assert len(data["data"]) >= 1
