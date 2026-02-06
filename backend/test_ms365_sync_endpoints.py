"""
Microsoft 365同期APIエンドポイントのテスト

Usage:
    python test_ms365_sync_endpoints.py
"""

import json

import requests

# テスト設定
BASE_URL = "http://localhost:5200/api/v1"
TEST_USER = {"username": "admin", "password": "Admin123!"}


def get_auth_token():
    """認証トークンを取得"""
    response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {}).get("access_token")
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None


def test_endpoints():
    """全エンドポイントをテスト"""

    # 認証
    print("=== 認証 ===")
    token = get_auth_token()
    if not token:
        print("Failed to get auth token")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"✓ Token obtained: {token[:20]}...")
    print()

    # テスト用の設定ID（後で作成したものに置き換え）
    config_id = None

    # 1. 設定一覧取得
    print("=== 1. GET /sync/configs (設定一覧) ===")
    response = requests.get(
        f"{BASE_URL}/integrations/microsoft365/sync/configs", headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    # 2. 設定作成
    print("=== 2. POST /sync/configs (設定作成) ===")
    new_config = {
        "name": "テスト同期設定",
        "site_id": "test-site-id",
        "drive_id": "test-drive-id",
        "folder_path": "/Documents",
        "sync_schedule": "0 3 * * *",
        "sync_strategy": "incremental",
        "file_extensions": ["pdf", "docx", "xlsx"],
        "is_enabled": False,  # テストなので無効化
    }
    response = requests.post(
        f"{BASE_URL}/integrations/microsoft365/sync/configs",
        headers=headers,
        json=new_config,
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

    if response.status_code == 201 and data.get("success"):
        config_id = data.get("data", {}).get("id")
        print(f"✓ Created config ID: {config_id}")
    print()

    if not config_id:
        print("Failed to create config, skipping remaining tests")
        return

    # 3. 設定取得
    print(f"=== 3. GET /sync/configs/{config_id} (設定取得) ===")
    response = requests.get(
        f"{BASE_URL}/integrations/microsoft365/sync/configs/{config_id}",
        headers=headers,
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    # 4. 設定更新
    print(f"=== 4. PUT /sync/configs/{config_id} (設定更新) ===")
    update_data = {"name": "更新されたテスト同期設定", "sync_schedule": "0 4 * * *"}
    response = requests.put(
        f"{BASE_URL}/integrations/microsoft365/sync/configs/{config_id}",
        headers=headers,
        json=update_data,
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    # 5. 接続テスト
    print(f"=== 5. POST /sync/configs/{config_id}/test (接続テスト) ===")
    response = requests.post(
        f"{BASE_URL}/integrations/microsoft365/sync/configs/{config_id}/test",
        headers=headers,
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    # 6. 同期履歴取得
    print(f"=== 6. GET /sync/configs/{config_id}/history (同期履歴) ===")
    response = requests.get(
        f"{BASE_URL}/integrations/microsoft365/sync/configs/{config_id}/history",
        headers=headers,
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    # 7. 統計情報取得
    print("=== 7. GET /sync/stats (統計情報) ===")
    response = requests.get(
        f"{BASE_URL}/integrations/microsoft365/sync/stats", headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    # 8. ステータス取得
    print("=== 8. GET /sync/status (ステータス) ===")
    response = requests.get(
        f"{BASE_URL}/integrations/microsoft365/sync/status", headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    # 9. 手動同期実行（スキップ - 実際のMS365接続が必要）
    print(f"=== 9. POST /sync/configs/{config_id}/execute (手動同期) ===")
    print("スキップ: 実際のMicrosoft 365接続が必要なため")
    print()

    # 10. 設定削除
    print(f"=== 10. DELETE /sync/configs/{config_id} (設定削除) ===")
    response = requests.delete(
        f"{BASE_URL}/integrations/microsoft365/sync/configs/{config_id}",
        headers=headers,
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

    print("=== テスト完了 ===")


if __name__ == "__main__":
    try:
        test_endpoints()
    except Exception as e:
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()
