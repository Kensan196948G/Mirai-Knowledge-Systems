"""
エラーハンドラーのユニットテスト
Phase L-1: error_handlers.py のテストカバレッジ
"""
import pytest
from unittest.mock import MagicMock
from error_handlers import error_response, register_error_handlers


class TestErrorResponse:
    """error_response 関数のテスト"""

    def test_basic_error_response(self, client):
        """基本的なエラーレスポンスの形式"""
        import app_v2
        with app_v2.app.app_context():
            response, status = error_response("Test error", "TEST_ERROR", 400)
            data = response.get_json()
            assert status == 400
            assert data["success"] is False
            assert data["error"]["code"] == "TEST_ERROR"
            assert data["error"]["message"] == "Test error"

    def test_error_response_with_details(self, client):
        """詳細情報付きエラーレスポンス"""
        import app_v2
        with app_v2.app.app_context():
            details = {"field": "username", "reason": "too short"}
            response, status = error_response("Validation failed", "VALIDATION_ERROR", 422, details)
            data = response.get_json()
            assert status == 422
            assert data["error"]["details"] == details

    def test_error_response_without_details(self, client):
        """詳細情報なしの場合はdetailsキーがない"""
        import app_v2
        with app_v2.app.app_context():
            response, status = error_response("Not found", "NOT_FOUND", 404)
            data = response.get_json()
            assert "details" not in data["error"]

    def test_error_response_500(self, client):
        """500エラーレスポンス"""
        import app_v2
        with app_v2.app.app_context():
            response, status = error_response("Internal error", "INTERNAL_ERROR", 500)
            assert status == 500

    def test_error_response_401(self, client):
        """401エラーレスポンス"""
        import app_v2
        with app_v2.app.app_context():
            response, status = error_response("Token expired", "TOKEN_EXPIRED", 401)
            data = response.get_json()
            assert status == 401
            assert data["error"]["code"] == "TOKEN_EXPIRED"


class TestRegisterErrorHandlers:
    """register_error_handlers のテスト"""

    def test_404_handler(self, client):
        """404エラーハンドラーが正しく動作"""
        response = client.get("/nonexistent-endpoint-xyz")
        assert response.status_code == 404
        data = response.get_json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_405_handler(self, client):
        """405エラーハンドラーが正しく動作"""
        response = client.delete("/api/v1/health")
        assert response.status_code == 405
        data = response.get_json()
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_expired_token(self, client):
        """期限切れトークンのハンドリング"""
        response = client.get(
            "/api/v1/knowledge",
            headers={"Authorization": "Bearer expired.token.here"}
        )
        assert response.status_code in (401, 422)

    def test_missing_token(self, client):
        """トークン未指定のハンドリング"""
        response = client.get("/api/v1/knowledge")
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_TOKEN"
