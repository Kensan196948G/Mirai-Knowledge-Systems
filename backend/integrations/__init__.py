# -*- coding: utf-8 -*-
"""
Mirai Knowledge System - 外部連携モジュール

このパッケージは外部サービスとの連携機能を提供します：
- Microsoft Graph API（SharePoint, OneDrive, Teams等）
- CSV/Excelインポート
- サーバー直接接続
"""

from .data_import import DataImporter
from .microsoft_graph import MicrosoftGraphClient

__all__ = ["MicrosoftGraphClient", "DataImporter"]
