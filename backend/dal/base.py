"""
BaseDAL - インフラストラクチャ基盤
JSON/PostgreSQL切り替えの基底クラス
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from config import Config

logger = logging.getLogger(__name__)


class BaseDAL:
    """データアクセス基底クラス（インフラ層）"""

    def __init__(self, use_postgresql=None):
        """
        初期化

        Args:
            use_postgresql: PostgreSQLを使用するかどうか（Noneの場合は環境変数から取得）
        """
        if use_postgresql is None:
            use_postgresql = Config.USE_POSTGRESQL
        self.use_postgresql = use_postgresql
        self.data_dir = Config.DATA_DIR

    def _use_postgresql(self) -> bool:
        """PostgreSQL使用可否を判定（利用不可ならJSONにフォールバック）"""
        if not self.use_postgresql:
            return False
        try:
            from database import config as db_config
        except Exception:
            return False
        return db_config.is_postgres_available()

    def _get_json_path(self, filename):
        """JSONファイルのパスを取得"""
        return os.path.join(self.data_dir, filename)

    def _load_json(self, filename):
        """JSONファイルからデータを読み込み"""
        filepath = self._get_json_path(filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        return []
                    return [item for item in data if isinstance(item, dict)]
            except (json.JSONDecodeError, ValueError):
                return []
        return []

    def _save_json(self, filename, data):
        """JSONファイルにデータを保存"""
        filepath = self._get_json_path(filename)
        dirpath = os.path.dirname(filepath)
        os.makedirs(dirpath, exist_ok=True)

        import tempfile

        fd, tmp_path = tempfile.mkstemp(
            prefix=f".{filename}.", suffix=".tmp", dir=dirpath
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, filepath)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
