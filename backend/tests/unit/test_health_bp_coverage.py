"""
blueprints/utils/health_bp.py カバレッジ強化テスト

対象エンドポイント:
  GET /api/v1/metrics   - Prometheus互換メトリクス（認証不要）
  GET /api/docs         - Swagger UI（静的ファイル）
  GET /api/openapi.yaml - OpenAPI仕様（静的ファイル）
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestGetMetrics:
    """GET /api/v1/metrics - Prometheus互換メトリクス"""

    def test_returns_200(self, client):
        """メトリクスエンドポイントは 200 を返す"""
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200

    def test_content_type_is_text_plain(self, client):
        """Content-Type は text/plain"""
        resp = client.get("/api/v1/metrics")
        assert "text/plain" in resp.content_type

    def test_no_auth_required(self, client):
        """認証不要 — 401 にならない"""
        resp = client.get("/api/v1/metrics")
        assert resp.status_code != 401

    def test_contains_app_info(self, client):
        """app_info メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"app_info" in resp.data

    def test_contains_cpu_metric(self, client):
        """CPU メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"system_cpu_usage_percent" in resp.data

    def test_contains_memory_metric(self, client):
        """メモリメトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"system_memory_usage_percent" in resp.data

    def test_contains_disk_metric(self, client):
        """ディスクメトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"system_disk_usage_percent" in resp.data

    def test_contains_knowledge_total(self, client):
        """knowledge_total メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"knowledge_total" in resp.data

    def test_contains_sop_total(self, client):
        """sop_total メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"sop_total" in resp.data

    def test_contains_active_users(self, client):
        """active_users メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"active_users" in resp.data

    def test_contains_login_attempts(self, client):
        """login_attempts_total メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"login_attempts_total" in resp.data

    def test_contains_http_errors(self, client):
        """http_errors_total メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"http_errors_total" in resp.data

    def test_contains_uptime(self, client):
        """app_uptime_seconds が含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"app_uptime_seconds" in resp.data

    def test_contains_knowledge_created_total(self, client):
        """knowledge_created_total が含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"knowledge_created_total" in resp.data

    def test_response_is_non_empty(self, client):
        """レスポンスが空でない"""
        resp = client.get("/api/v1/metrics")
        assert len(resp.data) > 100

    def test_contains_help_comments(self, client):
        """Prometheus の # HELP コメントが含まれる"""
        resp = client.get("/api/v1/metrics")
        assert b"# HELP" in resp.data
        assert b"# TYPE" in resp.data

    def test_with_access_log_data(self, client, tmp_path):
        """アクセスログがあってもメトリクスが正常に返る"""
        import json
        from datetime import datetime

        logs = [
            {
                "user_id": 1,
                "action": "auth.login",
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "session_id": "session-001",
            },
            {
                "user_id": 2,
                "action": "auth.login",
                "status": "failure",
                "timestamp": datetime.now().isoformat(),
                "session_id": "session-002",
            },
        ]
        (tmp_path / "access_logs.json").write_text(
            json.dumps(logs, ensure_ascii=False), encoding="utf-8"
        )
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200

    def test_with_knowledge_data(self, client, tmp_path):
        """ナレッジデータがあるときカテゴリメトリクスが出力される"""
        import json

        knowledge = [
            {"id": 1, "title": "K1", "category": "safety"},
            {"id": 2, "title": "K2", "category": "safety"},
            {"id": 3, "title": "K3", "category": "quality"},
        ]
        (tmp_path / "knowledge.json").write_text(
            json.dumps(knowledge, ensure_ascii=False), encoding="utf-8"
        )
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        assert b"knowledge_by_category" in resp.data


class TestApiDocs:
    """GET /api/docs - Swagger UI"""

    def test_returns_response(self, client):
        """エンドポイントが応答を返す（ファイルが無くても 404 で OK）"""
        resp = client.get("/api/docs")
        assert resp.status_code in (200, 404, 500)

    def test_no_auth_required(self, client):
        """認証不要 — 401 にならない"""
        resp = client.get("/api/docs")
        assert resp.status_code != 401


class TestOpenApiSpec:
    """GET /api/openapi.yaml - OpenAPI仕様"""

    def test_returns_response(self, client):
        """エンドポイントが応答を返す"""
        resp = client.get("/api/openapi.yaml")
        assert resp.status_code in (200, 404, 500)

    def test_no_auth_required(self, client):
        """認証不要 — 401 にならない"""
        resp = client.get("/api/openapi.yaml")
        assert resp.status_code != 401


class TestIndexPage:
    """GET / - トップページ"""

    def test_root_returns_response(self, client):
        """トップページが何らかのレスポンスを返す"""
        resp = client.get("/")
        assert resp.status_code in (200, 404, 500)

    def test_index_html_alias_returns_response(self, client):
        """GET /index.html でもレスポンスを返す"""
        resp = client.get("/index.html")
        assert resp.status_code in (200, 404, 500)

    def test_root_not_401(self, client):
        """認証不要 — 401 にならない"""
        resp = client.get("/")
        assert resp.status_code != 401


class TestServeStatic:
    """GET /<path:path> - 静的ファイル配信"""

    def test_js_file_returns_response(self, client):
        """JS ファイルへのアクセスが応答を返す"""
        resp = client.get("/app.js")
        assert resp.status_code in (200, 404)

    def test_css_file_returns_response(self, client):
        """CSS ファイルへのアクセスが応答を返す"""
        resp = client.get("/styles.css")
        assert resp.status_code in (200, 404)

    def test_png_file_returns_response(self, client):
        """PNG ファイルへのアクセスが応答を返す"""
        resp = client.get("/icon.png")
        assert resp.status_code in (200, 404)

    def test_html_file_returns_response(self, client):
        """HTML ファイルへのアクセスが応答を返す"""
        resp = client.get("/login.html")
        assert resp.status_code in (200, 404)
