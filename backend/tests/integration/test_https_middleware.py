"""
統合テスト: HTTPSミドルウェア

HTTPS強制リダイレクトミドルウェアのテスト
"""
import pytest
import os
from app_v2 import HTTPSRedirectMiddleware, app


class TestHTTPSRedirectMiddleware:
    """HTTPSリダイレクトミドルウェアのテスト"""

    def test_middleware_disabled_by_default(self):
        """デフォルトでHTTPS強制が無効であることを確認"""
        middleware = HTTPSRedirectMiddleware(app)
        assert middleware.force_https is False

    def test_middleware_enabled_via_param(self):
        """パラメータでHTTPS強制を有効化できることを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True)
        assert middleware.force_https is True

    def test_middleware_enabled_via_env_true(self):
        """環境変数'true'でHTTPS強制を有効化できることを確認"""
        os.environ['MKS_FORCE_HTTPS'] = 'true'
        middleware = HTTPSRedirectMiddleware(app)
        assert middleware.force_https is True
        del os.environ['MKS_FORCE_HTTPS']

    def test_middleware_enabled_via_env_1(self):
        """環境変数'1'でHTTPS強制を有効化できることを確認"""
        os.environ['MKS_FORCE_HTTPS'] = '1'
        middleware = HTTPSRedirectMiddleware(app)
        assert middleware.force_https is True
        del os.environ['MKS_FORCE_HTTPS']

    def test_middleware_enabled_via_env_yes(self):
        """環境変数'yes'でHTTPS強制を有効化できることを確認"""
        os.environ['MKS_FORCE_HTTPS'] = 'yes'
        middleware = HTTPSRedirectMiddleware(app)
        assert middleware.force_https is True
        del os.environ['MKS_FORCE_HTTPS']

    def test_middleware_disabled_via_env_false(self):
        """環境変数'false'でHTTPS強制が無効であることを確認"""
        os.environ['MKS_FORCE_HTTPS'] = 'false'
        middleware = HTTPSRedirectMiddleware(app)
        assert middleware.force_https is False
        del os.environ['MKS_FORCE_HTTPS']

    def test_trust_proxy_disabled_by_default(self):
        """デフォルトでプロキシヘッダーの信頼が無効であることを確認"""
        middleware = HTTPSRedirectMiddleware(app)
        assert middleware.trust_proxy is False

    def test_trust_proxy_enabled_via_param(self):
        """パラメータでプロキシヘッダーの信頼を有効化できることを確認"""
        middleware = HTTPSRedirectMiddleware(app, trust_proxy=True)
        assert middleware.trust_proxy is True

    def test_trust_proxy_enabled_via_env(self):
        """環境変数でプロキシヘッダーの信頼を有効化できることを確認"""
        os.environ['MKS_TRUST_PROXY_HEADERS'] = 'true'
        middleware = HTTPSRedirectMiddleware(app)
        assert middleware.trust_proxy is True
        del os.environ['MKS_TRUST_PROXY_HEADERS']


class TestHTTPSRedirectBehavior:
    """HTTPSリダイレクトの動作テスト"""

    def test_no_redirect_when_disabled(self):
        """HTTPS強制が無効の場合、リダイレクトしないことを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=False)

        # モックのWSGI環境
        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        called = {'value': False}

        def start_response(status, headers):
            called['value'] = True
            # リダイレクトではないことを確認
            assert not status.startswith('30')

        # アプリケーションが通常通り呼ばれることを確認
        result = middleware(environ, start_response)
        # start_responseが呼ばれるか、アプリが呼ばれる
        assert result is not None

    def test_redirect_http_to_https(self):
        """HTTPからHTTPSへリダイレクトすることを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        status_code = None
        location = None

        def start_response(status, headers):
            nonlocal status_code, location
            status_code = status
            for header, value in headers:
                if header == 'Location':
                    location = value

        result = middleware(environ, start_response)

        assert status_code == '301 Moved Permanently'
        assert location == 'https://example.com/api/v1/knowledge'
        assert result == [b'']

    def test_redirect_preserves_query_string(self):
        """クエリ文字列を保持してリダイレクトすることを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/search',
            'QUERY_STRING': 'q=test&category=technical'
        }

        location = None

        def start_response(status, headers):
            nonlocal location
            for header, value in headers:
                if header == 'Location':
                    location = value

        middleware(environ, start_response)

        assert location == 'https://example.com/api/search?q=test&category=technical'

    def test_no_redirect_when_already_https(self):
        """既にHTTPSの場合はリダイレクトしないことを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True)

        environ = {
            'wsgi.url_scheme': 'https',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        redirected = {'value': False}

        def start_response(status, headers):
            if status.startswith('30'):
                redirected['value'] = True

        result = middleware(environ, start_response)

        # リダイレクトされないことを確認
        assert not redirected['value']


class TestHTTPSRedirectWithProxy:
    """プロキシ経由のHTTPSリダイレクトテスト"""

    def test_trust_x_forwarded_proto_header(self):
        """X-Forwarded-Protoヘッダーを信頼することを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True, trust_proxy=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_X_FORWARDED_PROTO': 'https',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        redirected = {'value': False}

        def start_response(status, headers):
            if status.startswith('30'):
                redirected['value'] = True

        middleware(environ, start_response)

        # X-Forwarded-ProtoがHTTPSなのでリダイレクトしない
        assert not redirected['value']

    def test_redirect_when_x_forwarded_proto_http(self):
        """X-Forwarded-ProtoがHTTPの場合はリダイレクトすることを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True, trust_proxy=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_X_FORWARDED_PROTO': 'http',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        status_code = None

        def start_response(status, headers):
            nonlocal status_code
            status_code = status

        middleware(environ, start_response)

        assert status_code == '301 Moved Permanently'

    def test_trust_x_forwarded_host_header(self):
        """X-Forwarded-Hostヘッダーを信頼することを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True, trust_proxy=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'internal.example.com',
            'HTTP_X_FORWARDED_HOST': 'public.example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        location = None

        def start_response(status, headers):
            nonlocal location
            for header, value in headers:
                if header == 'Location':
                    location = value

        middleware(environ, start_response)

        # X-Forwarded-Hostが使用されることを確認
        assert location == 'https://public.example.com/api/v1/knowledge'

    def test_ignore_proxy_headers_when_not_trusted(self):
        """プロキシヘッダーを信頼しない場合は無視することを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True, trust_proxy=False)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_X_FORWARDED_PROTO': 'https',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        status_code = None

        def start_response(status, headers):
            nonlocal status_code
            status_code = status

        middleware(environ, start_response)

        # X-Forwarded-Protoを無視してリダイレクト
        assert status_code == '301 Moved Permanently'


class TestHTTPSRedirectEdgeCases:
    """HTTPSリダイレクトのエッジケーステスト"""

    def test_handles_missing_http_host(self):
        """HTTP_HOSTが欠けている場合の処理を確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'SERVER_NAME': 'fallback.example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/v1/knowledge',
            'QUERY_STRING': ''
        }

        location = None

        def start_response(status, headers):
            nonlocal location
            for header, value in headers:
                if header == 'Location':
                    location = value

        middleware(environ, start_response)

        # SERVER_NAMEが使用されることを確認
        assert location == 'https://fallback.example.com/api/v1/knowledge'

    def test_handles_root_path(self):
        """ルートパスのリダイレクトを確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/',
            'QUERY_STRING': ''
        }

        location = None

        def start_response(status, headers):
            nonlocal location
            for header, value in headers:
                if header == 'Location':
                    location = value

        middleware(environ, start_response)

        assert location == 'https://example.com/'

    def test_handles_empty_path(self):
        """空のパスの処理を確認"""
        middleware = HTTPSRedirectMiddleware(app, force_https=True)

        environ = {
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'example.com',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': ''
        }

        location = None

        def start_response(status, headers):
            nonlocal location
            for header, value in headers:
                if header == 'Location':
                    location = value

        middleware(environ, start_response)

        assert location == 'https://example.com/'
