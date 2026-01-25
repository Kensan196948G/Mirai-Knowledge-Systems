"""
通知APIの統合テスト
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def _write_json(path, data):
    """JSONファイル書き込みヘルパー"""
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


@pytest.fixture()
def client(tmp_path):
    """テストクライアント"""
    import app_v2

    app = app_v2.app
    app.config['TESTING'] = True
    app.config['DATA_DIR'] = str(tmp_path)
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    app_v2.limiter.enabled = False

    # ユーザー設定
    users = [
        {
            'id': 1,
            'username': 'admin',
            'password_hash': app_v2.hash_password('admin123'),
            'full_name': 'Admin User',
            'department': 'Admin',
            'roles': ['admin']
        },
        {
            'id': 2,
            'username': 'manager',
            'password_hash': app_v2.hash_password('manager123'),
            'full_name': 'Construction Manager',
            'department': 'Construction',
            'roles': ['construction_manager']
        },
        {
            'id': 3,
            'username': 'qauser',
            'password_hash': app_v2.hash_password('qa123456'),
            'full_name': 'QA Engineer',
            'department': 'Quality',
            'roles': ['quality_assurance']
        }
    ]

    # 初期通知データ
    notifications = [
        {
            'id': 1,
            'title': '承認待ち通知',
            'message': 'ナレッジの承認をお願いします',
            'type': 'approval_required',
            'target_users': [],
            'target_roles': ['admin', 'quality_assurance'],
            'priority': 'high',
            'related_entity_type': 'knowledge',
            'related_entity_id': 1,
            'created_at': '2025-01-15T10:00:00',
            'status': 'sent',
            'read_by': []
        },
        {
            'id': 2,
            'title': '承認完了通知',
            'message': 'ナレッジが承認されました',
            'type': 'approval_completed',
            'target_users': [2],
            'target_roles': [],
            'priority': 'medium',
            'related_entity_type': 'knowledge',
            'related_entity_id': 1,
            'created_at': '2025-01-15T11:00:00',
            'status': 'sent',
            'read_by': []
        },
        {
            'id': 3,
            'title': '管理者専用通知',
            'message': '管理者のみに表示される通知',
            'type': 'system',
            'target_users': [],
            'target_roles': ['admin'],
            'priority': 'low',
            'related_entity_type': None,
            'related_entity_id': None,
            'created_at': '2025-01-15T12:00:00',
            'status': 'sent',
            'read_by': [1]  # 管理者は既読
        }
    ]

    _write_json(tmp_path / 'users.json', users)
    _write_json(tmp_path / 'notifications.json', notifications)
    _write_json(tmp_path / 'access_logs.json', [])
    _write_json(tmp_path / 'knowledge.json', [])

    with app.test_client() as test_client:
        yield test_client


def _login(client, username='admin', password='admin123'):
    """ログインヘルパー"""
    response = client.post(
        '/api/v1/auth/login',
        json={'username': username, 'password': password}
    )
    return response.get_json()['data']['access_token']


class TestGetNotifications:
    """通知一覧取得のテスト"""

    def test_get_notifications_returns_user_targeted_notifications(self, client):
        """ユーザーに宛てられた通知を取得"""
        token = _login(client, 'manager', 'manager123')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        # manager(id=2)宛ての通知は id=2 のみ
        assert any(n['id'] == 2 for n in data['data'])

    def test_get_notifications_returns_role_targeted_notifications(self, client):
        """ロールに宛てられた通知を取得"""
        token = _login(client)  # admin

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        # admin宛て通知（id=1, id=3）
        notification_ids = [n['id'] for n in data['data']]
        assert 1 in notification_ids
        assert 3 in notification_ids

    def test_get_notifications_requires_auth(self, client):
        """認証が必要"""
        response = client.get('/api/v1/notifications')

        assert response.status_code == 401

    def test_get_notifications_includes_is_read_flag(self, client):
        """既読フラグが含まれる"""
        token = _login(client)  # admin

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()

        for notification in data['data']:
            assert 'is_read' in notification

        # id=3は管理者が既読済み
        notification_3 = next(n for n in data['data'] if n['id'] == 3)
        assert notification_3['is_read'] is True

        # id=1は未読
        notification_1 = next(n for n in data['data'] if n['id'] == 1)
        assert notification_1['is_read'] is False

    def test_get_notifications_sorted_by_created_at_desc(self, client):
        """作成日時の降順でソート"""
        token = _login(client)

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()

        if len(data['data']) >= 2:
            dates = [n['created_at'] for n in data['data']]
            assert dates == sorted(dates, reverse=True)

    def test_get_notifications_includes_unread_count(self, client):
        """未読数が含まれる"""
        token = _login(client)

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data
        assert 'unread_count' in data['pagination']

    def test_qa_user_sees_approval_notifications(self, client):
        """QAユーザーは承認関連通知を見られる"""
        token = _login(client, 'qauser', 'qa123456')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        # quality_assurance向け通知（id=1）が含まれる
        notification_ids = [n['id'] for n in data['data']]
        assert 1 in notification_ids


class TestMarkNotificationRead:
    """通知既読化のテスト"""

    def test_mark_notification_as_read(self, client):
        """通知を既読にする"""
        token = _login(client)

        response = client.put(
            '/api/v1/notifications/1/read',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['id'] == 1
        assert data['data']['is_read'] is True

    def test_mark_notification_read_requires_auth(self, client):
        """認証が必要"""
        response = client.put('/api/v1/notifications/1/read')

        assert response.status_code == 401

    def test_mark_nonexistent_notification_returns_404(self, client):
        """存在しない通知は404を返す"""
        token = _login(client)

        response = client.put(
            '/api/v1/notifications/999/read',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 404

    def test_mark_read_persists(self, client, tmp_path):
        """既読状態が永続化される"""
        token = _login(client)

        # 既読にする
        client.put(
            '/api/v1/notifications/1/read',
            headers={'Authorization': f'Bearer {token}'}
        )

        # ファイルを確認
        notifications_file = tmp_path / 'notifications.json'
        with open(notifications_file, 'r', encoding='utf-8') as f:
            notifications = json.load(f)

        notification_1 = next(n for n in notifications if n['id'] == 1)
        assert 1 in notification_1['read_by']

    def test_mark_read_is_idempotent(self, client):
        """複数回既読にしても問題ない"""
        token = _login(client)

        # 2回既読にする
        client.put(
            '/api/v1/notifications/1/read',
            headers={'Authorization': f'Bearer {token}'}
        )
        response = client.put(
            '/api/v1/notifications/1/read',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200


class TestUnreadCount:
    """未読通知数取得のテスト"""

    def test_get_unread_count(self, client):
        """未読数を取得"""
        token = _login(client)

        response = client.get(
            '/api/v1/notifications/unread/count',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'unread_count' in data['data']
        # admin向け通知は id=1, 3 で id=3は既読なので未読は1件
        assert data['data']['unread_count'] == 1

    def test_get_unread_count_requires_auth(self, client):
        """認証が必要"""
        response = client.get('/api/v1/notifications/unread/count')

        assert response.status_code == 401

    def test_unread_count_decreases_after_read(self, client):
        """既読後に未読数が減少"""
        token = _login(client)

        # 初期未読数
        response1 = client.get(
            '/api/v1/notifications/unread/count',
            headers={'Authorization': f'Bearer {token}'}
        )
        initial_count = response1.get_json()['data']['unread_count']

        # 通知を既読に
        client.put(
            '/api/v1/notifications/1/read',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 再度未読数を取得
        response2 = client.get(
            '/api/v1/notifications/unread/count',
            headers={'Authorization': f'Bearer {token}'}
        )
        new_count = response2.get_json()['data']['unread_count']

        assert new_count == initial_count - 1


class TestCreateNotificationFunction:
    """create_notification関数のテスト"""

    def test_create_notification_adds_to_file(self, client, tmp_path):
        """通知がファイルに追加される"""
        import app_v2

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        # 既存の通知をロード
        notifications_file = tmp_path / 'notifications.json'
        with open(notifications_file, 'r', encoding='utf-8') as f:
            initial_notifications = json.load(f)
        initial_count = len(initial_notifications)

        # 新規通知作成
        new_notification = app_v2.create_notification(
            title='テスト通知',
            message='テストメッセージ',
            type='test_type',
            target_users=[1, 2],
            target_roles=['admin'],
            priority='high',
            related_entity_type='test',
            related_entity_id=99
        )

        # ファイルを確認
        with open(notifications_file, 'r', encoding='utf-8') as f:
            updated_notifications = json.load(f)

        assert len(updated_notifications) == initial_count + 1
        assert new_notification['title'] == 'テスト通知'
        assert new_notification['target_users'] == [1, 2]
        assert new_notification['target_roles'] == ['admin']
        assert new_notification['priority'] == 'high'

    def test_create_notification_auto_increments_id(self, client, tmp_path):
        """通知IDは自動インクリメント"""
        import app_v2

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        # 2つの通知を作成
        notification1 = app_v2.create_notification(
            title='通知1',
            message='メッセージ1',
            type='test'
        )
        notification2 = app_v2.create_notification(
            title='通知2',
            message='メッセージ2',
            type='test'
        )

        assert notification2['id'] > notification1['id']

    def test_create_notification_sets_defaults(self, client, tmp_path):
        """デフォルト値が設定される"""
        import app_v2

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        notification = app_v2.create_notification(
            title='シンプル通知',
            message='メッセージ',
            type='simple'
        )

        assert notification['target_users'] == []
        assert notification['target_roles'] == []
        assert notification['status'] == 'sent'
        assert notification['read_by'] == []
        assert 'created_at' in notification


class TestNotificationFiltering:
    """通知フィルタリングのテスト"""

    def test_user_only_sees_relevant_notifications(self, client):
        """ユーザーは自分宛ての通知のみ見られる"""
        # managerとしてログイン
        token = _login(client, 'manager', 'manager123')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()

        # manager(id=2)向け通知のみ
        for notification in data['data']:
            is_targeted_user = 2 in notification.get('target_users', [])
            is_targeted_role = any(
                role in notification.get('target_roles', [])
                for role in ['construction_manager']
            )
            assert is_targeted_user or is_targeted_role

    def test_empty_notifications_for_new_user(self, client, tmp_path):
        """新規ユーザーに対する通知がない場合は空リスト"""
        import app_v2

        # 新規ユーザーを追加（ロールなし）
        users_file = tmp_path / 'users.json'
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)

        users.append({
            'id': 99,
            'username': 'newuser',
            'password_hash': app_v2.hash_password('newuser123'),
            'full_name': 'New User',
            'department': 'New',
            'roles': []
        })

        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

        token = _login(client, 'newuser', 'newuser123')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data'] == []
        assert data['pagination']['unread_count'] == 0
