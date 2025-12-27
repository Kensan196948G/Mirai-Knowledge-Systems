"""
建設土木ナレッジシステム - 設定パッケージ

使用方法:
    from config.production import get_config
    config = get_config()
"""

from .production import get_config, ProductionConfig, DevelopmentConfig, TestingConfig

__all__ = ['get_config', 'ProductionConfig', 'DevelopmentConfig', 'TestingConfig']
