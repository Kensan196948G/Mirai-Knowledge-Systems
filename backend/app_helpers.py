"""
共有ヘルパーモジュール (Phase H-1 Blueprint移行)

app_v2.py と Blueprints の両方から利用される共通関数・状態を定義。
循環インポートを防ぐため、このモジュールは app_v2.py をインポートしない。

Python モジュールキャッシュにより、_file_lock / _token_blacklist 等の
シングルトンはプロセス内で同一インスタンスとして共有される。
"""

import hashlib
import json
import logging
import os
import re
import smtplib
import ssl
import tempfile
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from email.message import EmailMessage
from functools import wraps

import bcrypt

try:
    import requests as _requests_lib
except ImportError:
    _requests_lib = None

try:
    import redis as _redis_lib
except ImportError:
    _redis_lib = None

from flask import jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest

from data_access import DataAccessLayer
from recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

# ================================================================
# グローバル状態（Pythonモジュールキャッシュでシングルトン保証）
# ================================================================

_file_lock = threading.RLock()
_token_blacklist: set = set()
_dal = None
_access_log_queue: list = []
_access_log_queue_lock = threading.Lock()

# 環境設定
MKS_ENV = os.environ.get("MKS_ENV", "development")
IS_PRODUCTION = MKS_ENV.lower() == "production"

# データディレクトリ
_base_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(_base_dir, "data")

# ================================================================
# Redis キャッシュ設定
# ================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))

if _redis_lib is None:
    redis_client = None
    CACHE_ENABLED = False
else:
    try:
        redis_client = _redis_lib.from_url(REDIS_URL)
        redis_client.ping()
        CACHE_ENABLED = True
    except Exception:
        redis_client = None
        CACHE_ENABLED = False

# ================================================================
# 推薦エンジン（シングルトン）
# ================================================================

recommendation_engine = RecommendationEngine(cache_ttl=300)

# ================================================================
# データディレクトリ / DAL
# ================================================================


def get_data_dir() -> str:
    """データ保存先ディレクトリを取得

    優先順位:
    1. MKS_DATA_DIR 環境変数（テスト時の monkeypatch.setenv で上書き可能）
    2. Flask current_app.config["DATA_DIR"]（リクエストコンテキスト内）
    3. app_v2.app.config["DATA_DIR"]（コンテキスト外でも参照可能）
    4. DEFAULT_DATA_DIR（フォールバック）
    """
    # 1. env var（テストの monkeypatch.setenv が最優先）
    data_dir = os.environ.get("MKS_DATA_DIR")
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    # 2. Flask current_app.config（リクエストコンテキスト or app.app_context() 内）
    try:
        from flask import current_app
        cfg_dir = current_app.config.get("DATA_DIR")
        if cfg_dir:
            os.makedirs(cfg_dir, exist_ok=True)
            return cfg_dir
    except RuntimeError:
        pass  # Flask application context 外

    # 3. app_v2.app.config（コンテキスト外テスト対応: monkeypatch.setitem 使用時）
    import sys
    _app_mod = sys.modules.get("app_v2")
    if _app_mod is not None:
        _flask_app = getattr(_app_mod, "app", None)
        if _flask_app is not None:
            cfg_dir = _flask_app.config.get("DATA_DIR")
            if cfg_dir:
                os.makedirs(cfg_dir, exist_ok=True)
                return cfg_dir

    # 4. デフォルト
    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    return DEFAULT_DATA_DIR


def get_dal() -> DataAccessLayer:
    """DataAccessLayerインスタンスを取得（シングルトン）"""
    global _dal
    if _dal is None:
        use_pg = os.environ.get("MKS_USE_POSTGRESQL", "false").lower() in (
            "true", "1", "yes",
        )
        # pytest実行中はJSONモード強制（PYTEST_CURRENT_TESTはpytestが自動設定）
        if os.environ.get("PYTEST_CURRENT_TEST"):
            use_pg = False
        _dal = DataAccessLayer(use_postgresql=use_pg)
    return _dal


# ================================================================
# キャッシュヘルパー
# ================================================================


def get_cache_key(prefix, *args) -> str:
    """キャッシュキー生成"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"


def cache_get(key):
    """キャッシュ取得"""
    if not CACHE_ENABLED or not redis_client:
        return None
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_set(key, value, ttl=CACHE_TTL):
    """キャッシュ設定"""
    if not CACHE_ENABLED or not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.debug("Redis cache write failed for key: %s - %s", key, str(e))


class CacheInvalidator:
    """集中キャッシュ無効化ロジック（Phase G-6）"""

    @staticmethod
    def invalidate_knowledge(knowledge_id=None):
        """ナレッジ関連キャッシュ無効化"""
        if not redis_client:
            return
        try:
            patterns = [
                "knowledge_list:*",
                "knowledge_popular:*",
                "knowledge_tags",
                "knowledge_recent:*",
            ]
            if knowledge_id:
                patterns.append(f"knowledge_related:{knowledge_id}:*")
            for pattern in patterns:
                for key in redis_client.scan_iter(pattern):
                    redis_client.delete(key)
            logger.info("Cache invalidated: knowledge (id=%s)", knowledge_id or "all")
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)

    @staticmethod
    def invalidate_projects(project_id=None):
        if not redis_client:
            return
        try:
            patterns = ["projects_list:*"]
            if project_id:
                patterns.extend([
                    f"projects_detail:{project_id}",
                    f"projects_progress:{project_id}",
                ])
            for pattern in patterns:
                for key in redis_client.scan_iter(pattern):
                    redis_client.delete(key)
            logger.info("Cache invalidated: projects (id=%s)", project_id or "all")
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)

    @staticmethod
    def invalidate_experts(expert_id=None):
        if not redis_client:
            return
        try:
            patterns = ["experts_list:*", "experts_stats"]
            if expert_id:
                patterns.extend([f"experts_detail:{expert_id}"])
            for pattern in patterns:
                for key in redis_client.scan_iter(pattern):
                    redis_client.delete(key)
            logger.info("Cache invalidated: experts (id=%s)", expert_id or "all")
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)

    @staticmethod
    def invalidate_regulations(reg_id=None):
        if not redis_client:
            return
        try:
            patterns = []
            if reg_id:
                patterns.append(f"regulations_detail:{reg_id}")
            for pattern in patterns:
                for key in redis_client.scan_iter(pattern):
                    redis_client.delete(key)
            logger.info("Cache invalidated: regulations (id=%s)", reg_id or "all")
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)

    @staticmethod
    def invalidate_sop(sop_id=None):
        if not redis_client:
            return
        try:
            patterns = ["sop_list"]
            if sop_id:
                patterns.append(f"sop_related:{sop_id}:*")
            for pattern in patterns:
                for key in redis_client.scan_iter(pattern):
                    redis_client.delete(key)
            logger.info("Cache invalidated: sop (id=%s)", sop_id or "all")
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)


# ================================================================
# ユーザー管理
# ================================================================


def load_users() -> list:
    """ユーザーデータ読み込み（スレッドセーフ）"""
    with _file_lock:
        filepath = os.path.join(get_data_dir(), "users.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return []


def save_users(users: list):
    """ユーザーデータ保存"""
    filepath = os.path.join(get_data_dir(), "users.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# ================================================================
# パスワード管理
# ================================================================


def hash_password(password: str) -> str:
    """パスワードをbcryptでハッシュ化"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """パスワードを検証（bcryptとレガシーSHA256の両方をサポート）"""
    if password_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception as e:
            logger.error("bcrypt verification failed: %s", e)
            return False
    else:
        logger.warning("Using legacy SHA256 verification for password.")
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        return legacy_hash == password_hash


# ================================================================
# 権限管理
# ================================================================


def get_user_permissions(user: dict) -> list:
    """ユーザーの権限を取得"""
    role_permissions = {
        "admin": ["*"],
        "construction_manager": [
            "knowledge.create", "knowledge.read", "knowledge.update", "knowledge.delete",
            "sop.read", "incident.create", "incident.read", "consultation.create",
            "approval.read", "notification.read",
        ],
        "quality_assurance": [
            "knowledge.read", "knowledge.create", "knowledge.approve",
            "sop.read", "sop.update", "incident.read",
            "approval.execute", "notification.read",
        ],
        "safety_officer": [
            "knowledge.read", "knowledge.create", "sop.read",
            "incident.create", "incident.read", "incident.update",
            "approval.read", "notification.read",
        ],
        "partner_company": [
            "knowledge.read", "sop.read", "incident.read", "notification.read",
        ],
        "manager": [
            "knowledge.read", "knowledge.create", "knowledge.update",
            "sop.read", "incident.read", "incident.create",
            "approval.read", "approval.execute", "notification.read",
        ],
        "engineer": [
            "knowledge.read", "knowledge.create", "sop.read",
            "incident.read", "notification.read",
        ],
    }

    roles = user.get("roles", [])
    permissions: set = set()

    for role in roles:
        role_perms = role_permissions.get(role, [])
        if "*" in role_perms:
            return ["*"]
        permissions.update(role_perms)

    return list(permissions)


def check_permission(required_permission: str):
    """権限チェックデコレータ（JWT claims最適化版 v1.4.1）

    JWTトークンのclaimsから直接rolesを取得することで、
    毎リクエストのload_users()呼び出し（N+1問題）を解消する。
    claimsにrolesが存在しない場合はDBフォールバックで後方互換性を維持。
    """

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            try:
                current_user_id = get_jwt_identity()
                user_id_int = (
                    int(current_user_id)
                    if isinstance(current_user_id, str)
                    else current_user_id
                )
                logger.debug(
                    "check_permission: user_id=%s, required=%s",
                    user_id_int,
                    required_permission,
                )

                claims = get_jwt()
                roles = claims.get("roles", None)

                if roles is None:
                    logger.debug(
                        "JWT claims に roles が存在しないためDBフォールバック: user_id=%s",
                        current_user_id,
                    )
                    users = load_users()
                    user = next((u for u in users if u["id"] == user_id_int), None)
                    if not user:
                        logger.debug("User not found: %s", current_user_id)
                        return jsonify({"success": False, "error": "User not found"}), 404
                    roles = user.get("roles", [])

                permissions = get_user_permissions({"roles": roles})
                logger.debug("User permissions (from JWT claims): %s", permissions)

                if "*" in permissions or required_permission in permissions:
                    logger.debug("Permission granted")
                    return fn(*args, **kwargs)

                logger.debug("Permission denied")
                return (
                    jsonify({
                        "success": False,
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "Insufficient permissions",
                        },
                    }),
                    403,
                )
            except Exception as e:
                import traceback
                logger.debug("Exception in check_permission: %s", e)
                logger.error("Unexpected error traceback:\n%s", traceback.format_exc())
                return (
                    jsonify({
                        "success": False,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "Internal server error",
                        },
                    }),
                    500,
                )

        return wrapper

    return decorator


def validate_request(schema_class):
    """リクエストデータを検証するデコレータ"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                schema = schema_class()
                validated_data = schema.load(request.json or {})
                request.validated_data = validated_data
                return fn(*args, **kwargs)
            except BadRequest:
                return (
                    jsonify({
                        "success": False,
                        "error": {
                            "code": "INVALID_JSON",
                            "message": "Invalid JSON payload",
                        },
                    }),
                    400,
                )
            except ValidationError as err:
                return (
                    jsonify({
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "入力データが不正です",
                            "details": err.messages,
                        },
                    }),
                    400,
                )

        return wrapper

    return decorator


# ================================================================
# 監査ログ
# ================================================================


def _flush_access_logs():
    """アクセスログをファイルに一括書き込み"""
    global _access_log_queue
    with _access_log_queue_lock:
        if not _access_log_queue:
            return
        entries_to_write = _access_log_queue[:]
        _access_log_queue = []

    try:
        with _file_lock:
            logs = load_data("access_logs.json")
            for entry in entries_to_write:
                entry["id"] = len(logs) + 1
                logs.append(entry)
            save_data("access_logs.json", logs)
    except Exception as e:
        logger.warning("_flush_access_logs failed: %s: %s", type(e).__name__, e)


def log_access(
    user_id,
    action,
    resource=None,
    resource_id=None,
    status="success",
    details=None,
    old_value=None,
    new_value=None,
):
    """詳細な監査ログを記録（本番のみ同期書き込み）"""
    try:
        if not IS_PRODUCTION:
            return

        session_id = None
        try:
            jwt_data = get_jwt()
            session_id = jwt_data.get("jti", None)
        except Exception as e:
            logger.debug(
                "JWT not available for audit log - session_id will be None: %s", str(e)
            )

        safe_resource_id = None
        if resource_id is not None:
            if isinstance(resource_id, int):
                safe_resource_id = resource_id
            elif isinstance(resource_id, str) and resource_id.isdigit():
                safe_resource_id = int(resource_id)

        log_entry = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": safe_resource_id,
            "status": status,
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "request_method": request.method,
            "request_path": request.path,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }

        if old_value is not None or new_value is not None:
            log_entry["changes"] = {"old_value": old_value, "new_value": new_value}

        if details:
            log_entry["details"] = details

        with _file_lock:
            logs = load_data("access_logs.json")
            log_entry["id"] = len(logs) + 1
            logs.append(log_entry)
            save_data("access_logs.json", logs)
    except Exception as e:
        logger.warning("log_access failed: %s: %s", type(e).__name__, e)


# ================================================================
# データ管理関数
# ================================================================


def load_data(filename: str) -> list:
    """JSONファイルまたはPostgreSQLからデータを読み込む（透過的切り替え）"""
    dal = get_dal()

    if dal.use_postgresql:
        try:
            if filename == "knowledge.json":
                return dal.get_knowledge_list()
            elif filename == "sop.json":
                return dal.get_sop_list()
            elif filename == "incidents.json":
                return dal.get_incidents_list()
            elif filename == "approvals.json":
                return dal.get_approvals_list()
            elif filename == "notifications.json":
                return dal.get_notifications()
            elif filename == "access_logs.json":
                return dal.get_access_logs()
        except Exception as e:
            logger.error("PostgreSQL query error for %s: %s", filename, e)
            logger.info("Falling back to JSON mode for %s", filename)

    filepath = os.path.join(get_data_dir(), filename)

    try:
        with _file_lock:
            if not os.path.exists(filepath):
                logger.info("File not found: %s (returning empty list)", filename)
                return []

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning(
                    "%s: Expected list, got %s. Returning empty list.",
                    filename,
                    type(data).__name__,
                )
                return []

            valid_items = [item for item in data if isinstance(item, dict)]
            if len(valid_items) != len(data):
                logger.warning(
                    "%s: Filtered out %d non-dict items",
                    filename,
                    len(data) - len(valid_items),
                )

            return valid_items

    except json.JSONDecodeError as e:
        logger.error(
            "JSON decode error in %s: %s (line %d, col %d)", filename, e, e.lineno, e.colno
        )
        return []
    except PermissionError as e:
        logger.error("Permission denied reading %s: %s", filename, e)
        return []
    except UnicodeDecodeError as e:
        logger.error("Encoding error reading %s: %s", filename, e)
        return []
    except Exception as e:
        logger.error("Unexpected error reading %s: %s: %s", filename, type(e).__name__, e)
        return []


def save_data(filename: str, data: list):
    """JSONファイルに安全にデータを保存（アトミック書き込み + スレッドロック）"""
    with _file_lock:
        filepath = os.path.join(get_data_dir(), filename)
        dirpath = os.path.dirname(filepath)

        try:
            os.makedirs(dirpath, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create directory %s: %s", dirpath, e)
            raise

        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(
                prefix=f".{filename}.", suffix=".tmp", dir=dirpath
            )

            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            os.replace(tmp_path, filepath)
            tmp_path = None

        except PermissionError as e:
            logger.error("Permission denied writing %s: %s", filename, e)
            raise
        except OSError as e:
            logger.error("OS error writing %s: %s", filename, e)
            raise
        except Exception as e:
            logger.error("Unexpected error writing %s: %s: %s", filename, type(e).__name__, e)
            raise
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception as e:
                    logger.warning("Failed to remove temp file %s: %s", tmp_path, e)


# ================================================================
# 検索ヘルパー
# ================================================================


def search_in_fields(item: dict, query: str, fields: list) -> tuple:
    """複数フィールドから検索し、マッチ情報とスコアを返す"""
    query_lower = query.lower()
    matched_fields = []
    relevance_score = 0.0

    for field in fields:
        value = str(item.get(field, "")).lower()
        if query_lower in value:
            matched_fields.append(field)
            if field == "title":
                relevance_score += 1.0
            elif field == "summary":
                relevance_score += 0.7
            elif field == "content":
                relevance_score += 0.5

    return matched_fields, relevance_score


def highlight_text(text: str, query: str) -> str:
    """検索語をハイライトマークで囲む"""
    if not text or not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group()}</mark>", text)


# ================================================================
# 通知ヘルパー
# ================================================================


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _external_notifications_disabled() -> bool:
    """外部通知を無効化するか判定（テスト環境またはenv var設定時）"""
    if _env_bool("MKS_DISABLE_EXTERNAL_NOTIFICATIONS", False):
        return True
    # PYTEST_CURRENT_TEST はpytestが自動設定するenv var
    if os.environ.get("PYTEST_CURRENT_TEST"):
        # app.config["TESTING"] = False で明示的に有効化可能（テスト内部での検証用）
        import sys
        _app_mod = sys.modules.get("app_v2")
        if _app_mod is not None:
            _flask_app = getattr(_app_mod, "app", None)
            if _flask_app is not None and _flask_app.config.get("TESTING") is False:
                return False
        return True
    return False


def _external_notification_types():
    raw_types = os.environ.get("MKS_EXTERNAL_NOTIFICATION_TYPES", "").strip()
    if not raw_types:
        return None
    return {t.strip() for t in raw_types.split(",") if t.strip()}


def _should_send_external(notification_type: str) -> bool:
    allowed_types = _external_notification_types()
    if allowed_types is None:
        return True
    return notification_type in allowed_types


def _get_notification_recipients(target_users, target_roles) -> list:
    target_users = target_users or []
    target_roles = target_roles or []
    if not target_users and not target_roles:
        return []

    users = load_users()
    recipients = []
    seen: set = set()

    for user in users:
        if user.get("id") in target_users or any(
            role in target_roles for role in user.get("roles", [])
        ):
            email = user.get("email")
            if email and email not in seen:
                seen.add(email)
                recipients.append(email)

    return recipients


def _build_notification_message(notification, recipient_count=None) -> tuple:
    summary_parts = []
    if notification.get("target_users"):
        summary_parts.append(
            f"対象ユーザーID: {', '.join(map(str, notification['target_users']))}"
        )
    if notification.get("target_roles"):
        summary_parts.append(f"対象ロール: {', '.join(notification['target_roles'])}")
    if recipient_count is not None:
        summary_parts.append(f"受信者数: {recipient_count}")

    summary = " / ".join(summary_parts)
    subject = (
        f"[{notification.get('type', 'notification')}] {notification.get('title', '')}"
    )
    body_lines = [
        notification.get("message", ""),
        "",
        f"タイプ: {notification.get('type', '')}",
        f"優先度: {notification.get('priority', '')}",
        f"通知ID: {notification.get('id', '')}",
        f"作成日時: {notification.get('created_at', '')}",
    ]
    if summary:
        body_lines.append(summary)

    body = "\n".join(body_lines).strip()
    return subject, body


def _retry_operation(operation, label, max_attempts=5, backoff_seconds=0.5) -> dict:
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            operation()
            return {"status": "sent", "attempts": attempt}
        except Exception as exc:
            last_error = str(exc)
            logger.info("%s attempt %d failed: %s", label, attempt, exc)
            if attempt < max_attempts:
                time.sleep(backoff_seconds * attempt)
    return {"status": "failed", "attempts": max_attempts, "last_error": last_error}


def _get_retry_count() -> int:
    raw = os.environ.get("MKS_NOTIFICATION_RETRY_COUNT", "5").strip()
    return int(raw) if raw.isdigit() else 5


def _send_teams_notification(notification) -> dict:
    webhook_url = os.environ.get("MKS_TEAMS_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return {"status": "skipped", "reason": "MKS_TEAMS_WEBHOOK_URL not set"}

    if _requests_lib is None:
        return {"status": "skipped", "reason": "requests library not available"}

    subject, body = _build_notification_message(notification)
    payload = {"text": f"{subject}\n{body}"}
    data = json.dumps(payload).encode("utf-8")

    def _post():
        response = _requests_lib.post(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code not in (200, 201, 202):
            raise RuntimeError(f"Teams webhook response: {response.status_code}")

    return _retry_operation(_post, "teams", max_attempts=_get_retry_count())


def _send_email_notification(notification) -> dict:
    smtp_host = os.environ.get("MKS_SMTP_HOST", "").strip()
    smtp_from = os.environ.get("MKS_SMTP_FROM", "").strip()
    if not smtp_host or not smtp_from:
        return {"status": "skipped", "reason": "SMTP config not set"}

    recipients = _get_notification_recipients(
        notification.get("target_users"), notification.get("target_roles")
    )
    if not recipients:
        return {"status": "skipped", "reason": "no recipients"}

    smtp_port = int(os.environ.get("MKS_SMTP_PORT", "587"))
    smtp_user = os.environ.get("MKS_SMTP_USER", "").strip()
    smtp_password = os.environ.get("MKS_SMTP_PASSWORD", "").strip()
    use_tls = _env_bool("MKS_SMTP_USE_TLS", True)
    use_ssl = _env_bool("MKS_SMTP_USE_SSL", False)

    subject, body = _build_notification_message(
        notification, recipient_count=len(recipients)
    )
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    context = ssl.create_default_context()

    def _send():
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10, context=context) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            return
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if use_tls:
                server.starttls(context=context)
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

    result = _retry_operation(_send, "email", max_attempts=_get_retry_count())
    result["recipient_count"] = len(recipients)
    return result


def _send_external_notifications(notification) -> dict:
    """外部通知（Teams / Email）を送信"""
    if _external_notifications_disabled():
        logger.debug("External notifications disabled")
        return {}

    if not _should_send_external(notification.get("type", "")):
        logger.debug(
            "Notification type '%s' not in allowed types", notification.get("type")
        )
        return {
            "teams": {"reason": "type filtered"},
            "email": {"reason": "type filtered"},
        }

    results = {}
    teams_result = _send_teams_notification(notification)
    if teams_result.get("status") != "skipped":
        results["teams"] = teams_result

    email_result = _send_email_notification(notification)
    if email_result.get("status") != "skipped":
        results["email"] = email_result

    return results


def create_notification(
    title,
    message,
    type,
    target_users=None,
    target_roles=None,
    priority="medium",
    related_entity_type=None,
    related_entity_id=None,
) -> dict:
    """通知を作成してJSONに保存"""
    notifications = load_data("notifications.json")

    new_notification = {
        "id": max([n["id"] for n in notifications], default=0) + 1,
        "title": title,
        "message": message,
        "type": type,
        "target_users": target_users or [],
        "target_roles": target_roles or [],
        "priority": priority,
        "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
        "created_at": datetime.now().isoformat(),
        "status": "sent",
        "read_by": [],
        "external_delivery": {},
        "external_delivery_failed": False,
    }

    notifications.append(new_notification)
    save_data("notifications.json", notifications)

    delivery_results = _send_external_notifications(new_notification)
    if delivery_results:
        new_notification["external_delivery"] = delivery_results
        new_notification["external_delivery_failed"] = any(
            result.get("status") == "failed" for result in delivery_results.values()
        )
        save_data("notifications.json", notifications)

    return new_notification
