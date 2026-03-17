"""
blueprints/metrics.py - Prometheus メトリクス Blueprint

Phase K-4: app_v2.py から以下のルートを移行
  GET /metrics             - Prometheus ネイティブスクレイピング用
  GET /api/metrics/summary - 管理者向け JSON メトリクスサマリー
"""

import logging
import time
from collections import Counter

import psutil
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

logger = logging.getLogger(__name__)

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics", methods=["GET"])
def metrics():
    """
    Prometheus ネイティブメトリクスエンドポイント

    Prometheus サーバーがスクレイピングするため認証不要。
    prometheus_client の generate_latest() で出力する。
    """
    try:
        import app_v2 as _app_v2

        _app_v2.update_system_metrics()
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
    except Exception as e:
        logger.error("Metrics endpoint error: %s", e)
        return jsonify({"error": "Failed to generate metrics"}), 500


@metrics_bp.route("/api/metrics/summary", methods=["GET"])
@jwt_required()
def metrics_summary():
    """
    メトリクスサマリー API（管理者用）

    人間が読みやすい JSON 形式でシステムメトリクスを返す。
    """
    try:
        get_jwt_identity()

        import app_v2 as _app_v2
        from app_helpers import load_data

        metrics_storage = _app_v2.metrics_storage

        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        knowledges = load_data("knowledge.json")

        summary = {
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage_percent": disk.percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
            },
            "application": {
                "knowledge_total": len(knowledges),
                "active_sessions": len(
                    metrics_storage.get("active_sessions", set())
                ),
                "uptime_seconds": time.time()
                - metrics_storage.get("start_time", time.time()),
            },
            "requests": {
                "total": sum(metrics_storage["http_requests_total"].values()),
                "by_status": dict(
                    Counter(
                        key.split("_")[-1]
                        for key in metrics_storage["http_requests_total"].keys()
                    )
                ),
            },
            "errors": {
                "total": sum(metrics_storage["errors"].values()),
                "by_code": dict(metrics_storage["errors"]),
            },
        }

        return jsonify(summary), 200

    except Exception as e:
        logger.error("Metrics summary error: %s", e)
        return jsonify({"error": "Failed to generate metrics summary"}), 500
