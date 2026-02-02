"""
データアクセスレイヤー
JSON/PostgreSQLの切り替えを透過的に行う
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import Config
from database import get_session_factory
from models import (
    Knowledge,
    SOP,
    Incident,
    Consultation,
    Approval,
    Notification,
    User,
    AccessLog,
    Project,
    ProjectTask,
    Expert,
    ExpertRating,
    MS365SyncConfig,
    MS365SyncHistory,
    MS365FileMapping,
)


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

    def _use_postgresql(self) -> bool:
        """PostgreSQL使用可否を判定（利用不可ならJSONにフォールバック）"""
        if not self.use_postgresql:
            return False
        try:
            from database import config as db_config
        except Exception:
            return False
        return db_config.is_postgres_available()

    def _get_json_path(self, filename):
        """JSONファイルのパスを取得"""
        return os.path.join(self.data_dir, filename)

    def _load_json(self, filename):
        """JSONファイルからデータを読み込み"""
        filepath = self._get_json_path(filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
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

        fd, tmp_path = tempfile.mkstemp(
            prefix=f".{filename}.", suffix=".tmp", dir=dirpath
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, filepath)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ============================================================
    # ナレッジ（Knowledge）
    # ============================================================

    def get_knowledge_list(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        ナレッジ一覧を取得

        Args:
            filters: フィルタ条件 (category, search, tags など)

        Returns:
            ナレッジリスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                from sqlalchemy.orm import selectinload

                # N+1クエリ最適化: リレーションを先読み
                query = db.query(Knowledge).options(
                    selectinload(Knowledge.created_by),
                    selectinload(Knowledge.updated_by)
                )

                # フィルタリング
                if filters:
                    if "category" in filters:
                        query = query.filter(Knowledge.category == filters["category"])
                    if "search" in filters:
                        search_term = f"%{filters['search']}%"
                        query = query.filter(
                            (Knowledge.title.ilike(search_term))
                            | (Knowledge.summary.ilike(search_term))
                            | (Knowledge.content.ilike(search_term))
                        )

                results = query.order_by(Knowledge.updated_at.desc()).all()
                return [self._knowledge_to_dict(k) for k in results]
            finally:
                db.close()
        else:
            data = self._load_json("knowledge.json")

            # フィルタリング
            if filters:
                if "category" in filters:
                    data = [k for k in data if k.get("category") == filters["category"]]
                if "search" in filters:
                    search_term = filters["search"].lower()
                    data = [
                        k
                        for k in data
                        if search_term in k.get("title", "").lower()
                        or search_term in k.get("summary", "").lower()
                        or search_term in k.get("content", "").lower()
                    ]

            return data

    def get_knowledge_by_id(self, knowledge_id: int) -> Optional[Dict]:
        """
        ナレッジをIDで取得

        Args:
            knowledge_id: ナレッジID

        Returns:
            ナレッジデータ（見つからない場合はNone）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                from sqlalchemy.orm import selectinload

                # N+1クエリ最適化: リレーションを先読み
                knowledge = (
                    db.query(Knowledge)
                    .options(
                        selectinload(Knowledge.created_by),
                        selectinload(Knowledge.updated_by)
                    )
                    .filter(Knowledge.id == knowledge_id)
                    .first()
                )
                return self._knowledge_to_dict(knowledge) if knowledge else None
            finally:
                db.close()
        else:
            data = self._load_json("knowledge.json")
            return next((k for k in data if k["id"] == knowledge_id), None)

    def get_related_knowledge_by_tags(
        self, tags: List[str], limit: int = 5, exclude_id: Optional[int] = None
    ) -> List[Dict]:
        """
        タグベースで関連ナレッジを取得

        Args:
            tags: 検索対象のタグリスト
            limit: 取得件数の上限
            exclude_id: 除外するナレッジID（自分自身を除外）

        Returns:
            関連ナレッジのリスト（タグ一致数の多い順）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                # N+1クエリ最適化: PostgreSQLのCTE（Common Table Expression）と配列関数を使用
                from sqlalchemy import func, and_, case, literal_column
                from sqlalchemy.orm import selectinload

                # タグ一致数をSQLで直接計算（N+1回避）
                # cardinality(array_intersect(tags, :tags)) でタグ一致数を計算
                if tags:
                    # PostgreSQLのarray演算子を使用してタグ一致数を計算
                    tag_match_count = func.cardinality(
                        func.array(
                            func.unnest(Knowledge.tags)
                        ).op('&&')(func.array(tags))
                    )

                    # リレーションを先読みしてN+1クエリを回避
                    query = (
                        db.query(Knowledge)
                        .options(
                            selectinload(Knowledge.created_by),
                            selectinload(Knowledge.updated_by)
                        )
                        .filter(Knowledge.status == "approved")
                        .filter(Knowledge.tags.overlap(tags))
                    )

                    if exclude_id:
                        query = query.filter(Knowledge.id != exclude_id)

                    # updated_atで降順ソート（タグ一致度は同等として最新順）
                    knowledge_list = query.order_by(Knowledge.updated_at.desc()).limit(limit * 2).all()

                    # Python側でタグ一致数でソート（PostgreSQLの複雑なCTE避けてシンプルに）
                    def tag_match_score(k):
                        if not k.tags or not tags:
                            return 0
                        return len(set(k.tags) & set(tags))

                    knowledge_list = sorted(
                        knowledge_list, key=tag_match_score, reverse=True
                    )[:limit]
                else:
                    # タグ指定なしの場合は最近のナレッジを返す
                    knowledge_list = (
                        db.query(Knowledge)
                        .options(
                            selectinload(Knowledge.created_by),
                            selectinload(Knowledge.updated_by)
                        )
                        .filter(Knowledge.status == "approved")
                        .filter(Knowledge.id != exclude_id if exclude_id else True)
                        .order_by(Knowledge.updated_at.desc())
                        .limit(limit)
                        .all()
                    )

                # フォールバック: タグ一致が0件なら最近のナレッジを返す
                if not knowledge_list:
                    knowledge_list = (
                        db.query(Knowledge)
                        .options(
                            selectinload(Knowledge.created_by),
                            selectinload(Knowledge.updated_by)
                        )
                        .filter(Knowledge.status == "approved")
                        .filter(Knowledge.id != exclude_id if exclude_id else True)
                        .order_by(Knowledge.updated_at.desc())
                        .limit(limit)
                        .all()
                    )

                return [self._knowledge_to_dict(k) for k in knowledge_list]

            finally:
                db.close()
        else:
            # JSON: タグベースフィルタリング
            data = self._load_json("knowledge.json")

            # 自分自身を除外
            if exclude_id:
                data = [k for k in data if k["id"] != exclude_id]

            # タグが一致するナレッジをフィルタ
            related = []
            if tags:
                for k in data:
                    k_tags = k.get("tags", [])
                    if k_tags:
                        # タグの一致数を計算
                        match_count = len(set(k_tags) & set(tags))
                        if match_count > 0:
                            related.append({**k, "_tag_match_count": match_count})

                # タグ一致数でソート
                related.sort(key=lambda x: x.get("_tag_match_count", 0), reverse=True)
                related = related[:limit]

                # _tag_match_count を削除
                for item in related:
                    item.pop("_tag_match_count", None)

            # フォールバック: タグ一致が0件なら最近のナレッジを返す
            if not related:
                related = sorted(
                    data,
                    key=lambda x: x.get("updated_at", x.get("created_at", "")),
                    reverse=True,
                )[:limit]

            return related

    def create_knowledge(self, knowledge_data: Dict) -> Dict:
        """
        ナレッジを作成

        Args:
            knowledge_data: ナレッジデータ

        Returns:
            作成されたナレッジデータ
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                knowledge = Knowledge(
                    title=knowledge_data["title"],
                    summary=knowledge_data["summary"],
                    content=knowledge_data.get("content"),
                    category=knowledge_data["category"],
                    tags=knowledge_data.get("tags", []),
                    status=knowledge_data.get("status", "draft"),
                    priority=knowledge_data.get("priority", "medium"),
                    project=knowledge_data.get("project"),
                    owner=knowledge_data["owner"],
                    created_by_id=knowledge_data.get("created_by_id"),
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
            data = self._load_json("knowledge.json")
            new_id = max([k["id"] for k in data], default=0) + 1

            new_knowledge = {
                "id": new_id,
                "title": knowledge_data["title"],
                "summary": knowledge_data["summary"],
                "content": knowledge_data.get("content"),
                "category": knowledge_data["category"],
                "tags": knowledge_data.get("tags", []),
                "status": knowledge_data.get("status", "draft"),
                "priority": knowledge_data.get("priority", "medium"),
                "project": knowledge_data.get("project"),
                "owner": knowledge_data["owner"],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "created_by_id": knowledge_data.get("created_by_id"),
            }

            data.append(new_knowledge)
            self._save_json("knowledge.json", data)
            return new_knowledge

    def update_knowledge(
        self, knowledge_id: int, knowledge_data: Dict
    ) -> Optional[Dict]:
        """
        ナレッジを更新

        Args:
            knowledge_id: ナレッジID
            knowledge_data: 更新データ

        Returns:
            更新されたナレッジデータ（見つからない場合はNone）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                knowledge = (
                    db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
                )
                if not knowledge:
                    return None

                for key, value in knowledge_data.items():
                    if hasattr(knowledge, key) and key not in ["id", "created_at"]:
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
            data = self._load_json("knowledge.json")
            knowledge = next((k for k in data if k["id"] == knowledge_id), None)

            if not knowledge:
                return None

            for key, value in knowledge_data.items():
                if key != "id":
                    knowledge[key] = value

            knowledge["updated_at"] = datetime.now().isoformat()
            self._save_json("knowledge.json", data)
            return knowledge

    def delete_knowledge(self, knowledge_id: int) -> bool:
        """
        ナレッジを削除

        Args:
            knowledge_id: ナレッジID

        Returns:
            削除成功時True
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                knowledge = (
                    db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
                )
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
            data = self._load_json("knowledge.json")
            original_length = len(data)
            data = [k for k in data if k["id"] != knowledge_id]

            if len(data) < original_length:
                self._save_json("knowledge.json", data)
                return True
            return False

    # ============================================================
    # 通知（Notification）
    # ============================================================

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
            except Exception as e:
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

    # ============================================================
    # SOP（標準施工手順）
    # ============================================================

    def get_sop_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        SOP一覧を取得

        Args:
            filters: フィルタ条件 (category, search, status など)

        Returns:
            SOPリスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                from sqlalchemy.orm import selectinload

                # N+1クエリ最適化: リレーションを先読み
                query = db.query(SOP).options(
                    selectinload(SOP.created_by),
                    selectinload(SOP.updated_by)
                )

                # フィルタリング
                if filters:
                    if "category" in filters:
                        query = query.filter(SOP.category == filters["category"])
                    if "status" in filters:
                        query = query.filter(SOP.status == filters["status"])
                    if "search" in filters:
                        search_term = f"%{filters['search']}%"
                        query = query.filter(
                            (SOP.title.ilike(search_term))
                            | (SOP.content.ilike(search_term))
                        )

                results = query.order_by(SOP.updated_at.desc()).all()
                return [self._sop_to_dict(s) for s in results]
            finally:
                db.close()
        else:
            data = self._load_json("sop.json")

            # フィルタリング
            if filters:
                if "category" in filters:
                    data = [s for s in data if s.get("category") == filters["category"]]
                if "status" in filters:
                    data = [s for s in data if s.get("status") == filters["status"]]
                if "search" in filters:
                    search_term = filters["search"].lower()
                    data = [
                        s
                        for s in data
                        if search_term in s.get("title", "").lower()
                        or search_term in s.get("content", "").lower()
                    ]

            return data

    def get_sop_by_id(self, sop_id: int) -> Optional[Dict]:
        """
        SOPをIDで取得

        Args:
            sop_id: SOP ID

        Returns:
            SOPデータ（見つからない場合はNone）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                from sqlalchemy.orm import selectinload

                # N+1クエリ最適化: リレーションを先読み
                sop = (
                    db.query(SOP)
                    .options(
                        selectinload(SOP.created_by),
                        selectinload(SOP.updated_by)
                    )
                    .filter(SOP.id == sop_id)
                    .first()
                )
                return self._sop_to_dict(sop) if sop else None
            finally:
                db.close()
        else:
            data = self._load_json("sop.json")
            return next((s for s in data if s["id"] == sop_id), None)

    # ============================================================
    # Incident（事故・ヒヤリレポート）
    # ============================================================

    def get_incidents_list(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        インシデント一覧を取得

        Args:
            filters: フィルタ条件 (project, severity, status など)

        Returns:
            インシデントリスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                from sqlalchemy.orm import selectinload

                # N+1クエリ最適化: リレーションを先読み
                query = db.query(Incident).options(
                    selectinload(Incident.reporter)
                )

                # フィルタリング
                if filters:
                    if "project" in filters:
                        query = query.filter(Incident.project == filters["project"])
                    if "severity" in filters:
                        query = query.filter(Incident.severity == filters["severity"])
                    if "status" in filters:
                        query = query.filter(Incident.status == filters["status"])
                    if "search" in filters:
                        search_term = f"%{filters['search']}%"
                        query = query.filter(
                            (Incident.title.ilike(search_term))
                            | (Incident.description.ilike(search_term))
                        )

                results = query.order_by(Incident.incident_date.desc()).all()
                return [self._incident_to_dict(i) for i in results]
            finally:
                db.close()
        else:
            data = self._load_json("incidents.json")

            # フィルタリング
            if filters:
                if "project" in filters:
                    data = [i for i in data if i.get("project") == filters["project"]]
                if "severity" in filters:
                    data = [i for i in data if i.get("severity") == filters["severity"]]
                if "status" in filters:
                    data = [i for i in data if i.get("status") == filters["status"]]
                if "search" in filters:
                    search_term = filters["search"].lower()
                    data = [
                        i
                        for i in data
                        if search_term in i.get("title", "").lower()
                        or search_term in i.get("description", "").lower()
                    ]

            return sorted(data, key=lambda x: x.get("incident_date", ""), reverse=True)

    def get_incident_by_id(self, incident_id: int) -> Optional[Dict]:
        """
        インシデントをIDで取得

        Args:
            incident_id: インシデントID

        Returns:
            インシデントデータ（見つからない場合はNone）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                from sqlalchemy.orm import selectinload

                # N+1クエリ最適化: リレーションを先読み
                incident = (
                    db.query(Incident)
                    .options(
                        selectinload(Incident.reporter)
                    )
                    .filter(Incident.id == incident_id)
                    .first()
                )
                return self._incident_to_dict(incident) if incident else None
            finally:
                db.close()
        else:
            data = self._load_json("incidents.json")
            return next((i for i in data if i["id"] == incident_id), None)

    # ============================================================
    # Approval（承認フロー）
    # ============================================================

    def get_approvals_list(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        承認一覧を取得

        Args:
            filters: フィルタ条件 (status, type, requester_id など)

        Returns:
            承認リスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                query = db.query(Approval)

                # フィルタリング
                if filters:
                    if "status" in filters:
                        query = query.filter(Approval.status == filters["status"])
                    if "type" in filters:
                        query = query.filter(Approval.type == filters["type"])
                    if "requester_id" in filters:
                        query = query.filter(
                            Approval.requester_id == filters["requester_id"]
                        )
                    if "priority" in filters:
                        query = query.filter(Approval.priority == filters["priority"])

                results = query.order_by(Approval.created_at.desc()).all()
                return [self._approval_to_dict(a) for a in results]
            finally:
                db.close()
        else:
            data = self._load_json("approvals.json")

            # フィルタリング
            if filters:
                if "status" in filters:
                    data = [a for a in data if a.get("status") == filters["status"]]
                if "type" in filters:
                    data = [a for a in data if a.get("type") == filters["type"]]
                if "requester_id" in filters:
                    data = [
                        a
                        for a in data
                        if a.get("requester_id") == filters["requester_id"]
                    ]
                if "priority" in filters:
                    data = [a for a in data if a.get("priority") == filters["priority"]]

            return sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)

    # ============================================================
    # Regulation（法令・規格）
    # ============================================================

    def get_regulation_by_id(self, regulation_id: int) -> Optional[Dict]:
        """
        法令をIDで取得

        Args:
            regulation_id: 法令ID

        Returns:
            法令データ（見つからない場合はNone）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                from models import Regulation

                regulation = (
                    db.query(Regulation).filter(Regulation.id == regulation_id).first()
                )
                return self._regulation_to_dict(regulation) if regulation else None
            finally:
                db.close()
        else:
            data = self._load_json("regulations.json")
            return next((r for r in data if r["id"] == regulation_id), None)

    # ============================================================
    # Project（プロジェクト）
    # ============================================================

    def get_projects_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        プロジェクト一覧を取得

        Args:
            filters: フィルタ条件 (type, status など)

        Returns:
            プロジェクトリスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                query = db.query(Project)

                # フィルタリング
                if filters:
                    if "type" in filters:
                        query = query.filter(Project.type == filters["type"])
                    if "status" in filters:
                        query = query.filter(Project.status == filters["status"])

                results = query.order_by(Project.updated_at.desc()).all()
                return [self._project_to_dict(p) for p in results]
            finally:
                db.close()
        else:
            # プロジェクトはJSONベースのみ
            data = self._load_json("projects.json")

            # フィルタリング
            if filters:
                if "type" in filters:
                    data = [p for p in data if p.get("type") == filters["type"]]
                if "status" in filters:
                    data = [p for p in data if p.get("status") == filters["status"]]

            return data

    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """
        プロジェクトをIDで取得

        Args:
            project_id: プロジェクトID

        Returns:
            プロジェクトデータ（見つからない場合はNone）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                return self._project_to_dict(project) if project else None
            finally:
                db.close()
        else:
            # プロジェクトはJSONベースのみ
            data = self._load_json("projects.json")
            return next((p for p in data if p["id"] == project_id), None)

    def get_project_progress(self, project_id: int) -> Dict:
        """
        プロジェクトの進捗率を計算

        Args:
            project_id: プロジェクトID

        Returns:
            進捗情報
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return {
                    "progress_percentage": 0,
                    "completed_tasks": 0,
                    "total_tasks": 0,
                }
            db = factory()
            try:
                # プロジェクトの全タスクを取得
                tasks = (
                    db.query(ProjectTask)
                    .filter(ProjectTask.project_id == project_id)
                    .all()
                )

                if not tasks:
                    return {
                        "progress_percentage": 0,
                        "completed_tasks": 0,
                        "total_tasks": 0,
                    }

                total_tasks = len(tasks)
                completed_tasks = len([t for t in tasks if t.status == "completed"])

                # タスクの進捗率を加重平均で計算
                total_weighted_progress = sum(t.progress_percentage for t in tasks)
                progress_percentage = (
                    total_weighted_progress // total_tasks if total_tasks > 0 else 0
                )

                return {
                    "progress_percentage": progress_percentage,
                    "completed_tasks": completed_tasks,
                    "total_tasks": total_tasks,
                    "in_progress_tasks": len(
                        [t for t in tasks if t.status == "in_progress"]
                    ),
                    "pending_tasks": len([t for t in tasks if t.status == "pending"]),
                }
            finally:
                db.close()
        else:
            # JSONベースの実装
            tasks = self._load_json("project_tasks.json")
            project_tasks = [t for t in tasks if t.get("project_id") == project_id]

            if not project_tasks:
                return {
                    "progress_percentage": 0,
                    "completed_tasks": 0,
                    "total_tasks": 0,
                }

            total_tasks = len(project_tasks)
            completed_tasks = len(
                [t for t in project_tasks if t.get("status") == "completed"]
            )

            # タスクの進捗率を加重平均で計算
            total_weighted_progress = sum(
                t.get("progress_percentage", 0) for t in project_tasks
            )
            progress_percentage = (
                total_weighted_progress // total_tasks if total_tasks > 0 else 0
            )

            return {
                "progress_percentage": progress_percentage,
                "completed_tasks": completed_tasks,
                "total_tasks": total_tasks,
                "in_progress_tasks": len(
                    [t for t in project_tasks if t.get("status") == "in_progress"]
                ),
                "pending_tasks": len(
                    [t for t in project_tasks if t.get("status") == "pending"]
                ),
            }

    # ============================================================
    # Expert（専門家）
    # ============================================================

    def get_experts_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        専門家一覧を取得

        Args:
            filters: フィルタ条件 (specialization, is_available など)

        Returns:
            専門家リスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                query = db.query(Expert)

                # フィルタリング
                if filters:
                    if "specialization" in filters:
                        query = query.filter(
                            Expert.specialization == filters["specialization"]
                        )
                    if "is_available" in filters:
                        query = query.filter(
                            Expert.is_available == filters["is_available"]
                        )

                results = query.order_by(Expert.rating.desc()).all()
                return [self._expert_to_dict(e) for e in results]
            finally:
                db.close()
        else:
            # 専門家はJSONベースのみ
            data = self._load_json("experts.json")

            # フィルタリング
            if filters:
                if "specialization" in filters:
                    data = [
                        e
                        for e in data
                        if e.get("specialization") == filters["specialization"]
                    ]
                if "is_available" in filters:
                    data = [
                        e
                        for e in data
                        if e.get("is_available") == filters["is_available"]
                    ]

            return data

    def get_expert_by_id(self, expert_id: int) -> Optional[Dict]:
        """
        専門家をIDで取得

        Args:
            expert_id: 専門家ID

        Returns:
            専門家データ（見つからない場合はNone）
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                expert = db.query(Expert).filter(Expert.id == expert_id).first()
                return self._expert_to_dict(expert) if expert else None
            finally:
                db.close()
        else:
            # 専門家はJSONベースのみ
            data = self._load_json("experts.json")
            return next((e for e in data if e["id"] == expert_id), None)

    def get_expert_stats(self, expert_id: int = None) -> Dict:
        """
        専門家の統計を取得

        Args:
            expert_id: 特定の専門家のID（Noneの場合は全専門家の統計）

        Returns:
            統計情報
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return {}
            db = factory()
            try:
                if expert_id:
                    # 特定の専門家の統計
                    expert = db.query(Expert).filter(Expert.id == expert_id).first()
                    if not expert:
                        return {}

                    # 評価の平均を計算
                    ratings = (
                        db.query(ExpertRating)
                        .filter(ExpertRating.expert_id == expert_id)
                        .all()
                    )
                    avg_rating = (
                        sum(r.rating for r in ratings) / len(ratings) if ratings else 0
                    )

                    # 相談件数を取得
                    consultations = (
                        db.query(Consultation)
                        .filter(Consultation.expert_id == expert.user_id)
                        .all()
                    )

                    return {
                        "expert_id": expert_id,
                        "consultation_count": len(consultations),
                        "average_rating": round(avg_rating, 1),
                        "total_ratings": len(ratings),
                        "specialization": expert.specialization,
                        "experience_years": expert.experience_years,
                        "is_available": expert.is_available,
                    }
                else:
                    # 全専門家の統計
                    experts = db.query(Expert).all()
                    stats = []

                    for expert in experts:
                        ratings = (
                            db.query(ExpertRating)
                            .filter(ExpertRating.expert_id == expert.id)
                            .all()
                        )
                        avg_rating = (
                            sum(r.rating for r in ratings) / len(ratings)
                            if ratings
                            else 0
                        )
                        consultations = (
                            db.query(Consultation)
                            .filter(Consultation.expert_id == expert.user_id)
                            .all()
                        )

                        stats.append(
                            {
                                "expert_id": expert.id,
                                "name": expert.user.full_name
                                if expert.user
                                else "Unknown",
                                "specialization": expert.specialization,
                                "consultation_count": len(consultations),
                                "average_rating": round(avg_rating, 1),
                                "total_ratings": len(ratings),
                                "experience_years": expert.experience_years,
                                "is_available": expert.is_available,
                            }
                        )

                    return {"experts": stats}
            finally:
                db.close()
        else:
            # JSONベースの実装
            experts = self._load_json("experts.json")
            ratings = self._load_json("expert_ratings.json")
            consultations = self._load_json("consultations.json")

            if expert_id:
                expert = next((e for e in experts if e["id"] == expert_id), None)
                if not expert:
                    return {}

                expert_ratings = [r for r in ratings if r.get("expert_id") == expert_id]
                avg_rating = (
                    sum(r.get("rating", 0) for r in expert_ratings)
                    / len(expert_ratings)
                    if expert_ratings
                    else 0
                )

                expert_consultations = [
                    c
                    for c in consultations
                    if c.get("expert_id") == expert.get("user_id")
                ]

                return {
                    "expert_id": expert_id,
                    "consultation_count": len(expert_consultations),
                    "average_rating": round(avg_rating, 1),
                    "total_ratings": len(expert_ratings),
                    "specialization": expert.get("specialization"),
                    "experience_years": expert.get("experience_years", 0),
                    "is_available": expert.get("is_available", True),
                }
            else:
                stats = []
                for expert in experts:
                    expert_ratings = [
                        r for r in ratings if r.get("expert_id") == expert["id"]
                    ]
                    avg_rating = (
                        sum(r.get("rating", 0) for r in expert_ratings)
                        / len(expert_ratings)
                        if expert_ratings
                        else 0
                    )
                    expert_consultations = [
                        c
                        for c in consultations
                        if c.get("expert_id") == expert.get("user_id")
                    ]

                    stats.append(
                        {
                            "expert_id": expert["id"],
                            "name": expert.get("name", "Unknown"),
                            "specialization": expert.get("specialization"),
                            "consultation_count": len(expert_consultations),
                            "average_rating": round(avg_rating, 1),
                            "total_ratings": len(expert_ratings),
                            "experience_years": expert.get("experience_years", 0),
                            "is_available": expert.get("is_available", True),
                        }
                    )

                return {"experts": stats}

    def calculate_expert_rating(self, expert_id: int) -> float:
        """
        専門家の評価をアルゴリズムで計算

        評価アルゴリズム:
        - 基本評価: ユーザーレビュー平均 (40%)
        - 相談件数: 件数に応じたボーナス (30%)
        - 応答時間: 平均応答時間が短いほど高評価 (20%)
        - 経験年数: 経験年数に応じたボーナス (10%)

        Args:
            expert_id: 専門家ID

        Returns:
            計算された評価スコア (0-5)
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return 0.0
            db = factory()
            try:
                expert = db.query(Expert).filter(Expert.id == expert_id).first()
                if not expert:
                    return 0.0

                # ユーザーレビュー平均
                ratings = (
                    db.query(ExpertRating)
                    .filter(ExpertRating.expert_id == expert_id)
                    .all()
                )
                user_rating_avg = (
                    sum(r.rating for r in ratings) / len(ratings) if ratings else 3.0
                )  # デフォルト3.0

                # 相談件数ボーナス (0-50件: 0-1.0点)
                consultation_count = expert.consultation_count
                consultation_bonus = min(consultation_count / 50.0, 1.0)

                # 応答時間ボーナス (平均応答時間が短いほど高評価)
                response_time = expert.response_time_avg or 60  # デフォルト60分
                response_bonus = max(0, 1.0 - (response_time / 120.0))  # 120分以上で0点

                # 経験年数ボーナス (0-20年: 0-1.0点)
                experience_bonus = min(expert.experience_years / 20.0, 1.0)

                # 加重平均で最終評価を計算
                final_rating = (
                    user_rating_avg * 0.4
                    + consultation_bonus * 0.3
                    + response_bonus * 0.2
                    + experience_bonus * 0.1
                )

                # 0-5の範囲にクリッピング
                final_rating = max(0.0, min(5.0, final_rating))

                return round(final_rating, 1)
            finally:
                db.close()
        else:
            # JSONベースの実装
            experts = self._load_json("experts.json")
            ratings = self._load_json("expert_ratings.json")

            expert = next((e for e in experts if e["id"] == expert_id), None)
            if not expert:
                return 0.0

            # ユーザーレビュー平均
            expert_ratings = [r for r in ratings if r.get("expert_id") == expert_id]
            user_rating_avg = (
                sum(r.get("rating", 0) for r in expert_ratings) / len(expert_ratings)
                if expert_ratings
                else 3.0
            )

            # 相談件数ボーナス
            consultation_count = expert.get("consultation_count", 0)
            consultation_bonus = min(consultation_count / 50.0, 1.0)

            # 応答時間ボーナス
            response_time = expert.get("response_time_avg", 60)
            response_bonus = max(0, 1.0 - (response_time / 120.0))

            # 経験年数ボーナス
            experience_years = expert.get("experience_years", 0)
            experience_bonus = min(experience_years / 20.0, 1.0)

            # 加重平均で最終評価を計算
            final_rating = (
                user_rating_avg * 0.4
                + consultation_bonus * 0.3
                + response_bonus * 0.2
                + experience_bonus * 0.1
            )

            # 0-5の範囲にクリッピング
            final_rating = max(0.0, min(5.0, final_rating))

            return round(final_rating, 1)

    # ============================================================
    # AccessLog（アクセスログ）
    # ============================================================

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
            except Exception as e:
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

    # ============================================================
    # ヘルパーメソッド（ORMオブジェクト→辞書変換）
    # ============================================================

    @staticmethod
    def _knowledge_to_dict(knowledge: Knowledge) -> Dict:
        """KnowledgeオブジェクトをDictに変換"""
        if not knowledge:
            return None
        return {
            "id": knowledge.id,
            "title": knowledge.title,
            "summary": knowledge.summary,
            "content": knowledge.content,
            "category": knowledge.category,
            "tags": knowledge.tags or [],
            "status": knowledge.status,
            "priority": knowledge.priority,
            "project": knowledge.project,
            "owner": knowledge.owner,
            "created_at": knowledge.created_at.isoformat()
            if knowledge.created_at
            else None,
            "updated_at": knowledge.updated_at.isoformat()
            if knowledge.updated_at
            else None,
            "created_by_id": knowledge.created_by_id,
            "updated_by_id": knowledge.updated_by_id,
        }

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
            "created_at": notification.created_at.isoformat()
            if notification.created_at
            else None,
            "sent_at": notification.sent_at.isoformat()
            if notification.sent_at
            else None,
            "status": notification.status,
        }

    @staticmethod
    def _regulation_to_dict(regulation) -> Dict:
        """RegulationオブジェクトをDictに変換"""
        if not regulation:
            return None
        return {
            "id": regulation.id,
            "title": regulation.title,
            "issuer": regulation.issuer,
            "category": regulation.category,
            "revision_date": regulation.revision_date.isoformat()
            if regulation.revision_date
            else None,
            "applicable_scope": regulation.applicable_scope or [],
            "summary": regulation.summary,
            "content": regulation.content,
            "status": regulation.status,
            "effective_date": regulation.effective_date.isoformat()
            if regulation.effective_date
            else None,
            "url": regulation.url,
            "created_at": regulation.created_at.isoformat()
            if regulation.created_at
            else None,
            "updated_at": regulation.updated_at.isoformat()
            if regulation.updated_at
            else None,
        }

    @staticmethod
    def _sop_to_dict(sop: SOP) -> Dict:
        """SOPオブジェクトをDictに変換"""
        if not sop:
            return None
        return {
            "id": sop.id,
            "title": sop.title,
            "category": sop.category,
            "version": sop.version,
            "revision_date": sop.revision_date.isoformat()
            if sop.revision_date
            else None,
            "target": sop.target,
            "tags": sop.tags or [],
            "content": sop.content,
            "status": sop.status,
            "supersedes_id": sop.supersedes_id,
            "attachments": sop.attachments,
            "created_at": sop.created_at.isoformat() if sop.created_at else None,
            "updated_at": sop.updated_at.isoformat() if sop.updated_at else None,
            "created_by_id": sop.created_by_id,
            "updated_by_id": sop.updated_by_id,
        }

    @staticmethod
    def _incident_to_dict(incident: Incident) -> Dict:
        """IncidentオブジェクトをDictに変換"""
        if not incident:
            return None
        return {
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "project": incident.project,
            "incident_date": incident.incident_date.isoformat()
            if incident.incident_date
            else None,
            "severity": incident.severity,
            "status": incident.status,
            "corrective_actions": incident.corrective_actions,
            "root_cause": incident.root_cause,
            "tags": incident.tags or [],
            "location": incident.location,
            "involved_parties": incident.involved_parties or [],
            "created_at": incident.created_at.isoformat()
            if incident.created_at
            else None,
            "updated_at": incident.updated_at.isoformat()
            if incident.updated_at
            else None,
            "reporter_id": incident.reporter_id,
        }

    @staticmethod
    def _approval_to_dict(approval: Approval) -> Dict:
        """ApprovalオブジェクトをDictに変換"""
        if not approval:
            return None
        return {
            "id": approval.id,
            "title": approval.title,
            "type": approval.type,
            "description": approval.description,
            "requester_id": approval.requester_id,
            "status": approval.status,
            "priority": approval.priority,
            "related_entity_type": approval.related_entity_type,
            "related_entity_id": approval.related_entity_id,
            "approval_flow": approval.approval_flow,
            "created_at": approval.created_at.isoformat()
            if approval.created_at
            else None,
            "updated_at": approval.updated_at.isoformat()
            if approval.updated_at
            else None,
            "approved_at": approval.approved_at.isoformat()
            if approval.approved_at
            else None,
            "approver_id": approval.approver_id,
        }

    @staticmethod
    def _expert_to_dict(expert) -> Dict:
        """ExpertオブジェクトをDictに変換"""
        if not expert:
            return None
        return {
            "id": expert.id,
            "user_id": expert.user_id,
            "specialization": expert.specialization,
            "experience_years": expert.experience_years,
            "certifications": expert.certifications or [],
            "rating": expert.rating,
            "consultation_count": expert.consultation_count,
            "response_time_avg": expert.response_time_avg,
            "is_available": expert.is_available,
            "bio": expert.bio,
            "created_at": expert.created_at.isoformat() if expert.created_at else None,
            "updated_at": expert.updated_at.isoformat() if expert.updated_at else None,
        }

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

    @staticmethod
    def _project_to_dict(project) -> Dict:
        """ProjectオブジェクトをDictに変換"""
        if not project:
            return None
        return {
            "id": project.id,
            "name": project.name,
            "code": project.code,
            "description": project.description,
            "type": project.type,
            "status": project.status,
            "start_date": project.start_date.isoformat()
            if project.start_date
            else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "budget": project.budget,
            "location": project.location,
            "manager_id": project.manager_id,
            "progress_percentage": project.progress_percentage,
            "created_at": project.created_at.isoformat()
            if project.created_at
            else None,
            "updated_at": project.updated_at.isoformat()
            if project.updated_at
            else None,
        }

    @staticmethod
    def _expert_to_dict(expert) -> Dict:
        """ExpertオブジェクトをDictに変換"""
        if not expert:
            return None
        return {
            "id": expert.id,
            "user_id": expert.user_id,
            "specialization": expert.specialization,
            "experience_years": expert.experience_years,
            "certifications": expert.certifications or [],
            "rating": expert.rating,
            "consultation_count": expert.consultation_count,
            "response_time_avg": expert.response_time_avg,
            "is_available": expert.is_available,
            "bio": expert.bio,
            "created_at": expert.created_at.isoformat() if expert.created_at else None,
            "updated_at": expert.updated_at.isoformat() if expert.updated_at else None,
        }

    # ============================================================
    # プロジェクト（Project）
    # ============================================================

    def get_project_progress(self, project_id: int) -> Dict:
        """
        プロジェクトの進捗%を計算

        Args:
            project_id: プロジェクトID

        Returns:
            進捗データ
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return {
                    "project_id": project_id,
                    "progress_percentage": 0,
                    "tasks_completed": 0,
                    "total_tasks": 0,
                }
            db = factory()
            try:
                # プロジェクトのタスクを取得
                tasks = (
                    db.query(ProjectTask)
                    .filter(ProjectTask.project_id == project_id)
                    .all()
                )

                if not tasks:
                    return {
                        "project_id": project_id,
                        "progress_percentage": 0,
                        "tasks_completed": 0,
                        "total_tasks": 0,
                    }

                total_tasks = len(tasks)
                completed_tasks = len([t for t in tasks if t.status == "completed"])

                progress_percentage = (
                    int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
                )

                return {
                    "project_id": project_id,
                    "progress_percentage": progress_percentage,
                    "tasks_completed": completed_tasks,
                    "total_tasks": total_tasks,
                }
            finally:
                db.close()
        else:
            # JSONベースの実装
            projects = self._load_json("projects.json")
            project_tasks = self._load_json("project_tasks.json")

            # プロジェクトのタスクを取得
            tasks = [t for t in project_tasks if t.get("project_id") == project_id]

            if not tasks:
                return {
                    "project_id": project_id,
                    "progress_percentage": 0,
                    "tasks_completed": 0,
                    "total_tasks": 0,
                }

            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get("status") == "completed"])

            progress_percentage = (
                int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
            )

            return {
                "project_id": project_id,
                "progress_percentage": progress_percentage,
                "tasks_completed": completed_tasks,
                "total_tasks": total_tasks,
            }

    def get_projects_list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        プロジェクト一覧を取得

        Args:
            filters: フィルタ条件 (type, status など)

        Returns:
            プロジェクトリスト
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                query = db.query(Project)

                # フィルタリング
                if filters:
                    if "type" in filters:
                        query = query.filter(Project.type == filters["type"])
                    if "status" in filters:
                        query = query.filter(Project.status == filters["status"])

                results = query.all()
                return [self._project_to_dict(project) for project in results]
            finally:
                db.close()
        else:
            data = self._load_json("projects.json")

            # フィルタリング
            if filters:
                if "type" in filters:
                    data = [p for p in data if p.get("type") == filters["type"]]
                if "status" in filters:
                    data = [p for p in data if p.get("status") == filters["status"]]

            return data

    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """
        プロジェクト詳細を取得

        Args:
            project_id: プロジェクトID

        Returns:
            プロジェクトデータ
        """
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                return self._project_to_dict(project)
            finally:
                db.close()
        else:
            projects = self._load_json("projects.json")
            return next((p for p in projects if p["id"] == project_id), None)


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
                config = db.query(MS365SyncConfig).filter(MS365SyncConfig.id == config_id).first()
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
            new_config = {"id": new_id, **config_data, "created_at": datetime.utcnow().isoformat()}
            configs.append(new_config)
            self._save_json("ms365_sync_configs.json", configs)
            return new_config

    def update_ms365_sync_config(self, config_id: int, update_data: Dict) -> Optional[Dict]:
        """MS365同期設定を更新"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                config = db.query(MS365SyncConfig).filter(MS365SyncConfig.id == config_id).first()
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
                    config["updated_at"] = datetime.utcnow().isoformat()
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
                config = db.query(MS365SyncConfig).filter(MS365SyncConfig.id == config_id).first()
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
            new_history = {"id": new_id, **history_data, "created_at": datetime.utcnow().isoformat()}
            histories.append(new_history)
            self._save_json("ms365_sync_histories.json", histories)
            return new_history

    def update_ms365_sync_history(self, history_id: int, update_data: Dict) -> Optional[Dict]:
        """MS365同期履歴を更新"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                history = db.query(MS365SyncHistory).filter(MS365SyncHistory.id == history_id).first()
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

    def get_ms365_sync_histories_by_config(self, config_id: int, limit: int = 20) -> List[Dict]:
        """設定IDで同期履歴を取得"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return []
            db = factory()
            try:
                histories = db.query(MS365SyncHistory)\
                    .filter(MS365SyncHistory.config_id == config_id)\
                    .order_by(MS365SyncHistory.sync_started_at.desc())\
                    .limit(limit)\
                    .all()
                return [self._ms365_sync_history_to_dict(h) for h in histories]
            finally:
                db.close()
        else:
            histories = self._load_json("ms365_sync_histories.json")
            filtered = [h for h in histories if h.get("config_id") == config_id]
            filtered.sort(key=lambda x: x.get("sync_started_at", ""), reverse=True)
            return filtered[:limit]

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
                mappings = db.query(MS365FileMapping)\
                    .filter(MS365FileMapping.config_id == config_id)\
                    .all()
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
                mapping = db.query(MS365FileMapping)\
                    .filter(MS365FileMapping.sharepoint_file_id == file_id)\
                    .first()
                return self._ms365_file_mapping_to_dict(mapping) if mapping else None
            finally:
                db.close()
        else:
            mappings = self._load_json("ms365_file_mappings.json")
            return next((m for m in mappings if m.get("sharepoint_file_id") == file_id), None)

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
            new_mapping = {"id": new_id, **mapping_data, "created_at": datetime.utcnow().isoformat()}
            mappings.append(new_mapping)
            self._save_json("ms365_file_mappings.json", mappings)
            return new_mapping

    def update_ms365_file_mapping(self, mapping_id: int, update_data: Dict) -> Optional[Dict]:
        """MS365ファイルマッピングを更新"""
        if self._use_postgresql():
            factory = get_session_factory()
            if not factory:
                return None
            db = factory()
            try:
                mapping = db.query(MS365FileMapping).filter(MS365FileMapping.id == mapping_id).first()
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
                    mapping["updated_at"] = datetime.utcnow().isoformat()
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
            "last_sync_at": config.last_sync_at.isoformat() if config.last_sync_at else None,
            "next_sync_at": config.next_sync_at.isoformat() if config.next_sync_at else None,
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
            "sync_started_at": history.sync_started_at.isoformat() if history.sync_started_at else None,
            "sync_completed_at": history.sync_completed_at.isoformat() if history.sync_completed_at else None,
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
            "created_at": history.created_at.isoformat() if history.created_at else None,
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
            "sharepoint_modified_at": mapping.sharepoint_modified_at.isoformat() if mapping.sharepoint_modified_at else None,
            "sharepoint_size_bytes": mapping.sharepoint_size_bytes,
            "knowledge_id": mapping.knowledge_id,
            "sync_status": mapping.sync_status,
            "last_synced_at": mapping.last_synced_at.isoformat() if mapping.last_synced_at else None,
            "checksum": mapping.checksum,
            "file_metadata": mapping.file_metadata,
            "error_message": mapping.error_message,
            "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
            "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None,
        }


# グローバルインスタンス
dal = DataAccessLayer()
