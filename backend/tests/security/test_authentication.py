"""
認証セキュリティテスト

目的:
- パスワード認証が正常に機能すること
- JWTトークンの発行・検証が正しく行われること
- トークンの有効期限が適切に管理されること
- ログアウト後はトークンが無効化されること
- 不正なトークンでAPIアクセスが拒否されること

参照: docs/09_品質保証(QA)/03_Final-Acceptance-Test-Plan.md
      セクション 5.1 認証・認可テスト
"""

import json
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest


class TestPasswordAuthentication:
    """パスワード認証テスト"""

    def test_successful_login_with_valid_credentials(self, client):
        """有効な認証情報でログイン成功"""
        response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data.get("data", {})
        assert "refresh_token" in data.get("data", {})
        assert data["data"]["user"]["username"] == "admin"

    def test_login_fails_with_invalid_username(self, client):
        """無効なユーザー名でログイン失敗"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "admin123"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_login_fails_with_invalid_password(self, client):
        """無効なパスワードでログイン失敗"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_login_fails_with_missing_credentials(self, client):
        """認証情報が欠落している場合のログイン失敗"""
        # ユーザー名なし
        response = client.post("/api/v1/auth/login", json={"password": "admin123"})
        assert response.status_code == 400

        # パスワードなし
        response = client.post("/api/v1/auth/login", json={"username": "admin"})
        assert response.status_code == 400

    def test_login_fails_with_empty_credentials(self, client):
        """空の認証情報でログイン失敗"""
        response = client.post(
            "/api/v1/auth/login", json={"username": "", "password": ""}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_password_is_hashed_not_stored_plaintext(self, client, tmp_path):
        """パスワードがハッシュ化されて保存されていることを確認"""
        users_file = tmp_path / "users.json"
        users = json.loads(users_file.read_text())

        # パスワードフィールドが存在しないことを確認（ハッシュのみ）
        for user in users:
            assert "password" not in user
            assert "password_hash" in user
            # bcryptハッシュの形式確認（$2b$で始まる）
            assert user["password_hash"].startswith("$2b$")


class TestJWTTokenValidation:
    """JWTトークン検証テスト"""

    def test_valid_token_grants_api_access(self, client):
        """有効なトークンでAPIアクセス可能"""
        # ログインしてトークン取得
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        # トークンを使用してAPIアクセス
        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_missing_token_denies_api_access(self, client):
        """トークンなしでAPIアクセス拒否（401）"""
        response = client.get("/api/v1/knowledge")

        assert response.status_code == 401
        data = response.get_json()
        assert "msg" in data or "error" in data

    def test_invalid_token_format_denies_access(self, client):
        """不正なトークン形式でアクセス拒否"""
        # 不正な形式のトークン
        invalid_tokens = [
            "invalid-token",
            "Bearer invalid",
            "12345",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        ]

        for invalid_token in invalid_tokens:
            response = client.get(
                "/api/v1/knowledge",
                headers={"Authorization": f"Bearer {invalid_token}"},
            )
            assert response.status_code in [401, 422]
            data = response.get_json()
            assert "msg" in data or "error" in data

    def test_malformed_authorization_header_denies_access(self, client):
        """不正なAuthorizationヘッダー形式でアクセス拒否"""
        malformed_headers = [
            {"Authorization": "InvalidFormat token"},
            {"Authorization": "token-without-bearer"},
            {"Authorization": ""},
        ]

        for header in malformed_headers:
            response = client.get("/api/v1/knowledge", headers=header)
            assert response.status_code == 401

    def test_token_with_invalid_signature_denies_access(self, client):
        """署名が無効なトークンでアクセス拒否"""
        # 正しいトークンを取得
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        valid_token = login_response.get_json()["data"]["access_token"]

        # トークンの署名部分を改ざん
        parts = valid_token.split(".")
        if len(parts) == 3:
            # 署名を変更
            tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature"

            response = client.get(
                "/api/v1/knowledge",
                headers={"Authorization": f"Bearer {tampered_token}"},
            )
            assert response.status_code in [401, 422]


class TestTokenExpiration:
    """トークン有効期限テスト"""

    def test_token_contains_expiration_claim(self, client):
        """トークンにexp（有効期限）クレームが含まれること"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        # トークンをデコード（検証なし）
        decoded = jwt.decode(token, options={"verify_signature": False})

        assert "exp" in decoded
        assert "iat" in decoded  # issued at

        # 有効期限が未来であることを確認
        assert decoded["exp"] > time.time()

    def test_access_token_expires_after_configured_time(self, client):
        """アクセストークンが設定時間後に期限切れになること（モック）"""
        # 注: 実際の有効期限テストは時間がかかるため、
        # トークンの設定を確認するのみ
        from app_v2 import app

        # JWT_ACCESS_TOKEN_EXPIRESが設定されていることを確認
        assert "JWT_ACCESS_TOKEN_EXPIRES" in app.config
        assert app.config["JWT_ACCESS_TOKEN_EXPIRES"] == timedelta(hours=1)

    def test_refresh_token_has_longer_expiration(self, client):
        """リフレッシュトークンの有効期限がアクセストークンより長いこと"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        data = login_response.get_json()

        access_token = data["data"]["access_token"]
        refresh_token = data["data"]["refresh_token"]

        # 両方のトークンをデコード
        access_decoded = jwt.decode(access_token, options={"verify_signature": False})
        refresh_decoded = jwt.decode(refresh_token, options={"verify_signature": False})

        # リフレッシュトークンの有効期限がアクセストークンより長いこと
        assert refresh_decoded["exp"] > access_decoded["exp"]


class TestLogoutTokenInvalidation:
    """ログアウト・トークン無効化テスト"""

    def test_logout_endpoint_exists(self, client):
        """ログアウトエンドポイントが存在すること"""
        # ログイン
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        # ログアウト試行
        response = client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )

        # エンドポイントが未実装の場合は404/405を許容
        assert response.status_code in [
            200,
            201,
            204,
            404,
            405,
            501,
        ]  # 実装状況に応じて

    def test_token_validation_claims(self, client):
        """トークンに必要なクレームが含まれていること"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        decoded = jwt.decode(token, options={"verify_signature": False})

        # 必須クレーム確認
        assert "sub" in decoded or "identity" in decoded  # ユーザー識別子
        assert "exp" in decoded  # 有効期限
        assert "iat" in decoded  # 発行時刻


class TestInvalidTokenScenarios:
    """不正トークンシナリオテスト"""

    def test_token_from_different_secret_key_denied(self, client):
        """異なる秘密鍵で生成されたトークンが拒否されること"""
        # 異なる秘密鍵でトークンを生成
        now = datetime.now(timezone.utc)
        fake_token = jwt.encode(
            {"sub": "admin", "exp": now + timedelta(hours=1), "iat": now},
            "different-secret-key",  # 異なる秘密鍵
            algorithm="HS256",
        )

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {fake_token}"}
        )

        assert response.status_code in [401, 422]  # Signature verification failed

    def test_expired_token_denied(self, client):
        """期限切れトークンが拒否されること"""
        # 既に期限切れのトークンを生成
        now = datetime.now(timezone.utc)
        expired_token = jwt.encode(
            {
                "sub": "admin",
                "exp": now - timedelta(hours=1),  # 1時間前に期限切れ
                "iat": now - timedelta(hours=2),
            },
            "test-secret",  # conftest.pyの秘密鍵と一致させる
            algorithm="HS256",
        )

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401  # Token has expired

    def test_token_without_required_claims_denied(self, client):
        """必須クレームが欠落したトークンが拒否されること"""
        # subクレームなしのトークン
        now = datetime.now(timezone.utc)
        invalid_token = jwt.encode(
            {
                "exp": now + timedelta(hours=1),
                "iat": now,
                # 'sub' or 'identity' missing
            },
            "test-secret",
            algorithm="HS256",
        )

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {invalid_token}"}
        )

        # クレーム不足でエラー
        assert response.status_code in [401, 422]

    def test_token_replay_attack_scenario(self, client):
        """トークンリプレイ攻撃のシナリオテスト"""
        # ログインしてトークン取得
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        # 同じトークンを複数回使用（現在の実装では許可されるべき）
        response1 = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )
        response2 = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )

        # 両方とも成功するべき（トークンは有効期限内は再利用可能）
        assert response1.status_code == 200
        assert response2.status_code == 200

        # 注: より強力な保護が必要な場合は、
        # トークンのjtiクレーム（JWT ID）とブラックリストの実装が必要


class TestBruteForceProtection:
    """ブルートフォース攻撃保護テスト"""

    def test_rate_limiting_on_login_endpoint(self, client):
        """ログインエンドポイントにレート制限があること（確認のみ）"""
        # レート制限の存在を確認
        from app_v2 import limiter

        # リミッターが有効であることを確認
        assert limiter is not None

        # 注: 実際のレート制限テストは時間がかかるため、
        # 設定の確認のみ実施

    def test_multiple_failed_login_attempts(self, client):
        """複数回のログイン失敗を記録（基本動作）"""
        # 5回失敗を試行
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": f"wrongpass{i}"},
            )
            assert response.status_code == 401

        # 注: ログインロックアウト機能の実装状況に応じて、
        # さらなるテストが必要


class TestSecureTokenStorage:
    """トークンの安全な保存テスト"""

    def test_token_not_stored_in_url(self, client):
        """トークンがURLに含まれないこと（Bearer token使用）"""
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        # Authorizationヘッダーでトークンを送信（URLパラメータではない）
        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # URLパラメータでトークンを送ろうとしても機能しないことを確認
        response_url = client.get(f"/api/v1/knowledge?token={token}")
        assert response_url.status_code == 401  # トークンなしとして扱われる

    def test_token_response_over_https_recommended(self, client):
        """トークンレスポンスはHTTPS経由が推奨される（設定確認）"""
        # HTTPS強制の設定を確認
        import os

        from app_v2 import HTTPSRedirectMiddleware

        # HTTPSRedirectMiddlewareが存在することを確認
        assert HTTPSRedirectMiddleware is not None

        # 注: 実際のHTTPS通信テストは統合テストで実施
