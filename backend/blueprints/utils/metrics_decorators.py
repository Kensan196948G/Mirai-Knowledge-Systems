"""
blueprints/utils/metrics_decorators.py - メトリクスデコレータ

Phase M-1: app_v2.py から抽出
"""

import time
from functools import wraps

from blueprints.metrics_defs import DB_QUERY_DURATION, ERROR_COUNT


def track_db_query(operation):
    """
    データベースクエリのメトリクスを記録するデコレータ

    使用例:
        @track_db_query('select')
        def load_knowledges():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
                return result
            except Exception:
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(operation=operation).observe(duration)
                ERROR_COUNT.labels(type="db_error", endpoint=operation).inc()
                raise

        return wrapper

    return decorator
