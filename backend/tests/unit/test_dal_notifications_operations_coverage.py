"""
DAL テストカバレッジ強化: notifications.py / operations.py

対象モジュール:
- dal/notifications.py  (NotificationMixin)
- dal/operations.py     (OperationsMixin)

テスト方針:
- JSON モード（use_postgresql=False）で DAL を直接テスト
- 正常系・異常系・境界値を網羅
- _to_dict スタティックメソッドへの None 渡し
"""

import json
import os
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, BACKEND_DIR)

from dal import DataAccessLayer


# ============================================================
# ヘルパー
# ============================================================


def make_dal(tmp_path):
    """JSONモードの DAL インスタンスを返す"""
    dal = DataAccessLayer(use_postgresql=False)
    dal.data_dir = str(tmp_path)
    return dal


def write_json(tmp_path, filename, data):
    """tmp_path 配下にJSONファイルを書き込む"""
    (tmp_path / filename).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ============================================================
# NotificationMixin 追加テスト (dal/notifications.py)
# ============================================================


class TestNotificationMixinExtra:
    """NotificationMixin の境界値・異常系・静的メソッドを補強するテスト"""

    # ----------------------------------------------------------
    # get_notifications - フィルタリングの境界
    # ----------------------------------------------------------

    def test_get_notifications_missing_file_returns_empty(self, tmp_path):
        """notifications.json が存在しない場合は空リストを返す"""
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert result == []

    def test_get_notifications_all_users_returned_when_no_user_id(self, tmp_path):
        """user_id 未指定の場合、全通知が返される"""
        notifications = [
            {"id": 1, "title": "お知らせ1", "created_at": "2024-01-03", "target_users": [1]},
            {"id": 2, "title": "お知らせ2", "created_at": "2024-01-02", "target_users": [2]},
            {"id": 3, "title": "お知らせ3", "created_at": "2024-01-01", "target_users": []},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert len(result) == 3

    def test_get_notifications_filter_user_id_match(self, tmp_path):
        """user_id が target_users に含まれる通知のみ返される"""
        notifications = [
            {"id": 1, "title": "N1", "created_at": "2024-01-03", "target_users": [10, 20]},
            {"id": 2, "title": "N2", "created_at": "2024-01-02", "target_users": [20, 30]},
            {"id": 3, "title": "N3", "created_at": "2024-01-01", "target_users": [30]},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=20)
        assert len(result) == 2
        titles = {n["title"] for n in result}
        assert titles == {"N1", "N2"}

    def test_get_notifications_user_id_not_in_any_target(self, tmp_path):
        """user_id が誰の target_users にも含まれない場合は空リスト"""
        notifications = [
            {"id": 1, "title": "N1", "created_at": "2024-01-01", "target_users": [99]},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=1)
        assert result == []

    def test_get_notifications_sorted_descending_by_created_at(self, tmp_path):
        """created_at の降順でソートされる"""
        notifications = [
            {"id": 1, "title": "Old", "created_at": "2024-01-01", "target_users": []},
            {"id": 2, "title": "New", "created_at": "2024-03-01", "target_users": []},
            {"id": 3, "title": "Mid", "created_at": "2024-02-01", "target_users": []},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert result[0]["title"] == "New"
        assert result[1]["title"] == "Mid"
        assert result[2]["title"] == "Old"

    def test_get_notifications_empty_list_file(self, tmp_path):
        """空のJSONリストから呼び出すと空リストを返す"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_notifications()
        assert result == []

    def test_get_notifications_target_users_missing_key(self, tmp_path):
        """target_users キーがないエントリは user_id フィルタで除外される"""
        notifications = [
            {"id": 1, "title": "NoTargetKey", "created_at": "2024-01-01"},
        ]
        write_json(tmp_path, "notifications.json", notifications)
        dal = make_dal(tmp_path)
        result = dal.get_notifications(user_id=1)
        assert result == []

    # ----------------------------------------------------------
    # create_notification - 境界値・フィールド
    # ----------------------------------------------------------

    def test_create_notification_required_fields(self, tmp_path):
        """必須フィールドで通知を作成できる"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        notification = dal.create_notification({
            "title": "緊急通知",
            "message": "工事中断のお知らせ",
            "type": "emergency",
        })
        assert notification["id"] == 1
        assert notification["title"] == "緊急通知"
        assert notification["message"] == "工事中断のお知らせ"
        assert notification["type"] == "emergency"
        assert notification["status"] == "sent"

    def test_create_notification_default_priority_is_medium(self, tmp_path):
        """priority 未指定の場合は 'medium' がデフォルト"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        notification = dal.create_notification({
            "title": "通知",
            "message": "メッセージ",
            "type": "info",
        })
        assert notification["priority"] == "medium"

    def test_create_notification_explicit_priority(self, tmp_path):
        """priority を明示指定できる"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        notification = dal.create_notification({
            "title": "高優先通知",
            "message": "緊急",
            "type": "warning",
            "priority": "high",
        })
        assert notification["priority"] == "high"

    def test_create_notification_with_all_fields(self, tmp_path):
        """全フィールドを指定した通知を作成できる"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        notification = dal.create_notification({
            "title": "フル通知",
            "message": "詳細メッセージ",
            "type": "info",
            "target_users": [1, 2, 3],
            "target_roles": ["admin", "manager"],
            "priority": "low",
            "related_entity_type": "knowledge",
            "related_entity_id": 42,
        })
        assert notification["target_users"] == [1, 2, 3]
        assert notification["target_roles"] == ["admin", "manager"]
        assert notification["related_entity_type"] == "knowledge"
        assert notification["related_entity_id"] == 42

    def test_create_notification_increments_id_from_existing(self, tmp_path):
        """既存データの最大 ID + 1 で新規通知が作成される"""
        write_json(tmp_path, "notifications.json", [
            {"id": 5, "title": "既存", "message": "", "type": "info"},
        ])
        dal = make_dal(tmp_path)
        notification = dal.create_notification({
            "title": "新規",
            "message": "",
            "type": "info",
        })
        assert notification["id"] == 6

    def test_create_notification_persists_to_json(self, tmp_path):
        """作成した通知が JSON ファイルに永続化される"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        dal.create_notification({
            "title": "永続テスト",
            "message": "M",
            "type": "info",
        })
        # 別の DAL インスタンスで読み直しても存在する
        dal2 = make_dal(tmp_path)
        result = dal2.get_notifications()
        assert len(result) == 1
        assert result[0]["title"] == "永続テスト"

    def test_create_notification_has_created_at_field(self, tmp_path):
        """作成した通知に created_at フィールドが含まれる"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        notification = dal.create_notification({
            "title": "T",
            "message": "M",
            "type": "info",
        })
        assert "created_at" in notification
        assert notification["created_at"] is not None

    def test_create_notification_has_read_by_empty_list(self, tmp_path):
        """作成した通知の read_by は空リスト"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        notification = dal.create_notification({
            "title": "T",
            "message": "M",
            "type": "info",
        })
        assert notification["read_by"] == []

    def test_create_multiple_notifications_sequential_ids(self, tmp_path):
        """複数作成時に ID が順番に振られる"""
        write_json(tmp_path, "notifications.json", [])
        dal = make_dal(tmp_path)
        n1 = dal.create_notification({"title": "1st", "message": "", "type": "info"})
        n2 = dal.create_notification({"title": "2nd", "message": "", "type": "info"})
        n3 = dal.create_notification({"title": "3rd", "message": "", "type": "info"})
        assert n1["id"] == 1
        assert n2["id"] == 2
        assert n3["id"] == 3

    # ----------------------------------------------------------
    # _notification_to_dict staticmethod
    # ----------------------------------------------------------

    def test_notification_to_dict_returns_none_for_none_input(self):
        """None を渡すと None を返す"""
        from dal.notifications import NotificationMixin
        result = NotificationMixin._notification_to_dict(None)
        assert result is None


# ============================================================
# OperationsMixin 追加テスト (dal/operations.py)
# ============================================================


class TestOperationsMixinExtra:
    """OperationsMixin の境界値・異常系・静的メソッドを補強するテスト"""

    # ----------------------------------------------------------
    # get_sop_list - 境界値・複合フィルタ
    # ----------------------------------------------------------

    def test_get_sop_list_missing_file_returns_empty(self, tmp_path):
        """sop.json が存在しない場合は空リストを返す"""
        dal = make_dal(tmp_path)
        result = dal.get_sop_list()
        assert result == []

    def test_get_sop_list_no_filters_returns_all(self, tmp_path):
        """フィルタなしで全SOPが返される"""
        sops = [
            {"id": 1, "title": "SOP-A", "category": "safety", "status": "active"},
            {"id": 2, "title": "SOP-B", "category": "quality", "status": "draft"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list()
        assert len(result) == 2

    def test_get_sop_list_filter_by_category(self, tmp_path):
        """category フィルタが正しく動作する"""
        sops = [
            {"id": 1, "title": "SOP-A", "category": "safety"},
            {"id": 2, "title": "SOP-B", "category": "quality"},
            {"id": 3, "title": "SOP-C", "category": "safety"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"category": "safety"})
        assert len(result) == 2
        for s in result:
            assert s["category"] == "safety"

    def test_get_sop_list_filter_by_status(self, tmp_path):
        """status フィルタが正しく動作する"""
        sops = [
            {"id": 1, "title": "SOP-A", "status": "active"},
            {"id": 2, "title": "SOP-B", "status": "draft"},
            {"id": 3, "title": "SOP-C", "status": "active"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"status": "active"})
        assert len(result) == 2

    def test_get_sop_list_filter_by_search_title(self, tmp_path):
        """search フィルタがタイトルを大文字小文字無視で検索する"""
        sops = [
            {"id": 1, "title": "足場組立手順", "content": "詳細内容A"},
            {"id": 2, "title": "溶接作業手順", "content": "詳細内容B"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"search": "足場"})
        assert len(result) == 1
        assert result[0]["title"] == "足場組立手順"

    def test_get_sop_list_filter_by_search_content(self, tmp_path):
        """search フィルタがコンテンツも検索する"""
        sops = [
            {"id": 1, "title": "SOP-A", "content": "高所作業の注意事項"},
            {"id": 2, "title": "SOP-B", "content": "溶接の注意事項"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"search": "高所"})
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_get_sop_list_filter_no_match(self, tmp_path):
        """フィルタ条件に一致するものがない場合は空リスト"""
        sops = [
            {"id": 1, "title": "SOP-A", "category": "safety"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters={"category": "nonexistent"})
        assert result == []

    def test_get_sop_list_filters_is_none(self, tmp_path):
        """filters=None の場合は全件返す"""
        sops = [{"id": 1, "title": "SOP-A"}, {"id": 2, "title": "SOP-B"}]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_list(filters=None)
        assert len(result) == 2

    def test_get_sop_list_empty_file(self, tmp_path):
        """空のJSONリストから呼び出すと空リストを返す"""
        write_json(tmp_path, "sop.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_sop_list()
        assert result == []

    # ----------------------------------------------------------
    # get_sop_by_id - 境界値
    # ----------------------------------------------------------

    def test_get_sop_by_id_found(self, tmp_path):
        """存在するIDでSOPを取得できる"""
        sops = [
            {"id": 1, "title": "SOP-A"},
            {"id": 2, "title": "SOP-B"},
        ]
        write_json(tmp_path, "sop.json", sops)
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(1)
        assert result is not None
        assert result["title"] == "SOP-A"

    def test_get_sop_by_id_not_found(self, tmp_path):
        """存在しないIDは None を返す"""
        write_json(tmp_path, "sop.json", [{"id": 1, "title": "SOP-A"}])
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(9999)
        assert result is None

    def test_get_sop_by_id_missing_file(self, tmp_path):
        """sop.json が存在しない場合は None を返す"""
        dal = make_dal(tmp_path)
        result = dal.get_sop_by_id(1)
        assert result is None

    # ----------------------------------------------------------
    # get_incidents_list - フィルタリング・ソート
    # ----------------------------------------------------------

    def _make_incidents(self, tmp_path):
        incidents = [
            {
                "id": 1,
                "title": "墜落事故",
                "description": "高所からの墜落",
                "project": "PROJ-001",
                "incident_date": "2024-03-10",
                "severity": "high",
                "status": "open",
            },
            {
                "id": 2,
                "title": "ヒヤリハット",
                "description": "転倒しかけた",
                "project": "PROJ-002",
                "incident_date": "2024-02-01",
                "severity": "low",
                "status": "closed",
            },
            {
                "id": 3,
                "title": "機器故障",
                "description": "クレーン異音",
                "project": "PROJ-001",
                "incident_date": "2024-01-15",
                "severity": "medium",
                "status": "in_progress",
            },
        ]
        write_json(tmp_path, "incidents.json", incidents)
        return make_dal(tmp_path)

    def test_get_incidents_list_no_filters(self, tmp_path):
        """フィルタなしで全インシデントが返される"""
        dal = self._make_incidents(tmp_path)
        result = dal.get_incidents_list()
        assert len(result) == 3

    def test_get_incidents_list_sorted_by_incident_date_desc(self, tmp_path):
        """incident_date の降順でソートされる"""
        dal = self._make_incidents(tmp_path)
        result = dal.get_incidents_list()
        dates = [r["incident_date"] for r in result]
        assert dates == sorted(dates, reverse=True)

    def test_get_incidents_list_filter_by_project(self, tmp_path):
        """project フィルタが正しく動作する"""
        dal = self._make_incidents(tmp_path)
        result = dal.get_incidents_list(filters={"project": "PROJ-001"})
        assert len(result) == 2
        for i in result:
            assert i["project"] == "PROJ-001"

    def test_get_incidents_list_filter_by_severity(self, tmp_path):
        """severity フィルタが正しく動作する"""
        dal = self._make_incidents(tmp_path)
        result = dal.get_incidents_list(filters={"severity": "high"})
        assert len(result) == 1
        assert result[0]["severity"] == "high"

    def test_get_incidents_list_filter_by_status(self, tmp_path):
        """status フィルタが正しく動作する"""
        dal = self._make_incidents(tmp_path)
        result = dal.get_incidents_list(filters={"status": "closed"})
        assert len(result) == 1
        assert result[0]["status"] == "closed"

    def test_get_incidents_list_filter_by_search_title(self, tmp_path):
        """search フィルタがタイトルを検索する"""
        dal = self._make_incidents(tmp_path)
        result = dal.get_incidents_list(filters={"search": "墜落"})
        assert len(result) == 1
        assert result[0]["title"] == "墜落事故"

    def test_get_incidents_list_filter_by_search_description(self, tmp_path):
        """search フィルタが description も検索する"""
        dal = self._make_incidents(tmp_path)
        result = dal.get_incidents_list(filters={"search": "クレーン"})
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_get_incidents_list_empty_file(self, tmp_path):
        """空のJSONリストから呼び出すと空リストを返す"""
        write_json(tmp_path, "incidents.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list()
        assert result == []

    def test_get_incidents_list_missing_file(self, tmp_path):
        """incidents.json が存在しない場合は空リストを返す"""
        dal = make_dal(tmp_path)
        result = dal.get_incidents_list()
        assert result == []

    # ----------------------------------------------------------
    # get_incident_by_id - 境界値
    # ----------------------------------------------------------

    def test_get_incident_by_id_found(self, tmp_path):
        """存在するIDでインシデントを取得できる"""
        incidents = [{"id": 1, "title": "事故A"}, {"id": 2, "title": "事故B"}]
        write_json(tmp_path, "incidents.json", incidents)
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(2)
        assert result is not None
        assert result["title"] == "事故B"

    def test_get_incident_by_id_not_found(self, tmp_path):
        """存在しないIDは None を返す"""
        write_json(tmp_path, "incidents.json", [{"id": 1, "title": "事故A"}])
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(9999)
        assert result is None

    def test_get_incident_by_id_missing_file(self, tmp_path):
        """incidents.json が存在しない場合は None を返す"""
        dal = make_dal(tmp_path)
        result = dal.get_incident_by_id(1)
        assert result is None

    # ----------------------------------------------------------
    # get_approvals_list - フィルタリング
    # ----------------------------------------------------------

    def _make_approvals(self, tmp_path):
        approvals = [
            {
                "id": 1,
                "title": "設計変更申請",
                "type": "design_change",
                "status": "pending",
                "requester_id": 1,
                "priority": "high",
                "created_at": "2024-03-10",
            },
            {
                "id": 2,
                "title": "材料承認申請",
                "type": "material",
                "status": "approved",
                "requester_id": 2,
                "priority": "medium",
                "created_at": "2024-02-01",
            },
            {
                "id": 3,
                "title": "工程変更申請",
                "type": "schedule",
                "status": "rejected",
                "requester_id": 1,
                "priority": "low",
                "created_at": "2024-01-15",
            },
        ]
        write_json(tmp_path, "approvals.json", approvals)
        return make_dal(tmp_path)

    def test_get_approvals_list_no_filters(self, tmp_path):
        """フィルタなしで全承認案件が返される"""
        dal = self._make_approvals(tmp_path)
        result = dal.get_approvals_list()
        assert len(result) == 3

    def test_get_approvals_list_sorted_by_created_at_desc(self, tmp_path):
        """created_at の降順でソートされる"""
        dal = self._make_approvals(tmp_path)
        result = dal.get_approvals_list()
        dates = [r["created_at"] for r in result]
        assert dates == sorted(dates, reverse=True)

    def test_get_approvals_list_filter_by_status(self, tmp_path):
        """status フィルタが正しく動作する"""
        dal = self._make_approvals(tmp_path)
        result = dal.get_approvals_list(filters={"status": "pending"})
        assert len(result) == 1
        assert result[0]["status"] == "pending"

    def test_get_approvals_list_filter_by_type(self, tmp_path):
        """type フィルタが正しく動作する"""
        dal = self._make_approvals(tmp_path)
        result = dal.get_approvals_list(filters={"type": "material"})
        assert len(result) == 1
        assert result[0]["type"] == "material"

    def test_get_approvals_list_filter_by_requester_id(self, tmp_path):
        """requester_id フィルタが正しく動作する"""
        dal = self._make_approvals(tmp_path)
        result = dal.get_approvals_list(filters={"requester_id": 1})
        assert len(result) == 2
        for a in result:
            assert a["requester_id"] == 1

    def test_get_approvals_list_filter_by_priority(self, tmp_path):
        """priority フィルタが正しく動作する"""
        dal = self._make_approvals(tmp_path)
        result = dal.get_approvals_list(filters={"priority": "high"})
        assert len(result) == 1
        assert result[0]["priority"] == "high"

    def test_get_approvals_list_empty_file(self, tmp_path):
        """空のJSONリストから呼び出すと空リストを返す"""
        write_json(tmp_path, "approvals.json", [])
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list()
        assert result == []

    def test_get_approvals_list_missing_file(self, tmp_path):
        """approvals.json が存在しない場合は空リストを返す"""
        dal = make_dal(tmp_path)
        result = dal.get_approvals_list()
        assert result == []

    def test_get_approvals_list_combined_filters(self, tmp_path):
        """複数フィルタの組み合わせが正しく動作する"""
        dal = self._make_approvals(tmp_path)
        result = dal.get_approvals_list(filters={"status": "pending", "requester_id": 1})
        assert len(result) == 1
        assert result[0]["title"] == "設計変更申請"

    # ----------------------------------------------------------
    # get_regulation_by_id - 境界値
    # ----------------------------------------------------------

    def test_get_regulation_by_id_found(self, tmp_path):
        """存在するIDで法令を取得できる"""
        regulations = [
            {"id": 1, "title": "建設業法"},
            {"id": 2, "title": "労働安全衛生法"},
        ]
        write_json(tmp_path, "regulations.json", regulations)
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(2)
        assert result is not None
        assert result["title"] == "労働安全衛生法"

    def test_get_regulation_by_id_not_found(self, tmp_path):
        """存在しないIDは None を返す"""
        write_json(tmp_path, "regulations.json", [{"id": 1, "title": "建設業法"}])
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(9999)
        assert result is None

    def test_get_regulation_by_id_missing_file(self, tmp_path):
        """regulations.json が存在しない場合は None を返す"""
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(1)
        assert result is None

    def test_get_regulation_by_id_first_entry(self, tmp_path):
        """先頭エントリを ID で取得できる"""
        regulations = [
            {"id": 10, "title": "消防法"},
            {"id": 20, "title": "建築基準法"},
        ]
        write_json(tmp_path, "regulations.json", regulations)
        dal = make_dal(tmp_path)
        result = dal.get_regulation_by_id(10)
        assert result["title"] == "消防法"

    # ----------------------------------------------------------
    # _sop_to_dict, _incident_to_dict, _approval_to_dict, _regulation_to_dict staticmethod
    # ----------------------------------------------------------

    def test_sop_to_dict_returns_none_for_none_input(self):
        """None を渡すと None を返す"""
        from dal.operations import OperationsMixin
        result = OperationsMixin._sop_to_dict(None)
        assert result is None

    def test_incident_to_dict_returns_none_for_none_input(self):
        """None を渡すと None を返す"""
        from dal.operations import OperationsMixin
        result = OperationsMixin._incident_to_dict(None)
        assert result is None

    def test_approval_to_dict_returns_none_for_none_input(self):
        """None を渡すと None を返す"""
        from dal.operations import OperationsMixin
        result = OperationsMixin._approval_to_dict(None)
        assert result is None

    def test_regulation_to_dict_returns_none_for_none_input(self):
        """None を渡すと None を返す"""
        from dal.operations import OperationsMixin
        result = OperationsMixin._regulation_to_dict(None)
        assert result is None
