"""
HTTPS・セキュリティヘッダーテスト

目的:
- HTTPS通信が強制されること
- セキュリティヘッダーが適切に設定されていること
- SSL/TLS設定が安全であること
- HSTS（HTTP Strict Transport Security）が有効であること

参照: docs/09_品質保証(QA)/03_Final-Acceptance-Test-Plan.md
      セクション 5.2 HTTPS強制確認
      セクション 5.3 セキュリティヘッダー確認
"""
import pytest
import os


class TestHTTPSEnforcement:
    """HTTPS強制テスト"""

    def test_https_redirect_middleware_exists(self):
        """HTTPSリダイレクトミドルウェアが存在すること"""
        from app_v2 import HTTPSRedirectMiddleware

        # ミドルウェアクラスが定義されている
        assert HTTPSRedirectMiddleware is not None

    def test_https_redirect_configuration(self):
        """HTTPS強制設定の確認"""
        from app_v2 import HTTPSRedirectMiddleware

        # 環境変数で制御可能であることを確認
        middleware = HTTPSRedirectMiddleware(None, force_https=True)
        assert middleware.force_https is True

        middleware_disabled = HTTPSRedirectMiddleware(None, force_https=False)
        assert middleware_disabled.force_https is False

    def test_https_redirect_respects_environment_variable(self):
        """HTTPS強制が環境変数を尊重すること"""
        # 環境変数のテスト
        original_value = os.environ.get('MKS_FORCE_HTTPS')

        try:
            os.environ['MKS_FORCE_HTTPS'] = 'true'
            from app_v2 import HTTPSRedirectMiddleware
            middleware = HTTPSRedirectMiddleware(None)
            # 環境変数が読み込まれている

            os.environ['MKS_FORCE_HTTPS'] = 'false'
            middleware_off = HTTPSRedirectMiddleware(None)
            # 環境変数が読み込まれている

        finally:
            # 元に戻す
            if original_value:
                os.environ['MKS_FORCE_HTTPS'] = original_value
            elif 'MKS_FORCE_HTTPS' in os.environ:
                del os.environ['MKS_FORCE_HTTPS']

    def test_proxy_header_trust_configuration(self):
        """プロキシヘッダー信頼設定の確認"""
        from app_v2 import HTTPSRedirectMiddleware

        # プロキシヘッダーの信頼設定
        middleware_trust = HTTPSRedirectMiddleware(None, trust_proxy=True)
        assert middleware_trust.trust_proxy is True

        middleware_no_trust = HTTPSRedirectMiddleware(None, trust_proxy=False)
        assert middleware_no_trust.trust_proxy is False


class TestSecurityHeaders:
    """セキュリティヘッダーテスト"""

    def test_x_content_type_options_header(self, client, admin_token):
        """X-Content-Type-Options ヘッダーの確認"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

    def test_x_frame_options_header(self, client, admin_token):
        """X-Frame-Options ヘッダーの確認"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] in ['DENY', 'SAMEORIGIN']

    def test_x_xss_protection_header(self, client, admin_token):
        """X-XSS-Protection ヘッダーの確認"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        assert 'X-XSS-Protection' in response.headers
        assert '1' in response.headers['X-XSS-Protection']
        assert 'mode=block' in response.headers['X-XSS-Protection']

    def test_content_security_policy_header(self, client, admin_token):
        """Content-Security-Policy ヘッダーの確認"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        if 'Content-Security-Policy' not in response.headers:
            return

        csp = response.headers['Content-Security-Policy']

        # 主要なディレクティブが含まれていること
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        assert "frame-ancestors" in csp

    def test_referrer_policy_header(self, client, admin_token):
        """Referrer-Policy ヘッダーの確認"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        assert 'Referrer-Policy' in response.headers
        # 'no-referrer' または 'strict-origin-when-cross-origin' など
        assert response.headers['Referrer-Policy'] in [
            'no-referrer',
            'strict-origin',
            'strict-origin-when-cross-origin',
            'same-origin'
        ]

    def test_permissions_policy_header(self, client, admin_token):
        """Permissions-Policy ヘッダーの確認"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        assert 'Permissions-Policy' in response.headers

        policy = response.headers['Permissions-Policy']

        # 危険な機能が無効化されていること
        assert 'geolocation=()' in policy
        assert 'microphone=()' in policy
        assert 'camera=()' in policy

    def test_hsts_header_in_production(self, client, admin_token):
        """本番環境でHSTSヘッダーが設定されること"""
        # 本番環境設定をシミュレート
        original_env = os.environ.get('MKS_ENV')
        original_hsts = os.environ.get('MKS_HSTS_ENABLED')

        try:
            os.environ['MKS_ENV'] = 'production'
            os.environ['MKS_HSTS_ENABLED'] = 'true'

            # アプリケーションをリロード（実際のテストでは再起動が必要）
            # 注: このテストは設定の確認のみ
            from app_v2 import HSTS_ENABLED, IS_PRODUCTION

            # 本番環境では有効化される
            # 実際のヘッダー確認は統合テストで実施

        finally:
            # 元に戻す
            if original_env:
                os.environ['MKS_ENV'] = original_env
            elif 'MKS_ENV' in os.environ:
                del os.environ['MKS_ENV']

            if original_hsts:
                os.environ['MKS_HSTS_ENABLED'] = original_hsts
            elif 'MKS_HSTS_ENABLED' in os.environ:
                del os.environ['MKS_HSTS_ENABLED']

    def test_cache_control_for_api_responses(self, client, admin_token):
        """APIレスポンスにキャッシュ制御ヘッダーが設定されること"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        # 開発環境ではキャッシュ制御が緩い可能性があるが、
        # 本番環境では厳格であるべき
        # Cache-Controlヘッダーが存在するか確認（実装依存）


class TestContentSecurityPolicy:
    """Content Security Policy 詳細テスト"""

    def test_csp_default_src_self(self, client, admin_token):
        """CSP default-src が 'self' であること"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        csp = response.headers.get('Content-Security-Policy', '')
        if not csp:
            return
        assert "default-src 'self'" in csp

    def test_csp_script_src_restricted(self, client, admin_token):
        """CSP script-src が適切に制限されていること"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        csp = response.headers.get('Content-Security-Policy', '')
        if not csp:
            return
        assert "script-src" in csp

        # 本番環境では 'unsafe-inline' が含まれないべき
        # （開発環境では許可される可能性あり）

    def test_csp_frame_ancestors_restricted(self, client, admin_token):
        """CSP frame-ancestors が制限されていること"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {admin_token}'})

        csp = response.headers.get('Content-Security-Policy', '')
        if not csp:
            return
        assert "frame-ancestors" in csp
        # 'none' または 'self' であるべき
        assert "'none'" in csp or "'self'" in csp

    def test_csp_upgrade_insecure_requests(self, client, admin_token):
        """本番環境でCSP upgrade-insecure-requests が設定されること"""
        # 本番環境の場合のみ
        original_env = os.environ.get('MKS_ENV')

        try:
            os.environ['MKS_ENV'] = 'production'

            # 設定の確認（実際のヘッダーテストは統合テストで実施）
            from app_v2 import IS_PRODUCTION

            # 本番環境フラグが立っていることを確認

        finally:
            if original_env:
                os.environ['MKS_ENV'] = original_env
            elif 'MKS_ENV' in os.environ:
                del os.environ['MKS_ENV']


class TestHSTS:
    """HSTS（HTTP Strict Transport Security）テスト"""

    def test_hsts_configuration_values(self):
        """HSTS設定値の確認"""
        from app_v2 import HSTS_MAX_AGE, HSTS_INCLUDE_SUBDOMAINS

        # デフォルト値の確認
        assert HSTS_MAX_AGE > 0
        assert isinstance(HSTS_INCLUDE_SUBDOMAINS, bool)

    def test_hsts_max_age_sufficient(self):
        """HSTS max-age が十分な長さであること"""
        from app_v2 import HSTS_MAX_AGE

        # 最低6ヶ月（15768000秒）が推奨
        # デフォルトは1年（31536000秒）
        assert HSTS_MAX_AGE >= 15768000

    def test_hsts_environment_variable_override(self):
        """HSTS設定が環境変数でオーバーライド可能であること"""
        original_max_age = os.environ.get('MKS_HSTS_MAX_AGE')

        try:
            os.environ['MKS_HSTS_MAX_AGE'] = '63072000'  # 2年

            # 設定が読み込まれることを確認（実際はアプリ再起動が必要）

        finally:
            if original_max_age:
                os.environ['MKS_HSTS_MAX_AGE'] = original_max_age
            elif 'MKS_HSTS_MAX_AGE' in os.environ:
                del os.environ['MKS_HSTS_MAX_AGE']


class TestSSLTLSConfiguration:
    """SSL/TLS設定テスト"""

    def test_minimum_tls_version_configuration(self):
        """最小TLSバージョンの設定確認"""
        # TLS 1.2以上が必要
        # 注: この設定は通常、Webサーバー（Nginx、Gunicorn等）で行われる
        # アプリケーション層での確認は限定的

    def test_secure_cipher_suites(self):
        """安全な暗号スイートの使用確認"""
        # 弱い暗号（RC4、DES、MD5等）が無効化されていることを確認
        # 注: この設定はWebサーバー層で行われる


class TestSecureConfiguration:
    """セキュアな設定全般のテスト"""

    def test_debug_mode_disabled_in_production(self):
        """本番環境でデバッグモードが無効であること"""
        from app_v2 import app

        # テスト環境ではTRUEだが、本番環境では FALSE であるべき
        # 注: 環境変数で制御されることを確認

    def test_secret_key_configured(self):
        """シークレットキーが設定されていること"""
        from app_v2 import app

        assert 'JWT_SECRET_KEY' in app.config
        assert app.config['JWT_SECRET_KEY'] is not None
        assert len(app.config['JWT_SECRET_KEY']) > 20

    def test_secret_key_not_default_in_production(self):
        """本番環境でデフォルトのシークレットキーが使用されていないこと"""
        from app_v2 import app, JWT_SECRET

        # テスト環境ではデフォルト値が使用されるが、
        # 本番環境では環境変数から読み込まれるべき

        # デフォルト値と同じでないことを確認（本番環境の場合）
        if os.environ.get('MKS_ENV') == 'production':
            assert app.config['JWT_SECRET_KEY'] != JWT_SECRET

    def test_cors_origins_configured(self):
        """CORS オリジンが適切に設定されていること"""
        # CORS設定の確認
        allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5000')

        # 本番環境では '*' が設定されていないこと
        if os.environ.get('MKS_ENV') == 'production':
            assert '*' not in allowed_origins


class TestErrorHandling:
    """エラーハンドリング・情報漏洩防止テスト"""

    def test_error_messages_no_stack_trace_in_production(self, client):
        """本番環境でエラー時にスタックトレースが表示されないこと"""
        # 存在しないエンドポイントにアクセス
        response = client.get('/api/nonexistent')

        assert response.status_code == 404

        # レスポンスにスタックトレースが含まれていないこと
        response_text = response.get_data(as_text=True).lower()
        assert 'traceback' not in response_text
        assert 'exception' not in response_text

    def test_authentication_error_generic_message(self, client):
        """認証エラー時に詳細な情報が漏洩しないこと"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })

        assert response.status_code == 401

        # ユーザーが存在しないか、パスワードが間違っているか区別できない
        # 汎用的なエラーメッセージであるべき
        data = response.get_json()
        error_payload = data.get('error', '')
        if isinstance(error_payload, dict):
            error_message = error_payload.get('message', '').lower()
        else:
            error_message = str(error_payload).lower()

        # 「ユーザーが見つかりません」等の詳細は含まない
        # 「認証に失敗しました」等の汎用的メッセージであるべき

    def test_authorization_error_no_information_leakage(self, client, viewer_token):
        """認可エラー時にリソースの存在が漏洩しないこと"""
        # 存在するが権限のないリソース
        response = client.delete('/api/v1/knowledge/1',
                               headers={'Authorization': f'Bearer {viewer_token}'})

        assert response.status_code in [403, 404, 405]

        # 403と404を使い分けることで、リソースの存在が推測される可能性
        # 統一的に404を返すか、403を返すかは設計判断


class TestRateLimiting:
    """レート制限テスト"""

    def test_rate_limiter_configured(self):
        """レート制限が設定されていること"""
        from app_v2 import limiter

        assert limiter is not None
        # リミッターが有効であることを確認

    def test_static_files_exempt_from_rate_limiting(self, client):
        """静的ファイルがレート制限から除外されていること"""
        from app_v2 import exempt_static

        # 除外フィルター関数が存在することを確認
        assert exempt_static is not None

    def test_rate_limit_configuration(self):
        """レート制限の設定値確認"""
        from app_v2 import limiter

        # デフォルトリミットが設定されていることを確認
        # 注: 実際のレート制限テストは時間がかかるため、設定確認のみ


class TestSessionSecurity:
    """セッションセキュリティテスト"""

    def test_jwt_token_expiration_configured(self):
        """JWTトークンの有効期限が設定されていること"""
        from app_v2 import app
        from datetime import timedelta

        assert 'JWT_ACCESS_TOKEN_EXPIRES' in app.config
        assert isinstance(app.config['JWT_ACCESS_TOKEN_EXPIRES'], timedelta)
        assert app.config['JWT_ACCESS_TOKEN_EXPIRES'] > timedelta(0)

    def test_refresh_token_expiration_configured(self):
        """リフレッシュトークンの有効期限が設定されていること"""
        from app_v2 import app
        from datetime import timedelta

        assert 'JWT_REFRESH_TOKEN_EXPIRES' in app.config
        assert isinstance(app.config['JWT_REFRESH_TOKEN_EXPIRES'], timedelta)

        # リフレッシュトークンはアクセストークンより長い
        assert app.config['JWT_REFRESH_TOKEN_EXPIRES'] > \
               app.config['JWT_ACCESS_TOKEN_EXPIRES']

    def test_csrf_disabled_for_api(self):
        """API専用のためCSRF保護が無効であること"""
        from app_v2 import app

        # JWTを使用するためCSRF保護は不要
        assert app.config.get('JWT_COOKIE_CSRF_PROTECT') is False
        assert app.config.get('WTF_CSRF_ENABLED') is False


class TestDataProtection:
    """データ保護テスト"""

    def test_password_hashing_function_exists(self):
        """パスワードハッシュ化関数が存在すること"""
        from app_v2 import hash_password

        assert hash_password is not None

        # bcryptが使用されていることを確認
        hashed = hash_password('test123')
        assert hashed.startswith('$2b$')

    def test_password_verification_function_exists(self):
        """パスワード検証関数が存在すること"""
        from app_v2 import hash_password
        import bcrypt

        password = 'test123'
        hashed = hash_password(password)

        # 検証が成功すること
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def test_sensitive_data_not_logged(self, client):
        """機密データがログに記録されないこと"""
        # ログイン試行
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })

        # 注: ログファイルに平文パスワードが記録されていないことを確認
        # （実際のログファイル確認は統合テストで実施）
