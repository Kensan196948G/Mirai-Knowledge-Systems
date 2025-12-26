"""
負荷テストシナリオ（Locust）
"""
from locust import HttpUser, task, between
import random

class KnowledgeSystemUser(HttpUser):
    """ナレッジシステムユーザーのシミュレーション"""
    wait_time = between(1, 3)  # 1-3秒待機

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

    @task(3)
    def get_knowledge_list(self):
        """ナレッジ一覧取得（重み: 3）"""
        self.client.get("/api/v1/knowledge", headers=self.headers)

    @task(2)
    def get_knowledge_detail(self):
        """ナレッジ詳細取得（重み: 2）"""
        knowledge_id = random.randint(1, 10)
        self.client.get(f"/api/v1/knowledge/{knowledge_id}",
                       headers=self.headers)

    @task(1)
    def search_knowledge(self):
        """検索（重み: 1）"""
        keywords = ['安全', '品質', '施工', 'コンクリート', '温度管理']
        keyword = random.choice(keywords)
        self.client.get(f"/api/v1/knowledge?search={keyword}",
                       headers=self.headers)

    @task(1)
    def get_dashboard_stats(self):
        """ダッシュボード統計"""
        self.client.get("/api/v1/dashboard/stats", headers=self.headers)

    @task(1)
    def unified_search(self):
        """横断検索"""
        keywords = ['砂防', '橋梁', '護岸']
        keyword = random.choice(keywords)
        self.client.get(f"/api/v1/search/unified?q={keyword}",
                       headers=self.headers)
