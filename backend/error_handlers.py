"""
エラーハンドラー＆JWTコールバック
Phase L-1: app_v2.py から抽出

標準化されたエラーレスポンス形式と、Flask/JWT のエラーハンドラーを提供する。
"""

import logging

from flask import jsonify
from werkzeug.exceptions import UnsupportedMediaType

logger = logging.getLogger(__name__)


def error_response(message, code="ERROR", status_code=400, details=None):
    """
    標準化されたエラーレスポンスを返す

    Args:
        message: エラーメッセージ
        code: エラーコード（例: 'NOT_FOUND', 'VALIDATION_ERROR'）
        status_code: HTTPステータスコード
        details: 追加のエラー詳細情報

    Returns:
        tuple: (JSONレスポンス, HTTPステータスコード)
    """
    response = {"success": False, "error": {"code": code, "message": message}}

    if details:
        response["error"]["details"] = details

    logger.error("%s: %s (status=%d)", code, message, status_code)

    return jsonify(response), status_code


def register_error_handlers(app, jwt):
    """Flask アプリケーションにエラーハンドラーを登録する

    Args:
        app: Flask アプリケーションインスタンス
        jwt: JWTManager インスタンス
    """

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """全ての未処理例外をキャッチ"""
        import traceback

        logger.error("Unexpected error: %s: %s", type(e).__name__, e)
        logger.error("Unexpected error traceback:\n%s", traceback.format_exc())
        return error_response("Internal server error", "INTERNAL_ERROR", 500)

    @app.errorhandler(404)
    def not_found(error):
        return error_response("Resource not found", "NOT_FOUND", 404)

    @app.errorhandler(500)
    def internal_error(error):
        return error_response("Internal server error", "INTERNAL_ERROR", 500)

    @app.errorhandler(429)
    def ratelimit_handler(error):
        """レート制限エラーハンドラ"""
        retry_after = (
            str(error.description) if hasattr(error, "description") else "60 seconds"
        )
        return error_response(
            "リクエストが多すぎます。しばらく待ってから再試行してください。",
            "RATE_LIMIT_EXCEEDED",
            429,
            {"retry_after": retry_after},
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        """405 Method Not Allowedエラーハンドラ"""
        return error_response(
            "The method is not allowed for the requested URL",
            "METHOD_NOT_ALLOWED",
            405,
        )

    @app.errorhandler(415)
    def unsupported_media_type(error):
        """415 Unsupported Media Typeエラーハンドラ"""
        return error_response(
            "Unsupported Media Type. Content-Type must be application/json",
            "UNSUPPORTED_MEDIA_TYPE",
            415,
        )

    @app.errorhandler(UnsupportedMediaType)
    def unsupported_media_type_exception(error):
        """UnsupportedMediaType例外ハンドラ"""
        return error_response(
            "Unsupported Media Type. Content-Type must be application/json",
            "UNSUPPORTED_MEDIA_TYPE",
            415,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response("Token has expired", "TOKEN_EXPIRED", 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return error_response("Invalid token", "INVALID_TOKEN", 401)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return error_response("Authorization token is missing", "MISSING_TOKEN", 401)
