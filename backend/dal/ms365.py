"""
MS365Mixin - Microsoft 365同期ドメインDAL
MS365SyncConfig / MS365SyncHistory / MS365FileMapping
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from database import get_session_factory
from models import MS365FileMapping, MS365SyncConfig, MS365SyncHistory


class MS365Mixin:
    """Microsoft 365同期CRUD操作"""

    # ============================================================
    # Microsoft 365同期設定（MS365SyncConfig）
    # ============================================================

    def get_all_ms365_sync_configs(self) -> List[Dict]:
        """MS365同期設定一覧を取得"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                configs = db.query(MS365SyncConfig).all()
                return [self._ms365_sync_config_to_dict(c) for c in configs]
            finally:
                db.close()
        else:
            return self._load_json("ms365_sync_configs.json")

    def get_ms365_sync_config(self, config_id: int) -> Optional[Dict]:
        """MS365同期設定を取得"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                config = (
                    db.query(MS365SyncConfig)
                    .filter(MS365SyncConfig.id == config_id)
                    .first()
                )
                return self._ms365_sync_config_to_dict(config) if config else None
            finally:
                db.close()
        else:
            configs = self._load_json("ms365_sync_configs.json")
            return next((c for c in configs if c["id"] == config_id), None)

    def create_ms365_sync_config(self, config_data: Dict) -> Dict:
        """MS365同期設定を作成"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                raise Exception("データベース接続エラー")
            db = factory()
            try:
                config = MS365SyncConfig(**config_data)
                db.add(config)
                db.commit()
                db.refresh(config)
                return self._ms365_sync_config_to_dict(config)
            finally:
                db.close()
        else:
            configs = self._load_json("ms365_sync_configs.json")
            new_id = max([c.get("id", 0) for c in configs], default=0) + 1
            new_config = {
                "id": new_id,
                **config_data,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            configs.append(new_config)
            self._save_json("ms365_sync_configs.json", configs)
            return new_config

    def update_ms365_sync_config(
        self, config_id: int, update_data: Dict
    ) -> Optional[Dict]:
        """MS365同期設定を更新"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                config = (
                    db.query(MS365SyncConfig)
                    .filter(MS365SyncConfig.id == config_id)
                    .first()
                )
                if config:
                    for key, value in update_data.items():
                        setattr(config, key, value)
                    db.commit()
                    db.refresh(config)
                    return self._ms365_sync_config_to_dict(config)
                return None
            finally:
                db.close()
        else:
            configs = self._load_json("ms365_sync_configs.json")
            for config in configs:
                if config["id"] == config_id:
                    config.update(update_data)
                    config["updated_at"] = datetime.now(timezone.utc).isoformat()
                    self._save_json("ms365_sync_configs.json", configs)
                    return config
            return None

    def delete_ms365_sync_config(self, config_id: int) -> bool:
        """MS365同期設定を削除"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return False
            db = factory()
            try:
                config = (
                    db.query(MS365SyncConfig)
                    .filter(MS365SyncConfig.id == config_id)
                    .first()
                )
                if config:
                    db.delete(config)
                    db.commit()
                    return True
                return False
            finally:
                db.close()
        else:
            configs = self._load_json("ms365_sync_configs.json")
            original_len = len(configs)
            configs = [c for c in configs if c["id"] != config_id]
            if len(configs) < original_len:
                self._save_json("ms365_sync_configs.json", configs)
                return True
            return False

    # ============================================================
    # Microsoft 365同期履歴（MS365SyncHistory）
    # ============================================================

    def create_ms365_sync_history(self, history_data: Dict) -> Dict:
        """MS365同期履歴を作成"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                raise Exception("データベース接続エラー")
            db = factory()
            try:
                history = MS365SyncHistory(**history_data)
                db.add(history)
                db.commit()
                db.refresh(history)
                return self._ms365_sync_history_to_dict(history)
            finally:
                db.close()
        else:
            histories = self._load_json("ms365_sync_histories.json")
            new_id = max([h.get("id", 0) for h in histories], default=0) + 1
            new_history = {
                "id": new_id,
                **history_data,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            histories.append(new_history)
            self._save_json("ms365_sync_histories.json", histories)
            return new_history

    def update_ms365_sync_history(
        self, history_id: int, update_data: Dict
    ) -> Optional[Dict]:
        """MS365同期履歴を更新"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                history = (
                    db.query(MS365SyncHistory)
                    .filter(MS365SyncHistory.id == history_id)
                    .first()
                )
                if history:
                    for key, value in update_data.items():
                        setattr(history, key, value)
                    db.commit()
                    db.refresh(history)
                    return self._ms365_sync_history_to_dict(history)
                return None
            finally:
                db.close()
        else:
            histories = self._load_json("ms365_sync_histories.json")
            for history in histories:
                if history["id"] == history_id:
                    history.update(update_data)
                    self._save_json("ms365_sync_histories.json", histories)
                    return history
            return None

    def get_ms365_sync_histories_by_config(
        self, config_id: int, limit: int = 20
    ) -> List[Dict]:
        """設定IDで同期履歴を取得"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                histories = (
                    db.query(MS365SyncHistory)
                    .filter(MS365SyncHistory.config_id == config_id)
                    .order_by(MS365SyncHistory.sync_started_at.desc())
                    .limit(limit)
                    .all()
                )
                return [self._ms365_sync_history_to_dict(h) for h in histories]
            finally:
                db.close()
        else:
            histories = self._load_json("ms365_sync_histories.json")
            filtered = [h for h in histories if h.get("config_id") == config_id]
            filtered.sort(key=lambda x: x.get("sync_started_at", ""), reverse=True)
            return filtered[:limit]

    def get_recent_ms365_sync_histories(
        self, config_ids: List[int], limit_per_config: int = 5
    ) -> List[Dict]:
        """複数設定の同期履歴を一括取得（N+1回避）"""
        if not config_ids:
            return []
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                from sqlalchemy import func

                subq = (
                    db.query(
                        MS365SyncHistory,
                        func.row_number()
                        .over(
                            partition_by=MS365SyncHistory.config_id,
                            order_by=MS365SyncHistory.sync_started_at.desc(),
                        )
                        .label("rn"),
                    )
                    .filter(MS365SyncHistory.config_id.in_(config_ids))
                    .subquery()
                )
                histories = (
                    db.query(MS365SyncHistory)
                    .join(subq, MS365SyncHistory.id == subq.c.id)
                    .filter(subq.c.rn <= limit_per_config)
                    .all()
                )
                return [self._ms365_sync_history_to_dict(h) for h in histories]
            finally:
                db.close()
        else:
            all_histories = self._load_json("ms365_sync_histories.json")
            config_id_set = set(config_ids)
            grouped = {}
            for h in all_histories:
                cid = h.get("config_id")
                if cid in config_id_set:
                    grouped.setdefault(cid, []).append(h)
            result = []
            for cid, histories in grouped.items():
                histories.sort(
                    key=lambda x: x.get("sync_started_at", ""), reverse=True
                )
                result.extend(histories[:limit_per_config])
            return result

    # ============================================================
    # Microsoft 365ファイルマッピング（MS365FileMapping）
    # ============================================================

    def get_ms365_file_mappings_by_config(self, config_id: int) -> List[Dict]:
        """設定IDでファイルマッピングを取得"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                mappings = (
                    db.query(MS365FileMapping)
                    .filter(MS365FileMapping.config_id == config_id)
                    .all()
                )
                return [self._ms365_file_mapping_to_dict(m) for m in mappings]
            finally:
                db.close()
        else:
            mappings = self._load_json("ms365_file_mappings.json")
            return [m for m in mappings if m.get("config_id") == config_id]

    def get_ms365_file_mapping_by_sp_id(self, file_id: str) -> Optional[Dict]:
        """SharePointファイルIDでマッピングを取得"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                mapping = (
                    db.query(MS365FileMapping)
                    .filter(MS365FileMapping.sharepoint_file_id == file_id)
                    .first()
                )
                return self._ms365_file_mapping_to_dict(mapping) if mapping else None
            finally:
                db.close()
        else:
            mappings = self._load_json("ms365_file_mappings.json")
            return next(
                (m for m in mappings if m.get("sharepoint_file_id") == file_id), None
            )

    def create_ms365_file_mapping(self, mapping_data: Dict) -> Dict:
        """MS365ファイルマッピングを作成"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                raise Exception("データベース接続エラー")
            db = factory()
            try:
                mapping = MS365FileMapping(**mapping_data)
                db.add(mapping)
                db.commit()
                db.refresh(mapping)
                return self._ms365_file_mapping_to_dict(mapping)
            finally:
                db.close()
        else:
            mappings = self._load_json("ms365_file_mappings.json")
            new_id = max([m.get("id", 0) for m in mappings], default=0) + 1
            new_mapping = {
                "id": new_id,
                **mapping_data,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            mappings.append(new_mapping)
            self._save_json("ms365_file_mappings.json", mappings)
            return new_mapping

    def update_ms365_file_mapping(
        self, mapping_id: int, update_data: Dict
    ) -> Optional[Dict]:
        """MS365ファイルマッピングを更新"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                mapping = (
                    db.query(MS365FileMapping)
                    .filter(MS365FileMapping.id == mapping_id)
                    .first()
                )
                if mapping:
                    for key, value in update_data.items():
                        setattr(mapping, key, value)
                    db.commit()
                    db.refresh(mapping)
                    return self._ms365_file_mapping_to_dict(mapping)
                return None
            finally:
                db.close()
        else:
            mappings = self._load_json("ms365_file_mappings.json")
            for mapping in mappings:
                if mapping["id"] == mapping_id:
                    mapping.update(update_data)
                    mapping["updated_at"] = datetime.now(timezone.utc).isoformat()
                    self._save_json("ms365_file_mappings.json", mappings)
                    return mapping
            return None

    # ============================================================
    # ヘルパーメソッド - MS365関連
    # ============================================================

    def _ms365_sync_config_to_dict(self, config) -> Dict:
        """MS365SyncConfig を辞書に変換"""
        if not config:
            return None
        return {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "site_id": config.site_id,
            "drive_id": config.drive_id,
            "folder_path": config.folder_path,
            "file_extensions": config.file_extensions,
            "sync_schedule": config.sync_schedule,
            "is_enabled": config.is_enabled,
            "last_sync_at": (
                config.last_sync_at.isoformat() if config.last_sync_at else None
            ),
            "next_sync_at": (
                config.next_sync_at.isoformat() if config.next_sync_at else None
            ),
            "sync_strategy": config.sync_strategy,
            "metadata_mapping": config.metadata_mapping,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            "created_by_id": config.created_by_id,
            "updated_by_id": config.updated_by_id,
        }

    def _ms365_sync_history_to_dict(self, history) -> Dict:
        """MS365SyncHistory を辞書に変換"""
        if not history:
            return None
        return {
            "id": history.id,
            "config_id": history.config_id,
            "sync_started_at": (
                history.sync_started_at.isoformat() if history.sync_started_at else None
            ),
            "sync_completed_at": (
                history.sync_completed_at.isoformat()
                if history.sync_completed_at
                else None
            ),
            "status": history.status,
            "files_processed": history.files_processed,
            "files_created": history.files_created,
            "files_updated": history.files_updated,
            "files_skipped": history.files_skipped,
            "files_failed": history.files_failed,
            "error_message": history.error_message,
            "error_details": history.error_details,
            "execution_time_seconds": history.execution_time_seconds,
            "triggered_by": history.triggered_by,
            "triggered_by_user_id": history.triggered_by_user_id,
            "created_at": (
                history.created_at.isoformat() if history.created_at else None
            ),
        }

    def _ms365_file_mapping_to_dict(self, mapping) -> Dict:
        """MS365FileMapping を辞書に変換"""
        if not mapping:
            return None
        return {
            "id": mapping.id,
            "config_id": mapping.config_id,
            "sharepoint_file_id": mapping.sharepoint_file_id,
            "sharepoint_file_name": mapping.sharepoint_file_name,
            "sharepoint_file_path": mapping.sharepoint_file_path,
            "sharepoint_modified_at": (
                mapping.sharepoint_modified_at.isoformat()
                if mapping.sharepoint_modified_at
                else None
            ),
            "sharepoint_size_bytes": mapping.sharepoint_size_bytes,
            "knowledge_id": mapping.knowledge_id,
            "sync_status": mapping.sync_status,
            "last_synced_at": (
                mapping.last_synced_at.isoformat() if mapping.last_synced_at else None
            ),
            "checksum": mapping.checksum,
            "file_metadata": mapping.file_metadata,
            "error_message": mapping.error_message,
            "created_at": (
                mapping.created_at.isoformat() if mapping.created_at else None
            ),
            "updated_at": (
                mapping.updated_at.isoformat() if mapping.updated_at else None
            ),
        }
