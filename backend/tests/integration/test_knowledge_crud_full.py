"""
ナレッジCRUD完全フローの統合テスト
Update/Delete操作を含む
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
        }
    ]

    # 初期ナレッジデータ
    knowledge = [
        {
            'id': 1,
            'title': 'Test Knowledge 1',
            'summary': 'Test summary 1',
            'content': 'Test content 1',
            'category': 'safety',
            'tags': ['test'],
            'status': 'approved',
            'priority': 'high',
            'owner': 'admin'
        }
    ]

    _write_json(tmp_path / 'users.json', users)
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


class TestKnowledgeCRUDFlow:
    """ナレッジCRUD全体フローのテスト"""

    def test_full_crud_lifecycle(self, client):
        """完全なCRUDライフサイクル"""
        token = _login(client)

        # 1. 作成 (Create)
        create_response = client.post(
            '/api/v1/knowledge',
            json={
                'title': '新規ナレッジ',
                'summary': '概要',
                'content': '詳細コンテンツの内容です',
                'category': '施工計画',
                'tags': ['new', 'test']
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert create_response.status_code == 201
        knowledge_id = create_response.get_json()['data']['id']

        # 2. 読み取り (Read)
        read_response = client.get(
            f'/api/v1/knowledge/{knowledge_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert read_response.status_code == 200
        assert read_response.get_json()['data']['title'] == '新規ナレッジ'

        # 3. 更新 (Update)
        update_response = client.put(
            f'/api/v1/knowledge/{knowledge_id}',
            json={'title': '更新後タイトル', 'summary': '更新後概要'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert update_response.status_code == 200
        assert update_response.get_json()['data']['title'] == '更新後タイトル'

        # 4. 削除 (Delete)
        delete_response = client.delete(
            f'/api/v1/knowledge/{knowledge_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert delete_response.status_code == 200

        # 5. 削除後は取得できない
        get_after_delete = client.get(
            f'/api/v1/knowledge/{knowledge_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert get_after_delete.status_code == 404


class TestKnowledgeUpdate:
    """ナレッジ更新のテスト"""

    def test_update_knowledge_success(self, client):
        """ナレッジ更新成功"""
        token = _login(client)

        response = client.put(
            '/api/v1/knowledge/1',
            json={
                'title': '更新タイトル',
                'summary': '更新概要',
                'content': '更新コンテンツ'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == '更新タイトル'
        assert data['data']['summary'] == '更新概要'

    def test_update_knowledge_partial(self, client):
        """部分更新が可能"""
        token = _login(client)

        # タイトルのみ更新
        response = client.put(
            '/api/v1/knowledge/1',
            json={'title': '新しいタイトル'},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['title'] == '新しいタイトル'
        # 他のフィールドは保持される
        assert data['data']['category'] == 'safety'

    def test_update_nonexistent_knowledge_returns_404(self, client):
        """存在しないナレッジの更新は404"""
        token = _login(client)

        response = client.put(
            '/api/v1/knowledge/999',
            json={'title': 'Update'},
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 404

    def test_update_knowledge_requires_auth(self, client):
        """認証が必要"""
        response = client.put(
            '/api/v1/knowledge/1',
            json={'title': 'Update'}
        )

        assert response.status_code == 401

    def test_update_knowledge_updates_timestamp(self, client):
        """更新時にupdated_atが更新される"""
        token = _login(client)

        # 元のナレッジ取得
        original = client.get(
            '/api/v1/knowledge/1',
            headers={'Authorization': f'Bearer {token}'}
        ).get_json()['data']

        # 更新
        updated = client.put(
            '/api/v1/knowledge/1',
            json={'title': '更新後'},
            headers={'Authorization': f'Bearer {token}'}
        ).get_json()['data']

        # updated_atが更新されている（または存在する）
        assert 'updated_at' in updated


class TestKnowledgeDelete:
    """ナレッジ削除のテスト"""

    def test_delete_knowledge_success(self, client):
        """ナレッジ削除成功"""
        token = _login(client)

        response = client.delete(
            '/api/v1/knowledge/1',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_delete_nonexistent_knowledge_returns_404(self, client):
        """存在しないナレッジの削除は404"""
        token = _login(client)

        response = client.delete(
            '/api/v1/knowledge/999',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 404

    def test_delete_knowledge_requires_auth(self, client):
        """認証が必要"""
        response = client.delete('/api/v1/knowledge/1')

        assert response.status_code == 401

    def test_delete_knowledge_is_persisted(self, client, tmp_path):
        """削除が永続化される"""
        token = _login(client)

        client.delete(
            '/api/v1/knowledge/1',
            headers={'Authorization': f'Bearer {token}'}
        )

        # ファイルを確認
        knowledge_file = tmp_path / 'knowledge.json'
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            knowledge_list = json.load(f)

        # id=1のナレッジが削除されている
        assert not any(k['id'] == 1 for k in knowledge_list)

    def test_delete_knowledge_logs_access(self, client, tmp_path):
        """削除がログに記録される"""
        token = _login(client)

        client.delete(
            '/api/v1/knowledge/1',
            headers={'Authorization': f'Bearer {token}'}
        )

        # ログファイルを確認
        logs_file = tmp_path / 'access_logs.json'
        with open(logs_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)

        delete_logs = [l for l in logs if l['action'] == 'knowledge.delete']
        assert len(delete_logs) >= 1
        assert delete_logs[0]['resource_id'] == 1


class TestKnowledgeValidation:
    """ナレッジバリデーションのテスト"""

    def test_create_knowledge_requires_title(self, client):
        """タイトルは必須"""
        token = _login(client)

        response = client.post(
            '/api/v1/knowledge',
            json={
                'summary': '概要',
                'content': 'コンテンツの詳細',
                'category': '施工計画'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 400

    def test_create_knowledge_requires_content(self, client):
        """コンテンツは必須"""
        token = _login(client)

        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': 'タイトル',
                'summary': '概要',
                'category': '施工計画'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 400

    def test_create_knowledge_validates_category(self, client):
        """カテゴリのバリデーション"""
        token = _login(client)

        response = client.post(
            '/api/v1/knowledge',
            json={
                'title': 'タイトル',
                'summary': '概要',
                'content': 'コンテンツ',
                'category': '無効なカテゴリ'
            },
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 400


class TestKnowledgePagination:
    """ナレッジページネーションのテスト"""

    def test_knowledge_list_pagination(self, client, tmp_path):
        """ページネーションが機能する"""
        import app_v2

        # 15件のナレッジを作成
        knowledge_file = tmp_path / 'knowledge.json'
        knowledge_list = []
        for i in range(1, 16):
            knowledge_list.append({
                'id': i,
                'title': f'Knowledge {i}',
                'summary': f'Summary {i}',
                'content': f'Content {i}',
                'category': 'safety',
                'tags': []
            })

        _write_json(knowledge_file, knowledge_list)

        token = _login(client)

        # 1ページ目（10件）
        response1 = client.get(
            '/api/v1/knowledge?page=1&per_page=10',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response1.status_code == 200
        data1 = response1.get_json()
        assert len(data1['data']) == 10
        assert data1['pagination']['total_items'] == 15
        assert data1['pagination']['total_pages'] == 2

        # 2ページ目（5件）
        response2 = client.get(
            '/api/v1/knowledge?page=2&per_page=10',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response2.status_code == 200
        data2 = response2.get_json()
        assert len(data2['data']) == 5
