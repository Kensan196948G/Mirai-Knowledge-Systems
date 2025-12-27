"""
負荷テストシナリオ（Locust）- 拡張版
同時接続300ユーザー想定の5つのユーザーシナリオ
"""
from locust import HttpUser, task, between, TaskSet
import random
import json


class LoginSearchBrowseUser(HttpUser):
    """シナリオ1: ログイン → 検索 → 閲覧（重み: 50）"""
    wait_time = between(1, 3)
    weight = 50

    def on_start(self):
        """テスト開始時にログイン"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

        if response.status_code == 200:
            self.token = response.json()['data']['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.headers = {}

    @task(5)
    def search_knowledge(self):
        """検索実行（目標: 2秒以内）"""
        keywords = ['安全', '品質', '施工', 'コンクリート', '温度管理',
                   '砂防', '橋梁', '護岸', '土工', '鉄筋']
        keyword = random.choice(keywords)
        with self.client.get(
            f"/api/v1/knowledge?search={keyword}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 2.0:
                response.failure(f"検索が遅い: {response.elapsed.total_seconds()}秒")

    @task(3)
    def browse_knowledge_list(self):
        """ナレッジ一覧閲覧（目標: 3秒以内）"""
        with self.client.get(
            "/api/v1/knowledge",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 3.0:
                response.failure(f"一覧表示が遅い: {response.elapsed.total_seconds()}秒")

    @task(2)
    def browse_knowledge_detail(self):
        """ナレッジ詳細閲覧（目標: 3秒以内）"""
        knowledge_id = random.randint(1, 50)
        with self.client.get(
            f"/api/v1/knowledge/{knowledge_id}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() > 3.0:
                    response.failure(f"詳細表示が遅い: {response.elapsed.total_seconds()}秒")


class KnowledgeCreationUser(HttpUser):
    """シナリオ2: ナレッジ作成（重み: 20）"""
    wait_time = between(2, 5)
    weight = 20

    def on_start(self):
        """ログイン"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

        if response.status_code == 200:
            self.token = response.json()['data']['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.headers = {}

    @task(3)
    def create_knowledge(self):
        """ナレッジ作成（目標: 3秒以内）"""
        data = {
            "title": f"負荷テスト_{random.randint(1000, 9999)}",
            "content": "これは負荷テスト用のナレッジです。" * 10,
            "category": random.choice(["砂防", "橋梁", "護岸", "土工"]),
            "tags": ["負荷テスト", "自動生成"],
            "status": "draft"
        }
        with self.client.post(
            "/api/v1/knowledge",
            headers=self.headers,
            json=data,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 3.0:
                response.failure(f"作成が遅い: {response.elapsed.total_seconds()}秒")

    @task(2)
    def update_knowledge(self):
        """ナレッジ更新"""
        knowledge_id = random.randint(1, 50)
        data = {
            "title": f"更新_負荷テスト_{random.randint(1000, 9999)}",
            "content": "更新されたコンテンツ" * 5
        }
        self.client.put(
            f"/api/v1/knowledge/{knowledge_id}",
            headers=self.headers,
            json=data
        )

    @task(1)
    def delete_knowledge(self):
        """ナレッジ削除"""
        knowledge_id = random.randint(1, 50)
        self.client.delete(
            f"/api/v1/knowledge/{knowledge_id}",
            headers=self.headers
        )


class ApprovalOperationUser(HttpUser):
    """シナリオ3: 承認操作（重み: 15）"""
    wait_time = between(2, 4)
    weight = 15

    def on_start(self):
        """ログイン"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

        if response.status_code == 200:
            self.token = response.json()['data']['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.headers = {}

    @task(3)
    def get_approval_list(self):
        """承認待ち一覧取得"""
        self.client.get(
            "/api/v1/approvals?status=pending",
            headers=self.headers
        )

    @task(2)
    def approve_knowledge(self):
        """ナレッジ承認（目標: 3秒以内）"""
        approval_id = random.randint(1, 20)
        with self.client.post(
            f"/api/v1/approvals/{approval_id}/approve",
            headers=self.headers,
            json={"comment": "承認します"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() > 3.0:
                    response.failure(f"承認処理が遅い: {response.elapsed.total_seconds()}秒")

    @task(1)
    def reject_knowledge(self):
        """ナレッジ差戻し"""
        approval_id = random.randint(1, 20)
        self.client.post(
            f"/api/v1/approvals/{approval_id}/reject",
            headers=self.headers,
            json={"comment": "修正が必要です"}
        )


class NotificationCheckUser(HttpUser):
    """シナリオ4: 通知確認（重み: 10）"""
    wait_time = between(3, 6)
    weight = 10

    def on_start(self):
        """ログイン"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

        if response.status_code == 200:
            self.token = response.json()['data']['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.headers = {}

    @task(5)
    def get_notifications(self):
        """通知一覧取得（目標: 2秒以内）"""
        with self.client.get(
            "/api/v1/notifications?limit=20",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 2.0:
                response.failure(f"通知取得が遅い: {response.elapsed.total_seconds()}秒")

    @task(3)
    def mark_notification_read(self):
        """通知を既読にする"""
        notification_id = random.randint(1, 50)
        self.client.post(
            f"/api/v1/notifications/{notification_id}/read",
            headers=self.headers
        )

    @task(1)
    def get_unread_count(self):
        """未読件数取得"""
        self.client.get(
            "/api/v1/notifications/unread/count",
            headers=self.headers
        )


class DashboardRefreshUser(HttpUser):
    """シナリオ5: ダッシュボード更新（重み: 5）"""
    wait_time = between(5, 10)
    weight = 5

    def on_start(self):
        """ログイン"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })

        if response.status_code == 200:
            self.token = response.json()['data']['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.headers = {}

    @task(4)
    def get_dashboard_stats(self):
        """ダッシュボード統計（目標: 3秒以内）"""
        with self.client.get(
            "/api/v1/dashboard/stats",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 3.0:
                response.failure(f"統計取得が遅い: {response.elapsed.total_seconds()}秒")

    @task(3)
    def get_recent_activities(self):
        """最近のアクティビティ取得"""
        self.client.get(
            "/api/v1/dashboard/activities?limit=10",
            headers=self.headers
        )

    @task(2)
    def get_popular_knowledge(self):
        """人気ナレッジ取得"""
        self.client.get(
            "/api/v1/dashboard/popular?limit=5",
            headers=self.headers
        )

    @task(1)
    def unified_search(self):
        """横断検索（目標: 2秒以内）"""
        keywords = ['砂防', '橋梁', '護岸']
        keyword = random.choice(keywords)
        with self.client.get(
            f"/api/v1/search/unified?q={keyword}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 2.0:
                response.failure(f"横断検索が遅い: {response.elapsed.total_seconds()}秒")
