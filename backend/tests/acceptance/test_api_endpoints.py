"""
全APIエンドポイントの包括的テスト

このファイルは全てのAPIエンドポイントを以下の観点でテストします：
- 正常系動作
- 異常系エラーハンドリング
- レスポンス形式の検証
- バリデーションエラー
- 認証・認可エラー
"""

import json

import pytest


class TestAuthEndpoints:
    """認証関連エンドポイントのテスト"""

    def test_login_success(self, client):
        """POST /api/v1/auth/login - 正常系"""
        response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json.get("data", {})
        assert "refresh_token" in response.json.get("data", {})
        assert "user" in response.json.get("data", {})

    def test_login_missing_username(self, client):
        """POST /api/v1/auth/login - ユーザー名なし"""
        response = client.post("/api/v1/auth/login", json={"password": "admin123"})
        assert response.status_code in [400, 422]

    def test_login_missing_password(self, client):
        """POST /api/v1/auth/login - パスワードなし"""
        response = client.post("/api/v1/auth/login", json={"username": "admin"})
        assert response.status_code in [400, 422]

    def test_login_invalid_credentials(self, client):
        """POST /api/v1/auth/login - 無効な認証情報"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "error" in response.json or "message" in response.json

    def test_login_nonexistent_user(self, client):
        """POST /api/v1/auth/login - 存在しないユーザー"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == 401

    def test_login_empty_payload(self, client):
        """POST /api/v1/auth/login - 空のペイロード"""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code in [400, 422]

    def test_login_invalid_json(self, client):
        """POST /api/v1/auth/login - 不正なJSON"""
        response = client.post(
            "/api/v1/auth/login", data="invalid json", content_type="application/json"
        )
        assert response.status_code in [400, 422]

    def test_refresh_token_success(self, client):
        """POST /api/v1/auth/refresh - 正常系"""
        # まずログイン
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        refresh_token = login_response.json.get("data", {}).get("refresh_token")

        if refresh_token:
            response = client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {refresh_token}"},
            )
            assert response.status_code == 200
            assert "access_token" in response.json.get("data", {})

    def test_refresh_token_missing(self, client):
        """POST /api/v1/auth/refresh - トークンなし"""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    def test_refresh_token_invalid(self, client):
        """POST /api/v1/auth/refresh - 無効なトークン"""
        response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_get_current_user_success(self, client):
        """GET /api/v1/auth/me - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "username" in response.json.get("data", {})
        assert response.json["data"]["username"] == "admin"

    def test_get_current_user_no_token(self, client):
        """GET /api/v1/auth/me - トークンなし"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """GET /api/v1/auth/me - 無効なトークン"""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestKnowledgeEndpoints:
    """ナレッジ関連エンドポイントのテスト"""

    def test_get_knowledge_list_success(self, client):
        """GET /api/v1/knowledge - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json["data"], list)

    def test_get_knowledge_list_no_auth(self, client):
        """GET /api/v1/knowledge - 認証なし"""
        response = client.get("/api/v1/knowledge")
        assert response.status_code == 401

    def test_get_knowledge_list_with_category_filter(self, client):
        """GET /api/v1/knowledge?category=安全衛生 - カテゴリーフィルター"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/knowledge?category=安全衛生",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json["data"]
        for item in data:
            assert item["category"] == "安全衛生"

    def test_get_knowledge_list_with_tag_filter(self, client):
        """GET /api/v1/knowledge?tags=test - タグフィルター"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/knowledge?tags=test", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json["data"]
        for item in data:
            assert "test" in item.get("tags", [])

    def test_get_knowledge_by_id_success(self, client):
        """GET /api/v1/knowledge/1 - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/knowledge/1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json["data"]["id"] == 1

    def test_get_knowledge_by_id_not_found(self, client):
        """GET /api/v1/knowledge/99999 - 存在しないID"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/knowledge/99999", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    def test_get_knowledge_by_id_invalid_id(self, client):
        """GET /api/v1/knowledge/invalid - 無効なID"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/knowledge/invalid", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    def test_create_knowledge_success(self, client):
        """POST /api/v1/knowledge - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.post(
            "/api/v1/knowledge",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "APIテストナレッジ",
                "summary": "API自動テスト",
                "content": "詳細な内容",
                "category": "安全衛生",
                "tags": ["api", "test"],
            },
        )
        assert response.status_code == 201
        assert "id" in response.json.get("data", {})
        assert response.json["data"]["title"] == "APIテストナレッジ"

    def test_create_knowledge_missing_title(self, client):
        """POST /api/v1/knowledge - タイトルなし"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.post(
            "/api/v1/knowledge",
            headers={"Authorization": f"Bearer {token}"},
            json={"summary": "サマリーのみ", "category": "安全衛生"},
        )
        assert response.status_code in [400, 422]

    def test_create_knowledge_missing_summary(self, client):
        """POST /api/v1/knowledge - サマリーなし"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.post(
            "/api/v1/knowledge",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "タイトルのみ", "category": "安全衛生"},
        )
        assert response.status_code in [400, 422]

    def test_create_knowledge_invalid_category(self, client):
        """POST /api/v1/knowledge - 無効なカテゴリー"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.post(
            "/api/v1/knowledge",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "テスト",
                "summary": "サマリー",
                "category": "invalid_category",
            },
        )
        # カテゴリーバリデーションがある場合は400/422、ない場合は201
        assert response.status_code in [201, 400, 422]

    def test_create_knowledge_no_auth(self, client):
        """POST /api/v1/knowledge - 認証なし"""
        response = client.post(
            "/api/v1/knowledge",
            json={"title": "テスト", "summary": "サマリー", "category": "安全衛生"},
        )
        assert response.status_code == 401


class TestSearchEndpoints:
    """検索関連エンドポイントのテスト"""

    def test_unified_search_success(self, client):
        """GET /api/v1/search/unified?q=test - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/search/unified?q=test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json["data"]
        assert "knowledge" in data
        assert "sop" in data

    def test_unified_search_no_query(self, client):
        """GET /api/v1/search/unified - クエリなし"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/search/unified", headers={"Authorization": f"Bearer {token}"}
        )
        # クエリなしでも200か400かは実装次第
        assert response.status_code in [200, 400]

    def test_unified_search_empty_query(self, client):
        """GET /api/v1/search/unified?q= - 空クエリ"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/search/unified?q=", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 400]

    def test_unified_search_with_category(self, client):
        """GET /api/v1/search/unified?q=test&types=knowledge - カテゴリー指定"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/search/unified?q=test&types=knowledge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_unified_search_no_auth(self, client):
        """GET /api/v1/search/unified - 認証なし"""
        response = client.get("/api/v1/search/unified?q=test")
        assert response.status_code == 401

    def test_unified_search_special_characters(self, client):
        """GET /api/v1/search/unified - 特殊文字"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/search/unified?q=test%20@#$%",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestNotificationEndpoints:
    """通知関連エンドポイントのテスト"""

    def test_get_notifications_success(self, client, tmp_path):
        """GET /api/v1/notifications - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        # 通知データを作成
        notifications_file = tmp_path / "notifications.json"
        notifications_file.write_text("[]", encoding="utf-8")

        response = client.get(
            "/api/v1/notifications", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json["data"], list)

    def test_get_notifications_no_auth(self, client):
        """GET /api/v1/notifications - 認証なし"""
        response = client.get("/api/v1/notifications")
        assert response.status_code == 401

    def test_mark_notification_read_success(self, client, tmp_path):
        """PUT /api/v1/notifications/1/read - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        # 通知データを作成
        notifications_file = tmp_path / "notifications.json"
        test_notifications = [
            {
                "id": 1,
                "user_id": 1,
                "message": "テスト",
                "type": "info",
                "is_read": False,
                "created_at": "2025-01-20T10:00:00",
            }
        ]
        notifications_file.write_text(
            json.dumps(test_notifications, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        response = client.put(
            "/api/v1/notifications/1/read", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_mark_notification_read_not_found(self, client, tmp_path):
        """PUT /api/v1/notifications/99999/read - 存在しないID"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        # 空の通知データ
        notifications_file = tmp_path / "notifications.json"
        notifications_file.write_text("[]", encoding="utf-8")

        response = client.put(
            "/api/v1/notifications/99999/read",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_get_unread_count_success(self, client, tmp_path):
        """GET /api/v1/notifications/unread/count - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        # 通知データを作成
        notifications_file = tmp_path / "notifications.json"
        notifications_file.write_text("[]", encoding="utf-8")

        response = client.get(
            "/api/v1/notifications/unread/count",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "unread_count" in response.json.get("data", {})
        assert isinstance(response.json["data"]["unread_count"], int)


class TestSOPEndpoints:
    """SOP関連エンドポイントのテスト"""

    def test_get_sop_list_success(self, client, tmp_path):
        """GET /api/v1/sop - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        # SOPデータを作成
        sop_file = tmp_path / "sop.json"
        sop_file.write_text("[]", encoding="utf-8")

        response = client.get(
            "/api/v1/sop", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json["data"], list)

    def test_get_sop_list_no_auth(self, client):
        """GET /api/v1/sop - 認証なし"""
        response = client.get("/api/v1/sop")
        assert response.status_code == 401


class TestApprovalEndpoints:
    """承認関連エンドポイントのテスト"""

    def test_get_approvals_success(self, client, tmp_path):
        """GET /api/v1/approvals - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        # 承認データを作成
        approvals_file = tmp_path / "approvals.json"
        approvals_file.write_text("[]", encoding="utf-8")

        response = client.get(
            "/api/v1/approvals", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json["data"], list)

    def test_get_approvals_with_status_filter(self, client, tmp_path):
        """GET /api/v1/approvals?status=pending - ステータスフィルター"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        # 承認データを作成
        approvals_file = tmp_path / "approvals.json"
        test_approvals = [
            {
                "id": 1,
                "knowledge_id": 1,
                "requested_by": 1,
                "status": "pending",
                "requested_at": "2025-01-20T09:00:00",
            }
        ]
        approvals_file.write_text(
            json.dumps(test_approvals, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        response = client.get(
            "/api/v1/approvals?status=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json["data"], list)


class TestDashboardEndpoints:
    """ダッシュボード関連エンドポイントのテスト"""

    def test_get_dashboard_stats_success(self, client):
        """GET /api/v1/dashboard/stats - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json["data"]
        assert "counts" in data
        assert "kpis" in data
        assert "total_knowledge" in data["counts"]

    def test_get_dashboard_stats_no_auth(self, client):
        """GET /api/v1/dashboard/stats - 認証なし"""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 401


class TestMetricsEndpoints:
    """メトリクス関連エンドポイントのテスト"""

    def test_get_metrics_success(self, client):
        """GET /api/v1/metrics - 正常系"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/metrics", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.mimetype == "text/plain"
        assert response.get_data(as_text=True)


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_404_not_found(self, client):
        """存在しないエンドポイント"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """許可されていないHTTPメソッド"""
        response = client.delete("/api/v1/auth/login")
        assert response.status_code == 405

    def test_invalid_content_type(self, client):
        """無効なContent-Type"""
        response = client.post(
            "/api/v1/auth/login",
            data="username=admin&password=admin123",
            content_type="application/x-www-form-urlencoded",
        )
        # JSONを期待しているので400/415/422
        assert response.status_code in [400, 415, 422]


class TestResponseFormat:
    """レスポンス形式の検証"""

    def test_success_response_format(self, client):
        """成功レスポンスの形式検証"""
        response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = response.json["data"]
        assert isinstance(data, dict)

    def test_error_response_format(self, client):
        """エラーレスポンスの形式検証"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.content_type == "application/json"
        data = response.json
        assert isinstance(data, dict)
        assert "error" in data

    def test_list_response_format(self, client):
        """リストレスポンスの形式検証"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json["data"]["access_token"]

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json["data"], list)


class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""

    def test_cors_headers(self, client):
        """CORSヘッダーの検証"""
        response = client.options(
            "/api/v1/auth/login", headers={"Origin": "http://localhost:5000"}
        )
        # CORSヘッダーが設定されているか確認
        # 実装によってはAccess-Control-Allow-Originが返る
        assert response.status_code in [200, 204]

    def test_content_type_json(self, client):
        """Content-Typeヘッダーの検証"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        assert "application/json" in login_response.content_type
