"""
ExpertsMixin - 専門家ドメインDAL
"""

import hashlib
import json as _json
import logging
from typing import Any, Dict, List, Optional

from app_helpers import CACHE_TTL_DEFAULT, CACHE_TTL_LONG, cache_get, cache_set
from database import get_session_factory
from models import Consultation, Expert, ExpertRating
from sqlalchemy import func
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class ExpertsMixin:
    """専門家CRUD・統計操作"""

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
            filter_hash = hashlib.md5(
                _json.dumps(filters or {}, sort_keys=True).encode()
            ).hexdigest()[:8]
            cache_key = f"experts:list:{filter_hash}"
            cached = cache_get(cache_key)
            if cached is not None:
                return cached

            # 一括ロードしてメモリ内フィルタリング
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

            cache_set(cache_key, data, ttl=CACHE_TTL_LONG)
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

                    result = {
                        "expert_id": expert_id,
                        "consultation_count": len(consultations),
                        "average_rating": round(avg_rating, 1),
                        "total_ratings": len(ratings),
                        "specialization": expert.specialization,
                        "experience_years": expert.experience_years,
                        "is_available": expert.is_available,
                    }
                    logger.info(
                        "get_expert_stats(): クエリ完了 - expert_id=%d", expert_id
                    )
                    return result
                else:
                    # 全専門家の統計（N+1クエリ最適化版）
                    # サブクエリで評価データを集計
                    expert_ratings_subq = (
                        db.query(
                            ExpertRating.expert_id,
                            func.avg(ExpertRating.rating).label("avg_rating"),
                            func.count(ExpertRating.id).label("rating_count"),
                        )
                        .group_by(ExpertRating.expert_id)
                        .subquery()
                    )

                    # サブクエリで相談件数を集計
                    consultation_counts_subq = (
                        db.query(
                            Consultation.expert_id.label("expert_user_id"),
                            func.count(Consultation.id).label("consultation_count"),
                        )
                        .group_by(Consultation.expert_id)
                        .subquery()
                    )

                    # Eager Loadingで一発取得（クエリ3回に削減）
                    experts_with_stats = (
                        db.query(Expert)
                        .options(joinedload(Expert.user))  # Userを先読み（1対1）
                        .outerjoin(
                            expert_ratings_subq,
                            Expert.id == expert_ratings_subq.c.expert_id,
                        )
                        .outerjoin(
                            consultation_counts_subq,
                            Expert.user_id == consultation_counts_subq.c.expert_user_id,
                        )
                        .add_columns(
                            expert_ratings_subq.c.avg_rating,
                            expert_ratings_subq.c.rating_count,
                            consultation_counts_subq.c.consultation_count,
                        )
                        .all()
                    )

                    # ループ内でクエリ不要（既に全データ取得済み）
                    stats = []
                    for expert, avg_rating, rating_count, consultation_count in (
                        experts_with_stats
                    ):
                        stats.append(
                            {
                                "expert_id": expert.id,
                                "name": (
                                    expert.user.full_name if expert.user else "Unknown"
                                ),
                                "specialization": expert.specialization,
                                "consultation_count": consultation_count or 0,
                                "average_rating": (
                                    round(float(avg_rating), 1) if avg_rating else 0
                                ),
                                "total_ratings": rating_count or 0,
                                "experience_years": expert.experience_years,
                                "is_available": expert.is_available,
                            }
                        )

                    logger.info(
                        "get_expert_stats(): N+1最適化クエリ完了 - %d件取得", len(stats)
                    )
                    return {"experts": stats}
            except Exception as e:
                logger.error("get_expert_stats(): クエリ実行エラー: %s", str(e))
                raise
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
            # JSONベースの実装: 計算結果をキャッシュして繰り返し呼び出しを回避
            cache_key = f"experts:rating:{expert_id}"
            cached = cache_get(cache_key)
            if cached is not None:
                return cached

            # 両ファイルを一括ロード
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
            result = round(final_rating, 1)
            cache_set(cache_key, result, ttl=CACHE_TTL_DEFAULT)
            return result

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
