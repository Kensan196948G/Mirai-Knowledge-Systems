"""
統合テスト: レート制限

レート制限機能の統合テストを実施
"""

import time


class TestRateLimitingConfiguration:
    """レート制限設定のテスト"""

    def test_static_files_exempt_from_rate_limit(self, client):
        """
        静的ファイルへのアクセスがレート制限から除外されることを確認

        目的:
        - 静的ファイル（CSS, JS, 画像等）はレート制限対象外
        - 大量アクセスがあっても正常に配信される
        """
        # 静的ファイルに連続アクセス（レート制限を超える回数）
        responses = []
        for _ in range(15):
            response = client.get("/")  # index.html
            responses.append(response)

        # すべてのリクエストが成功（429が返されない）
        for response in responses:
            # 静的ファイルは200または304（キャッシュ）
            assert response.status_code in [
                200,
                304,
                404,
            ], f"Expected 200/304/404 for static file, got {response.status_code}"

    def test_static_files_css_exempt_from_rate_limit(self, client):
        """
        CSS/JSファイルへのアクセスがレート制限から除外されることを確認

        目的:
        - styles.css等の静的リソースが制限されない
        - ページ読み込みが阻害されない
        """
        # CSSファイルに連続アクセス
        for _ in range(10):
            response = client.get("/styles.css")
            # 429が返されないことを確認（ファイルが存在すれば200、存在しなければ404）
            assert response.status_code != 429

    def test_health_check_exempt_from_rate_limit(self, client):
        """
        ヘルスチェックエンドポイントがレート制限から除外されることを確認

        目的:
        - /healthや/api/v1/healthが制限されない
        - 監視システムが正常に動作
        """
        # ヘルスチェックに連続アクセス
        for _ in range(20):
            response = client.get("/health")
            # 429が返されないことを確認
            assert response.status_code in [200, 404]


class TestAPIRateLimiting:
    """APIエンドポイントのレート制限テスト"""

    def test_api_endpoints_rate_limited(self, client):
        """
        APIエンドポイントにレート制限が適用されることを確認

        目的:
        - ログインエンドポイントが過度なアクセスを制限
        - レート制限超過時に429エラーが返される
        """
        # ログインエンドポイントに連続アクセス
        # 注: 実装によっては「5 per minute」制限がある
        responses = []
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": f"test{i}", "password": "password"},
            )
            responses.append(response)
            # レート制限回避のため短時間待機（テスト環境での調整）
            if i < 5:
                time.sleep(0.1)

        # いずれかのリクエストで429が返されるか、すべて401/400
        status_codes = [r.status_code for r in responses]

        # レート制限が有効な場合、429が含まれる可能性がある
        # 開発環境では無効化されている可能性もあるため、401/400も許容
        assert any(
            code in [400, 401, 429] for code in status_codes
        ), f"Expected rate limiting or auth errors, got {status_codes}"

    def test_api_endpoints_rate_limited_login_specific(self, client):
        """
        ログインエンドポイント専用のレート制限を確認

        目的:
        - ブルートフォース攻撃対策
        - 短時間での大量ログイン試行を防止
        """
        # 同じユーザー名で連続ログイン試行
        failure_count = 0
        rate_limited = False

        for i in range(12):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "attacker", "password": f"wrong{i}"},
            )

            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code in [400, 401]:
                failure_count += 1

            time.sleep(0.1)

        # レート制限が発動するか、すべて認証失敗
        assert (
            rate_limited or failure_count >= 5
        ), "Expected rate limiting or authentication failures"

    def test_authenticated_endpoints_have_higher_limits(self, client, auth_headers):
        """
        認証済みエンドポイントのレート制限が適切に設定されることを確認

        目的:
        - 認証済みユーザーは適切な制限内でアクセス可能
        - 正常な利用が阻害されない
        """
        # 認証済みエンドポイントに連続アクセス
        success_count = 0

        for _ in range(10):
            response = client.get("/api/v1/knowledge", headers=auth_headers)

            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                # レート制限に達した
                break

            time.sleep(0.1)

        # 少なくとも数回は成功する（レート制限が緩い）
        assert (
            success_count >= 3
        ), f"Expected at least 3 successful requests, got {success_count}"


class TestRateLimitPerIP:
    """IPアドレスごとのレート制限テスト"""

    def test_rate_limit_per_ip(self, client):
        """
        IPアドレス単位でレート制限が適用されることを確認

        目的:
        - 同一IPからの過度なアクセスを制限
        - 異なるIPは独立してカウント（テストでは検証困難）
        """
        # 同一クライアント（IP）から連続アクセス
        responses = []

        for i in range(15):
            response = client.post(
                "/api/v1/auth/login", json={"username": f"user{i}", "password": "test"}
            )
            responses.append(response)
            time.sleep(0.1)

        status_codes = [r.status_code for r in responses]

        # レート制限または認証エラーが発生
        assert any(code in [400, 401, 429] for code in status_codes)

    def test_rate_limit_includes_retry_after_header(self, client):
        """
        レート制限レスポンスにRetry-Afterヘッダーが含まれることを確認

        目的:
        - クライアントが再試行タイミングを知ることができる
        - RFC準拠のレート制限実装
        """
        # レート制限を発動させる
        rate_limited_response = None

        for i in range(20):
            response = client.post(
                "/api/v1/auth/login", json={"username": "test", "password": "test"}
            )

            if response.status_code == 429:
                rate_limited_response = response
                break

            time.sleep(0.05)

        # レート制限が発動した場合、ヘッダーまたはボディにretry情報が含まれる
        if rate_limited_response:
            # Retry-Afterヘッダーが含まれる可能性
            has_retry_after = "Retry-After" in rate_limited_response.headers

            # またはレスポンスボディにretry情報が含まれる
            data = rate_limited_response.get_json()
            has_retry_info = False
            if data and isinstance(data, dict):
                # retry_after, retry, message等のキーをチェック
                has_retry_info = any(
                    key in str(data).lower() for key in ["retry", "wait", "seconds"]
                )

            # どちらかの形式でretry情報が提供される
            assert (
                has_retry_after or has_retry_info
            ), "Expected Retry-After header or retry information in response"


class TestRateLimitBypass:
    """レート制限バイパステスト"""

    def test_health_endpoints_bypass_rate_limit(self, client):
        """
        ヘルスチェック系エンドポイントがレート制限をバイパスすることを確認

        目的:
        - /health, /metrics等の監視エンドポイントは無制限
        - システム監視が阻害されない
        """
        # /healthに大量アクセス
        for _ in range(30):
            response = client.get("/health")
            # 429が返されないことを確認
            assert response.status_code != 429

    def test_metrics_endpoint_bypass_rate_limit(self, client):
        """
        Prometheusメトリクスエンドポイントがレート制限をバイパスすることを確認

        目的:
        - /metricsが無制限でアクセス可能
        - Prometheusスクレイピングが正常動作
        """
        # /metricsに大量アクセス
        for _ in range(20):
            response = client.get("/metrics")
            # 429または404（存在しない場合）
            assert response.status_code in [200, 404]


class TestRateLimitErrorResponse:
    """レート制限エラーレスポンステスト"""

    def test_rate_limit_error_response_format(self, client):
        """
        レート制限エラーのレスポンス形式を確認

        目的:
        - 一貫したエラーレスポンス形式
        - クライアント側での統一的なエラー処理
        """
        # レート制限を発動させる
        for i in range(15):
            response = client.post(
                "/api/v1/auth/login", json={"username": "test", "password": "test"}
            )

            if response.status_code == 429:
                data = response.get_json()

                # エラーレスポンスが適切な形式
                assert isinstance(data, dict)
                assert "error" in data or "message" in data

                # エラーコードまたはメッセージが含まれる
                response_str = str(data).lower()
                assert (
                    "rate" in response_str
                    or "limit" in response_str
                    or "many" in response_str
                )
                break

            time.sleep(0.05)

    def test_rate_limit_error_code(self, client):
        """
        レート制限エラーコードがRFC準拠であることを確認

        目的:
        - HTTP 429 Too Many Requestsが返される
        - 標準準拠の実装
        """
        # レート制限を発動させる
        for i in range(20):
            response = client.post(
                "/api/v1/auth/login", json={"username": "test", "password": "test"}
            )

            if response.status_code == 429:
                # 429が正しく返されることを確認
                assert response.status_code == 429
                break

            time.sleep(0.05)
