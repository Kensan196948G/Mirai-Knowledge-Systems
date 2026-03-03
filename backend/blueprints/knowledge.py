"""
ナレッジ管理APIエンドポイント - Blueprint版
Phase G-3-1: app_v2.py knowledge エンドポイント分割準備
Phase G-3-3: Blueprint移行デモ - /api/v1/ping エンドポイント追加
"""
import os
from datetime import datetime

from flask import Blueprint, jsonify

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/v1')


# ============================================================
# Phase G-3-3: Blueprint移行デモ用エンドポイント
# /api/v1/ping - シンプルな死活確認エンドポイント
# app_v2.py の /api/v1/health とは別 URL のため競合なし
# ============================================================

@knowledge_bp.route('/ping', methods=['GET'])
def ping():
    """
    Blueprint移行デモ用 Ping エンドポイント

    Phase G-3-3 で追加。Blueprint ルーティングが正常に動作することを実証する。
    既存の /api/v1/health エンドポイント（app_v2.py 管理）とは独立して動作する。

    Returns:
        JSON: {"status": "ok", "source": "blueprint", "timestamp": ...}
    """
    return jsonify({
        "status": "ok",
        "source": "knowledge_blueprint",
        "blueprint_name": knowledge_bp.name,
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("MKS_ENV", "development"),
        "phase": "G-3-3",
    }), 200


# Phase G-3-2 以降で段階的にエンドポイントを移行予定
