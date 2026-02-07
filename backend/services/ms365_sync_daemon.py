#!/usr/bin/env python3
"""
Microsoft 365同期デーモン

スケジューラーを常駐させて定期同期を実行するデーモンプロセス
systemdサービスとして実行されることを想定
"""

import logging
import os
import signal
import sys
import time
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from data_access import DataAccessLayer
from services.ms365_scheduler_service import MS365SchedulerService

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.environ.get("MKS_LOG_FILE", "logs/ms365-sync-daemon.log")
        ),
    ],
)

logger = logging.getLogger(__name__)

# グローバル変数
scheduler_service = None
shutdown_requested = False


def signal_handler(signum, frame):
    """
    シグナルハンドラ（SIGTERM, SIGINT）

    Args:
        signum: シグナル番号
        frame: スタックフレーム
    """
    global shutdown_requested
    logger.info(f"シャットダウンシグナル受信: {signum}")
    shutdown_requested = True

    # スケジューラー停止
    if scheduler_service:
        scheduler_service.stop()


def main():
    """メイン処理"""
    global scheduler_service

    logger.info("=== Microsoft 365 Sync Daemon 起動 ===")

    # シグナルハンドラ登録
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # データアクセスレイヤー初期化
        dal = DataAccessLayer()
        logger.info("データアクセスレイヤー初期化完了")

        # スケジューラーサービス初期化
        scheduler_service = MS365SchedulerService(dal)
        logger.info("スケジューラーサービス初期化完了")

        # スケジューラー開始
        if scheduler_service.start():
            logger.info("スケジューラー起動成功")

            # スケジュール一覧表示
            jobs = scheduler_service.get_scheduled_jobs()
            logger.info(f"登録されたジョブ: {len(jobs)}件")
            for job in jobs:
                logger.info(f"  - {job['name']}: 次回実行 {job['next_run_time']}")

            # デーモンループ
            logger.info("デーモンループ開始（Ctrl+C またはSIGTERMで終了）")
            while not shutdown_requested:
                time.sleep(1)

        else:
            logger.error("スケジューラー起動失敗")
            sys.exit(1)

    except Exception as e:
        logger.error(f"デーモン起動エラー: {e}", exc_info=True)
        sys.exit(1)

    finally:
        logger.info("=== Microsoft 365 Sync Daemon 終了 ===")


if __name__ == "__main__":
    main()
