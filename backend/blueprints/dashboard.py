"""
blueprints/dashboard.py - ダッシュボード・SOP API Blueprint

Phase H-2: app_v2.py から移行
  - GET /api/v1/sop
  - GET /api/v1/sop/<sop_id>
  - GET /api/v1/sop/<sop_id>/related
  - GET /api/v1/dashboard/stats
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    CacheInvalidator,
    cache_get,
    cache_set,
    check_permission,
    get_cache_key,
    load_data,
    log_access,
    recommendation_engine,
)

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/v1")


# ================================================================
# SOP API
# ================================================================


@dashboard_bp.route("/sop", methods=["GET"])
@check_permission("sop.read")
def get_sop():
    """SOP一覧取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "sop.list", "sop")

        cache_key = get_cache_key("sop_list")
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: sop_list - %s", cache_key)
            return jsonify(cached_result)

        sop_list = load_data("sop.json") or []
        response_data = {
            "success": True,
            "data": sop_list,
            "pagination": {"total_items": len(sop_list)},
        }
        cache_set(cache_key, response_data, ttl=3600)
        logger.info("Cache set: sop_list - %s", cache_key)

        return jsonify(response_data)
    except Exception as e:
        logger.error("get_sop: %s: %s", type(e).__name__, e)
        raise


@dashboard_bp.route("/sop/<int:sop_id>", methods=["GET"])
@check_permission("sop.read")
def get_sop_detail(sop_id):
    """SOP詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "sop.view", "sop", sop_id)

    sop_list = load_data("sop.json")
    sop = next((s for s in sop_list if s["id"] == sop_id), None)

    if not sop:
        return jsonify({"success": False, "error": "SOP not found"}), 404

    return jsonify({"success": True, "data": sop})


@dashboard_bp.route("/sop/<int:sop_id>/related", methods=["GET"])
@check_permission("sop.read")
def get_related_sop(sop_id):
    """
    関連SOPを取得（キャッシュ対応 - Phase G-6 Phase 2）

    クエリパラメータ:
        limit: 取得件数（デフォルト: 5）
        algorithm: アルゴリズム（tag/category/keyword/hybrid、デフォルト: hybrid）
        min_score: 最小スコア閾値（デフォルト: 0.1）

    NOTE: MLアルゴリズム（O(n²)計算量）のため、キャッシュ優先度最高。
    """
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "sop.related", "sop", sop_id)

    limit = int(request.args.get("limit", 5))
    algorithm = request.args.get("algorithm", "hybrid")
    min_score = float(request.args.get("min_score", 0.1))

    min_score_key = f"{min_score:.2f}"
    cache_key = get_cache_key("sop_related", sop_id, limit, algorithm, min_score_key)
    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: sop_related - %s", cache_key)
        return jsonify(cached_result)

    if limit < 1 or limit > 20:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_LIMIT",
                        "message": "limit must be between 1 and 20",
                    },
                }
            ),
            400,
        )

    if algorithm not in ["tag", "category", "keyword", "hybrid"]:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_ALGORITHM",
                        "message": "algorithm must be tag, category, keyword, or hybrid",
                    },
                }
            ),
            400,
        )

    sop_list = load_data("sop.json")
    target_sop = next((s for s in sop_list if s["id"] == sop_id), None)

    if not target_sop:
        return jsonify({"success": False, "error": "SOP not found"}), 404

    related = recommendation_engine.get_related_items(
        target_sop, sop_list, limit=limit, algorithm=algorithm, min_score=min_score
    )

    response_data = {
        "success": True,
        "data": {
            "target_id": sop_id,
            "related_items": related,
            "algorithm": algorithm,
            "count": len(related),
        },
    }

    cache_set(cache_key, response_data, ttl=3600)
    logger.info("Cache set: sop_related - %s", cache_key)

    return jsonify(response_data)


# ================================================================
# Dashboard API
# ================================================================


@dashboard_bp.route("/dashboard/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    """ダッシュボード統計情報取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "dashboard.view", "dashboard")

    cache_key = get_cache_key("dashboard_stats")
    cached_result = cache_get(cache_key)
    if cached_result:
        return jsonify(cached_result)

    knowledge_list = load_data("knowledge.json")
    sop_list = load_data("sop.json")
    incidents = load_data("incidents.json")
    approvals = load_data("approvals.json")

    pending_approvals_count = len(
        [a for a in approvals if a.get("status") == "pending"]
    )

    stats = {
        "kpis": {
            "knowledge_reuse_rate": 71,
            "accident_free_days": 184,
            "active_audits": 6,
            "delayed_corrections": 3,
        },
        "counts": {
            "total_knowledge": len(knowledge_list),
            "total_sop": len(sop_list),
            "recent_incidents": len(
                [i for i in incidents if i.get("status") == "reported"]
            ),
            "pending_approvals": pending_approvals_count,
        },
        "last_sync_time": datetime.now().isoformat(),
        "active_workers": 0,
        "total_workers": 100,
        "pending_approvals": pending_approvals_count,
    }

    response_data = {"success": True, "data": stats}
    cache_set(cache_key, response_data, ttl=300)  # 5分

    return jsonify(response_data)
