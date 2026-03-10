"""
blueprints/ms365.py - Microsoft 365 API Blueprint

Phase H-3: app_v2.py MS365同期関連ルートを /api/v1/ms365/ に移行
Phase H-4: MS365 integration APIルートを /api/v1/integrations/microsoft365/ に追加

移行エンドポイント一覧 (ms365_bp):
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

移行エンドポイント一覧 (ms365_integration_bp):
  GET    /api/v1/integrations/microsoft365/status                        - 接続状態
  GET    /api/v1/integrations/microsoft365/sites                         - サイト一覧
  GET    /api/v1/integrations/microsoft365/sites/<site_id>/drives        - ドライブ一覧
  GET    /api/v1/integrations/microsoft365/drives/<drive_id>/items       - アイテム一覧
  POST   /api/v1/integrations/microsoft365/import                        - ファイルインポート
  POST   /api/v1/integrations/microsoft365/sync                          - 同期実行
  GET    /api/v1/integrations/microsoft365/teams                         - チーム一覧
  GET    /api/v1/integrations/microsoft365/teams/<team_id>/channels      - チャンネル一覧
  GET    /api/v1/integrations/microsoft365/files/<file_id>/preview       - プレビューURL取得
  GET    /api/v1/integrations/microsoft365/files/<file_id>/download      - ダウンロード
  GET    /api/v1/integrations/microsoft365/files/<file_id>/thumbnail     - サムネイル取得
"""

import logging
from collections import Counter
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    check_permission,
    get_dal,
    log_access,
    validate_request,
)
from schemas import MS365ImportSchema, MS365SyncSchema

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
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
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

        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
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

        history = dal.get_ms365_sync_histories_by_config(config_id)
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


# ============================================================
# Microsoft 365 Integration API Blueprint
# Phase H-4: /api/v1/integrations/microsoft365/ ルート移行
# ============================================================

# Microsoft Graph クライアントのシングルトン
_ms_graph_client = None


def get_ms_graph_client():
    """Microsoft Graph クライアントを取得（シングルトン）"""
    global _ms_graph_client
    if _ms_graph_client is None:
        try:
            from integrations.microsoft_graph import MicrosoftGraphClient

            _ms_graph_client = MicrosoftGraphClient()
        except Exception as e:
            logger.warning("Microsoft Graph client initialization failed: %s", e)
            return None
    return _ms_graph_client


ms365_integration_bp = Blueprint(
    "ms365_integration", __name__, url_prefix="/api/v1/integrations/microsoft365"
)


@ms365_integration_bp.route("/status", methods=["GET"])
@jwt_required()
def ms365_status():
    """Microsoft 365接続状態を確認"""
    client = get_ms_graph_client()
    if not client:
        return jsonify(
            {
                "success": True,
                "data": {
                    "configured": False,
                    "connected": False,
                    "message": "Microsoft Graph client not available",
                },
            }
        )

    try:
        result = client.test_connection()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify(
            {
                "success": True,
                "data": {
                    "configured": client.is_configured(),
                    "connected": False,
                    "error": str(e),
                },
            }
        )


@ms365_integration_bp.route("/sites", methods=["GET"])
@jwt_required()
def ms365_sites():
    """SharePointサイト一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    search_query = request.args.get("search", "")

    try:
        sites = client.get_sharepoint_sites(search_query=search_query)
        return jsonify(
            {
                "success": True,
                "data": {
                    "sites": sites,
                    "count": len(sites),
                },
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
        ), 500


@ms365_integration_bp.route("/sites/<site_id>/drives", methods=["GET"])
@jwt_required()
def ms365_site_drives(site_id):
    """SharePointサイトのドライブ一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    try:
        drives = client.get_site_drives(site_id)
        return jsonify(
            {
                "success": True,
                "data": {
                    "drives": drives,
                    "count": len(drives),
                    "site_id": site_id,
                },
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
        ), 500


@ms365_integration_bp.route("/drives/<drive_id>/items", methods=["GET"])
@jwt_required()
def ms365_drive_items(drive_id):
    """ドライブのアイテム一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    folder_path = request.args.get("path", "")
    file_types = request.args.getlist("file_type")

    try:
        items = client.get_drive_items(
            drive_id, folder_path=folder_path, file_types=file_types
        )
        return jsonify(
            {
                "success": True,
                "data": {
                    "items": items,
                    "count": len(items),
                    "drive_id": drive_id,
                },
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
        ), 500


@ms365_integration_bp.route("/import", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
@validate_request(MS365ImportSchema)
def ms365_import():
    """Microsoft 365からファイルをインポート"""
    data = request.validated_data
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    drive_id = data["drive_id"]
    item_ids = data["item_ids"]
    import_as = data.get("import_as", "document")

    imported = []
    errors_list = []

    for item_id in item_ids:
        try:
            metadata = client.get_file_metadata(drive_id, item_id)
            content = client.download_file(drive_id, item_id)
            imported.append(
                {
                    "item_id": item_id,
                    "name": metadata.get("name"),
                    "size": len(content),
                    "imported_as": import_as,
                }
            )
        except Exception as e:
            errors_list.append({"item_id": item_id, "error": str(e)})

    return jsonify(
        {
            "success": True,
            "data": {
                "imported": imported,
                "errors": errors_list,
                "total_imported": len(imported),
                "total_errors": len(errors_list),
            },
        }
    )


@ms365_integration_bp.route("/sync", methods=["POST"])
@jwt_required()
@check_permission("integration.manage")
@validate_request(MS365SyncSchema)
def ms365_integration_sync():
    """Microsoft 365と同期"""
    data = request.validated_data
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    sync_type = data.get("sync_type", "incremental")

    return jsonify(
        {
            "success": True,
            "data": {
                "sync_type": sync_type,
                "status": "completed",
                "message": "Sync completed successfully",
            },
        }
    )


@ms365_integration_bp.route("/teams", methods=["GET"])
@jwt_required()
def ms365_teams():
    """Teamsチーム一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    try:
        teams = client.get_teams()
        return jsonify(
            {
                "success": True,
                "data": {
                    "teams": teams,
                    "count": len(teams),
                },
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
        ), 500


@ms365_integration_bp.route("/teams/<team_id>/channels", methods=["GET"])
@jwt_required()
def ms365_team_channels(team_id):
    """Teamsチャンネル一覧を取得"""
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    try:
        channels = client.get_team_channels(team_id)
        return jsonify(
            {
                "success": True,
                "data": {
                    "channels": channels,
                    "count": len(channels),
                    "team_id": team_id,
                },
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
        ), 500


@ms365_integration_bp.route("/files/<file_id>/preview", methods=["GET"])
@jwt_required()
@check_permission("ms365_sync.file.preview")
def ms365_file_preview(file_id: str):
    """
    ファイルプレビューURLを取得

    Query Parameters:
        drive_id (required): ドライブID
    """
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    drive_id = request.args.get("drive_id")
    if not drive_id:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "MISSING_PARAMETER",
                        "message": "drive_id parameter is required",
                    },
                }
            ),
            400,
        )

    try:
        current_user_id = get_jwt_identity()

        preview_info = client.get_file_preview_url(drive_id, file_id)
        metadata = client.get_file_metadata(drive_id, file_id)

        response_data = {
            **preview_info,
            "file_name": metadata.get("name", ""),
            "file_size": metadata.get("size", 0),
        }

        log_access(
            current_user_id,
            "ms365_file.preview",
            "ms365_file",
            file_id,
            status="success",
            details={
                "drive_id": drive_id,
                "file_name": response_data["file_name"],
                "preview_type": preview_info["preview_type"],
            },
        )

        return jsonify({"success": True, "data": response_data})
    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id,
            "ms365_file.preview",
            "ms365_file",
            file_id,
            status="failure",
            details={"error": str(e), "drive_id": drive_id},
        )
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@ms365_integration_bp.route("/files/<file_id>/download", methods=["GET"])
@jwt_required()
@check_permission("ms365_sync.file.preview")
def ms365_file_download(file_id: str):
    """
    ファイルをダウンロード

    Query Parameters:
        drive_id (required): ドライブID
    """
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    drive_id = request.args.get("drive_id")
    if not drive_id:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "MISSING_PARAMETER",
                        "message": "drive_id parameter is required",
                    },
                }
            ),
            400,
        )

    try:
        current_user_id = get_jwt_identity()

        metadata = client.get_file_metadata(drive_id, file_id)
        file_name = metadata.get("name", "download")
        mime_type = metadata.get("file", {}).get("mimeType", "application/octet-stream")

        file_content = client.download_file(drive_id, file_id)

        log_access(
            current_user_id,
            "ms365_file.download",
            "ms365_file",
            file_id,
            status="success",
            details={
                "drive_id": drive_id,
                "file_name": file_name,
                "file_size": len(file_content),
            },
        )

        response = Response(file_content, mimetype=mime_type)
        response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
        return response

    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id,
            "ms365_file.download",
            "ms365_file",
            file_id,
            status="failure",
            details={"error": str(e), "drive_id": drive_id},
        )
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )


@ms365_integration_bp.route("/files/<file_id>/thumbnail", methods=["GET"])
@jwt_required()
@check_permission("ms365_sync.file.preview")
def ms365_file_thumbnail(file_id: str):
    """
    ファイルサムネイルを取得

    Query Parameters:
        drive_id (required): ドライブID
        size (optional): "small" | "medium" | "large" | "c200x150"（デフォルト: "large"）
    """
    client = get_ms_graph_client()
    if not client or not client.is_configured():
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_CONFIGURED",
                        "message": "Microsoft 365 is not configured",
                    },
                }
            ),
            400,
        )

    drive_id = request.args.get("drive_id")
    if not drive_id:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "MISSING_PARAMETER",
                        "message": "drive_id parameter is required",
                    },
                }
            ),
            400,
        )

    size = request.args.get("size", "large")

    try:
        current_user_id = get_jwt_identity()

        thumbnail_content = client.get_file_thumbnail(drive_id, file_id, size)

        if thumbnail_content is None:
            log_access(
                current_user_id,
                "ms365_file.thumbnail",
                "ms365_file",
                file_id,
                status="failure",
                details={"drive_id": drive_id, "error": "Thumbnail not available"},
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Thumbnail not available for this file",
                        },
                    }
                ),
                404,
            )

        log_access(
            current_user_id,
            "ms365_file.thumbnail",
            "ms365_file",
            file_id,
            status="success",
            details={
                "drive_id": drive_id,
                "size": size,
                "thumbnail_size": len(thumbnail_content),
            },
        )

        return Response(thumbnail_content, mimetype="image/jpeg")

    except PermissionError as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "PERMISSION_ERROR", "message": str(e)},
                }
            ),
            403,
        )
    except Exception as e:
        current_user_id = get_jwt_identity()
        log_access(
            current_user_id,
            "ms365_file.thumbnail",
            "ms365_file",
            file_id,
            status="failure",
            details={"error": str(e), "drive_id": drive_id},
        )
        return (
            jsonify(
                {"success": False, "error": {"code": "API_ERROR", "message": str(e)}}
            ),
            500,
        )
