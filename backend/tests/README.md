# Mirai Knowledge Systems - テストスイート

## 概要

このディレクトリには、Mirai Knowledge Systemsの包括的なテストスイートが含まれています。

- **バックエンド**: Python (pytest) - 245+ テスト
- **フロントエンド**: JavaScript (Jest + Playwright) - 242+ テスト

## クイックスタート

### フロントエンドテスト (新規追加)

```bash
# セットアップ
cd backend
./setup-frontend-tests.sh

# ユニットテスト実行
npm run test:unit

# E2Eテスト実行
npm run test:e2e

# 全テスト実行
npm test
```

### バックエンドテスト

### カバレッジ測定（推奨）

```bash
cd backend
source venv/bin/activate
./run_coverage.sh
```

### 全テスト実行

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

## テスト構成

```
tests/
├── unit/                           # ユニットテスト
│   ├── [Backend] Python (40+件)
│   │   ├── test_password_hashing.py
│   │   ├── test_validation.py
│   │   ├── test_data_operations.py
│   │   ├── test_notification_helpers.py
│   │   └── test_app_v2_additional_coverage.py
│   └── [Frontend] JavaScript (129件) ★NEW
│       ├── setup.js
│       ├── dom-helpers.test.js (24 tests)
│       ├── actions.test.js (22 tests)
│       ├── notifications.test.js (25 tests)
│       ├── app-auth.test.js (31 tests)
│       └── detail-pages-utils.test.js (27 tests)
│
├── integration/                    # 統合テスト (130+件)
│   ├── test_auth_flow.py          # 認証フロー
│   ├── test_knowledge_api.py      # ナレッジCRUD基本
│   ├── test_knowledge_crud_full.py # ナレッジCRUD完全版 ★NEW
│   ├── test_rbac_flow.py          # RBAC統合テスト ★NEW
│   ├── test_notifications_api.py  # 通知API
│   ├── test_search_api.py         # 検索API
│   ├── test_metrics_api.py        # メトリクスAPI
│   ├── test_error_handlers.py     # エラーハンドラ
│   ├── test_https_middleware.py   # HTTPSミドルウェア
│   └── test_other_apis.py         # その他API
│
├── security/                       # セキュリティテスト (30+件)
│   ├── test_authentication.py     # 認証テスト
│   ├── test_authorization.py      # 認可テスト
│   ├── test_input_validation.py   # 入力検証
│   └── test_https_security.py     # HTTPSセキュリティ
│
├── e2e/                           # E2Eテスト
│   ├── [Backend] Python (20+件)
│   │   ├── test_dashboard_flow.py     # ダッシュボードフロー ★NEW
│   │   └── test_knowledge_search_flow.py # 検索フロー ★NEW
│   └── [Frontend] JavaScript (113件) ★NEW
│       ├── global-setup.js
│       ├── login.spec.js (9 tests)
│       ├── knowledge-search.spec.js (11 tests)
│       ├── sop-detail-expert-consult.spec.js (16 tests)
│       ├── scenario1_knowledge_lifecycle.spec.js (2 tests)
│       ├── scenario2_approval_flow.spec.js (5 tests)
│       ├── scenario3_search_and_view.spec.js (9 tests)
│       ├── scenario4_incident_report.spec.js (7 tests)
│       ├── scenario5_expert_consultation.spec.js (7 tests)
│       └── compatibility/
│           ├── browsers.spec.js (19 tests)
│           └── responsive.spec.js (28 tests)
│
├── acceptance/                     # 受け入れテスト (15+件)
│   ├── test_all_features.py
│   ├── test_api_endpoints.py
│   └── test_quick_validation.py
│
├── load/                          # 負荷テスト (10+件)
│   ├── locustfile.py
│   ├── performance_benchmark.py
│   └── stress_test.py
│
├── fixtures/                      # テストフィクスチャ
├── reports/                       # テストレポート
│   ├── coverage_html/            # HTMLカバレッジレポート
│   └── coverage.xml              # XMLカバレッジレポート
│
└── conftest.py                    # 共通フィクスチャ
```

## テストカテゴリ

### ユニットテスト (40+件)
個別の関数やメソッドの動作をテスト

```bash
pytest tests/unit -v
```

### 統合テスト (130+件)
APIエンドポイント全体の動作をテスト

```bash
pytest tests/integration -v
```

**新規追加:**
- `test_knowledge_crud_full.py`: ナレッジの更新・削除を含む完全CRUD (18件)
- `test_rbac_flow.py`: 全ロールでの権限チェック (20件)

### セキュリティテスト (30+件)
認証・認可・入力検証をテスト

```bash
pytest tests/security -v
```

### E2Eテスト (20+件)
ブラウザを使用したエンドツーエンドテスト

```bash
pytest tests/e2e -v
```

**新規追加:**
- `test_dashboard_flow.py`: ログイン→ダッシュボード表示 (11件)
- `test_knowledge_search_flow.py`: 検索→詳細表示 (8件)

## カバレッジ目標

**目標: 80%以上**

- app_v2.py: 80%以上
- schemas.py: 80%以上

### カバレッジ測定

```bash
# HTMLレポート生成
pytest tests/ --cov=app_v2 --cov=schemas --cov-report=html:tests/reports/coverage_html

# ターミナル出力
pytest tests/ --cov=app_v2 --cov=schemas --cov-report=term-missing

# 80%未満でテスト失敗
pytest tests/ --cov=app_v2 --cov=schemas --cov-fail-under=80
```

## マーカーを使用したテスト実行

```bash
# ユニットテストのみ
pytest -m unit -v

# 統合テストのみ
pytest -m integration -v

# セキュリティテストのみ
pytest -m security -v

# E2Eテストのみ
pytest -m e2e -v

# 遅いテスト以外
pytest -m "not slow" -v
```

## 並列実行（高速化）

```bash
# 自動的に最適なプロセス数で並列実行
pytest tests/ -n auto
```

## デバッグ

```bash
# 詳細なトレースバック
pytest tests/ -v --tb=long

# 最初の失敗で停止
pytest tests/ -x

# 失敗したテストのみ再実行
pytest tests/ --lf

# PDBデバッガ起動
pytest tests/ --pdb
```

## CI/CD

GitHub Actionsで自動的にテストが実行されます。

- ワークフロー: `.github/workflows/ci-backend-improved.yml`
- カバレッジ必須: 80%以上
- テストマトリクス: Python 3.10, 3.11, 3.12

## ドキュメント

詳細なガイドは以下を参照してください：

- [テスト実行ガイド](/docs/testing-guide.md)
- [テストカバレッジレポート](/docs/test-coverage-report.md)

## トラブルシューティング

### ImportError

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-flask pytest-xdist playwright
```

### Playwright関連エラー

```bash
playwright install
```

### カバレッジが80%に達しない

```bash
# HTMLレポートで詳細確認
pytest tests/ --cov=app_v2 --cov=schemas --cov-report=html
# ブラウザで tests/reports/coverage_html/index.html を開く
```

## テスト統計

### バックエンド (Python)
| カテゴリ | ファイル数 | テストケース数 |
|---------|-----------|--------------|
| ユニット | 5 | 40+ |
| 統合 | 10 | 130+ |
| セキュリティ | 4 | 30+ |
| E2E | 2 | 20+ |
| 受け入れ | 3 | 15+ |
| 負荷 | 3 | 10+ |
| **小計** | **27** | **245+** |

### フロントエンド (JavaScript) ★NEW
| カテゴリ | ファイル数 | テストケース数 |
|---------|-----------|--------------|
| ユニット (Jest) | 5 | 129 |
| E2E (Playwright) | 10 | 113 |
| **小計** | **15** | **242** |

### 総合計
| | ファイル数 | テストケース数 |
|--|-----------|--------------|
| **全テスト** | **42** | **487+** |

## 最新の更新

### 2026-01-01: フロントエンドテスト環境構築 ★NEW

**追加されたフロントエンドテスト (242件):**

1. **ユニットテスト (Jest) - 129件**
   - `dom-helpers.test.js` - XSS対策、セキュアなDOM操作 (24件)
   - `actions.test.js` - トースト通知、アクション処理 (22件)
   - `notifications.test.js` - 通知システム、バッジ管理 (25件)
   - `app-auth.test.js` - 認証、RBAC、権限管理 (31件)
   - `detail-pages-utils.test.js` - API呼び出し、日付フォーマット (27件)

2. **E2Eテスト (Playwright) - 113件**
   - `login.spec.js` - ログインフロー (9件)
   - `knowledge-search.spec.js` - ナレッジ検索 (11件)
   - `sop-detail-expert-consult.spec.js` - SOP詳細・専門家相談 (16件)
   - その他シナリオテスト (77件)

**新規設定ファイル:**
- `jest.config.js` - Jest設定
- `playwright.config.js` - Playwright設定（更新）
- `package.json` - フロントエンド依存パッケージ
- `setup-frontend-tests.sh` - セットアップスクリプト
- `.github/workflows/frontend-tests.yml` - CI/CD統合

**カバレッジ目標:**
- フロントエンド: 70%以上（全メトリクス）

**ドキュメント:**
- `FRONTEND_TESTING.md` - フロントエンドテスト完全ガイド

### 2025-12-30: バックエンドテスト強化

1. **統合テスト**
   - `test_knowledge_crud_full.py` - ナレッジの更新・削除を含む完全CRUD (18件)
   - `test_rbac_flow.py` - 全ロール(5種類)での詳細な権限テスト (20件)

2. **E2Eテスト**
   - `test_dashboard_flow.py` - ダッシュボードフロー全体 (11件)
   - `test_knowledge_search_flow.py` - 検索フロー全体 (8件)

**合計追加テストケース: 299件**

---

## 貢献

新しいテストを追加する際は、以下のガイドラインに従ってください：

1. 適切なディレクトリに配置
2. 明確なテスト名（何をテストしているか分かる）
3. AAAパターン（Arrange, Act, Assert）
4. テストの独立性を保つ
5. マーカーを適切に設定

詳細は [テスト実行ガイド](/docs/testing-guide.md) を参照してください。
