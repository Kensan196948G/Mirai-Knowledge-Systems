"""
レート制限ユーティリティ
Blueprint内からlimiterインスタンスを参照するためのモジュール
"""
# limiterはapp_v2.pyで初期化されているため、ここでは参照のみ
# 使用例: from backend.blueprints.utils.rate_limit import get_limiter
#         limiter = get_limiter()

_limiter = None


def init_limiter(limiter_instance):
    """app_v2.pyから limiter インスタンスを登録"""
    global _limiter
    _limiter = limiter_instance


def get_limiter():
    """limiter インスタンスを取得"""
    if _limiter is None:
        raise RuntimeError("Limiter not initialized. Call init_limiter() first.")
    return _limiter
