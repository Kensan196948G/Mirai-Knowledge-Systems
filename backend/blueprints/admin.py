"""
blueprints/admin.py - 管理者API Blueprint

Phase H-4: app_v2.py 監査ログ・ヘルスチェックルートを移行

移行エンドポイント一覧:
  GET  /api/v1/logs/access         - 監査ログ取得（管理者専用）
  GET  /api/v1/logs/access/stats   - 監査ログ統計（管理者専用）
  GET  /api/v1/health              - システムヘルスチェック
  GET  /api/v1/health/db           - データベースヘルスチェック
"""

import logging
import os
from collections import Counter
from datetime import datetime, timedelta

import psutil
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app_helpers import check_permission, load_data, log_access

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1")


# ============================================================
# 監査ログAPI
# ============================================================


@admin_bp.route("/logs/access", methods=["GET"])
@jwt_required()
@check_permission("admin")
def get_access_logs():
    """
    監査ログの取得（管理者専用）

    クエリパラメータ:
        user_id: 特定ユーザーでフィルタ
        action: 特定アクションでフィルタ（部分一致）
        resource: リソース種別でフィルタ
        status: success/failureでフィルタ
        start_date: 開始日時（ISO形式）
        end_date: 終了日時（ISO形式）
        page: ページ番号（デフォルト1）
        per_page: 1ページあたりの件数（デフォルト50、最大200）
        sort: 'asc' または 'desc'（デフォルト: desc）
    """
    try:
        current_user_id = get_jwt_identity()
        logs = load_data("access_logs.json")

        user_id_filter = request.args.get("user_id", type=int)
        action_filter = request.args.get("action", "")
        resource_filter = request.args.get("resource", "")
        status_filter = request.args.get("status", "")
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 50, type=int), 200)
        sort_order = request.args.get("sort", "desc")

        filtered_logs = logs

        if user_id_filter:
            filtered_logs = [
                l for l in filtered_logs if l.get("user_id") == user_id_filter
            ]

        if action_filter:
            filtered_logs = [
                l
                for l in filtered_logs
                if action_filter.lower() in str(l.get("action", "")).lower()
            ]

        if resource_filter:
            filtered_logs = [
                l for l in filtered_logs if l.get("resource") == resource_filter
            ]

        if status_filter:
            filtered_logs = [
                l for l in filtered_logs if l.get("status") == status_filter
            ]

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                filtered_logs = [
                    l
                    for l in filtered_logs
                    if datetime.fromisoformat(l.get("timestamp", "")) >= start_dt
                ]
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                filtered_logs = [
                    l
                    for l in filtered_logs
                    if datetime.fromisoformat(l.get("timestamp", "")) <= end_dt
                ]
            except ValueError:
                pass

        filtered_logs.sort(
            key=lambda x: x.get("timestamp", ""), reverse=(sort_order == "desc")
        )

        total = len(filtered_logs)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_logs = filtered_logs[start_idx:end_idx]

        users = load_data("users.json")
        user_map = {u["id"]: u.get("username", "Unknown") for u in users}

        for log in paginated_logs:
            log["username"] = user_map.get(log.get("user_id"), "Unknown")

        log_access(
            current_user_id,
            "logs.access.view",
            "audit_logs",
            details={
                "filters_applied": bool(
                    user_id_filter or action_filter or resource_filter
                )
            },
        )

        return (
            jsonify(
                {
                    "logs": paginated_logs,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "total_pages": (total + per_page - 1) // per_page,
                    },
                    "filters": {
                        "user_id": user_id_filter,
                        "action": action_filter,
                        "resource": resource_filter,
                        "status": status_filter,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Access logs error: %s", e)
        return jsonify({"error": "Failed to retrieve access logs"}), 500


@admin_bp.route("/logs/access/stats", methods=["GET"])
@jwt_required()
@check_permission("admin")
def get_access_logs_stats():
    """監査ログの統計情報（管理者専用）"""
    try:
        current_user_id = get_jwt_identity()
        logs = load_data("access_logs.json")

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        total_logs = len(logs)
        today_logs = 0
        week_logs = 0
        action_counts = Counter()
        resource_counts = Counter()
        status_counts = Counter()
        user_activity = Counter()

        for log in logs:
            try:
                log_time = datetime.fromisoformat(log.get("timestamp", ""))

                if log_time >= today_start:
                    today_logs += 1
                if log_time >= week_start:
                    week_logs += 1

                action_counts[log.get("action", "unknown")] += 1
                resource_counts[log.get("resource") or "none"] += 1
                status_counts[log.get("status", "unknown")] += 1
                user_activity[log.get("user_id", 0)] += 1

            except (ValueError, TypeError):
                continue

        users = load_data("users.json")
        user_map = {u["id"]: u.get("username", "Unknown") for u in users}
        top_users = [
            {
                "user_id": uid,
                "username": user_map.get(uid, "Unknown"),
                "action_count": count,
            }
            for uid, count in user_activity.most_common(5)
        ]

        log_access(current_user_id, "logs.access.stats", "audit_logs")

        return (
            jsonify(
                {
                    "total_logs": total_logs,
                    "today_logs": today_logs,
                    "week_logs": week_logs,
                    "by_action": dict(action_counts.most_common(10)),
                    "by_resource": dict(resource_counts),
                    "by_status": dict(status_counts),
                    "top_active_users": top_users,
                    "generated_at": now.isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Access logs stats error: %s", e)
        return jsonify({"error": "Failed to retrieve access logs stats"}), 500


# ============================================================
# ヘルスチェックAPI
# ============================================================


@admin_bp.route("/health", methods=["GET"])
def health_check():
    """
    システムヘルスチェックエンドポイント

    Returns:
        JSON: システム状態（データベース、メモリ、CPU等）
    """
    try:
        try:
            from database import check_database_health, get_storage_mode

            db_health = check_database_health()
            storage_mode = get_storage_mode()
        except ImportError:
            db_health = {"mode": "json", "healthy": True}
            storage_mode = "json"

        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return jsonify(
            {
                "status": "healthy" if db_health.get("healthy", True) else "degraded",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "environment": os.environ.get("MKS_ENV", "development"),
                "database": db_health,
                "storage_mode": storage_mode,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available // (1024 * 1024),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free // (1024 * 1024 * 1024),
                },
            }
        ), (200 if db_health.get("healthy", True) else 503)

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@admin_bp.route("/health/db", methods=["GET"])
def db_health_check():
    """
    データベース専用ヘルスチェック

    Returns:
        JSON: データベース接続状態の詳細
    """
    try:
        from database import check_database_health, get_storage_mode

        health = check_database_health()
        return jsonify(
            {
                "healthy": health.get("healthy", False),
                "mode": health.get("mode", "unknown"),
                "details": health.get("details", {}),
                "timestamp": datetime.now().isoformat(),
            }
        ), (200 if health.get("healthy") else 503)
    except ImportError:
        return (
            jsonify(
                {
                    "healthy": True,
                    "mode": "json",
                    "details": {"message": "Using JSON backend"},
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            503,
        )
