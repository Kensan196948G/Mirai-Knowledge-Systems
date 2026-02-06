"""
推薦APIのintegrationテスト

このテストモジュールは、推薦関連のAPIエンドポイントを検証します。
"""

import json
import os
import sys
import unittest

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from app_v2 import app, hash_password, load_data


class TestRecommendationAPI(unittest.TestCase):
    """推薦APIのテストクラス"""

    @classmethod
    def setUpClass(cls):
        """全テストの前に一度だけ実行"""
        app.config["TESTING"] = True
        app.config["JWT_SECRET_KEY"] = "test-secret-key-12345"

    def setUp(self):
        """各テストの前に実行"""
        self.client = app.test_client()
        self.test_user = None
        self.access_token = None

        # テストユーザーを作成してログイン
        self._setup_test_user()
        self._login()

    def tearDown(self):
        """各テストの後に実行"""
        # テストユーザーを削除（オプション）
        pass

    def _setup_test_user(self):
        """テスト用ユーザーを作成"""
        from app_v2 import load_users, save_users

        users = load_users()

        # テストユーザーが存在しない場合のみ作成
        test_user = next((u for u in users if u["username"] == "test_rec_user"), None)

        if not test_user:
            test_user = {
                "id": 9999,
                "username": "test_rec_user",
                "email": "test_rec@example.com",
                "password_hash": hash_password("test123"),
                "full_name": "テスト推薦ユーザー",
                "department": "テスト部門",
                "roles": ["construction_manager"],
                "is_active": True,
            }
            users.append(test_user)
            save_users(users)

        self.test_user = test_user

    def _login(self):
        """テストユーザーでログイン"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "test_rec_user", "password": "test123"},
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.access_token = data["data"]["access_token"]

    def _get_auth_headers(self):
        """認証ヘッダーを取得"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def test_get_related_knowledge_success(self):
        """関連ナレッジ取得APIのテスト（成功ケース）"""
        # ナレッジIDを取得
        knowledge_list = load_data("knowledge.json")
        if len(knowledge_list) == 0:
            self.skipTest("No knowledge data available")

        knowledge_id = knowledge_list[0]["id"]

        # APIリクエスト
        response = self.client.get(
            f"/api/v1/knowledge/{knowledge_id}/related",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("related_items", data["data"])
        self.assertIn("algorithm", data["data"])
        self.assertEqual(data["data"]["algorithm"], "hybrid")  # デフォルト

    def test_get_related_knowledge_with_parameters(self):
        """関連ナレッジ取得API（パラメータ指定）のテスト"""
        knowledge_list = load_data("knowledge.json")
        if len(knowledge_list) == 0:
            self.skipTest("No knowledge data available")

        knowledge_id = knowledge_list[0]["id"]

        # パラメータ指定
        response = self.client.get(
            f"/api/v1/knowledge/{knowledge_id}/related?algorithm=tag&limit=3",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["algorithm"], "tag")
        self.assertLessEqual(len(data["data"]["related_items"]), 3)

    def test_get_related_knowledge_invalid_id(self):
        """関連ナレッジ取得API（無効なID）のテスト"""
        response = self.client.get(
            "/api/v1/knowledge/999999/related", headers=self._get_auth_headers()
        )

        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertFalse(data["success"])

    def test_get_related_knowledge_invalid_algorithm(self):
        """関連ナレッジ取得API（無効なアルゴリズム）のテスト"""
        knowledge_list = load_data("knowledge.json")
        if len(knowledge_list) == 0:
            self.skipTest("No knowledge data available")

        knowledge_id = knowledge_list[0]["id"]

        response = self.client.get(
            f"/api/v1/knowledge/{knowledge_id}/related?algorithm=invalid",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_get_related_knowledge_invalid_limit(self):
        """関連ナレッジ取得API（無効なlimit）のテスト"""
        knowledge_list = load_data("knowledge.json")
        if len(knowledge_list) == 0:
            self.skipTest("No knowledge data available")

        knowledge_id = knowledge_list[0]["id"]

        # limit=0（無効）
        response = self.client.get(
            f"/api/v1/knowledge/{knowledge_id}/related?limit=0",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 400)

        # limit=30（上限超過）
        response = self.client.get(
            f"/api/v1/knowledge/{knowledge_id}/related?limit=30",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 400)

    def test_get_related_sop_success(self):
        """関連SOP取得APIのテスト（成功ケース）"""
        sop_list = load_data("sop.json")
        if len(sop_list) == 0:
            self.skipTest("No SOP data available")

        sop_id = sop_list[0]["id"]

        response = self.client.get(
            f"/api/v1/sop/{sop_id}/related", headers=self._get_auth_headers()
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("related_items", data["data"])

    def test_get_personalized_recommendations_success(self):
        """パーソナライズ推薦取得APIのテスト（成功ケース）"""
        response = self.client.get(
            "/api/v1/recommendations/personalized", headers=self._get_auth_headers()
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("parameters", data["data"])

    def test_get_personalized_recommendations_with_parameters(self):
        """パーソナライズ推薦取得API（パラメータ指定）のテスト"""
        response = self.client.get(
            "/api/v1/recommendations/personalized?type=knowledge&limit=3&days=7",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("knowledge", data["data"])
        self.assertEqual(data["data"]["parameters"]["type"], "knowledge")
        self.assertEqual(data["data"]["parameters"]["limit"], 3)
        self.assertEqual(data["data"]["parameters"]["days"], 7)

    def test_get_personalized_recommendations_invalid_type(self):
        """パーソナライズ推薦取得API（無効なtype）のテスト"""
        response = self.client.get(
            "/api/v1/recommendations/personalized?type=invalid",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertFalse(data["success"])

    def test_get_personalized_recommendations_invalid_limit(self):
        """パーソナライズ推薦取得API（無効なlimit）のテスト"""
        response = self.client.get(
            "/api/v1/recommendations/personalized?limit=100",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 400)

    def test_get_personalized_recommendations_invalid_days(self):
        """パーソナライズ推薦取得API（無効なdays）のテスト"""
        response = self.client.get(
            "/api/v1/recommendations/personalized?days=500",
            headers=self._get_auth_headers(),
        )

        self.assertEqual(response.status_code, 400)

    def test_recommendation_without_auth(self):
        """認証なしでのアクセステスト"""
        # 認証ヘッダーなし
        response = self.client.get("/api/v1/recommendations/personalized")

        self.assertEqual(response.status_code, 401)

        data = json.loads(response.data)
        self.assertFalse(data["success"])

    def test_cache_stats_admin_only(self):
        """キャッシュ統計取得API（管理者権限テスト）"""
        # 管理者でない場合はアクセス拒否されるべき
        response = self.client.get(
            "/api/v1/recommendations/cache/stats", headers=self._get_auth_headers()
        )

        # 管理者でない場合は403
        if "admin" not in self.test_user.get("roles", []):
            self.assertEqual(response.status_code, 403)
        else:
            self.assertEqual(response.status_code, 200)

    def test_cache_clear_admin_only(self):
        """キャッシュクリアAPI（管理者権限テスト）"""
        response = self.client.post(
            "/api/v1/recommendations/cache/clear", headers=self._get_auth_headers()
        )

        # 管理者でない場合は403
        if "admin" not in self.test_user.get("roles", []):
            self.assertEqual(response.status_code, 403)
        else:
            self.assertEqual(response.status_code, 200)


class TestRecommendationAPIPerformance(unittest.TestCase):
    """推薦APIのパフォーマンステスト"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["JWT_SECRET_KEY"] = "test-secret-key-12345"

    def setUp(self):
        self.client = app.test_client()

        # 管理者ユーザーでログイン
        response = self.client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
        )

        data = json.loads(response.data)
        self.access_token = data["data"]["access_token"]

    def _get_auth_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def test_response_time_related_knowledge(self):
        """関連ナレッジ取得のレスポンスタイムテスト"""
        knowledge_list = load_data("knowledge.json")
        if len(knowledge_list) == 0:
            self.skipTest("No knowledge data available")

        knowledge_id = knowledge_list[0]["id"]

        import time

        start_time = time.time()

        response = self.client.get(
            f"/api/v1/knowledge/{knowledge_id}/related",
            headers=self._get_auth_headers(),
        )

        elapsed_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        # 1秒以内に完了することを確認
        self.assertLess(
            elapsed_time, 1.0, f"レスポンスタイムが遅すぎます: {elapsed_time:.2f}秒"
        )

    def test_response_time_personalized_recommendations(self):
        """パーソナライズ推薦のレスポンスタイムテスト"""
        import time

        start_time = time.time()

        response = self.client.get(
            "/api/v1/recommendations/personalized?type=all&limit=10",
            headers=self._get_auth_headers(),
        )

        elapsed_time = time.time() - start_time

        self.assertEqual(response.status_code, 200)
        # 2秒以内に完了することを確認（より複雑な処理のため）
        self.assertLess(
            elapsed_time, 2.0, f"レスポンスタイムが遅すぎます: {elapsed_time:.2f}秒"
        )

    def test_concurrent_requests(self):
        """並行リクエストのテスト"""
        import concurrent.futures

        knowledge_list = load_data("knowledge.json")
        if len(knowledge_list) == 0:
            self.skipTest("No knowledge data available")

        knowledge_id = knowledge_list[0]["id"]

        def make_request():
            return self.client.get(
                f"/api/v1/knowledge/{knowledge_id}/related",
                headers=self._get_auth_headers(),
            )

        # 10個の並行リクエスト
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 全てのリクエストが成功
        for response in results:
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
