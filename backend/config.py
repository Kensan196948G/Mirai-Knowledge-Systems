"""
アプリケーション設定
"""
import os
from datetime import timedelta


class Config:
    """基本設定クラス"""

    # データベース設定
    USE_POSTGRESQL = os.environ.get('MKS_USE_POSTGRESQL', 'false').lower() in ('true', '1', 'yes')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/mirai_knowledge_db')

    # SQLAlchemy設定
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('MKS_DB_POOL_SIZE', '10'))
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('MKS_DB_MAX_OVERFLOW', '20'))
    SQLALCHEMY_POOL_TIMEOUT = int(os.environ.get('MKS_DB_POOL_TIMEOUT', '30'))
    SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('MKS_DB_POOL_RECYCLE', '3600'))
    SQLALCHEMY_POOL_PRE_PING = True  # 接続の健全性チェック
    SQLALCHEMY_ECHO = os.environ.get('MKS_DB_ECHO', 'false').lower() in ('true', '1', 'yes')

    # JSONバックエンド設定（フォールバック）
    DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    DATA_DIR = os.environ.get('MKS_DATA_DIR', DEFAULT_DATA_DIR)

    # JWT設定
    JWT_SECRET_KEY = os.environ.get('MKS_JWT_SECRET_KEY', 'mirai-knowledge-system-jwt-secret-key-2025')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '1')))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '30')))
    JWT_COOKIE_CSRF_PROTECT = False

    # セキュリティ設定
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-flask-secret-key-change-this-too')
    WTF_CSRF_ENABLED = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_SECURE = os.environ.get('MKS_FORCE_HTTPS', 'false').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # CORS設定
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5100').split(',')

    # 環境設定
    ENV = os.environ.get('MKS_ENV', 'development')
    IS_PRODUCTION = ENV.lower() == 'production'
    DEBUG = os.environ.get('MKS_DEBUG', 'false').lower() in ('true', '1', 'yes')

    # レート制限設定
    RATELIMIT_ENABLED = IS_PRODUCTION
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

    # HTTPS設定
    FORCE_HTTPS = os.environ.get('MKS_FORCE_HTTPS', 'false').lower() in ('true', '1', 'yes')
    HSTS_ENABLED = os.environ.get('MKS_HSTS_ENABLED', 'false').lower() in ('true', '1', 'yes')
    HSTS_MAX_AGE = int(os.environ.get('MKS_HSTS_MAX_AGE', '31536000'))
    HSTS_INCLUDE_SUBDOMAINS = os.environ.get('MKS_HSTS_INCLUDE_SUBDOMAINS', 'true').lower() in ('true', '1', 'yes')

    # ファイルアップロード設定
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  # 16MB

    # ログ設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')

    # 通知設定
    TEAMS_WEBHOOK_URL = os.environ.get('MKS_TEAMS_WEBHOOK_URL', '')
    SMTP_HOST = os.environ.get('MKS_SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('MKS_SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('MKS_SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('MKS_SMTP_PASSWORD', '')
    SMTP_FROM = os.environ.get('MKS_SMTP_FROM', '')
    SMTP_USE_TLS = os.environ.get('MKS_SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
    SMTP_USE_SSL = os.environ.get('MKS_SMTP_USE_SSL', 'false').lower() in ('true', '1', 'yes')
    NOTIFICATION_RETRY_COUNT = int(os.environ.get('MKS_NOTIFICATION_RETRY_COUNT', '5'))
    DISABLE_EXTERNAL_NOTIFICATIONS = os.environ.get('MKS_DISABLE_EXTERNAL_NOTIFICATIONS', 'false').lower() in ('true', '1', 'yes')
    EXTERNAL_NOTIFICATION_TYPES = os.environ.get('MKS_EXTERNAL_NOTIFICATION_TYPES', '').split(',') if os.environ.get('MKS_EXTERNAL_NOTIFICATION_TYPES') else []

    @staticmethod
    def init_app(app):
        """アプリケーション初期化時の設定"""
        # データディレクトリの作成
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        # ログディレクトリの作成
        log_dir = os.path.dirname(Config.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)


class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    FORCE_HTTPS = True
    HSTS_ENABLED = True


class TestingConfig(Config):
    """テスト環境設定"""
    TESTING = True
    USE_POSTGRESQL = False  # テストではJSONを使用
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DISABLE_EXTERNAL_NOTIFICATIONS = True


# 設定マッピング
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """環境に応じた設定を取得"""
    if env is None:
        env = os.environ.get('MKS_ENV', 'development')
    return config.get(env, config['default'])
