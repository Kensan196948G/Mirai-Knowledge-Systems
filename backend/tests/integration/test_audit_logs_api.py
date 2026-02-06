"""
監査ログAPIの統合テスト
"""




class TestAuditLogsAPI:
    """監査ログAPIのテスト"""

    def test_get_access_logs_admin(self, client, auth_headers):
        """管理者が監査ログを取得できる"""
        response = client.get("/api/v1/logs/access", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "logs" in data
        assert "pagination" in data
        assert "filters" in data

    def test_get_access_logs_pagination(self, client, auth_headers):
        """監査ログのページネーションが機能する"""
        response = client.get(
            "/api/v1/logs/access?page=1&per_page=5", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["pagination"]["per_page"] == 5
        assert data["pagination"]["page"] == 1

    def test_get_access_logs_filter_action(self, client, auth_headers):
        """アクションでフィルタリングできる"""
        response = client.get("/api/v1/logs/access?action=login", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        # フィルタが適用されていることを確認
        assert data["filters"]["action"] == "login"

    def test_get_access_logs_filter_status(self, client, auth_headers):
        """ステータスでフィルタリングできる"""
        response = client.get(
            "/api/v1/logs/access?status=success", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["filters"]["status"] == "success"

    def test_get_access_logs_non_admin_forbidden(
        self, client, create_test_users, viewer_token
    ):
        """一般ユーザーは監査ログにアクセスできない"""
        headers = {"Authorization": f"Bearer {viewer_token}"}
        response = client.get("/api/v1/logs/access", headers=headers)
        assert response.status_code == 403

    def test_get_access_logs_unauthenticated(self, client):
        """未認証ユーザーは監査ログにアクセスできない"""
        response = client.get("/api/v1/logs/access")
        assert response.status_code == 401

    def test_get_access_logs_stats_admin(self, client, auth_headers):
        """管理者が監査ログ統計を取得できる"""
        response = client.get("/api/v1/logs/access/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "total_logs" in data
        assert "today_logs" in data
        assert "week_logs" in data
        assert "by_action" in data
        assert "by_status" in data
        assert "top_active_users" in data

    def test_get_access_logs_stats_non_admin_forbidden(
        self, client, create_test_users, viewer_token
    ):
        """一般ユーザーは監査ログ統計にアクセスできない"""
        headers = {"Authorization": f"Bearer {viewer_token}"}
        response = client.get("/api/v1/logs/access/stats", headers=headers)
        assert response.status_code == 403

    def test_get_access_logs_max_per_page(self, client, auth_headers):
        """per_pageの最大値が制限される（200件まで）"""
        response = client.get("/api/v1/logs/access?per_page=500", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        # 最大200件に制限される
        assert data["pagination"]["per_page"] <= 200

    def test_get_access_logs_sort_order(self, client, auth_headers):
        """ソート順序が指定できる"""
        # 降順（デフォルト）
        response = client.get("/api/v1/logs/access?sort=desc", headers=auth_headers)
        assert response.status_code == 200

        # 昇順
        response = client.get("/api/v1/logs/access?sort=asc", headers=auth_headers)
        assert response.status_code == 200
