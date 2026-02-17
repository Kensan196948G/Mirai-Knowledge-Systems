"""Redisキャッシュレイヤーのテスト

cache_get / cache_set / get_cache_key のユニットテスト、
および /dashboard/stats エンドポイントのキャッシュ統合テスト。
Redis未接続時のフォールバック動作も検証する。
"""

import json
import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

import app_v2


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def client(tmp_path):
    app = app_v2.app
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(tmp_path)
    app.config["JWT_SECRET_KEY"] = "test-secret-key-longer-than-20"
    app_v2.limiter.enabled = False

    users = [
        {
            "id": 1,
            "username": "admin",
            "password_hash": app_v2.hash_password("admin123"),
            "full_name": "Admin User",
            "department": "Admin",
            "roles": ["admin"],
        }
    ]
    _write_json(tmp_path / "users.json", users)
    _write_json(tmp_path / "knowledge.json", [{"id": 1, "title": "Test"}])
    _write_json(tmp_path / "sop.json", [])
    _write_json(tmp_path / "incidents.json", [])
    _write_json(tmp_path / "approvals.json", [{"id": 1, "status": "pending"}])
    _write_json(tmp_path / "access_logs.json", [])
    _write_json(tmp_path / "notifications.json", [])
    _write_json(tmp_path / "favorites.json", [])
    _write_json(tmp_path / "consultations.json", [])

    with app.test_client() as c:
        yield c


def _get_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return resp.get_json()["data"]["access_token"]


# ============================================================
# get_cache_key テスト
# ============================================================


class TestGetCacheKey:
    """キャッシュキー生成のテスト"""

    def test_basic_key(self):
        key = app_v2.get_cache_key("prefix", "a", "b")
        assert key == "prefix:a:b"

    def test_single_arg(self):
        key = app_v2.get_cache_key("search", "query")
        assert key == "search:query"

    def test_no_args(self):
        key = app_v2.get_cache_key("dashboard_stats")
        assert key == "dashboard_stats:"

    def test_numeric_args(self):
        key = app_v2.get_cache_key("page", 1, 10)
        assert key == "page:1:10"

    def test_mixed_args(self):
        key = app_v2.get_cache_key("search", "hello", "knowledge,sop", "true", 1, 10)
        assert key == "search:hello:knowledge,sop:true:1:10"

    def test_deterministic(self):
        """同じ引数は同じキーを生成"""
        key1 = app_v2.get_cache_key("s", "query", "types")
        key2 = app_v2.get_cache_key("s", "query", "types")
        assert key1 == key2

    def test_different_args_different_keys(self):
        """異なる引数は異なるキーを生成"""
        key1 = app_v2.get_cache_key("s", "hello")
        key2 = app_v2.get_cache_key("s", "world")
        assert key1 != key2


# ============================================================
# cache_get / cache_set テスト (Redis不在時)
# ============================================================


class TestCacheDisabled:
    """Redis未接続時のフォールバック"""

    def test_cache_get_returns_none_when_disabled(self):
        """Redis無効時にcache_getはNoneを返す"""
        original = app_v2.CACHE_ENABLED
        try:
            app_v2.CACHE_ENABLED = False
            result = app_v2.cache_get("any_key")
            assert result is None
        finally:
            app_v2.CACHE_ENABLED = original

    def test_cache_set_noop_when_disabled(self):
        """Redis無効時にcache_setはエラーなしで何もしない"""
        original = app_v2.CACHE_ENABLED
        try:
            app_v2.CACHE_ENABLED = False
            # エラーが発生しないことを確認
            app_v2.cache_set("key", {"data": "test"})
        finally:
            app_v2.CACHE_ENABLED = original

    def test_cache_get_returns_none_when_no_client(self):
        """redis_clientがNoneのときNoneを返す"""
        original_client = app_v2.redis_client
        original_enabled = app_v2.CACHE_ENABLED
        try:
            app_v2.redis_client = None
            app_v2.CACHE_ENABLED = True
            result = app_v2.cache_get("key")
            assert result is None
        finally:
            app_v2.redis_client = original_client
            app_v2.CACHE_ENABLED = original_enabled


# ============================================================
# cache_get / cache_set テスト (Redis モック)
# ============================================================


class TestCacheWithMockRedis:
    """Redisモックを使ったキャッシュテスト"""

    def test_cache_roundtrip(self):
        """cache_set → cache_get でデータが復元される"""
        mock_redis = MagicMock()
        store = {}

        def mock_setex(key, ttl, value):
            store[key] = value

        def mock_get(key):
            return store.get(key)

        mock_redis.setex = mock_setex
        mock_redis.get = mock_get

        original_client = app_v2.redis_client
        original_enabled = app_v2.CACHE_ENABLED
        try:
            app_v2.redis_client = mock_redis
            app_v2.CACHE_ENABLED = True

            test_data = {"success": True, "data": {"count": 42}}
            app_v2.cache_set("test_key", test_data, ttl=300)
            result = app_v2.cache_get("test_key")
            assert result == test_data
        finally:
            app_v2.redis_client = original_client
            app_v2.CACHE_ENABLED = original_enabled

    def test_cache_get_handles_exception(self):
        """cache_getがRedis例外をNoneに変換"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Connection lost")

        original_client = app_v2.redis_client
        original_enabled = app_v2.CACHE_ENABLED
        try:
            app_v2.redis_client = mock_redis
            app_v2.CACHE_ENABLED = True
            result = app_v2.cache_get("key")
            assert result is None
        finally:
            app_v2.redis_client = original_client
            app_v2.CACHE_ENABLED = original_enabled

    def test_cache_get_returns_none_for_missing_key(self):
        """存在しないキーはNoneを返す"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        original_client = app_v2.redis_client
        original_enabled = app_v2.CACHE_ENABLED
        try:
            app_v2.redis_client = mock_redis
            app_v2.CACHE_ENABLED = True
            result = app_v2.cache_get("nonexistent")
            assert result is None
        finally:
            app_v2.redis_client = original_client
            app_v2.CACHE_ENABLED = original_enabled


# ============================================================
# /dashboard/stats キャッシュ統合テスト
# ============================================================


class TestDashboardStatsCache:
    """/dashboard/stats のRedisキャッシュ動作テスト"""

    def test_dashboard_stats_returns_success(self, client):
        """キャッシュなし時も正常レスポンスを返す"""
        token = _get_token(client)
        resp = client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "kpis" in data["data"]
        assert "counts" in data["data"]
        assert data["data"]["counts"]["pending_approvals"] == 1

    def test_dashboard_stats_cache_hit(self, client):
        """2回目のリクエストでキャッシュヒット"""
        mock_redis = MagicMock()
        store = {}

        def mock_setex(key, ttl, value):
            store[key] = value

        def mock_get(key):
            return store.get(key)

        mock_redis.setex = mock_setex
        mock_redis.get = mock_get

        original_client = app_v2.redis_client
        original_enabled = app_v2.CACHE_ENABLED
        try:
            app_v2.redis_client = mock_redis
            app_v2.CACHE_ENABLED = True

            token = _get_token(client)
            headers = {"Authorization": f"Bearer {token}"}

            # 1回目: キャッシュミス → JSONファイル読み込み → キャッシュ設定
            resp1 = client.get("/api/v1/dashboard/stats", headers=headers)
            assert resp1.status_code == 200

            # cache_setが呼ばれたことを確認
            assert len(store) > 0

            # 2回目: キャッシュヒット
            resp2 = client.get("/api/v1/dashboard/stats", headers=headers)
            assert resp2.status_code == 200

            # 両方のレスポンスが同じデータ構造を持つ
            data1 = resp1.get_json()
            data2 = resp2.get_json()
            assert data1["data"]["counts"] == data2["data"]["counts"]
        finally:
            app_v2.redis_client = original_client
            app_v2.CACHE_ENABLED = original_enabled
