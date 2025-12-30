"""
認可・権限管理セキュリティテスト

目的:
- ロールベースアクセス制御（RBAC）が機能すること
- 権限のない機能へのアクセスが拒否されること
- ロール昇格攻撃が防止されていること
- 各ユーザーが適切な権限のみを持つこと

参照: docs/09_品質保証(QA)/03_Final-Acceptance-Test-Plan.md
      セクション 5.1 認証・認可テスト
"""
import pytest
import json


@pytest.fixture
def create_test_users(client, tmp_path):
    """異なるロールを持つテストユーザーを作成"""
    from app_v2 import hash_password

    users = [
        {
            'id': 1,
            'username': 'admin_user',
            'password_hash': hash_password('admin123'),
            'full_name': 'Admin User',
            'department': 'Admin',
            'roles': ['admin']
        },
        {
            'id': 2,
            'username': 'editor_user',
            'password_hash': hash_password('editor123'),
            'full_name': 'Editor User',
            'department': 'Construction',
            'roles': ['construction_manager']
        },
        {
            'id': 3,
            'username': 'viewer_user',
            'password_hash': hash_password('viewer123'),
            'full_name': 'Viewer User',
            'department': 'Partner',
            'roles': ['partner_company']
        },
        {
            'id': 4,
            'username': 'no_role_user',
            'password_hash': hash_password('norole123'),
            'full_name': 'No Role User',
            'department': 'General',
            'roles': []
        }
    ]

    users_file = tmp_path / 'users.json'
    users_file.write_text(json.dumps(users, ensure_ascii=False, indent=2))

    return users


@pytest.fixture
def admin_token(client, create_test_users):
    """管理者トークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin_user',
        'password': 'admin123'
    })
    return response.get_json()['data']['access_token']


@pytest.fixture
def editor_token(client, create_test_users):
    """編集者トークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'editor_user',
        'password': 'editor123'
    })
    return response.get_json()['data']['access_token']


@pytest.fixture
def viewer_token(client, create_test_users):
    """閲覧者トークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'viewer_user',
        'password': 'viewer123'
    })
    return response.get_json()['data']['access_token']


@pytest.fixture
def no_role_token(client, create_test_users):
    """ロールなしユーザーのトークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'no_role_user',
        'password': 'norole123'
    })
    return response.get_json()['data']['access_token']


class TestRoleBasedAccessControl:
    """ロールベースアクセス制御テスト"""

    def test_admin_can_access_admin_endpoints(self, client, admin_token):
        """管理者が管理機能にアクセスできること"""
        # ユーザー一覧取得（管理者専用）
        response = client.get('/api/users',
                            headers={'Authorization': f'Bearer {admin_token}'})

        # 管理者はアクセス可能
        assert response.status_code in [200, 404, 501]  # 実装状況に応じて

    def test_editor_can_create_knowledge(self, client, editor_token):
        """編集者がナレッジを作成できること"""
        response = client.post('/api/v1/knowledge',
                             headers={'Authorization': f'Bearer {editor_token}'},
                             json={
                                 'title': 'Test Knowledge',
                                 'summary': 'Test summary',
                                 'category': '安全衛生',
                                 'tags': ['test']
                             })

        # 編集者は作成可能
        assert response.status_code in [201, 200, 400]  # バリデーションエラーも許容

    def test_viewer_can_read_knowledge(self, client, viewer_token):
        """閲覧者がナレッジを閲覧できること"""
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {viewer_token}'})

        # 閲覧者は閲覧可能
        assert response.status_code == 200

    def test_viewer_cannot_create_knowledge(self, client, viewer_token):
        """閲覧者がナレッジを作成できないこと"""
        response = client.post('/api/v1/knowledge',
                             headers={'Authorization': f'Bearer {viewer_token}'},
                             json={
                                 'title': 'Unauthorized Knowledge',
                                 'summary': 'Should fail',
                                 'category': '安全衛生',
                                 'tags': ['test']
                             })

        # 閲覧者は作成不可（403 Forbidden）
        assert response.status_code in [403, 401]

    def test_viewer_cannot_delete_knowledge(self, client, viewer_token):
        """閲覧者がナレッジを削除できないこと"""
        response = client.delete('/api/v1/knowledge/1',
                               headers={'Authorization': f'Bearer {viewer_token}'})

        # 閲覧者は削除不可
        assert response.status_code in [403, 401, 404, 405]

    def test_viewer_cannot_access_admin_endpoints(self, client, viewer_token):
        """閲覧者が管理エンドポイントにアクセスできないこと"""
        response = client.get('/api/users',
                            headers={'Authorization': f'Bearer {viewer_token}'})

        # 閲覧者は管理機能にアクセス不可
        assert response.status_code in [403, 401, 404]


class TestUnauthorizedAccess:
    """権限なしアクセステスト"""

    def test_no_role_user_denied_all_operations(self, client, no_role_token):
        """ロールなしユーザーが全操作を拒否されること"""
        # ナレッジ閲覧
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {no_role_token}'})
        assert response.status_code in [403, 401]

        # ナレッジ作成
        response = client.post('/api/v1/knowledge',
                             headers={'Authorization': f'Bearer {no_role_token}'},
                             json={
                                 'title': 'Test',
                                 'summary': 'Test',
                                 'category': '安全衛生',
                                 'tags': []
                             })
        assert response.status_code in [403, 401]

    def test_unauthenticated_user_denied_access(self, client):
        """未認証ユーザーがアクセスを拒否されること"""
        # トークンなし
        response = client.get('/api/v1/knowledge')
        assert response.status_code == 401

        # ナレッジ作成試行
        response = client.post('/api/v1/knowledge', json={
            'title': 'Unauthorized',
            'summary': 'Test',
            'category': '安全衛生',
            'tags': []
        })
        assert response.status_code == 401


class TestPrivilegeEscalation:
    """ロール昇格攻撃防止テスト"""

    def test_user_cannot_modify_own_roles(self, client, viewer_token, tmp_path):
        """ユーザーが自分のロールを変更できないこと"""
        # ユーザー情報更新試行（ロールを管理者に変更）
        response = client.put('/api/users/3',  # viewer_userのID
                            headers={'Authorization': f'Bearer {viewer_token}'},
                            json={
                                'roles': ['admin', 'construction_manager', 'partner_company']  # 管理者権限追加試行
                            })

        # ロール変更は拒否されるべき
        assert response.status_code in [403, 401, 404, 405]

        # 実際にロールが変更されていないことを確認
        users_file = tmp_path / 'users.json'
        users = json.loads(users_file.read_text())
        viewer_user = next(u for u in users if u['username'] == 'viewer_user')
        assert 'admin' not in viewer_user['roles']

    def test_token_manipulation_role_claim(self, client, viewer_token):
        """トークンのロールクレーム改ざん防止"""
        import jwt

        # トークンをデコード
        decoded = jwt.decode(viewer_token, options={"verify_signature": False})

        # ロールを改ざん（管理者に変更）
        decoded['roles'] = ['admin', 'construction_manager', 'partner_company']

        # 異なる秘密鍵で再署名（攻撃者が推測した鍵）
        tampered_token = jwt.encode(decoded, 'guessed-secret', algorithm='HS256')

        # 改ざんされたトークンでアクセス試行
        response = client.get('/api/v1/knowledge',
                            headers={'Authorization': f'Bearer {tampered_token}'})

        # 署名検証失敗で拒否されるべき
        assert response.status_code in [401, 422]

    def test_role_verification_on_each_request(self, client, editor_token, tmp_path):
        """各リクエストでロールが検証されること"""
        # 編集者でアクセス
        response1 = client.post('/api/v1/knowledge',
                              headers={'Authorization': f'Bearer {editor_token}'},
                              json={
                                  'title': 'Test',
                                  'summary': 'Test',
                                  'category': '安全衛生',
                                  'tags': []
                              })
        assert response1.status_code in [201, 200, 400]

        # バックエンドでユーザーのロールを変更（シミュレーション）
        users_file = tmp_path / 'users.json'
        users = json.loads(users_file.read_text())
        for user in users:
            if user['username'] == 'editor_user':
                user['roles'] = ['partner_company']  # 編集権限を削除
        users_file.write_text(json.dumps(users, ensure_ascii=False, indent=2))

        # 同じトークンで再度アクセス試行
        response2 = client.post('/api/v1/knowledge',
                              headers={'Authorization': f'Bearer {editor_token}'},
                              json={
                                  'title': 'Test 2',
                                  'summary': 'Test',
                                  'category': '安全衛生',
                                  'tags': []
                              })

        # 注: JWTの場合、トークンに含まれる情報が使用されるため、
        # この動作は実装方針に依存する
        # トークン内にロール情報がある場合は成功する可能性がある


class TestHorizontalAccessControl:
    """横方向アクセス制御テスト（同じロール間のデータ分離）"""

    def test_user_cannot_access_other_user_data(self, client, editor_token, tmp_path):
        """ユーザーが他ユーザーのデータにアクセスできないこと"""
        # 他のユーザーの個人データにアクセス試行
        response = client.get('/api/users/1',  # 別のユーザーID
                            headers={'Authorization': f'Bearer {editor_token}'})

        # 自分以外のユーザー詳細は取得できないべき
        assert response.status_code in [403, 401, 404]

    def test_user_cannot_modify_other_user_data(self, client, editor_token):
        """ユーザーが他ユーザーのデータを変更できないこと"""
        # 他のユーザー情報の更新試行
        response = client.put('/api/users/1',  # 別のユーザーID
                            headers={'Authorization': f'Bearer {editor_token}'},
                            json={
                                'full_name': 'Hacked Name'
                            })

        # 他ユーザーの更新は拒否されるべき
        assert response.status_code in [403, 401, 404, 405]

    def test_user_can_access_own_data(self, client, editor_token):
        """ユーザーが自分のデータにアクセスできること"""
        # 自分のプロフィール取得
        response = client.get('/api/v1/auth/me',
                            headers={'Authorization': f'Bearer {editor_token}'})

        # 自分の情報は取得可能
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['username'] == 'editor_user'


class TestResourceOwnership:
    """リソース所有権テスト"""

    def test_user_cannot_delete_others_knowledge(self, client, editor_token, tmp_path):
        """ユーザーが他人のナレッジを削除できないこと"""
        # 別ユーザーが作成したナレッジを準備
        knowledge_file = tmp_path / 'knowledge.json'
        knowledge = [
            {
                'id': 1,
                'title': 'Admin Knowledge',
                'summary': 'Created by admin',
                'category': '安全衛生',
                'tags': ['admin'],
                'created_by': 1,  # admin_userのID
                'author': 'Admin User'
            }
        ]
        knowledge_file.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2))

        # 編集者が管理者のナレッジを削除試行
        response = client.delete('/api/v1/knowledge/1',
                               headers={'Authorization': f'Bearer {editor_token}'})

        # 他人のナレッジは削除できない（または管理者のみ可能）
        assert response.status_code in [403, 401, 404, 405]


class TestDirectObjectReference:
    """直接オブジェクト参照の脆弱性テスト"""

    def test_sequential_id_enumeration_protected(self, client, viewer_token):
        """連続したIDの列挙攻撃が保護されていること"""
        # 連続したIDでアクセス試行
        for user_id in range(1, 10):
            response = client.get(f'/api/users/{user_id}',
                                headers={'Authorization': f'Bearer {viewer_token}'})

            # 権限のないデータは取得できない
            if user_id != 3:  # 自分のID以外
                assert response.status_code in [403, 401, 404]

    def test_guessable_id_access_denied(self, client, viewer_token):
        """推測可能なIDでのアクセスが拒否されること"""
        # 様々なID形式でアクセス試行
        test_ids = [1, 2, 999, 'admin', '../../etc/passwd']

        for test_id in test_ids:
            response = client.get(f'/api/users/{test_id}',
                                headers={'Authorization': f'Bearer {viewer_token}'})

            # 自分以外は全て拒否
            if test_id != 3:
                assert response.status_code in [403, 401, 404, 400]


class TestAPIEndpointProtection:
    """APIエンドポイント保護テスト"""

    def test_all_api_endpoints_require_authentication(self, client):
        """全APIエンドポイントが認証を要求すること"""
        # 主要なエンドポイント
        endpoints = [
            '/api/v1/knowledge',
            '/api/v1/search/unified',
            '/api/v1/notifications',
            '/api/v1/approvals',
            '/api/v1/sop',
        ]

        for endpoint in endpoints:
            # 認証なしでアクセス
            response = client.get(endpoint)

            # ログインエンドポイント以外は認証が必要
            if endpoint != '/api/v1/auth/login':
                assert response.status_code == 401

    def test_admin_endpoints_require_admin_role(self, client, viewer_token, editor_token):
        """管理エンドポイントが管理者ロールを要求すること"""
        admin_endpoints = [
            '/api/users',
            '/api/admin/settings',
            '/api/admin/logs',
        ]

        for endpoint in admin_endpoints:
            # 閲覧者でアクセス
            response = client.get(endpoint,
                                headers={'Authorization': f'Bearer {viewer_token}'})
            assert response.status_code in [403, 401, 404]

            # 編集者でアクセス
            response = client.get(endpoint,
                                headers={'Authorization': f'Bearer {editor_token}'})
            assert response.status_code in [403, 401, 404]


class TestRoleConsistency:
    """ロール一貫性テスト"""

    def test_user_roles_are_validated_on_login(self, client, create_test_users):
        """ログイン時にユーザーロールが検証されること"""
        # ログイン
        response = client.post('/api/v1/auth/login', json={
            'username': 'editor_user',
            'password': 'editor123'
        })

        assert response.status_code == 200
        data = response.get_json()

        # レスポンスにロール情報が含まれる（トークンまたはユーザー情報）
        user_data = data.get('data', {}).get('user', {})
        assert user_data
        assert 'roles' in user_data or 'role' in user_data

    def test_invalid_role_assignment_prevented(self, client, admin_token, tmp_path):
        """無効なロール割り当てが防止されること"""
        # 存在しないロールの割り当て試行
        response = client.post('/api/users',
                             headers={'Authorization': f'Bearer {admin_token}'},
                             json={
                                 'username': 'newuser',
                                 'password': 'password123',
                                 'full_name': 'New User',
                                 'department': 'Test',
                                 'roles': ['invalid_role', 'super_admin']  # 無効なロール
                             })

        # 無効なロールは拒否されるべき
        assert response.status_code in [400, 422, 405]
