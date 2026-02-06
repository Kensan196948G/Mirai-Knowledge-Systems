

def test_get_project_progress_api(client, auth_headers):
    """プロジェクト進捗%計算API テスト"""
    # プロジェクトID 1の進捗を取得
    response = client.get("/api/v1/projects/1/progress", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    # 進捗データに必要なフィールドがあるか確認
    progress_data = data["data"]
    assert "progress_percentage" in progress_data
    assert "tasks_completed" in progress_data
    assert "total_tasks" in progress_data


def test_get_project_progress_not_found_api(client, auth_headers):
    """存在しないプロジェクトの進捗取得テスト"""
    response = client.get("/api/v1/projects/999999/progress", headers=auth_headers)
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_get_project_progress_unauthorized(client):
    """未認証でのプロジェクト進捗取得テスト"""
    response = client.get("/api/v1/projects/1/progress")
    assert response.status_code == 401


def test_get_projects_list_api(client, auth_headers):
    """プロジェクト一覧取得API テスト"""
    response = client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_get_project_detail_api(client, auth_headers):
    """プロジェクト詳細取得API テスト"""
    response = client.get("/api/v1/projects/1", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["id"] == 1
