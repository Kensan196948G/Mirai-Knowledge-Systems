"""
N+1クエリ最適化のユニットテスト

Phase E-2: P0最適化の効果を検証
- get_expert_stats(): クエリ実行回数を31回→3回に削減
- get_project_progress(): Python側ループ処理をDB側集計に変更
"""

import logging
import os
from unittest.mock import patch

import pytest
from data_access import DataAccessLayer
from database import get_session_factory
from models import Consultation, Expert, ExpertRating, ProjectTask, User
from sqlalchemy import event
from sqlalchemy.engine import Engine

# SQLAlchemyクエリログ設定
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


@pytest.fixture
def use_real_db():
    """実際のPostgreSQLを使用するかどうか（環境変数から判定）"""
    return os.environ.get("USE_POSTGRESQL", "false").lower() == "true"


@pytest.fixture
def db_session(use_real_db):
    """テスト用DBセッション（PostgreSQL優先、トランザクション分離）"""
    if use_real_db:
        # 実際のPostgreSQLを使用
        factory = get_session_factory()
        if factory:
            session = factory()
            # テスト開始時にトランザクション開始
            session.begin_nested()  # SAVEPOINTを使用してネストトランザクション
            yield session
            # テスト終了時に必ずロールバック（テストデータを残さない）
            session.rollback()
            session.close()
            return

    # PostgreSQL未設定の場合はスキップ
    pytest.skip("PostgreSQL required for this test (USE_POSTGRESQL=true)")


@pytest.fixture
def query_counter():
    """クエリ実行回数をカウント"""
    queries = []

    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        queries.append(statement)

    yield queries

    event.remove(Engine, "before_cursor_execute", receive_before_cursor_execute)


@pytest.fixture
def mock_session_factory(db_session):
    """DataAccessLayer用のモックセッションファクトリー（テスト分離用）"""
    # 実際のセッションをそのまま使用（トランザクション分離）
    with patch("data_access.get_session_factory") as mock:
        mock.return_value = lambda: db_session
        yield mock


class TestGetExpertStatsOptimization:
    """get_expert_stats()のN+1クエリ最適化テスト"""

    def test_get_expert_stats_query_count(
        self, db_session, query_counter, mock_session_factory
    ):
        """クエリ実行回数を検証（31回→3回に削減）"""
        # 10人の専門家を作成
        for i in range(10):
            user = User(
                username=f"user_{i}",
                full_name=f"Expert {i}",
                email=f"expert{i}@example.com",
                password_hash="hash",
            )
            db_session.add(user)
            db_session.flush()

            expert = Expert(
                user_id=user.id,
                specialization="Construction",
                experience_years=5 + i,
                is_available=True,
            )
            db_session.add(expert)
            db_session.flush()

            # 各専門家に2件の評価
            for j in range(2):
                rating = ExpertRating(
                    expert_id=expert.id,
                    user_id=user.id,
                    rating=4 + (j % 2),
                    review="Good",
                )
                db_session.add(rating)

            # 各専門家に1件の相談
            consultation = Consultation(
                expert_id=user.id,
                requester_id=user.id,
                title=f"Consultation {i}",
                question="Test question",
                category="Technical",
                status="completed",
            )
            db_session.add(consultation)

        db_session.commit()

        # クエリカウンタリセット
        query_counter.clear()

        # DataAccessLayerを使用（PostgreSQLモード）
        dal = DataAccessLayer(use_postgresql=True)
        stats = dal.get_expert_stats()

        # 結果検証
        assert "experts" in stats
        assert len(stats["experts"]) == 10

        # クエリ実行回数検証（5回以下: 最適化により大幅削減）
        query_count = len(query_counter)
        assert (
            query_count <= 5
        ), f"Expected ≤5 queries (optimized), got {query_count} queries"

    def test_get_expert_stats_result_format(self, db_session, mock_session_factory):
        """返却値形式を検証（既存APIとの互換性）"""
        # 専門家1人を作成
        user = User(
            username="user_1",
            full_name="Test Expert",
            email="expert@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.flush()

        expert = Expert(
            user_id=user.id,
            specialization="Civil Engineering",
            experience_years=10,
            is_available=True,
        )
        db_session.add(expert)
        db_session.commit()

        dal = DataAccessLayer(use_postgresql=True)
        stats = dal.get_expert_stats()

        # 形式検証
        assert "experts" in stats
        assert len(stats["experts"]) == 1

        expert_stat = stats["experts"][0]
        assert "expert_id" in expert_stat
        assert "name" in expert_stat
        assert "specialization" in expert_stat
        assert "consultation_count" in expert_stat
        assert "average_rating" in expert_stat
        assert "total_ratings" in expert_stat
        assert "experience_years" in expert_stat
        assert "is_available" in expert_stat

        assert expert_stat["name"] == "Test Expert"
        assert expert_stat["specialization"] == "Civil Engineering"
        assert expert_stat["experience_years"] == 10

    def test_get_expert_stats_zero_experts(self, db_session, mock_session_factory):
        """専門家0人の場合の動作確認"""
        dal = DataAccessLayer(use_postgresql=True)
        stats = dal.get_expert_stats()

        assert "experts" in stats
        assert len(stats["experts"]) == 0

    def test_get_expert_stats_multiple_experts(self, db_session, mock_session_factory):
        """専門家10人の場合の集計精度検証"""
        for i in range(10):
            user = User(
                username=f"user_{i}",
                full_name=f"Expert {i}",
                email=f"expert{i}@example.com",
                password_hash="hash",
            )
            db_session.add(user)
            db_session.flush()

            expert = Expert(
                user_id=user.id,
                specialization="Test",
                experience_years=i + 1,
                is_available=True,
            )
            db_session.add(expert)
            db_session.flush()

            # 評価: i=0→1件(5.0), i=1→2件(4.5), i=2→3件(4.3)...
            for j in range(i + 1):
                rating = ExpertRating(
                    expert_id=expert.id,
                    user_id=user.id,
                    rating=5 - (j % 2) * 0.5,
                    review="Test review",
                )
                db_session.add(rating)

        db_session.commit()

        dal = DataAccessLayer(use_postgresql=True)
        stats = dal.get_expert_stats()

        assert len(stats["experts"]) == 10

        # 専門家0の評価: 1件 (5.0)
        expert_0 = next(e for e in stats["experts"] if e["name"] == "Expert 0")
        assert expert_0["total_ratings"] == 1
        assert expert_0["average_rating"] == 5.0

        # 専門家9の評価: 10件
        expert_9 = next(e for e in stats["experts"] if e["name"] == "Expert 9")
        assert expert_9["total_ratings"] == 10

    def test_get_expert_stats_no_ratings(self, db_session, mock_session_factory):
        """評価0件の専門家の処理確認"""
        user = User(
            username="user_1",
            full_name="Expert No Rating",
            email="expert@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.flush()

        expert = Expert(
            user_id=user.id,
            specialization="Test",
            experience_years=5,
            is_available=True,
        )
        db_session.add(expert)
        db_session.commit()

        dal = DataAccessLayer(use_postgresql=True)
        stats = dal.get_expert_stats()

        assert len(stats["experts"]) == 1
        expert_stat = stats["experts"][0]
        assert expert_stat["total_ratings"] == 0
        assert expert_stat["average_rating"] == 0
        assert expert_stat["consultation_count"] == 0

    def test_get_expert_stats_performance_10_experts(
        self, db_session, query_counter, mock_session_factory
    ):
        """
        専門家10人時のパフォーマンス検証（TC#16）

        期待値:
        - クエリ実行回数: ≤3回（31回から大幅削減）
        - レスポンス時間: < 100ms（開発環境基準）
        """
        import time

        # テストデータ作成: 専門家10人
        for i in range(10):
            user = User(
                username=f"expert_{i}",
                full_name=f"専門家 {i}",
                email=f"expert{i}@example.com",
                password_hash="dummy",
            )
            db_session.add(user)
            db_session.flush()

            expert = Expert(
                user_id=user.id, specialization=f"専門分野{i % 3}", experience_years=5 + i
            )
            db_session.add(expert)
            db_session.flush()

            # 評価5件追加
            for j in range(5):
                rating = ExpertRating(
                    expert_id=expert.id,
                    user_id=user.id,
                    rating=4.0 + (j * 0.2),
                    review=f"評価コメント{j}",
                )
                db_session.add(rating)

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
                db_session.add(consultation)

        db_session.commit()

        # クエリカウンタリセット
        query_counter.clear()

        # パフォーマンス計測開始
        start = time.time()

        # 実行
        dal = DataAccessLayer(use_postgresql=True)
        stats = dal.get_expert_stats()

        # パフォーマンス計測終了
        elapsed_ms = (time.time() - start) * 1000

        # クエリ実行回数検証（≤3回）
        query_count = len(query_counter)
        assert query_count <= 3, f"Expected ≤3 queries, got {query_count}"

        # レスポンス時間検証（< 100ms）
        assert elapsed_ms < 100, f"Expected < 100ms, got {elapsed_ms:.2f}ms"

        # 結果検証
        assert "experts" in stats
        assert len(stats["experts"]) == 10

        # 集計正確性検証
        for stat in stats["experts"]:
            assert "expert_id" in stat
            assert "name" in stat
            assert "average_rating" in stat
            assert "total_ratings" in stat
            assert "consultation_count" in stat

            assert stat["total_ratings"] == 5
            assert stat["consultation_count"] == 3
            assert 4.0 <= stat["average_rating"] <= 4.8


class TestGetProjectProgressOptimization:
    """get_project_progress()のN+1クエリ最適化テスト"""

    def test_get_project_progress_query_count(
        self, db_session, query_counter, mock_session_factory
    ):
        """クエリ実行回数を検証（1回のまま、DB側集計に変更）"""
        # タスク100件作成
        project_id = 1
        for i in range(100):
            task = ProjectTask(
                project_id=project_id,
                task_name=f"Task {i}",
                description="Test task",
                status=["completed", "in_progress", "pending"][i % 3],
                progress_percentage=33 * (i % 3 + 1),
            )
            db_session.add(task)
        db_session.commit()

        # クエリカウンタリセット
        query_counter.clear()

        # DataAccessLayerを使用
        dal = DataAccessLayer(use_postgresql=True)
        progress = dal.get_project_progress(project_id)

        # 結果検証
        assert "total_tasks" in progress
        assert progress["total_tasks"] == 100

        # クエリ実行回数検証（2回以下: DB側集計）
        query_count = len(query_counter)
        assert (
            query_count <= 2
        ), f"Expected ≤2 queries (DB aggregation), got {query_count} queries"

    def test_get_project_progress_result_format(self, db_session, mock_session_factory):
        """返却値形式を検証"""
        project_id = 1
        task = ProjectTask(
            project_id=project_id,
            task_name="Task 1",
            description="Test task",
            status="completed",
            progress_percentage=100,
        )
        db_session.add(task)
        db_session.commit()

        dal = DataAccessLayer(use_postgresql=True)
        progress = dal.get_project_progress(project_id)

        # 形式検証
        assert "total_tasks" in progress
        assert "completed_tasks" in progress or "tasks_completed" in progress
        assert "progress_percentage" in progress

    def test_get_project_progress_all_completed(
        self, db_session, mock_session_factory
    ):
        """全タスク完了の場合の進捗率確認"""
        project_id = 1
        for i in range(5):
            task = ProjectTask(
                project_id=project_id,
                task_name=f"Task {i}",
                description="Test task",
                status="completed",
                progress_percentage=100,
            )
            db_session.add(task)
        db_session.commit()

        dal = DataAccessLayer(use_postgresql=True)
        progress = dal.get_project_progress(project_id)

        assert progress["total_tasks"] == 5
        completed = progress.get("completed_tasks") or progress.get("tasks_completed")
        assert completed == 5
        assert progress["progress_percentage"] == 100

    def test_get_project_progress_mixed_status(self, db_session, mock_session_factory):
        """混在ステータスの場合の集計確認"""
        project_id = 1
        statuses = ["completed", "in_progress", "pending"]
        for i in range(9):  # 3ステータス × 3件ずつ
            task = ProjectTask(
                project_id=project_id,
                task_name=f"Task {i}",
                description="Test task",
                status=statuses[i % 3],
                progress_percentage=33 * (i % 3 + 1),
            )
            db_session.add(task)
        db_session.commit()

        dal = DataAccessLayer(use_postgresql=True)
        progress = dal.get_project_progress(project_id)

        assert progress["total_tasks"] == 9

        # ステータス別カウント（存在する場合のみ検証）
        if "in_progress_tasks" in progress:
            assert progress["in_progress_tasks"] == 3
        if "pending_tasks" in progress:
            assert progress["pending_tasks"] == 3

    def test_get_project_progress_zero_tasks(self, db_session, mock_session_factory):
        """タスク0件の場合のエッジケース"""
        project_id = 999  # 存在しないプロジェクト
        dal = DataAccessLayer(use_postgresql=True)
        progress = dal.get_project_progress(project_id)

        assert progress["total_tasks"] == 0
        completed = progress.get("completed_tasks") or progress.get("tasks_completed")
        assert completed == 0
        assert progress["progress_percentage"] == 0
