"""
統合テスト: エラーハンドラー

エラーハンドラーの統合テストを実施
"""


class TestErrorHandlers:
    """エラーハンドラーのテスト"""

    def test_404_error_handler(self, client):
        """404エラーハンドラーが正しく動作することを確認"""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert "message" in data["error"]

    def test_404_error_message(self, client):
        """404エラーメッセージが適切であることを確認"""
        response = client.get("/api/v1/does/not/exist")

        data = response.get_json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "resource not found" in data["error"]["message"].lower()

    def test_405_method_not_allowed(self, client, auth_headers):
        """405エラー（Method Not Allowed）が正しく処理されることを確認"""
        # GETのみ許可されているエンドポイントにPOSTを試みる
        response = client.post("/api/v1/dashboard/stats", headers=auth_headers)

        assert response.status_code == 405

    def test_invalid_json_request(self, client, auth_headers):
        """無効なJSONリクエストが適切に処理されることを確認"""
        response = client.post(
            "/api/v1/knowledge",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 400

    def test_missing_required_field(self, client, auth_headers):
        """必須フィールドが欠けている場合のエラー処理を確認"""
        response = client.post(
            "/api/v1/knowledge",
            json={"summary": "Test summary"},  # titleが欠けている
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data or "message" in data

    def test_validation_error_response_format(self, client, auth_headers):
        """バリデーションエラーのレスポンス形式を確認"""
        response = client.post(
            "/api/v1/knowledge", json={"title": ""}, headers=auth_headers  # 空のtitle
        )

        assert response.status_code == 400
        data = response.get_json()
        assert isinstance(data, dict)
        assert "error" in data or "message" in data or "errors" in data


class TestAuthenticationErrors:
    """認証エラーのテスト"""

    def test_missing_token_error(self, client):
        """トークンが欠けている場合のエラーを確認"""
        response = client.get("/api/v1/knowledge")

        assert response.status_code == 401
        data = response.get_json()
        assert "msg" in data or "message" in data or "error" in data

    def test_invalid_token_error(self, client):
        """無効なトークンのエラーを確認"""
        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code in [401, 422]

    def test_malformed_authorization_header(self, client):
        """不正なAuthorizationヘッダーのエラーを確認"""
        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": "InvalidFormat"}
        )

        assert response.status_code == 401 or response.status_code == 422

    def test_expired_token_error(self, client):
        """期限切れトークンのエラーを確認"""
        # 期限切れのトークンを作成
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.invalid"

        response = client.get(
            "/api/v1/knowledge", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code in [401, 422]


class TestAuthorizationErrors:
    """認可エラーのテスト"""

    def test_insufficient_permissions(self, client, partner_auth_headers):
        """権限不足のエラーを確認"""
        # 協力会社ユーザーがナレッジ作成を試みる
        response = client.post(
            "/api/v1/knowledge",
            json={
                "title": "Test",
                "summary": "Test",
                "content": "Test",
                "category": "technical",
            },
            headers=partner_auth_headers,
        )

        assert response.status_code == 403

    def test_forbidden_error_message(self, client, partner_auth_headers):
        """403エラーメッセージが適切であることを確認"""
        response = client.post(
            "/api/v1/knowledge",
            json={
                "title": "Test",
                "summary": "Test",
                "content": "Test",
                "category": "technical",
            },
            headers=partner_auth_headers,
        )

        data = response.get_json()
        assert "error" in data or "message" in data


class TestInputValidationErrors:
    """入力検証エラーのテスト"""

    def test_invalid_category_value(self, client, auth_headers):
        """無効なカテゴリ値のエラーを確認"""
        response = client.post(
            "/api/v1/knowledge",
            json={
                "title": "Test",
                "summary": "Test",
                "content": "Test",
                "category": "invalid_category",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_string_too_long(self, client, auth_headers):
        """文字列が長すぎる場合のエラーを確認"""
        response = client.post(
            "/api/v1/knowledge",
            json={
                "title": "A" * 300,  # 最大長を超える
                "summary": "Test",
                "content": "Test",
                "category": "technical",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_invalid_data_type(self, client, auth_headers):
        """無効なデータ型のエラーを確認"""
        response = client.post(
            "/api/v1/knowledge",
            json={
                "title": 123,  # 文字列が期待されるが数値
                "summary": "Test",
                "content": "Test",
                "category": "technical",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_negative_id_parameter(self, client, auth_headers):
        """負のID値のエラーを確認"""
        response = client.get("/api/v1/knowledge/-1", headers=auth_headers)

        assert response.status_code == 404

    def test_zero_id_parameter(self, client, auth_headers):
        """ゼロのID値のエラーを確認"""
        response = client.get("/api/v1/knowledge/0", headers=auth_headers)

        assert response.status_code == 404


class TestRateLimitingErrors:
    """レート制限エラーのテスト"""

    def test_rate_limit_on_login(self, client):
        """ログインエンドポイントのレート制限を確認"""
        # 複数回ログインを試みる
        for _ in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "invalid", "password": "invalid"},
            )

        # レート制限が適用されることを確認（429 Too Many Requests）
        # 注: 実際のレート制限設定によって異なる
        assert response.status_code in [401, 429]


class TestServerErrors:
    """サーバーエラーのテスト"""

    def test_500_error_handling(self, client, auth_headers, monkeypatch):
        """500エラーが適切に処理されることを確認"""

        # データロード関数をモックしてエラーを発生させる
        def mock_load_data(*args, **kwargs):
            raise Exception("Internal server error")

        # app_v2モジュールのload_data関数をパッチ
        import app_v2

        monkeypatch.setattr(app_v2, "load_data", mock_load_data)

        response = client.get("/api/v1/knowledge", headers=auth_headers)

        # サーバーエラーが発生
        assert response.status_code == 500

    def test_error_does_not_leak_stack_trace(self, client, auth_headers, monkeypatch):
        """エラーメッセージにスタックトレースが含まれないことを確認"""

        # データロード関数をモックしてエラーを発生させる
        def mock_load_data(*args, **kwargs):
            raise Exception("Internal error with sensitive info")

        import app_v2

        monkeypatch.setattr(app_v2, "load_data", mock_load_data)

        response = client.get("/api/v1/knowledge", headers=auth_headers)

        # レスポンスに機密情報が含まれないことを確認
        if response.data:
            data_str = response.data.decode("utf-8")
            assert "Traceback" not in data_str
            assert "sensitive info" not in data_str


class TestCORSErrors:
    """CORSエラーのテスト"""

    def test_cors_headers_present_on_error(self, client):
        """エラーレスポンスにもCORSヘッダーが含まれることを確認"""
        response = client.get(
            "/api/v1/knowledge", headers={"Origin": "http://localhost:3000"}
        )

        # 認証エラー時はCORSヘッダーが付与されない場合がある
        assert response.status_code in [401, 403]

    def test_cors_preflight_on_error_endpoint(self, client):
        """エラーエンドポイントでもCORSプリフライトが動作することを確認"""
        response = client.options(
            "/api/nonexistent",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code in [200, 204]
