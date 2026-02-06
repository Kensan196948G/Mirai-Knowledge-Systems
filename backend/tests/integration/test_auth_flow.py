"""
認証フローの統合テスト

Note: This module uses the 'client' fixture from conftest.py
"""



class TestAuthFlow:
    """認証フロー統合テスト"""

    def test_login_success_flow(self, client):
        """ログイン成功フロー"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["username"] == "admin"

    def test_login_failure_invalid_credentials(self, client):
        """認証失敗（無効な認証情報）"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False

    def test_protected_endpoint_without_token_returns_401(self, client):
        """トークンなしで保護されたエンドポイントにアクセス→401"""
        response = client.get("/api/v1/knowledge")
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token_returns_200(self, client):
        """有効なトークンで保護されたエンドポイントにアクセス→200"""
        # ログイン
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        # 保護されたエンドポイントにアクセス
        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_token_refresh_flow(self, client):
        """トークンリフレッシュフロー"""
        # ログイン
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        refresh_token = login_response.get_json()["data"]["refresh_token"]

        # トークンリフレッシュ
        response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
