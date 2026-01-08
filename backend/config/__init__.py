"""
建設土木ナレッジシステム - 設定パッケージ

使用方法:
    from config.production import get_config
    config = get_config()

    または（レガシー互換性のため）:
    from config import Config
"""

from .production import get_config, ProductionConfig, DevelopmentConfig, TestingConfig

# レガシー互換性: config.py の Config クラスをインポート
import importlib.util
import os

# config.py を直接読み込む
config_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
if os.path.exists(config_py_path):
    spec = importlib.util.spec_from_file_location("legacy_config", config_py_path)
    if spec and spec.loader:
        legacy_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy_config)
        Config = legacy_config.Config
else:
    # config.pyが存在しない場合はDevelopmentConfigをデフォルトに
    Config = DevelopmentConfig

__all__ = ['get_config', 'ProductionConfig', 'DevelopmentConfig', 'TestingConfig', 'Config']
