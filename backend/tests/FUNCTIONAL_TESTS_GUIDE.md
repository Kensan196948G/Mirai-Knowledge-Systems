# 機能テスト実行ガイド

## 概要

このガイドでは、Mirai Knowledge Systemsの全機能を自動的にテストする方法を説明します。

## 前提条件

### 1. Python環境

```bash
# Python 3.8以上が必要
python3 --version
```

### 2. 仮想環境の作成とアクティベート

```bash
# 仮想環境を作成（まだの場合）
cd /path/to/Mirai-Knowledge-Systems/backend
python3 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
# アプリケーションの依存パッケージ
pip install -r requirements.txt

# テストに必要な追加パッケージ
pip install pytest pytest-cov pytest-html pytest-xdist
```

## クイックスタート

### 最も簡単な実行方法

```bash
# シェルスクリプトを使った一括実行
./tests/run_functional_tests.sh
```

### HTMLレポート付き実行

```bash
./tests/run_functional_tests.sh --html --coverage
```

実行後、以下のファイルをブラウザで開けます：
- **テストレポート**: `tests/reports/functional/report.html`
- **カバレッジレポート**: `tests/reports/functional/coverage/index.html`

## 詳細な実行方法

### 全ての受け入れテストを実行

```bash
pytest tests/acceptance/ -v
```

### 特定のテストファイルのみ実行

```bash
# 全機能テスト
pytest tests/acceptance/test_all_features.py -v

# APIエンドポイントテスト
pytest tests/acceptance/test_api_endpoints.py -v
```

### 特定の機能のみテスト

```bash
# ナレッジCRUD機能のみ
pytest tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature -v

# 認証エンドポイントのみ
pytest tests/acceptance/test_api_endpoints.py::TestAuthEndpoints -v

# 検索機能のみ
pytest tests/acceptance/test_all_features.py::TestSearchFeature -v
```

### 特定のテストケースのみ実行

```bash
pytest tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature::test_create_knowledge_success -v
```

## 便利なオプション

### 詳細な出力

```bash
# 標準の詳細モード
pytest tests/acceptance/ -v

# より詳細（print文も表示）
pytest tests/acceptance/ -vv -s

# 失敗したテストのみ詳細表示
pytest tests/acceptance/ -v --tb=short
```

### 並列実行（高速化）

```bash
# 自動的にCPUコア数に応じて並列実行
pytest tests/acceptance/ -n auto

# 4並列で実行
pytest tests/acceptance/ -n 4
```

### 失敗したテストのみ再実行

```bash
# 最初の実行
pytest tests/acceptance/

# 失敗したテストのみ再実行
pytest tests/acceptance/ --lf
```

### 特定のマーカーでフィルター

```bash
# 遅いテストをスキップ（マーカーが設定されている場合）
pytest tests/acceptance/ -m "not slow"
```

## レポート生成

### HTMLレポート

```bash
pytest tests/acceptance/ \
  --html=tests/reports/acceptance_report.html \
  --self-contained-html
```

### カバレッジレポート

```bash
# HTMLとターミナル両方
pytest tests/acceptance/ \
  --cov=. \
  --cov-report=html:tests/reports/coverage \
  --cov-report=term

# カバレッジ不足の行を表示
pytest tests/acceptance/ \
  --cov=. \
  --cov-report=term-missing
```

### JUnit XML（CI/CD用）

```bash
pytest tests/acceptance/ \
  --junitxml=tests/reports/junit.xml
```

## シェルスクリプトのオプション

`run_functional_tests.sh` は以下のオプションをサポートしています：

```bash
# ヘルプを表示
./tests/run_functional_tests.sh --help

# HTMLレポート生成
./tests/run_functional_tests.sh --html

# カバレッジレポート生成
./tests/run_functional_tests.sh --coverage

# 詳細出力
./tests/run_functional_tests.sh --verbose

# 並列実行
./tests/run_functional_tests.sh --parallel

# 受け入れテストのみ
./tests/run_functional_tests.sh --acceptance

# エンドポイントテストのみ
./tests/run_functional_tests.sh --endpoints

# 全オプション組み合わせ
./tests/run_functional_tests.sh --html --coverage --parallel --verbose
```

## テスト内容

### test_all_features.py - 全機能テスト

以下の機能をエンドツーエンドでテストします：

1. **ナレッジCRUD機能** (5テスト)
   - 作成、一覧取得、詳細取得、フィルタリング、バリデーション

2. **SOP閲覧機能** (2テスト)
   - 一覧取得、認証確認

3. **事故レポート機能** (1テスト)
   - データ構造の検証

4. **専門家相談機能** (1テスト)
   - データ構造の検証

5. **検索機能** (3テスト)
   - 基本検索、カテゴリーフィルター、空クエリ

6. **通知機能** (3テスト)
   - 一覧取得、既読化、未読数取得

7. **承認フロー機能** (2テスト)
   - 一覧取得、ステータスフィルター

8. **ダッシュボード機能** (2テスト)
   - 統計取得、データ完全性

9. **認証フロー** (3テスト)
   - ログイン、無効な認証情報、トークンリフレッシュ

10. **エンドツーエンドシナリオ** (2テスト)
    - 完全なナレッジワークフロー、通知ワークフロー

### test_api_endpoints.py - APIエンドポイントテスト

以下のエンドポイントを正常系・異常系の両面でテストします：

1. **認証エンドポイント** (12テスト)
   - ログイン成功/失敗、トークンリフレッシュ、現在ユーザー取得

2. **ナレッジエンドポイント** (10テスト)
   - CRUD操作、フィルタリング、バリデーション、エラーケース

3. **検索エンドポイント** (6テスト)
   - 統合検索、クエリパターン、特殊文字

4. **通知エンドポイント** (6テスト)
   - 一覧、既読化、未読数、エラーケース

5. **SOPエンドポイント** (2テスト)
   - 一覧取得、認証確認

6. **承認エンドポイント** (2テスト)
   - 一覧取得、フィルタリング

7. **ダッシュボードエンドポイント** (2テスト)
   - 統計取得、認証確認

8. **メトリクスエンドポイント** (1テスト)
   - システムメトリクス取得

9. **エラーハンドリング** (3テスト)
   - 404、405、無効なContent-Type

10. **レスポンス形式検証** (3テスト)
    - 成功レスポンス、エラーレスポンス、リストレスポンス

11. **セキュリティヘッダー** (2テスト)
    - CORS、Content-Type

## トラブルシューティング

### よくある問題と解決方法

#### 1. ModuleNotFoundError

```bash
# 問題: No module named 'flask_cors'
# 解決策:
pip install -r requirements.txt
```

#### 2. 仮想環境がアクティベートされていない

```bash
# 解決策:
source venv/bin/activate
# または
source .venv/bin/activate
```

#### 3. テストが401 Unauthorizedで失敗

```bash
# 原因: テストデータが正しく作成されていない
# 解決策: conftest.pyがtmp_pathを使用して自動作成するため、
# 通常は発生しませんが、もし発生した場合は:
pytest tests/acceptance/ -v --tb=long
# でスタックトレースを確認
```

#### 4. テストが見つからない

```bash
# 問題: collected 0 items
# 解決策: 正しいディレクトリから実行されているか確認
cd /path/to/Mirai-Knowledge-Systems/backend
pytest tests/acceptance/
```

#### 5. 並列実行ができない

```bash
# 問題: invalid option: -n
# 解決策: pytest-xdist をインストール
pip install pytest-xdist
```

### デバッグのヒント

```bash
# 1. 詳細ログを表示
pytest tests/acceptance/ -vv -s --log-cli-level=DEBUG

# 2. 失敗時にPDBデバッガーを起動
pytest tests/acceptance/ --pdb

# 3. 最初の失敗で停止
pytest tests/acceptance/ -x

# 4. 特定のテストのみ詳細出力
pytest tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature::test_create_knowledge_success -vv -s
```

## CI/CD統合

### GitHub Actions

```yaml
name: Functional Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-html pytest-xdist

      - name: Run functional tests
        run: |
          cd backend
          ./tests/run_functional_tests.sh --html --coverage

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: backend/tests/reports/
```

### GitLab CI

```yaml
functional-tests:
  stage: test
  script:
    - cd backend
    - python3 -m venv venv
    - source venv/bin/activate
    - pip install -r requirements.txt
    - pip install pytest pytest-cov pytest-html pytest-xdist
    - ./tests/run_functional_tests.sh --html --coverage --parallel
  artifacts:
    when: always
    paths:
      - backend/tests/reports/
    reports:
      junit: backend/tests/reports/junit.xml
```

## ベストプラクティス

1. **定期的な実行**: 機能変更時は必ずテストを実行
2. **カバレッジ確認**: 新機能追加時はカバレッジが下がらないように
3. **並列実行**: 大量のテストは並列実行で時間短縮
4. **レポート保存**: CI/CDではレポートをアーティファクトとして保存
5. **失敗の調査**: 失敗したテストは詳細ログで原因を特定

## テスト結果の見方

### 成功例

```
tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature::test_create_knowledge_success PASSED [100%]

====== 1 passed in 0.52s ======
```

### 失敗例

```
tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature::test_create_knowledge_success FAILED [100%]

FAILED tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature::test_create_knowledge_success
AssertionError: assert 400 == 201
```

## 参考リンク

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-html](https://pytest-html.readthedocs.io/)
- [pytest-xdist](https://pytest-xdist.readthedocs.io/)

## サポート

問題が発生した場合は、以下を確認してください：

1. 依存パッケージが全てインストールされているか
2. 仮想環境がアクティベートされているか
3. テストログ（`tests/reports/functional/test_run_*.log`）を確認
4. 詳細モード（`-vv -s`）で実行して詳細を確認
