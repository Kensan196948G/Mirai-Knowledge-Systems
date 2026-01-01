"""
Mirai Knowledge System API - Python使用例

このスクリプトは、MKS APIの基本的な使用方法を示します。
"""

import requests
from typing import Optional, Dict, List
import time


class MKSAPIClient:
    """Mirai Knowledge System APIクライアント"""

    def __init__(self, base_url: str = "http://localhost:5100"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()

    def login(self, username: str, password: str) -> Dict:
        """
        ログイン

        Args:
            username: ユーザー名
            password: パスワード

        Returns:
            ユーザー情報を含むレスポンス
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()

        data = response.json()
        if data["success"]:
            self.access_token = data["data"]["access_token"]
            self.refresh_token = data["data"]["refresh_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            return data["data"]["user"]
        else:
            raise Exception(f"Login failed: {data.get('error')}")

    def refresh_access_token(self) -> None:
        """アクセストークンをリフレッシュ"""
        if not self.refresh_token:
            raise Exception("Refresh token not available")

        response = self.session.post(
            f"{self.base_url}/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {self.refresh_token}"}
        )
        response.raise_for_status()

        data = response.json()
        if data["success"]:
            self.access_token = data["data"]["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })

    def get_current_user(self) -> Dict:
        """現在のユーザー情報を取得"""
        response = self.session.get(f"{self.base_url}/api/v1/auth/me")
        response.raise_for_status()
        return response.json()["data"]

    # ナレッジ管理
    def list_knowledge(self, category: Optional[str] = None,
                      search: Optional[str] = None,
                      tags: Optional[str] = None) -> List[Dict]:
        """
        ナレッジ一覧を取得

        Args:
            category: カテゴリでフィルタ
            search: 検索キーワード
            tags: タグ（カンマ区切り）

        Returns:
            ナレッジのリスト
        """
        params = {}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        if tags:
            params["tags"] = tags

        response = self.session.get(
            f"{self.base_url}/api/v1/knowledge",
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]

    def get_knowledge(self, knowledge_id: int) -> Dict:
        """ナレッジ詳細を取得"""
        response = self.session.get(
            f"{self.base_url}/api/v1/knowledge/{knowledge_id}"
        )
        response.raise_for_status()
        return response.json()["data"]

    def create_knowledge(self, title: str, summary: str, content: str,
                        category: str, tags: List[str] = None,
                        priority: str = "medium", **kwargs) -> Dict:
        """
        新規ナレッジを作成

        Args:
            title: タイトル
            summary: 概要
            content: 本文
            category: カテゴリ
            tags: タグのリスト
            priority: 優先度（low/medium/high）
            **kwargs: その他のフィールド

        Returns:
            作成されたナレッジ
        """
        data = {
            "title": title,
            "summary": summary,
            "content": content,
            "category": category,
            "tags": tags or [],
            "priority": priority,
            **kwargs
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/knowledge",
            json=data
        )
        response.raise_for_status()
        return response.json()["data"]

    # 横断検索
    def unified_search(self, query: str, types: str = "knowledge,sop,incidents",
                      highlight: bool = True) -> Dict:
        """
        横断検索を実行

        Args:
            query: 検索クエリ
            types: 検索対象タイプ（カンマ区切り）
            highlight: ハイライト有効化

        Returns:
            検索結果
        """
        params = {
            "q": query,
            "types": types,
            "highlight": str(highlight).lower()
        }

        response = self.session.get(
            f"{self.base_url}/api/v1/search/unified",
            params=params
        )
        response.raise_for_status()
        return response.json()

    # 通知管理
    def list_notifications(self) -> List[Dict]:
        """通知一覧を取得"""
        response = self.session.get(f"{self.base_url}/api/v1/notifications")
        response.raise_for_status()
        return response.json()["data"]

    def mark_notification_read(self, notification_id: int) -> None:
        """通知を既読にする"""
        response = self.session.put(
            f"{self.base_url}/api/v1/notifications/{notification_id}/read"
        )
        response.raise_for_status()

    def get_unread_count(self) -> int:
        """未読通知数を取得"""
        response = self.session.get(
            f"{self.base_url}/api/v1/notifications/unread/count"
        )
        response.raise_for_status()
        return response.json()["data"]["unread_count"]

    # ダッシュボード
    def get_dashboard_stats(self) -> Dict:
        """ダッシュボード統計を取得"""
        response = self.session.get(f"{self.base_url}/api/v1/dashboard/stats")
        response.raise_for_status()
        return response.json()["data"]


# ============================================================
# 使用例
# ============================================================

def main():
    """メイン処理"""

    # クライアント初期化
    client = MKSAPIClient("http://localhost:5100")

    # 1. ログイン
    print("=== ログイン ===")
    user = client.login("admin", "admin123")
    print(f"ログインユーザー: {user['full_name']} ({user['username']})")
    print(f"ロール: {', '.join(user['roles'])}")
    print()

    # 2. ナレッジ一覧取得
    print("=== ナレッジ一覧取得 ===")
    all_knowledge = client.list_knowledge()
    print(f"総ナレッジ数: {len(all_knowledge)}")
    print()

    # 3. カテゴリでフィルタ
    print("=== 品質管理カテゴリのナレッジ ===")
    quality_knowledge = client.list_knowledge(category="品質管理")
    print(f"品質管理ナレッジ数: {len(quality_knowledge)}")
    for k in quality_knowledge[:3]:
        print(f"  - {k['title']}")
    print()

    # 4. 検索
    print("=== キーワード検索 ===")
    search_results = client.list_knowledge(search="コンクリート")
    print(f"「コンクリート」の検索結果: {len(search_results)}件")
    for k in search_results[:3]:
        print(f"  - {k['title']}")
    print()

    # 5. 新規ナレッジ作成
    print("=== 新規ナレッジ作成 ===")
    new_knowledge = client.create_knowledge(
        title="鉄筋配筋検査のチェックポイント",
        summary="配筋検査における重要確認項目",
        content="""
## 配筋検査の目的
- 設計図書との整合性確認
- 施工精度の確認
- 構造安全性の確保

## 主要チェック項目
1. 鉄筋径・鉄筋種別の確認
2. 配筋間隔の確認
3. かぶり厚さの確認
4. 定着長・継手長の確認
5. スペーサーの配置確認
        """,
        category="品質管理",
        tags=["鉄筋工事", "配筋検査", "品質管理"],
        priority="high",
        owner="山田太郎",
        project="東京タワー建設プロジェクト"
    )
    print(f"作成されたナレッジID: {new_knowledge['id']}")
    print(f"タイトル: {new_knowledge['title']}")
    print()

    # 6. 横断検索
    print("=== 横断検索 ===")
    unified_results = client.unified_search("基礎工事", types="knowledge,sop")
    print(f"検索クエリ: {unified_results['query']}")
    print(f"総検索結果数: {unified_results['total_results']}")
    print()

    if "knowledge" in unified_results["data"]:
        knowledge_results = unified_results["data"]["knowledge"]
        print(f"ナレッジ検索結果: {knowledge_results['count']}件")
        for item in knowledge_results["items"][:3]:
            print(f"  - {item['title']} (スコア: {item.get('relevance_score', 0):.2f})")
    print()

    # 7. 通知一覧取得
    print("=== 通知一覧 ===")
    notifications = client.list_notifications()
    unread_count = client.get_unread_count()
    print(f"総通知数: {len(notifications)}")
    print(f"未読通知数: {unread_count}")

    if notifications:
        print("最新の通知:")
        for notif in notifications[:3]:
            status = "未読" if not notif.get("is_read") else "既読"
            print(f"  [{status}] {notif['title']}")
    print()

    # 8. ダッシュボード統計
    print("=== ダッシュボード統計 ===")
    stats = client.get_dashboard_stats()
    print("KPI:")
    for key, value in stats.get("kpis", {}).items():
        print(f"  {key}: {value}")

    print("\nカウント:")
    for key, value in stats.get("counts", {}).items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as e:
        print(f"HTTPエラー: {e}")
        if e.response is not None:
            print(f"レスポンス: {e.response.text}")
    except Exception as e:
        print(f"エラー: {e}")
