"""
RBAC(Role-Based Access Control)統合テスト
ロールベースのアクセス制御フロー全体をテスト
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

    # 各ロールのユーザー設定
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
            'username': 'const_mgr',
            'password_hash': app_v2.hash_password('const123'),
            'full_name': 'Construction Manager',
            'department': 'Construction',
            'roles': ['construction_manager']
        },
        {
            'id': 3,
            'username': 'qa_user',
            'password_hash': app_v2.hash_password('qa123456'),
            'full_name': 'QA User',
            'department': 'Quality',
            'roles': ['quality_assurance']
        },
        {
            'id': 4,
            'username': 'safety_user',
            'password_hash': app_v2.hash_password('safety123'),
            'full_name': 'Safety Officer',
            'department': 'Safety',
            'roles': ['safety_officer']
        },
        {
            'id': 5,
            'username': 'partner',
            'password_hash': app_v2.hash_password('partner123'),
            'full_name': 'Partner User',
            'department': 'External',
            'roles': ['partner_company']
        }
    ]

    # テスト用ナレッジ
    knowledge = [
        {
            'id': 1,
            'title': 'Test Knowledge',
            'summary': 'Summary',
            'content': 'Content',
            'category': 'safety',
            'tags': [],
            'status': 'approved'
        }
    ]

    _write_json(tmp_path / 'users.json', users)
    _write_json(tmp_path / 'knowledge.json', knowledge)
    _write_json(tmp_path / 'access_logs.json', [])
    _write_json(tmp_path / 'notifications.json', [])

    with app.test_client() as test_client:
        yield test_client


def _login(client, username, password):
    """ログインヘルパー"""
    response = client.post(
        '/api/v1/auth/login',
        json={'username': username, 'password': password}
    )
    return response.get_json()['data']['access_token']


class TestAdminRolePermissions:
    """管理者ロールの権限テスト"""

    def test_admin_can_read_knowledge(self, client):
        """管理者はナレッジを読める"""
        token = _login(client, 'admin', 'admin123')

        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200

    def test_admin_can_create_knowledge(self, client):
        """管理者はナレッジを作成できる"""
        token = _login(client, 'admin', 'admin123')

        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': '管理者作成ナレッジ',
                'summary': '概要',
                'content': 'コンテンツの詳細内容',
                'category': '施工計画'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201

    def test_admin_can_update_knowledge(self, client):
        """管理者はナレッジを更新できる"""
        token = _login(client, 'admin', 'admin123')

        response = client.put(
            '/api/v1/knowledge/1',
            json={'title': '更新後'},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200

    def test_admin_can_delete_knowledge(self, client):
        """管理者はナレッジを削除できる"""
        token = _login(client, 'admin', 'admin123')

        response = client.delete(
            '/api/v1/knowledge/1',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200


class TestConstructionManagerRolePermissions:
    """建設マネージャーロールの権限テスト"""

    def test_construction_manager_can_read_knowledge(self, client):
        """建設マネージャーはナレッジを読める"""
        token = _login(client, 'const_mgr', 'const123')

        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200

    def test_construction_manager_can_create_knowledge(self, client):
        """建設マネージャーはナレッジを作成できる"""
        token = _login(client, 'const_mgr', 'const123')

        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': 'マネージャー作成ナレッジ',
                'summary': '概要',
                'content': 'コンテンツの詳細',
                'category': '施工計画'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201

    def test_construction_manager_can_update_knowledge(self, client):
        """建設マネージャーはナレッジを更新できる"""
        token = _login(client, 'const_mgr', 'const123')

        response = client.put(
            '/api/v1/knowledge/1',
            json={'title': '更新後'},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200


class TestQualityAssuranceRolePermissions:
    """品質保証ロールの権限テスト"""

    def test_qa_can_read_knowledge(self, client):
        """QAはナレッジを読める"""
        token = _login(client, 'qa_user', 'qa123456')

        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200

    def test_qa_can_create_knowledge(self, client):
        """QAはナレッジを作成できる"""
        token = _login(client, 'qa_user', 'qa123456')

        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': 'QA作成ナレッジ',
                'summary': '概要',
                'content': 'コンテンツ',
                'category': '品質管理'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201


class TestSafetyOfficerRolePermissions:
    """安全管理者ロールの権限テスト"""

    def test_safety_officer_can_read_knowledge(self, client):
        """安全管理者はナレッジを読める"""
        token = _login(client, 'safety_user', 'safety123')

        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200

    def test_safety_officer_can_create_knowledge(self, client):
        """安全管理者はナレッジを作成できる"""
        token = _login(client, 'safety_user', 'safety123')

        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': '安全ナレッジ',
                'summary': '概要',
                'content': 'コンテンツ',
                'category': '安全衛生'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201


class TestPartnerCompanyRolePermissions:
    """協力会社ロールの権限テスト（読み取り専用）"""

    def test_partner_can_read_knowledge(self, client):
        """協力会社はナレッジを読める"""
        token = _login(client, 'partner', 'partner123')

        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200

    def test_partner_cannot_create_knowledge(self, client):
        """協力会社はナレッジを作成できない"""
        token = _login(client, 'partner', 'partner123')

        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': 'パートナー作成ナレッジ',
                'summary': '概要',
                'content': 'コンテンツ',
                'category': '施工計画'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 403
        data = response.get_json()
        assert 'FORBIDDEN' in data['error']['code']

    def test_partner_cannot_update_knowledge(self, client):
        """協力会社はナレッジを更新できない"""
        token = _login(client, 'partner', 'partner123')

        response = client.put(
            '/api/v1/knowledge/1',
            json={'title': '更新後'},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 403

    def test_partner_cannot_delete_knowledge(self, client):
        """協力会社はナレッジを削除できない"""
        token = _login(client, 'partner', 'partner123')

        response = client.delete(
            '/api/v1/knowledge/1',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 403


class TestRoleBasedNotifications:
    """ロールベースの通知配信テスト"""

    def test_admin_receives_approval_notifications(self, client):
        """管理者は承認通知を受け取る"""
        # 承認が必要な通知を作成
        import app_v2
        app_v2.app.config['DATA_DIR'] = client.application.config['DATA_DIR']

        notification = app_v2.create_notification(
            title='承認要求',
            message='承認が必要です',
            type='approval_required',
            target_roles=['admin']
        )

        token = _login(client, 'admin', 'admin123')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        notification_ids = [n['id'] for n in data['data']]
        assert notification['id'] in notification_ids

    def test_qa_receives_quality_notifications(self, client):
        """QAは品質関連通知を受け取る"""
        import app_v2
        app_v2.app.config['DATA_DIR'] = client.application.config['DATA_DIR']

        notification = app_v2.create_notification(
            title='品質問題',
            message='品質確認が必要です',
            type='quality_issue',
            target_roles=['quality_assurance']
        )

        token = _login(client, 'qa_user', 'qa123456')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        notification_ids = [n['id'] for n in data['data']]
        assert notification['id'] in notification_ids

    def test_partner_does_not_receive_internal_notifications(self, client):
        """協力会社は内部通知を受け取らない"""
        import app_v2
        app_v2.app.config['DATA_DIR'] = client.application.config['DATA_DIR']

        # 内部向け通知
        app_v2.create_notification(
            title='内部通知',
            message='内部のみ',
            type='internal',
            target_roles=['admin', 'construction_manager']
        )

        token = _login(client, 'partner', 'partner123')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        # パートナーには表示されない
        internal_notifications = [n for n in data['data'] if n['type'] == 'internal']
        assert len(internal_notifications) == 0


class TestMultiRoleUser:
    """複数ロールを持つユーザーのテスト"""

    def test_user_with_multiple_roles_has_combined_permissions(self, client, tmp_path):
        """複数ロールを持つユーザーは統合された権限を持つ"""
        import app_v2

        # 複数ロールを持つユーザーを追加
        users_file = tmp_path / 'users.json'
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)

        users.append({
            'id': 99,
            'username': 'multi_role',
            'password_hash': app_v2.hash_password('multi123'),
            'full_name': 'Multi Role User',
            'department': 'Multiple',
            'roles': ['construction_manager', 'quality_assurance']
        })

        _write_json(users_file, users)

        token = _login(client, 'multi_role', 'multi123')

        # 両方のロールの権限を持つ
        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': 'マルチロールナレッジ',
                'summary': '概要',
                'content': 'コンテンツ',
                'category': '施工計画'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201

    def test_user_with_multiple_roles_receives_all_notifications(self, client, tmp_path):
        """複数ロールを持つユーザーは全ての関連通知を受け取る"""
        import app_v2

        # 複数ロールユーザー追加
        users_file = tmp_path / 'users.json'
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)

        users.append({
            'id': 98,
            'username': 'multi_notif',
            'password_hash': app_v2.hash_password('multi456'),
            'full_name': 'Multi Notification User',
            'department': 'Multiple',
            'roles': ['construction_manager', 'safety_officer']
        })

        _write_json(users_file, users)

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        # 建設マネージャー向け通知
        notif1 = app_v2.create_notification(
            title='建設通知',
            message='建設関連',
            type='construction',
            target_roles=['construction_manager']
        )

        # 安全管理者向け通知
        notif2 = app_v2.create_notification(
            title='安全通知',
            message='安全関連',
            type='safety',
            target_roles=['safety_officer']
        )

        token = _login(client, 'multi_notif', 'multi456')

        response = client.get(
            '/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        notification_ids = [n['id'] for n in data['data']]

        # 両方の通知を受け取る
        assert notif1['id'] in notification_ids
        assert notif2['id'] in notification_ids
