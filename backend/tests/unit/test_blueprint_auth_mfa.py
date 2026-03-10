"""
blueprints/auth.py MFA エンドポイント拡張テスト

DAL をモックして MFA エンドポイントの詳細テストを行う。

テスト対象エンドポイント:
  GET  /api/v1/auth/mfa/status                 - MFAステータス取得
  POST /api/v1/auth/mfa/setup                  - MFAセットアップ
  POST /api/v1/auth/mfa/enable                 - MFA有効化
  POST /api/v1/auth/mfa/disable                - MFA無効化
  POST /api/v1/auth/mfa/backup-codes/regenerate - バックアップコード再生成
  POST /api/v1/auth/login                      - MFA有効ユーザーのログイン
  POST /api/v1/auth/login/mfa                  - MFAコード検証（JSONフォールバック）
  POST /api/v1/auth/mfa/verify                 - MFA検証（DALモック）
"""

import json
import os
import sys
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import Config


# ============================================================
# ヘルパー: モックユーザー / モックDAL
# ============================================================


def _make_mock_user(
    id=1,
    username="admin",
    email="admin@test.com",
    mfa_enabled=False,
    mfa_secret=None,
    mfa_backup_codes=None,
    password_ok=True,
    roles=None,
):
    """SQLAlchemy User モデルを模倣したモックを作成する。

    MFA関連エンドポイントは ``dal.get_user_by_id()`` を通じて
    SQLAlchemy ORMオブジェクトを受け取る。このヘルパーで
    MagicMock を使い、必要な属性/メソッドを持つダミーオブジェクトを生成する。
    """
    user = MagicMock()
    user.id = id
    user.username = username
    user.email = email
    user.full_name = "テストユーザー"
    user.is_active = True
    user.mfa_enabled = mfa_enabled
    user.mfa_secret = mfa_secret
    user.mfa_backup_codes = mfa_backup_codes if mfa_backup_codes is not None else []
    user.roles = roles if roles is not None else []
    user.check_password.return_value = password_ok
    return user


def _make_mock_dal(user=None):
    """モック DAL（DataAccessLayer）を生成する。"""
    dal = MagicMock()
    dal.get_user_by_id.return_value = user
    dal.commit.return_value = None
    return dal


# ============================================================
# フィクスチャ: MFA有効ユーザーを持つクライアント
# ============================================================


@pytest.fixture()
def mfa_client(tmp_path, monkeypatch):
    """MFA有効ユーザーを含むテスト用クライアント。

    ``login/mfa`` エンドポイントの JSON フォールバック経路を
    テストするために、mfa_enabled=True のユーザーをJSON で用意する。
    """
    import app_v2
    import app_helpers

    monkeypatch.setattr(app_helpers, "CACHE_ENABLED", False)
    monkeypatch.setattr(Config, "DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MKS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app_helpers, "_dal", None)

    users = [
        {
            "id": 1,
            "username": "mfauser",
            "password_hash": app_v2.hash_password("secret123"),
            "full_name": "MFA User",
            "department": "Test",
            "roles": ["admin"],
            "mfa_enabled": True,
            "mfa_secret": "JBSWY3DPEHPK3PXP",
            "mfa_backup_codes": [
                {"code_hash": "hash_aaa", "used": False},
                {"code_hash": "hash_bbb", "used": True},
            ],
        },
        {
            "id": 2,
            "username": "normaluser",
            "password_hash": app_v2.hash_password("normal123"),
            "full_name": "Normal User",
            "department": "Test",
            "roles": ["admin"],
            "mfa_enabled": False,
        },
    ]
    for fname in ["access_logs.json", "sop.json", "notifications.json"]:
        (tmp_path / fname).write_text("[]", encoding="utf-8")
    (tmp_path / "users.json").write_text(
        json.dumps(users, ensure_ascii=False), encoding="utf-8"
    )

    app = app_v2.app
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key-longer-than-20"
    app_v2.limiter.enabled = False

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def mfa_user_token(mfa_client):
    """MFA有効ユーザーの MFA一時トークン（mfa_required=True 状態）を取得する。"""
    resp = mfa_client.post(
        "/api/v1/auth/login",
        json={"username": "mfauser", "password": "secret123"},
    )
    data = resp.get_json()
    assert data["data"]["mfa_required"] is True
    return data["data"]["mfa_token"]


@pytest.fixture()
def normal_user_token(mfa_client):
    """MFA未設定ユーザーのアクセストークンを取得する。"""
    resp = mfa_client.post(
        "/api/v1/auth/login",
        json={"username": "normaluser", "password": "normal123"},
    )
    return resp.get_json()["data"]["access_token"]


# ============================================================
# POST /api/v1/auth/login - MFA有効ユーザー
# ============================================================


class TestLoginMfaRequired:
    """POST /api/v1/auth/login - MFA有効ユーザーのログイン"""

    def test_mfa_user_returns_mfa_required_true(self, mfa_client):
        """MFA有効ユーザーのログインで mfa_required=True が返る"""
        resp = mfa_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "secret123"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["mfa_required"] is True

    def test_mfa_user_returns_mfa_token(self, mfa_client):
        """MFA有効ユーザーのログインで mfa_token が返る"""
        resp = mfa_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "secret123"},
        )
        data = resp.get_json()
        assert "mfa_token" in data["data"]
        assert isinstance(data["data"]["mfa_token"], str)

    def test_mfa_user_does_not_return_access_token(self, mfa_client):
        """MFA有効ユーザーのログインで access_token は返らない"""
        resp = mfa_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "secret123"},
        )
        data = resp.get_json()
        assert "access_token" not in data["data"]

    def test_non_mfa_user_returns_mfa_required_false(self, mfa_client):
        """MFA未設定ユーザーは mfa_required=False で通常トークンを返す"""
        resp = mfa_client.post(
            "/api/v1/auth/login",
            json={"username": "normaluser", "password": "normal123"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["mfa_required"] is False
        assert "access_token" in data["data"]


# ============================================================
# POST /api/v1/auth/login/mfa - MFAコード検証（JSONフォールバック）
# ============================================================


class TestLoginMfaVerify:
    """POST /api/v1/auth/login/mfa - JSONフォールバック経路のテスト"""

    def test_valid_totp_returns_access_token(self, mfa_client, mfa_user_token, monkeypatch):
        """有効なTOTPコードでアクセストークンが発行される"""
        import blueprints.auth as auth_module

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = True
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = mfa_client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": mfa_user_token, "code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["used_backup_code"] is False

    def test_invalid_totp_returns_401(self, mfa_client, mfa_user_token, monkeypatch):
        """無効なTOTPコードは 401 INVALID_MFA_CODE"""
        import blueprints.auth as auth_module

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = False
        mock_totp_mgr.verify_backup_code.return_value = False
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = mfa_client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": mfa_user_token, "code": "000000"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_MFA_CODE"

    def test_mfa_not_configured_user_returns_400(self, mfa_client, monkeypatch):
        """MFA設定なしユーザーのMFAトークンで 400 MFA_NOT_CONFIGURED"""
        import blueprints.auth as auth_module
        from flask_jwt_extended import create_access_token

        with mfa_client.application.app_context():
            # normaluser(id=2) は mfa_enabled=False
            mfa_token = create_access_token(
                identity="2",
                additional_claims={"mfa_pending": True, "type": "mfa_temp"},
                expires_delta=timedelta(minutes=5),
            )

        resp = mfa_client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": mfa_token, "code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MFA_NOT_CONFIGURED"

    def test_backup_code_login_success(self, mfa_client, mfa_user_token, monkeypatch):
        """有効なバックアップコードでログインできる"""
        import blueprints.auth as auth_module

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = False  # TOTPは失敗
        mock_totp_mgr.verify_backup_code.return_value = True  # バックアップは成功
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = mfa_client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": mfa_user_token, "backup_code": "ABCD-1234"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["used_backup_code"] is True


# ============================================================
# GET /api/v1/auth/mfa/status
# ============================================================


class TestMfaStatus:
    """GET /api/v1/auth/mfa/status - MFAステータス取得"""

    def test_status_mfa_disabled(self, client, auth_headers, monkeypatch):
        """MFA未設定ユーザーのステータスが返る"""
        mock_user = _make_mock_user(mfa_enabled=False, mfa_secret=None)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["mfa_enabled"] is False
        assert data["data"]["mfa_configured"] is False
        assert data["data"]["remaining_backup_codes"] == 0

    def test_status_mfa_enabled_with_backups(self, client, auth_headers, monkeypatch):
        """MFA有効ユーザーのステータスと残バックアップコード数が返る"""
        backup_codes = [
            {"code_hash": "hash1", "used": False},
            {"code_hash": "hash2", "used": False},
            {"code_hash": "hash3", "used": True},
        ]
        mock_user = _make_mock_user(
            mfa_enabled=True, mfa_secret="SECRET123", mfa_backup_codes=backup_codes
        )
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["mfa_enabled"] is True
        assert data["data"]["mfa_configured"] is True
        assert data["data"]["remaining_backup_codes"] == 2  # 使用済み1件を除く

    def test_status_user_not_found(self, client, auth_headers, monkeypatch):
        """ユーザーが存在しない場合は 404"""
        mock_dal = _make_mock_dal(user=None)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "USER_NOT_FOUND"

    def test_status_has_email_field(self, client, auth_headers, monkeypatch):
        """レスポンスに email フィールドが含まれる"""
        mock_user = _make_mock_user(email="user@example.com", mfa_enabled=False)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["email"] == "user@example.com"

    def test_status_requires_auth(self, client):
        """認証なしは 401"""
        resp = client.get("/api/v1/auth/mfa/status")
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/auth/mfa/setup
# ============================================================


class TestMfaSetup:
    """POST /api/v1/auth/mfa/setup - MFAセットアップ"""

    def test_setup_success(self, client, auth_headers, monkeypatch):
        """MFA未設定ユーザーでセットアップが成功する"""
        mock_user = _make_mock_user(mfa_enabled=False)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "secret" in data["data"]
        assert "qr_code_base64" in data["data"]
        assert "backup_codes" in data["data"]
        assert "provisioning_uri" in data["data"]

    def test_setup_backup_codes_count(self, client, auth_headers, monkeypatch):
        """セットアップで10件のバックアップコードが生成される"""
        mock_user = _make_mock_user(mfa_enabled=False)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        data = resp.get_json()
        assert len(data["data"]["backup_codes"]) == 10

    def test_setup_already_enabled_returns_400(self, client, auth_headers, monkeypatch):
        """MFA既に有効なユーザーは 400 MFA_ALREADY_ENABLED"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="EXISTING_SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MFA_ALREADY_ENABLED"

    def test_setup_user_not_found(self, client, auth_headers, monkeypatch):
        """ユーザーが見つからない場合は 404"""
        mock_dal = _make_mock_dal(user=None)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "USER_NOT_FOUND"

    def test_setup_requires_auth(self, client):
        """認証なしは 401"""
        resp = client.post("/api/v1/auth/mfa/setup")
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/auth/mfa/enable
# ============================================================


class TestMfaEnable:
    """POST /api/v1/auth/mfa/enable - MFA有効化"""

    def test_enable_success_with_valid_code(self, client, auth_headers, monkeypatch):
        """有効なTOTPコードでMFAが有効化される"""
        mock_user = _make_mock_user(mfa_enabled=False, mfa_secret="VALID_SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = True
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = client.post(
            "/api/v1/auth/mfa/enable", headers=auth_headers, json={"code": "123456"}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert mock_user.mfa_enabled is True  # フラグがセットされた

    def test_enable_invalid_code_returns_400(self, client, auth_headers, monkeypatch):
        """無効なTOTPコードは 400 INVALID_CODE"""
        mock_user = _make_mock_user(mfa_enabled=False, mfa_secret="VALID_SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = False
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = client.post(
            "/api/v1/auth/mfa/enable", headers=auth_headers, json={"code": "000000"}
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_CODE"

    def test_enable_missing_code_returns_400(self, client, auth_headers, monkeypatch):
        """コードなしは 400 MISSING_CODE"""
        mock_user = _make_mock_user(mfa_enabled=False, mfa_secret="VALID_SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post("/api/v1/auth/mfa/enable", headers=auth_headers, json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MISSING_CODE"

    def test_enable_no_mfa_secret_returns_400(self, client, auth_headers, monkeypatch):
        """MFAセットアップ前の有効化は 400 MFA_NOT_SETUP"""
        mock_user = _make_mock_user(mfa_enabled=False, mfa_secret=None)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/enable", headers=auth_headers, json={"code": "123456"}
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MFA_NOT_SETUP"

    def test_enable_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """ユーザーが見つからない場合は 404"""
        mock_dal = _make_mock_dal(user=None)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/enable", headers=auth_headers, json={"code": "123456"}
        )
        assert resp.status_code == 404

    def test_enable_requires_auth(self, client):
        """認証なしは 401"""
        resp = client.post("/api/v1/auth/mfa/enable", json={"code": "123456"})
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/auth/mfa/disable
# ============================================================


class TestMfaDisable:
    """POST /api/v1/auth/mfa/disable - MFA無効化"""

    def test_disable_success(self, client, auth_headers, monkeypatch):
        """正しいパスワードとTOTPコードでMFAが無効化される"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET", password_ok=True)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = True
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert mock_user.mfa_enabled is False  # 無効化フラグがリセットされた

    def test_disable_wrong_password_returns_401(self, client, auth_headers, monkeypatch):
        """パスワード誤りは 401 INVALID_PASSWORD"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET", password_ok=False)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "wrongpassword", "code": "123456"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_PASSWORD"

    def test_disable_invalid_totp_returns_401(self, client, auth_headers, monkeypatch):
        """無効なTOTPコードは 401 INVALID_CODE"""
        mock_user = _make_mock_user(
            mfa_enabled=True, mfa_secret="SECRET", password_ok=True, mfa_backup_codes=[]
        )
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = False
        mock_totp_mgr.verify_backup_code.return_value = False
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "000000"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_CODE"

    def test_disable_backup_code_accepted(self, client, auth_headers, monkeypatch):
        """有効なバックアップコードでもMFA無効化が可能"""
        mock_user = _make_mock_user(
            mfa_enabled=True,
            mfa_secret="SECRET",
            password_ok=True,
            mfa_backup_codes=[{"code_hash": "hash1", "used": False}],
        )
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = False  # TOTPは失敗
        mock_totp_mgr.verify_backup_code.return_value = True  # バックアップは成功
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "backup_code": "ABCD-1234"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_disable_mfa_not_enabled_returns_400(self, client, auth_headers, monkeypatch):
        """MFA未設定ユーザーは 400 MFA_NOT_ENABLED"""
        mock_user = _make_mock_user(mfa_enabled=False)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MFA_NOT_ENABLED"

    def test_disable_missing_password_returns_400(self, client, auth_headers, monkeypatch):
        """パスワードなしは 400 MISSING_PASSWORD"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MISSING_PASSWORD"

    def test_disable_missing_code_returns_400(self, client, auth_headers, monkeypatch):
        """コードなし（パスワードは正しい）は 400 MISSING_CODE"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET", password_ok=True)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MISSING_CODE"

    def test_disable_no_body_returns_4xx(self, client, auth_headers, monkeypatch):
        """ボディなしは 400 または 415（Content-Type未設定）"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post("/api/v1/auth/mfa/disable", headers=auth_headers)
        assert resp.status_code in (400, 415)

    def test_disable_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """ユーザーが存在しない場合は 404"""
        mock_dal = _make_mock_dal(user=None)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "123456"},
        )
        assert resp.status_code == 404


# ============================================================
# POST /api/v1/auth/mfa/backup-codes/regenerate
# ============================================================


class TestRegenerateBackupCodes:
    """POST /api/v1/auth/mfa/backup-codes/regenerate - バックアップコード再生成"""

    def test_regenerate_success(self, client, auth_headers, monkeypatch):
        """有効なTOTPコードでバックアップコードが再生成される"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = True
        mock_totp_mgr.generate_backup_codes.return_value = [f"code-{i}" for i in range(10)]
        mock_totp_mgr.prepare_backup_codes_for_storage.return_value = [
            {"code_hash": f"hash-{i}", "used": False} for i in range(10)
        ]
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "backup_codes" in data["data"]
        assert len(data["data"]["backup_codes"]) == 10

    def test_regenerate_invalid_code_returns_401(self, client, auth_headers, monkeypatch):
        """無効なTOTPコードは 401 INVALID_CODE"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = False
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "000000"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_CODE"

    def test_regenerate_missing_code_returns_400(self, client, auth_headers, monkeypatch):
        """コードなしは 400 MISSING_CODE"""
        mock_user = _make_mock_user(mfa_enabled=True, mfa_secret="SECRET")
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MISSING_CODE"

    def test_regenerate_mfa_not_enabled_returns_400(self, client, auth_headers, monkeypatch):
        """MFA未設定ユーザーは 400 MFA_NOT_ENABLED"""
        mock_user = _make_mock_user(mfa_enabled=False)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MFA_NOT_ENABLED"

    def test_regenerate_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """ユーザーが存在しない場合は 404"""
        mock_dal = _make_mock_dal(user=None)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 404

    def test_regenerate_requires_auth(self, client):
        """認証なしは 401"""
        resp = client.post("/api/v1/auth/mfa/backup-codes/regenerate", json={"code": "123456"})
        assert resp.status_code == 401


# ============================================================
# POST /api/v1/auth/mfa/verify（DALモック経由）
# ============================================================


class TestMfaVerifyWithDal:
    """POST /api/v1/auth/mfa/verify - DALモック使用テスト"""

    def test_verify_valid_totp_success(self, mfa_client, mfa_user_token, monkeypatch):
        """有効なMFAトークンとTOTPコードで検証成功"""
        mock_user = _make_mock_user(
            id=1, mfa_enabled=True, mfa_secret="SECRET", mfa_backup_codes=[]
        )
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = True
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = mfa_client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_user_token, "code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    def test_verify_user_not_found_returns_404(self, mfa_client, mfa_user_token, monkeypatch):
        """MFAトークンが有効でもDALにユーザーがない場合は 404"""
        mock_dal = _make_mock_dal(user=None)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = mfa_client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_user_token, "code": "123456"},
        )
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"]["code"] == "USER_NOT_FOUND"

    def test_verify_mfa_not_configured_returns_400(self, mfa_client, mfa_user_token, monkeypatch):
        """MFA未設定ユーザーのトークンで 400 MFA_NOT_CONFIGURED"""
        mock_user = _make_mock_user(mfa_enabled=False, mfa_secret=None)
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        resp = mfa_client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_user_token, "code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MFA_NOT_CONFIGURED"

    def test_verify_invalid_totp_returns_401(self, mfa_client, mfa_user_token, monkeypatch):
        """無効なTOTPコードは 401 INVALID_MFA_CODE"""
        mock_user = _make_mock_user(
            id=1, mfa_enabled=True, mfa_secret="SECRET", mfa_backup_codes=[]
        )
        mock_dal = _make_mock_dal(user=mock_user)

        import blueprints.auth as auth_module
        monkeypatch.setattr(auth_module, "get_dal", lambda: mock_dal)

        mock_totp_mgr = MagicMock()
        mock_totp_mgr.verify_totp.return_value = False
        mock_totp_mgr.verify_backup_code.return_value = False
        monkeypatch.setattr(auth_module, "TOTPManager", lambda: mock_totp_mgr)

        resp = mfa_client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": mfa_user_token, "code": "000000"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"]["code"] == "INVALID_MFA_CODE"
