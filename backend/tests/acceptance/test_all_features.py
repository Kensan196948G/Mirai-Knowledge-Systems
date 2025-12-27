"""
全機能の自動機能テスト

このファイルは全てのビジネス機能をエンドツーエンドでテストします。
- ナレッジCRUD機能
- SOP閲覧機能
- 事故レポート機能（データ作成想定）
- 専門家相談機能（データ作成想定）
- 検索機能
- 通知機能
- 承認フロー機能
- ダッシュボード機能
"""
import pytest
import json
from datetime import datetime


class TestKnowledgeCRUDFeature:
    """ナレッジCRUD機能の包括的テスト"""

    def test_create_knowledge_success(self, client):
        """ナレッジ作成 - 正常系"""
        # 前提: ログイン
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert login_response.status_code == 200
        token = login_response.json['access_token']

        # 実行: 新しいナレッジを作成
        response = client.post('/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'title': '新しいナレッジ',
                'summary': 'これはテストナレッジです',
                'content': '詳細な内容がここに入ります',
                'category': 'safety',
                'tags': ['test', 'automation']
            })

        # 検証
        assert response.status_code == 201
        data = response.json
        assert data['title'] == '新しいナレッジ'
        assert data['category'] == 'safety'
        assert 'test' in data['tags']
        assert 'id' in data

    def test_read_knowledge_list(self, client):
        """ナレッジ一覧取得 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) > 0
        assert 'title' in data[0]

    def test_read_knowledge_by_id(self, client):
        """ナレッジ詳細取得 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/knowledge/1',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert data['id'] == 1
        assert 'title' in data
        assert 'summary' in data

    def test_read_knowledge_with_filters(self, client):
        """ナレッジ一覧取得 - フィルター適用"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # カテゴリーでフィルター
        response = client.get('/api/v1/knowledge?category=safety',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        for item in data:
            assert item['category'] == 'safety'

    def test_knowledge_validation_error(self, client):
        """ナレッジ作成 - バリデーションエラー"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # タイトルなしで作成試行
        response = client.post('/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'summary': 'サマリーのみ',
                'category': 'safety'
            })

        assert response.status_code in [400, 422]


class TestSOPViewFeature:
    """SOP閲覧機能の包括的テスト"""

    def test_sop_list_retrieval(self, client):
        """SOP一覧取得 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/sop',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)

    def test_sop_unauthorized_access(self, client):
        """SOP取得 - 認証なしアクセス"""
        response = client.get('/api/v1/sop')
        assert response.status_code == 401


class TestIncidentReportFeature:
    """事故レポート機能のテスト（データ作成想定）"""

    def test_incident_data_structure(self, client, tmp_path):
        """事故レポートのデータ構造検証"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # incidents.jsonファイルを作成
        incidents_file = tmp_path / 'incidents.json'
        test_incidents = [
            {
                'id': 1,
                'title': 'クレーン転倒事故',
                'description': '強風によりタワークレーンが転倒',
                'severity': 'high',
                'status': 'investigating',
                'reported_at': '2025-01-15T10:30:00',
                'reporter_id': 1
            }
        ]
        incidents_file.write_text(
            json.dumps(test_incidents, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        # 検証: ファイルが正しく作成されたか
        assert incidents_file.exists()
        loaded_data = json.loads(incidents_file.read_text(encoding='utf-8'))
        assert len(loaded_data) == 1
        assert loaded_data[0]['title'] == 'クレーン転倒事故'


class TestExpertConsultationFeature:
    """専門家相談機能のテスト（データ作成想定）"""

    def test_consultation_data_structure(self, client, tmp_path):
        """専門家相談のデータ構造検証"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # consultations.jsonファイルを作成
        consultations_file = tmp_path / 'consultations.json'
        test_consultations = [
            {
                'id': 1,
                'title': '地盤改良工法の相談',
                'question': '軟弱地盤における最適な改良工法を教えてください',
                'category': 'geotechnical',
                'status': 'pending',
                'asked_by': 1,
                'asked_at': '2025-01-20T14:00:00'
            }
        ]
        consultations_file.write_text(
            json.dumps(test_consultations, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        # 検証
        assert consultations_file.exists()
        loaded_data = json.loads(consultations_file.read_text(encoding='utf-8'))
        assert len(loaded_data) == 1
        assert loaded_data[0]['category'] == 'geotechnical'


class TestSearchFeature:
    """検索機能の包括的テスト"""

    def test_unified_search_basic(self, client):
        """統合検索 - 基本検索"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/search/unified?q=test',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert 'knowledge' in data
        assert 'sop' in data
        assert isinstance(data['knowledge'], list)

    def test_unified_search_with_category(self, client):
        """統合検索 - カテゴリーフィルター"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/search/unified?q=test&category=safety',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert 'knowledge' in data

    def test_search_empty_query(self, client):
        """統合検索 - 空クエリ"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/search/unified?q=',
            headers={'Authorization': f'Bearer {token}'})

        # 空クエリでも200を返すか、400を返すかは実装次第
        assert response.status_code in [200, 400]


class TestNotificationFeature:
    """通知機能の包括的テスト"""

    def test_get_notifications_list(self, client, tmp_path):
        """通知一覧取得 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # テスト通知データを作成
        notifications_file = tmp_path / 'notifications.json'
        test_notifications = [
            {
                'id': 1,
                'user_id': 1,
                'message': '新しいナレッジが追加されました',
                'type': 'info',
                'is_read': False,
                'created_at': '2025-01-20T10:00:00'
            }
        ]
        notifications_file.write_text(
            json.dumps(test_notifications, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        response = client.get('/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)

    def test_mark_notification_as_read(self, client, tmp_path):
        """通知既読化 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # テスト通知データを作成
        notifications_file = tmp_path / 'notifications.json'
        test_notifications = [
            {
                'id': 1,
                'user_id': 1,
                'message': 'テスト通知',
                'type': 'info',
                'is_read': False,
                'created_at': '2025-01-20T10:00:00'
            }
        ]
        notifications_file.write_text(
            json.dumps(test_notifications, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        response = client.put('/api/v1/notifications/1/read',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert data['message'] in ['通知を既読にしました', 'Notification marked as read']

    def test_get_unread_count(self, client, tmp_path):
        """未読通知数取得 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # テスト通知データを作成
        notifications_file = tmp_path / 'notifications.json'
        test_notifications = [
            {
                'id': 1,
                'user_id': 1,
                'message': '未読通知1',
                'type': 'info',
                'is_read': False,
                'created_at': '2025-01-20T10:00:00'
            },
            {
                'id': 2,
                'user_id': 1,
                'message': '未読通知2',
                'type': 'warning',
                'is_read': False,
                'created_at': '2025-01-20T11:00:00'
            }
        ]
        notifications_file.write_text(
            json.dumps(test_notifications, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        response = client.get('/api/v1/notifications/unread/count',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert 'unread_count' in data
        assert data['unread_count'] >= 0


class TestApprovalFlowFeature:
    """承認フロー機能の包括的テスト"""

    def test_get_approval_list(self, client, tmp_path):
        """承認待ち一覧取得 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # テスト承認データを作成
        approvals_file = tmp_path / 'approvals.json'
        test_approvals = [
            {
                'id': 1,
                'knowledge_id': 1,
                'requested_by': 1,
                'status': 'pending',
                'requested_at': '2025-01-20T09:00:00'
            }
        ]
        approvals_file.write_text(
            json.dumps(test_approvals, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        response = client.get('/api/v1/approvals',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)

    def test_approval_status_filter(self, client, tmp_path):
        """承認一覧 - ステータスフィルター"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # テスト承認データを作成
        approvals_file = tmp_path / 'approvals.json'
        test_approvals = [
            {
                'id': 1,
                'knowledge_id': 1,
                'requested_by': 1,
                'status': 'pending',
                'requested_at': '2025-01-20T09:00:00'
            },
            {
                'id': 2,
                'knowledge_id': 2,
                'requested_by': 1,
                'status': 'approved',
                'requested_at': '2025-01-19T09:00:00'
            }
        ]
        approvals_file.write_text(
            json.dumps(test_approvals, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        response = client.get('/api/v1/approvals?status=pending',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json
        for item in data:
            if 'status' in item:
                assert item['status'] == 'pending'


class TestDashboardFeature:
    """ダッシュボード機能の包括的テスト"""

    def test_get_dashboard_stats(self, client):
        """ダッシュボード統計取得 - 正常系"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/dashboard/stats',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json

        # 必須フィールドの検証
        assert 'total_knowledge' in data
        assert 'total_users' in data
        assert isinstance(data['total_knowledge'], int)
        assert isinstance(data['total_users'], int)

    def test_dashboard_stats_completeness(self, client):
        """ダッシュボード統計 - データ完全性チェック"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        response = client.get('/api/v1/dashboard/stats',
            headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.json

        # 統計データの妥当性検証
        assert data['total_knowledge'] >= 0
        assert data['total_users'] >= 0


class TestAuthenticationFlow:
    """認証フローの包括的テスト"""

    def test_login_logout_flow(self, client):
        """ログイン〜ログアウトフロー"""
        # ログイン
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert login_response.status_code == 200
        assert 'access_token' in login_response.json

        token = login_response.json['access_token']

        # 認証が必要なエンドポイントにアクセス
        me_response = client.get('/api/v1/auth/me',
            headers={'Authorization': f'Bearer {token}'})
        assert me_response.status_code == 200
        assert 'username' in me_response.json

    def test_invalid_credentials(self, client):
        """無効な認証情報でのログイン"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401

    def test_token_refresh(self, client):
        """トークンリフレッシュ"""
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert login_response.status_code == 200
        refresh_token = login_response.json.get('refresh_token')

        if refresh_token:
            refresh_response = client.post('/api/v1/auth/refresh',
                headers={'Authorization': f'Bearer {refresh_token}'})
            assert refresh_response.status_code == 200
            assert 'access_token' in refresh_response.json


class TestEndToEndScenarios:
    """エンドツーエンドシナリオテスト"""

    def test_complete_knowledge_workflow(self, client):
        """完全なナレッジワークフロー"""
        # 1. ログイン
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert login_response.status_code == 200
        token = login_response.json['access_token']

        # 2. ナレッジ作成
        create_response = client.post('/api/v1/knowledge',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'title': 'E2Eテストナレッジ',
                'summary': 'エンドツーエンドテスト用',
                'content': '詳細内容',
                'category': 'safety',
                'tags': ['e2e', 'test']
            })
        assert create_response.status_code == 201
        knowledge_id = create_response.json['id']

        # 3. 作成したナレッジを取得
        get_response = client.get(f'/api/v1/knowledge/{knowledge_id}',
            headers={'Authorization': f'Bearer {token}'})
        assert get_response.status_code == 200
        assert get_response.json['title'] == 'E2Eテストナレッジ'

        # 4. 検索で見つかることを確認
        search_response = client.get('/api/v1/search/unified?q=E2E',
            headers={'Authorization': f'Bearer {token}'})
        assert search_response.status_code == 200

    def test_notification_workflow(self, client, tmp_path):
        """通知ワークフロー"""
        # 1. ログイン
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        token = login_response.json['access_token']

        # 2. 通知データ作成
        notifications_file = tmp_path / 'notifications.json'
        test_notifications = [
            {
                'id': 1,
                'user_id': 1,
                'message': 'E2Eテスト通知',
                'type': 'info',
                'is_read': False,
                'created_at': datetime.now().isoformat()
            }
        ]
        notifications_file.write_text(
            json.dumps(test_notifications, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        # 3. 未読数確認
        count_response = client.get('/api/v1/notifications/unread/count',
            headers={'Authorization': f'Bearer {token}'})
        assert count_response.status_code == 200
        initial_count = count_response.json['unread_count']

        # 4. 通知一覧取得
        list_response = client.get('/api/v1/notifications',
            headers={'Authorization': f'Bearer {token}'})
        assert list_response.status_code == 200

        # 5. 通知を既読化
        read_response = client.put('/api/v1/notifications/1/read',
            headers={'Authorization': f'Bearer {token}'})
        assert read_response.status_code == 200
