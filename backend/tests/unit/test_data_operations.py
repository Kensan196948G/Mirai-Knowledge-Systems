"""
データ操作関数（load_data, save_data）のユニットテスト
"""
import pytest
import json
import os
import sys

# backend ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestLoadData:
    """load_data関数のテスト"""

    def test_load_data_returns_empty_list_when_file_not_exists(self, tmp_path, monkeypatch):
        """ファイルが存在しない場合は空リストを返す"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        result = app_v2.load_data('nonexistent.json')
        assert result == []

    def test_load_data_reads_existing_file(self, tmp_path, monkeypatch):
        """既存ファイルを正しく読み込む"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        # テストデータファイル作成
        test_data = [{'id': 1, 'name': 'Test'}]
        data_file = tmp_path / 'test.json'
        data_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding='utf-8')

        result = app_v2.load_data('test.json')
        assert result == test_data

    def test_load_data_handles_utf8_content(self, tmp_path, monkeypatch):
        """UTF-8エンコードされた日本語を正しく読み込む"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        test_data = [{'id': 1, 'title': '施工計画書', 'category': '安全衛生'}]
        data_file = tmp_path / 'japanese.json'
        data_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding='utf-8')

        result = app_v2.load_data('japanese.json')
        assert result[0]['title'] == '施工計画書'
        assert result[0]['category'] == '安全衛生'

    def test_load_data_handles_complex_nested_structure(self, tmp_path, monkeypatch):
        """複雑なネスト構造を正しく読み込む"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        test_data = [
            {
                'id': 1,
                'metadata': {
                    'tags': ['safety', 'construction'],
                    'author': {'name': 'Admin', 'role': 'admin'}
                },
                'items': [1, 2, 3]
            }
        ]
        data_file = tmp_path / 'nested.json'
        data_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding='utf-8')

        result = app_v2.load_data('nested.json')
        assert result[0]['metadata']['tags'] == ['safety', 'construction']
        assert result[0]['metadata']['author']['name'] == 'Admin'

    def test_load_data_returns_empty_list_on_invalid_json(self, tmp_path, monkeypatch):
        """不正なJSONは空リストとして扱う"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        data_file = tmp_path / 'broken.json'
        data_file.write_text('{"invalid":', encoding='utf-8')

        result = app_v2.load_data('broken.json')
        assert result == []

    def test_load_data_returns_empty_list_on_non_list_json(self, tmp_path, monkeypatch):
        """配列以外のJSONは空リストとして扱う"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        data_file = tmp_path / 'object.json'
        data_file.write_text(json.dumps({'id': 1}), encoding='utf-8')

        result = app_v2.load_data('object.json')
        assert result == []


class TestSaveData:
    """save_data関数のテスト"""

    def test_save_data_creates_file(self, tmp_path, monkeypatch):
        """ファイルが作成される"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        test_data = [{'id': 1, 'name': 'Test'}]
        app_v2.save_data('new_file.json', test_data)

        saved_file = tmp_path / 'new_file.json'
        assert saved_file.exists()

    def test_save_data_preserves_content(self, tmp_path, monkeypatch):
        """データが正しく保存される"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        test_data = [{'id': 1, 'name': 'Test'}, {'id': 2, 'name': 'Test2'}]
        app_v2.save_data('preserved.json', test_data)

        saved_file = tmp_path / 'preserved.json'
        with open(saved_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded == test_data

    def test_save_data_preserves_utf8_content(self, tmp_path, monkeypatch):
        """UTF-8日本語が正しく保存される"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        test_data = [{'id': 1, 'title': '品質管理マニュアル', 'summary': 'テスト概要'}]
        app_v2.save_data('japanese_save.json', test_data)

        saved_file = tmp_path / 'japanese_save.json'
        with open(saved_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded[0]['title'] == '品質管理マニュアル'
        assert loaded[0]['summary'] == 'テスト概要'

    def test_save_data_overwrites_existing_file(self, tmp_path, monkeypatch):
        """既存ファイルを上書きする"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        # 初期データ保存
        initial_data = [{'id': 1, 'name': 'Initial'}]
        app_v2.save_data('overwrite.json', initial_data)

        # 新しいデータで上書き
        new_data = [{'id': 2, 'name': 'Overwritten'}]
        app_v2.save_data('overwrite.json', new_data)

        saved_file = tmp_path / 'overwrite.json'
        with open(saved_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded == new_data
        assert loaded != initial_data

    def test_save_data_uses_proper_indentation(self, tmp_path, monkeypatch):
        """インデント付きで保存される（可読性のため）"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        test_data = [{'id': 1}]
        app_v2.save_data('indented.json', test_data)

        saved_file = tmp_path / 'indented.json'
        content = saved_file.read_text(encoding='utf-8')

        # インデントがあることを確認（改行と空白がある）
        assert '\n' in content
        assert '  ' in content or '    ' in content


class TestLoadAndSaveIntegration:
    """load_dataとsave_dataの統合テスト"""

    def test_save_then_load_preserves_data(self, tmp_path, monkeypatch):
        """保存したデータが読み込みで復元される"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        original_data = [
            {'id': 1, 'title': 'Test1', 'tags': ['a', 'b']},
            {'id': 2, 'title': 'Test2', 'tags': ['c']}
        ]

        app_v2.save_data('roundtrip.json', original_data)
        loaded_data = app_v2.load_data('roundtrip.json')

        assert loaded_data == original_data

    def test_multiple_save_load_cycles(self, tmp_path, monkeypatch):
        """複数回の保存・読み込みサイクル"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        data = []

        for i in range(5):
            data.append({'id': i, 'name': f'Item{i}'})
            app_v2.save_data('cycle.json', data)
            loaded = app_v2.load_data('cycle.json')
            assert len(loaded) == i + 1
            assert loaded[-1]['name'] == f'Item{i}'


class TestLoadUsers:
    """load_users関数のテスト"""

    def test_load_users_returns_empty_list_when_no_file(self, tmp_path, monkeypatch):
        """ファイルがない場合は空リストを返す"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        result = app_v2.load_users()
        assert result == []

    def test_load_users_reads_users_file(self, tmp_path, monkeypatch):
        """users.jsonを正しく読み込む"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        users = [
            {'id': 1, 'username': 'admin', 'roles': ['admin']},
            {'id': 2, 'username': 'user', 'roles': ['user']}
        ]
        users_file = tmp_path / 'users.json'
        users_file.write_text(json.dumps(users, ensure_ascii=False), encoding='utf-8')

        result = app_v2.load_users()
        assert len(result) == 2
        assert result[0]['username'] == 'admin'


class TestSaveUsers:
    """save_users関数のテスト"""

    def test_save_users_creates_users_file(self, tmp_path, monkeypatch):
        """users.jsonを作成する"""
        import app_v2

        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(tmp_path)})

        users = [{'id': 1, 'username': 'newuser', 'roles': ['user']}]
        app_v2.save_users(users)

        users_file = tmp_path / 'users.json'
        assert users_file.exists()

        with open(users_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == users


class TestGetDataDir:
    """get_data_dir関数のテスト"""

    def test_get_data_dir_creates_directory_if_not_exists(self, tmp_path, monkeypatch):
        """ディレクトリが存在しない場合は作成する"""
        import app_v2

        new_data_dir = tmp_path / 'new_data_dir'
        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(new_data_dir)})

        result = app_v2.get_data_dir()

        assert result == str(new_data_dir)
        assert new_data_dir.exists()
        assert new_data_dir.is_dir()

    def test_get_data_dir_returns_existing_directory(self, tmp_path, monkeypatch):
        """既存のディレクトリを返す"""
        import app_v2

        existing_dir = tmp_path / 'existing'
        existing_dir.mkdir()
        monkeypatch.setattr(app_v2.app, 'config', {'DATA_DIR': str(existing_dir)})

        result = app_v2.get_data_dir()

        assert result == str(existing_dir)
