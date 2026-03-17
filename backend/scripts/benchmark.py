#!/usr/bin/env python3
"""
Phase I-5: パフォーマンスベンチマーク
目標: 82 req/sec → 150+ req/sec

使用方法:
  python scripts/benchmark.py --url http://localhost:5200 --token <JWT> --requests 100
"""
import argparse
import concurrent.futures
import time
from statistics import mean, median, stdev

import urllib.request
import urllib.error


def make_request(url: str, token: str) -> dict:
    """単一リクエストの実行と計測"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
            elapsed = time.perf_counter() - start
            return {"status": resp.status, "duration": elapsed, "error": None}
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        return {"status": e.code, "duration": elapsed, "error": str(e)}
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {"status": 0, "duration": elapsed, "error": str(e)}


def benchmark(url: str, token: str, n_requests: int, concurrency: int) -> dict:
    """ベンチマーク実行"""
    print(f"Benchmarking: {url}")
    print(f"Requests: {n_requests}, Concurrency: {concurrency}")
    print("-" * 50)

    results = []
    start_total = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, url, token) for _ in range(n_requests)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_time = time.perf_counter() - start_total

    durations = [r["duration"] for r in results if r["error"] is None]
    errors = [r for r in results if r["error"] is not None]

    if not durations:
        print("ERROR: All requests failed")
        return {}

    throughput = len(durations) / total_time

    stats = {
        "total_requests": n_requests,
        "successful": len(durations),
        "failed": len(errors),
        "total_time_sec": round(total_time, 2),
        "throughput_rps": round(throughput, 2),
        "latency_mean_ms": round(mean(durations) * 1000, 2),
        "latency_median_ms": round(median(durations) * 1000, 2),
        "latency_p95_ms": round(sorted(durations)[int(len(durations) * 0.95)] * 1000, 2),
        "latency_min_ms": round(min(durations) * 1000, 2),
        "latency_max_ms": round(max(durations) * 1000, 2),
    }
    if len(durations) > 1:
        stats["latency_stdev_ms"] = round(stdev(durations) * 1000, 2)

    print(f"✅ Throughput     : {stats['throughput_rps']} req/sec")
    print(f"   Total time     : {stats['total_time_sec']}s")
    print(f"   Success        : {stats['successful']}/{stats['total_requests']}")
    print(f"   Latency mean   : {stats['latency_mean_ms']}ms")
    print(f"   Latency median : {stats['latency_median_ms']}ms")
    print(f"   Latency p95    : {stats['latency_p95_ms']}ms")
    print(f"   Latency min    : {stats['latency_min_ms']}ms")
    print(f"   Latency max    : {stats['latency_max_ms']}ms")

    target_rps = 150
    status = "✅ 目標達成" if stats['throughput_rps'] >= target_rps else f"⚠️ 目標未達（目標: {target_rps} req/sec）"
    print(f"\n{status}")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MKS Performance Benchmark")
    parser.add_argument("--url", default="http://localhost:5200/api/health", help="ベンチマーク対象URL")
    parser.add_argument("--token", default="", help="JWT Bearer Token")
    parser.add_argument("--requests", type=int, default=100, help="総リクエスト数")
    parser.add_argument("--concurrency", type=int, default=10, help="並列リクエスト数")
    args = parser.parse_args()

    benchmark(args.url, args.token, args.requests, args.concurrency)
