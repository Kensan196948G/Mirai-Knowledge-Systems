"""
blueprints/consultations.py - 専門家相談 Blueprint

Phase J-2: app_v2.py consultations ルートの Blueprint化
  GET    /api/v1/consultations                        - 相談一覧取得
  GET    /api/v1/consultations/<id>                   - 相談詳細取得
  POST   /api/v1/consultations                        - 新規相談作成
  PUT    /api/v1/consultations/<id>                   - 相談更新
  POST   /api/v1/consultations/<id>/answers           - 回答投稿
"""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from app_helpers import (
    check_permission,
    create_notification,
    get_user_permissions,
    load_users,
    log_access,
    validate_request,
)
from dal import DataAccessLayer
from schemas import ConsultationAnswerSchema, ConsultationCreateSchema

logger = logging.getLogger(__name__)

consultations_bp = Blueprint("consultations", __name__, url_prefix="/api/v1")


def _get_dal():
    return DataAccessLayer()


def _get_current_user(current_user_id):
    """現在のユーザー情報を取得"""
    users = load_users()
    return next((u for u in users if u["id"] == int(current_user_id)), None)


# ============================================================
# 相談一覧・詳細
# ============================================================


@consultations_bp.route("/consultations", methods=["GET"])
@check_permission("consultation.read")
def get_consultations():
    """専門家相談一覧取得"""
    current_user_id = get_jwt_identity()
    log_access(current_user_id, "consultations.list", "consultation")

    category = request.args.get("category")
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    dal = _get_dal()
    result = dal.get_consultations(
        category=category, status=status, page=page, per_page=per_page
    )

    return jsonify(
        {
            "success": True,
            "data": result["data"],
            "pagination": result["pagination"],
        }
    )


@consultations_bp.route("/consultations/<int:consultation_id>", methods=["GET"])
@check_permission("consultation.read")
def get_consultation_detail(consultation_id):
    """専門家相談詳細取得"""
    current_user_id = get_jwt_identity()
    log_access(
        current_user_id, "consultation.view", "consultation", consultation_id
    )

    dal = _get_dal()
    consultation = dal.get_consultation_by_id(consultation_id)

    if not consultation:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Consultation not found",
                    },
                }
            ),
            404,
        )

    return jsonify({"success": True, "data": consultation})


# ============================================================
# 相談作成・更新
# ============================================================


@consultations_bp.route("/consultations", methods=["POST"])
@check_permission("consultation.create")
@validate_request(ConsultationCreateSchema)
def create_consultation():
    """新規相談作成"""
    current_user_id = get_jwt_identity()
    data = request.validated_data

    current_user = _get_current_user(current_user_id)

    dal = _get_dal()
    new_consultation = dal.create_consultation(
        data=data,
        current_user_id=current_user_id,
        current_user=current_user,
    )

    log_access(
        current_user_id,
        "consultation.create",
        "consultation",
        new_consultation["id"],
    )

    create_notification(
        title="新しい相談が投稿されました",
        message=(
            f"{new_consultation['requester']}さんから"
            f"「{new_consultation['title']}」の相談が投稿されました。"
        ),
        type="consultation_created",
        target_roles=["admin", "expert"],
        priority="normal",
        related_entity_type="consultation",
        related_entity_id=new_consultation["id"],
    )

    return jsonify({"success": True, "data": new_consultation}), 201


@consultations_bp.route(
    "/consultations/<int:consultation_id>", methods=["PUT"]
)
@check_permission("consultation.update")
def update_consultation(consultation_id):
    """相談更新"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)

    if not data:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_INPUT",
                        "message": "Request body is required",
                    },
                }
            ),
            400,
        )

    current_user = _get_current_user(current_user_id)
    user_permissions = get_user_permissions(current_user) if current_user else []
    is_admin = "*" in user_permissions

    dal = _get_dal()
    updated, error_code = dal.update_consultation(
        consultation_id=consultation_id,
        data=data,
        current_user_id=current_user_id,
        is_admin=is_admin,
    )

    if error_code == "NOT_FOUND":
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Consultation not found",
                    },
                }
            ),
            404,
        )

    if error_code == "FORBIDDEN":
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You can only update your own consultations",
                    },
                }
            ),
            403,
        )

    log_access(
        current_user_id, "consultation.update", "consultation", consultation_id
    )

    return jsonify({"success": True, "data": updated})


# ============================================================
# 回答投稿
# ============================================================


@consultations_bp.route(
    "/consultations/<int:consultation_id>/answers", methods=["POST"]
)
@check_permission("consultation.answer")
@validate_request(ConsultationAnswerSchema)
def post_consultation_answer(consultation_id):
    """相談に回答を投稿"""
    current_user_id = get_jwt_identity()
    data = request.validated_data

    current_user = _get_current_user(current_user_id)

    dal = _get_dal()
    new_answer, requester_id, consultation_title, error_code = (
        dal.add_consultation_answer(
            consultation_id=consultation_id,
            data=data,
            current_user_id=current_user_id,
            current_user=current_user,
        )
    )

    if error_code == "NOT_FOUND":
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Consultation not found",
                    },
                }
            ),
            404,
        )

    log_access(
        current_user_id,
        "consultation.answer",
        "consultation",
        consultation_id,
    )

    if requester_id:
        create_notification(
            title="相談に回答がありました",
            message=(
                f"{new_answer['expert']}さんが"
                f"「{consultation_title}」に回答しました。"
            ),
            type="consultation_answered",
            target_users=[requester_id],
            priority="normal",
            related_entity_type="consultation",
            related_entity_id=consultation_id,
        )

    return jsonify({"success": True, "data": new_answer}), 201
