#!/usr/bin/env python3
"""
ヘルスモニター - システム健全性チェックとメトリクス収集
"""

import json
import os
import socket
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict
from urllib.parse import urlparse

import psutil
import requests


class HealthMonitor:
    """システムヘルスチェックを実行するクラス"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "error_patterns.json"
        )
        self.config = self._load_config()
        self.health_checks = self.config.get("health_checks", [])

    def _load_config(self) -> dict:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            return {"health_checks": []}

    def check_database_connection(self, timeout: int = 5) -> Dict[str, Any]:
        """PostgreSQL接続チェック"""
        try:
            args = ["pg_isready", "-t", str(timeout)]
            host, port = self._resolve_pg_host_port()
            if host:
                args.extend(["-h", host])
            if port:
                args.extend(["-p", str(port)])

            result = subprocess.run(
                args, capture_output=True, text=True, timeout=timeout + 1
            )

            return {
                "status": "healthy" if result.returncode == 0 else "unhealthy",
                "message": result.stdout.strip() or result.stderr.strip(),
                "timestamp": datetime.now().isoformat(),
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "unhealthy",
                "message": "Database connection timeout",
                "timestamp": datetime.now().isoformat(),
            }
        except FileNotFoundError:
            return {
                "status": "unknown",
                "message": "pg_isready command not found",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def check_redis_connection(
        self, host: str = "localhost", port: int = 6379, timeout: int = 5
    ) -> Dict[str, Any]:
        """Redis接続チェック"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return {
                    "status": "healthy",
                    "message": f"Redis is accessible on {host}:{port}",
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Cannot connect to Redis on {host}:{port}",
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def check_disk_space(self, threshold: int = 90) -> Dict[str, Any]:
        """ディスク容量チェック"""
        try:
            disk = psutil.disk_usage("/")
            usage_percent = disk.percent

            return {
                "status": "healthy" if usage_percent < threshold else "unhealthy",
                "usage_percent": usage_percent,
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "message": f"Disk usage: {usage_percent}% (threshold: {threshold}%)",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def check_memory_usage(self, threshold: int = 85) -> Dict[str, Any]:
        """メモリ使用量チェック"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            return {
                "status": "healthy" if usage_percent < threshold else "unhealthy",
                "usage_percent": usage_percent,
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "message": f"Memory usage: {usage_percent}% (threshold: {threshold}%)",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def check_http_endpoint(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """HTTPエンドポイントチェック"""
        try:
            response = requests.get(url, timeout=timeout)

            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                "message": f"HTTP {response.status_code} - Response time: {response.elapsed.total_seconds():.3f}s",
                "timestamp": datetime.now().isoformat(),
            }
        except requests.exceptions.Timeout:
            return {
                "status": "unhealthy",
                "message": f"Request timeout after {timeout}s",
                "timestamp": datetime.now().isoformat(),
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "message": "Connection refused",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _resolve_pg_host_port(self) -> tuple:
        """環境変数やDATABASE_URLからPostgreSQLの接続先を解決"""
        host = os.environ.get("PGHOST")
        port = os.environ.get("PGPORT")
        db_url = os.environ.get("DATABASE_URL")

        if db_url:
            try:
                parsed = urlparse(db_url)
                if parsed.hostname:
                    host = parsed.hostname
                if parsed.port:
                    port = parsed.port
            except Exception:
                pass

        return host, port

    def _resolve_http_check_url(self, configured_url: str) -> str:
        """HTTPヘルスチェックURLを環境変数で上書き"""
        env_url = os.environ.get("MKS_HEALTHCHECK_URL")
        if env_url:
            return env_url

        port = os.environ.get("MKS_PORT")
        if port:
            return f"http://localhost:{port}/api/health"

        return configured_url

    def _skip_http_check(self) -> bool:
        """HTTPヘルスチェックのスキップ判定"""
        return os.environ.get("MKS_SKIP_HTTP_CHECK", "").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    def check_port_available(self, port: int) -> Dict[str, Any]:
        """ポート使用状況チェック"""
        try:
            connections = psutil.net_connections()
            port_in_use = any(
                conn.laddr.port == port for conn in connections if conn.laddr
            )

            if port_in_use:
                # ポートを使用しているプロセスを特定
                for conn in connections:
                    if conn.laddr and conn.laddr.port == port:
                        try:
                            process = psutil.Process(conn.pid)
                            return {
                                "status": "in_use",
                                "port": port,
                                "pid": conn.pid,
                                "process_name": process.name(),
                                "message": f"Port {port} is in use by {process.name()} (PID: {conn.pid})",
                                "timestamp": datetime.now().isoformat(),
                            }
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                return {
                    "status": "in_use",
                    "port": port,
                    "message": f"Port {port} is in use",
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "available",
                    "port": port,
                    "message": f"Port {port} is available",
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクスを収集"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # ネットワーク統計
            net_io = psutil.net_io_counters()

            # プロセス数
            process_count = len(psutil.pids())

            return {
                "cpu": {"usage_percent": cpu_percent, "count": psutil.cpu_count()},
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": disk.percent,
                },
                "network": {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                },
                "processes": {"count": process_count},
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def run_all_checks(self) -> Dict[str, Any]:
        """すべてのヘルスチェックを実行"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "healthy",
        }

        critical_failure = False

        for check in self.health_checks:
            check_name = check["name"]
            check_type = check["type"]
            is_critical = check.get("critical", False)

            if check_type == "postgresql":
                result = self.check_database_connection(timeout=check.get("timeout", 5))
            elif check_type == "redis":
                result = self.check_redis_connection(timeout=check.get("timeout", 5))
            elif check_type == "disk":
                result = self.check_disk_space(threshold=check.get("threshold", 90))
            elif check_type == "memory":
                result = self.check_memory_usage(threshold=check.get("threshold", 85))
            elif check_type == "http":
                if self._skip_http_check():
                    result = {
                        "status": "skipped",
                        "message": "HTTP health check skipped by MKS_SKIP_HTTP_CHECK",
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    configured_url = check.get("url", "http://localhost:5000")
                    result = self.check_http_endpoint(
                        url=self._resolve_http_check_url(configured_url),
                        timeout=check.get("timeout", 10),
                    )
            else:
                result = {
                    "status": "unknown",
                    "message": f"Unknown check type: {check_type}",
                }

            results["checks"][check_name] = {**result, "critical": is_critical}

            # クリティカルなチェックが失敗した場合
            if is_critical and result.get("status") in ["unhealthy", "error"]:
                critical_failure = True

        # 全体のステータスを決定
        if critical_failure:
            results["overall_status"] = "critical"
        elif any(c.get("status") == "unhealthy" for c in results["checks"].values()):
            results["overall_status"] = "degraded"

        # システムメトリクスを追加
        results["metrics"] = self.get_system_metrics()

        return results

    def send_alert(self, message: str, severity: str = "warning"):
        """アラートを送信"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "message": message,
        }

        # ログファイルに記録
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)

        alert_log = os.path.join(log_dir, "alerts.log")
        with open(alert_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert_data, ensure_ascii=False) + "\n")

        print(f"[ALERT] [{severity.upper()}] {message}")


def main():
    """メイン処理"""
    monitor = HealthMonitor()

    # すべてのヘルスチェックを実行
    results = monitor.run_all_checks()

    # 結果を出力
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # クリティカルな問題がある場合はアラート送信
    if results["overall_status"] == "critical":
        failed_checks = [
            name
            for name, check in results["checks"].items()
            if check.get("critical") and check.get("status") in ["unhealthy", "error"]
        ]
        monitor.send_alert(
            f"Critical health check failures: {', '.join(failed_checks)}",
            severity="critical",
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
