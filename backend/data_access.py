"""
データアクセスレイヤー
JSON/PostgreSQLの切り替えを透過的に行う
"""
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import Config
from database import SessionLocal
from models import Knowledge, SOP, Incident, Consultation, Approval, Notification, User


class DataAccessLayer:
    """データアクセス抽象化レイヤー"""

    def __init__(self, use_postgresql=None):
        """
        初期化

        Args:
            use_postgresql: PostgreSQLを使用するかどうか（Noneの場合は環境変数から取得）
        """
        if use_postgresql is None:
            use_postgresql = Config.USE_POSTGRESQL
        self.use_postgresql = use_postgresql
        self.data_dir = Config.DATA_DIR

    def _get_json_path(self, filename):
        """JSONファイルのパスを取得"""
        return os.path.join(self.data_dir, filename)

    def _load_json(self, filename):
        """JSONファイルからデータを読み込み"""
        filepath = self._get_json_path(filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        return []
                    return [item for item in data if isinstance(item, dict)]
            except (json.JSONDecodeError, ValueError):
                return []
        return []

    def _save_json(self, filename, data):
        """JSONファイルにデータを保存"""
        filepath = self._get_json_path(filename)
        dirpath = os.path.dirname(filepath)
        os.makedirs(dirpath, exist_ok=True)

        import tempfile
        fd, tmp_path = tempfile.mkstemp(prefix=f".{filename}.", suffix=".tmp", dir=dirpath)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, filepath)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ============================================================
    # ナレッジ（Knowledge）
    # ============================================================

    def get_knowledge_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        ナレッジ一覧を取得

        Args:
            filters: フィルタ条件 (category, search, tags など)

        Returns:
            ナレッジリスト
        """
        if self.use_postgresql:
            db = SessionLocal()
            try:
                query = db.query(Knowledge)

                # フィルタリング
                if filters:
                    if 'category' in filters:
                        query = query.filter(Knowledge.category == filters['category'])
                    if 'search' in filters:
                        search_term = f"%{filters['search']}%"
                        query = query.filter(
                            (Knowledge.title.ilike(search_term)) |
                            (Knowledge.summary.ilike(search_term)) |
                            (Knowledge.content.ilike(search_term))
                        )

                results = query.order_by(Knowledge.updated_at.desc()).all()
                return [self._knowledge_to_dict(k) for k in results]
            finally:
                db.close()
        else:
            data = self._load_json('knowledge.json')

            # フィルタリング
            if filters:
                if 'category' in filters:
                    data = [k for k in data if k.get('category') == filters['category']]
                if 'search' in filters:
                    search_term = filters['search'].lower()
                    data = [k for k in data if
                           search_term in k.get('title', '').lower() or
                           search_term in k.get('summary', '').lower() or
                           search_term in k.get('content', '').lower()]

            return data

    def get_knowledge_by_id(self, knowledge_id: int) -> Optional[Dict]:
        """
        ナレッジをIDで取得

        Args:
            knowledge_id: ナレッジID

        Returns:
            ナレッジデータ（見つからない場合はNone）
        """
        if self.use_postgresql:
            db = SessionLocal()
            try:
                knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
                return self._knowledge_to_dict(knowledge) if knowledge else None
            finally:
                db.close()
        else:
            data = self._load_json('knowledge.json')
            return next((k for k in data if k['id'] == knowledge_id), None)

    def create_knowledge(self, knowledge_data: Dict) -> Dict:
        """
        ナレッジを作成

        Args:
            knowledge_data: ナレッジデータ

        Returns:
            作成されたナレッジデータ
        """
        if self.use_postgresql:
            db = SessionLocal()
            try:
                knowledge = Knowledge(
                    title=knowledge_data['title'],
                    summary=knowledge_data['summary'],
                    content=knowledge_data.get('content'),
                    category=knowledge_data['category'],
                    tags=knowledge_data.get('tags', []),
                    status=knowledge_data.get('status', 'draft'),
                    priority=knowledge_data.get('priority', 'medium'),
                    project=knowledge_data.get('project'),
                    owner=knowledge_data['owner'],
                    created_by_id=knowledge_data.get('created_by_id')
                )
                db.add(knowledge)
                db.commit()
                db.refresh(knowledge)
                return self._knowledge_to_dict(knowledge)
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
        else:
            data = self._load_json('knowledge.json')
            new_id = max([k['id'] for k in data], default=0) + 1

            new_knowledge = {
                'id': new_id,
                'title': knowledge_data['title'],
                'summary': knowledge_data['summary'],
                'content': knowledge_data.get('content'),
                'category': knowledge_data['category'],
                'tags': knowledge_data.get('tags', []),
                'status': knowledge_data.get('status', 'draft'),
                'priority': knowledge_data.get('priority', 'medium'),
                'project': knowledge_data.get('project'),
                'owner': knowledge_data['owner'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'created_by_id': knowledge_data.get('created_by_id')
            }

            data.append(new_knowledge)
            self._save_json('knowledge.json', data)
            return new_knowledge

    def update_knowledge(self, knowledge_id: int, knowledge_data: Dict) -> Optional[Dict]:
        """
        ナレッジを更新

        Args:
            knowledge_id: ナレッジID
            knowledge_data: 更新データ

        Returns:
            更新されたナレッジデータ（見つからない場合はNone）
        """
        if self.use_postgresql:
            db = SessionLocal()
            try:
                knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
                if not knowledge:
                    return None

                for key, value in knowledge_data.items():
                    if hasattr(knowledge, key) and key not in ['id', 'created_at']:
                        setattr(knowledge, key, value)

                knowledge.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(knowledge)
                return self._knowledge_to_dict(knowledge)
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
        else:
            data = self._load_json('knowledge.json')
            knowledge = next((k for k in data if k['id'] == knowledge_id), None)

            if not knowledge:
                return None

            for key, value in knowledge_data.items():
                if key != 'id':
                    knowledge[key] = value

            knowledge['updated_at'] = datetime.now().isoformat()
            self._save_json('knowledge.json', data)
            return knowledge

    def delete_knowledge(self, knowledge_id: int) -> bool:
        """
        ナレッジを削除

        Args:
            knowledge_id: ナレッジID

        Returns:
            削除成功時True
        """
        if self.use_postgresql:
            db = SessionLocal()
            try:
                knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
                if not knowledge:
                    return False

                db.delete(knowledge)
                db.commit()
                return True
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
        else:
            data = self._load_json('knowledge.json')
            original_length = len(data)
            data = [k for k in data if k['id'] != knowledge_id]

            if len(data) < original_length:
                self._save_json('knowledge.json', data)
                return True
            return False

    # ============================================================
    # 通知（Notification）
    # ============================================================

    def get_notifications(self, user_id: int = None, filters: Dict = None) -> List[Dict]:
        """
        通知一覧を取得

        Args:
            user_id: ユーザーID（指定時はそのユーザー向けの通知のみ）
            filters: フィルタ条件

        Returns:
            通知リスト
        """
        if self.use_postgresql:
            db = SessionLocal()
            try:
                query = db.query(Notification)

                if user_id:
                    # PostgreSQLの配列検索
                    query = query.filter(
                        (Notification.target_users.any(user_id))
                    )

                results = query.order_by(Notification.created_at.desc()).all()
                return [self._notification_to_dict(n) for n in results]
            finally:
                db.close()
        else:
            data = self._load_json('notifications.json')

            if user_id:
                # ユーザーIDがtarget_usersに含まれる通知のみ
                data = [n for n in data if user_id in n.get('target_users', [])]

            return sorted(data, key=lambda x: x.get('created_at', ''), reverse=True)

    def create_notification(self, notification_data: Dict) -> Dict:
        """
        通知を作成

        Args:
            notification_data: 通知データ

        Returns:
            作成された通知データ
        """
        if self.use_postgresql:
            db = SessionLocal()
            try:
                notification = Notification(
                    title=notification_data['title'],
                    message=notification_data['message'],
                    type=notification_data['type'],
                    target_users=notification_data.get('target_users', []),
                    target_roles=notification_data.get('target_roles', []),
                    priority=notification_data.get('priority', 'medium'),
                    related_entity_type=notification_data.get('related_entity_type'),
                    related_entity_id=notification_data.get('related_entity_id'),
                    status='sent'
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
                return self._notification_to_dict(notification)
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
        else:
            data = self._load_json('notifications.json')
            new_id = max([n['id'] for n in data], default=0) + 1

            new_notification = {
                'id': new_id,
                'title': notification_data['title'],
                'message': notification_data['message'],
                'type': notification_data['type'],
                'target_users': notification_data.get('target_users', []),
                'target_roles': notification_data.get('target_roles', []),
                'priority': notification_data.get('priority', 'medium'),
                'related_entity_type': notification_data.get('related_entity_type'),
                'related_entity_id': notification_data.get('related_entity_id'),
                'created_at': datetime.now().isoformat(),
                'status': 'sent',
                'read_by': []
            }

            data.append(new_notification)
            self._save_json('notifications.json', data)
            return new_notification

    # ============================================================
    # ヘルパーメソッド（ORMオブジェクト→辞書変換）
    # ============================================================

    @staticmethod
    def _knowledge_to_dict(knowledge: Knowledge) -> Dict:
        """KnowledgeオブジェクトをDictに変換"""
        if not knowledge:
            return None
        return {
            'id': knowledge.id,
            'title': knowledge.title,
            'summary': knowledge.summary,
            'content': knowledge.content,
            'category': knowledge.category,
            'tags': knowledge.tags or [],
            'status': knowledge.status,
            'priority': knowledge.priority,
            'project': knowledge.project,
            'owner': knowledge.owner,
            'created_at': knowledge.created_at.isoformat() if knowledge.created_at else None,
            'updated_at': knowledge.updated_at.isoformat() if knowledge.updated_at else None,
            'created_by_id': knowledge.created_by_id,
            'updated_by_id': knowledge.updated_by_id
        }

    @staticmethod
    def _notification_to_dict(notification: Notification) -> Dict:
        """NotificationオブジェクトをDictに変換"""
        if not notification:
            return None
        return {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'target_users': notification.target_users or [],
            'target_roles': notification.target_roles or [],
            'priority': notification.priority,
            'related_entity_type': notification.related_entity_type,
            'related_entity_id': notification.related_entity_id,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
            'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
            'status': notification.status
        }


# グローバルインスタンス
dal = DataAccessLayer()
