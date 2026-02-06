"""
エラーハンドリング強化のテストスクリプト
"""

import json
import os
import sys
import tempfile

# テスト用のdata_dirを設定
TEST_DATA_DIR = tempfile.mkdtemp()
print(f"[TEST] Using temporary data directory: {TEST_DATA_DIR}")

# app_v2をインポート前に環境変数を設定
os.environ["MKS_DATA_DIR"] = TEST_DATA_DIR
os.environ["MKS_JWT_SECRET_KEY"] = "test-secret-key-for-error-handling-testing"

# パスを追加してapp_v2をインポート
sys.path.insert(0, os.path.dirname(__file__))

# 関数のみインポート（Flaskアプリは起動しない）
from app_v2 import get_data_dir, load_data, save_data


def test_load_data_file_not_found():
    """ファイルが存在しない場合のテスト"""
    print("\n[TEST 1] File not found")
    result = load_data("non_existent_file.json")
    assert result == [], f"Expected empty list, got {result}"
    print("[PASS] Returns empty list when file not found")


def test_load_data_json_decode_error():
    """JSONデコードエラーのテスト"""
    print("\n[TEST 2] JSON decode error")

    # 壊れたJSONファイルを作成
    filepath = os.path.join(get_data_dir(), "broken.json")
    with open(filepath, "w") as f:
        f.write("{ broken json content }")

    result = load_data("broken.json")
    assert result == [], f"Expected empty list, got {result}"
    print("[PASS] Returns empty list when JSON is invalid")

    # クリーンアップ
    os.remove(filepath)


def test_load_data_non_list_data():
    """リスト以外のデータ型のテスト"""
    print("\n[TEST 3] Non-list data type")

    # 辞書型のJSONファイルを作成
    filepath = os.path.join(get_data_dir(), "dict_data.json")
    with open(filepath, "w") as f:
        json.dump({"key": "value"}, f)

    result = load_data("dict_data.json")
    assert result == [], f"Expected empty list, got {result}"
    print("[PASS] Returns empty list when data is not a list")

    # クリーンアップ
    os.remove(filepath)


def test_save_data_success():
    """正常なデータ保存のテスト"""
    print("\n[TEST 4] Save data success")

    test_data = [{"id": 1, "name": "Test Item 1"}, {"id": 2, "name": "Test Item 2"}]

    save_data("test_save.json", test_data)

    # データを読み込んで検証
    loaded_data = load_data("test_save.json")
    assert loaded_data == test_data, f"Expected {test_data}, got {loaded_data}"
    print("[PASS] Data saved and loaded correctly")

    # クリーンアップ
    filepath = os.path.join(get_data_dir(), "test_save.json")
    os.remove(filepath)


def test_save_data_atomic_write():
    """アトミック書き込みのテスト"""
    print("\n[TEST 5] Atomic write")

    # 既存ファイルを作成
    filepath = os.path.join(get_data_dir(), "atomic_test.json")
    original_data = [{"id": 1, "name": "Original"}]
    save_data("atomic_test.json", original_data)

    # 新しいデータを保存
    new_data = [{"id": 2, "name": "Updated"}]
    save_data("atomic_test.json", new_data)

    # データを読み込んで検証
    loaded_data = load_data("atomic_test.json")
    assert loaded_data == new_data, f"Expected {new_data}, got {loaded_data}"
    print("[PASS] Atomic write works correctly")

    # クリーンアップ
    os.remove(filepath)


def test_load_data_unicode_handling():
    """Unicode文字の処理テスト"""
    print("\n[TEST 6] Unicode handling")

    test_data = [{"id": 1, "title": "日本語テスト"}, {"id": 2, "title": "テスト項目２"}]

    save_data("unicode_test.json", test_data)
    loaded_data = load_data("unicode_test.json")

    assert loaded_data == test_data, f"Expected {test_data}, got {loaded_data}"
    print("[PASS] Unicode characters handled correctly")

    # クリーンアップ
    filepath = os.path.join(get_data_dir(), "unicode_test.json")
    os.remove(filepath)


def test_error_response_format():
    """エラーレスポンス形式のテスト"""
    print("\n[TEST 7] Error response format")

    from app_v2 import error_response

    # 基本的なエラーレスポンス
    response, status_code = error_response("Test error", "TEST_ERROR", 400)
    response_data = response.get_json()

    assert not response_data["success"]
    assert response_data["error"]["code"] == "TEST_ERROR"
    assert response_data["error"]["message"] == "Test error"
    assert status_code == 400
    print("[PASS] Error response format is correct")

    # 詳細付きエラーレスポンス
    response, status_code = error_response(
        "Validation failed",
        "VALIDATION_ERROR",
        400,
        {"field": "username", "reason": "too short"},
    )
    response_data = response.get_json()

    assert "details" in response_data["error"]
    assert response_data["error"]["details"]["field"] == "username"
    print("[PASS] Error response with details is correct")


def run_all_tests():
    """全テストを実行"""
    print("=" * 60)
    print("エラーハンドリング強化テスト")
    print("=" * 60)

    tests = [
        test_load_data_file_not_found,
        test_load_data_json_decode_error,
        test_load_data_non_list_data,
        test_save_data_success,
        test_save_data_atomic_write,
        test_load_data_unicode_handling,
        test_error_response_format,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"テスト結果: {passed} passed, {failed} failed")
    print("=" * 60)

    # クリーンアップ
    import shutil

    shutil.rmtree(TEST_DATA_DIR)
    print(f"[CLEANUP] Removed temporary directory: {TEST_DATA_DIR}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
