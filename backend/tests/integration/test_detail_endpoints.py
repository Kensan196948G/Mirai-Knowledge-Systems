"""
詳細エンドポイントのテスト
regulations, projects, experts の詳細取得APIをテスト
"""
import pytest
from flask import json


class TestRegulationDetail:
    """法令詳細エンドポイントのテスト"""

    def test_get_regulation_detail_success(self, client, auth_headers):
        """法令詳細取得 - 成功"""
        # regulations.json に id=1 のデータが存在することを前提
        response = client.get('/api/v1/regulations/1', headers=auth_headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['id'] == 1
        assert 'title' in data['data']
        assert 'issuer' in data['data']
        assert 'category' in data['data']
        assert 'summary' in data['data']

    def test_get_regulation_detail_not_found(self, client, auth_headers):
        """法令詳細取得 - 存在しないID"""
        response = client.get('/api/v1/regulations/99999', headers=auth_headers)
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_get_regulation_detail_unauthorized(self, client):
        """法令詳細取得 - 認証なし"""
        response = client.get('/api/v1/regulations/1')
        assert response.status_code == 401


class TestProjectDetail:
    """プロジェクト詳細エンドポイントのテスト"""

    def test_get_project_detail_success(self, client, auth_headers):
        """プロジェクト詳細取得 - 成功"""
        # projects.json に id=1 のデータが存在することを前提
        response = client.get('/api/v1/projects/1', headers=auth_headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['id'] == 1
        assert 'name' in data['data']
        assert 'description' in data['data']
        assert 'status' in data['data']
        assert 'members' in data['data']
        assert 'milestones' in data['data']

    def test_get_project_detail_not_found(self, client, auth_headers):
        """プロジェクト詳細取得 - 存在しないID"""
        response = client.get('/api/v1/projects/99999', headers=auth_headers)
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data

    def test_get_project_detail_unauthorized(self, client):
        """プロジェクト詳細取得 - 認証なし"""
        response = client.get('/api/v1/projects/1')
        assert response.status_code == 401


class TestExpertDetail:
    """専門家詳細エンドポイントのテスト"""

    def test_get_expert_detail_success(self, client, auth_headers):
        """専門家詳細取得 - 成功"""
        # experts.json に id=1 のデータが存在することを前提
        response = client.get('/api/v1/experts/1', headers=auth_headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['id'] == 1
        assert 'name' in data['data']
        assert 'email' in data['data']
        assert 'department' in data['data']
        assert 'specialties' in data['data']
        assert isinstance(data['data']['specialties'], list)

    def test_get_expert_detail_not_found(self, client, auth_headers):
        """専門家詳細取得 - 存在しないID"""
        response = client.get('/api/v1/experts/99999', headers=auth_headers)
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data

    def test_get_expert_detail_unauthorized(self, client):
        """専門家詳細取得 - 認証なし"""
        response = client.get('/api/v1/experts/1')
        assert response.status_code == 401


class TestDetailEndpointsIntegration:
    """詳細エンドポイント統合テスト"""

    def test_all_detail_endpoints_consistency(self, client, auth_headers):
        """全詳細エンドポイントのレスポンス一貫性テスト"""
        endpoints = [
            '/api/v1/regulations/1',
            '/api/v1/projects/1',
            '/api/v1/experts/1'
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            data = json.loads(response.data)

            # 全てのエンドポイントが同じレスポンス構造を持つことを確認
            assert 'success' in data
            assert 'data' in data
            assert data['data']['id'] == 1

    def test_detail_endpoints_with_various_ids(self, client, auth_headers):
        """複数IDでの詳細取得テスト"""
        # regulations の複数IDテスト
        for reg_id in [1, 2, 3]:
            response = client.get(f'/api/v1/regulations/{reg_id}', headers=auth_headers)
            if response.status_code == 200:
                data = json.loads(response.data)
                assert data['data']['id'] == reg_id

        # projects の複数IDテスト
        for project_id in [1, 2, 3]:
            response = client.get(f'/api/v1/projects/{project_id}', headers=auth_headers)
            if response.status_code == 200:
                data = json.loads(response.data)
                assert data['data']['id'] == project_id

        # experts の複数IDテスト
        for expert_id in [1, 2, 3]:
            response = client.get(f'/api/v1/experts/{expert_id}', headers=auth_headers)
            if response.status_code == 200:
                data = json.loads(response.data)
                assert data['data']['id'] == expert_id
