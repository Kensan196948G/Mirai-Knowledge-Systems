#!/usr/bin/env python3
"""
自動修復システムのテストスクリプト
"""

import json
import os
import sys
import time
from datetime import datetime

# モジュールのインポート
sys.path.insert(0, os.path.dirname(__file__))
from auto_fix_daemon import AutoFixDaemon
from health_monitor import HealthMonitor


def test_health_monitor():
    """ヘルスモニターのテスト"""
    print("\n=== ヘルスモニターテスト ===\n")

    monitor = HealthMonitor()

    # 個別のヘルスチェック
    print("1. データベース接続チェック")
    db_result = monitor.check_database_connection()
    print(json.dumps(db_result, ensure_ascii=False, indent=2))

    print("\n2. Redis接続チェック")
    redis_result = monitor.check_redis_connection()
    print(json.dumps(redis_result, ensure_ascii=False, indent=2))

    print("\n3. ディスク容量チェック")
    disk_result = monitor.check_disk_space()
    print(json.dumps(disk_result, ensure_ascii=False, indent=2))

    print("\n4. メモリ使用量チェック")
    memory_result = monitor.check_memory_usage()
    print(json.dumps(memory_result, ensure_ascii=False, indent=2))

    print("\n5. ポート確認（5000番）")
    port_result = monitor.check_port_available(5000)
    print(json.dumps(port_result, ensure_ascii=False, indent=2))

    print("\n6. システムメトリクス取得")
    metrics = monitor.get_system_metrics()
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    print("\n7. 全ヘルスチェック実行")
    all_results = monitor.run_all_checks()
    print(json.dumps(all_results, ensure_ascii=False, indent=2))

    assert "checks" in all_results
    assert all_results.get("overall_status") in {"healthy", "warning", "critical"}


def test_error_detection():
    """エラー検知のテスト"""
    print("\n\n=== エラー検知テスト ===\n")

    daemon = AutoFixDaemon()

    # テスト用ログファイルを作成
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    test_log = os.path.join(log_dir, "test_errors.log")

    # エラーパターンを書き込み
    test_errors = [
        "2025-12-28 10:30:00 - ERROR - HTTP/1.1 500 Internal Server Error",
        "2025-12-28 10:30:01 - ERROR - Traceback (most recent call last):",
        "2025-12-28 10:30:02 - ERROR - psycopg2.OperationalError: could not connect to server",
        "2025-12-28 10:30:03 - ERROR - FileNotFoundError: [Errno 2] No such file or directory",
        "2025-12-28 10:30:04 - ERROR - PermissionError: [Errno 13] Permission denied",
        "2025-12-28 10:30:05 - ERROR - MemoryError: Cannot allocate memory",
        "2025-12-28 10:30:06 - ERROR - OSError: [Errno 28] No space left on device",
        "2025-12-28 10:30:07 - ERROR - Address already in use: port 5000",
        "2025-12-28 10:30:08 - ERROR - JSONDecodeError: Invalid JSON",
        "2025-12-28 10:30:09 - ERROR - ConnectionRefusedError: Redis connection failed on port 6379",
    ]

    with open(test_log, "w", encoding="utf-8") as f:
        f.write("\n".join(test_errors))

    print(f"テスト用ログファイル作成: {test_log}\n")

    # エラー検知実行
    detected_errors = daemon.scan_logs([test_log])

    print(f"検出されたエラー数: {len(detected_errors)}\n")

    for i, error in enumerate(detected_errors, 1):
        print(f"{i}. {error['pattern_name']} (Severity: {error['severity']})")
        print(f"   ファイル: {error['log_file']}")
        print(f"   内容: {error['line_content'][:80]}...")
        print(f"   自動修復: {'有効' if error.get('auto_fix') else '無効'}")
        print(f"   アクション数: {len(error.get('actions', []))}")
        print()

    # テストログファイルを削除
    os.remove(test_log)

    assert len(detected_errors) > 0


def test_auto_fix_actions():
    """自動修復アクションのテスト"""
    print("\n\n=== 自動修復アクションテスト ===\n")

    daemon = AutoFixDaemon()

    # 安全なアクションのみテスト
    safe_actions = [
        {
            "type": "create_missing_dirs",
            "directories": ["data", "logs", "uploads", "cache"],
            "description": "ディレクトリ作成テスト",
        },
        {"type": "cache_clear", "description": "キャッシュクリアテスト"},
        {
            "type": "temp_file_cleanup",
            "description": "一時ファイルクリーンアップテスト",
        },
        {"type": "log_analysis", "description": "ログ分析テスト"},
        {"type": "check_port", "port": 5000, "description": "ポートチェックテスト"},
    ]

    results = []

    for action in safe_actions:
        print(f"テスト: {action['description']}")
        success = daemon.execute_action(action)
        results.append(success)
        print(f"結果: {'成功' if success else '失敗'}\n")
        time.sleep(1)

    assert all(results)


def test_detection_cycle():
    """検知サイクルのテスト"""
    print("\n\n=== 検知サイクルテスト ===\n")

    daemon = AutoFixDaemon()

    # 1回の検知サイクルを実行
    daemon.run_detection_cycle(cycle_num=1)

    print("\n検知サイクル完了")

    assert True


def main():
    """全テストを実行"""
    print("\n" + "=" * 60)
    print("エラー自動検知・自動修復システム テストスイート")
    print("=" * 60)

    results = {
        "health_monitor": False,
        "error_detection": False,
        "auto_fix_actions": False,
        "detection_cycle": False,
    }

    try:
        # 1. ヘルスモニターテスト
        test_health_monitor()
        results["health_monitor"] = True
    except Exception as e:
        print(f"\n[ERROR] ヘルスモニターテスト失敗: {e}")

    try:
        # 2. エラー検知テスト
        test_error_detection()
        results["error_detection"] = True
    except Exception as e:
        print(f"\n[ERROR] エラー検知テスト失敗: {e}")

    try:
        # 3. 自動修復アクションテスト
        test_auto_fix_actions()
        results["auto_fix_actions"] = True
    except Exception as e:
        print(f"\n[ERROR] 自動修復アクションテスト失敗: {e}")

    try:
        # 4. 検知サイクルテスト
        test_detection_cycle()
        results["detection_cycle"] = True
    except Exception as e:
        print(f"\n[ERROR] 検知サイクルテスト失敗: {e}")

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"{test_name:.<40} {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print("\n" + "-" * 60)
    print(f"合計: {passed_tests}/{total_tests} テスト成功")
    print("=" * 60 + "\n")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
