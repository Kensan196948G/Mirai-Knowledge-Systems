"""
KnowledgeMixin - ナレッジドメインDAL
"""

import hashlib
import json as _json
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_session_factory
from models import Knowledge


class KnowledgeMixin:
    """ナレッジCRUD操作"""

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
                    selectinload(Knowledge.updated_by),
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
            # キャッシュキー（フィルタ内容を含む）
            filter_hash = hashlib.md5(
                _json.dumps(filters or {}, sort_keys=True).encode()
            ).hexdigest()[:8]
            cache_key = f"knowledge:list:{filter_hash}"
            # 循環インポート回避のため遅延インポート
            from app_helpers import cache_get, cache_set  # noqa: PLC0415
            cached = cache_get(cache_key)
            if cached is not None:
                return cached

            # 一括ロードしてメモリ内フィルタリング（load_data重複呼び出し排除）
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

            cache_set(cache_key, data, ttl=3600)  # CACHE_TTL_LONG: 静的データ用
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
                        selectinload(Knowledge.updated_by),
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
                from sqlalchemy import func
                from sqlalchemy.orm import selectinload

                # タグ一致数をSQLで直接計算（N+1回避）
                # cardinality(array_intersect(tags, :tags)) でタグ一致数を計算
                if tags:
                    # PostgreSQLのarray演算子を使用してタグ一致数を計算
                    func.cardinality(
                        func.array(func.unnest(Knowledge.tags)).op("&&")(
                            func.array(tags)
                        )
                    )

                    # リレーションを先読みしてN+1クエリを回避
                    query = (
                        db.query(Knowledge)
                        .options(
                            selectinload(Knowledge.created_by),
                            selectinload(Knowledge.updated_by),
                        )
                        .filter(Knowledge.status == "approved")
                        .filter(Knowledge.tags.overlap(tags))
                    )

                    if exclude_id:
                        query = query.filter(Knowledge.id != exclude_id)

                    # updated_atで降順ソート（タグ一致度は同等として最新順）
                    knowledge_list = (
                        query.order_by(Knowledge.updated_at.desc())
                        .limit(limit * 2)
                        .all()
                    )

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
                            selectinload(Knowledge.updated_by),
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
                            selectinload(Knowledge.updated_by),
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
            except Exception:
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
            except Exception:
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
            except Exception:
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
            "created_at": (
                knowledge.created_at.isoformat() if knowledge.created_at else None
            ),
            "updated_at": (
                knowledge.updated_at.isoformat() if knowledge.updated_at else None
            ),
            "created_by_id": knowledge.created_by_id,
            "updated_by_id": knowledge.updated_by_id,
        }
