"""
その他APIの統合テスト
SOP、ダッシュボード、承認などのAPIテスト
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
        }
    ]

    # SOPデータ
    sop = [
        {
            'id': 1,
            'title': 'コンクリート打設手順',
            'content': '標準作業手順書',
            'status': 'active'
        },
        {
            'id': 2,
            'title': '安全帯使用手順',
            'content': '高所作業時の安全帯着用手順',
            'status': 'active'
        }
    ]

    # インシデントデータ
    incidents = [
        {
            'id': 1,
            'title': '転倒事故',
            'description': '軽微な転倒事故',
            'status': 'reported'
        },
        {
            'id': 2,
            'title': '品質不良',
            'description': 'コンクリート配合ミス',
            'status': 'resolved'
        }
    ]

    # 承認データ
    approvals = [
        {
            'id': 1,
            'title': 'ナレッジ承認',
            'status': 'pending',
            'type': 'knowledge_approval'
        },
        {
            'id': 2,
            'title': 'SOP変更承認',
            'status': 'pending',
            'type': 'sop_change'
        },
        {
            'id': 3,
            'title': '完了済み承認',
            'status': 'approved',
            'type': 'knowledge_approval'
        }
    ]

    # ナレッジデータ
    knowledge = [
        {'id': 1, 'title': 'Test Knowledge', 'category': 'safety'},
        {'id': 2, 'title': 'Test Knowledge 2', 'category': 'quality'}
    ]

    _write_json(tmp_path / 'users.json', users)
    _write_json(tmp_path / 'sop.json', sop)
    _write_json(tmp_path / 'incidents.json', incidents)
    _write_json(tmp_path / 'approvals.json', approvals)
    _write_json(tmp_path / 'knowledge.json', knowledge)
    _write_json(tmp_path / 'access_logs.json', [])
    _write_json(tmp_path / 'notifications.json', [])

    with app.test_client() as test_client:
        yield test_client


def _login(client, username='admin', password='admin123'):
    """ログインヘルパー"""
    response = client.post(
        '/api/v1/auth/login',
        json={'username': username, 'password': password}
    )
    return response.get_json()['data']['access_token']


class TestSOPAPI:
    """SOP APIのテスト"""

    def test_get_sop_list(self, client):
        """SOP一覧を取得"""
        token = _login(client)

        response = client.get(
            '/api/v1/sop',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 2
        assert data['pagination']['total_items'] == 2

    def test_get_sop_requires_auth(self, client):
        """認証が必要"""
        response = client.get('/api/v1/sop')

        assert response.status_code == 401

    def test_construction_manager_can_access_sop(self, client):
        """施工管理者もSOPにアクセス可能"""
        token = _login(client, 'manager', 'manager123')

        response = client.get(
            '/api/v1/sop',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200


class TestDashboardAPI:
    """ダッシュボードAPIのテスト"""

    def test_get_dashboard_stats(self, client):
        """ダッシュボード統計情報を取得"""
        token = _login(client)

        response = client.get(
            '/api/v1/dashboard/stats',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'kpis' in data['data']
        assert 'counts' in data['data']

    def test_dashboard_stats_includes_kpis(self, client):
        """KPI情報が含まれる"""
        token = _login(client)

        response = client.get(
            '/api/v1/dashboard/stats',
            headers={'Authorization': f'Bearer {token}'}
        )

        data = response.get_json()
        kpis = data['data']['kpis']

        assert 'knowledge_reuse_rate' in kpis
        assert 'accident_free_days' in kpis
        assert 'active_audits' in kpis
        assert 'delayed_corrections' in kpis

    def test_dashboard_stats_includes_counts(self, client):
        """カウント情報が含まれる"""
        token = _login(client)

        response = client.get(
            '/api/v1/dashboard/stats',
            headers={'Authorization': f'Bearer {token}'}
        )

        data = response.get_json()
        counts = data['data']['counts']

        assert 'total_knowledge' in counts
        assert 'total_sop' in counts
        assert 'recent_incidents' in counts
        assert 'pending_approvals' in counts

    def test_dashboard_counts_are_correct(self, client):
        """カウント値が正しい"""
        token = _login(client)

        response = client.get(
            '/api/v1/dashboard/stats',
            headers={'Authorization': f'Bearer {token}'}
        )

        data = response.get_json()
        counts = data['data']['counts']

        assert counts['total_knowledge'] == 2
        assert counts['total_sop'] == 2
        assert counts['recent_incidents'] == 1  # status='reported'のみ
        assert counts['pending_approvals'] == 2  # status='pending'のみ

    def test_dashboard_requires_auth(self, client):
        """認証が必要"""
        response = client.get('/api/v1/dashboard/stats')

        assert response.status_code == 401


class TestApprovalsAPI:
    """承認APIのテスト"""

    def test_get_approvals_list(self, client):
        """承認一覧を取得"""
        token = _login(client)

        response = client.get(
            '/api/v1/approvals',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']) == 3
        assert data['pagination']['total_items'] == 3

    def test_approvals_requires_auth(self, client):
        """認証が必要"""
        response = client.get('/api/v1/approvals')

        assert response.status_code == 401


class TestErrorHandlers:
    """エラーハンドラーのテスト"""

    def test_404_error_handler(self, client):
        """404エラーハンドラー"""
        token = _login(client)

        response = client.get(
            '/api/v1/nonexistent_endpoint',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'NOT_FOUND'

    def test_invalid_token_error(self, client):
        """無効なトークンエラー"""
        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': 'Bearer invalid_token_here'}
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_TOKEN'

    def test_missing_token_error(self, client):
        """トークン欠落エラー"""
        response = client.get('/api/v1/knowledge')

        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_TOKEN'


class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""

    def test_security_headers_present(self, client):
        """セキュリティヘッダーが設定される"""
        token = _login(client)

        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'

        assert 'Referrer-Policy' in response.headers
        assert response.headers['Referrer-Policy'] == 'no-referrer'

    def test_csp_header_present(self, client):
        """Content-Security-Policyヘッダーが設定される"""
        token = _login(client)

        response = client.get(
            '/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert 'Content-Security-Policy' in response.headers


class TestPermissionSystem:
    """権限システムのテスト"""

    def test_get_user_permissions_admin(self, client, tmp_path):
        """管理者は全権限を持つ"""
        import app_v2

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        user = {'id': 1, 'username': 'admin', 'roles': ['admin']}
        permissions = app_v2.get_user_permissions(user)

        assert permissions == ['*']

    def test_get_user_permissions_construction_manager(self, client, tmp_path):
        """施工管理者の権限"""
        import app_v2

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        user = {'id': 2, 'username': 'manager', 'roles': ['construction_manager']}
        permissions = app_v2.get_user_permissions(user)

        assert 'knowledge.create' in permissions
        assert 'knowledge.read' in permissions
        assert 'sop.read' in permissions

    def test_get_user_permissions_partner(self, client, tmp_path):
        """協力会社の権限（読み取りのみ）"""
        import app_v2

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        user = {'id': 3, 'username': 'partner', 'roles': ['partner_company']}
        permissions = app_v2.get_user_permissions(user)

        assert 'knowledge.read' in permissions
        assert 'sop.read' in permissions
        assert 'knowledge.create' not in permissions

    def test_get_user_permissions_no_roles(self, client, tmp_path):
        """ロールなしユーザー"""
        import app_v2

        app_v2.app.config['DATA_DIR'] = str(tmp_path)

        user = {'id': 4, 'username': 'noone', 'roles': []}
        permissions = app_v2.get_user_permissions(user)

        assert permissions == []


class TestTokenRefresh:
    """トークンリフレッシュのテスト"""

    def test_refresh_token_success(self, client):
        """リフレッシュトークンでアクセストークンを再取得"""
        # ログインしてリフレッシュトークンを取得
        login_response = client.post(
            '/api/v1/auth/login',
            json={'username': 'admin', 'password': 'admin123'}
        )
        refresh_token = login_response.get_json()['data']['refresh_token']

        # リフレッシュ
        response = client.post(
            '/api/v1/auth/refresh',
            headers={'Authorization': f'Bearer {refresh_token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert data['data']['expires_in'] == 3600

    def test_refresh_with_access_token_fails(self, client):
        """アクセストークンではリフレッシュできない"""
        token = _login(client)

        response = client.post(
            '/api/v1/auth/refresh',
            headers={'Authorization': f'Bearer {token}'}
        )

        # アクセストークンはリフレッシュエンドポイントでは無効
        assert response.status_code == 401
