"""
統合テスト: Expert Stats & Project Progress API

Phase E-2: N+1クエリ最適化の統合テストを実施
- GET /api/v1/experts/stats エンドポイント検証（TC#17）
- GET /api/v1/projects/{id}/progress エンドポイント検証（TC#18）
"""

import json
import os
import pathlib

import pytest

# PostgreSQL環境変数チェック
USE_POSTGRESQL = os.environ.get("USE_POSTGRESQL", "false").lower() == "true"


def _setup_expert_test_data(client, auth_headers):
    """専門家10人のテストデータをセットアップ"""
    # PostgreSQL環境でのみ実行（JSONモードでは専門家テーブルが存在しない）
    if not USE_POSTGRESQL:
        pytest.skip("PostgreSQL required for expert stats test")

    # SQLAlchemyセッションを直接使用してテストデータ作成
    from database import get_session_factory
    from models import Consultation, Expert, ExpertRating, User

    factory = get_session_factory()
    if not factory:
        pytest.skip("PostgreSQL session factory not available")

    session = factory()
    try:
        # 専門家10人を作成
        for i in range(10):
            user = User(
                username=f"expert_test_{i}",
                full_name=f"専門家 {i}",
                email=f"expert_test_{i}@example.com",
                password_hash="dummy_hash",
            )
            session.add(user)
            session.flush()

            expert = Expert(
                user_id=user.id,
                specialization=f"専門分野{i % 3}",
                experience_years=5 + i,
            )
            session.add(expert)
            session.flush()

            # 評価5件追加
            for j in range(5):
                rating = ExpertRating(
                    expert_id=expert.id,
                    user_id=user.id,
                    rating=4.0 + (j * 0.2),
                    review=f"評価コメント{j}",
                )
                session.add(rating)

            # 相談3件追加
            for k in range(3):
                consultation = Consultation(
                    expert_id=user.id,
                    requester_id=user.id,
                    title=f"相談{k}",
                    question=f"相談内容{k}",
                    category="Technical",
                    status="completed",
                )
                session.add(consultation)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def _setup_project_test_data(client, auth_headers):
    """プロジェクトとタスク10件のテストデータをセットアップ"""
    # PostgreSQL環境でのみ実行
    if not USE_POSTGRESQL:
        pytest.skip("PostgreSQL required for project progress test")

    from database import get_session_factory
    from models import Project, ProjectTask

    factory = get_session_factory()
    if not factory:
        pytest.skip("PostgreSQL session factory not available")

    session = factory()
    try:
        # プロジェクト1件作成
        project = Project(code="TEST-001", name="テストプロジェクト", type="construction")
        session.add(project)
        session.flush()

        # タスク10件（完了3件、進行中5件、保留2件）
        tasks_data = [
            {"status": "completed", "progress": 100},
            {"status": "completed", "progress": 100},
            {"status": "completed", "progress": 100},
            {"status": "in_progress", "progress": 50},
            {"status": "in_progress", "progress": 30},
            {"status": "in_progress", "progress": 70},
            {"status": "in_progress", "progress": 40},
            {"status": "in_progress", "progress": 60},
            {"status": "pending", "progress": 0},
            {"status": "pending", "progress": 0},
        ]

        for i, task_data in enumerate(tasks_data):
            task = ProjectTask(
                project_id=project.id,
                task_name=f"タスク{i+1}",
                description=f"タスク{i+1}の説明",
                status=task_data["status"],
                progress_percentage=task_data["progress"],
            )
            session.add(task)

        session.commit()
        return project.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


class TestExpertStatsAPI:
    """GET /api/v1/experts/stats エンドポイントの統合テスト（TC#17）"""

    def test_api_get_expert_stats_endpoint(self, client, auth_headers):
        """
        GET /api/v1/experts/stats エンドポイントの正常動作検証

        期待値:
        - HTTP 200 OK
        - JSON形式レスポンス
        - 統計データ正確性
        """
        # テストデータセットアップ
        _setup_expert_test_data(client, auth_headers)

        # APIリクエスト実行
        response = client.get("/api/v1/experts/stats", headers=auth_headers)

        # ステータスコード検証
        assert response.status_code == 200

        # レスポンス形式検証
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data

        # 統計データ検証
        stats = data["data"]
        assert "total_experts" in stats
        assert "available_experts" in stats
        assert "specializations" in stats
        assert "average_rating" in stats

        # 集計値検証（10人の専門家）
        assert stats["total_experts"] == 10
        assert stats["available_experts"] >= 0
        assert isinstance(stats["specializations"], dict)
        assert isinstance(stats["average_rating"], (int, float))

    def test_api_get_expert_stats_empty_database(self, client, auth_headers):
        """
        専門家データが存在しない場合の動作検証

        期待値:
        - HTTP 200 OK
        - 空の統計データ
        """
        # PostgreSQL環境でのみ実行
        if not USE_POSTGRESQL:
            pytest.skip("PostgreSQL required for this test")

        # APIリクエスト実行（テストデータ作成なし）
        response = client.get("/api/v1/experts/stats", headers=auth_headers)

        # ステータスコード検証
        assert response.status_code == 200

        # レスポンス形式検証
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data

        # 空の統計データ検証
        stats = data["data"]
        # エラーケースでもsuccessがTrueなので、デフォルト値を検証
        assert stats.get("total_experts", 0) >= 0
        assert stats.get("available_experts", 0) >= 0


class TestProjectProgressAPI:
    """GET /api/v1/projects/{id}/progress エンドポイントの統合テスト（TC#18）"""

    def test_api_get_project_progress_endpoint(self, client, auth_headers):
        """
        GET /api/v1/projects/{id}/progress エンドポイントの正常動作検証

        期待値:
        - HTTP 200 OK
        - 進捗率計算正確性
        """
        # テストデータセットアップ
        project_id = _setup_project_test_data(client, auth_headers)

        # APIリクエスト実行
        response = client.get(
            f"/api/v1/projects/{project_id}/progress", headers=auth_headers
        )

        # ステータスコード検証
        assert response.status_code == 200

        # レスポンス形式検証
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data

        # 進捗データ検証
        progress = data["data"]
        assert "progress_percentage" in progress
        assert "total_tasks" in progress

        # completed_tasks または tasks_completed のいずれかが存在
        assert "completed_tasks" in progress or "tasks_completed" in progress

        # 集計正確性検証
        assert progress["total_tasks"] == 10

        completed_tasks = progress.get("completed_tasks") or progress.get(
            "tasks_completed"
        )
        assert completed_tasks == 3

        # ステータス別カウント（実装により異なる）
        if "in_progress_tasks" in progress:
            assert progress["in_progress_tasks"] == 5
        if "pending_tasks" in progress:
            assert progress["pending_tasks"] == 2

        # 進捗率計算検証（期待値: 55%）
        # 完了3件(100%) + 進行中5件(平均50%) + 保留2件(0%) = (300 + 250 + 0) / 10 = 55
        expected_progress = 55
        assert (
            progress["progress_percentage"] == expected_progress
        ), f"Expected {expected_progress}%, got {progress['progress_percentage']}%"

    def test_api_get_project_progress_nonexistent_project(self, client, auth_headers):
        """
        存在しないプロジェクトIDの場合の動作検証

        期待値:
        - HTTP 200 OK（エラーケースでもsuccessがTrue）
        - デフォルト値（0%、0件）
        """
        # PostgreSQL環境でのみ実行
        if not USE_POSTGRESQL:
            pytest.skip("PostgreSQL required for this test")

        # 存在しないプロジェクトID
        nonexistent_project_id = 9999

        # APIリクエスト実行
        response = client.get(
            f"/api/v1/projects/{nonexistent_project_id}/progress", headers=auth_headers
        )

        # ステータスコード検証
        assert response.status_code == 200

        # レスポンス形式検証
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data

        # デフォルト値検証
        progress = data["data"]
        assert progress["progress_percentage"] == 0
        assert progress["total_tasks"] == 0

        completed_tasks = progress.get("completed_tasks") or progress.get(
            "tasks_completed"
        )
        assert completed_tasks == 0

    def test_api_get_project_progress_all_completed(self, client, auth_headers):
        """
        全タスク完了の場合の進捗率検証

        期待値:
        - 進捗率100%
        """
        # PostgreSQL環境でのみ実行
        if not USE_POSTGRESQL:
            pytest.skip("PostgreSQL required for this test")

        from database import get_session_factory
        from models import Project, ProjectTask

        factory = get_session_factory()
        if not factory:
            pytest.skip("PostgreSQL session factory not available")

        session = factory()
        try:
            # プロジェクト作成
            project = Project(
                code="TEST-COMPLETE", name="完了プロジェクト", type="construction"
            )
            session.add(project)
            session.flush()

            # 全タスク完了（5件）
            for i in range(5):
                task = ProjectTask(
                    project_id=project.id,
                    task_name=f"完了タスク{i+1}",
                    description=f"完了タスク{i+1}の説明",
                    status="completed",
                    progress_percentage=100,
                )
                session.add(task)

            session.commit()
            project_id = project.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        # APIリクエスト実行
        response = client.get(
            f"/api/v1/projects/{project_id}/progress", headers=auth_headers
        )

        # ステータスコード検証
        assert response.status_code == 200

        # 進捗率検証
        data = response.get_json()
        progress = data["data"]

        assert progress["total_tasks"] == 5
        completed_tasks = progress.get("completed_tasks") or progress.get(
            "tasks_completed"
        )
        assert completed_tasks == 5
        assert (
            progress["progress_percentage"] == 100
        ), f"Expected 100%, got {progress['progress_percentage']}%"
