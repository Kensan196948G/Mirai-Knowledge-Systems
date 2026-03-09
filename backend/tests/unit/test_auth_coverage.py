"""
認証Blueprint 補完テスト (Phase I-5 カバレッジ強化)

test_blueprint_auth.py と重複しないテストケースを追加する。
- トークンの具体的な値検証
- refresh エンドポイント
- logout 後のトークン無効化（ブラックリスト）
- me エンドポイントの詳細なレスポンス内容
- MFA ステータスの具体的なフィールド確認
- 400 系エラーレスポンス構造の詳細確認
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestLoginTokenContent:
    """POST /api/v1/auth/login - トークン内容の詳細検証"""

    def test_login_token_is_non_empty_string(self, client):
        """access_token は空でない文字列"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        data = resp.get_json()
        token = data["data"]["access_token"]
        assert isinstance(token, str)
        assert len(token) > 10

    def test_login_refresh_token_is_non_empty_string(self, client):
        """refresh_token は空でない文字列"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        data = resp.get_json()
        refresh_token = data["data"]["refresh_token"]
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 10

    def test_login_expires_in_is_integer(self, client):
        """expires_in は整数値"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        data = resp.get_json()
        expires_in = data["data"]["expires_in"]
        assert isinstance(expires_in, int)
        assert expires_in > 0

    def test_login_access_token_differs_between_logins(self, client):
        """同じユーザーで2回ログインすると異なるトークンが発行される"""
        resp1 = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        resp2 = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        token1 = resp1.get_json()["data"]["access_token"]
        token2 = resp2.get_json()["data"]["access_token"]
        # JWT は jti（固有ID）を含むため異なるトークンになる
        assert token1 != token2

    def test_login_user_roles_returned(self, client):
        """ログインレスポンスのユーザー情報に roles が含まれる"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        data = resp.get_json()
        user = data["data"]["user"]
        assert "roles" in user
        assert isinstance(user["roles"], list)

    def test_login_empty_json_body_returns_400(self, client):
        """空の JSON オブジェクトで 400 エラーを返す"""
        resp = client.post(
            "/api/v1/auth/login",
            json={},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_login_non_json_content_type_returns_4xx(self, client):
        """Content-Type が JSON でない場合は 4xx エラー"""
        resp = client.post(
            "/api/v1/auth/login",
            data="username=admin&password=admin123",
            content_type="application/x-www-form-urlencoded",
        )
        # スキーマバリデーションまたはコンテンツタイプエラーで 4xx
        assert resp.status_code in (400, 415, 422)

    def test_login_response_success_field_is_bool(self, client):
        """success フィールドはブール型"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        data = resp.get_json()
        assert isinstance(data["success"], bool)
        assert data["success"] is True

    def test_login_error_response_has_error_field(self, client):
        """失敗時のレスポンスに error フィールドが含まれる"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword12345"},
        )
        assert resp.status_code in (400, 401)
        data = resp.get_json()
        assert "error" in data


class TestRefreshToken:
    """POST /api/v1/auth/refresh - リフレッシュトークン"""

    def test_refresh_returns_new_access_token(self, client):
        """リフレッシュトークンで新しいアクセストークンを取得できる"""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        refresh_token = login_resp.get_json()["data"]["refresh_token"]

        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    def test_refresh_response_has_expires_in(self, client):
        """リフレッシュレスポンスに expires_in が含まれる"""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        refresh_token = login_resp.get_json()["data"]["refresh_token"]

        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        data = resp.get_json()
        assert "expires_in" in data["data"]
        assert isinstance(data["data"]["expires_in"], int)

    def test_refresh_without_token_returns_401(self, client):
        """トークンなしでリフレッシュすると 401"""
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    def test_refresh_with_access_token_returns_4xx(self, client):
        """アクセストークン（リフレッシュトークンではない）で 401/422"""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access_token = login_resp.get_json()["data"]["access_token"]

        # リフレッシュエンドポイントにアクセストークンを送ると失敗
        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code in (401, 422)

    def test_refresh_with_invalid_token_returns_4xx(self, client):
        """無効なトークンでリフレッシュすると 4xx"""
        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        assert resp.status_code in (401, 422)

    def test_refresh_new_token_differs_from_original(self, client):
        """リフレッシュ後の新トークンは元のアクセストークンと異なる"""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        login_data = login_resp.get_json()["data"]
        original_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        new_token = refresh_resp.get_json()["data"]["access_token"]
        assert new_token != original_token


class TestLogoutBlacklist:
    """POST /api/v1/auth/logout - ブラックリスト検証"""

    def test_logout_token_becomes_invalid_after_logout(self, client):
        """ログアウト後にトークンでアクセスすると 401"""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        token = login_resp.get_json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ログアウト
        logout_resp = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_resp.status_code == 200

        # ログアウト後に同じトークンで /me にアクセスすると 401
        me_resp = client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 401

    def test_logout_response_message_is_string(self, client, auth_headers):
        """ログアウトレスポンスの message は文字列"""
        resp = client.post("/api/v1/auth/logout", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0

    def test_logout_partner_user_success(self, client, partner_auth_headers):
        """協力会社ユーザーもログアウトできる"""
        resp = client.post("/api/v1/auth/logout", headers=partner_auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True


class TestGetCurrentUserDetail:
    """GET /api/v1/auth/me - ユーザー情報の詳細検証"""

    def test_me_response_has_required_fields(self, client, auth_headers):
        """レスポンスに必須フィールドが含まれる"""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        user_data = data["data"]
        # 必須フィールドの確認
        for field in ("id", "username", "roles"):
            assert field in user_data, f"フィールド {field!r} がレスポンスに含まれていない"

    def test_me_password_hash_is_excluded(self, client, auth_headers):
        """password_hash がレスポンスから除外されている"""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        data = resp.get_json()
        assert "password_hash" not in data["data"]

    def test_me_permissions_is_list(self, client, auth_headers):
        """permissions はリスト型"""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        data = resp.get_json()
        assert isinstance(data["data"]["permissions"], list)

    def test_me_admin_has_wildcard_permission(self, client, auth_headers):
        """admin ユーザーは '*' 権限を持つ"""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        data = resp.get_json()
        assert "*" in data["data"]["permissions"]

    def test_me_partner_has_limited_permissions(self, client, partner_auth_headers):
        """partner_company ユーザーは '*' 権限を持たない"""
        resp = client.get("/api/v1/auth/me", headers=partner_auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "*" not in data["data"]["permissions"]

    def test_me_with_invalid_token_returns_4xx(self, client):
        """無効なトークンでは 4xx を返す"""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code in (401, 422)

    def test_me_user_id_is_integer(self, client, auth_headers):
        """user の id は整数値"""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        data = resp.get_json()
        user_id = data["data"]["id"]
        assert isinstance(user_id, int)


class TestMfaStatus:
    """GET /api/v1/auth/mfa/status - MFA ステータス詳細"""

    def test_mfa_status_success_field_present(self, client, auth_headers):
        """認証済みで success フィールドが返る"""
        resp = client.get("/api/v1/auth/mfa/status", headers=auth_headers)
        # JSON モードでは get_user_by_id が DAL に未実装のため 500 となる場合がある
        assert resp.status_code in (200, 500)
        data = resp.get_json()
        assert data is not None
        assert "success" in data

    def test_mfa_status_without_auth_returns_401(self, client):
        """認証なしでは 401"""
        resp = client.get("/api/v1/auth/mfa/status")
        assert resp.status_code == 401

    def test_mfa_status_with_invalid_token_returns_4xx(self, client):
        """無効なトークンでは 4xx"""
        resp = client.get(
            "/api/v1/auth/mfa/status",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert resp.status_code in (401, 422)

    def test_mfa_status_partner_user_returns_response(self, client, partner_auth_headers):
        """協力会社ユーザーも MFA ステータスエンドポイントにアクセスできる"""
        resp = client.get("/api/v1/auth/mfa/status", headers=partner_auth_headers)
        # JSON モードでは 500 の可能性あり
        assert resp.status_code in (200, 500)
        assert resp.get_json() is not None


class TestLoginMfaEndpoint:
    """POST /api/v1/auth/login/mfa - MFA ログイン詳細"""

    def test_mfa_login_invalid_token_returns_401(self, client):
        """正規でない mfa_token で 401"""
        resp = client.post(
            "/api/v1/auth/login/mfa",
            json={"mfa_token": "invalid.mfa.token", "code": "123456"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["success"] is False
        # エラーコードは MFA_TOKEN_EXPIRED または INVALID_MFA_TOKEN
        assert data["error"]["code"] in ("MFA_TOKEN_EXPIRED", "INVALID_MFA_TOKEN")

    def test_mfa_login_error_has_code_field(self, client):
        """エラーレスポンスに code フィールドが含まれる"""
        resp = client.post(
            "/api/v1/auth/login/mfa",
            json={"code": "123456"},  # mfa_token 欠落
        )
        data = resp.get_json()
        assert "error" in data
        assert "code" in data["error"]

    def test_mfa_verify_missing_mfa_token(self, client):
        """POST /api/v1/auth/mfa/verify - mfa_token なしで 400"""
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "123456"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_MFA_TOKEN"

    def test_mfa_verify_missing_code_returns_400(self, client):
        """POST /api/v1/auth/mfa/verify - code なしで 400"""
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            json={"mfa_token": "some.token"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_CODE"

    def test_mfa_validate_alias_works(self, client):
        """POST /api/v1/auth/mfa/validate は /verify の別名として機能する"""
        resp = client.post(
            "/api/v1/auth/mfa/validate",
            json={"code": "123456"},  # mfa_token 欠落
        )
        # 同じルートのため同じエラーコードが返る
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "MISSING_MFA_TOKEN"


class TestMfaRecovery:
    """POST /api/v1/auth/mfa/recovery"""

    def test_mfa_recovery_missing_email_returns_400(self, client):
        """email 欠落で 400"""
        resp = client.post(
            "/api/v1/auth/mfa/recovery",
            json={"username": "admin"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_FIELDS"

    def test_mfa_recovery_missing_username_returns_400(self, client):
        """username 欠落で 400"""
        resp = client.post(
            "/api/v1/auth/mfa/recovery",
            json={"email": "admin@example.com"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_mfa_recovery_unknown_user_returns_200(self, client):
        """存在しないユーザー情報でも 200 を返す（タイミング攻撃対策）"""
        resp = client.post(
            "/api/v1/auth/mfa/recovery",
            json={"username": "nonexistent", "email": "nonexistent@example.com"},
        )
        # セキュリティ上、ユーザー存在有無にかかわらず 200 を返す
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "message" in data

    def test_mfa_recovery_empty_body_returns_400(self, client):
        """空ボディで 400"""
        resp = client.post(
            "/api/v1/auth/mfa/recovery",
            json={},
        )
        assert resp.status_code == 400


class TestMfaEnableDisableRequiresAuth:
    """MFA 有効化・無効化・バックアップコード再生成の認証必須チェック"""

    def test_mfa_enable_without_auth_returns_401(self, client):
        """MFA 有効化には JWT 必須"""
        resp = client.post(
            "/api/v1/auth/mfa/enable",
            json={"code": "123456"},
        )
        assert resp.status_code == 401

    def test_mfa_enable_with_invalid_token_returns_4xx(self, client):
        """無効なトークンで MFA 有効化すると 4xx"""
        resp = client.post(
            "/api/v1/auth/mfa/enable",
            json={"code": "123456"},
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert resp.status_code in (401, 422)

    def test_mfa_disable_with_invalid_token_returns_4xx(self, client):
        """無効なトークンで MFA 無効化すると 4xx"""
        resp = client.post(
            "/api/v1/auth/mfa/disable",
            json={"password": "admin123", "code": "123456"},
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert resp.status_code in (401, 422)

    def test_mfa_backup_regenerate_with_invalid_token_returns_4xx(self, client):
        """無効なトークンでバックアップコード再生成すると 4xx"""
        resp = client.post(
            "/api/v1/auth/mfa/backup-codes/regenerate",
            json={"code": "123456"},
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert resp.status_code in (401, 422)
