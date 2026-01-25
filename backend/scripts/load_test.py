#!/usr/bin/env python3
"""
簡易負荷テストスクリプト

APIエンドポイントに対して並行リクエストを送信し、
レスポンス時間とスループットを計測します。

使用方法:
    python scripts/load_test.py [--url URL] [--requests N] [--concurrency C]

例:
    python scripts/load_test.py --requests 100 --concurrency 10
"""

import argparse
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json


def make_request(url: str, timeout: int = 10) -> dict:
    """単一リクエストを実行して結果を返す"""
    start_time = time.time()
    try:
        req = Request(url)
        req.add_header('Content-Type', 'application/json')
        with urlopen(req, timeout=timeout) as response:
            elapsed = (time.time() - start_time) * 1000  # ms
            return {
                "success": True,
                "status_code": response.status,
                "elapsed_ms": elapsed
            }
    except HTTPError as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "success": False,
            "status_code": e.code,
            "elapsed_ms": elapsed,
            "error": str(e)
        }
    except URLError as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "success": False,
            "status_code": 0,
            "elapsed_ms": elapsed,
            "error": str(e)
        }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            "success": False,
            "status_code": 0,
            "elapsed_ms": elapsed,
            "error": str(e)
        }


def run_load_test(url: str, total_requests: int, concurrency: int) -> dict:
    """負荷テストを実行"""
    print(f"\n{'='*60}")
    print(f"負荷テスト開始")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"総リクエスト数: {total_requests}")
    print(f"同時接続数: {concurrency}")
    print(f"{'='*60}\n")

    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, url) for _ in range(total_requests)]

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 10 == 0:
                print(f"進捗: {completed}/{total_requests} ({completed*100//total_requests}%)")

    total_time = time.time() - start_time

    # 結果集計
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    response_times = [r["elapsed_ms"] for r in successful]

    summary = {
        "total_requests": total_requests,
        "successful": len(successful),
        "failed": len(failed),
        "total_time_sec": round(total_time, 2),
        "requests_per_sec": round(total_requests / total_time, 2),
        "response_time": {}
    }

    if response_times:
        summary["response_time"] = {
            "min_ms": round(min(response_times), 2),
            "max_ms": round(max(response_times), 2),
            "avg_ms": round(statistics.mean(response_times), 2),
            "median_ms": round(statistics.median(response_times), 2),
            "p95_ms": round(sorted(response_times)[int(len(response_times) * 0.95)], 2) if len(response_times) >= 20 else None,
            "p99_ms": round(sorted(response_times)[int(len(response_times) * 0.99)], 2) if len(response_times) >= 100 else None
        }

    return summary


def print_results(summary: dict):
    """結果を出力"""
    print(f"\n{'='*60}")
    print(f"負荷テスト結果")
    print(f"{'='*60}")
    print(f"総リクエスト数: {summary['total_requests']}")
    print(f"成功: {summary['successful']}")
    print(f"失敗: {summary['failed']}")
    print(f"成功率: {summary['successful']*100//summary['total_requests']}%")
    print(f"{'='*60}")
    print(f"総実行時間: {summary['total_time_sec']}秒")
    print(f"スループット: {summary['requests_per_sec']} req/sec")
    print(f"{'='*60}")

    if summary["response_time"]:
        rt = summary["response_time"]
        print(f"レスポンス時間:")
        print(f"  最小: {rt['min_ms']} ms")
        print(f"  最大: {rt['max_ms']} ms")
        print(f"  平均: {rt['avg_ms']} ms")
        print(f"  中央値: {rt['median_ms']} ms")
        if rt.get('p95_ms'):
            print(f"  P95: {rt['p95_ms']} ms")
        if rt.get('p99_ms'):
            print(f"  P99: {rt['p99_ms']} ms")

    print(f"{'='*60}")

    # 評価
    avg_ms = summary["response_time"].get("avg_ms", 0)
    if avg_ms < 100:
        print("評価: 優秀 (平均100ms未満)")
    elif avg_ms < 200:
        print("評価: 良好 (平均200ms未満)")
    elif avg_ms < 500:
        print("評価: 許容範囲 (平均500ms未満)")
    else:
        print("評価: 要改善 (平均500ms以上)")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="簡易負荷テストスクリプト")
    parser.add_argument(
        "--url",
        default="http://localhost:5100/api/v1/health",
        help="テスト対象URL"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="総リクエスト数"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="同時接続数"
    )
    parser.add_argument(
        "--output",
        help="結果をJSONファイルに出力"
    )

    args = parser.parse_args()

    summary = run_load_test(args.url, args.requests, args.concurrency)
    print_results(summary)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"結果を {args.output} に保存しました")


if __name__ == "__main__":
    main()
