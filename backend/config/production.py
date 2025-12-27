"""
建設土木ナレッジシステム - 本番環境設定

使用方法:
    環境変数 MKS_ENV=production を設定してアプリケーションを起動

セキュリティ注意事項:
    - 本番環境では必ず環境変数で秘密鍵を設定すること
    - このファイルには機密情報を直接記載しないこと
"""

import os
from datetime import timedelta


class ProductionConfig:
    """本番環境用設定クラス"""

    # ==========================================================
    # 基本設定
    # ==========================================================
    ENV = 'production'
    DEBUG = False
    TESTING = False

    # ==========================================================
    # セキュリティ設定
    # ==========================================================

    # 秘密鍵（必須: 環境変数から取得）
    SECRET_KEY = os.environ.get('MKS_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("MKS_SECRET_KEY environment variable is required in production")

    # JWT設定
    JWT_SECRET_KEY = os.environ.get('MKS_JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("MKS_JWT_SECRET_KEY environment variable is required in production")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get('MKS_JWT_ACCESS_TOKEN_HOURS', '1'))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get('MKS_JWT_REFRESH_TOKEN_DAYS', '7'))
    )
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SECURE = True  # HTTPS必須

    # CSRF保護
    WTF_CSRF_ENABLED = True

    # ==========================================================
    # HTTPS / SSL設定
    # ==========================================================

    # HTTPS強制（リバースプロキシ経由の場合はFalse）
    FORCE_HTTPS = os.environ.get('MKS_FORCE_HTTPS', 'true').lower() in ('true', '1', 'yes')

    # プロキシヘッダー信頼設定（Nginx経由の場合はTrue）
    TRUST_PROXY_HEADERS = os.environ.get('MKS_TRUST_PROXY_HEADERS', 'true').lower() in ('true', '1', 'yes')

    # SSL証明書パス（Gunicornで直接SSL使用時）
    SSL_CERT_PATH = os.environ.get('MKS_SSL_CERT_PATH', 'ssl/server.crt')
    SSL_KEY_PATH = os.environ.get('MKS_SSL_KEY_PATH', 'ssl/server.key')

    # ==========================================================
    # セキュリティヘッダー設定
    # ==========================================================

    # HSTS（HTTP Strict Transport Security）
    HSTS_ENABLED = os.environ.get('MKS_HSTS_ENABLED', 'true').lower() in ('true', '1', 'yes')
    HSTS_MAX_AGE = int(os.environ.get('MKS_HSTS_MAX_AGE', '31536000'))  # 1年
    HSTS_INCLUDE_SUBDOMAINS = os.environ.get('MKS_HSTS_INCLUDE_SUBDOMAINS', 'true').lower() in ('true', '1', 'yes')
    HSTS_PRELOAD = os.environ.get('MKS_HSTS_PRELOAD', 'false').lower() in ('true', '1', 'yes')

    # Content Security Policy（本番用強化版）
    CSP_POLICY = {
        'default-src': "'self'",
        'script-src': "'self'",  # unsafe-inline を削除
        'style-src': "'self'",   # unsafe-inline を削除
        'img-src': "'self' data: https:",
        'font-src': "'self' data:",
        'connect-src': "'self'",
        'frame-ancestors': "'none'",
        'base-uri': "'self'",
        'form-action': "'self'",
        'upgrade-insecure-requests': ''  # HTTPリクエストを自動的にHTTPSに変換
    }

    # その他のセキュリティヘッダー
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=()',
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
        'Pragma': 'no-cache'
    }

    # ==========================================================
    # CORS設定
    # ==========================================================

    # 許可オリジン（環境変数から取得）
    CORS_ORIGINS = os.environ.get('MKS_CORS_ORIGINS', '').split(',')
    if not CORS_ORIGINS or CORS_ORIGINS == ['']:
        raise ValueError("MKS_CORS_ORIGINS environment variable is required in production")

    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_MAX_AGE = 3600

    # ==========================================================
    # レート制限設定（本番用強化版）
    # ==========================================================

    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = os.environ.get('MKS_REDIS_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window-elastic-expiry'

    # エンドポイント別レート制限
    RATELIMIT_LOGIN = "5 per minute, 20 per hour"
    RATELIMIT_API = "200 per day, 50 per hour"

    # ==========================================================
    # データベース設定
    # ==========================================================

    # データディレクトリ
    DATA_DIR = os.environ.get('MKS_DATA_DIR', '/var/lib/mirai-knowledge-system/data')

    # PostgreSQL接続（オプション）
    DATABASE_URL = os.environ.get('MKS_DATABASE_URL')

    # ==========================================================
    # ログ設定
    # ==========================================================

    LOG_LEVEL = os.environ.get('MKS_LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('MKS_LOG_FILE', '/var/log/mirai-knowledge-system/app.log')

    # ==========================================================
    # Gunicorn設定（参考）
    # ==========================================================

    # これらの設定はGunicornの設定ファイルで使用
    GUNICORN_WORKERS = int(os.environ.get('MKS_GUNICORN_WORKERS', '4'))
    GUNICORN_THREADS = int(os.environ.get('MKS_GUNICORN_THREADS', '2'))
    GUNICORN_BIND = os.environ.get('MKS_GUNICORN_BIND', '127.0.0.1:8000')
    GUNICORN_TIMEOUT = int(os.environ.get('MKS_GUNICORN_TIMEOUT', '30'))

    @classmethod
    def get_csp_string(cls):
        """CSPポリシーを文字列として取得"""
        parts = []
        for directive, value in cls.CSP_POLICY.items():
            if value:
                parts.append(f"{directive} {value}")
            else:
                parts.append(directive)
        return "; ".join(parts)

    @classmethod
    def get_hsts_header(cls):
        """HSTSヘッダー値を取得"""
        if not cls.HSTS_ENABLED:
            return None

        header = f"max-age={cls.HSTS_MAX_AGE}"
        if cls.HSTS_INCLUDE_SUBDOMAINS:
            header += "; includeSubDomains"
        if cls.HSTS_PRELOAD:
            header += "; preload"
        return header


class DevelopmentConfig:
    """開発環境用設定クラス"""

    ENV = 'development'
    DEBUG = True
    TESTING = False

    SECRET_KEY = 'dev-secret-key-not-for-production'
    JWT_SECRET_KEY = 'dev-jwt-secret-key-not-for-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False

    FORCE_HTTPS = False
    TRUST_PROXY_HEADERS = False
    HSTS_ENABLED = False

    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']

    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "1000 per hour"
    RATELIMIT_STORAGE_URL = 'memory://'

    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

    LOG_LEVEL = 'DEBUG'


class TestingConfig:
    """テスト環境用設定クラス"""

    ENV = 'testing'
    DEBUG = True
    TESTING = True

    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
    JWT_COOKIE_CSRF_PROTECT = False
    WTF_CSRF_ENABLED = False

    FORCE_HTTPS = False
    HSTS_ENABLED = False

    CORS_ORIGINS = ['*']

    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URL = 'memory://'

    DATA_DIR = '/tmp/mirai-knowledge-system-test'

    LOG_LEVEL = 'WARNING'


def get_config():
    """
    環境変数に基づいて適切な設定クラスを返す

    Returns:
        設定クラス（ProductionConfig, DevelopmentConfig, TestingConfig）
    """
    env = os.environ.get('MKS_ENV', 'development').lower()

    config_map = {
        'production': ProductionConfig,
        'development': DevelopmentConfig,
        'testing': TestingConfig
    }

    return config_map.get(env, DevelopmentConfig)


# ==========================================================
# 環境変数テンプレート（本番環境用）
# ==========================================================
"""
本番環境で必要な環境変数:

# 必須
export MKS_ENV=production
export MKS_SECRET_KEY="your-very-long-random-secret-key"
export MKS_JWT_SECRET_KEY="your-very-long-random-jwt-secret-key"
export MKS_CORS_ORIGINS="https://example.com,https://app.example.com"

# オプション
export MKS_DATA_DIR="/var/lib/mirai-knowledge-system/data"
export MKS_LOG_FILE="/var/log/mirai-knowledge-system/app.log"
export MKS_LOG_LEVEL="INFO"

# HTTPS設定
export MKS_FORCE_HTTPS="true"
export MKS_TRUST_PROXY_HEADERS="true"
export MKS_SSL_CERT_PATH="/etc/letsencrypt/live/api.example.com/fullchain.pem"
export MKS_SSL_KEY_PATH="/etc/letsencrypt/live/api.example.com/privkey.pem"

# HSTS設定
export MKS_HSTS_ENABLED="true"
export MKS_HSTS_MAX_AGE="31536000"
export MKS_HSTS_INCLUDE_SUBDOMAINS="true"
export MKS_HSTS_PRELOAD="false"

# JWT設定
export MKS_JWT_ACCESS_TOKEN_HOURS="1"
export MKS_JWT_REFRESH_TOKEN_DAYS="7"

# Gunicorn設定
export MKS_GUNICORN_WORKERS="4"
export MKS_GUNICORN_THREADS="2"
export MKS_GUNICORN_BIND="127.0.0.1:8000"
export MKS_GUNICORN_TIMEOUT="30"

# Redis（レート制限用、オプション）
export MKS_REDIS_URL="redis://localhost:6379/0"

# PostgreSQL（オプション）
export MKS_DATABASE_URL="postgresql://user:password@localhost:5432/mks"
"""
