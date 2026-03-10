"""
データアクセスレイヤー（互換性ファサード）
実装は backend/dal/ パッケージに移行済み

使用方法（既存コードは変更不要）:
    from data_access import DataAccessLayer
    dal = DataAccessLayer()
"""

from dal import DataAccessLayer

__all__ = ["DataAccessLayer"]

# グローバルインスタンス（既存コードとの互換性維持）
dal = DataAccessLayer()
