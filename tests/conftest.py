import os
import sys
import tempfile

import pytest

# テスト環境変数を設定
os.environ.setdefault(
    "MKS_JWT_SECRET_KEY", "test-secret-key-for-jwt-tokens-minimum-32-chars"
)
os.environ.setdefault("MKS_SECRET_KEY", "test-secret-key-for-sessions-minimum-32-chars")
os.environ.setdefault("MKS_DATA_DIR", tempfile.mkdtemp())
os.environ.setdefault("MKS_CORS_ORIGINS", "http://localhost:5100")
os.environ.setdefault("MKS_ENV", "development")
os.environ.setdefault("MKS_FORCE_HTTPS", "false")
os.environ.setdefault("MKS_HSTS_ENABLED", "false")
os.environ.setdefault("MKS_USE_POSTGRESQL", "false")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from faker import Faker


@pytest.fixture
def test_db():
    """テスト用 SQLite データベース"""
    # JSONモードでテストするため、init_dbは呼ばない
    yield


@pytest.fixture
def client():
    """Flask テストクライアント"""
    # テスト用に環境変数を設定
    os.environ["TESTING"] = "true"

    from backend.app_v2 import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        # テスト用ユーザーデータを初期化
        import bcrypt

        test_users = [
            {
                "id": 1,
                "username": "admin",
                "password_hash": bcrypt.hashpw(
                    "admin123".encode(), bcrypt.gensalt()
                ).decode(),
                "full_name": "管理者",
                "department": "システム管理部",
                "email": "admin@company.local",
                "roles": ["admin"],
                "is_active": True,
            }
        ]
        from backend.app_v2 import save_data

        save_data("users.json", test_users)
        yield client


@pytest.fixture
def auth_headers(client):
    """JWT 認証ヘッダー"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.get_json()
    token = data["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_knowledge():
    """サンプルナレッジデータ"""
    fake = Faker()
    return {
        "title": fake.sentence(),
        "content": fake.text(),
        "category": "施工計画",
        "author": fake.name(),
    }
