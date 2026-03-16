"""
エラーハンドラーのユニットテスト
Phase L-1: error_handlers.py のテストカバレッジ
"""
import datetime
import pytest
from unittest.mock import MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, jwt_required
from error_handlers import error_response, register_error_handlers


# ---------------------------------------------------------------------------
# テスト用フィクスチャ: app_v2 に依存せず error_handlers.py を直接テスト
# ---------------------------------------------------------------------------

@pytest.fixture()
def eh_app():
    """error_handlers をロードした最小限の Flask アプリ。
    ハンドラー登録時に全ての内部ハンドラー関数を capture する。
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key-minimum-32-chars-ok"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
    jwt = JWTManager(app)

    # @app.errorhandler(415) は @app.errorhandler(UnsupportedMediaType) によって
    # 上書きされる。直接呼び出しでカバレッジを取得するため、関数を capture する。
    original_errorhandler = app.errorhandler
    _captured_handlers = {}

    def tracking_errorhandler(code_or_exception):
        decorator = original_errorhandler(code_or_exception)
        def wrapper(f):
            _captured_handlers[code_or_exception] = f
            return decorator(f)
        return wrapper

    app.errorhandler = tracking_errorhandler
    register_error_handlers(app, jwt)
    app.errorhandler = original_errorhandler

    # テストから参照できるよう app に付与
    app._test_captured_handlers = _captured_handlers

    # JWT 保護ルート（JWT ハンドラーのテスト用）
    @app.route("/protected")
    @jwt_required()
    def protected():
        return "ok"

    # 未処理例外（Exception ハンドラーのテスト用）
    @app.route("/trigger-exception")
    def trigger_exception():
        raise ValueError("unexpected test error")

    # 500 エラー直接発生（500 ハンドラーのテスト用）
    @app.route("/trigger-500")
    def trigger_500():
        from werkzeug.exceptions import InternalServerError
        raise InternalServerError()

    # 429 エラー（レート制限ハンドラーのテスト用）
    @app.route("/trigger-429")
    def trigger_429():
        from werkzeug.exceptions import TooManyRequests
        raise TooManyRequests()

    # 415 エラー（メディアタイプハンドラーのテスト用）
    @app.route("/trigger-415", methods=["POST"])
    def trigger_415():
        from werkzeug.exceptions import UnsupportedMediaType
        raise UnsupportedMediaType()

    # UnsupportedMediaType 例外ハンドラーのテスト用（werkzeug.exceptions 経由）
    @app.route("/trigger-unsupported-media", methods=["POST"])
    def trigger_unsupported_media():
        from werkzeug.exceptions import UnsupportedMediaType as UMT
        raise UMT()

    return app


@pytest.fixture()
def eh_client(eh_app):
    with eh_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# TestErrorResponse: error_response ヘルパー関数
# ---------------------------------------------------------------------------

class TestErrorResponse:
    """error_response 関数のテスト"""

    def test_basic_error_response(self, eh_client, eh_app):
        """基本的なエラーレスポンスの形式"""
        with eh_app.app_context():
            response, status = error_response("Test error", "TEST_ERROR", 400)
            data = response.get_json()
            assert status == 400
            assert data["success"] is False
            assert data["error"]["code"] == "TEST_ERROR"
            assert data["error"]["message"] == "Test error"

    def test_error_response_with_details(self, eh_client, eh_app):
        """詳細情報付きエラーレスポンス"""
        with eh_app.app_context():
            details = {"field": "username", "reason": "too short"}
            response, status = error_response("Validation failed", "VALIDATION_ERROR", 422, details)
            data = response.get_json()
            assert status == 422
            assert data["error"]["details"] == details

    def test_error_response_without_details(self, eh_client, eh_app):
        """詳細情報なしの場合はdetailsキーがない"""
        with eh_app.app_context():
            response, status = error_response("Not found", "NOT_FOUND", 404)
            data = response.get_json()
            assert "details" not in data["error"]

    def test_error_response_500(self, eh_client, eh_app):
        """500エラーレスポンス"""
        with eh_app.app_context():
            response, status = error_response("Internal error", "INTERNAL_ERROR", 500)
            assert status == 500

    def test_error_response_401(self, eh_client, eh_app):
        """401エラーレスポンス"""
        with eh_app.app_context():
            response, status = error_response("Token expired", "TOKEN_EXPIRED", 401)
            data = response.get_json()
            assert status == 401
            assert data["error"]["code"] == "TOKEN_EXPIRED"

    def test_error_response_details_none_not_included(self, eh_client, eh_app):
        """details=None の場合、レスポンスに details キーが含まれない"""
        with eh_app.app_context():
            response, status = error_response("msg", "CODE", 400, details=None)
            data = response.get_json()
            assert "details" not in data["error"]

    def test_error_response_details_dict_included(self, eh_client, eh_app):
        """details が辞書の場合、レスポンスに details キーが含まれる"""
        with eh_app.app_context():
            response, status = error_response("msg", "CODE", 400, details={"k": "v"})
            data = response.get_json()
            assert data["error"]["details"] == {"k": "v"}

    def test_error_response_429_with_details(self, eh_client, eh_app):
        """429 レート制限レスポンスに retry_after が含まれる"""
        with eh_app.app_context():
            response, status = error_response(
                "Too many requests",
                "RATE_LIMIT_EXCEEDED",
                429,
                {"retry_after": "60 seconds"},
            )
            data = response.get_json()
            assert status == 429
            assert data["error"]["details"]["retry_after"] == "60 seconds"


# ---------------------------------------------------------------------------
# TestRegisterErrorHandlers: Flask に登録されたハンドラーの動作テスト
# ---------------------------------------------------------------------------

class TestRegisterErrorHandlers:
    """register_error_handlers のテスト"""

    def test_404_handler(self, eh_client):
        """404エラーハンドラーが正しく動作"""
        response = eh_client.get("/nonexistent-endpoint-xyz")
        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_404_handler_message(self, eh_client):
        """404 エラーメッセージが正しい"""
        response = eh_client.get("/not-exist")
        data = response.get_json()
        assert data["error"]["message"] == "Resource not found"

    def test_405_handler(self, eh_client):
        """405エラーハンドラーが正しく動作（GET 専用ルートに POST）"""
        response = eh_client.post("/protected")
        assert response.status_code == 405
        data = response.get_json()
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_405_handler_message(self, eh_client):
        """405 エラーメッセージが正しい"""
        response = eh_client.post("/protected")
        data = response.get_json()
        assert "method is not allowed" in data["error"]["message"].lower()

    def test_500_handler(self, eh_client):
        """500エラーハンドラーが正しく動作"""
        response = eh_client.get("/trigger-500")
        assert response.status_code == 500
        data = response.get_json()
        assert data["error"]["code"] == "INTERNAL_ERROR"

    def test_500_handler_message(self, eh_client):
        """500 エラーメッセージが正しい"""
        response = eh_client.get("/trigger-500")
        data = response.get_json()
        assert "Internal server error" in data["error"]["message"]

    def test_unexpected_exception_handler(self, eh_client):
        """未処理例外ハンドラーが500を返す"""
        response = eh_client.get("/trigger-exception")
        assert response.status_code == 500
        data = response.get_json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["success"] is False

    def test_429_handler(self, eh_client):
        """429 レート制限エラーハンドラーが正しく動作"""
        response = eh_client.get("/trigger-429")
        assert response.status_code == 429
        data = response.get_json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_429_handler_retry_after_in_details(self, eh_client):
        """429 レスポンスに retry_after が含まれる"""
        response = eh_client.get("/trigger-429")
        data = response.get_json()
        assert "details" in data["error"]
        assert "retry_after" in data["error"]["details"]

    def test_415_handler(self, eh_client):
        """415 Unsupported Media Type エラーハンドラーが正しく動作"""
        response = eh_client.post(
            "/trigger-415",
            data="not json",
            content_type="text/plain",
        )
        assert response.status_code == 415
        data = response.get_json()
        assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    def test_415_handler_message(self, eh_client):
        """415 エラーメッセージが正しい"""
        response = eh_client.post(
            "/trigger-415",
            data="not json",
            content_type="text/plain",
        )
        data = response.get_json()
        assert "application/json" in data["error"]["message"]

    def test_unsupported_media_type_exception_handler(self, eh_client):
        """UnsupportedMediaType 例外ハンドラーが正しく動作"""
        response = eh_client.post(
            "/trigger-unsupported-media",
            data="plain",
            content_type="text/plain",
        )
        assert response.status_code == 415
        data = response.get_json()
        assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    # JWT ハンドラー

    def test_missing_token(self, eh_client):
        """トークン未指定のハンドリング"""
        response = eh_client.get("/protected")
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_TOKEN"

    def test_invalid_token(self, eh_client):
        """無効なトークンのハンドリング"""
        response = eh_client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_expired_token(self, eh_client):
        """期限切れトークンのハンドリング"""
        import jwt as pyjwt

        expired_payload = {
            "sub": "user1",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=60),
            "jti": "test-jti-expired",
            "type": "access",
            "fresh": False,
        }
        expired_token = pyjwt.encode(
            expired_payload, "test-secret-key-minimum-32-chars-ok", algorithm="HS256"
        )
        response = eh_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "TOKEN_EXPIRED"

    def test_expired_token_message(self, eh_client):
        """期限切れトークンのエラーメッセージが正しい"""
        import jwt as pyjwt

        expired_payload = {
            "sub": "user1",
            "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=60),
            "jti": "test-jti-expired-2",
            "type": "access",
            "fresh": False,
        }
        expired_token = pyjwt.encode(
            expired_payload, "test-secret-key-minimum-32-chars-ok", algorithm="HS256"
        )
        response = eh_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        data = response.get_json()
        assert "expired" in data["error"]["message"].lower()

    def test_invalid_token_message(self, eh_client):
        """無効トークンのエラーメッセージが正しい"""
        response = eh_client.get(
            "/protected",
            headers={"Authorization": "Bearer bad.token.xyz"},
        )
        data = response.get_json()
        assert "Invalid token" in data["error"]["message"]

    def test_missing_token_message(self, eh_client):
        """トークン未指定のエラーメッセージが正しい"""
        response = eh_client.get("/protected")
        data = response.get_json()
        assert "Authorization token is missing" in data["error"]["message"]

    # app_v2 経由のテスト（後方互換）

    def test_404_handler_via_app_v2(self, client):
        """404エラーハンドラーが正しく動作 (app_v2 経由)"""
        response = client.get("/nonexistent-endpoint-xyz")
        assert response.status_code == 404
        data = response.get_json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_405_handler_via_app_v2(self, client):
        """405エラーハンドラーが正しく動作 (app_v2 経由)"""
        response = client.delete("/api/v1/health")
        assert response.status_code == 405
        data = response.get_json()
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_missing_token_via_app_v2(self, client):
        """トークン未指定のハンドリング (app_v2 経由)"""
        response = client.get("/api/v1/knowledge")
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_TOKEN"


# ---------------------------------------------------------------------------
# TestOverwrittenHandlers: Flask の優先順位で上書きされたハンドラーを直接テスト
# ---------------------------------------------------------------------------

class TestOverwrittenHandlers:
    """Flask が @errorhandler(UnsupportedMediaType) で上書きする
    @errorhandler(415) ハンドラーを直接呼び出してカバレッジを補完するテスト。
    """

    def test_http_415_handler_direct_call(self, eh_app):
        """@app.errorhandler(415) の関数本体を直接呼び出してカバレッジを取得"""
        # @app.errorhandler(UnsupportedMediaType) が @app.errorhandler(415) を Flask 内で
        # 上書きするため、通常のリクエスト経由では unsupported_media_type 関数(line 89)
        # に到達できない。ここでは capture した関数を直接呼び出す。
        captured = eh_app._test_captured_handlers
        handler_fn = captured.get(415)
        assert handler_fn is not None, "@app.errorhandler(415) handler was not captured"

        with eh_app.app_context():
            mock_error = MagicMock()
            response, status = handler_fn(mock_error)
            data = response.get_json()
            assert status == 415
            assert data["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
            assert "application/json" in data["error"]["message"]
