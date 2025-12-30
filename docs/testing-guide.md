# テスト実行ガイド

## 概要

Mirai Knowledge Systemsのテストスイートは、以下の4つのレベルで構成されています：

1. **ユニットテスト** - 個別の関数やメソッドのテスト
2. **統合テスト** - APIエンドポイント全体のテスト
3. **セキュリティテスト** - 認証・認可・入力検証のテスト
4. **E2Eテスト** - ブラウザを使用したエンドツーエンドテスト

## 前提条件

### Python環境

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-flask pytest-xdist playwright
```

### Playwright(E2Eテスト用)

```bash
playwright install
```

## テストの実行方法

### 全テストの実行

```bash
cd backend
pytest tests/ -v
```

### ユニットテストのみ実行

```bash
pytest tests/unit -v
```

### 統合テストのみ実行

```bash
pytest tests/integration -v
```

### セキュリティテストのみ実行

```bash
pytest tests/security -v
```

### E2Eテストのみ実行

```bash
pytest tests/e2e -v
```

### マーカーを使用したテスト実行

```bash
# ユニットテストのみ
pytest -m unit -v

# 統合テストのみ
pytest -m integration -v

# セキュリティテストのみ
pytest -m security -v

# E2Eテストのみ
pytest -m e2e -v
```

## カバレッジ測定

### 基本的なカバレッジ測定

```bash
pytest tests/ --cov=app_v2 --cov=schemas --cov-report=term-missing
```

### HTMLレポートの生成

```bash
pytest tests/ --cov=app_v2 --cov=schemas --cov-report=html:tests/reports/coverage_html
```

生成されたレポートは `backend/tests/reports/coverage_html/index.html` で閲覧できます。

### XMLレポートの生成（CI用）

```bash
pytest tests/ --cov=app_v2 --cov=schemas --cov-report=xml:tests/reports/coverage.xml
```

### カバレッジ目標の確認

```bash
pytest tests/ --cov=app_v2 --cov=schemas --cov-fail-under=80
```

カバレッジが80%未満の場合、テストは失敗します。

## 並列実行（高速化）

```bash
# CPUコア数に応じて自動的に並列実行
pytest tests/unit tests/integration -n auto
```

## 特定のテストファイルやテストケースの実行

### 特定のファイル

```bash
pytest tests/integration/test_auth_flow.py -v
```

### 特定のクラス

```bash
pytest tests/integration/test_auth_flow.py::TestAuthFlow -v
```

### 特定のテストケース

```bash
pytest tests/integration/test_auth_flow.py::TestAuthFlow::test_login_success_flow -v
```

### パターンマッチング

```bash
# "auth"を含むテストのみ実行
pytest tests/ -k "auth" -v

# "create"または"update"を含むテストのみ実行
pytest tests/ -k "create or update" -v
```

## テスト失敗時のデバッグ

### 詳細なトレースバック

```bash
pytest tests/ -v --tb=long
```

### 最初の失敗で停止

```bash
pytest tests/ -x
```

### 最大5個の失敗で停止

```bash
pytest tests/ --maxfail=5
```

### PDB（Python Debugger）を使用

```bash
pytest tests/ --pdb
```

### 失敗したテストのみ再実行

```bash
pytest tests/ --lf
```

### 失敗したテストを最初に実行

```bash
pytest tests/ --ff
```

## テストカバレッジの目標

現在のカバレッジ目標: **80%以上**

### カバレッジの内訳（目標）

- **app_v2.py**: 85%以上
- **schemas.py**: 90%以上
- **統合テスト**: API全エンドポイント
- **セキュリティテスト**: 全認証・認可パス

## テストファイルの構成

```
backend/tests/
├── unit/                           # ユニットテスト
│   ├── test_password_hashing.py
│   ├── test_validation.py
│   ├── test_data_operations.py
│   ├── test_notification_helpers.py
│   └── test_app_v2_additional_coverage.py
├── integration/                    # 統合テスト
│   ├── test_auth_flow.py          # 認証フロー
│   ├── test_knowledge_api.py      # ナレッジCRUD
│   ├── test_knowledge_crud_full.py # ナレッジ完全CRUD
│   ├── test_rbac_flow.py          # RBAC統合テスト
│   ├── test_notifications_api.py  # 通知API
│   ├── test_search_api.py         # 検索API
│   ├── test_metrics_api.py        # メトリクスAPI
│   ├── test_error_handlers.py     # エラーハンドラ
│   └── test_other_apis.py         # その他API
├── security/                       # セキュリティテスト
│   ├── test_authentication.py     # 認証テスト
│   ├── test_authorization.py      # 認可テスト
│   ├── test_input_validation.py   # 入力検証
│   └── test_https_security.py     # HTTPS/セキュリティ
├── e2e/                           # E2Eテスト
│   ├── test_dashboard_flow.py     # ダッシュボード
│   ├── test_knowledge_search_flow.py # 検索フロー
│   └── playwright.config.js       # Playwright設定
├── acceptance/                     # 受け入れテスト
│   ├── test_all_features.py
│   ├── test_api_endpoints.py
│   └── test_quick_validation.py
├── load/                          # 負荷テスト
│   ├── locustfile.py
│   ├── performance_benchmark.py
│   └── stress_test.py
├── fixtures/                      # テストフィクスチャ
├── reports/                       # テストレポート
│   ├── coverage_html/            # HTMLカバレッジレポート
│   └── coverage.xml              # XMLカバレッジレポート
└── conftest.py                    # 共通フィクスチャ
```

## テストのベストプラクティス

### 1. テストの独立性

各テストは独立して実行可能であり、他のテストに依存しないこと。

```python
def test_example(client):
    # セットアップ
    token = login(client)

    # 実行
    response = client.get('/api/v1/endpoint', headers={'Authorization': f'Bearer {token}'})

    # 検証
    assert response.status_code == 200

    # クリーンアップ（必要に応じて）
```

### 2. テストデータの分離

各テストで独自のテストデータを使用し、共有データによる副作用を避ける。

```python
@pytest.fixture()
def client(tmp_path):
    # 一時ディレクトリを使用してデータを分離
    app.config['DATA_DIR'] = str(tmp_path)
    # ...
```

### 3. 明確なテスト名

テスト名は、何をテストしているのかが明確にわかるようにする。

```python
# 良い例
def test_admin_can_create_knowledge():
    pass

def test_partner_cannot_create_knowledge():
    pass

# 悪い例
def test_knowledge():
    pass
```

### 4. AAAパターン

- **Arrange**: テストのセットアップ
- **Act**: テスト対象の実行
- **Assert**: 結果の検証

```python
def test_example(client):
    # Arrange
    token = login(client)
    data = {'title': 'Test'}

    # Act
    response = client.post('/api/v1/knowledge', json=data, headers={'Authorization': f'Bearer {token}'})

    # Assert
    assert response.status_code == 201
    assert response.get_json()['data']['title'] == 'Test'
```

## CI/CDでのテスト実行

### GitHub Actions

プッシュまたはプルリクエスト時に自動的にテストが実行されます。

ワークフロー: `.github/workflows/ci-backend-improved.yml`

### ローカルでCI環境を再現

```bash
# Python 3.12でテスト
python3.12 -m pytest tests/ -v --cov=app_v2 --cov=schemas --cov-fail-under=80

# 並列実行
pytest tests/unit tests/integration -n auto --cov=app_v2 --cov-append
```

## トラブルシューティング

### ImportError: No module named 'flask_cors'

```bash
pip install -r backend/requirements.txt
```

### カバレッジが80%に達しない

カバレッジレポートを確認して、未カバーの行を特定します。

```bash
pytest tests/ --cov=app_v2 --cov-report=html:tests/reports/coverage_html
# ブラウザで tests/reports/coverage_html/index.html を開く
```

### E2Eテストが失敗する

1. Playwrightがインストールされているか確認
2. アプリケーションが起動しているか確認
3. BASE_URL環境変数が正しく設定されているか確認

```bash
export BASE_URL=http://localhost:5010
pytest tests/e2e -v
```

### テストが遅い

並列実行を使用します。

```bash
pytest tests/ -n auto
```

## さらなる情報

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-cov公式ドキュメント](https://pytest-cov.readthedocs.io/)
- [Playwright Python公式ドキュメント](https://playwright.dev/python/)

## カバレッジ目標達成のために

現在のカバレッジを確認し、不足しているテストを特定します。

```bash
# カバレッジ測定
pytest tests/unit tests/integration --cov=app_v2 --cov=schemas --cov-report=html --cov-report=term-missing

# 未カバーの行を確認
# HTMLレポートで赤くハイライトされた行を確認
# ターミナル出力で "Missing" として表示された行番号を確認
```

### 優先的にカバーすべき領域

1. **エラーハンドリング**: 例外パス、エラーレスポンス
2. **RBAC**: 全ロールでの権限チェック
3. **バリデーション**: 無効な入力のテスト
4. **エッジケース**: 境界値、空データ、NULL値

## まとめ

- 全テスト実行: `pytest tests/ -v`
- カバレッジ確認: `pytest tests/ --cov=app_v2 --cov=schemas --cov-report=term-missing`
- カバレッジ目標: **80%以上**
- 失敗時: `pytest tests/ -v --tb=long --pdb`
