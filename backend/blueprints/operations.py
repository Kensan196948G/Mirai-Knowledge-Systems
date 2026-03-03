"""
blueprints/operations.py - 事故レポート・承認フロー API Blueprint

Phase H-3: app_v2.py incidents/approvals ルートを移行

移行エンドポイント一覧:
  GET  /api/v1/incidents                        - 事故レポート一覧
  GET  /api/v1/incidents/<id>                   - 事故レポート詳細
  GET  /api/v1/approvals                        - 承認フロー一覧
  POST /api/v1/approvals/<id>/approve           - 承認処理
  POST /api/v1/approvals/<id>/reject            - 却下処理
"""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    cache_get,
    cache_set,
    check_permission,
    get_cache_key,
    load_data,
    log_access,
    save_data,
)
from datetime import datetime

logger = logging.getLogger(__name__)

operations_bp = Blueprint("operations", __name__, url_prefix="/api/v1")


# ============================================================
# 事故レポート API
# ============================================================


@operations_bp.route("/incidents", methods=["GET"])
@check_permission("incident.read")
def get_incidents():
    """事故レポート一覧取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "incidents.list", "incidents")

        cache_key = get_cache_key("incidents_list")
        cached_result = cache_get(cache_key)
        if cached_result:
            return jsonify(cached_result)

        incidents_list = load_data("incidents.json") or []
        response_data = {
            "success": True,
            "data": incidents_list,
            "pagination": {"total_items": len(incidents_list)},
        }
        cache_set(cache_key, response_data, ttl=3600)

        return jsonify(response_data)
    except Exception:
        raise


@operations_bp.route("/incidents/<int:incident_id>", methods=["GET"])
@check_permission("incident.read")
def get_incident_detail(incident_id):
    """事故レポート詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "incidents.view", "incidents", incident_id)

    incidents_list = load_data("incidents.json")
    incident = next((i for i in incidents_list if i["id"] == incident_id), None)

    if not incident:
        return jsonify({"success": False, "error": "Incident not found"}), 404

    return jsonify({"success": True, "data": incident})


# ============================================================
# 承認フロー API
# ============================================================


@operations_bp.route("/approvals", methods=["GET"])
@jwt_required()
def get_approvals():
    """承認フロー一覧取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "approvals.list", "approvals")

        approvals = load_data("approvals.json") or []
        return jsonify({
            "success": True,
            "data": approvals,
            "pagination": {"total_items": len(approvals)},
        })
    except Exception:
        raise


@operations_bp.route("/approvals/<int:approval_id>/approve", methods=["POST"])
@check_permission("approval.approve")
def approve_approval(approval_id):
    """承認処理"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "approvals.approve", "approvals", approval_id)

    approvals = load_data("approvals.json")
    approval = next((a for a in approvals if a["id"] == approval_id), None)

    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    approval["status"] = "approved"
    approval["approved_by"] = current_user_id
    approval["approved_at"] = datetime.utcnow().isoformat()

    save_data("approvals.json", approvals)

    return jsonify({"success": True, "message": "承認しました", "data": approval})


@operations_bp.route("/approvals/<int:approval_id>/reject", methods=["POST"])
@check_permission("approval.approve")
def reject_approval(approval_id):
    """却下処理"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "approvals.reject", "approvals", approval_id)

    data = request.get_json()
    reason = data.get("reason", "") if data else ""

    if not reason:
        return jsonify({"success": False, "error": "却下理由を入力してください"}), 400

    approvals = load_data("approvals.json")
    approval = next((a for a in approvals if a["id"] == approval_id), None)

    if not approval:
        return jsonify({"success": False, "error": "Approval not found"}), 404

    approval["status"] = "rejected"
    approval["rejected_by"] = current_user_id
    approval["rejected_at"] = datetime.utcnow().isoformat()
    approval["rejection_reason"] = reason

    save_data("approvals.json", approvals)

    return jsonify({"success": True, "message": "却下しました", "data": approval})
