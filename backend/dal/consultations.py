"""
dal/consultations.py - 専門家相談ドメイン DAL Mixin

Phase J-2: app_v2.py consultations ルートの Blueprint化に伴い
ドメインロジックを DAL 層へ抽出。
"""

import time
from datetime import datetime


class ConsultationsMixin:
    """専門家相談（Consultations）ドメインの DAL メソッド群"""

    # ------------------------------------------------------------------
    # 取得系
    # ------------------------------------------------------------------

    def get_consultations(self, category=None, status=None, page=1, per_page=50):
        """
        相談一覧取得（フィルタリング・ページネーション付き）

        Returns:
            dict: {data, pagination}
        """
        per_page = min(per_page, 100)
        consultations = self._load_json("consultations.json")

        filtered = consultations
        if category:
            filtered = [c for c in filtered if c.get("category") == category]
        if status:
            filtered = [c for c in filtered if c.get("status") == status]

        total_items = len(filtered)
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 1
        start_idx = (page - 1) * per_page
        paginated = filtered[start_idx : start_idx + per_page]

        return {
            "data": paginated,
            "pagination": {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "per_page": per_page,
            },
        }

    def get_consultation_by_id(self, consultation_id):
        """
        相談詳細取得（閲覧数インクリメント）

        Returns:
            dict | None
        """
        consultations = self._load_json("consultations.json")
        idx = next(
            (i for i, c in enumerate(consultations) if c["id"] == consultation_id),
            None,
        )
        if idx is None:
            return None

        consultations[idx]["views"] = consultations[idx].get("views", 0) + 1
        self._save_json("consultations.json", consultations)
        return consultations[idx]

    # ------------------------------------------------------------------
    # 作成・更新系
    # ------------------------------------------------------------------

    def create_consultation(self, data, current_user_id, current_user=None):
        """
        新規相談作成

        Args:
            data: バリデーション済みリクエストデータ
            current_user_id: 投稿者ID
            current_user: ユーザー情報dict（任意）

        Returns:
            dict: 作成された相談オブジェクト
        """
        consultations = self._load_json("consultations.json")
        new_id = max((c["id"] for c in consultations), default=0) + 1

        requester_name = (
            current_user.get("full_name", "Unknown") if current_user else "Unknown"
        )

        new_consultation = {
            "id": new_id,
            "title": data.get("title"),
            "question": data.get("question"),
            "category": data.get("category"),
            "priority": data.get("priority", "通常"),
            "status": "pending",
            "requester_id": int(current_user_id),
            "requester": requester_name,
            "expert_id": None,
            "expert": None,
            "project": data.get("project"),
            "tags": data.get("tags", []),
            "views": 0,
            "follower_count": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "answered_at": None,
        }

        consultations.append(new_consultation)
        self._save_json("consultations.json", consultations)
        return new_consultation

    def update_consultation(self, consultation_id, data, current_user_id, is_admin=False):
        """
        相談更新（所有権チェック付き）

        Returns:
            tuple: (updated_consultation | None, error_code | None)
              error_code: "NOT_FOUND" | "FORBIDDEN" | None
        """
        consultations = self._load_json("consultations.json")
        idx = next(
            (i for i, c in enumerate(consultations) if c["id"] == consultation_id),
            None,
        )
        if idx is None:
            return None, "NOT_FOUND"

        is_owner = consultations[idx].get("requester_id") == int(current_user_id)
        if not is_admin and not is_owner:
            return None, "FORBIDDEN"

        updatable_fields = ["title", "question", "category", "priority", "tags", "status"]
        for field in updatable_fields:
            if field in data:
                consultations[idx][field] = data[field]

        consultations[idx]["updated_at"] = datetime.now().isoformat()
        self._save_json("consultations.json", consultations)
        return consultations[idx], None

    def add_consultation_answer(self, consultation_id, data, current_user_id, current_user=None):
        """
        相談への回答追加

        Returns:
            tuple: (new_answer | None, requester_id | None, consultation_title | None, error_code | None)
        """
        consultations = self._load_json("consultations.json")
        idx = next(
            (i for i, c in enumerate(consultations) if c["id"] == consultation_id),
            None,
        )
        if idx is None:
            return None, None, None, "NOT_FOUND"

        expert_name = (
            current_user.get("full_name", "Unknown") if current_user else "Unknown"
        )
        expert_title = (
            current_user.get("department", "専門家") if current_user else "専門家"
        )

        new_answer = {
            "id": int(time.time() * 1000),
            "content": data.get("content"),
            "references": data.get("references"),
            "is_best_answer": data.get("is_best_answer", False),
            "expert": expert_name,
            "expert_id": int(current_user_id),
            "expert_title": expert_title,
            "author_name": expert_name,
            "created_at": datetime.now().isoformat(),
            "helpful_count": 0,
            "attachments": data.get("attachments", []),
        }

        if "answers" not in consultations[idx]:
            consultations[idx]["answers"] = []
        consultations[idx]["answers"].append(new_answer)

        if consultations[idx]["status"] == "pending":
            consultations[idx]["status"] = "answered"
            consultations[idx]["answered_at"] = datetime.now().isoformat()

        if consultations[idx].get("expert_id") is None:
            consultations[idx]["expert_id"] = int(current_user_id)
            consultations[idx]["expert"] = expert_name

        consultations[idx]["updated_at"] = datetime.now().isoformat()
        self._save_json("consultations.json", consultations)

        requester_id = consultations[idx].get("requester_id")
        consultation_title = consultations[idx].get("title", "")
        return new_answer, requester_id, consultation_title, None
