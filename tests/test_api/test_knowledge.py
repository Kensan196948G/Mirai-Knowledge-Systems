import pytest


def test_create_knowledge_api(client, auth_headers, sample_knowledge):
    """ナレッジ作成 API テスト"""
    response = client.post(
        "/api/v1/knowledge", json=sample_knowledge, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["title"] == sample_knowledge["title"]


def test_get_knowledge_list_api(client, auth_headers):
    """ナレッジ一覧取得 API テスト"""
    response = client.get("/api/v1/knowledge", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_knowledge_by_id_api(client, auth_headers, sample_knowledge):
    """ナレッジ詳細取得 API テスト"""
    # まず作成
    create_response = client.post(
        "/api/v1/knowledge", json=sample_knowledge, headers=auth_headers
    )
    assert create_response.status_code == 201
    created_data = create_response.get_json()["data"]

    # 取得
    response = client.get(
        f"/api/v1/knowledge/{created_data['id']}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["id"] == created_data["id"]
    assert data["data"]["title"] == sample_knowledge["title"]


def test_get_knowledge_by_id_not_found_api(client, auth_headers):
    """存在しないナレッジ取得 API テスト"""
    response = client.get("/api/v1/knowledge/999999", headers=auth_headers)
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_update_knowledge_api(client, auth_headers, sample_knowledge):
    """ナレッジ更新 API テスト"""
    # まず作成
    create_response = client.post(
        "/api/v1/knowledge", json=sample_knowledge, headers=auth_headers
    )
    assert create_response.status_code == 201
    created_data = create_response.get_json()["data"]

    # 更新
    update_data = {"title": "Updated Title"}
    response = client.put(
        f"/api/v1/knowledge/{created_data['id']}",
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["title"] == "Updated Title"


def test_delete_knowledge_api(client, auth_headers, sample_knowledge):
    """ナレッジ削除 API テスト"""
    # まず作成
    create_response = client.post(
        "/api/v1/knowledge", json=sample_knowledge, headers=auth_headers
    )
    assert create_response.status_code == 201
    created_data = create_response.get_json()["data"]

    # 削除
    response = client.delete(
        f"/api/v1/knowledge/{created_data['id']}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    # 削除確認
    get_response = client.get(
        f"/api/v1/knowledge/{created_data['id']}", headers=auth_headers
    )
    assert get_response.status_code == 404


def test_create_knowledge_unauthorized(client, sample_knowledge):
    """未認証でのナレッジ作成テスト"""
    response = client.post("/api/v1/knowledge", json=sample_knowledge)
    assert response.status_code == 401


def test_get_knowledge_list_unauthorized(client):
    """未認証でのナレッジ一覧取得テスト"""
    response = client.get("/api/v1/knowledge")
    assert response.status_code == 401
