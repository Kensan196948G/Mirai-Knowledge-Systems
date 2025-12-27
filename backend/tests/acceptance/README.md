# 受け入れテスト (Acceptance Tests)

全機能の自動機能テストスイート

## 概要

このディレクトリには、システムの全機能をエンドツーエンドで検証する自動テストが含まれています。

## テストファイル

### 1. test_all_features.py
全ビジネス機能の包括的なテスト

- **ナレッジCRUD機能**: 作成・読取・更新・削除
- **SOP閲覧機能**: 標準作業手順書の取得
- **事故レポート機能**: データ構造の検証
- **専門家相談機能**: データ構造の検証
- **検索機能**: 統合検索、フィルタリング
- **通知機能**: 一覧取得、既読化、未読数取得
- **承認フロー機能**: 承認待ち一覧、ステータスフィルター
- **ダッシュボード機能**: 統計情報取得
- **認証フロー**: ログイン、トークンリフレッシュ
- **エンドツーエンドシナリオ**: 複数機能の連携動作

### 2. test_api_endpoints.py
全APIエンドポイントの網羅的なテスト

- **認証エンドポイント**: ログイン、リフレッシュ、現在ユーザー取得
- **ナレッジエンドポイント**: CRUD操作、フィルタリング
- **検索エンドポイント**: 統合検索、各種クエリパターン
- **通知エンドポイント**: 一覧、既読化、未読数
- **SOPエンドポイント**: 一覧取得
- **承認エンドポイント**: 一覧、フィルター
- **ダッシュボードエンドポイント**: 統計取得
- **メトリクスエンドポイント**: システムメトリクス
- **エラーハンドリング**: 404, 405, バリデーションエラー
- **レスポンス形式検証**: JSON構造、ヘッダー
- **セキュリティ検証**: CORS、Content-Type

## テストの実行

### 基本的な実行

```bash
# 全ての受け入れテストを実行
pytest tests/acceptance/

# 特定のテストファイルのみ実行
pytest tests/acceptance/test_all_features.py
pytest tests/acceptance/test_api_endpoints.py

# 特定のテストクラスのみ実行
pytest tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature

# 特定のテストケースのみ実行
pytest tests/acceptance/test_all_features.py::TestKnowledgeCRUDFeature::test_create_knowledge_success
```

### 詳細出力

```bash
# 詳細モード
pytest tests/acceptance/ -v

# より詳細（print文も表示）
pytest tests/acceptance/ -vv -s
```

### レポート生成

```bash
# HTMLレポート生成
pytest tests/acceptance/ --html=tests/reports/acceptance_report.html --self-contained-html

# カバレッジレポート生成
pytest tests/acceptance/ --cov=. --cov-report=html:tests/reports/coverage
```

### 並列実行（高速化）

```bash
# pytest-xdist が必要: pip install pytest-xdist
pytest tests/acceptance/ -n auto
```

### 一括実行スクリプト

便利なシェルスクリプトを用意しています：

```bash
# 基本実行
./tests/run_functional_tests.sh

# HTMLレポート付き
./tests/run_functional_tests.sh --html

# カバレッジレポート付き
./tests/run_functional_tests.sh --coverage

# 全機能有効
./tests/run_functional_tests.sh --html --coverage --parallel --verbose

# 受け入れテストのみ
./tests/run_functional_tests.sh --acceptance

# エンドポイントテストのみ
./tests/run_functional_tests.sh --endpoints
```

## テストカバレッジ

### test_all_features.py でカバーされる機能

| 機能 | テストクラス | テスト数 |
|-----|------------|---------|
| ナレッジCRUD | TestKnowledgeCRUDFeature | 5 |
| SOP閲覧 | TestSOPViewFeature | 2 |
| 事故レポート | TestIncidentReportFeature | 1 |
| 専門家相談 | TestExpertConsultationFeature | 1 |
| 検索機能 | TestSearchFeature | 3 |
| 通知機能 | TestNotificationFeature | 3 |
| 承認フロー | TestApprovalFlowFeature | 2 |
| ダッシュボード | TestDashboardFeature | 2 |
| 認証フロー | TestAuthenticationFlow | 3 |
| E2Eシナリオ | TestEndToEndScenarios | 2 |

### test_api_endpoints.py でカバーされるエンドポイント

| エンドポイント | テスト観点 | テスト数 |
|--------------|----------|---------|
| /api/v1/auth/* | 正常系、異常系、バリデーション | 12 |
| /api/v1/knowledge | CRUD、フィルター、エラー | 10 |
| /api/v1/search/unified | クエリパターン、認証 | 6 |
| /api/v1/notifications/* | 一覧、既読化、未読数 | 6 |
| /api/v1/sop | 一覧取得、認証 | 2 |
| /api/v1/approvals | 一覧、フィルター | 2 |
| /api/v1/dashboard/stats | 統計取得、認証 | 2 |
| /api/v1/metrics | メトリクス取得 | 1 |
| エラーハンドリング | 404, 405, バリデーション | 3 |
| レスポンス形式 | JSON、ヘッダー | 3 |
| セキュリティ | CORS、Content-Type | 2 |

## テストデータ

テストは `conftest.py` で定義されたフィクスチャを使用して、テスト用の一時データを作成します：

- **ユーザーデータ**: admin ユーザー（パスワード: admin123）
- **ナレッジデータ**: テスト用ナレッジアイテム
- **一時ディレクトリ**: 各テストで独立したデータディレクトリ

## CI/CD統合

このテストスイートはCI/CD パイプラインに統合可能です：

```yaml
# GitHub Actions の例
- name: Run Functional Tests
  run: |
    ./tests/run_functional_tests.sh --html --coverage

- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: tests/reports/
```

## トラブルシューティング

### テストが失敗する場合

1. **依存パッケージの確認**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov pytest-html pytest-xdist
   ```

2. **仮想環境の確認**
   ```bash
   source venv/bin/activate  # または .venv/bin/activate
   ```

3. **詳細ログの確認**
   ```bash
   pytest tests/acceptance/ -vv -s --log-cli-level=DEBUG
   ```

### よくある問題

- **ModuleNotFoundError**: 仮想環境がアクティベートされていない
- **401 Unauthorized**: 認証トークンの期限切れ（テストは自動で再ログイン）
- **404 Not Found**: データファイルが存在しない（conftest.py が自動作成）

## ベストプラクティス

1. **テストの独立性**: 各テストは他のテストに依存しない
2. **データのクリーンアップ**: tmp_path フィクスチャで自動クリーンアップ
3. **明確なアサーション**: 失敗時に原因が分かりやすい
4. **エラーメッセージ**: 日本語と英語の両方に対応

## 今後の拡張

- [ ] パフォーマンステスト（負荷テスト）
- [ ] セキュリティテスト（脆弱性スキャン）
- [ ] ブラウザ自動化テスト（Selenium/Playwright）
- [ ] APIコントラクトテスト（Pact）
- [ ] 視覚的回帰テスト（スクリーンショット比較）
