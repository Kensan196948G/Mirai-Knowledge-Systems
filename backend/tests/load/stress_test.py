"""
ストレステスト - システム限界値測定
段階的に負荷を増加させ、システムの限界点を特定する
"""
import requests
import time
import psutil
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import statistics


class StressTest:
    """ストレステスト実行クラス"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = []
        self.system_metrics = []

    def get_auth_token(self) -> str:
        """認証トークン取得"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            return response.json()['data']['access_token']
        return None

    def collect_system_metrics(self) -> Dict:
        """システムリソース監視"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024)
        }

    def single_request(self, endpoint: str, token: str) -> Dict:
        """単一リクエスト実行"""
        headers = {'Authorization': f'Bearer {token}'}
        start_time = time.time()

        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=10
            )
            elapsed = time.time() - start_time

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": elapsed,
                "error": None
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "status_code": 0,
                "response_time": elapsed,
                "error": str(e)
            }

    def run_concurrent_requests(
        self,
        num_users: int,
        endpoint: str,
        token: str
    ) -> Dict:
        """同時リクエスト実行"""
        print(f"\n{'='*60}")
        print(f"同時ユーザー数: {num_users}")
        print(f"エンドポイント: {endpoint}")
        print(f"{'='*60}")

        # システムメトリクス収集開始
        start_metrics = self.collect_system_metrics()

        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(self.single_request, endpoint, token)
                for _ in range(num_users)
            ]

            for future in as_completed(futures):
                results.append(future.result())

        elapsed_total = time.time() - start_time

        # システムメトリクス収集終了
        end_metrics = self.collect_system_metrics()

        # 結果集計
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count
        response_times = [r['response_time'] for r in results if r['success']]

        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95パーセンタイル
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99パーセンタイル
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = 0
            p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0

        error_rate = (error_count / len(results)) * 100
        requests_per_sec = num_users / elapsed_total

        result = {
            "num_users": num_users,
            "endpoint": endpoint,
            "total_requests": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "error_rate": error_rate,
            "total_time": elapsed_total,
            "requests_per_sec": requests_per_sec,
            "avg_response_time": avg_response_time,
            "median_response_time": median_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "start_metrics": start_metrics,
            "end_metrics": end_metrics
        }

        # 結果表示
        self._print_result(result)

        return result

    def _print_result(self, result: Dict):
        """結果を整形して表示"""
        print(f"\n結果:")
        print(f"  総リクエスト数: {result['total_requests']}")
        print(f"  成功: {result['success_count']}")
        print(f"  失敗: {result['error_count']}")
        print(f"  エラー率: {result['error_rate']:.2f}%")
        print(f"  処理時間: {result['total_time']:.2f}秒")
        print(f"  RPS: {result['requests_per_sec']:.2f}")
        print(f"\n応答時間:")
        print(f"  平均: {result['avg_response_time']:.3f}秒")
        print(f"  中央値: {result['median_response_time']:.3f}秒")
        print(f"  95%ile: {result['p95_response_time']:.3f}秒")
        print(f"  99%ile: {result['p99_response_time']:.3f}秒")
        print(f"  最小: {result['min_response_time']:.3f}秒")
        print(f"  最大: {result['max_response_time']:.3f}秒")
        print(f"\nシステムリソース:")
        print(f"  CPU: {result['end_metrics']['cpu_percent']:.1f}%")
        print(f"  メモリ: {result['end_metrics']['memory_percent']:.1f}%")

        # 目標値チェック
        print(f"\n目標値チェック:")
        if result['error_rate'] <= 1.0:
            print(f"  ✓ エラー率: {result['error_rate']:.2f}% <= 1%")
        else:
            print(f"  ✗ エラー率: {result['error_rate']:.2f}% > 1%")

        if result['avg_response_time'] <= 3.0:
            print(f"  ✓ 平均応答時間: {result['avg_response_time']:.3f}秒 <= 3秒")
        else:
            print(f"  ✗ 平均応答時間: {result['avg_response_time']:.3f}秒 > 3秒")

    def run_gradual_stress_test(self):
        """段階的負荷増加テスト（100→500ユーザー）"""
        print("\n" + "="*60)
        print("段階的ストレステスト開始")
        print("="*60)

        token = self.get_auth_token()
        if not token:
            print("認証失敗")
            return

        # テストシナリオ
        endpoints = [
            "/api/v1/knowledge",
            "/api/v1/knowledge?search=砂防",
            "/api/v1/dashboard/stats",
            "/api/v1/notifications?limit=20"
        ]

        # 段階的にユーザー数を増加
        user_levels = [10, 50, 100, 200, 300, 400, 500]

        all_results = []

        for num_users in user_levels:
            for endpoint in endpoints:
                result = self.run_concurrent_requests(num_users, endpoint, token)
                all_results.append(result)

                # エラー率が10%を超えたら限界点と判定
                if result['error_rate'] > 10.0:
                    print(f"\n{'!'*60}")
                    print(f"限界点検出: {num_users}ユーザー、エラー率{result['error_rate']:.2f}%")
                    print(f"{'!'*60}")
                    self._save_results(all_results)
                    return all_results

                # 次のテストまで5秒待機
                time.sleep(5)

        self._save_results(all_results)
        return all_results

    def _save_results(self, results: List[Dict]):
        """結果をJSON/CSVで保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON保存
        json_file = f"/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/reports/stress_test_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n結果をJSON保存: {json_file}")

        # CSV保存
        csv_file = f"/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/reports/stress_test_{timestamp}.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            # ヘッダー
            f.write("ユーザー数,エンドポイント,総リクエスト,成功,失敗,エラー率(%),")
            f.write("平均応答時間(秒),中央値(秒),P95(秒),P99(秒),")
            f.write("RPS,CPU(%),メモリ(%)\n")

            # データ
            for r in results:
                f.write(f"{r['num_users']},{r['endpoint']},{r['total_requests']},")
                f.write(f"{r['success_count']},{r['error_count']},{r['error_rate']:.2f},")
                f.write(f"{r['avg_response_time']:.3f},{r['median_response_time']:.3f},")
                f.write(f"{r['p95_response_time']:.3f},{r['p99_response_time']:.3f},")
                f.write(f"{r['requests_per_sec']:.2f},")
                f.write(f"{r['end_metrics']['cpu_percent']:.1f},")
                f.write(f"{r['end_metrics']['memory_percent']:.1f}\n")

        print(f"結果をCSV保存: {csv_file}")

        # サマリー表示
        self._print_summary(results)

    def _print_summary(self, results: List[Dict]):
        """テストサマリー表示"""
        print("\n" + "="*60)
        print("ストレステスト サマリー")
        print("="*60)

        # 最大成功ユーザー数
        successful_results = [r for r in results if r['error_rate'] <= 1.0]
        if successful_results:
            max_users = max(r['num_users'] for r in successful_results)
            print(f"最大安定ユーザー数: {max_users} (エラー率 <= 1%)")

        # 最も遅いエンドポイント
        slowest = max(results, key=lambda x: x['avg_response_time'])
        print(f"\n最も遅いエンドポイント:")
        print(f"  {slowest['endpoint']}")
        print(f"  平均応答時間: {slowest['avg_response_time']:.3f}秒")
        print(f"  ユーザー数: {slowest['num_users']}")

        # 推奨最大同時接続数
        stable_300_results = [
            r for r in results
            if r['num_users'] == 300 and r['error_rate'] <= 1.0
        ]

        if stable_300_results:
            print(f"\n✓ 目標達成: 300ユーザー同時接続可能")
            avg_response = statistics.mean([r['avg_response_time'] for r in stable_300_results])
            print(f"  平均応答時間: {avg_response:.3f}秒")
        else:
            print(f"\n✗ 目標未達成: 300ユーザー同時接続でエラー率が高い")


def main():
    """メイン実行"""
    stress_test = StressTest(base_url="http://localhost:5000")
    stress_test.run_gradual_stress_test()


if __name__ == "__main__":
    main()
