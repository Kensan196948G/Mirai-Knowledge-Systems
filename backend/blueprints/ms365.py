"""
blueprints/ms365.py - Microsoft 365 同期管理 API Blueprint

Phase H-3: app_v2.py MS365同期関連ルートを /api/v1/ms365/ に移行

移行エンドポイント一覧:
  GET    /api/v1/ms365/sync/configs                        - 同期設定一覧
  POST   /api/v1/ms365/sync/configs                        - 同期設定作成
  GET    /api/v1/ms365/sync/configs/<id>                   - 同期設定取得
  PUT    /api/v1/ms365/sync/configs/<id>                   - 同期設定更新
  DELETE /api/v1/ms365/sync/configs/<id>                   - 同期設定削除
  POST   /api/v1/ms365/sync/configs/<id>/execute           - 手動同期実行
  POST   /api/v1/ms365/sync/configs/<id>/test              - 接続テスト
  GET    /api/v1/ms365/sync/configs/<id>/history           - 同期履歴
  GET    /api/v1/ms365/sync/stats                          - 同期統計
  GET    /api/v1/ms365/sync/status                         - サービスステータス
"""

import logging
from collections import Counter
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    check_permission,
    get_dal,
    log_access,
)

logger = logging.getLogger(__name__)

ms365_bp = Blueprint("ms365", __name__, url_prefix="/api/v1/ms365")


def _get_sync_service():
    """MS365同期サービス（遅延インポートで循環参照回避）"""
    try:
        from app_v2 import get_ms365_sync_service
        return get_ms365_sync_service()
    except Exception:
        return None


def _get_scheduler_service():
    """MS365スケジューラーサービス（遅延インポートで循環参照回避）"""
    try:
        from app_v2 import get_ms365_scheduler_service
        return get_ms365_scheduler_service()
    except Exception:
        return None


# ============================================================
# 同期設定 CRUD
# ============================================================


@ms365_bp.route("/sync/configs", methods=["GET"])
@jwt_required()
def ms365_sync_configs_list():
    """同期設定一覧を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "ms365_sync_configs.list", "ms365_sync_config")

        dal = get_dal()
        configs = dal.get_all_ms365_sync_configs()

        return jsonify({"success": True, "data": configs})
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/configs", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_create():
    """同期設定を作成"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 必須フィールド検証
        required_fields = ["name", "site_id", "drive_id"]
        for field in required_fields:
            if not data or not data.get(field):
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"{field} is required",
                    },
                }), 400

        # cron形式バリデーション
        sync_schedule = data.get("sync_schedule", "0 2 * * *")
        if sync_schedule:
            parts = sync_schedule.split()
            if len(parts) != 5:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "sync_schedule must be a valid cron expression (5 fields)",
                        "details": {"sync_schedule": "Invalid cron expression"},
                    },
                }), 400

        config_data = {
            "name": data["name"],
            "description": data.get("description", ""),
            "site_id": data["site_id"],
            "drive_id": data["drive_id"],
            "folder_path": data.get("folder_path", "/"),
            "sync_schedule": sync_schedule,
            "sync_strategy": data.get("sync_strategy", "incremental"),
            "file_extensions": data.get("file_extensions", ["pdf", "docx", "xlsx"]),
            "is_enabled": data.get("is_enabled", True),
            "metadata_mapping": data.get("metadata_mapping", {}),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        dal = get_dal()
        result = dal.create_ms365_sync_config(config_data)

        log_access(
            current_user_id,
            "ms365_sync_configs.create",
            "ms365_sync_config",
        )

        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/configs/<int:config_id>", methods=["GET"])
@jwt_required()
def ms365_sync_configs_get(config_id):
    """同期設定を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id, "ms365_sync_configs.get", "ms365_sync_config", config_id
        )

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return jsonify({
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Sync config {config_id} not found"},
            }), 404

        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/configs/<int:config_id>", methods=["PUT"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_update(config_id):
    """同期設定を更新"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        dal = get_dal()
        existing = dal.get_ms365_sync_config(config_id)

        if not existing:
            return jsonify({
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Sync config {config_id} not found"},
            }), 404

        update_data = {"updated_at": datetime.utcnow().isoformat()}
        for field in ["name", "folder_path", "sync_schedule", "sync_strategy",
                      "file_extensions", "is_enabled", "description"]:
            if field in data:
                update_data[field] = data[field]

        dal.update_ms365_sync_config(config_id, update_data)

        scheduler_service = _get_scheduler_service()
        if scheduler_service:
            try:
                updated_config = dal.get_ms365_sync_config(config_id)
                scheduler_service.reschedule_sync(updated_config)
            except Exception as e:
                logger.warning("Failed to reschedule sync: %s", e)

        log_access(
            current_user_id, "ms365_sync_configs.update", "ms365_sync_config", config_id
        )

        result = dal.get_ms365_sync_config(config_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/configs/<int:config_id>", methods=["DELETE"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_delete(config_id):
    """同期設定を削除"""
    try:
        current_user_id = get_jwt_identity()

        dal = get_dal()
        existing = dal.get_ms365_sync_config(config_id)

        if not existing:
            return jsonify({
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Sync config {config_id} not found"},
            }), 404

        scheduler_service = _get_scheduler_service()
        if scheduler_service:
            try:
                scheduler_service.unschedule_sync(config_id)
            except Exception as e:
                logger.warning("Failed to unschedule sync: %s", e)

        dal.delete_ms365_sync_config(config_id)

        log_access(
            current_user_id, "ms365_sync_configs.delete", "ms365_sync_config", config_id
        )

        return jsonify({
            "success": True,
            "message": f"Sync config {config_id} deleted successfully",
        })
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/configs/<int:config_id>/execute", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_execute(config_id):
    """手動で同期を実行"""
    try:
        current_user_id = get_jwt_identity()

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return jsonify({
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Sync config {config_id} not found"},
            }), 404

        sync_service = _get_sync_service()
        if not sync_service:
            return jsonify({
                "success": False,
                "error": {"code": "SERVICE_UNAVAILABLE", "message": "MS365 sync service is not available"},
            }), 503

        result = sync_service.sync_configuration(
            config_id, triggered_by="manual", user_id=current_user_id
        )

        log_access(
            current_user_id, "ms365_sync_configs.execute", "ms365_sync_config", config_id
        )

        return jsonify({"success": True, "data": result})
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": str(e)},
        }), 400
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/configs/<int:config_id>/test", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
def ms365_sync_configs_test(config_id):
    """接続テスト（ドライラン）"""
    try:
        current_user_id = get_jwt_identity()

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return jsonify({
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Sync config {config_id} not found"},
            }), 404

        sync_service = _get_sync_service()
        if not sync_service:
            return jsonify({
                "success": False,
                "error": {"code": "SERVICE_UNAVAILABLE", "message": "MS365 sync service is not available"},
            }), 503

        result = sync_service.test_connection(config_id)

        log_access(
            current_user_id, "ms365_sync_configs.test", "ms365_sync_config", config_id
        )

        if result.get("success"):
            return jsonify({"success": True, "data": result})
        else:
            return jsonify({
                "success": False,
                "error": {"code": "CONNECTION_FAILED", "message": result.get("error")},
            }), 400
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/configs/<int:config_id>/history", methods=["GET"])
@jwt_required()
def ms365_sync_configs_history(config_id):
    """同期履歴を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id, "ms365_sync_configs.history", "ms365_sync_config", config_id
        )

        dal = get_dal()
        config = dal.get_ms365_sync_config(config_id)

        if not config:
            return jsonify({
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Sync config {config_id} not found"},
            }), 404

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        history = dal.get_ms365_sync_history_by_config(config_id)
        total = len(history)
        start = (page - 1) * per_page
        paginated = history[start:start + per_page]

        return jsonify({
            "success": True,
            "data": {
                "items": paginated,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page,
                },
            },
        })
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


# ============================================================
# 同期統計・ステータス
# ============================================================


@ms365_bp.route("/sync/stats", methods=["GET"])
@jwt_required()
def ms365_sync_stats():
    """同期統計情報を取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "ms365_sync.stats", "ms365_sync")

        dal = get_dal()
        all_configs = dal.get_all_ms365_sync_configs()
        enabled_configs = [c for c in all_configs if c.get("is_enabled")]

        config_ids = [c["id"] for c in all_configs]
        recent_syncs = dal.get_recent_ms365_sync_histories(config_ids, limit_per_config=5)

        status_counts = Counter([h.get("status") for h in recent_syncs])

        last_sync = None
        for sync in sorted(
            recent_syncs,
            key=lambda x: x.get("sync_started_at", ""),
            reverse=True,
        ):
            if sync.get("sync_completed_at"):
                last_sync = sync
                break

        stats = {
            "total_configs": len(all_configs),
            "active_configs": len(enabled_configs),
            "disabled_configs": len(all_configs) - len(enabled_configs),
            "recent_syncs": {
                "total": len(recent_syncs),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "running": status_counts.get("running", 0),
            },
            "last_sync": (
                {
                    "config_id": last_sync.get("config_id") if last_sync else None,
                    "status": last_sync.get("status") if last_sync else None,
                    "completed_at": last_sync.get("sync_completed_at") if last_sync else None,
                    "files_processed": last_sync.get("files_processed", 0) if last_sync else 0,
                }
                if last_sync
                else None
            ),
        }

        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500


@ms365_bp.route("/sync/status", methods=["GET"])
@jwt_required()
def ms365_sync_status():
    """同期サービスのステータスを取得"""
    try:
        current_user_id = get_jwt_identity()
        log_access(current_user_id, "ms365_sync.status", "ms365_sync")

        sync_service = _get_sync_service()
        scheduler_service = _get_scheduler_service()

        status = {
            "sync_service_available": sync_service is not None,
            "scheduler_service_available": scheduler_service is not None,
            "scheduler_running": (
                scheduler_service.is_running() if scheduler_service else False
            ),
            "scheduled_jobs": (
                scheduler_service.get_scheduled_jobs() if scheduler_service else []
            ),
            "graph_api_configured": False,
            "running_jobs": [],
        }

        if sync_service and hasattr(sync_service, "graph_client"):
            graph_client = sync_service.graph_client
            if graph_client and hasattr(graph_client, "is_configured"):
                status["graph_api_configured"] = graph_client.is_configured()

        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "SERVER_ERROR", "message": str(e)}}
        ), 500
