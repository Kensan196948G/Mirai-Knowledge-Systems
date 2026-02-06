

def test_login_success(client):
    """正常ログインテスト"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert "token" in data["data"]
    assert "user" in data["data"]


def test_login_invalid_username(client):
    """無効なユーザー名でのログインテスト"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "invalid", "password": "admin123"}
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_login_invalid_password(client):
    """無効なパスワードでのログインテスト"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_login_missing_fields(client):
    """必須フィールド欠如でのログインテスト"""
    response = client.post("/api/v1/auth/login", json={"username": "admin"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_protected_endpoint_without_token(client):
    """トークンなしでの保護されたエンドポイントアクセステスト"""
    response = client.get("/api/v1/knowledge")
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token(client):
    """無効なトークンでの保護されたエンドポイントアクセステスト"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/knowledge", headers=headers)
    assert response.status_code == 422  # JWT decode error


def test_protected_endpoint_with_valid_token(client, auth_headers):
    """有効なトークンでの保護されたエンドポイントアクセステスト"""
    response = client.get("/api/v1/knowledge", headers=auth_headers)
    assert response.status_code == 200
