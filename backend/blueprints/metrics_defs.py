"""
blueprints/metrics_defs.py - Prometheus メトリクス定義（共有モジュール）

Phase Prometheus: app_v2.py から ~130行のメトリクス定義を分離。
app_v2.py と blueprints/metrics.py の両方がここからインポートする。
テスト環境では NoOp オブジェクトを提供し、重複登録エラーを回避する。
"""

import os

from prometheus_client import Counter as PrometheusCounter
from prometheus_client import Gauge, Histogram, REGISTRY


class _NoOpMetric:
    """テスト環境用 NoOp メトリクス（収集処理をスキップ）"""

    def inc(self, *args, **kwargs):
        pass

    def set(self, *args, **kwargs):
        pass

    def observe(self, *args, **kwargs):
        pass

    def labels(self, **kwargs):
        return self


def _clear_registry():
    """Prometheusレジストリをクリア（重複登録エラー回避）"""
    try:
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass
    except Exception:
        pass


_noop = _NoOpMetric()

if os.environ.get("TESTING") == "true":
    # ---- テスト環境: NoOp オブジェクト ----
    REQUEST_COUNT = _noop
    REQUEST_DURATION = _noop
    ERROR_COUNT = _noop
    API_CALLS = _noop
    DB_CONNECTIONS = _noop
    DB_QUERY_DURATION = _noop
    ACTIVE_USERS = _noop
    KNOWLEDGE_TOTAL = _noop
    SYSTEM_CPU_USAGE = _noop
    SYSTEM_MEMORY_USAGE = _noop
    SYSTEM_DISK_USAGE = _noop
    AUTH_ATTEMPTS = _noop
    RATE_LIMIT_HITS = _noop
    MS365_SYNC_EXECUTIONS = _noop
    MS365_SYNC_DURATION = _noop
    MS365_FILES_PROCESSED = _noop
    MS365_SYNC_ERRORS = _noop
else:
    # ---- 本番/開発環境: Prometheus メトリクス登録 ----
    _clear_registry()

    REQUEST_COUNT = PrometheusCounter(
        "mks_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )

    REQUEST_DURATION = Histogram(
        "mks_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "endpoint"],
    )

    ERROR_COUNT = PrometheusCounter(
        "mks_errors_total", "Total errors", ["type", "endpoint"]
    )

    API_CALLS = PrometheusCounter(
        "mks_api_calls_total", "Total API calls", ["endpoint", "method"]
    )

    DB_CONNECTIONS = Gauge("mks_database_connections", "Number of database connections")

    DB_QUERY_DURATION = Histogram(
        "mks_database_query_duration_seconds", "Database query duration", ["operation"]
    )

    ACTIVE_USERS = Gauge("mks_active_users", "Number of active users")

    KNOWLEDGE_TOTAL = Gauge("mks_knowledge_total", "Total number of knowledge entries")

    SYSTEM_CPU_USAGE = Gauge(
        "mks_system_cpu_usage_percent", "System CPU usage percentage"
    )

    SYSTEM_MEMORY_USAGE = Gauge(
        "mks_system_memory_usage_percent", "System memory usage percentage"
    )

    SYSTEM_DISK_USAGE = Gauge(
        "mks_system_disk_usage_percent", "System disk usage percentage"
    )

    AUTH_ATTEMPTS = PrometheusCounter(
        "mks_auth_attempts_total", "Total authentication attempts", ["status"]
    )

    RATE_LIMIT_HITS = PrometheusCounter(
        "mks_rate_limit_hits_total", "Total rate limit hits", ["endpoint"]
    )

    MS365_SYNC_EXECUTIONS = PrometheusCounter(
        "mks_ms365_sync_executions_total",
        "Total MS365 sync executions",
        ["config_id", "status"],
    )

    MS365_SYNC_DURATION = Histogram(
        "mks_ms365_sync_duration_seconds",
        "MS365 sync execution duration in seconds",
        ["config_id"],
    )

    MS365_FILES_PROCESSED = PrometheusCounter(
        "mks_ms365_files_processed_total",
        "Total files processed from MS365",
        ["config_id", "result"],  # result: created/updated/skipped/failed
    )

    MS365_SYNC_ERRORS = PrometheusCounter(
        "mks_ms365_sync_errors_total",
        "Total MS365 sync errors",
        ["config_id", "error_type"],
    )
