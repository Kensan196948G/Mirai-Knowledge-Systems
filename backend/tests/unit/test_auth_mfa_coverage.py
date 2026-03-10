"""
blueprints/auth.py MFA エンドポイントカバレッジ強化テスト

対象（未カバーの主要パス）:
  POST /api/v1/auth/login             - MFA有効ユーザーのログイン (lines 91-96)
  POST /api/v1/auth/login/mfa         - MFAログイン (lines 145, 190-202, 217-329)
  POST /api/v1/auth/mfa/verify        - MFA検証 no-body (line 552)
  POST /api/v1/auth/mfa/setup         - MFAセットアップ (lines 420-458)
  POST /api/v1/auth/mfa/enable        - MFA有効化 (lines 480-526)
  POST /api/v1/auth/mfa/disable       - MFA無効化 (lines 732-836)
  POST /api/v1/auth/mfa/backup-codes/regenerate (lines 849-902)
  GET  /api/v1/auth/mfa/status        - MFAステータス (lines 924-937)
  POST /api/v1/auth/mfa/recovery      - ユーザー発見時 (lines 1004-1019)
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ============================================================
# モッククラス
# ============================================================


class MockUser:
    """PostgreSQL ORM User オブジェクトのモック"""

    def __init__(
        self,
        mfa_enabled=False,
        mfa_secret=None,
        mfa_backup_codes=None,
        user_id=1,
        password="admin123",
    ):
        self.id = user_id
        self.username = "admin"
        self.email = "admin@example.com"
        self.full_name = "Admin User"
        self.is_active = True
        self.mfa_enabled = mfa_enabled
        self.mfa_secret = mfa_secret
        self.mfa_backup_codes = mfa_backup_codes
        self.roles = []
        self._password = password

    def check_password(self, password):
        return password == self._password


class MockDAL:
    """DAL のモック"""

    def __init__(self, user=None):
        self.user = user
        self._committed = False

    def get_user_by_id(self, user_id):
        return self.user

    def commit(self):
        self._committed = True


class MockTOTPManagerFalse:
    """verify_totp が常に False を返す TOTP モック"""

    def verify_totp(self, secret, code):
        return False

    def verify_backup_code(self, code_hash, backup_code):
        return False

    def generate_totp_secret(self):
        return "TESTSECRET12345678"

    def generate_qr_code(self, email, secret):
        return "dGVzdHFyY29kZQ=="  # base64 "testqrcode"

    def generate_backup_codes(self, count=10):
        return [f"BACKUP{i:04d}" for i in range(count)]

    def prepare_backup_codes_for_storage(self, codes):
        return [{"code_hash": f"hash_{c}", "used": False} for c in codes]

    def get_provisioning_uri(self, email, secret):
        return f"otpauth://totp/Mirai:{email}?secret={secret}&issuer=Mirai"


class MockTOTPManagerTrue:
    """verify_totp が常に True を返す TOTP モック"""

    def verify_totp(self, secret, code):
        return True

    def verify_backup_code(self, code_hash, backup_code):
        return False

    def generate_totp_secret(self):
        return "TESTSECRET12345678"

    def generate_qr_code(self, email, secret):
        return "dGVzdHFyY29kZQ=="

    def generate_backup_codes(self, count=10):
        return [f"BACKUP{i:04d}" for i in range(count)]

    def prepare_backup_codes_for_storage(self, codes):
        return [{"code_hash": f"hash_{c}", "used": False} for c in codes]

    def get_provisioning_uri(self, email, secret):
        return f"otpauth://totp/Mirai:{email}?secret={secret}&issuer=Mirai"


# ============================================================
# MFA有効ユーザー用フィクスチャ
# ============================================================


@pytest.fixture()
def mfa_user_client(client, tmp_path):
    """users.json に MFA 有効ユーザーを追加したクライアント"""
    import app_v2

    users = [
        {
            "id": 1,
            "username": "admin",
            "password_hash": app_v2.hash_password("admin123"),
            "full_name": "Admin User",
            "department": "Admin",
            "roles": ["admin"],
        },
        {
            "id": 3,
            "username": "mfauser",
            "password_hash": app_v2.hash_password("mfa123"),
            "full_name": "MFA User",
            "email": "mfa@example.com",
            "roles": ["admin"],
            "mfa_enabled": True,
            "mfa_secret": "JBSWY3DPEHPK3PXP",  # テスト用 TOTP シークレット
        },
    ]
    (tmp_path / "users.json").write_text(
        json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return client


# ============================================================
# MFA 有効ユーザーのログイン（lines 91-96）
# ============================================================


class TestLoginMfaRequired:
    """POST /api/v1/auth/login - MFA 有効ユーザーのログイン"""

    def test_mfa_required_returns_mfa_token(self, mfa_user_client):
        """MFA 有効ユーザーのログインで mfa_required=True と mfa_token が返る"""
        resp = mfa_user_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "mfa123"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["mfa_required"] is True
        assert "mfa_token" in data["data"]

    def test_mfa_required_no_access_token(self, mfa_user_client):
        """MFA 有効ユーザーのログインでは access_token が返らない"""
        resp = mfa_user_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "mfa123"},
        )
        data = resp.get_json()
        assert "access_token" not in data.get("data", {})

    def test_mfa_required_message_included(self, mfa_user_client):
        """MFA 有効ユーザーのログインで message が含まれる"""
        resp = mfa_user_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "mfa123"},
        )
        data = resp.get_json()
        assert "message" in data["data"]

    def test_mfa_token_is_string(self, mfa_user_client):
        """mfa_token は非空の文字列"""
        resp = mfa_user_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "mfa123"},
        )
        data = resp.get_json()
        token = data["data"]["mfa_token"]
        assert isinstance(token, str)
        assert len(token) > 10


# ============================================================
# /login/mfa エンドポイント (lines 145, 190-202, 217-329)
# ============================================================


class TestLoginMfaEndpoint:
    """POST /api/v1/auth/login/mfa - 各パスのカバレッジ"""

    def test_no_body_returns_400(self, client):
        """空 JSON ボディで 400（line 145）— {} は Python で falsy → if not data が True"""
        resp = client.post("/api/v1/auth/login/mfa", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_REQUEST"

    def test_regular_token_as_mfa_token_returns_invalid_mfa_token(self, client):
        """通常の access_token を mfa_token として送ると INVALID_MFA_TOKEN（lines 190-202）"""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_resp.get_json()["data"]["access_token"]

        resp = client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": access_token, "code": "123456"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_MFA_TOKEN"

    def test_mfa_user_invalid_totp_returns_401(self, mfa_user_client):
        """MFA 有効ユーザーの mfa_token + 無効な TOTP → 401（lines 217-329）"""
        # Step 1: login → mfa_token 取得
        login_resp = mfa_user_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "mfa123"},
        )
        mfa_token = login_resp.get_json()["data"]["mfa_token"]

        # Step 2: 無効な TOTP で MFA ログイン
        resp = mfa_user_client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": mfa_token, "code": "000000"},
        )
        # mfa_secret が設定されているので MFA_NOT_CONFIGURED ではなく INVALID_MFA_CODE
        assert resp.status_code in (400, 401)
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] in ("INVALID_MFA_CODE", "MFA_NOT_CONFIGURED")

    def test_mfa_user_missing_code_returns_400(self, mfa_user_client):
        """mfa_token はあるが code も backup_code もない場合 400"""
        login_resp = mfa_user_client.post(
            "/api/v1/auth/login",
            json={"username": "mfauser", "password": "mfa123"},
        )
        mfa_token = login_resp.get_json()["data"]["mfa_token"]

        resp = mfa_user_client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": mfa_token},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_CODE"


# ============================================================
# /mfa/verify - ボディなし (line 552)
# ============================================================


class TestVerifyMfaLoginNoBody:
    """POST /api/v1/auth/mfa/verify - ボディなしのケース"""

    def test_no_body_returns_400(self, client):
        """空 JSON ボディで 400（line 552）— {} は Python で falsy"""
        resp = client.post("/api/v1/auth/mfa/verify", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_REQUEST"

    def test_validate_alias_no_body_returns_400(self, client):
        """/mfa/validate エイリアスでも空ボディで 400"""
        resp = client.post("/api/v1/auth/mfa/validate", json={})
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_REQUEST"

    def test_verify_with_regular_token_returns_invalid(self, client):
        """通常の access_token を mfa_token として送ると 401（lines 591-606）"""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_resp.get_json()["data"]["access_token"]

        resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": access_token, "code": "123456"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "INVALID_MFA_TOKEN"


# ============================================================
# /mfa/setup - DAL モック (lines 420-458)
# ============================================================


class TestSetupMfa:
    """POST /api/v1/auth/mfa/setup - DAL モックを使用"""

    def test_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """get_dal().get_user_by_id() が None を返す → 404"""
        import blueprints.auth as auth_mod

        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=None))
        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        assert resp.status_code == 404
        assert resp.get_json()["error"]["code"] == "USER_NOT_FOUND"

    def test_mfa_already_enabled_returns_400(self, client, auth_headers, monkeypatch):
        """MFA が既に有効なユーザーは 400 MFA_ALREADY_ENABLED"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MFA_ALREADY_ENABLED"

    def test_setup_mfa_success(self, client, auth_headers, monkeypatch):
        """MFA 未有効ユーザーのセットアップが成功する"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerFalse)

        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "secret" in data["data"]
        assert "qr_code_base64" in data["data"]
        assert "backup_codes" in data["data"]
        assert "provisioning_uri" in data["data"]

    def test_setup_mfa_backup_codes_are_list(self, client, auth_headers, monkeypatch):
        """バックアップコードはリスト形式"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerFalse)

        resp = client.post("/api/v1/auth/mfa/setup", headers=auth_headers)
        backup_codes = resp.get_json()["data"]["backup_codes"]
        assert isinstance(backup_codes, list)
        assert len(backup_codes) > 0

    def test_setup_mfa_no_auth_returns_401(self, client):
        """認証なしで 401"""
        resp = client.post("/api/v1/auth/mfa/setup")
        assert resp.status_code == 401


# ============================================================
# /mfa/enable - DAL モック (lines 480-526)
# ============================================================


class TestEnableMfa:
    """POST /api/v1/auth/mfa/enable - DAL モックを使用"""

    def test_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """ユーザーが存在しない → 404"""
        import blueprints.auth as auth_mod

        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=None))
        resp = client.post(
            "/api/v1/auth/mfa/enable", headers=auth_headers, json={"code": "123456"}
        )
        assert resp.status_code == 404

    def test_missing_code_returns_400(self, client, auth_headers, monkeypatch):
        """code なしで 400 MISSING_CODE"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/enable", headers=auth_headers, json={}
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_CODE"

    def test_mfa_not_setup_returns_400(self, client, auth_headers, monkeypatch):
        """mfa_secret が未設定 → 400 MFA_NOT_SETUP"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False, mfa_secret=None)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/enable",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MFA_NOT_SETUP"

    def test_invalid_totp_returns_400(self, client, auth_headers, monkeypatch):
        """無効な TOTP コード → 400 INVALID_CODE"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False, mfa_secret="TESTSECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerFalse)

        resp = client.post(
            "/api/v1/auth/mfa/enable",
            headers=auth_headers,
            json={"code": "000000"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_CODE"

    def test_valid_totp_enables_mfa(self, client, auth_headers, monkeypatch):
        """正しい TOTP コード → 200 で MFA 有効化"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False, mfa_secret="TESTSECRET")
        dal = MockDAL(user=user)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: dal)
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerTrue)

        resp = client.post(
            "/api/v1/auth/mfa/enable",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert user.mfa_enabled is True
        assert dal._committed is True

    def test_no_auth_returns_401(self, client):
        """認証なしで 401"""
        resp = client.post("/api/v1/auth/mfa/enable", json={"code": "123456"})
        assert resp.status_code == 401


# ============================================================
# /mfa/disable - DAL モック (lines 732-836)
# ============================================================


class TestDisableMfa:
    """POST /api/v1/auth/mfa/disable - DAL モックを使用"""

    def test_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """ユーザーが存在しない → 404"""
        import blueprints.auth as auth_mod

        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=None))
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "123456"},
        )
        assert resp.status_code == 404

    def test_mfa_not_enabled_returns_400(self, client, auth_headers, monkeypatch):
        """MFA が無効なユーザー → 400 MFA_NOT_ENABLED"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "123456"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MFA_NOT_ENABLED"

    def test_no_body_returns_400(self, client, auth_headers, monkeypatch):
        """空 JSON ボディで 400 — {} は Python で falsy"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post("/api/v1/auth/mfa/disable", headers=auth_headers, json={})
        assert resp.status_code == 400

    def test_missing_password_returns_400(self, client, auth_headers, monkeypatch):
        """password なしで 400 MISSING_PASSWORD"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_PASSWORD"

    def test_wrong_password_returns_401(self, client, auth_headers, monkeypatch):
        """パスワード誤り → 401 INVALID_PASSWORD"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "wrongpassword", "code": "123456"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "INVALID_PASSWORD"

    def test_missing_code_returns_400(self, client, auth_headers, monkeypatch):
        """code も backup_code もない → 400 MISSING_CODE"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_CODE"

    def test_invalid_code_returns_401(self, client, auth_headers, monkeypatch):
        """コード誤り → 401 INVALID_CODE"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerFalse)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "000000"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "INVALID_CODE"

    def test_valid_credentials_disables_mfa(self, client, auth_headers, monkeypatch):
        """正しい認証情報で MFA 無効化成功"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        dal = MockDAL(user=user)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: dal)
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerTrue)

        resp = client.post(
            "/api/v1/auth/mfa/disable",
            headers=auth_headers,
            json={"password": "admin123", "code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert user.mfa_enabled is False
        assert user.mfa_secret is None

    def test_no_auth_returns_401(self, client):
        """認証なしで 401"""
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            json={"password": "admin123", "code": "123456"},
        )
        assert resp.status_code == 401


# ============================================================
# /mfa/backup-codes/regenerate - DAL モック (lines 849-902)
# ============================================================


class TestRegenerateBackupCodes:
    """POST /api/v1/auth/mfa/backup-codes/regenerate - DAL モックを使用"""

    def test_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """ユーザーが存在しない → 404"""
        import blueprints.auth as auth_mod

        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=None))
        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 404

    def test_mfa_not_enabled_returns_400(self, client, auth_headers, monkeypatch):
        """MFA が無効 → 400 MFA_NOT_ENABLED"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MFA_NOT_ENABLED"

    def test_missing_code_returns_400(self, client, auth_headers, monkeypatch):
        """code なしで 400 MISSING_CODE"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_CODE"

    def test_invalid_totp_returns_401(self, client, auth_headers, monkeypatch):
        """無効な TOTP → 401 INVALID_CODE"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerFalse)

        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "000000"},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "INVALID_CODE"

    def test_valid_totp_regenerates_codes(self, client, auth_headers, monkeypatch):
        """正しい TOTP で新しいバックアップコードを生成"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=True, mfa_secret="SECRET")
        dal = MockDAL(user=user)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: dal)
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerFalse.__class__)
        monkeypatch.setattr(auth_mod, "TOTPManager", MockTOTPManagerTrue)

        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            headers=auth_headers,
            json={"code": "123456"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "backup_codes" in data["data"]
        assert isinstance(data["data"]["backup_codes"], list)

    def test_no_auth_returns_401(self, client):
        """認証なしで 401"""
        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate", json={"code": "123456"}
        )
        assert resp.status_code == 401


# ============================================================
# /mfa/status - DAL モック (lines 924-937)
# ============================================================


class TestMfaStatus:
    """GET /api/v1/auth/mfa/status - DAL モックを使用"""

    def test_user_not_found_returns_404(self, client, auth_headers, monkeypatch):
        """ユーザーが存在しない → 404"""
        import blueprints.auth as auth_mod

        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=None))
        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert resp.status_code == 404
        assert resp.get_json()["error"]["code"] == "USER_NOT_FOUND"

    def test_mfa_disabled_user_status(self, client, auth_headers, monkeypatch):
        """MFA 無効ユーザーのステータスが返る"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False, mfa_secret=None)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))

        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["mfa_enabled"] is False
        assert data["data"]["mfa_configured"] is False
        assert data["data"]["remaining_backup_codes"] == 0

    def test_mfa_enabled_user_status(self, client, auth_headers, monkeypatch):
        """MFA 有効ユーザーのステータスが返る"""
        import blueprints.auth as auth_mod

        user = MockUser(
            mfa_enabled=True,
            mfa_secret="TESTSECRET",
            mfa_backup_codes=[
                {"code_hash": "h1", "used": False},
                {"code_hash": "h2", "used": True},
                {"code_hash": "h3", "used": False},
            ],
        )
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))

        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["mfa_enabled"] is True
        assert data["data"]["mfa_configured"] is True
        assert data["data"]["remaining_backup_codes"] == 2

    def test_mfa_status_email_included(self, client, auth_headers, monkeypatch):
        """ステータスレスポンスに email が含まれる"""
        import blueprints.auth as auth_mod

        user = MockUser(mfa_enabled=False)
        monkeypatch.setattr(auth_mod, "get_dal", lambda: MockDAL(user=user))

        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        assert "email" in resp.get_json()["data"]

    def test_no_auth_returns_401(self, client):
        """認証なしで 401"""
        resp = client.get("/api/v1/auth/mfa/status")
        assert resp.status_code == 401


# ============================================================
# /mfa/recovery - ユーザー発見時 (lines 1004-1019)
# ============================================================


class TestMfaRecoveryFoundUser:
    """POST /api/v1/auth/mfa/recovery - ユーザーが存在する場合"""

    def test_user_found_mfa_disabled_returns_200(self, client, tmp_path):
        """ユーザー発見・MFA 無効 → 200（line 1004-1008）"""
        import app_v2

        users = [
            {
                "id": 1,
                "username": "admin",
                "password_hash": app_v2.hash_password("admin123"),
                "email": "admin@test.example.com",
                "roles": ["admin"],
                "mfa_enabled": False,
            }
        ]
        (tmp_path / "users.json").write_text(
            json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        resp = client.post(
            "/api/v1/auth/mfa/recovery",
            json={"username": "admin", "email": "admin@test.example.com"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_user_found_mfa_enabled_returns_200(self, client, tmp_path):
        """ユーザー発見・MFA 有効 → 200 + recovery token（lines 1010-1019）"""
        import app_v2

        users = [
            {
                "id": 1,
                "username": "admin",
                "password_hash": app_v2.hash_password("admin123"),
                "email": "admin@test.example.com",
                "roles": ["admin"],
                "mfa_enabled": True,
            }
        ]
        (tmp_path / "users.json").write_text(
            json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        resp = client.post(
            "/api/v1/auth/mfa/recovery",
            json={"username": "admin", "email": "admin@test.example.com"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "message" in data

    def test_recovery_message_is_consistent(self, client, tmp_path):
        """ユーザーが存在しない場合と同じメッセージで情報漏洩を防ぐ"""
        import app_v2

        users = [
            {
                "id": 1,
                "username": "admin",
                "password_hash": app_v2.hash_password("admin123"),
                "email": "admin@test.example.com",
                "roles": ["admin"],
                "mfa_enabled": True,
            }
        ]
        (tmp_path / "users.json").write_text(
            json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # 存在するユーザーへのリクエスト
        resp_found = client.post(
            "/api/v1/auth/mfa/recovery",
            json={"username": "admin", "email": "admin@test.example.com"},
        )
        # 存在しないユーザーへのリクエスト
        resp_notfound = client.post(
            "/api/v1/auth/mfa/recovery",
            json={"username": "nobody", "email": "nobody@example.com"},
        )
        # 両方とも 200 で同じメッセージを返す（タイミング攻撃対策）
        assert resp_found.status_code == 200
        assert resp_notfound.status_code == 200
        assert resp_found.get_json()["message"] == resp_notfound.get_json()["message"]
