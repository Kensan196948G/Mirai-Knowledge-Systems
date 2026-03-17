"""
blueprints/ms365_integration.py - Microsoft 365 Integration API Blueprint

Phase H-4: MS365 integration APIルートを /api/v1/integrations/microsoft365/ に追加
Step 5: blueprints/ms365.py から ms365_integration_bp を分離

エンドポイント一覧 (ms365_integration_bp):
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

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import (
    check_permission,
    log_access,
    validate_request,
)
from schemas import MS365ImportSchema, MS365SyncSchema

logger = logging.getLogger(__name__)

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
