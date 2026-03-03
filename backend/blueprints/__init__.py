"""
Flask Blueprints パッケージ
Phase G-3-1: Blueprint分割の基盤
Phase H-1: auth_bp / knowledge_bp は app_v2.py から直接インポート
           init_limiter() 呼び出し後にインポートすることで
           @get_limiter().limit() デコレータの初期化順序問題を回避
"""
# auth_bp, knowledge_bp は app_v2.py 側で個別にインポートする
# from .auth import auth_bp      # app_v2.py で import
# from .knowledge import knowledge_bp  # app_v2.py で import

__all__ = ['auth_bp', 'knowledge_bp']
