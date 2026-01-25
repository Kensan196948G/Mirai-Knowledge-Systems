import json
import pathlib
import sys

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import app_v2


def _write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


@pytest.fixture()
def client(tmp_path):
    app = app_v2.app
    app.config['TESTING'] = True
    app.config['DATA_DIR'] = str(tmp_path)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-longer-than-20'

    # テスト時はレート制限を無効化
    app_v2.limiter.enabled = False

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
            'username': 'partner',
            'password_hash': app_v2.hash_password('partner123'),
            'full_name': 'Partner User',
            'department': 'Partner',
            'roles': ['partner_company']
        }
    ]
    knowledge = [
        {
            'id': 1,
            'title': 'Test Knowledge',
            'summary': 'Test summary',
            'content': 'Test content',
            'category': 'safety',
            'tags': ['test']
        }
    ]

    _write_json(tmp_path / 'users.json', users)
    _write_json(tmp_path / 'knowledge.json', knowledge)
    _write_json(tmp_path / 'access_logs.json', [])
    _write_json(tmp_path / 'sop.json', [])
    _write_json(tmp_path / 'notifications.json', [])

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client):
    """管理者ユーザーの認証ヘッダーを提供"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    token = response.get_json()['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture()
def partner_auth_headers(client):
    """協力会社ユーザーの認証ヘッダーを提供"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'partner',
        'password': 'partner123'
    })
    token = response.get_json()['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture()
def mock_access_logs(tmp_path):
    """アクセスログをモックするフィクスチャ"""
    def _mock_logs(logs):
        _write_json(tmp_path / 'access_logs.json', logs)
    return _mock_logs


@pytest.fixture()
def create_knowledge(client, auth_headers):
    """ナレッジを作成するヘルパーフィクスチャ"""
    def _create(title='Test', summary='Test', content='Test', category='安全衛生', **kwargs):
        data = {
            'title': title,
            'summary': summary,
            'content': content,
            'category': category,
            **kwargs
        }
        response = client.post('/api/v1/knowledge', json=data, headers=auth_headers)
        return response.get_json()
    return _create


@pytest.fixture()
def create_test_users(tmp_path):
    """認可テスト用のユーザーを作成"""
    users = [
        {
            'id': 1,
            'username': 'admin_user',
            'password_hash': app_v2.hash_password('admin123'),
            'full_name': 'Admin User',
            'department': 'Admin',
            'roles': ['admin']
        },
        {
            'id': 2,
            'username': 'editor_user',
            'password_hash': app_v2.hash_password('editor123'),
            'full_name': 'Editor User',
            'department': 'Construction',
            'roles': ['construction_manager']
        },
        {
            'id': 3,
            'username': 'viewer_user',
            'password_hash': app_v2.hash_password('viewer123'),
            'full_name': 'Viewer User',
            'department': 'Partner',
            'roles': ['partner_company']
        },
        {
            'id': 4,
            'username': 'no_role_user',
            'password_hash': app_v2.hash_password('norole123'),
            'full_name': 'No Role User',
            'department': 'General',
            'roles': []
        }
    ]

    _write_json(tmp_path / 'users.json', users)
    return users


@pytest.fixture()
def admin_token(client, create_test_users):
    """管理者トークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'admin_user',
        'password': 'admin123'
    })
    return response.get_json()['data']['access_token']


@pytest.fixture()
def editor_token(client, create_test_users):
    """施工管理トークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'editor_user',
        'password': 'editor123'
    })
    return response.get_json()['data']['access_token']


@pytest.fixture()
def viewer_token(client, create_test_users):
    """協力会社トークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'viewer_user',
        'password': 'viewer123'
    })
    return response.get_json()['data']['access_token']


@pytest.fixture()
def no_role_token(client, create_test_users):
    """ロールなしユーザーのトークンを取得"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'no_role_user',
        'password': 'norole123'
    })
    return response.get_json()['data']['access_token']
