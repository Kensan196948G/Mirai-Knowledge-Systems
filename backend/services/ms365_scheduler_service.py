"""
Microsoft 365同期スケジューラーサービス

APSchedulerを使用した定期同期実行機能を提供
"""

import logging
from typing import Dict, List

from data_access import DataAccessLayer

from services.ms365_sync_service import MS365SyncService

logger = logging.getLogger(__name__)

# オプション依存関係の遅延インポート
try:
    from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning(
        "APScheduler未インストール。pip install APScheduler でインストールしてください"
    )


class MS365SchedulerService:
    """Microsoft 365同期スケジューラー"""

    def __init__(self, dal: DataAccessLayer):
        """
        初期化

        Args:
            dal: データアクセスレイヤー
        """
        self.dal = dal
        self.sync_service = MS365SyncService(dal)
        self.scheduler = None

        if APSCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
            # ジョブイベントリスナー登録
            self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        else:
            logger.error(
                "APSchedulerが利用できません。スケジューラー機能が無効化されています"
            )

    def start(self):
        """スケジューラーを開始"""
        if not APSCHEDULER_AVAILABLE or not self.scheduler:
            logger.error("APSchedulerが利用できません")
            return False

        # 既存のジョブをクリア
        self.scheduler.remove_all_jobs()

        # 有効な同期設定をすべてロード
        configs = self._get_enabled_configs()
        logger.info(f"有効な同期設定を{len(configs)}件ロードしました")

        for config in configs:
            try:
                self.schedule_sync(config)
            except Exception as e:
                logger.error(f"同期設定#{config['id']}のスケジュール登録エラー: {e}")

        # スケジューラー開始
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("スケジューラーを開始しました")
            return True
        else:
            logger.info("スケジューラーは既に起動しています")
            return True

    def stop(self):
        """スケジューラーを停止"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("スケジューラーを停止しました")
            return True
        return False

    def schedule_sync(self, config: Dict):
        """
        同期設定をスケジュールに登録

        Args:
            config: 同期設定
        """
        if not APSCHEDULER_AVAILABLE or not self.scheduler:
            logger.error("APSchedulerが利用できません")
            return

        config_id = config["id"]
        config_name = config["name"]
        cron_schedule = config.get("sync_schedule", "0 2 * * *")

        try:
            # cronスケジュールをパース
            trigger = CronTrigger.from_crontab(cron_schedule)

            # ジョブ登録（既存ジョブは置き換え）
            self.scheduler.add_job(
                func=self._execute_sync_job,
                args=[config_id],
                trigger=trigger,
                id=f"ms365_sync_{config_id}",
                name=f"MS365 Sync: {config_name}",
                replace_existing=True,
                max_instances=1,  # 同時実行を防ぐ
            )

            logger.info(
                f"同期設定#{config_id}「{config_name}」をスケジュール登録: {cron_schedule}"
            )

        except Exception as e:
            logger.error(f"スケジュール登録エラー: {e}")
            raise

    def unschedule_sync(self, config_id: int):
        """
        同期設定をスケジュールから削除

        Args:
            config_id: 同期設定ID
        """
        if not APSCHEDULER_AVAILABLE or not self.scheduler:
            return

        job_id = f"ms365_sync_{config_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"同期設定#{config_id}をスケジュールから削除しました")
        except Exception as e:
            logger.warning(f"スケジュール削除エラー（ジョブが存在しない可能性）: {e}")

    def reschedule_sync(self, config: Dict):
        """
        同期設定のスケジュールを更新

        Args:
            config: 同期設定
        """
        # 既存ジョブを削除してから再登録
        self.unschedule_sync(config["id"])

        if config.get("is_enabled"):
            self.schedule_sync(config)

    def get_scheduled_jobs(self) -> List[Dict]:
        """
        スケジュール登録されているジョブ一覧を取得

        Returns:
            ジョブ情報のリスト
        """
        if not APSCHEDULER_AVAILABLE or not self.scheduler:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
            )

        return jobs

    def is_running(self) -> bool:
        """
        スケジューラーが稼働中かどうか

        Returns:
            稼働中の場合True
        """
        if not APSCHEDULER_AVAILABLE or not self.scheduler:
            return False
        return self.scheduler.running

    def _execute_sync_job(self, config_id: int):
        """
        スケジュールされた同期ジョブを実行

        Args:
            config_id: 同期設定ID
        """
        logger.info(f"スケジュール同期実行開始: config_id={config_id}")

        try:
            result = self.sync_service.sync_configuration(
                config_id, triggered_by="scheduler", user_id=None
            )
            logger.info(f"スケジュール同期完了: config_id={config_id}, result={result}")

        except Exception as e:
            logger.error(
                f"スケジュール同期エラー: config_id={config_id}, error={e}",
                exc_info=True,
            )
            # エラーは記録されているので、ここでは再raiseしない

    def _on_job_executed(self, event):
        """
        ジョブ実行完了イベントハンドラ

        Args:
            event: ジョブ実行イベント
        """
        logger.debug(f"ジョブ実行完了: {event.job_id}")

    def _on_job_error(self, event):
        """
        ジョブエラーイベントハンドラ

        Args:
            event: ジョブエラーイベント
        """
        logger.error(f"ジョブエラー: {event.job_id}, exception={event.exception}")

    def _get_enabled_configs(self) -> List[Dict]:
        """有効な同期設定一覧を取得"""
        try:
            all_configs = self.dal.get_all_ms365_sync_configs()
            return [c for c in all_configs if c.get("is_enabled")]
        except Exception as e:
            logger.error(f"同期設定取得エラー: {e}")
            return []
