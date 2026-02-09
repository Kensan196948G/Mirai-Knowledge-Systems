"""
ヘルスチェックAPIの統合テスト
"""


class TestHealthAPI:
    """ヘルスチェックAPIのテスト"""

    def test_health_check_endpoint(self, client):
        """ヘルスチェックエンドポイントが正常に動作する"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert "timestamp" in data
        assert "database" in data
        assert "system" in data
        assert data["status"] in ("healthy", "degraded")

    def test_health_check_system_metrics(self, client):
        """システムメトリクスが含まれる"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.get_json()
        system = data.get("system", {})
        assert "cpu_percent" in system
        assert "memory_percent" in system
        assert "disk_percent" in system

    def test_health_check_database_info(self, client):
        """データベース情報が含まれる"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.get_json()
        database = data.get("database", {})
        assert "mode" in database
        assert "healthy" in database

    def test_db_health_endpoint(self, client):
        """データベース専用ヘルスチェックエンドポイント"""
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200
        data = response.get_json()
        assert "healthy" in data
        assert "mode" in data
        assert "timestamp" in data

    def test_health_storage_mode(self, client):
        """ストレージモードが正しく返される"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "storage_mode" in data
        assert data["storage_mode"] in ("json", "postgresql", "json_fallback")

    def test_health_version_info(self, client):
        """バージョン情報が含まれる"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "version" in data
        assert "environment" in data
