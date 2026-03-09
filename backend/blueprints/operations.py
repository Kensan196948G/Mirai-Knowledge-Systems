"""
blueprints/operations.py - 事故レポート・承認フロー・法令・プロジェクト・専門家・通知 API Blueprint

Phase H-3: app_v2.py incidents/approvals ルートを移行
Phase I-4: regulations/projects/experts/notifications ルートを移行

移行エンドポイント一覧:
  GET  /api/v1/incidents                          - 事故レポート一覧
  GET  /api/v1/incidents/<id>                     - 事故レポート詳細
  GET  /api/v1/approvals                          - 承認フロー一覧
  POST /api/v1/approvals/<id>/approve             - 承認処理
  POST /api/v1/approvals/<id>/reject              - 却下処理
  GET  /api/v1/regulations/<id>                   - 法令詳細
  GET  /api/v1/projects                           - プロジェクト一覧
  GET  /api/v1/projects/<id>                      - プロジェクト詳細
  GET  /api/v1/experts                            - 専門家一覧
  GET  /api/v1/experts/<id>                       - 専門家詳細
  GET  /api/v1/notifications                      - 通知一覧
  PUT  /api/v1/notifications/<id>/read            - 通知既読
  GET  /api/v1/notifications/unread/count         - 未読数取得
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    cache_get,
    cache_set,
    check_permission,
    get_cache_key,
    get_dal,
    load_data,
    load_users,
    log_access,
    save_data,
)

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


# ============================================================
# 法令 API（Phase I-4: app_v2.py から移行）
# ============================================================


@operations_bp.route("/regulations/<int:reg_id>", methods=["GET"])
@check_permission("knowledge.read")
def get_regulation_detail(reg_id):
    """法令詳細取得（キャッシュ対応）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "regulation.view", "regulation", reg_id)

    cache_key = get_cache_key("regulations_detail", reg_id)
    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: regulations_detail - %s", cache_key)
        return jsonify(cached_result)

    dal = get_dal()
    regulation = dal.get_regulation_by_id(reg_id)

    if not regulation:
        return jsonify({"success": False, "error": "Regulation not found"}), 404

    response_data = {"success": True, "data": regulation}
    cache_set(cache_key, response_data, ttl=86400)
    logger.info("Cache set: regulations_detail - %s", cache_key)
    return jsonify(response_data)


# ============================================================
# プロジェクト API（Phase I-4: app_v2.py から移行）
# ============================================================


@operations_bp.route("/projects", methods=["GET"])
@check_permission("knowledge.read")
def get_projects():
    """プロジェクト一覧取得（キャッシュ対応）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "projects.list", "project")

        type_filter = request.args.get("type", "")
        status_filter = request.args.get("status", "")
        cache_key = get_cache_key("projects_list", type_filter, status_filter)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: projects_list - %s", cache_key)
            return jsonify(cached_result)

        filters = {}
        if type_filter:
            filters["type"] = type_filter
        if status_filter:
            filters["status"] = status_filter

        dal = get_dal()
        projects = dal.get_projects_list(filters) or []
        response_data = {"success": True, "data": projects}
        cache_set(cache_key, response_data, ttl=3600)
        logger.info("Cache set: projects_list - %s", cache_key)
        return jsonify(response_data)
    except Exception as e:
        logger.error("get_projects: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@operations_bp.route("/projects/<int:project_id>", methods=["GET"])
@check_permission("knowledge.read")
def get_project_detail(project_id):
    """プロジェクト詳細取得（キャッシュ対応）"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "project.view", "project", project_id)

    cache_key = get_cache_key("projects_detail", project_id)
    cached_result = cache_get(cache_key)
    if cached_result:
        logger.info("Cache hit: projects_detail - %s", cache_key)
        return jsonify(cached_result)

    dal = get_dal()
    project = dal.get_project_by_id(project_id)

    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404

    response_data = {"success": True, "data": project}
    cache_set(cache_key, response_data, ttl=3600)
    logger.info("Cache set: projects_detail - %s", cache_key)
    return jsonify(response_data)


# ============================================================
# 専門家 API（Phase I-4: app_v2.py から移行）
# ============================================================


@operations_bp.route("/experts", methods=["GET"])
@check_permission("knowledge.read")
def get_experts():
    """専門家一覧取得（キャッシュ対応）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "experts.list", "expert")

        specialization_filter = request.args.get("specialization", "")
        available_filter = request.args.get("available", "")
        cache_key = get_cache_key("experts_list", specialization_filter, available_filter)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: experts_list - %s", cache_key)
            return jsonify(cached_result)

        filters = {}
        if specialization_filter:
            filters["specialization"] = specialization_filter
        if available_filter:
            filters["is_available"] = available_filter.lower() == "true"

        dal = get_dal()
        experts = dal.get_experts_list(filters) or []
        response_data = {"success": True, "data": experts}
        cache_set(cache_key, response_data, ttl=7200)
        logger.info("Cache set: experts_list - %s", cache_key)
        return jsonify(response_data)
    except Exception as e:
        logger.error("get_experts: %s: %s", type(e).__name__, e)
        return jsonify({"success": True, "data": []})


@operations_bp.route("/experts/<int:expert_id>", methods=["GET"])
@check_permission("knowledge.read")
def get_expert_detail(expert_id):
    """専門家詳細取得（キャッシュ対応）"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "expert.view", "expert", expert_id)

        cache_key = get_cache_key("experts_detail", expert_id)
        cached_result = cache_get(cache_key)
        if cached_result:
            logger.info("Cache hit: experts_detail - %s", cache_key)
            return jsonify(cached_result)

        dal = get_dal()
        expert = dal.get_expert_by_id(expert_id)

        if not expert:
            return jsonify({"success": False, "error": "Expert not found"}), 404

        response_data = {"success": True, "data": expert}
        cache_set(cache_key, response_data, ttl=7200)
        logger.info("Cache set: experts_detail - %s", cache_key)
        return jsonify(response_data)
    except Exception as e:
        logger.error("get_expert_detail(%s): %s: %s", expert_id, type(e).__name__, e)
        return jsonify({"success": False, "error": "Expert not found"}), 404


# ============================================================
# 通知 API（Phase I-4: app_v2.py から移行）
# ============================================================


def _get_user_notifications(current_user_id, user_roles):
    """ユーザーに該当する通知をフィルタリング（共通ヘルパー）"""
    notifications = load_data("notifications.json")
    user_roles_set = set(user_roles)
    user_notifications = []

    for n in notifications:
        if current_user_id in n.get("target_users", []) or (
            user_roles_set & set(n.get("target_roles", []))
        ):
            n_copy = n.copy()
            n_copy["is_read"] = current_user_id in n.get("read_by", [])
            user_notifications.append(n_copy)

    user_notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return user_notifications


@operations_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """ユーザーの通知一覧取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u["id"] == current_user_id), None)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_notifications = _get_user_notifications(
        current_user_id, user.get("roles", [])
    )
    unread_count = sum(1 for n in user_notifications if not n["is_read"])

    return jsonify(
        {
            "success": True,
            "data": user_notifications,
            "pagination": {
                "total_items": len(user_notifications),
                "unread_count": unread_count,
            },
        }
    )


@operations_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_read(notification_id):
    """通知を既読にする"""
    current_user_id = int(get_jwt_identity())
    notifications = load_data("notifications.json")

    notification = next((n for n in notifications if n["id"] == notification_id), None)
    if not notification:
        return jsonify({"success": False, "error": "Notification not found"}), 404

    # 既読リストに追加
    if current_user_id not in notification.get("read_by", []):
        notification.setdefault("read_by", []).append(current_user_id)
        save_data("notifications.json", notifications)

    return jsonify({"success": True, "data": {"id": notification_id, "is_read": True}})


@operations_bp.route("/notifications/unread/count", methods=["GET"])
@jwt_required()
def get_unread_count():
    """未読通知数取得"""
    current_user_id = int(get_jwt_identity())
    users = load_users()
    user = next((u for u in users if u["id"] == current_user_id), None)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_notifications = _get_user_notifications(
        current_user_id, user.get("roles", [])
    )
    unread_count = sum(1 for n in user_notifications if not n["is_read"])

    return jsonify({"success": True, "data": {"unread_count": unread_count}})
