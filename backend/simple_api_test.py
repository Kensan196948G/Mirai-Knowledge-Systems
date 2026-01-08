#!/usr/bin/env python3
"""簡易APIテストスクリプト - PostgreSQLモード検証用"""

import json
import sys
import requests

BASE_URL = "http://localhost:5100"


def test_health_endpoint():
    """ヘルスチェックエンドポイントのテスト"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        data = response.json()
        print(f"✓ Health endpoint: {data.get('status')}")
        print(f"  Storage mode: {data.get('storage_mode')}")
        print(f"  Database connected: {data.get('database_connected')}")
        return (
            data.get("status") == "healthy" and data.get("storage_mode") == "postgresql"
        )
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")
        return False


def test_login():
    """ログイン機能のテスト"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        data = response.json()
        if data.get("success"):
            token = data["data"]["access_token"]
            print("✓ Login successful")
            return token
        else:
            print(f"✗ Login failed: {data.get('error', {}).get('message')}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None


def test_knowledge_endpoint(token):
    """ナレッジエンドポイントのテスト"""
    if not token:
        print("✗ No token, skipping knowledge test")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/knowledge?page=1&per_page=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        if data.get("success"):
            items = data.get("data", [])
            print(f"✓ Knowledge endpoint: {len(items)} items")
            if items:
                print(f"  First item title: {items[0].get('title')}")
                print(f"  First item ID: {items[0].get('id')}")
            return len(items) > 0
        else:
            print(
                f"✗ Knowledge endpoint failed: {data.get('error', {}).get('message')}"
            )
            return False
    except Exception as e:
        print(f"✗ Knowledge endpoint error: {e}")
        return False


def test_sop_endpoint(token):
    """SOPエンドポイントのテスト"""
    if not token:
        print("✗ No token, skipping SOP test")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/sop?page=1&per_page=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        if data.get("success"):
            items = data.get("data", [])
            print(f"✓ SOP endpoint: {len(items)} items")
            return len(items) > 0
        else:
            print(f"✗ SOP endpoint failed: {data.get('error', {}).get('message')}")
            return False
    except Exception as e:
        print(f"✗ SOP endpoint error: {e}")
        return False


def test_dashboard_stats(token):
    """ダッシュボード統計エンドポイントのテスト"""
    if not token:
        print("✗ No token, skipping dashboard test")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        if data.get("success"):
            stats = data.get("data", {})
            print(f"✓ Dashboard stats:")
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    print(f"  - {key}: {value}")
            return True
        else:
            print(f"✗ Dashboard stats failed: {data.get('error', {}).get('message')}")
            return False
    except Exception as e:
        print(f"✗ Dashboard stats error: {e}")
        return False


def main():
    print("=" * 60)
    print("簡易APIテスト - PostgreSQLモード検証")
    print("=" * 60)

    results = {
        "health": False,
        "login": False,
        "knowledge": False,
        "sop": False,
        "dashboard": False,
    }

    # テスト1: ヘルスチェック
    print("\n[1] ヘルスチェックテスト")
    results["health"] = test_health_endpoint()

    # テスト2: ログイン
    print("\n[2] ログインテスト")
    token = test_login()
    results["login"] = token is not None

    if token:
        # テスト3: ナレッジエンドポイント
        print("\n[3] ナレッジエンドポイントテスト")
        results["knowledge"] = test_knowledge_endpoint(token)

        # テスト4: SOPエンドポイント
        print("\n[4] SOPエンドポイントテスト")
        results["sop"] = test_sop_endpoint(token)

        # テスト5: ダッシュボード統計
        print("\n[5] ダッシュボード統計テスト")
        results["dashboard"] = test_dashboard_stats(token)

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー:")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:15} {status}")

    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100

    print("\n" + "=" * 60)
    print(f"総合評価: {passed_tests}/{total_tests} テスト合格 ({success_rate:.1f}%)")
    print("=" * 60)

    if success_rate >= 80:
        print("✅ PostgreSQLモードは正常に動作しています")
        return 0
    else:
        print("❌ PostgreSQLモードに問題があります")
        return 1


if __name__ == "__main__":
    sys.exit(main())
