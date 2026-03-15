"""
SocketIO ハンドラーのユニットテスト
Phase L-1: socketio_handlers.py のテストカバレッジ
"""
import pytest
from unittest.mock import MagicMock, patch
from socketio_handlers import (
    register_socketio_handlers,
    emit_project_progress_update,
    emit_dashboard_stats_update,
    emit_expert_stats_update,
)


class TestRegisterSocketioHandlers:
    """register_socketio_handlers のテスト"""

    def test_register_handlers_attaches_events(self):
        """SocketIO インスタンスにイベントハンドラーが登録される"""
        mock_socketio = MagicMock()
        register_socketio_handlers(mock_socketio)
        # @socketio.on() デコレータが呼ばれたことを確認
        assert mock_socketio.on.call_count >= 5

    def test_register_handlers_event_names(self):
        """正しいイベント名が登録される"""
        mock_socketio = MagicMock()
        register_socketio_handlers(mock_socketio)
        event_names = [call[0][0] for call in mock_socketio.on.call_args_list]
        assert "connect" in event_names
        assert "disconnect" in event_names
        assert "join_project" in event_names
        assert "leave_project" in event_names
        assert "join_dashboard" in event_names
        assert "leave_dashboard" in event_names


class TestEmitFunctions:
    """emit ユーティリティ関数のテスト"""

    def test_emit_project_progress_update(self):
        """プロジェクト進捗更新の送信"""
        mock_socketio = MagicMock()
        emit_project_progress_update(mock_socketio, "proj-1", {"percent": 75})
        mock_socketio.emit.assert_called_once()
        args = mock_socketio.emit.call_args
        assert args[0][0] == "project_progress_update"
        assert args[1]["to"] == "project_proj-1"
        data = args[0][1]
        assert data["project_id"] == "proj-1"
        assert data["progress"]["percent"] == 75
        assert "timestamp" in data

    def test_emit_dashboard_stats_update(self):
        """ダッシュボード統計更新の送信"""
        mock_socketio = MagicMock()
        stats = {"total_knowledge": 100, "active_users": 5}
        emit_dashboard_stats_update(mock_socketio, stats)
        mock_socketio.emit.assert_called_once()
        args = mock_socketio.emit.call_args
        assert args[0][0] == "dashboard_stats_update"
        assert args[1]["to"] == "dashboard"
        assert args[0][1]["stats"] == stats

    def test_emit_expert_stats_update(self):
        """専門家統計更新の送信"""
        mock_socketio = MagicMock()
        expert_stats = {"expert_count": 10, "response_rate": 0.85}
        emit_expert_stats_update(mock_socketio, expert_stats)
        mock_socketio.emit.assert_called_once()
        args = mock_socketio.emit.call_args
        assert args[0][0] == "expert_stats_update"
        assert args[1]["to"] == "dashboard"
        assert args[0][1]["expert_stats"] == expert_stats
