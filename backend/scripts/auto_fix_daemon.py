#!/usr/bin/env python3
"""
自動修復デーモン - エラー検知と自動修復システム
15回のエラー検知ループを実行し、5分待機後に再開する永続的な監視システム
"""

import argparse
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# ヘルスモニターをインポート
from health_monitor import HealthMonitor


class AutoFixDaemon:
    """エラー自動検知・自動修復デーモン"""

    def __init__(self, config_path: str = None, log_file: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "error_patterns.json"
        )
        self.config = self._load_config()
        self.error_patterns = self.config.get("error_patterns", [])
        self.auto_fix_config = self.config.get("auto_fix_config", {})

        # ログ設定
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = log_file or os.path.join(log_dir, "auto_fix.log")

        self._setup_logging()

        # ヘルスモニター
        self.health_monitor = HealthMonitor(config_path=self.config_path)

        # 修復履歴（クールダウン管理用）
        self.fix_history = {}

        # シャットダウンフラグ
        self.shutdown_requested = False

        # シグナルハンドラ設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"Signal {signum} received. Shutting down gracefully...")
        self.shutdown_requested = True

    def _setup_logging(self):
        """ロギング設定"""
        self.logger = logging.getLogger("AutoFixDaemon")
        self.logger.setLevel(logging.INFO)

        # ファイルハンドラ
        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)

        # コンソールハンドラ
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # フォーマッター
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def _load_config(self) -> dict:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            return {"error_patterns": [], "auto_fix_config": {}}

    def scan_logs(self, log_paths: List[str]) -> List[Dict[str, Any]]:
        """ログファイルをスキャンしてエラーを検出"""
        detected_errors = []

        for log_path in log_paths:
            if not os.path.exists(log_path):
                continue

            try:
                # 最後の1000行を読み込み（パフォーマンス考慮）
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-1000:]

                for pattern_config in self.error_patterns:
                    pattern = pattern_config["pattern"]
                    regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)

                    for line_num, line in enumerate(lines, 1):
                        if regex.search(line):
                            detected_errors.append(
                                {
                                    "pattern_id": pattern_config["id"],
                                    "pattern_name": pattern_config["name"],
                                    "severity": pattern_config["severity"],
                                    "log_file": log_path,
                                    "line_number": len(lines) - 1000 + line_num,
                                    "line_content": line.strip(),
                                    "timestamp": datetime.now().isoformat(),
                                    "auto_fix": pattern_config.get("auto_fix", False),
                                    "actions": pattern_config.get("actions", []),
                                }
                            )

            except Exception as e:
                self.logger.error(f"ログファイル読み込みエラー ({log_path}): {e}")

        return detected_errors

    def execute_action(self, action: Dict[str, Any]) -> bool:
        """修復アクションを実行"""
        action_type = action.get("type")
        description = action.get("description", "")

        self.logger.info(f"修復アクション実行: {action_type} - {description}")

        try:
            if action_type == "service_restart":
                return self._restart_service(action.get("service"))

            elif action_type == "log_rotate":
                return self._rotate_logs()

            elif action_type == "cache_clear":
                return self._clear_cache()

            elif action_type == "temp_file_cleanup":
                return self._cleanup_temp_files()

            elif action_type == "create_missing_dirs":
                return self._create_missing_directories(action.get("directories", []))

            elif action_type == "fix_permissions":
                return self._fix_permissions(
                    action.get("paths", []), action.get("owner"), action.get("mode")
                )

            elif action_type == "check_port":
                return self._check_port(action.get("port"))

            elif action_type == "kill_process_on_port":
                return self._kill_process_on_port(action.get("port"))

            elif action_type == "database_vacuum":
                return self._database_vacuum()

            elif action_type == "backup_and_fix_json":
                return self._backup_and_fix_json()

            elif action_type == "old_file_cleanup":
                return self._cleanup_old_files(action.get("days", 30))

            elif action_type == "alert":
                self.logger.warning(f"アラート: {description}")
                return True

            elif action_type == "log_analysis":
                return self._analyze_logs()

            else:
                self.logger.warning(f"未知のアクションタイプ: {action_type}")
                return False

        except Exception as e:
            self.logger.error(f"アクション実行エラー ({action_type}): {e}")
            return False

    def _restart_service(self, service_name: str) -> bool:
        """サービスを再起動"""
        if not service_name:
            return False

        try:
            # Flaskアプリの場合は特別処理
            if service_name == "flask_app":
                # プロセスを探して再起動
                result = subprocess.run(
                    ["pgrep", "-f", "app.py"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    pids = result.stdout.strip().split("\n")
                    for pid in pids:
                        subprocess.run(["kill", "-HUP", pid])
                    self.logger.info(f"Flask app reloaded (PIDs: {', '.join(pids)})")
                return True

            # systemdサービスの再起動
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.logger.info(f"サービス再起動成功: {service_name}")
                return True
            else:
                self.logger.error(
                    f"サービス再起動失敗: {service_name} - {result.stderr}"
                )
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"サービス再起動タイムアウト: {service_name}")
            return False
        except Exception as e:
            self.logger.error(f"サービス再起動エラー: {e}")
            return False

    def _rotate_logs(self) -> bool:
        """ログファイルをローテーション"""
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for log_file in Path(log_dir).glob("*.log"):
                if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB以上
                    archive_name = f"{log_file.stem}_{timestamp}.log.gz"
                    archive_path = log_dir / archive_name

                    # gzip圧縮
                    subprocess.run(
                        ["gzip", "-c", str(log_file)],
                        stdout=open(archive_path, "wb"),
                        check=True,
                    )

                    # 元のファイルをクリア
                    with open(log_file, "w") as f:
                        f.write("")

                    self.logger.info(
                        f"ログローテーション完了: {log_file.name} -> {archive_name}"
                    )

            return True

        except Exception as e:
            self.logger.error(f"ログローテーションエラー: {e}")
            return False

    def _clear_cache(self) -> bool:
        """キャッシュをクリア"""
        try:
            cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "cache"
            )
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir)
                self.logger.info("キャッシュクリア完了")
                return True
            return True

        except Exception as e:
            self.logger.error(f"キャッシュクリアエラー: {e}")
            return False

    def _cleanup_temp_files(self) -> bool:
        """一時ファイルを削除"""
        try:
            temp_patterns = ["/tmp/*.tmp", "/tmp/flask_*", "/var/tmp/*.tmp"]

            for pattern in temp_patterns:
                subprocess.run(
                    f"find {os.path.dirname(pattern)} -name '{os.path.basename(pattern)}' -type f -mtime +1 -delete",
                    shell=True,
                    capture_output=True,
                )

            self.logger.info("一時ファイルクリーンアップ完了")
            return True

        except Exception as e:
            self.logger.error(f"一時ファイルクリーンアップエラー: {e}")
            return False

    def _create_missing_directories(self, directories: List[str]) -> bool:
        """必要なディレクトリを作成"""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))

            for directory in directories:
                dir_path = os.path.join(base_dir, directory)
                os.makedirs(dir_path, exist_ok=True)
                self.logger.info(f"ディレクトリ作成: {dir_path}")

            return True

        except Exception as e:
            self.logger.error(f"ディレクトリ作成エラー: {e}")
            return False

    def _fix_permissions(
        self, paths: List[str], owner: str = None, mode: str = None
    ) -> bool:
        """ファイル権限を修正"""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))

            for path in paths:
                full_path = os.path.join(base_dir, path)

                if mode:
                    subprocess.run(["chmod", "-R", mode, full_path], check=True)
                    self.logger.info(f"権限変更: {full_path} -> {mode}")

                if owner:
                    subprocess.run(
                        ["sudo", "chown", "-R", owner, full_path], check=True
                    )
                    self.logger.info(f"所有者変更: {full_path} -> {owner}")

            return True

        except Exception as e:
            self.logger.error(f"権限修正エラー: {e}")
            return False

    def _check_port(self, port: int) -> bool:
        """ポートの状態をチェック"""
        result = self.health_monitor.check_port_available(port)
        self.logger.info(f"ポートチェック: {port} - {result.get('status')}")
        return result.get("status") != "error"

    def _kill_process_on_port(self, port: int) -> bool:
        """ポートを使用しているプロセスを終了"""
        try:
            result = subprocess.run(
                f"lsof -ti:{port}", shell=True, capture_output=True, text=True
            )

            if result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    subprocess.run(["kill", "-9", pid])
                    self.logger.info(f"プロセス終了: PID {pid} (Port {port})")

                return True

            return True

        except Exception as e:
            self.logger.error(f"プロセス終了エラー: {e}")
            return False

    def _database_vacuum(self) -> bool:
        """データベースVACUUM実行"""
        try:
            # PostgreSQL VACUUM
            result = subprocess.run(
                ["vacuumdb", "--all", "--analyze"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                self.logger.info("データベースVACUUM完了")
                return True
            else:
                self.logger.error(f"データベースVACUUMエラー: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("データベースVACUUMタイムアウト")
            return False
        except Exception as e:
            self.logger.error(f"データベースVACUUMエラー: {e}")
            return False

    def _backup_and_fix_json(self) -> bool:
        """破損したJSONファイルをバックアップして修復"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for json_file in Path(data_dir).glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError:
                    # バックアップ
                    backup_file = json_file.with_suffix(f".{timestamp}.bak")
                    shutil.copy2(json_file, backup_file)

                    # 空の配列で初期化
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump([], f, ensure_ascii=False, indent=2)

                    self.logger.warning(
                        f"破損したJSONファイルを修復: {json_file.name} (バックアップ: {backup_file.name})"
                    )

            return True

        except Exception as e:
            self.logger.error(f"JSON修復エラー: {e}")
            return False

    def _cleanup_old_files(self, days: int) -> bool:
        """古いファイルを削除"""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            cutoff_date = datetime.now() - timedelta(days=days)

            for directory in ["logs", "cache", "uploads"]:
                dir_path = os.path.join(base_dir, directory)
                if not os.path.exists(dir_path):
                    continue

                for file_path in Path(dir_path).rglob("*"):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            file_path.unlink()
                            self.logger.info(f"古いファイル削除: {file_path}")

            return True

        except Exception as e:
            self.logger.error(f"古いファイル削除エラー: {e}")
            return False

    def _analyze_logs(self) -> bool:
        """ログの詳細分析"""
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            app_log = os.path.join(log_dir, "app.log")

            if not os.path.exists(app_log):
                return True

            # エラーパターンの統計を収集
            error_stats = {}

            with open(app_log, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-1000:]

            for pattern_config in self.error_patterns:
                pattern = pattern_config["pattern"]
                regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                matches = sum(1 for line in lines if regex.search(line))

                if matches > 0:
                    error_stats[pattern_config["name"]] = matches

            if error_stats:
                self.logger.info(
                    f"エラー統計: {json.dumps(error_stats, ensure_ascii=False)}"
                )

            return True

        except Exception as e:
            self.logger.error(f"ログ分析エラー: {e}")
            return False

    def is_in_cooldown(self, pattern_id: str) -> bool:
        """クールダウン期間中かチェック"""
        if pattern_id not in self.fix_history:
            return False

        last_fix_time = self.fix_history[pattern_id]
        cooldown_period = self.auto_fix_config.get("cooldown_period", 300)

        return (datetime.now() - last_fix_time).total_seconds() < cooldown_period

    def auto_fix_error(self, error: Dict[str, Any]) -> bool:
        """エラーを自動修復"""
        pattern_id = error["pattern_id"]

        # クールダウンチェック
        if self.is_in_cooldown(pattern_id):
            self.logger.info(f"クールダウン期間中: {pattern_id}")
            return False

        # 自動修復が有効かチェック
        if not error.get("auto_fix", False):
            self.logger.info(f"自動修復無効: {pattern_id}")
            return False

        self.logger.warning(
            f"エラー検出: {error['pattern_name']} "
            f"(Severity: {error['severity']}, File: {error['log_file']})"
        )

        # バックアップ（設定されている場合）
        if self.auto_fix_config.get("backup_before_fix", True):
            self._create_backup()

        # アクションを実行
        success = True
        for action in error.get("actions", []):
            if not self.execute_action(action):
                success = False

        # 修復履歴を記録
        if success:
            self.fix_history[pattern_id] = datetime.now()
            self.logger.info(f"自動修復完了: {pattern_id}")
        else:
            self.logger.error(f"自動修復失敗: {pattern_id}")

        return success

    def _create_backup(self):
        """重要なファイルをバックアップ"""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            backup_dir = os.path.join(base_dir, "backups")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            os.makedirs(backup_dir, exist_ok=True)

            # データディレクトリをバックアップ
            data_dir = os.path.join(base_dir, "data")
            if os.path.exists(data_dir):
                backup_path = os.path.join(backup_dir, f"data_{timestamp}.tar.gz")
                subprocess.run(
                    ["tar", "-czf", backup_path, "-C", base_dir, "data"], check=True
                )
                self.logger.info(f"バックアップ作成: {backup_path}")

        except Exception as e:
            self.logger.error(f"バックアップエラー: {e}")

    def run_detection_cycle(self, cycle_num: int):
        """1回の検知サイクルを実行"""
        self.logger.info(f"=== 検知サイクル {cycle_num} 開始 ===")

        # ヘルスチェック実行
        health_results = self.health_monitor.run_all_checks()
        self.logger.info(f"ヘルスチェック完了: {health_results['overall_status']}")

        # ログファイルをスキャン
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        log_files = [
            os.path.join(log_dir, "app.log"),
            os.path.join(log_dir, "auto_fix.log"),
            "/var/log/syslog",
            "/var/log/postgresql/postgresql.log",
        ]

        detected_errors = self.scan_logs(log_files)

        if detected_errors:
            self.logger.warning(f"{len(detected_errors)} 件のエラーを検出")

            # エラーごとに自動修復を試行
            for error in detected_errors:
                self.auto_fix_error(error)
        else:
            self.logger.info("エラーは検出されませんでした")

        self.logger.info(f"=== 検知サイクル {cycle_num} 完了 ===\n")

    def run_continuous(self, loop_count: int = 15, wait_minutes: int = 5):
        """継続的な監視を実行"""
        self.logger.info("自動修復デーモン起動")
        self.logger.info(f"設定: {loop_count}回ループ、{wait_minutes}分待機後再開")

        iteration = 0

        while not self.shutdown_requested:
            iteration += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"イテレーション {iteration} 開始")
            self.logger.info(f"{'='*60}\n")

            # 15回のループを実行
            for cycle in range(1, loop_count + 1):
                if self.shutdown_requested:
                    break

                self.run_detection_cycle(cycle)
                time.sleep(2)  # ループ間の短い待機

            if self.shutdown_requested:
                break

            # 5分待機
            self.logger.info(f"\n{wait_minutes}分間待機します...\n")
            for _ in range(wait_minutes * 60):
                if self.shutdown_requested:
                    break
                time.sleep(1)

        self.logger.info("自動修復デーモン停止")


def fix_import_errors(log_file: str = "import_errors.log") -> bool:
    """Import エラーを検知・修復（PR自動修復用）"""
    if not os.path.exists(log_file):
        print(f"[PR MODE] Import エラーログが見つかりません: {log_file}")
        return False

    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        log = f.read()

    # "ModuleNotFoundError: No module named 'xxx'" を検出
    import re

    missing_modules = re.findall(r"ModuleNotFoundError: No module named '(\w+)'", log)

    if missing_modules:
        print(f"[PR MODE] 不足モジュール検出: {missing_modules}")
        for module in missing_modules:
            try:
                # requirements.txt に追加（既存の場合はスキップ）
                print(f"[PR MODE] モジュールインストール中: {module}")
                subprocess.run(
                    ["pip", "install", module, "--break-system-packages"],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"[PR MODE] モジュールインストール失敗: {module} - {e}")
        return True

    print("[PR MODE] Import エラーは検出されませんでした")
    return False


def fix_lint_errors() -> bool:
    """Lint エラーを自動修復（PR自動修復用）"""
    fixed = False

    # black でフォーマット
    try:
        print("[PR MODE] black による自動フォーマット実行中...")
        result = subprocess.run(
            ["black", "backend/"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print("[PR MODE] black 完了")
        else:
            print(f"[PR MODE] black 警告: {result.stderr}")
    except Exception as e:
        print(f"[PR MODE] black エラー: {e}")

    # isort で import 整理
    try:
        print("[PR MODE] isort による import 整理中...")
        result = subprocess.run(
            ["isort", "backend/"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print("[PR MODE] isort 完了")
        else:
            print(f"[PR MODE] isort 警告: {result.stderr}")
    except Exception as e:
        print(f"[PR MODE] isort エラー: {e}")

    # 変更があるか確認
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )

    if result.stdout.strip():
        print("[PR MODE] Lint 修復により変更が発生しました")
        print(result.stdout)
        fixed = True
    else:
        print("[PR MODE] Lint エラーは検出されませんでした")

    return fixed


def main_pr_mode():
    """PRモード（GitHub Actionsから呼び出し）"""
    print("=" * 60)
    print("[PR MODE] 自動修復開始")
    print("=" * 60)

    fixed = False

    # 1. Import エラー修復
    print("\n[STEP 1] Import エラー修復")
    if os.path.exists("import_errors.log"):
        fixed |= fix_import_errors("import_errors.log")
    else:
        print("[PR MODE] import_errors.log が存在しません（スキップ）")

    # 2. Lint エラー修復
    print("\n[STEP 2] Lint エラー修復")
    fixed |= fix_lint_errors()

    # 3. 結果報告
    print("\n" + "=" * 60)
    if fixed:
        print("[PR MODE] ✅ 修復完了（変更あり）")
        print("=" * 60)
        sys.exit(0)
    else:
        print("[PR MODE] ℹ️  修復不要（変更なし）")
        print("=" * 60)
        sys.exit(1)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="エラー自動検知・自動修復デーモン")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="継続的な監視モード（15回ループ後5分待機を繰り返す）",
    )
    parser.add_argument("--config", type=str, help="設定ファイルパス", default=None)
    parser.add_argument("--log-file", type=str, help="ログファイルパス", default=None)
    parser.add_argument(
        "--loop-count",
        type=int,
        default=15,
        help="1イテレーションあたりのループ回数（デフォルト: 15）",
    )
    parser.add_argument(
        "--wait-minutes",
        type=int,
        default=5,
        help="イテレーション間の待機時間（分）（デフォルト: 5）",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="1回だけ検知サイクルを実行（デフォルト動作と互換）",
    )
    parser.add_argument(
        "--pr-mode", action="store_true", help="PR自動修復モード（GitHub Actions用）"
    )

    args = parser.parse_args()

    # PRモード
    if args.pr_mode:
        main_pr_mode()
        return

    # デーモン起動
    daemon = AutoFixDaemon(config_path=args.config, log_file=args.log_file)

    if args.continuous:
        daemon.run_continuous(
            loop_count=args.loop_count, wait_minutes=args.wait_minutes
        )
    else:
        # 1回だけ実行（--once 互換）
        daemon.run_detection_cycle(1)


if __name__ == "__main__":
    main()
