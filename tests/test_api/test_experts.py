import pytest


def test_get_experts_stats_api(client, auth_headers):
    """Experts統計表示API テスト"""
    response = client.get("/api/v1/experts/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    # 統計データに必要なフィールドがあるか確認
    stats_data = data["data"]
    assert "total_experts" in stats_data
    assert "available_experts" in stats_data
    assert "specializations" in stats_data
    assert "average_rating" in stats_data


def test_get_experts_list_api(client, auth_headers):
    """専門家一覧取得API テスト"""
    response = client.get("/api/v1/experts", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_expert_detail_api(client, auth_headers):
    """専門家詳細取得API テスト"""
    response = client.get("/api/v1/experts/1", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["id"] == 1


def test_calculate_expert_rating_api(client, auth_headers):
    """専門家評価アルゴリズムAPI テスト"""
    response = client.get("/api/v1/experts/1/rating", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    rating_data = data["data"]
    assert "expert_id" in rating_data
    assert "calculated_rating" in rating_data
    assert rating_data["expert_id"] == 1


def test_get_experts_stats_unauthorized(client):
    """未認証でのExperts統計取得テスト"""
    response = client.get("/api/v1/experts/stats")
    assert response.status_code == 401


def test_get_expert_detail_not_found_api(client, auth_headers):
    """存在しない専門家の詳細取得テスト"""
    response = client.get("/api/v1/experts/999999", headers=auth_headers)
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
