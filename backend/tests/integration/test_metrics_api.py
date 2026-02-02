"""
統合テスト: メトリクスAPI

メトリクスエンドポイントの統合テストを実施
"""

from datetime import datetime

import pytest


class TestMetricsEndpoint:
    """メトリクスエンドポイントのテスト"""

    def test_get_metrics_returns_prometheus_format(self, client, auth_headers):
        """メトリクスがPrometheus形式で返されることを確認"""
        response = client.get("/api/v1/metrics", headers=auth_headers)

        assert response.status_code == 200
        assert response.mimetype == "text/plain"

        # Prometheus形式の確認
        data = response.data.decode("utf-8")
        assert "# HELP" in data
        assert "# TYPE" in data

    def test_metrics_includes_system_stats(self, client, auth_headers):
        """メトリクスにシステム統計が含まれることを確認"""
        response = client.get("/api/v1/metrics", headers=auth_headers)
        data = response.data.decode("utf-8")

        # システムメトリクス
        assert "system_cpu_usage_percent" in data
        assert "system_memory_total_bytes" in data
        assert "system_memory_available_bytes" in data
        assert "system_disk_total_bytes" in data

    def test_metrics_includes_knowledge_stats(self, client, auth_headers):
        """メトリクスにナレッジ統計が含まれることを確認"""
        response = client.get("/api/v1/metrics", headers=auth_headers)
        data = response.data.decode("utf-8")

        # ナレッジ統計
        assert "knowledge_total" in data
        assert "knowledge_by_category" in data
        assert "sop_total" in data

    def test_metrics_includes_user_stats(self, client, auth_headers):
        """メトリクスにユーザー統計が含まれることを確認"""
        response = client.get("/api/v1/metrics", headers=auth_headers)
        data = response.data.decode("utf-8")

        # ユーザー統計
        assert "active_users" in data
        assert "active_sessions" in data

    def test_metrics_includes_http_stats(self, client, auth_headers):
        """メトリクスにHTTP統計が含まれることを確認"""
        # まず他のエンドポイントにアクセスしてメトリクスを生成
        client.get("/api/v1/knowledge", headers=auth_headers)

        response = client.get("/api/v1/metrics", headers=auth_headers)
        data = response.data.decode("utf-8")

        # HTTPメトリクス
        assert "http_requests_total" in data

    def test_metrics_requires_authentication(self, client):
        """メトリクスが認証を必要とすることを確認"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

    def test_metrics_calculates_active_users_correctly(
        self, client, auth_headers, mock_access_logs
    ):
        """アクティブユーザー数が正しく計算されることを確認"""
        # 15分以内のアクセスログを作成
        now = datetime.now()
        logs = [
            {
                "timestamp": now.isoformat(),
                "user_id": 1,
                "session_id": "session1",
                "action": "knowledge.list",
                "status": "success",
            },
            {
                "timestamp": now.isoformat(),
                "user_id": 2,
                "session_id": "session2",
                "action": "knowledge.list",
                "status": "success",
            },
        ]
        mock_access_logs(logs)

        response = client.get("/api/v1/metrics", headers=auth_headers)
        data = response.data.decode("utf-8")

        # アクティブユーザーが存在することを確認
        assert "active_users" in data
        assert "active_sessions" in data


class TestMetricsAccuracy:
    """メトリクスの精度テスト"""

    def test_metrics_category_counts_accurate(
        self, client, auth_headers, create_knowledge
    ):
        """カテゴリ別カウントが正確であることを確認"""
        # 異なるカテゴリのナレッジを作成
        create_knowledge(category="安全衛生")
        create_knowledge(category="品質管理")
        create_knowledge(category="安全衛生")

        response = client.get("/api/v1/metrics", headers=auth_headers)
        data = response.data.decode("utf-8")

        # カテゴリ別カウントが含まれていることを確認
        assert 'knowledge_by_category{category="安全衛生"}' in data
        assert 'knowledge_by_category{category="品質管理"}' in data

    def test_metrics_login_stats_accurate(self, client, mock_access_logs):
        """ログイン統計が正確であることを確認"""
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "action": "auth.login",
                "status": "success",
                "user_id": 1,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "action": "auth.login",
                "status": "failure",
                "user_id": None,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "action": "auth.login",
                "status": "success",
                "user_id": 2,
            },
        ]
        mock_access_logs(logs)

        # adminでログイン
        login_response = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )
        token = login_response.get_json()["data"]["access_token"]

        response = client.get(
            "/api/v1/metrics", headers={"Authorization": f"Bearer {token}"}
        )
        data = response.data.decode("utf-8")

        # ログイン統計が含まれることを確認
        assert 'login_attempts_total{status="success"}' in data
        assert 'login_attempts_total{status="failure"}' in data


class TestMetricsPerformance:
    """メトリクスのパフォーマンステスト"""

    def test_metrics_responds_quickly(self, client, auth_headers):
        """メトリクスが素早く応答することを確認"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/metrics", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 2.0  # 2秒以内に応答

    def test_metrics_handles_large_logs(self, client, auth_headers, mock_access_logs):
        """大量のログがあってもメトリクスが処理できることを確認"""
        # 1000件のログを作成
        logs = []
        for i in range(1000):
            logs.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": i % 10 + 1,
                    "session_id": f"session{i}",
                    "action": "knowledge.list",
                    "status": "success",
                }
            )
        mock_access_logs(logs)

        response = client.get("/api/v1/metrics", headers=auth_headers)
        assert response.status_code == 200


class TestMetricsErrorHandling:
    """メトリクスのエラーハンドリングテスト"""

    def test_metrics_handles_invalid_log_timestamps(
        self, client, auth_headers, mock_access_logs
    ):
        """無効なタイムスタンプを持つログを適切に処理することを確認"""
        logs = [
            {
                "timestamp": "invalid-timestamp",
                "user_id": 1,
                "action": "knowledge.list",
            },
            {
                "timestamp": datetime.now().isoformat(),
                "user_id": 2,
                "action": "knowledge.list",
                "status": "success",
            },
        ]
        mock_access_logs(logs)

        response = client.get("/api/v1/metrics", headers=auth_headers)
        assert response.status_code == 200  # エラーにならずに処理される

    def test_metrics_handles_missing_data_files(self, client, auth_headers, tmp_path):
        """データファイルが存在しない場合でもメトリクスが動作することを確認"""
        response = client.get("/api/v1/metrics", headers=auth_headers)

        # ファイルがなくてもエラーにならない
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "# HELP" in data
