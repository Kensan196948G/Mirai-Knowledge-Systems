"""
パフォーマンスベンチマーク
主要画面の応答時間を測定し、結果をJSON/CSVで出力
"""

import csv
import json
import statistics
import time
from datetime import datetime
from typing import Dict

import requests


class PerformanceBenchmark:
    """パフォーマンスベンチマーク実行クラス"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.results = []

    def setup(self):
        """初期設定（認証）"""
        print("認証トークン取得中...")
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )

        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]
            print("✓ 認証成功\n")
            return True
        else:
            print("✗ 認証失敗\n")
            return False

    def measure_endpoint(
        self,
        name: str,
        endpoint: str,
        method: str = "GET",
        data: Dict = None,
        iterations: int = 10,
    ) -> Dict:
        """エンドポイントの応答時間測定"""
        print(f"測定中: {name}")
        print(f"  エンドポイント: {endpoint}")
        print(f"  試行回数: {iterations}")

        headers = {"Authorization": f"Bearer {self.token}"}
        response_times = []
        errors = 0

        for i in range(iterations):
            start_time = time.time()

            try:
                if method == "GET":
                    response = requests.get(
                        f"{self.base_url}{endpoint}", headers=headers, timeout=10
                    )
                elif method == "POST":
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json=data,
                        timeout=10,
                    )
                elif method == "PUT":
                    response = requests.put(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json=data,
                        timeout=10,
                    )

                elapsed = time.time() - start_time

                if response.status_code in [200, 201]:
                    response_times.append(elapsed)
                else:
                    errors += 1

            except Exception as e:
                errors += 1
                print(f"  エラー: {str(e)}")

            # 次の測定まで少し待機
            time.sleep(0.5)

        if not response_times:
            print("  ✗ 全ての試行が失敗しました\n")
            return None

        # 統計計算
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0

        # パーセンタイル計算
        if len(response_times) >= 20:
            p95_time = statistics.quantiles(response_times, n=20)[18]
            p99_time = (
                statistics.quantiles(response_times, n=100)[98]
                if len(response_times) >= 100
                else max_time
            )
        else:
            p95_time = max_time
            p99_time = max_time

        result = {
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "success_count": len(response_times),
            "error_count": errors,
            "avg_time": avg_time,
            "median_time": median_time,
            "min_time": min_time,
            "max_time": max_time,
            "p95_time": p95_time,
            "p99_time": p99_time,
            "std_dev": std_dev,
            "timestamp": datetime.now().isoformat(),
        }

        # 結果表示
        self._print_result(result)

        return result

    def _print_result(self, result: Dict):
        """測定結果を表示"""
        print(f"  平均: {result['avg_time']:.3f}秒")
        print(f"  中央値: {result['median_time']:.3f}秒")
        print(f"  最小: {result['min_time']:.3f}秒")
        print(f"  最大: {result['max_time']:.3f}秒")
        print(f"  P95: {result['p95_time']:.3f}秒")
        print(f"  標準偏差: {result['std_dev']:.3f}秒")
        print(f"  成功: {result['success_count']}/{result['iterations']}")

        # 目標値チェック
        target_time = 3.0
        if "検索" in result["name"]:
            target_time = 2.0

        if result["avg_time"] <= target_time:
            print(f"  ✓ 目標達成 (平均 {result['avg_time']:.3f}秒 <= {target_time}秒)")
        else:
            print(f"  ✗ 目標未達成 (平均 {result['avg_time']:.3f}秒 > {target_time}秒)")

        print()

    def run_benchmark(self):
        """ベンチマーク実行"""
        print("\n" + "=" * 60)
        print("パフォーマンスベンチマーク開始")
        print("=" * 60 + "\n")

        if not self.setup():
            return

        # 主要画面のベンチマーク定義
        benchmarks = [
            # 画面: ダッシュボード（目標: 3秒以内）
            {
                "name": "ダッシュボード - 統計情報",
                "endpoint": "/api/v1/dashboard/stats",
                "method": "GET",
            },
            {
                "name": "ダッシュボード - 最近のアクティビティ",
                "endpoint": "/api/v1/dashboard/activities?limit=10",
                "method": "GET",
            },
            {
                "name": "ダッシュボード - 人気ナレッジ",
                "endpoint": "/api/v1/dashboard/popular?limit=5",
                "method": "GET",
            },
            # 画面: ナレッジ一覧（目標: 3秒以内）
            {
                "name": "ナレッジ一覧 - 全件",
                "endpoint": "/api/v1/knowledge",
                "method": "GET",
            },
            {
                "name": "ナレッジ一覧 - ページネーション",
                "endpoint": "/api/v1/knowledge?page=1&limit=20",
                "method": "GET",
            },
            # 画面: ナレッジ詳細（目標: 3秒以内）
            {
                "name": "ナレッジ詳細",
                "endpoint": "/api/v1/knowledge/1",
                "method": "GET",
            },
            # 機能: 検索（目標: 2秒以内）
            {
                "name": "検索 - キーワード検索",
                "endpoint": "/api/v1/knowledge?search=砂防",
                "method": "GET",
            },
            {
                "name": "検索 - 横断検索",
                "endpoint": "/api/v1/search/unified?q=橋梁",
                "method": "GET",
            },
            {
                "name": "検索 - 全文検索",
                "endpoint": "/api/v1/search/fulltext?q=コンクリート",
                "method": "GET",
            },
            # 画面: 通知（目標: 2秒以内）
            {
                "name": "通知一覧",
                "endpoint": "/api/v1/notifications?limit=20",
                "method": "GET",
            },
            {
                "name": "未読通知数",
                "endpoint": "/api/v1/notifications/unread/count",
                "method": "GET",
            },
            # 画面: 承認（目標: 3秒以内）
            {
                "name": "承認待ち一覧",
                "endpoint": "/api/v1/approvals?status=pending",
                "method": "GET",
            },
            # 機能: ナレッジ作成（目標: 3秒以内）
            {
                "name": "ナレッジ作成",
                "endpoint": "/api/v1/knowledge",
                "method": "POST",
                "data": {
                    "title": "ベンチマークテスト",
                    "content": "これはベンチマーク用のテストデータです。",
                    "category": "砂防",
                    "tags": ["テスト"],
                    "status": "draft",
                },
            },
            # 機能: ナレッジ更新（目標: 3秒以内）
            {
                "name": "ナレッジ更新",
                "endpoint": "/api/v1/knowledge/1",
                "method": "PUT",
                "data": {"title": "更新テスト", "content": "更新されたコンテンツ"},
            },
        ]

        # 各ベンチマーク実行
        for benchmark in benchmarks:
            result = self.measure_endpoint(
                name=benchmark["name"],
                endpoint=benchmark["endpoint"],
                method=benchmark.get("method", "GET"),
                data=benchmark.get("data"),
                iterations=10,
            )

            if result:
                self.results.append(result)

        # 結果保存
        self.save_results()

        # サマリー表示
        self.print_summary()

    def save_results(self):
        """結果をJSON/CSVで保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON保存
        json_file = f"/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/reports/benchmark_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n結果をJSON保存: {json_file}")

        # CSV保存
        csv_file = f"/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/reports/benchmark_{timestamp}.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            if not self.results:
                return

            fieldnames = [
                "機能名",
                "エンドポイント",
                "メソッド",
                "試行回数",
                "平均(秒)",
                "中央値(秒)",
                "最小(秒)",
                "最大(秒)",
                "P95(秒)",
                "P99(秒)",
                "標準偏差",
                "成功",
                "エラー",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in self.results:
                writer.writerow(
                    {
                        "機能名": r["name"],
                        "エンドポイント": r["endpoint"],
                        "メソッド": r["method"],
                        "試行回数": r["iterations"],
                        "平均(秒)": f"{r['avg_time']:.3f}",
                        "中央値(秒)": f"{r['median_time']:.3f}",
                        "最小(秒)": f"{r['min_time']:.3f}",
                        "最大(秒)": f"{r['max_time']:.3f}",
                        "P95(秒)": f"{r['p95_time']:.3f}",
                        "P99(秒)": f"{r['p99_time']:.3f}",
                        "標準偏差": f"{r['std_dev']:.3f}",
                        "成功": r["success_count"],
                        "エラー": r["error_count"],
                    }
                )

        print(f"結果をCSV保存: {csv_file}")

    def print_summary(self):
        """ベンチマークサマリー表示"""
        if not self.results:
            return

        print("\n" + "=" * 60)
        print("ベンチマーク サマリー")
        print("=" * 60 + "\n")

        # 目標値チェック
        main_screens = [
            r
            for r in self.results
            if "一覧" in r["name"]
            or "詳細" in r["name"]
            or "ダッシュボード" in r["name"]
        ]
        search_functions = [r for r in self.results if "検索" in r["name"]]

        # 主要画面（3秒以内）
        main_screen_ok = [r for r in main_screens if r["avg_time"] <= 3.0]
        print("主要画面（目標: 3秒以内）:")
        print(f"  合格: {len(main_screen_ok)}/{len(main_screens)}")
        for r in main_screens:
            status = "✓" if r["avg_time"] <= 3.0 else "✗"
            print(f"  {status} {r['name']}: {r['avg_time']:.3f}秒")

        # 検索（2秒以内）
        print("\n検索機能（目標: 2秒以内）:")
        search_ok = [r for r in search_functions if r["avg_time"] <= 2.0]
        print(f"  合格: {len(search_ok)}/{len(search_functions)}")
        for r in search_functions:
            status = "✓" if r["avg_time"] <= 2.0 else "✗"
            print(f"  {status} {r['name']}: {r['avg_time']:.3f}秒")

        # 最も遅い処理
        slowest = max(self.results, key=lambda x: x["avg_time"])
        print("\n最も遅い処理:")
        print(f"  {slowest['name']}: {slowest['avg_time']:.3f}秒")

        # 最も速い処理
        fastest = min(self.results, key=lambda x: x["avg_time"])
        print("\n最も速い処理:")
        print(f"  {fastest['name']}: {fastest['avg_time']:.3f}秒")

        # エラー率
        total_requests = sum(
            r["success_count"] + r["error_count"] for r in self.results
        )
        total_errors = sum(r["error_count"] for r in self.results)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        print(f"\nエラー率: {error_rate:.2f}%")
        if error_rate <= 1.0:
            print(f"  ✓ 目標達成 (エラー率 {error_rate:.2f}% <= 1%)")
        else:
            print(f"  ✗ 目標未達成 (エラー率 {error_rate:.2f}% > 1%)")

        print("\n" + "=" * 60 + "\n")


def main():
    """メイン実行"""
    benchmark = PerformanceBenchmark(base_url="http://localhost:5000")
    benchmark.run_benchmark()


if __name__ == "__main__":
    main()
