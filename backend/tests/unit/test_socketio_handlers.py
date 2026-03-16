"""
SocketIO ハンドラーのユニットテスト
Phase L-1: socketio_handlers.py のテストカバレッジ
"""
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from flask_socketio import SocketIO
from socketio_handlers import (
    register_socketio_handlers,
    emit_project_progress_update,
    emit_dashboard_stats_update,
    emit_expert_stats_update,
)


# ---------------------------------------------------------------------------
# テスト用フィクスチャ
# ---------------------------------------------------------------------------

@pytest.fixture()
def sio_app():
    """SocketIO ハンドラーを登録した最小限の Flask アプリ"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    sio = SocketIO(app)
    register_socketio_handlers(sio)
    return app, sio


@pytest.fixture()
def sio_client(sio_app):
    """Flask-SocketIO テストクライアント"""
    app, sio = sio_app
    with app.test_request_context():
        tc = sio.test_client(app)
        yield tc
        if tc.is_connected():
            tc.disconnect()


# ---------------------------------------------------------------------------
# TestRegisterSocketioHandlers: ハンドラー登録確認
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TestSocketioHandlerBehavior: 実際のイベント発火テスト
# ---------------------------------------------------------------------------

class TestSocketioHandlerBehavior:
    """Flask-SocketIO テストクライアントを使った実際のハンドラー動作テスト"""

    def test_connect_emits_connected(self, sio_app):
        """接続時に connected イベントが発行される"""
        app, sio = sio_app
        client = sio.test_client(app)
        received = client.get_received()
        assert any(e["name"] == "connected" for e in received)
        client.disconnect()

    def test_connect_status_success(self, sio_app):
        """接続時の connected イベントのステータスが success"""
        app, sio = sio_app
        client = sio.test_client(app)
        received = client.get_received()
        connected_events = [e for e in received if e["name"] == "connected"]
        assert len(connected_events) > 0
        assert connected_events[0]["args"][0]["status"] == "success"
        client.disconnect()

    def test_disconnect(self, sio_app):
        """切断処理が正常に完了する"""
        app, sio = sio_app
        client = sio.test_client(app)
        assert client.is_connected()
        client.disconnect()
        assert not client.is_connected()

    def test_join_project_with_project_id(self, sio_app):
        """プロジェクト参加イベントで joined_project が返される"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()  # 接続イベントをクリア

        client.emit("join_project", {"project_id": "proj-42"})
        received = client.get_received()
        assert any(e["name"] == "joined_project" for e in received)
        client.disconnect()

    def test_join_project_returns_project_id(self, sio_app):
        """joined_project イベントに project_id が含まれる"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()

        client.emit("join_project", {"project_id": "my-project"})
        received = client.get_received()
        joined = [e for e in received if e["name"] == "joined_project"]
        assert len(joined) == 1
        assert joined[0]["args"][0]["project_id"] == "my-project"
        client.disconnect()

    def test_join_project_without_project_id(self, sio_app):
        """project_id なしの join_project は joined_project を返さない"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()

        client.emit("join_project", {})
        received = client.get_received()
        assert not any(e["name"] == "joined_project" for e in received)
        client.disconnect()

    def test_leave_project_with_project_id(self, sio_app):
        """プロジェクト退出イベントが処理される（emit なし）"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()

        # まずルームに参加
        client.emit("join_project", {"project_id": "proj-99"})
        client.get_received()  # joined_project をクリア

        # 退出
        client.emit("leave_project", {"project_id": "proj-99"})
        received = client.get_received()
        # leave_project は emit を返さない（正常動作）
        assert not any(e["name"] == "left_project" for e in received)
        client.disconnect()

    def test_leave_project_without_project_id(self, sio_app):
        """project_id なしの leave_project は何も発行しない"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()

        client.emit("leave_project", {})
        received = client.get_received()
        assert len(received) == 0
        client.disconnect()

    def test_join_dashboard(self, sio_app):
        """ダッシュボード参加イベントで joined_dashboard が返される"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()

        client.emit("join_dashboard")
        received = client.get_received()
        assert any(e["name"] == "joined_dashboard" for e in received)
        client.disconnect()

    def test_join_dashboard_status(self, sio_app):
        """joined_dashboard イベントのステータスが success"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()

        client.emit("join_dashboard")
        received = client.get_received()
        joined = [e for e in received if e["name"] == "joined_dashboard"]
        assert len(joined) == 1
        assert joined[0]["args"][0]["status"] == "success"
        client.disconnect()

    def test_leave_dashboard(self, sio_app):
        """ダッシュボード退出イベントが処理される（emit なし）"""
        app, sio = sio_app
        client = sio.test_client(app)
        client.get_received()

        # まず参加
        client.emit("join_dashboard")
        client.get_received()

        # 退出
        client.emit("leave_dashboard")
        received = client.get_received()
        # leave_dashboard は emit を返さない（正常動作）
        assert not any(e["name"] == "left_dashboard" for e in received)
        client.disconnect()


# ---------------------------------------------------------------------------
# TestEmitFunctions: ユーティリティ emit 関数
# ---------------------------------------------------------------------------

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

    def test_emit_project_progress_update_timestamp_format(self):
        """プロジェクト進捗更新のタイムスタンプが ISO 形式"""
        mock_socketio = MagicMock()
        emit_project_progress_update(mock_socketio, "proj-2", {"percent": 50})
        data = mock_socketio.emit.call_args[0][1]
        # ISO 8601 形式の文字列であることを確認
        from datetime import datetime
        dt = datetime.fromisoformat(data["timestamp"])
        assert dt is not None

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

    def test_emit_dashboard_stats_update_timestamp(self):
        """ダッシュボード統計更新のタイムスタンプが存在する"""
        mock_socketio = MagicMock()
        emit_dashboard_stats_update(mock_socketio, {})
        data = mock_socketio.emit.call_args[0][1]
        assert "timestamp" in data

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

    def test_emit_expert_stats_update_timestamp(self):
        """専門家統計更新のタイムスタンプが存在する"""
        mock_socketio = MagicMock()
        emit_expert_stats_update(mock_socketio, {"count": 3})
        data = mock_socketio.emit.call_args[0][1]
        assert "timestamp" in data

    def test_emit_project_progress_uses_correct_room(self):
        """プロジェクト進捗更新が正しいルームに送信される"""
        mock_socketio = MagicMock()
        emit_project_progress_update(mock_socketio, "abc-123", {})
        assert mock_socketio.emit.call_args[1]["to"] == "project_abc-123"

    def test_emit_dashboard_stats_uses_dashboard_room(self):
        """ダッシュボード統計が dashboard ルームに送信される"""
        mock_socketio = MagicMock()
        emit_dashboard_stats_update(mock_socketio, {"key": "val"})
        assert mock_socketio.emit.call_args[1]["to"] == "dashboard"

    def test_emit_expert_stats_uses_dashboard_room(self):
        """専門家統計が dashboard ルームに送信される"""
        mock_socketio = MagicMock()
        emit_expert_stats_update(mock_socketio, {"rate": 0.9})
        assert mock_socketio.emit.call_args[1]["to"] == "dashboard"
