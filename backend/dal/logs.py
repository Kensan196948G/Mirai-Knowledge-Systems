"""
LogsMixin - アクセスログドメインDAL
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_session_factory
from models import AccessLog


class LogsMixin:
    """アクセスログCRUD操作"""

    def get_access_logs(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        アクセスログを取得

        Args:
            filters: フィルタ条件 (user_id, action, resource など)

        Returns:
            アクセスログリスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                query = db.query(AccessLog)

                # フィルタリング
                if filters:
                    if "user_id" in filters:
                        query = query.filter(AccessLog.user_id == filters["user_id"])
                    if "action" in filters:
                        query = query.filter(AccessLog.action == filters["action"])
                    if "resource" in filters:
                        query = query.filter(AccessLog.resource == filters["resource"])
                    if "limit" in filters:
                        query = query.limit(filters["limit"])

                results = query.order_by(AccessLog.created_at.desc()).all()
                return [self._access_log_to_dict(log) for log in results]
            finally:
                db.close()
        else:
            data = self._load_json("access_logs.json")

            # フィルタリング
            if filters:
                if "user_id" in filters:
                    data = [
                        log for log in data if log.get("user_id") == filters["user_id"]
                    ]
                if "action" in filters:
                    data = [
                        log for log in data if log.get("action") == filters["action"]
                    ]
                if "resource" in filters:
                    data = [
                        log
                        for log in data
                        if log.get("resource") == filters["resource"]
                    ]

            # ソート
            data = sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)

            # リミット
            if filters and "limit" in filters:
                data = data[: filters["limit"]]

            return data

    def create_access_log(self, log_data: Dict) -> Dict:
        """
        アクセスログを作成

        Args:
            log_data: ログデータ

        Returns:
            作成されたログデータ
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                access_log = AccessLog(
                    user_id=log_data.get("user_id"),
                    username=log_data.get("username"),
                    action=log_data["action"],
                    resource=log_data.get("resource"),
                    resource_id=log_data.get("resource_id"),
                    ip_address=log_data.get("ip_address"),
                    user_agent=log_data.get("user_agent"),
                )
                db.add(access_log)
                db.commit()
                db.refresh(access_log)
                return self._access_log_to_dict(access_log)
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        else:
            data = self._load_json("access_logs.json")
            new_id = max([log["id"] for log in data], default=0) + 1

            new_log = {
                "id": new_id,
                "user_id": log_data.get("user_id"),
                "username": log_data.get("username"),
                "action": log_data["action"],
                "resource": log_data.get("resource"),
                "resource_id": log_data.get("resource_id"),
                "ip_address": log_data.get("ip_address"),
                "user_agent": log_data.get("user_agent"),
                "created_at": datetime.now().isoformat(),
            }

            data.append(new_log)
            self._save_json("access_logs.json", data)
            return new_log

    @staticmethod
    def _access_log_to_dict(log: AccessLog) -> Dict:
        """AccessLogオブジェクトをDictに変換"""
        if not log:
            return None
        return {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "ip_address": str(log.ip_address) if log.ip_address else None,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
