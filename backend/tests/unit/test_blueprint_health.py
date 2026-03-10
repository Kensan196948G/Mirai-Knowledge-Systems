"""
blueprints/utils/health_bp.py Blueprint ユニットテスト

テスト対象エンドポイント:
  GET /api/v1/metrics    - Prometheus互換カスタムメトリクス
  GET /api/docs          - Swagger UI
  GET /api/openapi.yaml  - OpenAPI仕様
  GET /                  - トップページ（静的ファイル）
  GET /<path:path>       - 静的ファイル配信
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# ============================================================
# GET /api/v1/metrics
# ============================================================


class TestGetMetrics:
    def test_metrics_returns_200(self, client):
        """メトリクスエンドポイントが200を返す"""
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200

    def test_metrics_content_type_text(self, client):
        """メトリクスのContent-TypeはPrometheus互換"""
        resp = client.get("/api/v1/metrics")
        assert "text/plain" in resp.content_type

    def test_metrics_no_auth_required(self, client):
        """認証なしでアクセスできる"""
        resp = client.get("/api/v1/metrics")
        assert resp.status_code != 401

    def test_metrics_contains_app_info(self, client):
        """app_info メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "app_info" in text

    def test_metrics_contains_system_cpu(self, client):
        """CPUメトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "system_cpu_usage_percent" in text

    def test_metrics_contains_system_memory(self, client):
        """メモリメトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "system_memory_usage_percent" in text

    def test_metrics_contains_system_disk(self, client):
        """ディスクメトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "system_disk_usage_percent" in text

    def test_metrics_contains_knowledge_total(self, client):
        """ナレッジ総数メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "knowledge_total" in text

    def test_metrics_contains_sop_total(self, client):
        """SOPドキュメント総数が含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "sop_total" in text

    def test_metrics_contains_active_users(self, client):
        """アクティブユーザー数が含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "active_users" in text

    def test_metrics_contains_login_attempts(self, client):
        """ログイン試行数メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "login_attempts_total" in text

    def test_metrics_contains_uptime(self, client):
        """アプリ稼働時間メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "app_uptime_seconds" in text

    def test_metrics_contains_http_requests_comment(self, client):
        """HTTPリクエストメトリクスセクションが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "http_requests_total" in text

    def test_metrics_contains_http_errors(self, client):
        """HTTPエラーメトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "http_errors_total" in text

    def test_metrics_contains_knowledge_searches(self, client):
        """ナレッジ検索数メトリクスが含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "knowledge_searches_total" in text

    def test_metrics_with_access_logs(self, client, tmp_path, monkeypatch):
        """アクセスログが存在する場合のメトリクス取得"""
        import app_helpers

        # アクセスログを書き込む（ログイン成功・失敗を含む）
        from datetime import datetime
        logs = [
            {
                "user_id": 1,
                "action": "auth.login",
                "status": "success",
                "session_id": "sess-001",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "user_id": None,
                "action": "auth.login",
                "status": "failure",
                "session_id": "sess-002",
                "timestamp": datetime.now().isoformat(),
            },
        ]
        (tmp_path / "access_logs.json").write_text(
            json.dumps(logs, ensure_ascii=False), encoding="utf-8"
        )
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        # ログイン成功・失敗がカウントされる
        assert 'login_attempts_total{status="success"}' in text
        assert 'login_attempts_total{status="failure"}' in text

    def test_metrics_prometheus_help_format(self, client):
        """Prometheus の HELP/TYPE 形式が含まれる"""
        resp = client.get("/api/v1/metrics")
        text = resp.data.decode("utf-8")
        assert "# HELP" in text
        assert "# TYPE" in text


# ============================================================
# GET /api/docs  (静的ファイル - テスト環境では404)
# ============================================================


class TestApiDocs:
    def test_api_docs_returns_response(self, client):
        """Swagger UIエンドポイントが何らかのレスポンスを返す"""
        resp = client.get("/api/docs")
        # swagger-ui.htmlが存在しない場合は404、存在すれば200
        assert resp.status_code in (200, 404)

    def test_api_docs_no_auth_required(self, client):
        """認証なしでアクセスできる（401でない）"""
        resp = client.get("/api/docs")
        assert resp.status_code != 401


# ============================================================
# GET /api/openapi.yaml  (静的ファイル - テスト環境では404)
# ============================================================


class TestOpenAPISpec:
    def test_openapi_yaml_returns_response(self, client):
        """OpenAPI仕様エンドポイントが何らかのレスポンスを返す"""
        resp = client.get("/api/openapi.yaml")
        assert resp.status_code in (200, 404)

    def test_openapi_yaml_no_auth_required(self, client):
        """認証なしでアクセスできる（401でない）"""
        resp = client.get("/api/openapi.yaml")
        assert resp.status_code != 401


# ============================================================
# GET /  (静的ファイル配信)
# ============================================================


class TestServeIndex:
    def test_root_returns_response(self, client):
        """ルートパスが何らかのレスポンスを返す"""
        resp = client.get("/")
        # テスト環境ではstaticフォルダが設定されていないため200か404
        assert resp.status_code in (200, 404)

    def test_index_html_alias(self, client):
        """/index.html も同様のレスポンスを返す"""
        resp = client.get("/index.html")
        assert resp.status_code in (200, 404)
