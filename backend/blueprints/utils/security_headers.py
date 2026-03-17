"""
blueprints/utils/security_headers.py - セキュリティヘッダー設定

Phase M-1: app_v2.py から抽出（~73行）
"""

import logging

from flask import request

logger = logging.getLogger(__name__)


def apply_security_headers(response, *, is_production, hsts_enabled=False,
                           hsts_max_age=31536000, hsts_include_subdomains=True):
    """セキュリティヘッダーを追加（本番/開発環境で設定を切り替え）

    Args:
        response: Flask response object
        is_production: 本番環境フラグ
        hsts_enabled: HSTS有効フラグ
        hsts_max_age: HSTS max-age（デフォルト1年）
        hsts_include_subdomains: サブドメイン含むフラグ
    """
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    response.headers.setdefault(
        "Permissions-Policy", "geolocation=(), microphone=(), camera=(), payment=()"
    )

    if is_production:
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )

        if hsts_enabled:
            hsts_value = f"max-age={hsts_max_age}"
            if hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            response.headers.setdefault("Strict-Transport-Security", hsts_value)

        csp_policy = "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "img-src 'self' data: https:",
                "font-src 'self' data: https://fonts.gstatic.com",
                "connect-src 'self' ws: wss:",
                "worker-src 'self'",
                "manifest-src 'self'",
                "object-src 'none'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests",
            ]
        )

        if request.path.startswith("/api/"):
            response.headers.setdefault(
                "Cache-Control", "no-store, no-cache, must-revalidate"
            )
            response.headers.setdefault("Pragma", "no-cache")
    else:
        response.headers.setdefault("Referrer-Policy", "no-referrer")

        csp_policy = "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "img-src 'self' data: https:",
                "font-src 'self' data: https://fonts.gstatic.com",
                "connect-src 'self' ws: wss:",
                "worker-src 'self'",
                "manifest-src 'self'",
                "object-src 'none'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        )

    response.headers.setdefault("Content-Security-Policy", csp_policy)

    return response
