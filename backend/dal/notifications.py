"""
NotificationMixin - 通知ドメインDAL
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_session_factory
from models import Notification


class NotificationMixin:
    """通知CRUD操作"""

    def get_notifications(
        self, user_id: int = None, filters: Dict = None
    ) -> List[Dict]:
        """
        通知一覧を取得

        Args:
            user_id: ユーザーID（指定時はそのユーザー向けの通知のみ）
            filters: フィルタ条件

        Returns:
            通知リスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                query = db.query(Notification)

                if user_id:
                    # PostgreSQLの配列検索
                    query = query.filter((Notification.target_users.any(user_id)))

                results = query.order_by(Notification.created_at.desc()).all()
                return [self._notification_to_dict(n) for n in results]
            finally:
                db.close()
        else:
            data = self._load_json("notifications.json")

            if user_id:
                # ユーザーIDがtarget_usersに含まれる通知のみ
                data = [n for n in data if user_id in n.get("target_users", [])]

            return sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)

    def create_notification(self, notification_data: Dict) -> Dict:
        """
        通知を作成

        Args:
            notification_data: 通知データ

        Returns:
            作成された通知データ
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                notification = Notification(
                    title=notification_data["title"],
                    message=notification_data["message"],
                    type=notification_data["type"],
                    target_users=notification_data.get("target_users", []),
                    target_roles=notification_data.get("target_roles", []),
                    priority=notification_data.get("priority", "medium"),
                    related_entity_type=notification_data.get("related_entity_type"),
                    related_entity_id=notification_data.get("related_entity_id"),
                    status="sent",
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
                return self._notification_to_dict(notification)
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        else:
            data = self._load_json("notifications.json")
            new_id = max([n["id"] for n in data], default=0) + 1

            new_notification = {
                "id": new_id,
                "title": notification_data["title"],
                "message": notification_data["message"],
                "type": notification_data["type"],
                "target_users": notification_data.get("target_users", []),
                "target_roles": notification_data.get("target_roles", []),
                "priority": notification_data.get("priority", "medium"),
                "related_entity_type": notification_data.get("related_entity_type"),
                "related_entity_id": notification_data.get("related_entity_id"),
                "created_at": datetime.now().isoformat(),
                "status": "sent",
                "read_by": [],
            }

            data.append(new_notification)
            self._save_json("notifications.json", data)
            return new_notification

    @staticmethod
    def _notification_to_dict(notification: Notification) -> Dict:
        """NotificationオブジェクトをDictに変換"""
        if not notification:
            return None
        return {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "target_users": notification.target_users or [],
            "target_roles": notification.target_roles or [],
            "priority": notification.priority,
            "related_entity_type": notification.related_entity_type,
            "related_entity_id": notification.related_entity_id,
            "created_at": (
                notification.created_at.isoformat() if notification.created_at else None
            ),
            "sent_at": (
                notification.sent_at.isoformat() if notification.sent_at else None
            ),
            "status": notification.status,
        }
