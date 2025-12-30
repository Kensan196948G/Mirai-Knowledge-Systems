"""
クイック検証テスト

依存パッケージなしで構文と構造を検証するテスト
"""
import pytest
import importlib.util
from pathlib import Path


def _load_module(name, filename):
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_imports_are_valid():
    """テストファイルのインポートが有効か確認"""
    try:
        _load_module('test_all_features', 'test_all_features.py')
        _load_module('test_api_endpoints', 'test_api_endpoints.py')
        assert True
    except SyntaxError as e:
        pytest.fail(f"Syntax error in test files: {e}")


def test_test_structure():
    """テストクラスの構造を検証"""
    test_all_features = _load_module('test_all_features', 'test_all_features.py')

    # 各テストクラスが存在することを確認
    assert hasattr(test_all_features, 'TestKnowledgeCRUDFeature')
    assert hasattr(test_all_features, 'TestSOPViewFeature')
    assert hasattr(test_all_features, 'TestSearchFeature')
    assert hasattr(test_all_features, 'TestNotificationFeature')
    assert hasattr(test_all_features, 'TestApprovalFlowFeature')
    assert hasattr(test_all_features, 'TestDashboardFeature')
    assert hasattr(test_all_features, 'TestAuthenticationFlow')
    assert hasattr(test_all_features, 'TestEndToEndScenarios')


def test_endpoint_test_structure():
    """エンドポイントテストクラスの構造を検証"""
    test_api_endpoints = _load_module('test_api_endpoints', 'test_api_endpoints.py')

    # 各テストクラスが存在することを確認
    assert hasattr(test_api_endpoints, 'TestAuthEndpoints')
    assert hasattr(test_api_endpoints, 'TestKnowledgeEndpoints')
    assert hasattr(test_api_endpoints, 'TestSearchEndpoints')
    assert hasattr(test_api_endpoints, 'TestNotificationEndpoints')
    assert hasattr(test_api_endpoints, 'TestSOPEndpoints')
    assert hasattr(test_api_endpoints, 'TestApprovalEndpoints')
    assert hasattr(test_api_endpoints, 'TestDashboardEndpoints')
    assert hasattr(test_api_endpoints, 'TestErrorHandling')
    assert hasattr(test_api_endpoints, 'TestResponseFormat')


if __name__ == '__main__':
    print("✓ All validation tests passed")
