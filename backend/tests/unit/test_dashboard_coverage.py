"""
blueprints/dashboard.py カバレッジ強化テスト

対象エンドポイント:
  GET /api/v1/sop                  - SOP一覧取得
  GET /api/v1/sop/<id>             - SOP詳細取得
  GET /api/v1/sop/<id>/related     - 関連SOP取得
  GET /api/v1/dashboard/stats      - ダッシュボード統計
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


_SOP_DATA = [
    {
        "id": 1,
        "title": "高所作業SOP",
        "summary": "高所作業の標準手順",
        "content": "1. 安全帯を確認する 2. 足場を点検する",
        "category": "安全",
        "tags": ["高所", "安全帯", "足場"],
    },
    {
        "id": 2,
        "title": "掘削作業SOP",
        "summary": "掘削作業の標準手順",
        "content": "1. 地盤調査 2. 掘削計画の策定",
        "category": "工事",
        "tags": ["掘削", "地盤", "工事"],
    },
    {
        "id": 3,
        "title": "重機操作SOP",
        "summary": "重機操作の標準手順",
        "content": "1. 点検 2. 操作",
        "category": "安全",
        "tags": ["重機", "操作"],
    },
]


@pytest.fixture()
def sop_client(client, tmp_path):
    """SOP・ダッシュボード関連データを準備したクライアント"""
    _write_json(tmp_path / "sop.json", _SOP_DATA)
    _write_json(tmp_path / "incidents.json", [
        {"id": 1, "title": "軽微な転倒", "status": "reported"},
    ])
    _write_json(tmp_path / "approvals.json", [
        {"id": 1, "title": "設計変更申請", "status": "pending"},
        {"id": 2, "title": "資材発注申請", "status": "approved"},
    ])
    return client


# ================================================================
# SOP 一覧取得
# ================================================================

class TestGetSOP:
    """GET /api/v1/sop"""

    def test_returns_200_with_data(self, sop_client, auth_headers):
        """SOP一覧を取得できる"""
        resp = sop_client.get("/api/v1/sop", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 3

    def test_has_pagination(self, sop_client, auth_headers):
        """ページネーション情報が含まれる"""
        resp = sop_client.get("/api/v1/sop", headers=auth_headers)
        assert resp.status_code == 200
        pag = resp.get_json()["pagination"]
        assert "total_items" in pag
        assert pag["total_items"] == 3

    def test_no_token_returns_401(self, sop_client):
        """トークンなしは 401"""
        resp = sop_client.get("/api/v1/sop")
        assert resp.status_code == 401

    def test_empty_sop_list(self, client, auth_headers):
        """SOP が空でも成功する（conftest は空リスト）"""
        resp = client.get("/api/v1/sop", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["pagination"]["total_items"] == 0

    def test_partner_can_read_sop(self, sop_client, partner_auth_headers):
        """協力会社ユーザーも SOP を読める"""
        resp = sop_client.get("/api/v1/sop", headers=partner_auth_headers)
        assert resp.status_code == 200


# ================================================================
# SOP 詳細取得
# ================================================================

class TestGetSOPDetail:
    """GET /api/v1/sop/<id>"""

    def test_returns_correct_sop(self, sop_client, auth_headers):
        """指定 ID の SOP 詳細が返る"""
        resp = sop_client.get("/api/v1/sop/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == 1
        assert data["data"]["title"] == "高所作業SOP"

    def test_not_found_returns_404(self, sop_client, auth_headers):
        """存在しない ID は 404"""
        resp = sop_client.get("/api/v1/sop/999", headers=auth_headers)
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_second_sop(self, sop_client, auth_headers):
        """2番目の SOP も取得できる"""
        resp = sop_client.get("/api/v1/sop/2", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["id"] == 2

    def test_no_token_returns_401(self, sop_client):
        """トークンなしは 401"""
        resp = sop_client.get("/api/v1/sop/1")
        assert resp.status_code == 401


# ================================================================
# 関連 SOP 取得
# ================================================================

class TestGetRelatedSOP:
    """GET /api/v1/sop/<id>/related"""

    def test_returns_200(self, sop_client, auth_headers):
        """関連SOPが取得できる"""
        resp = sop_client.get("/api/v1/sop/1/related", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "related_items" in data["data"]
        assert "algorithm" in data["data"]
        assert "count" in data["data"]
        assert data["data"]["target_id"] == 1

    def test_default_algorithm_is_hybrid(self, sop_client, auth_headers):
        """デフォルトアルゴリズムは hybrid"""
        resp = sop_client.get("/api/v1/sop/1/related", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["algorithm"] == "hybrid"

    def test_tag_algorithm(self, sop_client, auth_headers):
        """tag アルゴリズムが有効"""
        resp = sop_client.get(
            "/api/v1/sop/1/related?algorithm=tag", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["algorithm"] == "tag"

    def test_category_algorithm(self, sop_client, auth_headers):
        """category アルゴリズムが有効"""
        resp = sop_client.get(
            "/api/v1/sop/1/related?algorithm=category", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_keyword_algorithm(self, sop_client, auth_headers):
        """keyword アルゴリズムが有効"""
        resp = sop_client.get(
            "/api/v1/sop/1/related?algorithm=keyword", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_limit_applied(self, sop_client, auth_headers):
        """limit パラメータが count に反映される"""
        resp = sop_client.get(
            "/api/v1/sop/1/related?limit=2", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["count"] <= 2

    def test_invalid_limit_zero(self, sop_client, auth_headers):
        """limit=0 は 400"""
        resp = sop_client.get(
            "/api/v1/sop/1/related?limit=0", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_LIMIT"

    def test_invalid_limit_too_large(self, sop_client, auth_headers):
        """limit=21 は 400"""
        resp = sop_client.get(
            "/api/v1/sop/1/related?limit=21", headers=auth_headers
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_LIMIT"

    def test_invalid_algorithm(self, sop_client, auth_headers):
        """無効なアルゴリズムは 400"""
        resp = sop_client.get(
            "/api/v1/sop/1/related?algorithm=magic", headers=auth_headers
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_ALGORITHM"

    def test_not_found_sop(self, sop_client, auth_headers):
        """存在しない SOP ID は 404"""
        resp = sop_client.get(
            "/api/v1/sop/999/related", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_no_token_returns_401(self, sop_client):
        """トークンなしは 401"""
        resp = sop_client.get("/api/v1/sop/1/related")
        assert resp.status_code == 401


# ================================================================
# ダッシュボード統計
# ================================================================

class TestGetDashboardStats:
    """GET /api/v1/dashboard/stats"""

    def test_returns_200(self, sop_client, auth_headers):
        """統計情報が取得できる"""
        resp = sop_client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data

    def test_has_kpis(self, sop_client, auth_headers):
        """KPI 情報が含まれる"""
        resp = sop_client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        kpis = resp.get_json()["data"]["kpis"]
        assert "knowledge_reuse_rate" in kpis
        assert "accident_free_days" in kpis
        assert "active_audits" in kpis
        assert "delayed_corrections" in kpis

    def test_has_counts(self, sop_client, auth_headers):
        """カウント情報が含まれる"""
        resp = sop_client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        counts = resp.get_json()["data"]["counts"]
        assert "total_knowledge" in counts
        assert "total_sop" in counts
        assert "recent_incidents" in counts
        assert "pending_approvals" in counts

    def test_sop_count_matches_data(self, sop_client, auth_headers):
        """total_sop がデータ件数と一致する"""
        resp = sop_client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["counts"]["total_sop"] == 3

    def test_pending_approvals_count(self, sop_client, auth_headers):
        """pending 承認数が正しい（1件）"""
        resp = sop_client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        stats = resp.get_json()["data"]
        assert stats["counts"]["pending_approvals"] == 1
        assert stats["pending_approvals"] == 1

    def test_has_last_sync_time(self, sop_client, auth_headers):
        """last_sync_time が含まれる"""
        resp = sop_client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        assert "last_sync_time" in resp.get_json()["data"]

    def test_no_token_returns_401(self, sop_client):
        """トークンなしは 401"""
        resp = sop_client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 401

    def test_partner_can_view_dashboard(self, sop_client, partner_auth_headers):
        """協力会社ユーザーもダッシュボード統計を見られる"""
        resp = sop_client.get("/api/v1/dashboard/stats", headers=partner_auth_headers)
        assert resp.status_code == 200
