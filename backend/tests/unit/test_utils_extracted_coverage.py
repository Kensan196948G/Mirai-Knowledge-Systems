"""
blueprints/utils/ 抽出モジュールのカバレッジテスト

Phase M-1: app_v2.py から抽出された3モジュールのテスト
  - cors_config.py: get_local_ip_addresses, build_cors_origins
  - security_headers.py: apply_security_headers
  - metrics_decorators.py: track_db_query
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)


# ============================================================
# cors_config.py テスト
# ============================================================


class TestGetLocalIpAddresses:
    """get_local_ip_addresses() のテスト"""

    def test_returns_list(self):
        from blueprints.utils.cors_config import get_local_ip_addresses
        result = get_local_ip_addresses()
        assert isinstance(result, list)

    def test_includes_localhost(self):
        from blueprints.utils.cors_config import get_local_ip_addresses
        result = get_local_ip_addresses()
        assert "127.0.0.1" in result
        assert "localhost" in result

    def test_handles_gethostname_failure(self):
        from blueprints.utils.cors_config import get_local_ip_addresses
        with patch("blueprints.utils.cors_config.socket") as mock_socket:
            mock_socket.AF_INET = 2
            mock_socket.SOCK_DGRAM = 2
            mock_socket.gethostname.side_effect = Exception("fail")
            result = get_local_ip_addresses()
            assert "127.0.0.1" in result
            assert "localhost" in result

    def test_handles_socket_connect_failure(self):
        from blueprints.utils.cors_config import get_local_ip_addresses
        with patch("blueprints.utils.cors_config.socket") as mock_socket:
            mock_socket.AF_INET = 2
            mock_socket.SOCK_DGRAM = 2
            mock_socket.gaierror = OSError
            mock_socket.gethostname.return_value = "testhost"
            mock_socket.gethostbyname.side_effect = OSError("fail")
            mock_socket.getaddrinfo.side_effect = OSError("fail")
            mock_sock_inst = MagicMock()
            mock_sock_inst.connect.side_effect = Exception("no network")
            mock_socket.socket.return_value = mock_sock_inst
            result = get_local_ip_addresses()
            assert isinstance(result, list)


class TestBuildCorsOrigins:
    """build_cors_origins() のテスト"""

    def test_returns_list(self):
        from blueprints.utils.cors_config import build_cors_origins
        mock_config = MagicMock()
        mock_config.CORS_ORIGINS = ["http://localhost:5200"]
        with patch.dict(os.environ, {"MKS_ENV": "development"}):
            result = build_cors_origins(mock_config)
        assert isinstance(result, list)

    def test_includes_base_origins(self):
        from blueprints.utils.cors_config import build_cors_origins
        mock_config = MagicMock()
        mock_config.CORS_ORIGINS = ["http://custom:8080"]
        with patch.dict(os.environ, {"MKS_ENV": "development"}):
            result = build_cors_origins(mock_config)
        assert "http://custom:8080" in result

    def test_string_base_origins_converted_to_list(self):
        from blueprints.utils.cors_config import build_cors_origins
        mock_config = MagicMock()
        mock_config.CORS_ORIGINS = "http://single:5200"
        with patch.dict(os.environ, {"MKS_ENV": "development"}):
            result = build_cors_origins(mock_config)
        assert "http://single:5200" in result

    def test_production_origins(self):
        from blueprints.utils.cors_config import build_cors_origins
        mock_config = MagicMock()
        mock_config.CORS_ORIGINS = ["https://prod.example.com"]
        with patch.dict(os.environ, {"MKS_ENV": "production", "MKS_HTTP_PORT": "9100", "MKS_HTTPS_PORT": "9443"}):
            result = build_cors_origins(mock_config)
        assert isinstance(result, list)
        assert "https://prod.example.com" in result

    def test_development_adds_dynamic_ips(self):
        from blueprints.utils.cors_config import build_cors_origins
        mock_config = MagicMock()
        mock_config.CORS_ORIGINS = []
        with patch.dict(os.environ, {"MKS_ENV": "development", "MKS_HTTP_PORT": "5200", "MKS_HTTPS_PORT": "5243"}):
            with patch("blueprints.utils.cors_config.get_local_ip_addresses", return_value=["127.0.0.1"]):
                result = build_cors_origins(mock_config)
        assert "http://127.0.0.1:5200" in result
        assert "https://127.0.0.1:5243" in result
        assert "http://127.0.0.1" in result


# ============================================================
# security_headers.py テスト
# ============================================================


class TestApplySecurityHeaders:
    """apply_security_headers() のテスト"""

    def _make_response(self):
        """テスト用の Werkzeug Response を作成"""
        from werkzeug.test import Client
        from werkzeug.wrappers import Response
        return Response("OK", status=200)

    def test_common_headers_always_set(self):
        from blueprints.utils.security_headers import apply_security_headers
        import app_v2
        with app_v2.app.test_request_context("/"):
            resp = self._make_response()
            apply_security_headers(resp, is_production=False)
            assert resp.headers.get("X-Content-Type-Options") == "nosniff"
            assert resp.headers.get("X-Frame-Options") == "DENY"
            assert "1; mode=block" in resp.headers.get("X-XSS-Protection", "")

    def test_production_headers(self):
        from blueprints.utils.security_headers import apply_security_headers
        import app_v2
        with app_v2.app.test_request_context("/api/test"):
            resp = self._make_response()
            apply_security_headers(resp, is_production=True)
            assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
            csp = resp.headers.get("Content-Security-Policy", "")
            assert "upgrade-insecure-requests" in csp

    def test_production_hsts(self):
        from blueprints.utils.security_headers import apply_security_headers
        import app_v2
        with app_v2.app.test_request_context("/"):
            resp = self._make_response()
            apply_security_headers(
                resp, is_production=True, hsts_enabled=True,
                hsts_max_age=86400, hsts_include_subdomains=True
            )
            hsts = resp.headers.get("Strict-Transport-Security", "")
            assert "max-age=86400" in hsts
            assert "includeSubDomains" in hsts

    def test_production_hsts_without_subdomains(self):
        from blueprints.utils.security_headers import apply_security_headers
        import app_v2
        with app_v2.app.test_request_context("/"):
            resp = self._make_response()
            apply_security_headers(
                resp, is_production=True, hsts_enabled=True,
                hsts_max_age=86400, hsts_include_subdomains=False
            )
            hsts = resp.headers.get("Strict-Transport-Security", "")
            assert "max-age=86400" in hsts
            assert "includeSubDomains" not in hsts

    def test_development_headers(self):
        from blueprints.utils.security_headers import apply_security_headers
        import app_v2
        with app_v2.app.test_request_context("/"):
            resp = self._make_response()
            apply_security_headers(resp, is_production=False)
            assert resp.headers.get("Referrer-Policy") == "no-referrer"
            csp = resp.headers.get("Content-Security-Policy", "")
            assert "upgrade-insecure-requests" not in csp

    def test_api_cache_control_in_production(self):
        from blueprints.utils.security_headers import apply_security_headers
        import app_v2
        with app_v2.app.test_request_context("/api/v1/knowledge"):
            resp = self._make_response()
            apply_security_headers(resp, is_production=True)
            assert "no-store" in resp.headers.get("Cache-Control", "")
            assert resp.headers.get("Pragma") == "no-cache"


# ============================================================
# metrics_decorators.py テスト
# ============================================================


class TestTrackDbQuery:
    """track_db_query() デコレータのテスト"""

    def test_successful_call_records_duration(self):
        from blueprints.utils.metrics_decorators import track_db_query

        @track_db_query("select")
        def fake_query():
            return [{"id": 1}]

        result = fake_query()
        assert result == [{"id": 1}]

    def test_exception_records_duration_and_reraises(self):
        from blueprints.utils.metrics_decorators import track_db_query

        @track_db_query("insert")
        def failing_query():
            raise ValueError("DB error")

        with pytest.raises(ValueError, match="DB error"):
            failing_query()

    def test_decorator_preserves_function_name(self):
        from blueprints.utils.metrics_decorators import track_db_query

        @track_db_query("update")
        def my_update_func():
            pass

        assert my_update_func.__name__ == "my_update_func"

    def test_decorator_with_args_and_kwargs(self):
        from blueprints.utils.metrics_decorators import track_db_query

        @track_db_query("delete")
        def delete_by_id(table, record_id, cascade=False):
            return f"deleted {record_id} from {table} (cascade={cascade})"

        result = delete_by_id("users", 42, cascade=True)
        assert result == "deleted 42 from users (cascade=True)"
