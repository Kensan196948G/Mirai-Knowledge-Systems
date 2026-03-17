"""通知サービス (Phase N-1: app_helpers.py から分離)

外部通知（Teams / Email）とシステム内通知の作成・送信を管理する。

循環インポート回避のため、load_data / save_data / load_users は
関数スコープ内で遅延インポートする。
"""

import json
import logging
import os
import smtplib
import ssl
import time
from datetime import datetime
from email.message import EmailMessage

try:
    import requests as _requests_lib
except ImportError:
    _requests_lib = None

logger = logging.getLogger(__name__)


# ================================================================
# 環境変数ヘルパー
# ================================================================


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


# ================================================================
# 外部通知フィルタリング
# ================================================================


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


# ================================================================
# 通知受信者・メッセージ構築
# ================================================================


def _get_notification_recipients(target_users, target_roles) -> list:
    target_users = target_users or []
    target_roles = target_roles or []
    if not target_users and not target_roles:
        return []

    # 遅延インポートで循環インポート回避
    from app_helpers import load_users
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


# ================================================================
# リトライ
# ================================================================


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


# ================================================================
# Teams / Email 送信
# ================================================================


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


# ================================================================
# 外部通知ディスパッチャー
# ================================================================


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


# ================================================================
# 通知作成（メイン公開 API）
# ================================================================


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
    # 遅延インポートで循環インポート回避
    from app_helpers import load_data, save_data

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
