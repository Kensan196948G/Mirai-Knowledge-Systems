"""
blueprints/metrics_defs.py カバレッジ強化テスト

対象の未カバー行:
  Lines 19,22,25,28  - _NoOpMetric メソッド (inc, set, observe, labels)
  Lines 38-41        - _clear_registry() 本体
  Lines 48-64        - TESTING=true 時の NoOp メトリクス定義

テスト方針:
  - TESTING=true 環境で実行される前提（CI環境と同じ）
  - _NoOpMetric を直接インスタンス化してメソッドを検証
  - _clear_registry() の呼び出しが例外を発生させないことを確認
  - モジュールエクスポート名とインスタンス型を検証
"""

import importlib
import os
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)

# TESTING=true が設定されている前提でインポート
os.environ.setdefault("TESTING", "true")

# blueprints パッケージ経由でインポート
sys.path.insert(0, os.path.join(BACKEND_DIR, "blueprints"))
from blueprints.metrics_defs import (
    _NoOpMetric,
    _clear_registry,
    REQUEST_COUNT,
    REQUEST_DURATION,
    ERROR_COUNT,
    API_CALLS,
    DB_CONNECTIONS,
    DB_QUERY_DURATION,
    ACTIVE_USERS,
    KNOWLEDGE_TOTAL,
    SYSTEM_CPU_USAGE,
    SYSTEM_MEMORY_USAGE,
    SYSTEM_DISK_USAGE,
    AUTH_ATTEMPTS,
    RATE_LIMIT_HITS,
    MS365_SYNC_EXECUTIONS,
    MS365_SYNC_DURATION,
    MS365_FILES_PROCESSED,
    MS365_SYNC_ERRORS,
)


# ============================================================
# テストクラス 1: _NoOpMetric メソッドのカバレッジ
# ============================================================


class TestNoOpMetricMethods:
    """_NoOpMetric の各メソッドが正常に動作することを検証"""

    def setup_method(self):
        """各テスト前に新しいインスタンスを作成"""
        self.metric = _NoOpMetric()

    def test_inc_no_args(self):
        """inc() 引数なしで呼び出して例外が発生しないことを確認"""
        result = self.metric.inc()
        assert result is None

    def test_inc_with_positional_args(self):
        """inc() 位置引数ありで呼び出して例外が発生しないことを確認"""
        result = self.metric.inc(1)
        assert result is None

    def test_inc_with_keyword_args(self):
        """inc() キーワード引数ありで呼び出して例外が発生しないことを確認"""
        result = self.metric.inc(amount=5)
        assert result is None

    def test_inc_with_mixed_args(self):
        """inc() 位置引数とキーワード引数の混在で呼び出して例外が発生しないことを確認"""
        result = self.metric.inc(2, step=1)
        assert result is None

    def test_set_no_args(self):
        """set() 引数なしで呼び出して例外が発生しないことを確認"""
        result = self.metric.set()
        assert result is None

    def test_set_with_value(self):
        """set() 数値引数ありで呼び出して例外が発生しないことを確認"""
        result = self.metric.set(42.0)
        assert result is None

    def test_set_with_keyword_args(self):
        """set() キーワード引数ありで呼び出して例外が発生しないことを確認"""
        result = self.metric.set(value=100)
        assert result is None

    def test_observe_no_args(self):
        """observe() 引数なしで呼び出して例外が発生しないことを確認"""
        result = self.metric.observe()
        assert result is None

    def test_observe_with_value(self):
        """observe() 数値引数ありで呼び出して例外が発生しないことを確認"""
        result = self.metric.observe(0.123)
        assert result is None

    def test_observe_with_keyword_args(self):
        """observe() キーワード引数ありで呼び出して例外が発生しないことを確認"""
        result = self.metric.observe(amount=0.5)
        assert result is None

    def test_labels_returns_self(self):
        """labels() が self を返すことを確認"""
        returned = self.metric.labels(method="GET")
        assert returned is self.metric

    def test_labels_multiple_kwargs(self):
        """labels() 複数キーワード引数で self を返すことを確認"""
        returned = self.metric.labels(method="POST", endpoint="/api/test", status="200")
        assert returned is self.metric

    def test_labels_no_kwargs(self):
        """labels() 引数なしで self を返すことを確認"""
        returned = self.metric.labels()
        assert returned is self.metric

    def test_chaining_labels_then_inc(self):
        """labels().inc() のチェーン呼び出しが例外を発生させないことを確認"""
        # 最もよく使われるパターン
        self.metric.labels(method="GET").inc()

    def test_chaining_labels_then_inc_with_amount(self):
        """labels().inc(amount) のチェーン呼び出しが例外を発生させないことを確認"""
        self.metric.labels(endpoint="/api/test").inc(1)

    def test_chaining_labels_then_set(self):
        """labels().set() のチェーン呼び出しが例外を発生させないことを確認"""
        self.metric.labels(operation="query").set(0.001)

    def test_chaining_labels_then_observe(self):
        """labels().observe() のチェーン呼び出しが例外を発生させないことを確認"""
        self.metric.labels(config_id="1").observe(1.23)

    def test_chaining_labels_multiple_times(self):
        """labels().labels() のチェーン呼び出しが例外を発生させないことを確認"""
        result = self.metric.labels(method="GET").labels(status="200")
        # labels() は self を返すため、チェーンが継続できる
        assert result is not None

    def test_multiple_method_calls_on_same_instance(self):
        """同一インスタンスで複数回メソッドを呼び出しても例外が発生しないことを確認"""
        self.metric.inc()
        self.metric.inc(5)
        self.metric.set(10)
        self.metric.observe(0.1)
        self.metric.labels(x="y").inc()


# ============================================================
# テストクラス 2: _clear_registry() のカバレッジ
# ============================================================


class TestClearRegistry:
    """_clear_registry() が正常に動作することを検証"""

    def test_clear_registry_does_not_raise(self):
        """_clear_registry() が例外を発生させないことを確認"""
        _clear_registry()

    def test_clear_registry_called_twice(self):
        """_clear_registry() を2回呼び出しても例外が発生しないことを確認"""
        _clear_registry()
        _clear_registry()

    def test_clear_registry_returns_none(self):
        """_clear_registry() が None を返すことを確認"""
        result = _clear_registry()
        assert result is None

    def test_clear_registry_handles_attribute_error(self):
        """_clear_registry() が AttributeError を内部処理することを確認

        prometheus_client の REGISTRY を別オブジェクトに差し替えて
        _collector_to_names アクセス時に AttributeError が発生するシナリオをテスト。
        外部に例外が伝播しないことを確認する。
        """
        import unittest.mock as mock
        import blueprints.metrics_defs as mdef

        # REGISTRY を AttributeError を発生させるモックに差し替え
        bad_registry = mock.MagicMock()
        bad_registry._collector_to_names = mock.PropertyMock(
            side_effect=AttributeError("mocked registry error")
        )
        # type(bad_registry)._collector_to_names をプロパティとして設定
        type(bad_registry)._collector_to_names = mock.PropertyMock(
            side_effect=AttributeError("mocked registry error")
        )

        original_registry = mdef.REGISTRY if hasattr(mdef, "REGISTRY") else None
        try:
            # モジュールレベルの REGISTRY を差し替え
            import blueprints.metrics_defs
            orig = blueprints.metrics_defs.__dict__.get("REGISTRY")
            blueprints.metrics_defs.__dict__["REGISTRY"] = bad_registry

            # 例外が外部に漏れないこと
            try:
                _clear_registry()
            except Exception as e:
                pytest.fail(f"_clear_registry() が例外を外部に伝播させました: {e}")
        finally:
            if orig is not None:
                blueprints.metrics_defs.__dict__["REGISTRY"] = orig


# ============================================================
# テストクラス 3: TESTING=true 時のメトリクスエクスポート
# ============================================================


_IS_NOOP = isinstance(REQUEST_COUNT, _NoOpMetric)


@pytest.mark.skipif(not _IS_NOOP, reason="TESTING!=true at import — metrics are real Prometheus objects")
class TestTestingModeMetrics:
    """TESTING=true の場合、すべてのメトリクスが _NoOpMetric であることを検証"""

    def test_testing_env_was_set(self):
        """メトリクスが NoOp モードであることを確認"""
        assert _IS_NOOP

    def test_request_count_is_noop(self):
        assert isinstance(REQUEST_COUNT, _NoOpMetric)

    def test_request_duration_is_noop(self):
        assert isinstance(REQUEST_DURATION, _NoOpMetric)

    def test_error_count_is_noop(self):
        assert isinstance(ERROR_COUNT, _NoOpMetric)

    def test_api_calls_is_noop(self):
        assert isinstance(API_CALLS, _NoOpMetric)

    def test_db_connections_is_noop(self):
        assert isinstance(DB_CONNECTIONS, _NoOpMetric)

    def test_db_query_duration_is_noop(self):
        assert isinstance(DB_QUERY_DURATION, _NoOpMetric)

    def test_active_users_is_noop(self):
        assert isinstance(ACTIVE_USERS, _NoOpMetric)

    def test_knowledge_total_is_noop(self):
        assert isinstance(KNOWLEDGE_TOTAL, _NoOpMetric)

    def test_system_cpu_usage_is_noop(self):
        assert isinstance(SYSTEM_CPU_USAGE, _NoOpMetric)

    def test_system_memory_usage_is_noop(self):
        assert isinstance(SYSTEM_MEMORY_USAGE, _NoOpMetric)

    def test_system_disk_usage_is_noop(self):
        assert isinstance(SYSTEM_DISK_USAGE, _NoOpMetric)

    def test_auth_attempts_is_noop(self):
        assert isinstance(AUTH_ATTEMPTS, _NoOpMetric)

    def test_rate_limit_hits_is_noop(self):
        assert isinstance(RATE_LIMIT_HITS, _NoOpMetric)

    def test_ms365_sync_executions_is_noop(self):
        assert isinstance(MS365_SYNC_EXECUTIONS, _NoOpMetric)

    def test_ms365_sync_duration_is_noop(self):
        assert isinstance(MS365_SYNC_DURATION, _NoOpMetric)

    def test_ms365_files_processed_is_noop(self):
        assert isinstance(MS365_FILES_PROCESSED, _NoOpMetric)

    def test_ms365_sync_errors_is_noop(self):
        assert isinstance(MS365_SYNC_ERRORS, _NoOpMetric)


# ============================================================
# テストクラス 4: 実際のメトリクス利用パターン
# ============================================================


class TestMetricsUsagePatterns:
    """実際のアプリケーションコードが使うパターンの検証"""

    def test_request_count_labels_inc_pattern(self):
        """HTTP リクエストカウントの典型的な使用パターン"""
        REQUEST_COUNT.labels(method="GET", endpoint="/api/health", status="200").inc()

    def test_request_duration_labels_observe_pattern(self):
        """HTTP レイテンシ計測の典型的な使用パターン"""
        REQUEST_DURATION.labels(method="GET", endpoint="/api/health").observe(0.05)

    def test_error_count_labels_inc_pattern(self):
        """エラーカウントの典型的な使用パターン"""
        ERROR_COUNT.labels(type="ValueError", endpoint="/api/knowledge").inc()

    def test_db_connections_set_pattern(self):
        """DBコネクション数設定の典型的な使用パターン"""
        DB_CONNECTIONS.set(5)

    def test_active_users_inc_pattern(self):
        """アクティブユーザー数インクリメントの典型的な使用パターン"""
        ACTIVE_USERS.inc()

    def test_knowledge_total_set_pattern(self):
        """ナレッジ総数設定の典型的な使用パターン"""
        KNOWLEDGE_TOTAL.set(42)

    def test_auth_attempts_labels_inc_pattern(self):
        """認証試行カウントの典型的な使用パターン"""
        AUTH_ATTEMPTS.labels(status="success").inc()
        AUTH_ATTEMPTS.labels(status="failed").inc()

    def test_ms365_sync_executions_labels_inc_pattern(self):
        """MS365同期実行カウントの典型的な使用パターン"""
        MS365_SYNC_EXECUTIONS.labels(config_id="1", status="success").inc()

    def test_ms365_sync_duration_observe_pattern(self):
        """MS365同期時間計測の典型的な使用パターン"""
        MS365_SYNC_DURATION.labels(config_id="1").observe(3.5)

    def test_ms365_files_processed_labels_inc_pattern(self):
        """MS365ファイル処理カウントの典型的な使用パターン"""
        MS365_FILES_PROCESSED.labels(config_id="1", result="created").inc()
        MS365_FILES_PROCESSED.labels(config_id="1", result="skipped").inc()

    def test_ms365_sync_errors_labels_inc_pattern(self):
        """MS365同期エラーカウントの典型的な使用パターン"""
        MS365_SYNC_ERRORS.labels(config_id="1", error_type="ConnectionError").inc()

    def test_all_metrics_are_not_none(self):
        """すべてのメトリクスが None でないことを確認"""
        metrics = [
            REQUEST_COUNT, REQUEST_DURATION, ERROR_COUNT, API_CALLS,
            DB_CONNECTIONS, DB_QUERY_DURATION, ACTIVE_USERS, KNOWLEDGE_TOTAL,
            SYSTEM_CPU_USAGE, SYSTEM_MEMORY_USAGE, SYSTEM_DISK_USAGE,
            AUTH_ATTEMPTS, RATE_LIMIT_HITS, MS365_SYNC_EXECUTIONS,
            MS365_SYNC_DURATION, MS365_FILES_PROCESSED, MS365_SYNC_ERRORS,
        ]
        for metric in metrics:
            assert metric is not None

    @pytest.mark.skipif(not _IS_NOOP, reason="TESTING!=true at import — metrics are real Prometheus objects")
    def test_all_noop_metrics_are_same_instance(self):
        """TESTING=true の場合、すべてのメトリクスが同一の _noop インスタンスを参照することを確認"""
        from blueprints.metrics_defs import _noop
        metrics = [
            REQUEST_COUNT, REQUEST_DURATION, ERROR_COUNT, API_CALLS,
            DB_CONNECTIONS, DB_QUERY_DURATION, ACTIVE_USERS, KNOWLEDGE_TOTAL,
            SYSTEM_CPU_USAGE, SYSTEM_MEMORY_USAGE, SYSTEM_DISK_USAGE,
            AUTH_ATTEMPTS, RATE_LIMIT_HITS, MS365_SYNC_EXECUTIONS,
            MS365_SYNC_DURATION, MS365_FILES_PROCESSED, MS365_SYNC_ERRORS,
        ]
        for metric in metrics:
            assert metric is _noop
