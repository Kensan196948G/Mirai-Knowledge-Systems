"""
OperationsMixin - 運用ドメインDAL
SOP / Incidents / Approvals / Regulations
"""

from typing import Any, Dict, List, Optional

from database import get_session_factory
from models import (
    SOP,
    Approval,
    Incident,
)


class OperationsMixin:
    """SOP・インシデント・承認・法令CRUD操作"""

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
                    selectinload(SOP.created_by), selectinload(SOP.updated_by)
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
                    .options(selectinload(SOP.created_by), selectinload(SOP.updated_by))
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
                query = db.query(Incident).options(selectinload(Incident.reporter))

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
                    .options(selectinload(Incident.reporter))
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
                from sqlalchemy.orm import selectinload

                # N+1最適化: requesterとapproverを事前ロード
                query = db.query(Approval).options(
                    selectinload(Approval.requester), selectinload(Approval.approver)
                )

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
    # Serializers
    # ============================================================

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
            "revision_date": (
                sop.revision_date.isoformat() if sop.revision_date else None
            ),
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
            "incident_date": (
                incident.incident_date.isoformat() if incident.incident_date else None
            ),
            "severity": incident.severity,
            "status": incident.status,
            "corrective_actions": incident.corrective_actions,
            "root_cause": incident.root_cause,
            "tags": incident.tags or [],
            "location": incident.location,
            "involved_parties": incident.involved_parties or [],
            "created_at": (
                incident.created_at.isoformat() if incident.created_at else None
            ),
            "updated_at": (
                incident.updated_at.isoformat() if incident.updated_at else None
            ),
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
            "created_at": (
                approval.created_at.isoformat() if approval.created_at else None
            ),
            "updated_at": (
                approval.updated_at.isoformat() if approval.updated_at else None
            ),
            "approved_at": (
                approval.approved_at.isoformat() if approval.approved_at else None
            ),
            "approver_id": approval.approver_id,
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
            "revision_date": (
                regulation.revision_date.isoformat()
                if regulation.revision_date
                else None
            ),
            "applicable_scope": regulation.applicable_scope or [],
            "summary": regulation.summary,
            "content": regulation.content,
            "status": regulation.status,
            "effective_date": (
                regulation.effective_date.isoformat()
                if regulation.effective_date
                else None
            ),
            "url": regulation.url,
            "created_at": (
                regulation.created_at.isoformat() if regulation.created_at else None
            ),
            "updated_at": (
                regulation.updated_at.isoformat() if regulation.updated_at else None
            ),
        }
