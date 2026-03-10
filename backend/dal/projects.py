"""
ProjectsMixin - プロジェクトドメインDAL
"""

import logging
from typing import Any, Dict, List, Optional

from database import get_session_factory
from models import Project, ProjectTask
from sqlalchemy import case, func

logger = logging.getLogger(__name__)


class ProjectsMixin:
    """プロジェクトCRUD・進捗操作"""

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

    def get_project_progress(self, project_id: int) -> Dict:
        """
        プロジェクトの進捗%を計算（N+1クエリ最適化版）

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
                # PostgreSQL側で集計を完結（クエリ1回）
                task_stats = (
                    db.query(
                        func.count(ProjectTask.id).label("total_tasks"),
                        func.count(
                            case((ProjectTask.status == "completed", 1))
                        ).label("completed_tasks"),
                    )
                    .filter(ProjectTask.project_id == project_id)
                    .first()
                )

                if not task_stats or task_stats.total_tasks == 0:
                    return {
                        "project_id": project_id,
                        "progress_percentage": 0,
                        "tasks_completed": 0,
                        "total_tasks": 0,
                    }

                progress_percentage = (
                    int((task_stats.completed_tasks / task_stats.total_tasks) * 100)
                    if task_stats.total_tasks > 0
                    else 0
                )

                result = {
                    "project_id": project_id,
                    "progress_percentage": progress_percentage,
                    "tasks_completed": task_stats.completed_tasks,
                    "total_tasks": task_stats.total_tasks,
                }
                logger.info(
                    "get_project_progress(): N+1最適化クエリ完了 - project_id=%d, progress=%d%%",
                    project_id,
                    progress_percentage,
                )
                return result
            except Exception as e:
                logger.error(
                    "get_project_progress(): クエリ実行エラー - project_id=%d: %s",
                    project_id,
                    str(e),
                )
                raise
            finally:
                db.close()
        else:
            # JSONベースの実装
            self._load_json("projects.json")
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
            "start_date": (
                project.start_date.isoformat() if project.start_date else None
            ),
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "budget": project.budget,
            "location": project.location,
            "manager_id": project.manager_id,
            "progress_percentage": project.progress_percentage,
            "created_at": (
                project.created_at.isoformat() if project.created_at else None
            ),
            "updated_at": (
                project.updated_at.isoformat() if project.updated_at else None
            ),
        }
