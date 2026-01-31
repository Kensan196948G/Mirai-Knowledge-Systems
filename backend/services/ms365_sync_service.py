"""
Microsoft 365同期サービス

SharePoint/OneDriveからのファイル同期機能を提供
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

from integrations.microsoft_graph import MicrosoftGraphClient
from data_access import DataAccessLayer
from models import MS365SyncConfig, MS365SyncHistory, MS365FileMapping, Knowledge

logger = logging.getLogger(__name__)


class MS365SyncService:
    """Microsoft 365同期サービス"""

    def __init__(self, dal: DataAccessLayer):
        """
        初期化

        Args:
            dal: データアクセスレイヤー
        """
        self.dal = dal
        self.graph_client = None
        self._init_graph_client()

    def _init_graph_client(self):
        """Microsoft Graph クライアントを初期化"""
        try:
            self.graph_client = MicrosoftGraphClient()
            if not self.graph_client.is_configured():
                logger.warning("Microsoft Graph API が設定されていません")
        except Exception as e:
            logger.error(f"Microsoft Graph クライアント初期化エラー: {e}")
            self.graph_client = None

    def sync_configuration(
        self,
        config_id: int,
        triggered_by: str = "scheduler",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同期設定に基づいて同期を実行

        Args:
            config_id: 同期設定ID
            triggered_by: トリガー元（"scheduler", "manual", "api"）
            user_id: 実行ユーザーID（手動実行時）

        Returns:
            同期結果の統計情報
        """
        if not self.graph_client or not self.graph_client.is_configured():
            raise ValueError("Microsoft Graph API が設定されていません")

        # 設定取得
        config = self._get_sync_config(config_id)
        if not config:
            raise ValueError(f"同期設定ID {config_id} が見つかりません")

        if not config.get("is_enabled"):
            raise ValueError(f"同期設定ID {config_id} は無効化されています")

        # 同期履歴レコード作成（status: running）
        history_id = self._create_sync_history(
            config_id, triggered_by, user_id, status="running"
        )

        sync_started = datetime.utcnow()
        stats = {
            "files_processed": 0,
            "files_created": 0,
            "files_updated": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "errors": [],
        }

        try:
            # ファイル一覧取得
            logger.info(f"[Sync {history_id}] ファイル一覧取得開始: site={config['site_id']}, drive={config['drive_id']}")
            files = self.discover_files(config)
            logger.info(f"[Sync {history_id}] {len(files)} 件のファイルを検出")

            # 変更検出（増分同期の場合）
            if config.get("sync_strategy") == "incremental":
                files_to_process = self.detect_changes(files, config_id)
                logger.info(f"[Sync {history_id}] 増分同期: {len(files_to_process)} 件を処理対象として検出")
            else:
                files_to_process = files
                logger.info(f"[Sync {history_id}] 全件同期: {len(files_to_process)} 件を処理")

            # ファイル毎の処理
            for file_info in files_to_process:
                try:
                    result = self._process_file(file_info, config, config_id)
                    stats["files_processed"] += 1

                    if result["action"] == "created":
                        stats["files_created"] += 1
                    elif result["action"] == "updated":
                        stats["files_updated"] += 1
                    elif result["action"] == "skipped":
                        stats["files_skipped"] += 1

                except Exception as e:
                    logger.error(f"[Sync {history_id}] ファイル処理エラー: {file_info.get('name')}: {e}")
                    stats["files_failed"] += 1
                    stats["errors"].append({
                        "file": file_info.get("name"),
                        "error": str(e)
                    })

            # 同期完了
            sync_completed = datetime.utcnow()
            execution_time = int((sync_completed - sync_started).total_seconds())

            # 同期履歴更新
            self._update_sync_history(
                history_id,
                status="completed",
                sync_completed_at=sync_completed,
                execution_time_seconds=execution_time,
                **{k: v for k, v in stats.items() if k != "errors"}
            )

            # 次回同期時刻計算
            self._calculate_next_sync_time(config_id, config.get("sync_schedule"))

            logger.info(f"[Sync {history_id}] 同期完了: {stats}")

            return {
                "history_id": history_id,
                "status": "completed",
                "execution_time_seconds": execution_time,
                **stats
            }

        except Exception as e:
            # 同期失敗
            logger.error(f"[Sync {history_id}] 同期失敗: {e}", exc_info=True)
            sync_completed = datetime.utcnow()
            execution_time = int((sync_completed - sync_started).total_seconds())

            self._update_sync_history(
                history_id,
                status="failed",
                sync_completed_at=sync_completed,
                execution_time_seconds=execution_time,
                error_message=str(e),
                error_details={"errors": stats.get("errors", [])}
            )

            raise

    def discover_files(self, config: Dict) -> List[Dict]:
        """
        SharePoint/OneDriveからファイル一覧を取得

        Args:
            config: 同期設定

        Returns:
            ファイル情報のリスト
        """
        try:
            drive_id = config["drive_id"]
            folder_path = config.get("folder_path", "/")
            file_extensions = config.get("file_extensions", [])

            # ファイル一覧取得
            items = self.graph_client.get_drive_items(drive_id, folder_path)

            # フィルタリング
            files = []
            for item in items:
                # ファイルのみ（フォルダを除外）
                if "file" not in item:
                    continue

                # 拡張子フィルタ
                if file_extensions:
                    file_name = item.get("name", "")
                    if not any(file_name.lower().endswith(f".{ext.lower().lstrip('.')}") for ext in file_extensions):
                        continue

                files.append(item)

            return files

        except Exception as e:
            logger.error(f"ファイル一覧取得エラー: {e}")
            raise

    def detect_changes(self, files: List[Dict], config_id: int) -> List[Dict]:
        """
        変更されたファイルを検出（増分同期用）

        Args:
            files: SharePointファイルリスト
            config_id: 同期設定ID

        Returns:
            変更されたファイルのリスト
        """
        # 既存マッピング取得
        existing_mappings = self._get_file_mappings(config_id)
        existing_file_ids = {m["sharepoint_file_id"]: m for m in existing_mappings}

        changed_files = []

        for file_info in files:
            file_id = file_info.get("id")
            modified_at_str = file_info.get("lastModifiedDateTime")

            # 新規ファイル
            if file_id not in existing_file_ids:
                changed_files.append(file_info)
                continue

            # 変更チェック（更新日時）
            existing = existing_file_ids[file_id]
            if modified_at_str and existing.get("sharepoint_modified_at"):
                try:
                    modified_at = datetime.fromisoformat(modified_at_str.replace("Z", "+00:00"))
                    existing_modified = existing["sharepoint_modified_at"]

                    # SharePointの更新日時が新しい場合
                    if isinstance(existing_modified, str):
                        existing_modified = datetime.fromisoformat(existing_modified.replace("Z", "+00:00"))

                    if modified_at > existing_modified:
                        changed_files.append(file_info)
                except Exception as e:
                    logger.warning(f"日付比較エラー: {file_info.get('name')}: {e}")
                    # エラー時は再同期
                    changed_files.append(file_info)

        logger.info(f"変更検出: {len(files)} 件中 {len(changed_files)} 件が変更されています")
        return changed_files

    def _process_file(
        self,
        file_info: Dict,
        config: Dict,
        config_id: int
    ) -> Dict[str, str]:
        """
        ファイルを処理（ダウンロード→メタデータ抽出→ナレッジ作成/更新）

        Args:
            file_info: SharePointファイル情報
            config: 同期設定
            config_id: 同期設定ID

        Returns:
            処理結果（action: created/updated/skipped）
        """
        file_id = file_info.get("id")
        file_name = file_info.get("name")
        drive_id = config["drive_id"]

        # ファイルダウンロード
        logger.debug(f"ファイルダウンロード: {file_name}")
        file_content = self._download_file_with_retry(drive_id, file_id)

        # チェックサム計算
        checksum = self._calculate_checksum(file_content)

        # 既存マッピング確認
        existing_mapping = self._get_file_mapping_by_sp_id(file_id)

        # チェックサム一致→スキップ
        if existing_mapping and existing_mapping.get("checksum") == checksum:
            logger.debug(f"チェックサム一致→スキップ: {file_name}")
            return {"action": "skipped"}

        # メタデータ抽出（ここでは簡易版、Phase 2.3で実装）
        metadata = self._extract_basic_metadata(file_info, file_content)

        # ナレッジレコード作成/更新
        if existing_mapping and existing_mapping.get("knowledge_id"):
            # 更新
            knowledge_id = existing_mapping["knowledge_id"]
            self._update_knowledge(knowledge_id, metadata)
            action = "updated"
        else:
            # 新規作成
            knowledge_id = self._create_knowledge(metadata)
            action = "created"

        # ファイルマッピング作成/更新
        self._upsert_file_mapping(
            config_id=config_id,
            file_id=file_id,
            file_info=file_info,
            knowledge_id=knowledge_id,
            checksum=checksum
        )

        logger.info(f"ファイル処理完了: {file_name} → Knowledge#{knowledge_id} ({action})")
        return {"action": action, "knowledge_id": knowledge_id}

    def _download_file_with_retry(
        self,
        drive_id: str,
        item_id: str,
        max_retries: int = 3
    ) -> bytes:
        """
        ファイルダウンロード（リトライ付き）

        Args:
            drive_id: ドライブID
            item_id: アイテムID
            max_retries: 最大リトライ回数

        Returns:
            ファイル内容（bytes）
        """
        for attempt in range(1, max_retries + 1):
            try:
                return self.graph_client.download_file(drive_id, item_id)
            except Exception as e:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 指数バックオフ: 2, 4, 8秒
                    logger.warning(f"ダウンロード失敗（試行{attempt}/{max_retries}）: {e}。{wait_time}秒後にリトライ...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"ダウンロード失敗（最大リトライ回数超過）: {e}")
                    raise

    def _calculate_checksum(self, content: bytes) -> str:
        """
        SHA256チェックサムを計算

        Args:
            content: ファイル内容

        Returns:
            SHA256ハッシュ（16進数文字列）
        """
        return hashlib.sha256(content).hexdigest()

    def _extract_basic_metadata(
        self,
        file_info: Dict,
        file_content: bytes
    ) -> Dict[str, Any]:
        """
        基本的なメタデータを抽出（簡易版）

        Args:
            file_info: SharePointファイル情報
            file_content: ファイル内容

        Returns:
            ナレッジレコード用のメタデータ
        """
        file_name = file_info.get("name", "")
        created_by = file_info.get("createdBy", {}).get("user", {}).get("displayName", "不明")

        # 基本メタデータ
        metadata = {
            "title": file_name,
            "summary": f"SharePointから同期: {file_name}",
            "content": f"ファイル: {file_name}\nサイズ: {file_info.get('size', 0)} bytes",
            "category": "その他",  # デフォルトカテゴリ
            "tags": ["MS365同期"],
            "owner": created_by,
            "status": "draft",  # デフォルトで下書き
            "priority": "medium",
        }

        # TODO: Phase 2.3でMetadataExtractorを使用して詳細抽出

        return metadata

    def _create_knowledge(self, metadata: Dict) -> int:
        """
        新規ナレッジレコードを作成

        Args:
            metadata: ナレッジメタデータ

        Returns:
            作成されたナレッジID
        """
        # JSONモードでの実装（PostgreSQLモードは後で実装）
        knowledge_data = {
            **metadata,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # data_access.pyのcreate_knowledgeメソッドを使用
        result = self.dal.create_knowledge(knowledge_data)
        return result["id"]

    def _update_knowledge(self, knowledge_id: int, metadata: Dict):
        """
        既存ナレッジレコードを更新

        Args:
            knowledge_id: ナレッジID
            metadata: 更新するメタデータ
        """
        update_data = {
            **metadata,
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.dal.update_knowledge(knowledge_id, update_data)
        logger.info(f"ナレッジ#{knowledge_id}を更新しました")

    def _create_sync_history(
        self,
        config_id: int,
        triggered_by: str,
        user_id: Optional[int],
        status: str = "running"
    ) -> int:
        """
        同期履歴レコードを作成

        Args:
            config_id: 同期設定ID
            triggered_by: トリガー元
            user_id: 実行ユーザーID
            status: ステータス

        Returns:
            作成された履歴ID
        """
        history_data = {
            "config_id": config_id,
            "sync_started_at": datetime.utcnow().isoformat(),
            "status": status,
            "triggered_by": triggered_by,
            "triggered_by_user_id": user_id,
            "files_processed": 0,
            "files_created": 0,
            "files_updated": 0,
            "files_skipped": 0,
            "files_failed": 0,
        }

        # JSONモードでの実装
        result = self.dal.create_ms365_sync_history(history_data)
        return result["id"]

    def _update_sync_history(self, history_id: int, **kwargs):
        """
        同期履歴を更新

        Args:
            history_id: 履歴ID
            **kwargs: 更新するフィールド
        """
        self.dal.update_ms365_sync_history(history_id, kwargs)
        logger.debug(f"同期履歴#{history_id}を更新しました: {kwargs.get('status')}")

    def _upsert_file_mapping(
        self,
        config_id: int,
        file_id: str,
        file_info: Dict,
        knowledge_id: int,
        checksum: str
    ):
        """
        ファイルマッピングを作成/更新

        Args:
            config_id: 同期設定ID
            file_id: SharePointファイルID
            file_info: SharePointファイル情報
            knowledge_id: ナレッジID
            checksum: チェックサム
        """
        mapping_data = {
            "config_id": config_id,
            "sharepoint_file_id": file_id,
            "sharepoint_file_name": file_info.get("name"),
            "sharepoint_file_path": file_info.get("parentReference", {}).get("path"),
            "sharepoint_modified_at": file_info.get("lastModifiedDateTime"),
            "sharepoint_size_bytes": file_info.get("size"),
            "knowledge_id": knowledge_id,
            "sync_status": "synced",
            "last_synced_at": datetime.utcnow().isoformat(),
            "checksum": checksum,
            "file_metadata": file_info,  # SharePoint メタデータ全体を保存
        }

        # 既存マッピング確認
        existing = self._get_file_mapping_by_sp_id(file_id)
        if existing:
            self.dal.update_ms365_file_mapping(existing["id"], mapping_data)
        else:
            self.dal.create_ms365_file_mapping(mapping_data)

    def _get_sync_config(self, config_id: int) -> Optional[Dict]:
        """同期設定を取得"""
        return self.dal.get_ms365_sync_config(config_id)

    def _get_file_mappings(self, config_id: int) -> List[Dict]:
        """同期設定に紐づくファイルマッピング一覧を取得"""
        return self.dal.get_ms365_file_mappings_by_config(config_id)

    def _get_file_mapping_by_sp_id(self, file_id: str) -> Optional[Dict]:
        """SharePointファイルIDでマッピングを取得"""
        return self.dal.get_ms365_file_mapping_by_sp_id(file_id)

    def _calculate_next_sync_time(self, config_id: int, schedule: str):
        """
        次回同期時刻を計算

        Args:
            config_id: 同期設定ID
            schedule: cronスケジュール
        """
        # TODO: cronスケジュールをパースして次回実行時刻を計算
        # 暫定: 24時間後
        next_sync = datetime.utcnow() + timedelta(hours=24)

        self.dal.update_ms365_sync_config(config_id, {
            "last_sync_at": datetime.utcnow().isoformat(),
            "next_sync_at": next_sync.isoformat()
        })

    def test_connection(self, config_id: int) -> Dict[str, Any]:
        """
        接続テスト（ドライラン）

        Args:
            config_id: 同期設定ID

        Returns:
            テスト結果
        """
        if not self.graph_client or not self.graph_client.is_configured():
            return {
                "success": False,
                "error": "Microsoft Graph API が設定されていません"
            }

        config = self._get_sync_config(config_id)
        if not config:
            return {
                "success": False,
                "error": f"同期設定ID {config_id} が見つかりません"
            }

        try:
            # Graph API接続テスト
            org_test = self.graph_client.test_connection()
            if not org_test.get("connected"):
                return {
                    "success": False,
                    "error": "Graph API接続失敗",
                    "details": org_test
                }

            # ファイル一覧取得テスト
            files = self.discover_files(config)

            return {
                "success": True,
                "message": "接続テスト成功",
                "organization": org_test.get("organization"),
                "files_found": len(files),
                "sample_files": files[:5]  # 最初の5件をサンプル表示
            }

        except Exception as e:
            logger.error(f"接続テストエラー: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
