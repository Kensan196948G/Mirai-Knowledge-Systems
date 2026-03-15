"""
SocketIO イベントハンドラー（リアルタイム更新）
Phase L-1: app_v2.py から抽出

建設土木ナレッジシステムのリアルタイム通信機能を提供する。
プロジェクト進捗、ダッシュボード統計、専門家統計のリアルタイム更新を
WebSocket 経由でクライアントに配信する。
"""

import logging
from datetime import datetime

from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)


def register_socketio_handlers(socketio):
    """SocketIO イベントハンドラーを登録する

    Args:
        socketio: Flask-SocketIO インスタンス
    """

    @socketio.on("connect")
    def handle_connect():
        """クライアント接続時の処理"""
        logger.debug("[SOCKET] Client connected")
        emit("connected", {"status": "success"})

    @socketio.on("disconnect")
    def handle_disconnect():
        """クライアント切断時の処理"""
        logger.debug("[SOCKET] Client disconnected")

    @socketio.on("join_project")
    def handle_join_project(data):
        """プロジェクトルーム参加"""
        project_id = data.get("project_id")
        if project_id:
            join_room(f"project_{project_id}")
            logger.debug("[SOCKET] User joined project room: %s", project_id)
            emit("joined_project", {"project_id": project_id})

    @socketio.on("leave_project")
    def handle_leave_project(data):
        """プロジェクトルーム退出"""
        project_id = data.get("project_id")
        if project_id:
            leave_room(f"project_{project_id}")
            logger.debug("[SOCKET] User left project room: %s", project_id)

    @socketio.on("join_dashboard")
    def handle_join_dashboard():
        """ダッシュボードルーム参加"""
        join_room("dashboard")
        logger.debug("[SOCKET] User joined dashboard room")
        emit("joined_dashboard", {"status": "success"})

    @socketio.on("leave_dashboard")
    def handle_leave_dashboard():
        """ダッシュボードルーム退出"""
        leave_room("dashboard")
        logger.debug("[SOCKET] User left dashboard room")


def emit_project_progress_update(socketio, project_id, progress_data):
    """プロジェクト進捗更新をリアルタイム通知"""
    socketio.emit(
        "project_progress_update",
        {
            "project_id": project_id,
            "progress": progress_data,
            "timestamp": datetime.now().isoformat(),
        },
        to=f"project_{project_id}",
    )


def emit_dashboard_stats_update(socketio, stats_data):
    """ダッシュボード統計更新をリアルタイム通知"""
    socketio.emit(
        "dashboard_stats_update",
        {"stats": stats_data, "timestamp": datetime.now().isoformat()},
        to="dashboard",
    )


def emit_expert_stats_update(socketio, expert_stats):
    """専門家統計更新をリアルタイム通知"""
    socketio.emit(
        "expert_stats_update",
        {"expert_stats": expert_stats, "timestamp": datetime.now().isoformat()},
        to="dashboard",
    )
