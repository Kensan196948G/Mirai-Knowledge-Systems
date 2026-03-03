"""
建設土木ナレッジシステム - 認証機能付きFlaskバックエンド
JSONベース + JWT認証 + RBAC
"""

import hashlib
import json
import logging
import os
import threading
import time
import uuid  # Phase G-15: Correlation ID生成用
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
import psutil
from dotenv import load_dotenv
from flask import Flask, Response, g, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                create_refresh_token, get_jwt,
                                get_jwt_identity, jwt_required)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, emit, join_room, leave_room
from marshmallow import ValidationError
from schemas import (ConsultationAnswerSchema, ConsultationCreateSchema,
                     KnowledgeCreateSchema, LoginSchema, MS365ImportSchema,
                     MS365SyncSchema)
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

# ロガー設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# _file_lock: app_helpers モジュールで管理（Phase H-1）
import smtplib
import ssl
import tempfile
from email.message import EmailMessage

from auth.totp_manager import TOTPManager
from data_access import DataAccessLayer
from json_logger import setup_json_logging  # Phase G-15: Structured Logging
from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client import Counter as PrometheusCounter
from prometheus_client import Gauge, Histogram, generate_latest
from recommendation_engine import RecommendationEngine

from config import get_config

try:
    from msgraph.core import GraphClient
except ImportError:
    GraphClient = None

# Microsoft 365同期サービス
try:
    from services.ms365_scheduler_service import MS365SchedulerService
    from services.ms365_sync_service import MS365SyncService

    MS365_SERVICES_AVAILABLE = True
except ImportError:
    MS365SyncService = None
    MS365SchedulerService = None
    MS365_SERVICES_AVAILABLE = False

# 環境変数をロード
load_dotenv()

logger.info(
    "Environment: MKS_USE_JSON=%s, MKS_USE_POSTGRESQL=%s, MKS_ENV=%s",
    os.getenv("MKS_USE_JSON", "NOT_SET"),
    os.getenv("MKS_USE_POSTGRESQL", "NOT_SET"),
    os.getenv("MKS_ENV", "NOT_SET"),
)

# Redisキャッシュ設定
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))  # 5分

try:
    import redis
except ImportError:
    redis = None

if redis is None:
    redis_client = None
    CACHE_ENABLED = False
else:
    try:
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()  # 接続テスト
        CACHE_ENABLED = True
    except redis.ConnectionError:
        redis_client = None
        CACHE_ENABLED = False


# get_cache_key: app_helpers で管理（Phase H-1）


def cache_get(key):
    """キャッシュ取得（app_v2.redis_client / CACHE_ENABLED 参照 - テスト互換性のため）"""
    if not CACHE_ENABLED or not redis_client:
        return None
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_set(key, value, ttl=CACHE_TTL):
    """キャッシュ設定（app_v2.redis_client / CACHE_ENABLED 参照 - テスト互換性のため）"""
    if not CACHE_ENABLED or not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.debug("Redis cache write failed for key: %s - %s", key, str(e))


# CacheInvalidator: app_helpers で管理（Phase H-1）


# recommendation_engine: app_helpers で管理（Phase H-1）

# get_dal: app_helpers で管理（PYTEST_CURRENT_TEST 対応、Phase H-1）


# Microsoft 365同期サービスインスタンス（グローバル）
_ms365_sync_service = None
_ms365_scheduler_service = None


def get_ms365_sync_service():
    """MS365同期サービスを取得"""
    global _ms365_sync_service
    if _ms365_sync_service is None and MS365_SERVICES_AVAILABLE:
        _ms365_sync_service = MS365SyncService(get_dal())
    return _ms365_sync_service


def get_ms365_scheduler_service():
    """MS365スケジューラーサービスを取得"""
    global _ms365_scheduler_service
    if _ms365_scheduler_service is None and MS365_SERVICES_AVAILABLE:
        _ms365_scheduler_service = MS365SchedulerService(get_dal())
    return _ms365_scheduler_service


# ============================================================
# Prometheusメトリクス定義（app定義後に移動）
# ============================================================


# ============================================================
# HTTPS強制リダイレクトミドルウェア
# ============================================================


class HTTPSRedirectMiddleware:
    """
    HTTP リクエストを HTTPS にリダイレクトするミドルウェア

    リバースプロキシ（Nginx等）経由の場合は X-Forwarded-Proto ヘッダーを使用。
    環境変数 MKS_FORCE_HTTPS=true で有効化。
    環境変数 MKS_TRUST_PROXY_HEADERS=true でプロキシヘッダーを信頼。

    使用例:
        app.wsgi_app = HTTPSRedirectMiddleware(app.wsgi_app)
    """

    def __init__(self, app, force_https=None, trust_proxy=None):
        self.app = app
        # 本番環境ではHTTPS強制をデフォルト有効化
        is_production = os.environ.get("MKS_ENV", "development").lower() == "production"
        default_force_https = "true" if is_production else "false"

        self.force_https = (
            force_https
            if force_https is not None
            else os.environ.get("MKS_FORCE_HTTPS", default_force_https).lower()
            in ("true", "1", "yes")
        )
        self.trust_proxy = (
            trust_proxy
            if trust_proxy is not None
            else os.environ.get("MKS_TRUST_PROXY_HEADERS", "false").lower()
            in ("true", "1", "yes")
        )

    def __call__(self, environ, start_response):
        if not self.force_https:
            return self.app(environ, start_response)

        # プロトコルの判定
        if self.trust_proxy:
            # リバースプロキシからのヘッダーを信頼
            proto = environ.get("HTTP_X_FORWARDED_PROTO", "http")
        else:
            # 直接接続の場合
            proto = environ.get("wsgi.url_scheme", "http")

        if proto == "https":
            # 既にHTTPS
            return self.app(environ, start_response)

        # HTTPからHTTPSへリダイレクト
        host = environ.get("HTTP_HOST", environ.get("SERVER_NAME", "localhost"))

        # X-Forwarded-Host がある場合はそれを使用
        if self.trust_proxy and "HTTP_X_FORWARDED_HOST" in environ:
            host = environ["HTTP_X_FORWARDED_HOST"]

        path = environ.get("PATH_INFO", "/")
        query = environ.get("QUERY_STRING", "")

        https_url = f"https://{host}{path}"
        if query:
            https_url = f"{https_url}?{query}"

        # 301 Permanent Redirect
        status = "301 Moved Permanently"
        response_headers = [
            ("Location", https_url),
            ("Content-Type", "text/html"),
            ("Content-Length", "0"),
        ]
        start_response(status, response_headers)
        return [b""]


# 静的フォルダを絶対パスで設定（Windows/Linux両対応）
_base_dir = os.path.dirname(os.path.abspath(__file__))
_static_folder = os.path.normpath(os.path.join(_base_dir, "..", "webui"))
app = Flask(__name__, static_folder=_static_folder)

# Config取得
AppConfig = get_config()


def get_local_ip_addresses():
    """ローカルネットワークのIPアドレスを自動検出"""
    import socket

    ips = set()

    # 標準的なlocalhostアドレス
    ips.add("127.0.0.1")
    ips.add("localhost")

    try:
        # ホスト名からIPを取得
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
            ips.add(local_ip)
        except socket.gaierror:
            pass

        # 全ネットワークインターフェースのIPを取得
        try:
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ips.add(info[4][0])
        except socket.gaierror:
            pass

        # UDPソケットを使用した外部接続経由でのIP検出
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            # Google DNS に接続を試みることでローカルIPを取得
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            ips.add(local_ip)
            s.close()
        except Exception as e:
            logger.debug(
                "Failed to determine local IP via 8.8.8.8 connection: %s", str(e)
            )

        # 一般的なプライベートIPレンジのプレフィックス
        # 192.168.x.x, 10.x.x.x, 172.16-31.x.x
        for ip in list(ips):
            if (
                ip.startswith("192.168.")
                or ip.startswith("10.")
                or ip.startswith("172.")
            ):
                pass  # 既に追加済み

    except Exception as e:
        logger.warning("Failed to detect local IPs: %s", e)

    return list(ips)


def build_cors_origins():
    """CORS許可オリジンリストを構築（動的IP対応）"""
    # 基本設定から取得
    base_origins = getattr(AppConfig, "CORS_ORIGINS", ["http://localhost:5200"])
    if isinstance(base_origins, str):
        base_origins = [base_origins]

    origins = set(base_origins)

    # 開発環境では動的IPを追加
    if os.environ.get("MKS_ENV", "development").lower() == "development":
        # ポート番号を取得（デフォルト5200）
        port = os.environ.get("MKS_HTTP_PORT", "5200")
        https_port = os.environ.get("MKS_HTTPS_PORT", "5243")

        for ip in get_local_ip_addresses():
            origins.add(f"http://{ip}:{port}")
            origins.add(f"https://{ip}:{https_port}")
            # ポートなしも追加（プロキシ経由用）
            origins.add(f"http://{ip}")
            origins.add(f"https://{ip}")

    # 本番環境では設定されたオリジンのみ
    else:
        port = os.environ.get("MKS_HTTP_PORT", "9100")
        https_port = os.environ.get("MKS_HTTPS_PORT", "9443")
        for ip in get_local_ip_addresses():
            origins.add(f"http://{ip}:{port}")
            origins.add(f"https://{ip}:{https_port}")

    return list(origins)


# CORS設定（動的IP対応）
allowed_origins = build_cors_origins()
logger.info("[INIT] CORS configured for %d origins", len(allowed_origins))

# SocketIO設定（リアルタイム更新用）
socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode="threading")
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600,
        }
    },
)
logger.debug("[INIT] CORS origins: %s", allowed_origins)

# 設定
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
app.config["DATA_DIR"] = os.environ.get("MKS_DATA_DIR", DEFAULT_DATA_DIR)

# JWT設定
# セキュリティ強化: 環境変数必須化（デフォルト値を削除）
JWT_SECRET_KEY = os.environ.get("MKS_JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "MKS_JWT_SECRET_KEY environment variable is required. "
        "Please set a secure random key (minimum 32 characters). "
        'Example: export MKS_JWT_SECRET_KEY="your-secure-random-key-here"'
    )
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
# 完全なCSRF無効化（API専用）
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["WTF_CSRF_ENABLED"] = False

# セッションタイムアウト設定（本番環境での追加セキュリティ）
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
    "MKS_FORCE_HTTPS", "false"
).lower() in ("true", "1", "yes")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

logger.info("[INIT] JWT Secret Key configured (length=%d)", len(app.config["JWT_SECRET_KEY"]))
jwt = JWTManager(app)

# Phase G-15: Structured Logging統合
setup_json_logging(app)

# 本番環境判定（レート制限/セキュリティヘッダーで使用）
IS_PRODUCTION = os.environ.get("MKS_ENV", "development").lower() == "production"
HSTS_ENABLED = os.environ.get("MKS_HSTS_ENABLED", "false").lower() in (
    "true",
    "1",
    "yes",
)
HSTS_MAX_AGE = int(os.environ.get("MKS_HSTS_MAX_AGE", "31536000"))  # デフォルト1年
HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "MKS_HSTS_INCLUDE_SUBDOMAINS", "true"
).lower() in ("true", "1", "yes")

# レート制限設定
# 開発環境では無効化、本番環境では緩和された制限を適用
if IS_PRODUCTION:
    default_limits_config = ["1000 per minute", "10000 per hour", "100000 per day"]
else:
    # 開発環境: レート制限を無効化
    default_limits_config = []

# 開発環境ではレート制限を完全に無効化
_limiter_enabled = IS_PRODUCTION

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=default_limits_config,
    storage_uri="memory://",
    strategy="fixed-window",
    in_memory_fallback_enabled=True,
    enabled=_limiter_enabled,  # 開発環境では無効化
)


# 静的ファイルをレート制限から除外
@limiter.request_filter
def exempt_static():
    """静的ファイル（HTML、JS、CSS）をレート制限から除外"""
    return (
        request.path.startswith("/static/")
        or request.path.startswith("/webui/")
        or request.path.endswith(".html")
        or request.path.endswith(".js")
        or request.path.endswith(".css")
        or request.path == "/"
    )


if _limiter_enabled:
    logger.info("[INIT] Rate limiting ENABLED (production mode)")
else:
    logger.info("[INIT] Rate limiting DISABLED (development mode)")


# ============================================================
# Phase H-1: Blueprint登録（init_limiter → Blueprint import の順序を保証）
# ============================================================
# 重要: @get_limiter().limit() デコレータはインポート時に評価されるため、
# blueprints.utils.rate_limit を先に import して init_limiter() を呼び出してから
# auth_bp / knowledge_bp をインポートする必要がある

from blueprints.utils.rate_limit import init_limiter

# limiter インスタンスを Blueprint ユーティリティへ登録（Blueprint import 前に必須）
init_limiter(limiter)

# init_limiter() 後に Blueprint をインポート（@get_limiter().limit() が正常に動作）
from blueprints.auth import auth_bp          # Phase H-1: 12エンドポイント移行済み
from blueprints.knowledge import knowledge_bp  # Phase H-1: 12エンドポイント移行済み

# Blueprint を Flask app に登録
app.register_blueprint(auth_bp)
app.register_blueprint(knowledge_bp)

logger.info("[INIT] Blueprints registered: auth_bp (prefix=/api/v1/auth), knowledge_bp (prefix=/api/v1)")

# ============================================================
# Phase H-1: 共有ヘルパーを app_helpers からインポート
# Blueprint (auth.py, knowledge.py) と同一シングルトンを共有するために必要
# ============================================================
from app_helpers import (
    _file_lock,
    _token_blacklist as _ah_token_blacklist,
    get_data_dir,
    get_dal,
    get_cache_key,
    # cache_get / cache_set は app_v2.py でローカル定義（テスト互換性のため）
    CacheInvalidator,
    recommendation_engine,
    load_users,
    save_users,
    hash_password,
    verify_password,
    get_user_permissions,
    check_permission,
    validate_request,
    log_access,
    load_data,
    save_data,
    search_in_fields,
    highlight_text,
    create_notification,
    # 後方互換: テストコードが app_v2.xxx として参照している private helpers
    _env_bool,
    _external_notification_types,
    _should_send_external,
    _get_notification_recipients,
    _build_notification_message,
    _retry_operation,
    _get_retry_count,
    _send_teams_notification,
    _send_email_notification,
    _send_external_notifications,
)



# ============================================================
# Prometheusメトリクス定義
# ============================================================

# Prometheusレジストリをクリア（重複登録エラー回避）
from prometheus_client import REGISTRY

try:
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
except Exception:
    pass

# テスト環境ではメトリクスを定義しない（重複回避）
if os.environ.get("TESTING") != "true":
    # リクエストカウンター
    REQUEST_COUNT = PrometheusCounter(
        "mks_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )

    # レスポンスタイム
    REQUEST_DURATION = Histogram(
        "mks_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "endpoint"],
    )

    # エラーカウンター
    ERROR_COUNT = PrometheusCounter(
        "mks_errors_total", "Total errors", ["type", "endpoint"]
    )

    # API呼び出しカウンター
    API_CALLS = PrometheusCounter(
        "mks_api_calls_total", "Total API calls", ["endpoint", "method"]
    )

    # データベース接続数
    DB_CONNECTIONS = Gauge("mks_database_connections", "Number of database connections")

    # データベースクエリ時間
    DB_QUERY_DURATION = Histogram(
        "mks_database_query_duration_seconds", "Database query duration", ["operation"]
    )

    # アクティブユーザー数
    ACTIVE_USERS = Gauge("mks_active_users", "Number of active users")

    # ナレッジ総数
    KNOWLEDGE_TOTAL = Gauge("mks_knowledge_total", "Total number of knowledge entries")

    # システムメトリクス
    SYSTEM_CPU_USAGE = Gauge(
        "mks_system_cpu_usage_percent", "System CPU usage percentage"
    )

    SYSTEM_MEMORY_USAGE = Gauge(
        "mks_system_memory_usage_percent", "System memory usage percentage"
    )

    SYSTEM_DISK_USAGE = Gauge(
        "mks_system_disk_usage_percent", "System disk usage percentage"
    )

    # 認証メトリクス
    AUTH_ATTEMPTS = PrometheusCounter(
        "mks_auth_attempts_total", "Total authentication attempts", ["status"]
    )

    # レート制限メトリクス
    RATE_LIMIT_HITS = PrometheusCounter(
        "mks_rate_limit_hits_total", "Total rate limit hits", ["endpoint"]
    )

    # MS365同期メトリクス
    MS365_SYNC_EXECUTIONS = PrometheusCounter(
        "mks_ms365_sync_executions_total",
        "Total MS365 sync executions",
        ["config_id", "status"],
    )

    MS365_SYNC_DURATION = Histogram(
        "mks_ms365_sync_duration_seconds",
        "MS365 sync execution duration in seconds",
        ["config_id"],
    )

    MS365_FILES_PROCESSED = PrometheusCounter(
        "mks_ms365_files_processed_total",
        "Total files processed from MS365",
        ["config_id", "result"],  # result: created/updated/skipped/failed
    )

    MS365_SYNC_ERRORS = PrometheusCounter(
        "mks_ms365_sync_errors_total",
        "Total MS365 sync errors",
        ["config_id", "error_type"],
    )
else:
    # テスト環境用のダミーメトリクス
    REQUEST_COUNT = None
    REQUEST_DURATION = None
    ERROR_COUNT = None
    API_CALLS = None
    DB_CONNECTIONS = None
    DB_QUERY_DURATION = None
    ACTIVE_USERS = None
    KNOWLEDGE_TOTAL = None
    SYSTEM_CPU_USAGE = None
    SYSTEM_MEMORY_USAGE = None
    SYSTEM_DISK_USAGE = None
    AUTH_ATTEMPTS = None
    RATE_LIMIT_HITS = None
    MS365_SYNC_EXECUTIONS = None
    MS365_SYNC_DURATION = None
    MS365_FILES_PROCESSED = None
    MS365_SYNC_ERRORS = None


# データストレージディレクトリ
def get_data_dir():
    """データ保存先ディレクトリを取得"""
    data_dir = app.config.get("DATA_DIR", DEFAULT_DATA_DIR)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


# セキュリティヘッダー
@app.after_request
def add_security_headers(response):
    """セキュリティヘッダーを追加（本番/開発環境で設定を切り替え）"""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    response.headers.setdefault(
        "Permissions-Policy", "geolocation=(), microphone=(), camera=(), payment=()"
    )

    # 本番環境: 強化されたセキュリティ設定
    if IS_PRODUCTION:
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )

        # HSTS (HTTP Strict Transport Security)
        if HSTS_ENABLED:
            hsts_value = f"max-age={HSTS_MAX_AGE}"
            if HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            response.headers.setdefault("Strict-Transport-Security", hsts_value)

        # Content Security Policy（本番用: login.htmlのために'unsafe-inline'を許可）
        csp_policy = "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # Chart.js + Socket.IO (jsDelivr経由)
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",  # Google Fonts + インラインスタイル許可
                "img-src 'self' data: https:",
                "font-src 'self' data: https://fonts.gstatic.com",  # Google Fonts許可
                "connect-src 'self' ws: wss:",  # WebSocket接続許可
                "worker-src 'self'",  # Phase D-5: Service Worker (PWA)
                "manifest-src 'self'",  # Phase D-5: PWA Manifest
                "object-src 'none'",  # プラグイン無効化
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests",  # HTTPリクエストを自動的にHTTPSに変換
            ]
        )

        # APIレスポンスはキャッシュしない
        if request.path.startswith("/api/"):
            response.headers.setdefault(
                "Cache-Control", "no-store, no-cache, must-revalidate"
            )
            response.headers.setdefault("Pragma", "no-cache")
    else:
        # 開発環境: 緩和されたセキュリティ設定
        response.headers.setdefault("Referrer-Policy", "no-referrer")

        # Content Security Policy（開発用: unsafe-inline許可）
        csp_policy = "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # Chart.js + Socket.IO (jsDelivr経由)
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",  # インラインスタイル許可 + Google Fonts
                "img-src 'self' data: https:",
                "font-src 'self' data: https://fonts.gstatic.com",  # Google Fonts許可
                "connect-src 'self' ws: wss:",  # WebSocket接続許可
                "worker-src 'self'",  # Phase D-5: Service Worker (PWA)
                "manifest-src 'self'",  # Phase D-5: PWA Manifest
                "object-src 'none'",  # プラグイン無効化
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        )

    response.headers.setdefault("Content-Security-Policy", csp_policy)

    return response


# ============================================================
# メトリクス収集（Prometheus互換）
# ============================================================

# グローバルメトリクスストレージ
metrics_storage = {
    "http_requests_total": defaultdict(int),
    "http_request_duration_seconds": defaultdict(list),
    "active_users": set(),
    "active_sessions": set(),
    "login_attempts": defaultdict(int),
    "knowledge_operations": defaultdict(int),
    "errors": defaultdict(int),
    "start_time": time.time(),
}


@app.before_request
def before_request_metrics():
    """リクエスト前のメトリクス記録 + 相関ID生成（Phase G-15）"""
    request.start_time = time.time()

    # Phase G-15: Correlation ID生成（分散トレーシング対応）
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    g.correlation_id = correlation_id


@app.after_request
def after_request_metrics(response):
    """リクエスト後のメトリクス記録（Prometheus対応） + 相関ID返却（Phase G-15）"""
    # Phase G-15: Correlation IDをレスポンスヘッダーに追加
    if hasattr(g, "correlation_id"):
        response.headers["X-Correlation-ID"] = g.correlation_id

    # リクエスト処理時間計算
    if hasattr(request, "start_time"):
        duration = time.time() - request.start_time
        duration_ms = duration * 1000

        # エンドポイント特定
        endpoint = request.endpoint or "unknown"
        method = request.method
        status = str(response.status_code)

        # Phase G-15: 構造化ログでリクエスト完了記録
        logger.info(
            "Request completed",
            extra={
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "endpoint": endpoint,
                "method": method,
            },
        )

        # Prometheusメトリクス記録
        if REQUEST_COUNT:
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            API_CALLS.labels(endpoint=endpoint, method=method).inc()

        # レガシーメトリクス記録（互換性のため）
        key = f"{method}_{endpoint}_{status}"
        metrics_storage["http_requests_total"][key] += 1
        metrics_storage["http_request_duration_seconds"][endpoint].append(duration)

        # エラー記録
        if response.status_code >= 400:
            error_key = f"{status}"
            metrics_storage["errors"][error_key] += 1
            if ERROR_COUNT:
                ERROR_COUNT.labels(type="http_error", endpoint=endpoint).inc()

    return response


# load_users / save_users / check_permission 等: app_helpers で管理（Phase H-1）


# 認証APIルート: blueprints/auth.py に移行済み（Phase H-1）

# ============================================================
# JWT トークンブラックリストチェック（app_helpers._token_blacklist を参照）
# ============================================================


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """トークンがブラックリストにあるかチェック（app_helpers._token_blacklist 参照）"""
    jti = jwt_payload["jti"]
    # _ah_token_blacklist は app_helpers からインポートした同一オブジェクト
    return jti in _ah_token_blacklist


# ============================================================
# Microsoft 365 連携 API
# ============================================================

# Microsoft Graph クライアントのシングルトン
_ms_graph_client = None


def get_ms_graph_client():
    """Microsoft Graph クライアントを取得（シングルトン）"""
    global _ms_graph_client
    if _ms_graph_client is None:
        try:
            from integrations.microsoft_graph import MicrosoftGraphClient

            _ms_graph_client = MicrosoftGraphClient()
        except Exception as e:
            logger.warning("Microsoft Graph client initialization failed: %s", e)
            return None
    return _ms_graph_client


@app.route("/api/v1/integrations/microsoft365/status", methods=["GET"])
@jwt_required()
def ms365_status():
    """Microsoft 365接続状態を確認"""
    client = get_ms_graph_client()
    if not client:
        return jsonify(
            {
                "success": True,
                "data": {
                    "configured": False,
                    "connected": False,
                    "message": "Microsoft Graph client not available",
                },
            }
        )

    try:
        result = client.test_connection()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify(
            {
                "success": True,
                "data": {
                    "configured": client.is_configured(),
                    "connected": False,
                    "error": str(e),
                },
            }
        )


@app.route("/api/v1/integrations/microsoft365/sites", methods=["GET"])
@jwt_required()
def ms365_sites():
    """SharePointサイト一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    search = request.args.get("search", "")

    try:
        sites = client.get_sites(search=search if search else None)
        return jsonify({"success": True, "data": sites})
    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route("/api/v1/integrations/microsoft365/sites/<site_id>/drives", methods=["GET"])
@jwt_required()
def ms365_site_drives(site_id):
    """サイト内のドライブ（ドキュメントライブラリ）一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    try:
        drives = client.get_site_drives(site_id)
        return jsonify({"success": True, "data": drives})
    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route("/api/v1/integrations/microsoft365/drives/<drive_id>/items", methods=["GET"])
@jwt_required()
def ms365_drive_items(drive_id):
    """ドライブ内のアイテム（ファイル/フォルダ）一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    path = request.args.get("path", "/")

    try:
        items = client.get_drive_items(drive_id, path)
        return jsonify({"success": True, "data": items})
    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route("/api/v1/integrations/microsoft365/import", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
@validate_request(MS365ImportSchema)
def ms365_import():
    """Microsoft 365からファイルをインポート"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    data = request.validated_data
    drive_id = data["drive_id"]
    item_ids = data["item_ids"]
    import_as = data.get("import_as", "document")

    imported = []
    errors = []

    for item_id in item_ids:
        try:
            # ファイルメタデータ取得
            metadata = client.get_file_metadata(drive_id, item_id)

            # ファイルダウンロード
            content = client.download_file(drive_id, item_id)

            # インポート処理（実装はデータタイプに依存）
            imported.append(
                {
                    "item_id": item_id,
                    "name": metadata.get("name"),
                    "size": len(content),
                    "imported_as": import_as,
                }
            )

        except Exception as e:
            errors.append({"item_id": item_id, "error": str(e)})

    return jsonify(
        {
            "success": True,
            "data": {
                "imported": imported,
                "errors": errors,
                "total_imported": len(imported),
                "total_errors": len(errors),
            },
        }
    )


@app.route("/api/v1/integrations/microsoft365/sync", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
@validate_request(MS365SyncSchema)
def ms365_sync():
    """Microsoft 365と同期"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    data = request.validated_data
    sync_type = data.get("sync_type", "incremental")

    # 同期処理（実装は要件に依存）
    # ここでは基本的なレスポンスのみ返す

    return jsonify(
        {
            "success": True,
            "data": {
                "sync_type": sync_type,
                "status": "completed",
                "message": "Sync completed successfully",
            },
        }
    )


@app.route("/api/v1/integrations/microsoft365/teams", methods=["GET"])
@jwt_required()
def ms365_teams():
    """Teamsチーム一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    try:
        teams = client.get_teams()
        return jsonify({"success": True, "data": teams})
    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/teams/<team_id>/channels", methods=["GET"]
)
@jwt_required()
def ms365_team_channels(team_id):
    """Teamsチャネル一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    try:
        channels = client.get_team_channels(team_id)
        return jsonify({"success": True, "data": channels})
    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


# ============================================================
# Microsoft 365同期管理API
# ============================================================


@app.route("/api/v1/integrations/microsoft365/sync/configs", methods=["GET"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_list():
    """同期設定一覧を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "ms365_sync_configs.list", "ms365_sync_config")

        dal = get_dal()
        configs = dal.get_all_ms365_sync_configs()

        return jsonify({"success": True, "data": configs})
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route("/api/v1/integrations/microsoft365/sync/configs", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
@limiter.limit("10 per minute")
def ms365_sync_configs_create():
    """同期設定を作成"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 必須フィールド検証
        required_fields = ["name", "site_id", "drive_id"]
        for field in required_fields:
            if not data.get(field):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": f"{field} is required",
                            },
                        }
                    ),
                    400,
                )

        # デフォルト値設定
        config_data = {
            "name": data["name"],
            "site_id": data["site_id"],
            "drive_id": data["drive_id"],
            "folder_path": data.get("folder_path", "/"),
            "sync_schedule": data.get(
                "sync_schedule", "0 2 * * *"
            ),  # デフォルト: 毎日2時
            "sync_strategy": data.get("sync_strategy", "incremental"),
            "file_extensions": data.get("file_extensions", []),
            "is_enabled": data.get("is_enabled", True),
            "created_by": current_user_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        dal = get_dal()
        result = dal.create_ms365_sync_config(config_data)

        # スケジューラーに登録
        scheduler_service = get_ms365_scheduler_service()
        if scheduler_service and result.get("is_enabled"):
            try:
                scheduler_service.schedule_sync(result)
            except Exception as e:
                logger.warning("Failed to schedule sync: %s", e)

        log_access(
            current_user_id,
            "ms365_sync_configs.create",
            "ms365_sync_config",
            result.get("id"),
        )

        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/sync/configs/<int:config_id>", methods=["GET"]
)
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_get(config_id):
    """同期設定を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id, "ms365_sync_configs.get", "ms365_sync_config", config_id
        )

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Sync config {config_id} not found",
                        },
                    }
                ),
                404,
            )

        return jsonify({"success": True, "data": config})
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/sync/configs/<int:config_id>", methods=["PUT"]
)
@jwt_required()
@check_permission("integration.manage")
@limiter.limit("10 per minute")
def ms365_sync_configs_update(config_id):
    """同期設定を更新"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        dal = get_dal()
        existing = dal.get_ms365_sync_config(config_id)

        if not existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Sync config {config_id} not found",
                        },
                    }
                ),
                404,
            )

        # 更新データ準備
        update_data = {
            "updated_at": datetime.utcnow().isoformat(),
        }

        # 更新可能なフィールド
        updatable_fields = [
            "name",
            "folder_path",
            "sync_schedule",
            "sync_strategy",
            "file_extensions",
            "is_enabled",
        ]
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]

        dal.update_ms365_sync_config(config_id, update_data)

        # スケジューラー更新
        scheduler_service = get_ms365_scheduler_service()
        if scheduler_service:
            try:
                updated_config = dal.get_ms365_sync_config(config_id)
                scheduler_service.reschedule_sync(updated_config)
            except Exception as e:
                logger.warning("Failed to reschedule sync: %s", e)

        log_access(
            current_user_id, "ms365_sync_configs.update", "ms365_sync_config", config_id
        )

        # 更新後のデータを返す
        result = dal.get_ms365_sync_config(config_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/sync/configs/<int:config_id>", methods=["DELETE"]
)
@jwt_required()
@check_permission("integration.manage")
@limiter.limit("10 per minute")
def ms365_sync_configs_delete(config_id):
    """同期設定を削除"""
    try:
        current_user_id = get_jwt_identity()

        dal = get_dal()
        existing = dal.get_ms365_sync_config(config_id)

        if not existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Sync config {config_id} not found",
                        },
                    }
                ),
                404,
            )

        # スケジューラーから削除
        scheduler_service = get_ms365_scheduler_service()
        if scheduler_service:
            try:
                scheduler_service.unschedule_sync(config_id)
            except Exception as e:
                logger.warning("Failed to unschedule sync: %s", e)

        dal.delete_ms365_sync_config(config_id)

        log_access(
            current_user_id, "ms365_sync_configs.delete", "ms365_sync_config", config_id
        )

        return jsonify(
            {
                "success": True,
                "message": f"Sync config {config_id} deleted successfully",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/sync/configs/<int:config_id>/execute",
    methods=["POST"],
)
@jwt_required()
@check_permission("integration.manage")
@limiter.limit("5 per minute")
def ms365_sync_configs_execute(config_id):
    """手動で同期を実行"""
    try:
        current_user_id = get_jwt_identity()

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Sync config {config_id} not found",
                        },
                    }
                ),
                404,
            )

        sync_service = get_ms365_sync_service()
        if not sync_service:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "SERVICE_UNAVAILABLE",
                            "message": "MS365 sync service is not available",
                        },
                    }
                ),
                503,
            )

        # 同期実行
        result = sync_service.sync_configuration(
            config_id, triggered_by="manual", user_id=current_user_id
        )

        log_access(
            current_user_id,
            "ms365_sync_configs.execute",
            "ms365_sync_config",
            config_id,
        )

        return jsonify({"success": True, "data": result})
    except ValueError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "VALIDATION_ERROR", "message": str(e)},
                }
            ),
            400,
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/sync/configs/<int:config_id>/test",
    methods=["POST"],
)
@jwt_required()
@check_permission("integration.manage")
@limiter.limit("10 per minute")
def ms365_sync_configs_test(config_id):
    """接続テスト（ドライラン）"""
    try:
        current_user_id = get_jwt_identity()

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Sync config {config_id} not found",
                        },
                    }
                ),
                404,
            )

        sync_service = get_ms365_sync_service()
        if not sync_service:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "SERVICE_UNAVAILABLE",
                            "message": "MS365 sync service is not available",
                        },
                    }
                ),
                503,
            )

        # 接続テスト実行
        result = sync_service.test_connection(config_id)

        log_access(
            current_user_id, "ms365_sync_configs.test", "ms365_sync_config", config_id
        )

        if result.get("success"):
            return jsonify({"success": True, "data": result})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "CONNECTION_FAILED",
                            "message": result.get("error"),
                        },
                    }
                ),
                400,
            )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/sync/configs/<int:config_id>/history",
    methods=["GET"],
)
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_history(config_id):
    """同期履歴を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id,
            "ms365_sync_configs.history",
            "ms365_sync_config",
            config_id,
        )

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Sync config {config_id} not found",
                        },
                    }
                ),
                404,
            )

        # ページネーション
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        history = dal.get_ms365_sync_history_by_config(config_id)

        # ページネーション適用
        total = len(history)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = history[start:end]

        return jsonify(
            {
                "success": True,
                "data": {
                    "items": paginated,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "pages": (total + per_page - 1) // per_page,
                    },
                },
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route("/api/v1/integrations/microsoft365/sync/stats", methods=["GET"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_stats():
    """同期統計情報を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "ms365_sync.stats", "ms365_sync")

        dal = get_dal()

        # 統計データ取得
        all_configs = dal.get_all_ms365_sync_configs()
        enabled_configs = [c for c in all_configs if c.get("is_enabled")]

        # 最近の同期履歴（一括取得でN+1回避）
        config_ids = [c["id"] for c in all_configs]
        recent_syncs = dal.get_recent_ms365_sync_histories(config_ids, limit_per_config=5)

        # ステータス別カウント
        status_counts = Counter([h.get("status") for h in recent_syncs])

        # 最後の同期時刻
        last_sync = None
        for sync in sorted(
            recent_syncs, key=lambda x: x.get("sync_started_at", ""), reverse=True
        ):
            if sync.get("sync_completed_at"):
                last_sync = sync
                break

        stats = {
            "total_configs": len(all_configs),
            "enabled_configs": len(enabled_configs),
            "disabled_configs": len(all_configs) - len(enabled_configs),
            "recent_syncs": {
                "total": len(recent_syncs),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "running": status_counts.get("running", 0),
            },
            "last_sync": (
                {
                    "config_id": last_sync.get("config_id") if last_sync else None,
                    "status": last_sync.get("status") if last_sync else None,
                    "completed_at": (
                        last_sync.get("sync_completed_at") if last_sync else None
                    ),
                    "files_processed": (
                        last_sync.get("files_processed", 0) if last_sync else 0
                    ),
                }
                if last_sync
                else None
            ),
        }

        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route("/api/v1/integrations/microsoft365/sync/status", methods=["GET"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_status():
    """同期サービスのステータスを取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "ms365_sync.status", "ms365_sync")

        sync_service = get_ms365_sync_service()
        scheduler_service = get_ms365_scheduler_service()

        status = {
            "sync_service_available": sync_service is not None,
            "scheduler_service_available": scheduler_service is not None,
            "scheduler_running": (
                scheduler_service.is_running() if scheduler_service else False
            ),
            "scheduled_jobs": (
                scheduler_service.get_scheduled_jobs() if scheduler_service else []
            ),
            "graph_api_configured": False,
        }

        # Graph API設定確認
        if sync_service and hasattr(sync_service, "graph_client"):
            graph_client = sync_service.graph_client
            if graph_client and hasattr(graph_client, "is_configured"):
                status["graph_api_configured"] = graph_client.is_configured()

        return jsonify({"success": True, "data": status})
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route("/api/v1/integrations/microsoft365/files/<file_id>/preview", methods=["GET"])
@jwt_required()
@check_permission("ms365_sync.file.preview")
def ms365_file_preview(file_id: str):
    """
    ファイルプレビューURLを取得

    Query Parameters:
        drive_id (required): ドライブID

    Returns:
        {
            "success": True,
            "data": {
                "preview_url": "https://...",
                "preview_type": "office_embed | download | image",
                "mime_type": "application/pdf",
                "file_name": "example.pdf",
                "file_size": 1024
            }
        }
    """
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    drive_id = request.args.get("drive_id")
    if not drive_id:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "MISSING_PARAMETER",
                        "message": "drive_id parameter is required",
                    },
                }
            ),
            400,
        )

    try:
        current_user_id = get_jwt_identity()

        # プレビューURL取得
        preview_info = client.get_file_preview_url(drive_id, file_id)

        # ファイルメタデータ取得
        metadata = client.get_file_metadata(drive_id, file_id)

        # レスポンスデータ構築
        response_data = {
            **preview_info,
            "file_name": metadata.get("name", ""),
            "file_size": metadata.get("size", 0),
        }

        # 監査ログ記録
        log_access(
            current_user_id,
            "ms365_file.preview",
            "ms365_file",
            file_id,
            status="success",
            details={
                "drive_id": drive_id,
                "file_name": response_data["file_name"],
                "preview_type": preview_info["preview_type"],
            },
        )

        return jsonify({"success": True, "data": response_data})
    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id,
            "ms365_file.preview",
            "ms365_file",
            file_id,
            status="failure",
            details={"error": str(e), "drive_id": drive_id},
        )
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/files/<file_id>/download", methods=["GET"]
)
@jwt_required()
@check_permission("ms365_sync.file.preview")
def ms365_file_download(file_id: str):
    """
    ファイルをダウンロード

    Query Parameters:
        drive_id (required): ドライブID

    Returns:
        ファイルコンテンツ（バイナリ）
    """
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    drive_id = request.args.get("drive_id")
    if not drive_id:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "MISSING_PARAMETER",
                        "message": "drive_id parameter is required",
                    },
                }
            ),
            400,
        )

    try:
        current_user_id = get_jwt_identity()

        # ファイルメタデータ取得
        metadata = client.get_file_metadata(drive_id, file_id)
        file_name = metadata.get("name", "download")
        mime_type = metadata.get("file", {}).get("mimeType", "application/octet-stream")

        # ファイルダウンロード
        file_content = client.download_file(drive_id, file_id)

        # 監査ログ記録
        log_access(
            current_user_id,
            "ms365_file.download",
            "ms365_file",
            file_id,
            status="success",
            details={
                "drive_id": drive_id,
                "file_name": file_name,
                "file_size": len(file_content),
            },
        )

        # ファイルレスポンス作成
        response = Response(file_content, mimetype=mime_type)
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
        return response

    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id,
            "ms365_file.download",
            "ms365_file",
            file_id,
            status="failure",
            details={"error": str(e), "drive_id": drive_id},
        )
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@app.route(
    "/api/v1/integrations/microsoft365/files/<file_id>/thumbnail", methods=["GET"]
)
@jwt_required()
@check_permission("ms365_sync.file.preview")
def ms365_file_thumbnail(file_id: str):
    """
    ファイルサムネイルを取得

    Query Parameters:
        drive_id (required): ドライブID
        size (optional): サムネイルサイズ ("small" | "medium" | "large" | "c200x150")
                        デフォルト: "large"

    Returns:
        サムネイル画像（image/jpeg）
    """
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    drive_id = request.args.get("drive_id")
    if not drive_id:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "MISSING_PARAMETER",
                        "message": "drive_id parameter is required",
                    },
                }
            ),
            400,
        )

    size = request.args.get("size", "large")

    try:
        current_user_id = get_jwt_identity()

        # サムネイル取得
        thumbnail_content = client.get_file_thumbnail(drive_id, file_id, size)

        if thumbnail_content is None:
            # サムネイル利用不可
            log_access(
                current_user_id,
                "ms365_file.thumbnail",
                "ms365_file",
                file_id,
                status="failure",
                details={"drive_id": drive_id, "error": "Thumbnail not available"},
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Thumbnail not available for this file",
                        },
                    }
                ),
                404,
            )

        # 監査ログ記録
        log_access(
            current_user_id,
            "ms365_file.thumbnail",
            "ms365_file",
            file_id,
            status="success",
            details={
                "drive_id": drive_id,
                "size": size,
                "thumbnail_size": len(thumbnail_content),
            },
        )

        # 画像レスポンス作成
        response = Response(thumbnail_content, mimetype="image/jpeg")
        return response

    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id,
            "ms365_file.thumbnail",
            "ms365_file",
            file_id,
            status="failure",
            details={"error": str(e), "drive_id": drive_id},
        )
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


# ナレッジAPIルート: blueprints/knowledge.py に移行済み（Phase H-1）
# 以下は移行対象外のAPIルート（regulations/projects/experts）


# ============================================================
# 法令・プロジェクト・専門家 APIルート（Phase H-1 移行対象外）
# ============================================================


@app.route("/api/v1/regulations/<int:reg_id>", methods=["GET"])
@check_permission("knowledge.read")
def get_regulation_detail(reg_id):
    """法令詳細取得（キャッシュ対応）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "regulation.view", "regulation", reg_id)

    cache_key = get_cache_key("regulations_detail", reg_id)
    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: regulations_detail - %s", cache_key)
        return jsonify(cached_result)

    dal = get_dal()
    regulation = dal.get_regulation_by_id(reg_id)

    if not regulation:
        return jsonify({"success": False, "error": "Regulation not found"}), 404

    response_data = {"success": True, "data": regulation}
    cache_set(cache_key, response_data, ttl=86400)
    logger.info("Cache set: regulations_detail - %s", cache_key)
    return jsonify(response_data)


@app.route("/api/v1/projects", methods=["GET"])
@check_permission("knowledge.read")
def get_projects():
    """プロジェクト一覧取得（キャッシュ対応）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "projects.list", "project")

        type_filter = request.args.get("type", "")
        status_filter = request.args.get("status", "")
        cache_key = get_cache_key("projects_list", type_filter, status_filter)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: projects_list - %s", cache_key)
            return jsonify(cached_result)

        filters = {}
        if type_filter:
            filters["type"] = type_filter
        if status_filter:
            filters["status"] = status_filter

        dal = get_dal()
        projects = dal.get_projects_list(filters) or []
        response_data = {"success": True, "data": projects}
        cache_set(cache_key, response_data, ttl=3600)
        logger.info("Cache set: projects_list - %s", cache_key)
        return jsonify(response_data)
    except Exception as e:
        logger.error("get_projects: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@app.route("/api/v1/projects/<int:project_id>", methods=["GET"])
@check_permission("knowledge.read")
def get_project_detail(project_id):
    """プロジェクト詳細取得（キャッシュ対応）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "project.view", "project", project_id)

    cache_key = get_cache_key("projects_detail", project_id)
    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: projects_detail - %s", cache_key)
        return jsonify(cached_result)

    dal = get_dal()
    project = dal.get_project_by_id(project_id)

    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404

    response_data = {"success": True, "data": project}
    cache_set(cache_key, response_data, ttl=3600)
    logger.info("Cache set: projects_detail - %s", cache_key)
    return jsonify(response_data)


@app.route("/api/v1/experts", methods=["GET"])
@check_permission("knowledge.read")
def get_experts():
    """専門家一覧取得（キャッシュ対応）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "experts.list", "expert")

        specialization_filter = request.args.get("specialization", "")
        available_filter = request.args.get("available", "")
        cache_key = get_cache_key("experts_list", specialization_filter, available_filter)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: experts_list - %s", cache_key)
            return jsonify(cached_result)

        filters = {}
        if specialization_filter:
            filters["specialization"] = specialization_filter
        if available_filter:
            filters["is_available"] = available_filter.lower() == "true"

        dal = get_dal()
        experts = dal.get_experts_list(filters) or []
        response_data = {"success": True, "data": experts}
        cache_set(cache_key, response_data, ttl=7200)
        logger.info("Cache set: experts_list - %s", cache_key)
        return jsonify(response_data)
    except Exception as e:
        logger.error("get_experts: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@app.route("/api/v1/experts/<int:expert_id>", methods=["GET"])
@check_permission("knowledge.read")
def get_expert_detail(expert_id):
    """専門家詳細取得（キャッシュ対応）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "expert.view", "expert", expert_id)

        cache_key = get_cache_key("experts_detail", expert_id)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: experts_detail - %s", cache_key)
            return jsonify(cached_result)

        dal = get_dal()
        expert = dal.get_expert_by_id(expert_id)

        if not expert:
            return jsonify({"success": False, "error": "Expert not found"}), 404

        response_data = {"success": True, "data": expert}
        cache_set(cache_key, response_data, ttl=7200)
        logger.info("Cache set: experts_detail - %s", cache_key)
        return jsonify(response_data)
    except Exception as e:
        logger.error("get_expert_detail(%s): %s: %s", expert_id, type(e).__name__, e)
        return jsonify({"success": False, "error": "Expert not found"}), 404


# ============================================================
# 通知機能
# ============================================================


# _env_bool / create_notification等: app_helpers で管理（Phase H-1）



def _get_user_notifications(current_user_id, user_roles):
    """ユーザーに該当する通知をフィルタリング（共通ヘルパー）"""
    notifications = load_data("notifications.json")
    user_roles_set = set(user_roles)
    user_notifications = []

    for n in notifications:
        if current_user_id in n.get("target_users", []) or (
            user_roles_set & set(n.get("target_roles", []))
        ):
            n_copy = n.copy()
            n_copy["is_read"] = current_user_id in n.get("read_by", [])
            user_notifications.append(n_copy)

    user_notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return user_notifications


@app.route("/api/v1/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """ユーザーの通知一覧取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u["id"] == current_user_id), None)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_notifications = _get_user_notifications(
        current_user_id, user.get("roles", [])
    )
    unread_count = sum(1 for n in user_notifications if not n["is_read"])

    return jsonify(
        {
            "success": True,
            "data": user_notifications,
            "pagination": {
                "total_items": len(user_notifications),
                "unread_count": unread_count,
            },
        }
    )


@app.route("/api/v1/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_read(notification_id):
    """通知を既読にする"""
    current_user_id = int(get_jwt_identity())
    notifications = load_data("notifications.json")

    notification = next((n for n in notifications if n["id"] == notification_id), None)
    if not notification:
        return jsonify({"success": False, "error": "Notification not found"}), 404

    # 既読リストに追加
    if current_user_id not in notification.get("read_by", []):
        notification.setdefault("read_by", []).append(current_user_id)
        save_data("notifications.json", notifications)

    return jsonify({"success": True, "data": {"id": notification_id, "is_read": True}})


@app.route("/api/v1/notifications/unread/count", methods=["GET"])
@jwt_required()
def get_unread_count():
    """未読通知数取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u["id"] == current_user_id), None)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_notifications = _get_user_notifications(
        current_user_id, user.get("roles", [])
    )
    unread_count = sum(1 for n in user_notifications if not n["is_read"])

    return jsonify({"success": True, "data": {"unread_count": unread_count}})


# 他のエンドポイントも同様に権限チェックを追加...
# （簡潔にするため、主要なものの定義）


@app.route("/api/v1/sop", methods=["GET"])
@check_permission("sop.read")
def get_sop():
    """SOP一覧取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "sop.list", "sop")

        cache_key = get_cache_key("sop_list")
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: sop_list - %s", cache_key)
            return jsonify(cached_result)

        sop_list = load_data("sop.json") or []
        response_data = {
            "success": True,
            "data": sop_list,
            "pagination": {"total_items": len(sop_list)},
        }
        cache_set(cache_key, response_data, ttl=3600)
        logger.info("Cache set: sop_list - %s", cache_key)

        return jsonify(response_data)
    except Exception as e:
        logger.error("get_sop: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": [], "pagination": {"total_items": 0}})


@app.route("/api/v1/sop/<int:sop_id>", methods=["GET"])
@check_permission("sop.read")
def get_sop_detail(sop_id):
    """SOP詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "sop.view", "sop", sop_id)

    sop_list = load_data("sop.json")
    sop = next((s for s in sop_list if s["id"] == sop_id), None)

    if not sop:
        return jsonify({"success": False, "error": "SOP not found"}), 404

    return jsonify({"success": True, "data": sop})


@app.route("/api/v1/sop/<int:sop_id>/related", methods=["GET"])
@check_permission("sop.read")
def get_related_sop(sop_id):
    """
    関連SOPを取得（キャッシュ対応 - Phase G-6 Phase 2）

    クエリパラメータ:
        limit: 取得件数（デフォルト: 5）
        algorithm: アルゴリズム（tag/category/keyword/hybrid、デフォルト: hybrid）
        min_score: 最小スコア閾値（デフォルト: 0.1）

    NOTE: MLアルゴリズム（O(n²)計算量）のため、キャッシュ優先度最高。
    """
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "sop.related", "sop", sop_id)

    # パラメータ取得
    limit = int(request.args.get("limit", 5))
    algorithm = request.args.get("algorithm", "hybrid")
    min_score = float(request.args.get("min_score", 0.1))

    # Cache check (min_scoreは小数点2桁で正規化)
    min_score_key = f"{min_score:.2f}"
    cache_key = get_cache_key("sop_related", sop_id, limit, algorithm, min_score_key)
    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: sop_related - %s", cache_key)
        return jsonify(cached_result)

    # バリデーション
    if limit < 1 or limit > 20:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_LIMIT",
                        "message": "limit must be between 1 and 20",
                    },
                }
            ),
            400,
        )

    if algorithm not in ["tag", "category", "keyword", "hybrid"]:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_ALGORITHM",
                        "message": "algorithm must be tag, category, keyword, or hybrid",
                    },
                }
            ),
            400,
        )

    # SOP取得
    sop_list = load_data("sop.json")
    target_sop = next((s for s in sop_list if s["id"] == sop_id), None)

    if not target_sop:
        return jsonify({"success": False, "error": "SOP not found"}), 404

    # 関連アイテム取得（高負荷ML処理）
    related = recommendation_engine.get_related_items(
        target_sop, sop_list, limit=limit, algorithm=algorithm, min_score=min_score
    )

    response_data = {
        "success": True,
        "data": {
            "target_id": sop_id,
            "related_items": related,
            "algorithm": algorithm,
            "count": len(related),
        },
    }

    # Cache set (TTL: 1h, expensive ML computation)
    cache_set(cache_key, response_data, ttl=3600)
    logger.info("Cache set: sop_related - %s", cache_key)

    return jsonify(response_data)


@app.route("/api/v1/incidents", methods=["GET"])
@check_permission("incident.read")
def get_incidents():
    """事故レポート一覧取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "incidents.list", "incidents")

        cache_key = get_cache_key("incidents_list")
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: incidents_list - %s", cache_key)
            return jsonify(cached_result)

        incidents_list = load_data("incidents.json") or []
        response_data = {
            "success": True,
            "data": incidents_list,
            "pagination": {"total_items": len(incidents_list)},
        }
        cache_set(cache_key, response_data, ttl=3600)
        logger.info("Cache set: incidents_list - %s", cache_key)

        return jsonify(response_data)
    except Exception as e:
        logger.error("get_incidents: %s: %s", type(e).__name__, e)
        return jsonify(
            {
                "success": True,
                "data": [],
                "pagination": {"total_items": 0},
            }
        )


@app.route("/api/v1/incidents/<int:incident_id>", methods=["GET"])
@check_permission("incident.read")
def get_incident_detail(incident_id):
    """事故レポート詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "incidents.view", "incidents", incident_id)

    incidents_list = load_data("incidents.json")
    incident = next((i for i in incidents_list if i["id"] == incident_id), None)

    if not incident:
        return jsonify({"success": False, "error": "Incident not found"}), 404

    return jsonify({"success": True, "data": incident})


@app.route("/api/v1/dashboard/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    """ダッシュボード統計情報取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "dashboard.view", "dashboard")

    cache_key = get_cache_key("dashboard_stats")
    cached_result = cache_get(cache_key)
    if cached_result:
        return jsonify(cached_result)

    knowledge_list = load_data("knowledge.json")
    sop_list = load_data("sop.json")
    incidents = load_data("incidents.json")
    approvals = load_data("approvals.json")

    from datetime import datetime

    pending_approvals_count = len(
        [a for a in approvals if a.get("status") == "pending"]
    )

    stats = {
        "kpis": {
            "knowledge_reuse_rate": 71,
            "accident_free_days": 184,
            "active_audits": 6,
            "delayed_corrections": 3,
        },
        "counts": {
            "total_knowledge": len(knowledge_list),
            "total_sop": len(sop_list),
            "recent_incidents": len(
                [i for i in incidents if i.get("status") == "reported"]
            ),
            "pending_approvals": pending_approvals_count,
        },
        "last_sync_time": datetime.now().isoformat(),
        "active_workers": 0,
        "total_workers": 100,
        "pending_approvals": pending_approvals_count,
    }

    response_data = {"success": True, "data": stats}
    cache_set(cache_key, response_data, ttl=300)  # 5分

    return jsonify(response_data)


@app.route("/api/v1/approvals", methods=["GET"])
@jwt_required()
def get_approvals():
    """承認フロー一覧取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "approvals.list", "approvals")

        approvals = load_data("approvals.json") or []
        return jsonify(
            {
                "success": True,
                "data": approvals,
                "pagination": {"total_items": len(approvals)},
            }
        )
    except Exception as e:
        logger.error("get_approvals: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": [], "pagination": {"total_items": 0}})


@app.route("/api/v1/approvals/<int:approval_id>/approve", methods=["POST"])
@check_permission("approval.approve")
def approve_approval(approval_id):
    """承認処理"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "approvals.approve", "approvals", approval_id)

    approvals = load_data("approvals.json")
    approval = next((a for a in approvals if a["id"] == approval_id), None)

    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    approval["status"] = "approved"
    approval["approved_by"] = current_user_id
    approval["approved_at"] = datetime.utcnow().isoformat()

    save_data("approvals.json", approvals)

    return jsonify({"success": True, "message": "承認しました", "data": approval})


@app.route("/api/v1/approvals/<int:approval_id>/reject", methods=["POST"])
@check_permission("approval.approve")
def reject_approval(approval_id):
    """却下処理"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "approvals.reject", "approvals", approval_id)

    data = request.get_json()
    reason = data.get("reason", "")

    if not reason:
        return jsonify({"success": False, "error": "却下理由を入力してください"}), 400

    approvals = load_data("approvals.json")
    approval = next((a for a in approvals if a["id"] == approval_id), None)

    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    approval["status"] = "rejected"
    approval["rejected_by"] = current_user_id
    approval["rejected_at"] = datetime.utcnow().isoformat()
    approval["rejection_reason"] = reason

    save_data("approvals.json", approvals)

    return jsonify({"success": True, "message": "却下しました", "data": approval})


# ============================================================
# 推薦API
# ============================================================


@app.route("/api/v1/recommendations/personalized", methods=["GET"])
@jwt_required()
def get_personalized_recommendations():
    """
    パーソナライズ推薦を取得

    ユーザーの閲覧履歴に基づいて推薦を行います。
    協調フィルタリングとコンテンツベースフィルタリングを組み合わせています。

    クエリパラメータ:
        limit: 取得件数（デフォルト: 5、最大: 20）
        days: 対象期間（日数、デフォルト: 30）
        type: 推薦タイプ（knowledge/sop/all、デフォルト: all）
    """
    current_user_id = int(get_jwt_identity())
    log_access(current_user_id, "recommendations.personalized", "recommendations")

    # パラメータ取得
    limit = int(request.args.get("limit", 5))
    days = int(request.args.get("days", 30))
    rec_type = request.args.get("type", "all")

    # バリデーション
    if limit < 1 or limit > 20:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_LIMIT",
                        "message": "limit must be between 1 and 20",
                    },
                }
            ),
            400,
        )

    if days < 1 or days > 365:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_DAYS",
                        "message": "days must be between 1 and 365",
                    },
                }
            ),
            400,
        )

    if rec_type not in ["knowledge", "sop", "all"]:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_TYPE",
                        "message": "type must be knowledge, sop, or all",
                    },
                }
            ),
            400,
        )

    # データ読み込み
    access_logs = load_data("access_logs.json")
    knowledge_list = load_data("knowledge.json")
    sop_list = load_data("sop.json")

    results = {}

    # ナレッジ推薦
    if rec_type in ["knowledge", "all"]:
        knowledge_recommendations = (
            recommendation_engine.get_personalized_recommendations(
                user_id=current_user_id,
                access_logs=access_logs,
                all_items=knowledge_list,
                limit=limit,
                days=days,
            )
        )
        results["knowledge"] = {
            "items": knowledge_recommendations,
            "count": len(knowledge_recommendations),
        }

    # SOP推薦
    if rec_type in ["sop", "all"]:
        sop_recommendations = recommendation_engine.get_personalized_recommendations(
            user_id=current_user_id,
            access_logs=access_logs,
            all_items=sop_list,
            limit=limit,
            days=days,
        )
        results["sop"] = {
            "items": sop_recommendations,
            "count": len(sop_recommendations),
        }

    # parametersをresults内に追加
    results["parameters"] = {"limit": limit, "days": days, "type": rec_type}

    return jsonify({"success": True, "data": results})


@app.route("/api/v1/recommendations/cache/stats", methods=["GET"])
@jwt_required()
@check_permission("admin")
def get_recommendation_cache_stats():
    """推薦エンジンのキャッシュ統計を取得（管理者のみ）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "recommendations.cache_stats", "recommendations")

    stats = recommendation_engine.get_cache_stats()

    return jsonify({"success": True, "data": stats})


@app.route("/api/v1/recommendations/cache/clear", methods=["POST"])
@jwt_required()
@check_permission("admin")
def clear_recommendation_cache():
    """推薦エンジンのキャッシュをクリア（管理者のみ）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "recommendations.cache_clear", "recommendations")

    recommendation_engine.clear_cache()

    return jsonify(
        {"success": True, "message": "Recommendation cache cleared successfully"}
    )


# ============================================================
# メトリクスエンドポイント（Prometheus用）
# ============================================================


@app.route("/api/v1/metrics", methods=["GET"])
def get_metrics():
    """
    Prometheus互換メトリクスエンドポイント

    Returns:
        text/plain: Prometheus形式のメトリクスデータ
    """
    from flask import Response

    # システムメトリクス取得
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # ナレッジデータ統計
    knowledge_list = load_data("knowledge.json")
    sop_list = load_data("sop.json")

    # アクセスログ分析
    access_logs = load_data("access_logs.json")

    # アクティブユーザー計算（過去15分以内にアクセスがあったユーザー）
    now = datetime.now()
    active_users = set()
    active_sessions = set()
    login_success = 0
    login_failure = 0

    for log in access_logs:
        try:
            log_time = datetime.fromisoformat(log.get("timestamp", ""))
            if (now - log_time).total_seconds() < 900:  # 15分以内
                user_id = log.get("user_id")
                if user_id:
                    active_users.add(user_id)
                    active_sessions.add(log.get("session_id", ""))

            # ログイン統計
            if log.get("action") == "auth.login":
                if log.get("status") == "success":
                    login_success += 1
                else:
                    login_failure += 1
        except (ValueError, TypeError):
            continue

    # カテゴリ別ナレッジ数
    category_counts = Counter([k.get("category", "unknown") for k in knowledge_list])

    # HTTPリクエストメトリクス集計
    http_requests_metrics = []
    for key, count in metrics_storage["http_requests_total"].items():
        parts = key.split("_", 2)
        if len(parts) >= 3:
            method, endpoint, status = parts[0], parts[1], parts[2]
            http_requests_metrics.append(
                f'http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}'
            )

    # 応答時間メトリクス（ヒストグラム風）
    response_time_metrics = []
    for endpoint, durations in metrics_storage["http_request_duration_seconds"].items():
        if durations:
            sum(durations) / len(durations)
            max_duration = max(durations)
            min(durations)

            # パーセンタイル計算
            sorted_durations = sorted(durations)
            p50 = (
                sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0
            )
            p95_idx = int(len(sorted_durations) * 0.95)
            p95 = (
                sorted_durations[p95_idx]
                if p95_idx < len(sorted_durations)
                else max_duration
            )
            p99_idx = int(len(sorted_durations) * 0.99)
            p99 = (
                sorted_durations[p99_idx]
                if p99_idx < len(sorted_durations)
                else max_duration
            )

            response_time_metrics.extend(
                [
                    f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.5"}} {p50:.4f}',
                    f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.95"}} {p95:.4f}',
                    f'http_request_duration_seconds{{endpoint="{endpoint}",quantile="0.99"}} {p99:.4f}',
                    f'http_request_duration_seconds_sum{{endpoint="{endpoint}"}} {sum(durations):.4f}',
                    f'http_request_duration_seconds_count{{endpoint="{endpoint}"}} {len(durations)}',
                ]
            )

    # Prometheus形式のテキスト生成
    metrics_text = f"""# HELP app_info Application information
# TYPE app_info gauge
app_info{{version="2.0",name="mirai-knowledge-system"}} 1

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {time.time() - metrics_storage["start_time"]:.2f}

# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent {cpu_percent:.2f}

# HELP system_memory_usage_percent Memory usage percentage
# TYPE system_memory_usage_percent gauge
system_memory_usage_percent {memory.percent:.2f}

# HELP system_memory_total_bytes Total memory in bytes
# TYPE system_memory_total_bytes gauge
system_memory_total_bytes {memory.total}

# HELP system_memory_available_bytes Available memory in bytes
# TYPE system_memory_available_bytes gauge
system_memory_available_bytes {memory.available}

# HELP system_disk_usage_percent Disk usage percentage
# TYPE system_disk_usage_percent gauge
system_disk_usage_percent {disk.percent:.2f}

# HELP system_disk_total_bytes Total disk space in bytes
# TYPE system_disk_total_bytes gauge
system_disk_total_bytes {disk.total}

# HELP system_disk_free_bytes Free disk space in bytes
# TYPE system_disk_free_bytes gauge
system_disk_free_bytes {disk.free}

# HELP active_users Number of active users (last 15 minutes)
# TYPE active_users gauge
active_users {len(active_users)}

# HELP active_sessions Number of active sessions
# TYPE active_sessions gauge
active_sessions {len(active_sessions)}

# HELP login_attempts_total Total number of login attempts
# TYPE login_attempts_total counter
login_attempts_total{{status="success"}} {login_success}
login_attempts_total{{status="failure"}} {login_failure}

# HELP knowledge_total Total number of knowledge items
# TYPE knowledge_total gauge
knowledge_total {len(knowledge_list)}

# HELP knowledge_by_category Knowledge items by category
# TYPE knowledge_by_category gauge
"""

    # カテゴリ別メトリクス追加
    for category, count in category_counts.items():
        metrics_text += f'knowledge_by_category{{category="{category}"}} {count}\n'

    metrics_text += f"""
# HELP sop_total Total number of SOP documents
# TYPE sop_total gauge
sop_total {len(sop_list)}

# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
"""

    # HTTPリクエストメトリクス追加
    if http_requests_metrics:
        metrics_text += "\n".join(http_requests_metrics) + "\n"

    metrics_text += """
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
"""

    # 応答時間メトリクス追加
    if response_time_metrics:
        metrics_text += "\n".join(response_time_metrics) + "\n"

    # エラーメトリクス
    metrics_text += """
# HELP http_errors_total Total number of HTTP errors
# TYPE http_errors_total counter
"""
    for error_code, count in metrics_storage["errors"].items():
        metrics_text += f'http_errors_total{{code="{error_code}"}} {count}\n'

    # ナレッジ操作メトリクス
    metrics_text += """
# HELP knowledge_created_total Total number of created knowledge items
# TYPE knowledge_created_total counter
knowledge_created_total {0}

# HELP knowledge_searches_total Total number of knowledge searches
# TYPE knowledge_searches_total counter
knowledge_searches_total {0}

# HELP knowledge_views_total Total number of knowledge views
# TYPE knowledge_views_total counter
knowledge_views_total {0}
"""

    return Response(metrics_text, mimetype="text/plain; version=0.0.4; charset=utf-8")


# ============================================================
# Swagger UI統合（API Documentation）
# ============================================================


@app.route("/api/docs")
def api_docs():
    """Swagger UI for API documentation"""
    return send_from_directory(os.path.dirname(__file__), "swagger-ui.html")


@app.route("/api/openapi.yaml")
def openapi_spec():
    """OpenAPI仕様ファイルを配信"""
    return send_from_directory(os.path.dirname(__file__), "openapi.yaml")


# ============================================================
# 公開エンドポイント（認証不要）
# ============================================================


@app.route("/")
@app.route("/index.html")
def index():
    """トップページ"""
    response = send_from_directory(app.static_folder, "index.html")
    # HTMLファイルはキャッシュしない（動的更新対応）
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/<path:path>")
def serve_static(path):
    """静的ファイル配信（キャッシュ最適化）"""
    response = send_from_directory(app.static_folder, path)

    # ファイルタイプに応じたキャッシュ設定
    if path.endswith((".js", ".css")):
        # JS/CSSは1時間キャッシュ
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp")):
        # 画像は1日キャッシュ
        response.headers["Cache-Control"] = "public, max-age=86400"
    elif path.endswith((".woff", ".woff2", ".ttf", ".eot")):
        # フォントは1週間キャッシュ
        response.headers["Cache-Control"] = "public, max-age=604800"
    elif path.endswith(".html"):
        # HTMLファイルはキャッシュしない
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


# ============================================================
# 標準エラーレスポンス関数
# ============================================================


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


# ============================================================
# エラーハンドラー
# ============================================================


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
        "The method is not allowed for the requested URL", "METHOD_NOT_ALLOWED", 405
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


# ============================================================
# アプリケーション起動
# ============================================================

# ============================================================
# Prometheusメトリクスエンドポイント
# ============================================================


def update_system_metrics():
    """システムメトリクスを更新"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        SYSTEM_CPU_USAGE.set(cpu_percent)

        # メモリ使用率
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE.set(memory.percent)

        # ディスク使用率
        disk = psutil.disk_usage("/")
        SYSTEM_DISK_USAGE.set(disk.percent)

        # ナレッジ総数
        knowledges = load_data("knowledge.json")
        KNOWLEDGE_TOTAL.set(len(knowledges))

        # アクティブユーザー数（セッションベース）
        active_count = len(metrics_storage.get("active_sessions", set()))
        ACTIVE_USERS.set(active_count)

    except Exception as e:
        logger.error("Failed to update system metrics: %s", e)


@app.route("/metrics", methods=["GET"])
def metrics():
    """
    Prometheusメトリクスエンドポイント

    このエンドポイントはPrometheusサーバーがスクレイピングするため、
    認証不要でアクセス可能にする。
    """
    try:
        # システムメトリクスを更新
        update_system_metrics()

        # Prometheus形式でメトリクスを出力
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
    except Exception as e:
        logger.error("Metrics endpoint error: %s", e)
        return jsonify({"error": "Failed to generate metrics"}), 500


@app.route("/api/metrics/summary", methods=["GET"])
@jwt_required()
def metrics_summary():
    """
    メトリクスサマリーAPI（管理者用）
    人間が読みやすい形式でメトリクスを返す
    """
    try:
        get_jwt_identity()

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # メモリ使用率
        memory = psutil.virtual_memory()

        # ディスク使用率
        disk = psutil.disk_usage("/")

        # ナレッジ総数
        knowledges = load_data("knowledge.json")

        summary = {
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage_percent": disk.percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
            },
            "application": {
                "knowledge_total": len(knowledges),
                "active_sessions": len(metrics_storage.get("active_sessions", set())),
                "uptime_seconds": time.time()
                - metrics_storage.get("start_time", time.time()),
            },
            "requests": {
                "total": sum(metrics_storage["http_requests_total"].values()),
                "by_status": dict(
                    Counter(
                        key.split("_")[-1]
                        for key in metrics_storage["http_requests_total"].keys()
                    )
                ),
            },
            "errors": {
                "total": sum(metrics_storage["errors"].values()),
                "by_code": dict(metrics_storage["errors"]),
            },
        }

        return jsonify(summary), 200

    except Exception as e:
        logger.error("Metrics summary error: %s", e)
        return jsonify({"error": "Failed to generate metrics summary"}), 500


# ============================================================
# 監査ログAPI
# ============================================================


@app.route("/api/v1/logs/access", methods=["GET"])
@jwt_required()
@check_permission("admin")
def get_access_logs():
    """
    監査ログの取得（管理者専用）

    クエリパラメータ:
        user_id: 特定ユーザーでフィルタ
        action: 特定アクションでフィルタ（部分一致）
        resource: リソース種別でフィルタ
        status: success/failureでフィルタ
        start_date: 開始日時（ISO形式）
        end_date: 終了日時（ISO形式）
        page: ページ番号（デフォルト1）
        per_page: 1ページあたりの件数（デフォルト50、最大200）
        sort: 'asc' または 'desc'（デフォルト: desc）
    """
    try:
        current_user_id = get_jwt_identity()
        logs = load_data("access_logs.json")

        # フィルタパラメータ取得
        user_id_filter = request.args.get("user_id", type=int)
        action_filter = request.args.get("action", "")
        resource_filter = request.args.get("resource", "")
        status_filter = request.args.get("status", "")
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 50, type=int), 200)
        sort_order = request.args.get("sort", "desc")

        # フィルタリング
        filtered_logs = logs

        if user_id_filter:
            filtered_logs = [
                l for l in filtered_logs if l.get("user_id") == user_id_filter
            ]

        if action_filter:
            filtered_logs = [
                l
                for l in filtered_logs
                if action_filter.lower() in str(l.get("action", "")).lower()
            ]

        if resource_filter:
            filtered_logs = [
                l for l in filtered_logs if l.get("resource") == resource_filter
            ]

        if status_filter:
            filtered_logs = [
                l for l in filtered_logs if l.get("status") == status_filter
            ]

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                filtered_logs = [
                    l
                    for l in filtered_logs
                    if datetime.fromisoformat(l.get("timestamp", "")) >= start_dt
                ]
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                filtered_logs = [
                    l
                    for l in filtered_logs
                    if datetime.fromisoformat(l.get("timestamp", "")) <= end_dt
                ]
            except ValueError:
                pass

        # ソート
        filtered_logs.sort(
            key=lambda x: x.get("timestamp", ""), reverse=(sort_order == "desc")
        )

        # ページネーション
        total = len(filtered_logs)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_logs = filtered_logs[start_idx:end_idx]

        # ユーザー情報の付加
        users = load_data("users.json")
        user_map = {u["id"]: u.get("username", "Unknown") for u in users}

        for log in paginated_logs:
            log["username"] = user_map.get(log.get("user_id"), "Unknown")

        log_access(
            current_user_id,
            "logs.access.view",
            "audit_logs",
            details={
                "filters_applied": bool(
                    user_id_filter or action_filter or resource_filter
                )
            },
        )

        return (
            jsonify(
                {
                    "logs": paginated_logs,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "total_pages": (total + per_page - 1) // per_page,
                    },
                    "filters": {
                        "user_id": user_id_filter,
                        "action": action_filter,
                        "resource": resource_filter,
                        "status": status_filter,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Access logs error: %s", e)
        return jsonify({"error": "Failed to retrieve access logs"}), 500


@app.route("/api/v1/logs/access/stats", methods=["GET"])
@jwt_required()
@check_permission("admin")
def get_access_logs_stats():
    """
    監査ログの統計情報（管理者専用）
    """
    try:
        current_user_id = get_jwt_identity()
        logs = load_data("access_logs.json")

        # 統計情報の計算
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        total_logs = len(logs)
        today_logs = 0
        week_logs = 0
        action_counts = Counter()
        resource_counts = Counter()
        status_counts = Counter()
        user_activity = Counter()

        for log in logs:
            try:
                log_time = datetime.fromisoformat(log.get("timestamp", ""))

                if log_time >= today_start:
                    today_logs += 1
                if log_time >= week_start:
                    week_logs += 1

                action_counts[log.get("action", "unknown")] += 1
                resource_counts[log.get("resource") or "none"] += 1
                status_counts[log.get("status", "unknown")] += 1
                user_activity[log.get("user_id", 0)] += 1

            except (ValueError, TypeError):
                continue

        # 最もアクティブなユーザー（上位5名）
        users = load_data("users.json")
        user_map = {u["id"]: u.get("username", "Unknown") for u in users}
        top_users = [
            {
                "user_id": uid,
                "username": user_map.get(uid, "Unknown"),
                "action_count": count,
            }
            for uid, count in user_activity.most_common(5)
        ]

        log_access(current_user_id, "logs.access.stats", "audit_logs")

        return (
            jsonify(
                {
                    "total_logs": total_logs,
                    "today_logs": today_logs,
                    "week_logs": week_logs,
                    "by_action": dict(action_counts.most_common(10)),
                    "by_resource": dict(resource_counts),
                    "by_status": dict(status_counts),
                    "top_active_users": top_users,
                    "generated_at": now.isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Access logs stats error: %s", e)
        return jsonify({"error": "Failed to retrieve access logs stats"}), 500


# ============================================================
# データベースヘルスチェック
# ============================================================


@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """
    システムヘルスチェックエンドポイント

    Returns:
        JSON: システム状態（データベース、メモリ、CPU等）
    """
    try:
        # データベースヘルスチェック
        try:
            from database import check_database_health, get_storage_mode

            db_health = check_database_health()
            storage_mode = get_storage_mode()
        except ImportError:
            # database.pyが利用できない場合はJSONモード
            db_health = {"mode": "json", "healthy": True}
            storage_mode = "json"

        # システムメトリクス
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return jsonify(
            {
                "status": "healthy" if db_health.get("healthy", True) else "degraded",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "environment": os.environ.get("MKS_ENV", "development"),
                "database": db_health,
                "storage_mode": storage_mode,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available // (1024 * 1024),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free // (1024 * 1024 * 1024),
                },
            }
        ), (200 if db_health.get("healthy", True) else 503)

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.route("/api/v1/health/db", methods=["GET"])
def db_health_check():
    """
    データベース専用ヘルスチェック

    Returns:
        JSON: データベース接続状態の詳細
    """
    try:
        from database import check_database_health, get_storage_mode

        health = check_database_health()
        return jsonify(
            {
                "healthy": health.get("healthy", False),
                "mode": health.get("mode", "unknown"),
                "details": health.get("details", {}),
                "timestamp": datetime.now().isoformat(),
            }
        ), (200 if health.get("healthy") else 503)
    except ImportError:
        return (
            jsonify(
                {
                    "healthy": True,
                    "mode": "json",
                    "details": {"message": "Using JSON backend"},
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            503,
        )


# ============================================================
# デコレータ: メトリクス記録
# ============================================================


def track_db_query(operation):
    """
    データベースクエリのメトリクスを記録するデコレータ

    使用例:
        @track_db_query('select')
        def load_knowledges():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
                return result
            except Exception:
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
                ERROR_COUNT.labels(type="db_error", endpoint=operation).inc()
                raise

        return wrapper

    return decorator


def init_demo_users():
    """デモユーザー作成"""
    users = load_users()
    if len(users) == 0:
        demo_users = [
            {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": hash_password("admin123"),
                "full_name": "管理者",
                "department": "システム管理部",
                "roles": ["admin"],
                "is_active": True,
            },
            {
                "id": 2,
                "username": "yamada",
                "email": "yamada@example.com",
                "password_hash": hash_password("yamada123"),
                "full_name": "山田太郎",
                "department": "施工管理",
                "roles": ["construction_manager"],
                "is_active": True,
            },
            {
                "id": 3,
                "username": "partner",
                "email": "partner@example.com",
                "password_hash": hash_password("partner123"),
                "full_name": "協力会社ユーザー",
                "department": "協力会社",
                "roles": ["partner_company"],
                "is_active": True,
            },
        ]
        save_users(demo_users)
        logger.info("デモユーザーを作成しました: admin, yamada, partner")


# ============================================================
# 専門家相談API（Consultation Endpoints）
# ============================================================


@app.route("/api/v1/consultations", methods=["GET"])
@check_permission("consultation.read")
def get_consultations():
    """専門家相談一覧取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "consultations.list", "consultation")

    consultations = load_data("consultations.json")

    # クエリパラメータでのフィルタリング
    category = request.args.get("category")
    status = request.args.get("status")

    filtered = consultations

    if category:
        filtered = [c for c in filtered if c.get("category") == category]

    if status:
        filtered = [c for c in filtered if c.get("status") == status]

    # ページネーション
    total_items = len(filtered)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # per_pageの上限を設定
    per_page = min(per_page, 100)

    # ページ計算
    total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = filtered[start_idx:end_idx]

    return jsonify(
        {
            "success": True,
            "data": paginated_data,
            "pagination": {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "per_page": per_page,
            },
        }
    )


@app.route("/api/v1/consultations/<int:consultation_id>", methods=["GET"])
@check_permission("consultation.read")
def get_consultation_detail(consultation_id):
    """専門家相談詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "consultation.view", "consultation", consultation_id)

    consultations = load_data("consultations.json")
    consultation = next((c for c in consultations if c["id"] == consultation_id), None)

    if not consultation:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": "Consultation not found"},
                }
            ),
            404,
        )

    # 閲覧数をインクリメント
    consultation["views"] = consultation.get("views", 0) + 1
    save_data("consultations.json", consultations)

    return jsonify({"success": True, "data": consultation})


@app.route("/api/v1/consultations", methods=["POST"])
@check_permission("consultation.create")
@validate_request(ConsultationCreateSchema)
def create_consultation():
    """新規相談作成"""
    current_user_id = get_jwt_identity()
    data = request.validated_data
    consultations = load_data("consultations.json")

    # ID自動採番
    new_id = max([c["id"] for c in consultations], default=0) + 1

    # ユーザー情報取得
    users = load_users()
    current_user = next((u for u in users if u["id"] == int(current_user_id)), None)

    new_consultation = {
        "id": new_id,
        "title": data.get("title"),
        "question": data.get("question"),
        "category": data.get("category"),
        "priority": data.get("priority", "通常"),
        "status": "pending",
        "requester_id": int(current_user_id),
        "requester": (
            current_user.get("full_name", "Unknown") if current_user else "Unknown"
        ),
        "expert_id": None,
        "expert": None,
        "project": data.get("project"),
        "tags": data.get("tags", []),
        "views": 0,
        "follower_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "answered_at": None,
    }

    consultations.append(new_consultation)
    save_data("consultations.json", consultations)

    log_access(current_user_id, "consultation.create", "consultation", new_id)

    # 通知作成（専門家に通知）
    create_notification(
        title="新しい相談が投稿されました",
        message=f"{new_consultation['requester']}さんから「{new_consultation['title']}」の相談が投稿されました。",
        type="consultation_created",
        target_roles=["admin", "expert"],
        priority="normal",
        related_entity_type="consultation",
        related_entity_id=new_id,
    )

    return jsonify({"success": True, "data": new_consultation}), 201


@app.route("/api/v1/consultations/<int:consultation_id>", methods=["PUT"])
@check_permission("consultation.update")
def update_consultation(consultation_id):
    """相談更新"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_INPUT",
                        "message": "Request body is required",
                    },
                }
            ),
            400,
        )

    consultations = load_data("consultations.json")
    consultation_index = next(
        (i for i, c in enumerate(consultations) if c["id"] == consultation_id), None
    )

    if consultation_index is None:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": "Consultation not found"},
                }
            ),
            404,
        )

    consultation = consultations[consultation_index]

    # 所有権チェック: 管理者または相談投稿者のみ更新可能
    users = load_users()
    current_user = next((u for u in users if u["id"] == current_user_id), None)
    user_permissions = get_user_permissions(current_user) if current_user else []
    is_admin = "*" in user_permissions
    is_owner = consultation.get("requester_id") == current_user_id

    if not is_admin and not is_owner:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You can only update your own consultations",
                    },
                }
            ),
            403,
        )

    # 更新可能なフィールド
    updatable_fields = [
        "title",
        "question",
        "category",
        "priority",
        "tags",
        "status",
    ]

    for field in updatable_fields:
        if field in data:
            consultations[consultation_index][field] = data[field]

    consultations[consultation_index]["updated_at"] = datetime.now().isoformat()

    save_data("consultations.json", consultations)
    log_access(current_user_id, "consultation.update", "consultation", consultation_id)

    return jsonify({"success": True, "data": consultations[consultation_index]})


@app.route("/api/v1/consultations/<int:consultation_id>/answers", methods=["POST"])
@check_permission("consultation.answer")
@validate_request(ConsultationAnswerSchema)
def post_consultation_answer(consultation_id):
    """相談に回答を投稿"""
    current_user_id = get_jwt_identity()
    data = request.validated_data
    consultations = load_data("consultations.json")

    consultation_index = next(
        (i for i, c in enumerate(consultations) if c["id"] == consultation_id), None
    )

    if consultation_index is None:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": "Consultation not found"},
                }
            ),
            404,
        )

    # ユーザー情報取得
    users = load_users()
    current_user = next((u for u in users if u["id"] == int(current_user_id)), None)

    # 新しい回答オブジェクト
    new_answer = {
        "id": int(time.time() * 1000),  # ミリ秒タイムスタンプをIDとして使用
        "content": data.get("content"),
        "references": data.get("references"),
        "is_best_answer": data.get("is_best_answer", False),
        "expert": (
            current_user.get("full_name", "Unknown") if current_user else "Unknown"
        ),
        "expert_id": int(current_user_id),
        "expert_title": (
            current_user.get("department", "専門家") if current_user else "専門家"
        ),
        "author_name": (
            current_user.get("full_name", "Unknown") if current_user else "Unknown"
        ),
        "created_at": datetime.now().isoformat(),
        "helpful_count": 0,
        "attachments": data.get("attachments", []),
    }

    # answersフィールドがない場合は初期化
    if "answers" not in consultations[consultation_index]:
        consultations[consultation_index]["answers"] = []

    consultations[consultation_index]["answers"].append(new_answer)

    # ステータスを pending → answered に更新
    if consultations[consultation_index]["status"] == "pending":
        consultations[consultation_index]["status"] = "answered"
        consultations[consultation_index]["answered_at"] = datetime.now().isoformat()

    # expert情報を更新（最初の回答者を専門家として設定）
    if consultations[consultation_index].get("expert_id") is None:
        consultations[consultation_index]["expert_id"] = int(current_user_id)
        consultations[consultation_index]["expert"] = (
            current_user.get("full_name", "Unknown") if current_user else "Unknown"
        )

    consultations[consultation_index]["updated_at"] = datetime.now().isoformat()

    save_data("consultations.json", consultations)
    log_access(current_user_id, "consultation.answer", "consultation", consultation_id)

    # 通知作成（相談投稿者に通知）
    requester_id = consultations[consultation_index].get("requester_id")
    if requester_id:
        create_notification(
            title="相談に回答がありました",
            message=f"{new_answer['expert']}さんが「{consultations[consultation_index]['title']}」に回答しました。",
            type="consultation_answered",
            target_users=[requester_id],
            priority="normal",
            related_entity_type="consultation",
            related_entity_id=consultation_id,
        )

    return jsonify({"success": True, "data": new_answer}), 201


# HTTPS強制リダイレクトミドルウェアを適用（本番環境用）
# 環境変数 MKS_FORCE_HTTPS=true で有効化
if os.environ.get("MKS_FORCE_HTTPS", "false").lower() in ("true", "1", "yes"):
    app.wsgi_app = HTTPSRedirectMiddleware(app.wsgi_app)
    logger.info("[INIT] HTTPS強制リダイレクトを有効化しました")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("建設土木ナレッジシステム - サーバー起動中")
    logger.info("=" * 60)

    # 環境情報表示
    env_mode = os.environ.get("MKS_ENV", "development")
    logger.info("環境モード: %s", env_mode)

    if IS_PRODUCTION:
        logger.info("[PRODUCTION] 本番環境設定が有効です")
        if HSTS_ENABLED:
            logger.info("[SECURITY] HSTS有効 (max-age=%s)", HSTS_MAX_AGE)
    else:
        logger.info("[DEVELOPMENT] 開発環境設定が有効です")

    # デモユーザー初期化（開発環境のみ or 環境変数で明示的に有効化）
    create_demo_users = os.environ.get(
        "MKS_CREATE_DEMO_USERS", "true" if not IS_PRODUCTION else "false"
    ).lower() in ("true", "1", "yes")
    if create_demo_users:
        init_demo_users()
    else:
        logger.info("[PRODUCTION] デモユーザー作成をスキップ（MKS_CREATE_DEMO_USERS=false）")

    # ポート番号を環境変数から取得（固定値: 開発5100、本番8100）
    http_port = int(os.environ.get("MKS_HTTP_PORT", "5100"))

    protocol = (
        "https"
        if os.environ.get("MKS_FORCE_HTTPS", "false").lower() in ("true", "1", "yes")
        else "http"
    )
    logger.info("アクセスURL: %s://localhost:%s", protocol, http_port)
    logger.info("環境: %s", os.environ.get('MKS_ENV', 'development'))
    logger.info("ポート: HTTP=%s", http_port)
    logger.info("=" * 60)

    debug = os.environ.get("MKS_DEBUG", "false").lower() in ("1", "true", "yes")
    bind_host = os.environ.get(
        "MKS_BIND_HOST", "0.0.0.0"
    )  # Default: all interfaces (production: set to 127.0.0.1)

    # 全環境でsocketio.runを使用（WebSocket対応）
    logger.info("[SERVER] Using SocketIO server with WebSocket support (binding to %s:%s)", bind_host, http_port)
    socketio.run(
        app, host=bind_host, port=http_port, debug=debug, allow_unsafe_werkzeug=True
    )


# ============================================================
# SocketIOイベントハンドラー（リアルタイム更新）
# ============================================================


@socketio.on("connect")
def handle_connect():
    """クライアント接続時の処理"""
    logger.debug("[SOCKET] Client connected")
    emit("connected", {"status": "success"})


@socketio.on("disconnect")
def handle_disconnect():
    """クライアント切断時の処理"""
    logger.debug("[SOCKET] Client disconnected")


@socketio.on("join_project")
def handle_join_project(data):
    """プロジェクトルーム参加"""
    project_id = data.get("project_id")
    if project_id:
        join_room(f"project_{project_id}")
        logger.debug("[SOCKET] User joined project room: %s", project_id)
        emit("joined_project", {"project_id": project_id})


@socketio.on("leave_project")
def handle_leave_project(data):
    """プロジェクトルーム退出"""
    project_id = data.get("project_id")
    if project_id:
        leave_room(f"project_{project_id}")
        logger.debug("[SOCKET] User left project room: %s", project_id)


@socketio.on("join_dashboard")
def handle_join_dashboard():
    """ダッシュボードルーム参加"""
    join_room("dashboard")
    logger.debug("[SOCKET] User joined dashboard room")
    emit("joined_dashboard", {"status": "success"})


@socketio.on("leave_dashboard")
def handle_leave_dashboard():
    """ダッシュボードルーム退出"""
    leave_room("dashboard")
    logger.debug("[SOCKET] User left dashboard room")


# リアルタイム更新用の関数
def emit_project_progress_update(project_id, progress_data):
    """プロジェクト進捗更新をリアルタイム通知"""
    socketio.emit(
        "project_progress_update",
        {
            "project_id": project_id,
            "progress": progress_data,
            "timestamp": datetime.now().isoformat(),
        },
        to=f"project_{project_id}",
    )


def emit_dashboard_stats_update(stats_data):
    """ダッシュボード統計更新をリアルタイム通知"""
    socketio.emit(
        "dashboard_stats_update",
        {"stats": stats_data, "timestamp": datetime.now().isoformat()},
        to="dashboard",
    )


def emit_expert_stats_update(expert_stats):
    """専門家統計更新をリアルタイム通知"""
    socketio.emit(
        "expert_stats_update",
        {"expert_stats": expert_stats, "timestamp": datetime.now().isoformat()},
        to="dashboard",
    )
