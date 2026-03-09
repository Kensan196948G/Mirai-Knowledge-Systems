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


# get_cache_key / cache_get / cache_set: app_helpers で管理（Phase H-2）


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
from blueprints.auth import auth_bp              # Phase H-1: 12エンドポイント移行済み
from blueprints.knowledge import knowledge_bp    # Phase H-1: 12エンドポイント移行済み
from blueprints.dashboard import dashboard_bp    # Phase H-2: SOP/Dashboard移行
from blueprints.ms365 import ms365_bp, ms365_integration_bp, get_ms_graph_client  # Phase H-3/H-4: MS365移行
from blueprints.operations import operations_bp  # Phase H-3: Incidents/Approvals移行 + Phase I-4: regulations/projects/experts/notifications
from blueprints.recommendations import recommendations_bp  # Phase H-4: 推薦API移行
from blueprints.admin import admin_bp            # Phase H-4: 監査ログ・ヘルスチェック移行
from blueprints.utils.health_bp import health_bp  # Phase I-4: metrics/docs/static移行

# Blueprint を Flask app に登録
app.register_blueprint(auth_bp)
app.register_blueprint(knowledge_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(ms365_bp)
app.register_blueprint(ms365_integration_bp)
app.register_blueprint(operations_bp)
app.register_blueprint(recommendations_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(health_bp)

logger.info("[INIT] Blueprints registered: auth_bp, knowledge_bp, dashboard_bp, ms365_bp, ms365_integration_bp, operations_bp, recommendations_bp, admin_bp, health_bp")

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
    cache_get,   # Phase H-2: app_helpers に統合
    cache_set,   # Phase H-2: app_helpers に統合
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



# Microsoft 365 連携 API: blueprints/ms365.py に移行済み（Phase H-4）

# ナレッジAPIルート: blueprints/knowledge.py に移行済み（Phase H-1）
# 法令・プロジェクト・専門家 APIルート: blueprints/operations.py に移行済み（Phase I-4）


# 通知APIルート: blueprints/operations.py に移行済み（Phase I-4）
# _env_bool / create_notification等: app_helpers で管理（Phase H-1）

# 推薦API: blueprints/recommendations.py に移行済み（Phase H-4）

# カスタムメトリクス・Swagger・静的ファイルルート: blueprints/utils/health_bp.py に移行済み（Phase I-4）


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



# 監査ログ・ヘルスチェックAPI: blueprints/admin.py に移行済み（Phase H-4）

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
