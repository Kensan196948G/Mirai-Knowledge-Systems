import json
import pathlib
import smtplib
import types
import urllib.request

import app_v2


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_exempt_static_filters():
    with app_v2.app.test_request_context("/static/app.js"):
        assert app_v2.exempt_static() is True

    with app_v2.app.test_request_context("/api/v1/knowledge"):
        assert app_v2.exempt_static() is False


def test_verify_password_bcrypt_exception(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise ValueError("bcrypt failure")

    monkeypatch.setattr(app_v2.bcrypt, "checkpw", _raise)
    assert app_v2.verify_password("secret", "$2b$12$invalid") is False


def test_missing_user_paths(client):
    with app_v2.app.app_context():
        token = app_v2.create_access_token(identity="999")

    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/knowledge", headers=headers).status_code == 404
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 404
    assert client.get("/api/v1/notifications", headers=headers).status_code == 404
    assert (
        client.get("/api/v1/notifications/unread/count", headers=headers).status_code
        == 404
    )


def test_security_headers_production(client, admin_token, monkeypatch):
    monkeypatch.setattr(app_v2, "IS_PRODUCTION", True)
    monkeypatch.setattr(app_v2, "HSTS_ENABLED", True)
    monkeypatch.setattr(app_v2, "HSTS_INCLUDE_SUBDOMAINS", True)
    monkeypatch.setattr(app_v2, "HSTS_MAX_AGE", 123)

    response = client.get(
        "/api/v1/knowledge", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "upgrade-insecure-requests" in response.headers.get(
        "Content-Security-Policy", ""
    )
    assert (
        response.headers.get("Cache-Control") == "no-store, no-cache, must-revalidate"
    )

    hsts = response.headers.get("Strict-Transport-Security", "")
    assert "max-age=123" in hsts
    assert "includeSubDomains" in hsts


def test_build_notification_message():
    notification = {
        "id": 10,
        "title": "Test Title",
        "message": "Body message",
        "type": "approval_required",
        "priority": "high",
        "created_at": "2025-01-01T00:00:00",
        "target_users": [1, 2],
        "target_roles": ["admin"],
    }

    subject, body = app_v2._build_notification_message(notification, recipient_count=2)

    assert subject.startswith("[approval_required]")
    assert "対象ユーザーID" in body
    assert "対象ロール" in body
    assert "受信者数: 2" in body


def test_retry_operation_success_and_failure():
    attempts = {"count": 0}

    def _flaky():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("temporary")

    success = app_v2._retry_operation(_flaky, "test", max_attempts=3, backoff_seconds=0)
    assert success["status"] == "sent"
    assert success["attempts"] == 2

    def _fail():
        raise ValueError("nope")

    failed = app_v2._retry_operation(_fail, "test", max_attempts=2, backoff_seconds=0)
    assert failed["status"] == "failed"
    assert failed["attempts"] == 2
    assert failed["last_error"]


def test_get_retry_count(monkeypatch):
    monkeypatch.setenv("MKS_NOTIFICATION_RETRY_COUNT", "3")
    assert app_v2._get_retry_count() == 3

    monkeypatch.setenv("MKS_NOTIFICATION_RETRY_COUNT", "abc")
    assert app_v2._get_retry_count() == 5


def test_send_teams_notification_skip(monkeypatch):
    monkeypatch.delenv("MKS_TEAMS_WEBHOOK_URL", raising=False)
    result = app_v2._send_teams_notification({"title": "t"})
    assert result["status"] == "skipped"


def test_send_teams_notification_success(monkeypatch):
    class DummyResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _dummy_urlopen(_request, timeout=10):
        return DummyResponse()

    monkeypatch.setenv("MKS_TEAMS_WEBHOOK_URL", "https://example.invalid")
    monkeypatch.setenv("MKS_NOTIFICATION_RETRY_COUNT", "1")
    monkeypatch.setattr(urllib.request, "urlopen", _dummy_urlopen)

    result = app_v2._send_teams_notification(
        {"title": "Test", "message": "Hello", "type": "approval_required"}
    )

    assert result["status"] == "sent"


def test_send_email_notification_skip_missing_config(monkeypatch):
    monkeypatch.delenv("MKS_SMTP_HOST", raising=False)
    monkeypatch.delenv("MKS_SMTP_FROM", raising=False)
    result = app_v2._send_email_notification({"title": "Test"})
    assert result["status"] == "skipped"


def test_send_email_notification_skip_no_recipients(monkeypatch, client):
    monkeypatch.setenv("MKS_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("MKS_SMTP_FROM", "noreply@example.com")

    result = app_v2._send_email_notification({"title": "Test", "target_users": [999]})

    assert result["status"] == "skipped"
    assert result["reason"] == "no recipients"


def test_send_email_notification_success_tls(monkeypatch, client):
    data_dir = pathlib.Path(app_v2.app.config["DATA_DIR"])
    users_file = data_dir / "users.json"
    users = json.loads(users_file.read_text(encoding="utf-8"))
    users[0]["email"] = "admin@example.com"
    _write_json(users_file, users)

    monkeypatch.setenv("MKS_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("MKS_SMTP_FROM", "noreply@example.com")
    monkeypatch.setenv("MKS_SMTP_PORT", "587")
    monkeypatch.setenv("MKS_SMTP_USER", "user")
    monkeypatch.setenv("MKS_SMTP_PASSWORD", "pass")
    monkeypatch.setenv("MKS_SMTP_USE_TLS", "true")
    monkeypatch.setenv("MKS_SMTP_USE_SSL", "false")
    monkeypatch.setenv("MKS_NOTIFICATION_RETRY_COUNT", "1")

    class DummySMTP:
        def __init__(self, host, port, timeout=10):
            self.host = host
            self.port = port
            self.tls_started = False
            self.logged_in = False
            self.sent = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self, context=None):
            self.tls_started = True

        def login(self, user, password):
            self.logged_in = True

        def send_message(self, _msg):
            self.sent = True

    monkeypatch.setattr(smtplib, "SMTP", DummySMTP)

    result = app_v2._send_email_notification(
        {
            "title": "Test",
            "message": "Hello",
            "type": "approval_required",
            "target_roles": ["admin"],
        }
    )

    assert result["status"] == "sent"
    assert result["recipient_count"] == 1


def test_send_external_notifications_type_filtered(monkeypatch):
    monkeypatch.setitem(app_v2.app.config, "TESTING", False)
    monkeypatch.setenv("MKS_EXTERNAL_NOTIFICATION_TYPES", "incident")

    result = app_v2._send_external_notifications({"type": "approval_required"})

    assert result["teams"]["reason"] == "type filtered"
    assert result["email"]["reason"] == "type filtered"


def test_index_and_static_cache_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    assert (
        response.headers.get("Cache-Control") == "no-cache, no-store, must-revalidate"
    )

    static_root = pathlib.Path(app_v2.app.static_folder)
    js_path = static_root / "app.js"
    html_path = static_root / "index.html"

    if js_path.exists():
        response = client.get("/app.js")
        assert response.headers.get("Cache-Control") == "public, max-age=3600"

    if html_path.exists():
        response = client.get("/index.html")
        assert (
            response.headers.get("Cache-Control")
            == "no-cache, no-store, must-revalidate"
        )


def test_error_handlers_and_jwt_callbacks():
    with app_v2.app.app_context():
        response, status = app_v2.internal_error(Exception("boom"))
        assert status == 500
        assert response.get_json()["error"]["code"] == "INTERNAL_ERROR"

        error = types.SimpleNamespace(description="10 seconds")
        response, status = app_v2.ratelimit_handler(error)
        assert status == 429
        assert response.get_json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

        response, status = app_v2.expired_token_callback({}, {})
        assert status == 401
        assert response.get_json()["error"]["code"] == "TOKEN_EXPIRED"

        response, status = app_v2.invalid_token_callback("invalid")
        assert status == 401
        assert response.get_json()["error"]["code"] == "INVALID_TOKEN"

        response, status = app_v2.missing_token_callback("missing")
        assert status == 401
        assert response.get_json()["error"]["code"] == "MISSING_TOKEN"


def test_init_demo_users_creates_default(tmp_path, monkeypatch):
    monkeypatch.setitem(app_v2.app.config, "DATA_DIR", str(tmp_path))
    users_file = tmp_path / "users.json"
    if users_file.exists():
        users_file.unlink()

    app_v2.init_demo_users()

    users = json.loads(users_file.read_text(encoding="utf-8"))
    usernames = {user["username"] for user in users}
    assert {"admin", "yamada", "partner"}.issubset(usernames)
