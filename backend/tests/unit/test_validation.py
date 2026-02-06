"""
スキーマ検証のユニットテスト
Marshmallowスキーマのバリデーション機能をテスト
"""

import os
import sys

import pytest

# backend ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from marshmallow import ValidationError
from schemas import IncidentCreateSchema, KnowledgeCreateSchema, KnowledgeUpdateSchema, LoginSchema


class TestLoginSchema:
    """LoginSchemaのテスト"""

    def test_valid_login_data(self):
        """有効なログインデータ"""
        schema = LoginSchema()
        data = {"username": "admin", "password": "password123"}

        result = schema.load(data)

        assert result["username"] == "admin"
        assert result["password"] == "password123"

    def test_username_is_required(self):
        """ユーザー名は必須"""
        schema = LoginSchema()
        data = {"password": "password123"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "username" in exc.value.messages

    def test_password_is_required(self):
        """パスワードは必須"""
        schema = LoginSchema()
        data = {"username": "admin"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "password" in exc.value.messages

    def test_username_min_length(self):
        """ユーザー名の最小長は3文字"""
        schema = LoginSchema()
        data = {"username": "ab", "password": "password123"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "username" in exc.value.messages

    def test_username_max_length(self):
        """ユーザー名の最大長は50文字"""
        schema = LoginSchema()
        data = {"username": "a" * 51, "password": "password123"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "username" in exc.value.messages

    def test_password_min_length(self):
        """パスワードの最小長は6文字"""
        schema = LoginSchema()
        data = {"username": "admin", "password": "12345"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "password" in exc.value.messages

    def test_password_max_length(self):
        """パスワードの最大長は100文字"""
        schema = LoginSchema()
        data = {"username": "admin", "password": "a" * 101}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "password" in exc.value.messages

    def test_valid_boundary_username(self):
        """ユーザー名の境界値テスト（3文字、50文字）"""
        schema = LoginSchema()

        # 最小長
        data_min = {"username": "abc", "password": "password123"}
        result_min = schema.load(data_min)
        assert result_min["username"] == "abc"

        # 最大長
        data_max = {"username": "a" * 50, "password": "password123"}
        result_max = schema.load(data_max)
        assert result_max["username"] == "a" * 50


class TestKnowledgeCreateSchema:
    """KnowledgeCreateSchemaのテスト"""

    def test_valid_knowledge_data(self):
        """有効なナレッジデータ"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テスト施工計画",
            "summary": "テスト概要説明",
            "content": "テストコンテンツの詳細",
            "category": "施工計画",
        }

        result = schema.load(data)

        assert result["title"] == "テスト施工計画"
        assert result["category"] == "施工計画"
        assert result["tags"] == []  # デフォルト値
        assert result["priority"] == "medium"  # デフォルト値

    def test_title_is_required(self):
        """タイトルは必須"""
        schema = KnowledgeCreateSchema()
        data = {
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "施工計画",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "title" in exc.value.messages

    def test_summary_is_required(self):
        """概要は必須"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "content": "テストコンテンツ",
            "category": "施工計画",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "summary" in exc.value.messages

    def test_content_is_required(self):
        """内容は必須"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "category": "施工計画",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "content" in exc.value.messages

    def test_category_is_required(self):
        """カテゴリは必須"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "テストコンテンツ",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "category" in exc.value.messages

    def test_category_must_be_valid_value(self):
        """カテゴリは有効な値のみ"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "無効なカテゴリ",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "category" in exc.value.messages

    def test_valid_categories(self):
        """有効なカテゴリ一覧をテスト"""
        schema = KnowledgeCreateSchema()
        valid_categories = [
            "施工計画",
            "品質管理",
            "安全衛生",
            "環境対策",
            "原価管理",
            "出来形管理",
            "その他",
        ]

        for category in valid_categories:
            data = {
                "title": "テストタイトル",
                "summary": "テスト概要",
                "content": "テストコンテンツ",
                "category": category,
            }
            result = schema.load(data)
            assert result["category"] == category

    def test_title_max_length(self):
        """タイトルの最大長は200文字"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "a" * 201,
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "施工計画",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "title" in exc.value.messages

    def test_summary_max_length(self):
        """概要の最大長は500文字"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "a" * 501,
            "content": "テストコンテンツ",
            "category": "施工計画",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "summary" in exc.value.messages

    def test_content_max_length(self):
        """内容の最大長は50000文字"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "a" * 50001,
            "category": "施工計画",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "content" in exc.value.messages

    def test_tags_default_empty_list(self):
        """tagsはデフォルトで空リスト"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "施工計画",
        }

        result = schema.load(data)
        assert result["tags"] == []

    def test_tags_max_count(self):
        """タグの最大数は20個"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "施工計画",
            "tags": [f"tag{i}" for i in range(21)],
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "tags" in exc.value.messages

    def test_individual_tag_max_length(self):
        """各タグの最大長は30文字"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "施工計画",
            "tags": ["a" * 31],
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "tags" in exc.value.messages

    def test_priority_valid_values(self):
        """priorityは有効な値のみ（low, medium, high）"""
        schema = KnowledgeCreateSchema()

        for priority in ["low", "medium", "high"]:
            data = {
                "title": "テストタイトル",
                "summary": "テスト概要",
                "content": "テストコンテンツ",
                "category": "施工計画",
                "priority": priority,
            }
            result = schema.load(data)
            assert result["priority"] == priority

    def test_priority_invalid_value(self):
        """priorityの無効な値"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "施工計画",
            "priority": "critical",  # 無効
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "priority" in exc.value.messages

    def test_owner_default_value(self):
        """ownerのデフォルト値は'unknown'"""
        schema = KnowledgeCreateSchema()
        data = {
            "title": "テストタイトル",
            "summary": "テスト概要",
            "content": "テストコンテンツ",
            "category": "施工計画",
        }

        result = schema.load(data)
        assert result["owner"] == "unknown"


class TestKnowledgeUpdateSchema:
    """KnowledgeUpdateSchemaのテスト"""

    def test_partial_update_allowed(self):
        """部分更新が許可される"""
        schema = KnowledgeUpdateSchema()

        # タイトルのみ更新
        data = {"title": "新しいタイトル"}
        result = schema.load(data)
        assert result["title"] == "新しいタイトル"

    def test_all_fields_optional(self):
        """全フィールドがオプショナル"""
        schema = KnowledgeUpdateSchema()

        # 空データでもエラーにならない
        data = {}
        result = schema.load(data)
        assert result == {}

    def test_status_valid_values(self):
        """statusは有効な値のみ"""
        schema = KnowledgeUpdateSchema()

        for status in ["draft", "pending", "approved", "archived"]:
            data = {"status": status}
            result = schema.load(data)
            assert result["status"] == status

    def test_status_invalid_value(self):
        """statusの無効な値"""
        schema = KnowledgeUpdateSchema()
        data = {"status": "invalid_status"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "status" in exc.value.messages


class TestIncidentCreateSchema:
    """IncidentCreateSchemaのテスト"""

    def test_valid_incident_data(self):
        """有効な事故レポートデータ"""
        schema = IncidentCreateSchema()
        data = {
            "title": "事故レポートタイトル",
            "description": "事故の詳細説明",
            "project": "プロジェクトA",
            "date": "2025-01-15T10:30:00",
        }

        result = schema.load(data)

        assert result["title"] == "事故レポートタイトル"
        assert result["severity"] == "medium"  # デフォルト値

    def test_title_is_required(self):
        """タイトルは必須"""
        schema = IncidentCreateSchema()
        data = {
            "description": "事故の詳細説明",
            "project": "プロジェクトA",
            "date": "2025-01-15T10:30:00",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "title" in exc.value.messages

    def test_description_is_required(self):
        """説明は必須"""
        schema = IncidentCreateSchema()
        data = {
            "title": "事故レポート",
            "project": "プロジェクトA",
            "date": "2025-01-15T10:30:00",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "description" in exc.value.messages

    def test_project_is_required(self):
        """プロジェクトは必須"""
        schema = IncidentCreateSchema()
        data = {
            "title": "事故レポート",
            "description": "事故の詳細説明",
            "date": "2025-01-15T10:30:00",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "project" in exc.value.messages

    def test_date_is_required(self):
        """日付は必須"""
        schema = IncidentCreateSchema()
        data = {
            "title": "事故レポート",
            "description": "事故の詳細説明",
            "project": "プロジェクトA",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "date" in exc.value.messages

    def test_severity_valid_values(self):
        """severityは有効な値のみ（low, medium, high, critical）"""
        schema = IncidentCreateSchema()

        for severity in ["low", "medium", "high", "critical"]:
            data = {
                "title": "事故レポート",
                "description": "事故の詳細説明",
                "project": "プロジェクトA",
                "date": "2025-01-15T10:30:00",
                "severity": severity,
            }
            result = schema.load(data)
            assert result["severity"] == severity

    def test_severity_invalid_value(self):
        """severityの無効な値"""
        schema = IncidentCreateSchema()
        data = {
            "title": "事故レポート",
            "description": "事故の詳細説明",
            "project": "プロジェクトA",
            "date": "2025-01-15T10:30:00",
            "severity": "emergency",  # 無効
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "severity" in exc.value.messages

    def test_corrective_actions_default_empty_list(self):
        """corrective_actionsはデフォルトで空リスト"""
        schema = IncidentCreateSchema()
        data = {
            "title": "事故レポート",
            "description": "事故の詳細説明",
            "project": "プロジェクトA",
            "date": "2025-01-15T10:30:00",
        }

        result = schema.load(data)
        assert result["corrective_actions"] == []

    def test_title_max_length(self):
        """タイトルの最大長は200文字"""
        schema = IncidentCreateSchema()
        data = {
            "title": "a" * 201,
            "description": "事故の詳細説明",
            "project": "プロジェクトA",
            "date": "2025-01-15T10:30:00",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "title" in exc.value.messages

    def test_description_max_length(self):
        """説明の最大長は5000文字"""
        schema = IncidentCreateSchema()
        data = {
            "title": "事故レポート",
            "description": "a" * 5001,
            "project": "プロジェクトA",
            "date": "2025-01-15T10:30:00",
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "description" in exc.value.messages
