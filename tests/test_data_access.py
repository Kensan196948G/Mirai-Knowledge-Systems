import pytest
from faker import Faker

from backend.data_access import DataAccessLayer

fake = Faker()


@pytest.fixture
def dal():
    """DataAccessLayerインスタンス（JSONモード）"""
    return DataAccessLayer(use_postgresql=False)


def test_create_knowledge(dal):
    """ナレッジ作成テスト"""
    knowledge_data = {
        "title": fake.sentence(),
        "summary": fake.sentence(),
        "content": fake.text(),
        "category": "施工計画",
        "owner": fake.name(),
    }

    result = dal.create_knowledge(knowledge_data)

    assert result is not None
    assert result["title"] == knowledge_data["title"]
    assert result["category"] == knowledge_data["category"]
    assert "id" in result
    assert "created_at" in result


def test_get_knowledge_list(dal):
    """ナレッジ一覧取得テスト"""
    # テストデータを事前に作成
    knowledge_data = {
        "title": fake.sentence(),
        "summary": fake.sentence(),
        "content": fake.text(),
        "category": "施工計画",
        "owner": fake.name(),
    }
    dal.create_knowledge(knowledge_data)

    result = dal.get_knowledge_list()

    assert isinstance(result, list)
    assert len(result) > 0
    assert "title" in result[0]
    assert "category" in result[0]


def test_get_knowledge_by_id(dal):
    """ナレッジID取得テスト"""
    knowledge_data = {
        "title": fake.sentence(),
        "summary": fake.sentence(),
        "content": fake.text(),
        "category": "施工計画",
        "owner": fake.name(),
    }
    created = dal.create_knowledge(knowledge_data)

    result = dal.get_knowledge_by_id(created["id"])

    assert result is not None
    assert result["id"] == created["id"]
    assert result["title"] == knowledge_data["title"]


def test_get_knowledge_by_id_not_found(dal):
    """存在しないナレッジ取得テスト"""
    result = dal.get_knowledge_by_id(999999)

    assert result is None


def test_update_knowledge(dal):
    """ナレッジ更新テスト"""
    knowledge_data = {
        "title": fake.sentence(),
        "summary": fake.sentence(),
        "content": fake.text(),
        "category": "施工計画",
        "owner": fake.name(),
    }
    created = dal.create_knowledge(knowledge_data)

    update_data = {"title": "Updated Title"}
    result = dal.update_knowledge(created["id"], update_data)

    assert result is not None
    assert result["title"] == "Updated Title"
    assert result["id"] == created["id"]


def test_update_knowledge_not_found(dal):
    """存在しないナレッジ更新テスト"""
    update_data = {"title": "Updated Title"}
    result = dal.update_knowledge(999999, update_data)

    assert result is None


def test_delete_knowledge(dal):
    """ナレッジ削除テスト"""
    knowledge_data = {
        "title": fake.sentence(),
        "summary": fake.sentence(),
        "content": fake.text(),
        "category": "施工計画",
        "owner": fake.name(),
    }
    created = dal.create_knowledge(knowledge_data)

    result = dal.delete_knowledge(created["id"])

    assert result is True

    # 削除確認
    deleted = dal.get_knowledge_by_id(created["id"])
    assert deleted is None


def test_delete_knowledge_not_found(dal):
    """存在しないナレッジ削除テスト"""
    result = dal.delete_knowledge(999999)

    assert result is False


def test_get_knowledge_list_with_filters(dal):
    """フィルタ付きナレッジ一覧取得テスト"""
    # テストデータを複数作成
    knowledge1 = {
        "title": fake.sentence(),
        "summary": fake.sentence(),
        "content": fake.text(),
        "category": "施工計画",
        "owner": fake.name(),
    }
    knowledge2 = {
        "title": fake.sentence(),
        "summary": fake.sentence(),
        "content": fake.text(),
        "category": "品質",
        "owner": fake.name(),
    }
    dal.create_knowledge(knowledge1)
    dal.create_knowledge(knowledge2)

    # カテゴリフィルタ
    result = dal.get_knowledge_list(filters={"category": "施工計画"})

    assert len(result) >= 1
    for item in result:
        assert item["category"] == "施工計画"
