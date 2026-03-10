"""
blueprints/recommendations.py - 推薦API Blueprint

Phase H-4: app_v2.py 推薦関連ルートを移行

移行エンドポイント一覧:
  GET  /api/v1/recommendations/personalized   - パーソナライズ推薦
  GET  /api/v1/recommendations/cache/stats    - キャッシュ統計（管理者のみ）
  POST /api/v1/recommendations/cache/clear    - キャッシュクリア（管理者のみ）
"""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    check_permission,
    load_data,
    log_access,
    recommendation_engine,
)

logger = logging.getLogger(__name__)

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/v1")


# ============================================================
# 推薦API
# ============================================================


@recommendations_bp.route("/recommendations/personalized", methods=["GET"])
@jwt_required()
def get_personalized_recommendations():
    """
    パーソナライズ推薦を取得

    クエリパラメータ:
        limit: 取得件数（デフォルト: 5、最大: 20）
        days: 対象期間（日数、デフォルト: 30）
        type: 推薦タイプ（knowledge/sop/all、デフォルト: all）
    """
    current_user_id = int(get_jwt_identity())
    log_access(current_user_id, "recommendations.personalized", "recommendations")

    limit = int(request.args.get("limit", 5))
    days = int(request.args.get("days", 30))
    rec_type = request.args.get("type", "all")

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

    if days < 1 or days > 365:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_DAYS",
                        "message": "days must be between 1 and 365",
                    },
                }
            ),
            400,
        )

    if rec_type not in ["knowledge", "sop", "all"]:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_TYPE",
                        "message": "type must be knowledge, sop, or all",
                    },
                }
            ),
            400,
        )

    access_logs = load_data("access_logs.json")
    knowledge_list = load_data("knowledge.json")
    sop_list = load_data("sop.json")

    results = {}

    if rec_type in ["knowledge", "all"]:
        knowledge_recommendations = (
            recommendation_engine.get_personalized_recommendations(
                user_id=current_user_id,
                access_logs=access_logs,
                all_items=knowledge_list,
                limit=limit,
                days=days,
            )
        )
        results["knowledge"] = {
            "items": knowledge_recommendations,
            "count": len(knowledge_recommendations),
        }

    if rec_type in ["sop", "all"]:
        sop_recommendations = recommendation_engine.get_personalized_recommendations(
            user_id=current_user_id,
            access_logs=access_logs,
            all_items=sop_list,
            limit=limit,
            days=days,
        )
        results["sop"] = {
            "items": sop_recommendations,
            "count": len(sop_recommendations),
        }

    results["parameters"] = {"limit": limit, "days": days, "type": rec_type}

    return jsonify({"success": True, "data": results})


@recommendations_bp.route("/recommendations/cache/stats", methods=["GET"])
@jwt_required()
@check_permission("admin")
def get_recommendation_cache_stats():
    """推薦エンジンのキャッシュ統計を取得（管理者のみ）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "recommendations.cache_stats", "recommendations")

    stats = recommendation_engine.get_cache_stats()

    return jsonify({"success": True, "data": stats})


@recommendations_bp.route("/recommendations/cache/clear", methods=["POST"])
@jwt_required()
@check_permission("admin")
def clear_recommendation_cache():
    """推薦エンジンのキャッシュをクリア（管理者のみ）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "recommendations.cache_clear", "recommendations")

    recommendation_engine.clear_cache()

    return jsonify(
        {"success": True, "message": "Recommendation cache cleared successfully"}
    )
