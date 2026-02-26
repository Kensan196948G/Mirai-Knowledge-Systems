# Phase E-2 N+1クエリ最適化 テスト設計書

## 📋 ドキュメント情報

- **作成日**: 2026-02-16
- **作成者**: test-designer SubAgent
- **バージョン**: 1.0.0
- **対象フェーズ**: Phase E-2（N+1クエリ最適化）
- **対象実装**: data_access.py（P0最適化2件）

---

## 1. テスト概要

### 1.1 テスト対象

| 最適化箇所 | 対象メソッド | 期待効果 | 優先度 |
|-----------|-------------|---------|--------|
| P0-1 | `get_expert_stats()` | クエリ実行回数 31回→3回（90%削減） | P0 |
| P0-2 | `get_project_progress()` | DB側集計でPython側ループ削減（90%改善） | P0 |

### 1.2 テスト種別

| テスト種別 | 既存 | 追加 | 合計 | カバレッジ目標 |
|-----------|------|------|------|---------------|
| ユニットテスト | 10件 | 5件 | 15件 | 95%以上 |
| 統合テスト | 0件 | 5件 | 5件 | 90%以上 |
| E2Eテスト | 0件 | 3件 | 3件 | 主要シナリオ網羅 |
| **合計** | **10件** | **13件** | **23件** | **Overall 93%** |

### 1.3 テスト環境

- **Database**: PostgreSQL 15+（必須: `USE_POSTGRESQL=true`）
- **Python**: 3.14.0
- **Testing Framework**: pytest 9.0.0 + pytest-cov
- **E2E Framework**: Playwright 1.57.0
- **Browser**: Chromium/Firefox/Safari（Playwright）

---

## 2. 既存テスト確認（10件）

### 2.1 TestGetExpertStatsOptimization（6件）

| Test ID | テストケース名 | 検証内容 | 状態 |
|---------|---------------|---------|------|
| #1 | `test_get_expert_stats_query_count` | クエリ実行回数 ≤5回（最適化検証） | ✅ PASS |
| #2 | `test_get_expert_stats_result_format` | 返却値形式（既存API互換性） | ✅ PASS |
| #3 | `test_get_expert_stats_zero_experts` | 専門家0人時の挙動（エッジケース） | ✅ PASS |
| #4 | `test_get_expert_stats_multiple_experts` | 専門家10人時の集計精度 | ✅ PASS |
| #5 | `test_get_expert_stats_no_ratings` | 評価0件の専門家の処理 | ✅ PASS |
| #6 | （未実装） | DB接続エラー時の例外処理 | ❌ 不足 |

### 2.2 TestGetProjectProgressOptimization（4件）

| Test ID | テストケース名 | 検証内容 | 状態 |
|---------|---------------|---------|------|
| #7 | `test_get_project_progress_query_count` | クエリ実行回数 ≤2回（DB側集計検証） | ✅ PASS |
| #8 | `test_get_project_progress_result_format` | 返却値形式検証 | ✅ PASS |
| #9 | `test_get_project_progress_all_completed` | 全タスク完了時の進捗率確認 | ✅ PASS |
| #10 | `test_get_project_progress_mixed_status` | 混在ステータス時の集計確認 | ✅ PASS |
| #11 | `test_get_project_progress_zero_tasks` | タスク0件時のエッジケース | ✅ PASS |

### 2.3 既存テストのカバレッジ分析

**強み**:
- ✅ クエリ実行回数検証（query_counter fixture）
- ✅ 返却値形式検証（既存API互換性）
- ✅ エッジケース検証（0件、複数件、混在ステータス）
- ✅ トランザクション分離（begin_nested, rollback）

**不足点（code-reviewerレビューより）**:
- ⚠️ 異常系テスト不足（DB接続エラー、SQLAlchemyエラー）
- ⚠️ 性能テスト不足（レスポンス時間計測）
- ⚠️ 統合テスト不在（APIエンドポイント）
- ⚠️ E2Eテスト不在（実際のWebUI動作）

---

## 3. 追加ユニットテスト設計（5件）

### Test Case #11: test_get_expert_stats_db_connection_error

**目的**: DB接続エラー時の例外処理検証

**前提条件**:
- PostgreSQLサーバーが停止状態、または
- `get_session_factory()`が`None`を返す状態

**テスト手順**:
1. `get_session_factory()`を`None`を返すようモック
2. `DataAccessLayer(use_postgresql=True)`を初期化
3. `dal.get_expert_stats()`を実行
4. 例外発生を検証
5. ログ出力を確認（エラーメッセージ）

**期待結果**:
- `RuntimeError`または`ConnectionError`が発生
- エラーメッセージ: "Failed to connect to PostgreSQL"
- `db.close()`が実行されている（finallyブロック）

**テストデータ**: なし（エラー再現）

**優先度**: P1（高）

**実装例**:
```python
def test_get_expert_stats_db_connection_error(self, mock_session_factory):
    """DB接続エラー時の例外処理検証"""
    # get_session_factory()がNoneを返す
    mock_session_factory.return_value = None

    dal = DataAccessLayer(use_postgresql=True)

    # 例外発生を期待
    with pytest.raises((RuntimeError, ConnectionError)):
        dal.get_expert_stats()
```

**検証ポイント**:
- [ ] 適切な例外が発生する
- [ ] エラーメッセージが明確
- [ ] リソースリークがない（db.close()実行）

---

### Test Case #12: test_get_expert_stats_empty_database

**目的**: 空データベース時の挙動検証（全テーブル空）

**前提条件**:
- `Expert`テーブル: 0件
- `ExpertRating`テーブル: 0件
- `Consultation`テーブル: 0件

**テスト手順**:
1. 空のデータベースを準備（ロールバック後）
2. `dal.get_expert_stats()`を実行
3. 返却値を検証

**期待結果**:
```json
{
  "experts": []
}
```

**テストデータ**: なし（空データベース）

**優先度**: P2（中）

**実装例**:
```python
def test_get_expert_stats_empty_database(self, db_session, mock_session_factory):
    """空データベース時の挙動検証"""
    # データ未登録（ロールバック後の空状態）
    dal = DataAccessLayer(use_postgresql=True)
    stats = dal.get_expert_stats()

    assert stats == {"experts": []}
    # または
    assert "experts" in stats
    assert len(stats["experts"]) == 0
```

**検証ポイント**:
- [ ] 空リスト返却
- [ ] エラーが発生しない
- [ ] パフォーマンス劣化なし

**備考**: 既存の`test_get_expert_stats_zero_experts`と類似だが、全テーブルが空である点を明示的に検証

---

### Test Case #13: test_get_project_progress_invalid_project_id

**目的**: 存在しないプロジェクトID指定時の挙動検証

**前提条件**:
- `project_id = 9999`（存在しない）
- `ProjectTask`テーブルに該当データなし

**テスト手順**:
1. `dal.get_project_progress(9999)`を実行
2. 返却値を検証

**期待結果**:
```json
{
  "total_tasks": 0,
  "completed_tasks": 0,
  "in_progress_tasks": 0,
  "pending_tasks": 0,
  "progress_percentage": 0
}
```

**テストデータ**: なし（存在しないID）

**優先度**: P1（高）

**実装例**:
```python
def test_get_project_progress_invalid_project_id(self, db_session, mock_session_factory):
    """存在しないプロジェクトID指定時の挙動検証"""
    project_id = 9999  # 存在しないID

    dal = DataAccessLayer(use_postgresql=True)
    progress = dal.get_project_progress(project_id)

    # デフォルト値返却（エラーなし）
    assert progress["total_tasks"] == 0
    assert progress.get("completed_tasks", 0) == 0
    assert progress["progress_percentage"] == 0
```

**検証ポイント**:
- [ ] デフォルト値返却（エラーなし）
- [ ] 0除算エラー（ZeroDivisionError）が発生しない
- [ ] NULL処理が適切

---

### Test Case #14: test_get_project_progress_null_progress_percentage

**目的**: タスクの`progress_percentage`がNULLの場合の集計検証

**前提条件**:
- `ProjectTask.progress_percentage = NULL`（DBにNULL許可）
- `status = 'in_progress'`

**テスト手順**:
1. `progress_percentage = NULL`のタスクを作成
2. `dal.get_project_progress(project_id)`を実行
3. 集計結果を検証

**期待結果**:
- `average_progress = 0`（NULLを0扱い）
- または`COALESCE(progress_percentage, 0)`による集計

**テストデータ**:
```python
tasks = [
    {"task_name": "Task 1", "status": "in_progress", "progress_percentage": None},
    {"task_name": "Task 2", "status": "in_progress", "progress_percentage": 50},
]
```

**優先度**: P2（中）

**実装例**:
```python
def test_get_project_progress_null_progress_percentage(self, db_session, mock_session_factory):
    """progress_percentageがNULLの場合の集計検証"""
    project_id = 1

    # progress_percentage = NULL のタスク
    task1 = ProjectTask(
        project_id=project_id,
        task_name="Task 1",
        description="Test",
        status="in_progress",
        progress_percentage=None,  # NULL
    )
    db_session.add(task1)

    # progress_percentage = 50 のタスク
    task2 = ProjectTask(
        project_id=project_id,
        task_name="Task 2",
        description="Test",
        status="in_progress",
        progress_percentage=50,
    )
    db_session.add(task2)
    db_session.commit()

    dal = DataAccessLayer(use_postgresql=True)
    progress = dal.get_project_progress(project_id)

    # NULLを0として集計: (0 + 50) / 2 = 25
    assert progress["total_tasks"] == 2
    expected_avg = 25  # または実装による
    assert progress["progress_percentage"] == expected_avg
```

**検証ポイント**:
- [ ] NULL値の適切な処理（0扱い）
- [ ] 平均計算の正確性
- [ ] SQLエラーが発生しない

**備考**: SQLAlchemyの`func.avg()`がNULLをスキップするか、COALESCE使用かを検証

---

### Test Case #15: test_get_expert_stats_performance_10_experts

**目的**: 専門家10人時のクエリ実行回数とレスポンス時間検証

**前提条件**:
- 専門家: 10人
- 各専門家の評価: 5件
- 各専門家の相談: 3件

**テスト手順**:
1. テストデータを作成（専門家10人×評価5件×相談3件 = 80件）
2. `query_counter`をリセット
3. レスポンス時間計測開始
4. `dal.get_expert_stats()`を実行
5. レスポンス時間計測終了
6. クエリ実行回数とレスポンス時間を検証

**期待結果**:
- クエリ実行回数: ≤3回（最適化済み）
- レスポンス時間: < 100ms（開発環境基準）
- メモリ使用量: 約50%削減（既存実装比較）

**テストデータ**:
```python
experts = 10
ratings_per_expert = 5
consultations_per_expert = 3
```

**優先度**: P0（最高）

**実装例**:
```python
import time

def test_get_expert_stats_performance_10_experts(
    self, db_session, query_counter, mock_session_factory
):
    """専門家10人時のパフォーマンス検証"""
    # テストデータ作成
    for i in range(10):
        user = User(
            username=f"user_{i}",
            full_name=f"Expert {i}",
            email=f"expert{i}@example.com",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.flush()

        expert = Expert(
            user_id=user.id,
            specialization="Construction",
            experience_years=5 + i,
            is_available=True,
        )
        db_session.add(expert)
        db_session.flush()

        # 各専門家に5件の評価
        for j in range(5):
            rating = ExpertRating(
                expert_id=expert.id,
                user_id=user.id,
                rating=4 + (j % 2),
                review="Good",
            )
            db_session.add(rating)

        # 各専門家に3件の相談
        for k in range(3):
            consultation = Consultation(
                expert_id=user.id,
                requester_id=user.id,
                title=f"Consultation {i}_{k}",
                question="Test question",
                category="Technical",
                status="completed",
            )
            db_session.add(consultation)

    db_session.commit()

    # クエリカウンタリセット
    query_counter.clear()

    # レスポンス時間計測開始
    start_time = time.time()

    dal = DataAccessLayer(use_postgresql=True)
    stats = dal.get_expert_stats()

    # レスポンス時間計測終了
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # ms

    # 結果検証
    assert len(stats["experts"]) == 10

    # クエリ実行回数検証（最適化版: ≤3回）
    query_count = len(query_counter)
    assert query_count <= 3, f"Expected ≤3 queries, got {query_count}"

    # レスポンス時間検証（開発環境基準）
    assert response_time < 100, f"Expected <100ms, got {response_time:.2f}ms"

    # ログ出力（統計情報）
    print(f"\n[Performance] Queries: {query_count}, Response Time: {response_time:.2f}ms")
```

**検証ポイント**:
- [ ] クエリ実行回数 ≤3回
- [ ] レスポンス時間 < 100ms
- [ ] メモリリークなし
- [ ] パフォーマンス統計ログ出力

**備考**: 本番環境では閾値を調整（例: 50ms）

---

## 4. 統合テスト設計（5件）

### Test Case #16: test_api_get_expert_stats_endpoint

**テスト種別**: 統合テスト（API）

**目的**: `/api/v1/experts/stats`エンドポイントの正常動作検証

**前提条件**:
- JWT認証トークン: 有効なadminトークン
- 専門家: 10人登録済み

**テスト手順**:
1. テストデータ作成（専門家10人）
2. JWT認証トークン取得（ログインAPI）
3. `GET /api/v1/experts/stats`をリクエスト（Authorization: Bearer {token}）
4. レスポンスを検証

**期待結果**:
- **HTTP Status**: 200 OK
- **Response Body**:
```json
{
  "experts": [
    {
      "expert_id": 1,
      "name": "Expert 0",
      "specialization": "Construction",
      "consultation_count": 3,
      "average_rating": 4.5,
      "total_ratings": 5,
      "experience_years": 5,
      "is_available": true
    },
    ...
  ]
}
```
- **Response Time**: < 200ms

**テストデータ**: Test Case #15と同じ

**優先度**: P0（最高）

**実装例**:
```python
# backend/tests/integration/test_expert_stats_api.py

import pytest
from flask import Flask
from app_v2 import app

@pytest.fixture
def client():
    """Flaskテストクライアント"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_get_expert_stats_endpoint(client, db_session):
    """GET /api/v1/experts/stats エンドポイントの正常動作検証"""
    # 1. テストデータ作成（省略）

    # 2. JWT認証トークン取得
    login_response = client.post('/api/v1/auth/login', json={
        "username": "admin",
        "password": "admin123"
    })
    assert login_response.status_code == 200
    token = login_response.get_json()["access_token"]

    # 3. GET /api/v1/experts/stats
    response = client.get(
        '/api/v1/experts/stats',
        headers={"Authorization": f"Bearer {token}"}
    )

    # 4. レスポンス検証
    assert response.status_code == 200
    data = response.get_json()
    assert "experts" in data
    assert len(data["experts"]) == 10

    expert_0 = data["experts"][0]
    assert "expert_id" in expert_0
    assert "name" in expert_0
    assert "specialization" in expert_0
    assert "consultation_count" in expert_0
    assert "average_rating" in expert_0
```

**検証ポイント**:
- [ ] HTTP 200 OK
- [ ] JSON形式レスポンス
- [ ] 統計データ正確性
- [ ] レスポンス時間 < 200ms

---

### Test Case #17: test_api_get_project_progress_endpoint

**テスト種別**: 統合テスト（API）

**目的**: `/api/v1/projects/{id}/progress`エンドポイントの正常動作検証

**前提条件**:
- JWT認証トークン: 有効なadminトークン
- プロジェクト: 1件登録済み（project_id=1）
- タスク: 10件登録済み（完了3件、進行中5件、保留2件）

**テスト手順**:
1. テストデータ作成（プロジェクト1件、タスク10件）
2. JWT認証トークン取得
3. `GET /api/v1/projects/1/progress`をリクエスト
4. レスポンスを検証

**期待結果**:
- **HTTP Status**: 200 OK
- **Response Body**:
```json
{
  "total_tasks": 10,
  "completed_tasks": 3,
  "in_progress_tasks": 5,
  "pending_tasks": 2,
  "progress_percentage": 30
}
```
- **Response Time**: < 100ms

**テストデータ**:
```python
tasks = [
    {"status": "completed", "progress_percentage": 100},  # 3件
    {"status": "in_progress", "progress_percentage": 50}, # 5件
    {"status": "pending", "progress_percentage": 0},      # 2件
]
```

**優先度**: P0（最高）

**実装例**:
```python
def test_api_get_project_progress_endpoint(client, db_session):
    """GET /api/v1/projects/{id}/progress エンドポイントの正常動作検証"""
    # 1. テストデータ作成（省略）

    # 2. JWT認証トークン取得（省略）

    # 3. GET /api/v1/projects/1/progress
    response = client.get(
        '/api/v1/projects/1/progress',
        headers={"Authorization": f"Bearer {token}"}
    )

    # 4. レスポンス検証
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_tasks"] == 10
    assert data["completed_tasks"] == 3
    assert data["in_progress_tasks"] == 5
    assert data["pending_tasks"] == 2
    assert data["progress_percentage"] == 30
```

**検証ポイント**:
- [ ] HTTP 200 OK
- [ ] 進捗率計算正確性
- [ ] ステータス別カウント正確性

---

### Test Case #18: test_api_authentication_required

**テスト種別**: 統合テスト（認証）

**目的**: JWT認証なしアクセス時の401エラー検証

**前提条件**:
- JWT認証トークン: なし（Authorizationヘッダーなし）

**テスト手順**:
1. `GET /api/v1/experts/stats`をリクエスト（Authorizationヘッダーなし）
2. レスポンスを検証

**期待結果**:
- **HTTP Status**: 401 Unauthorized
- **Response Body**:
```json
{
  "msg": "Missing Authorization Header"
}
```

**優先度**: P1（高）

**実装例**:
```python
def test_api_authentication_required(client):
    """JWT認証なしアクセス時の401エラー検証"""
    # Authorizationヘッダーなし
    response = client.get('/api/v1/experts/stats')

    assert response.status_code == 401
    data = response.get_json()
    assert "msg" in data
    assert "Authorization" in data["msg"]
```

**検証ポイント**:
- [ ] HTTP 401 Unauthorized
- [ ] エラーメッセージ明確

---

### Test Case #19: test_fallback_to_old_implementation

**テスト種別**: 統合テスト（フォールバック）

**目的**: 最適化失敗時の既存実装フォールバック検証（Feature Flag）

**前提条件**:
- SQLAlchemyサブクエリエラーを模擬
- Feature Flag: `ENABLE_QUERY_OPTIMIZATION=true`（環境変数）

**テスト手順**:
1. SQLAlchemyクエリエラーを発生させる（モック）
2. `dal.get_expert_stats()`を実行
3. エラーログ出力を確認
4. 既存実装で継続（フォールバック）

**期待結果**:
- エラーログ: "Query optimization failed, falling back to old implementation"
- 既存実装で正常に動作
- エラーが発生しない（ユーザー影響なし）

**優先度**: P2（中）

**実装例**:
```python
def test_fallback_to_old_implementation(self, db_session, mock_session_factory, caplog):
    """最適化失敗時のフォールバック検証"""
    # SQLAlchemyエラーを模擬（モック）
    with patch('data_access.DataAccessLayer.get_expert_stats') as mock_stats:
        mock_stats.side_effect = Exception("SQLAlchemy error")

        dal = DataAccessLayer(use_postgresql=True)

        # フォールバック実装で継続
        stats = dal.get_expert_stats_fallback()  # 既存実装

        # エラーログ確認
        assert "falling back to old implementation" in caplog.text

        # 正常動作確認
        assert "experts" in stats
```

**検証ポイント**:
- [ ] エラーログ出力
- [ ] フォールバック実装で継続
- [ ] ユーザー影響なし

**備考**: Feature Flag実装が必要（環境変数`ENABLE_QUERY_OPTIMIZATION`）

---

### Test Case #20: test_backward_compatibility_json_mode

**テスト種別**: 統合テスト（後方互換性）

**目的**: JSONモード（開発環境）での後方互換性検証

**前提条件**:
- `use_postgresql=False`（JSONベース実装）

**テスト手順**:
1. `DataAccessLayer(use_postgresql=False)`を初期化
2. `dal.get_expert_stats()`を実行
3. 既存のJSONベース実装で動作確認

**期待結果**:
- JSONファイル読み込み成功
- 既存実装で正常に動作
- 最適化なし（PostgreSQLモードのみ最適化）

**優先度**: P2（中）

**実装例**:
```python
def test_backward_compatibility_json_mode(self):
    """JSONモード（開発環境）での後方互換性検証"""
    # use_postgresql=False（JSONベース）
    dal = DataAccessLayer(use_postgresql=False)
    stats = dal.get_expert_stats()

    # 既存実装で動作確認
    assert "experts" in stats
    # JSONモードでは最適化なし（既存実装）
```

**検証ポイント**:
- [ ] JSONモードで正常動作
- [ ] PostgreSQLモードと独立
- [ ] 既存実装で動作

---

## 5. E2Eテスト設計（3件）

### Test Case #21: test_e2e_expert_stats_page_load

**テスト種別**: E2Eテスト（Playwright）

**目的**: 専門家統計ページの読み込み速度検証

**前提条件**:
- 専門家: 10人登録済み
- ブラウザ: Chromium
- ログイン済み

**テスト手順**:
1. Playwrightブラウザ起動
2. ログインページにアクセス
3. ログイン（admin/admin123）
4. 専門家統計ページに遷移
5. ページ読み込み時間計測
6. Lighthouse Performance スコア取得

**期待結果**:
- ページ読み込み時間: < 1秒
- Lighthouse Performance スコア: 90+
- 専門家統計テーブル表示確認

**優先度**: P1（高）

**実装例**:
```python
# backend/tests/e2e/test_expert_stats_page.spec.py

import pytest
from playwright.sync_api import sync_playwright

def test_e2e_expert_stats_page_load():
    """専門家統計ページの読み込み速度検証"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # 1. ログイン
        page.goto("http://localhost:5200/login.html")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin123")

        # 2. ページ読み込み時間計測開始
        start_time = time.time()
        page.click('button[type="submit"]')

        # 3. 専門家統計ページ遷移
        page.goto("http://localhost:5200/expert-stats.html")
        page.wait_for_selector("table.expert-stats-table")

        # 4. ページ読み込み時間計測終了
        end_time = time.time()
        load_time = end_time - start_time

        # 5. 検証
        assert load_time < 1.0, f"Expected <1s, got {load_time:.2f}s"

        # 6. 専門家統計テーブル表示確認
        table = page.query_selector("table.expert-stats-table")
        assert table is not None

        browser.close()
```

**検証ポイント**:
- [ ] ページ読み込み時間 < 1秒
- [ ] Lighthouse Performance 90+
- [ ] UI要素表示確認

**備考**: Lighthouse スコア取得にはPlaywright Lighthouse Plugin使用

---

### Test Case #22: test_e2e_project_progress_realtime_update

**テスト種別**: E2Eテスト（Playwright）

**目的**: プロジェクト進捗のリアルタイム更新検証

**前提条件**:
- プロジェクト: 1件登録済み
- タスク: 10件登録済み（完了3件、進行中5件、保留2件）
- WebSocket/SSE対応済み（リアルタイム更新機能）

**テスト手順**:
1. プロジェクト詳細ページ表示
2. 現在の進捗率取得（30%）
3. タスク1件を「完了」に変更（API操作）
4. ページリロードなしで進捗率自動更新確認（40%）

**期待結果**:
- 進捗率: 30% → 40%（リロードなし）
- 更新時間: < 2秒
- WebSocket/SSE通知受信確認

**優先度**: P2（中）

**実装例**:
```python
def test_e2e_project_progress_realtime_update():
    """プロジェクト進捗のリアルタイム更新検証"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # 1. プロジェクト詳細ページ表示
        page.goto("http://localhost:5200/project-detail.html?id=1")
        page.wait_for_selector(".progress-percentage")

        # 2. 現在の進捗率取得
        progress_before = page.inner_text(".progress-percentage")
        assert "30%" in progress_before

        # 3. タスク1件を「完了」に変更（API操作）
        page.evaluate("""
            fetch('/api/v1/tasks/1', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + localStorage.getItem('token')
                },
                body: JSON.stringify({"status": "completed"})
            });
        """)

        # 4. リアルタイム更新待機（WebSocket/SSE）
        page.wait_for_function("document.querySelector('.progress-percentage').innerText.includes('40%')", timeout=2000)

        # 5. 検証
        progress_after = page.inner_text(".progress-percentage")
        assert "40%" in progress_after

        browser.close()
```

**検証ポイント**:
- [ ] リロードなしで更新
- [ ] 更新時間 < 2秒
- [ ] WebSocket/SSE通知受信

**備考**: WebSocket/SSE未実装の場合はスキップ（`pytest.skip()`）

---

### Test Case #23: test_e2e_large_dataset_performance

**テスト種別**: E2Eテスト（Playwright）

**目的**: 大量データ時のパフォーマンス検証

**前提条件**:
- 専門家: 50人
- 各専門家の評価: 20件
- 各専門家の相談: 10件
- 合計: 専門家50人×評価20件×相談10件 = 1,500件

**テスト手順**:
1. テストデータ作成（専門家50人×評価20件×相談10件）
2. 専門家統計ページにアクセス
3. ページ読み込み時間計測
4. テーブル表示確認

**期待結果**:
- ページ読み込み時間: < 2秒
- テーブル表示: 50人全員表示
- スクロール可能

**優先度**: P1（高）

**実装例**:
```python
def test_e2e_large_dataset_performance():
    """大量データ時のパフォーマンス検証"""
    # 1. テストデータ作成（専門家50人×評価20件×相談10件）
    # （省略: APIまたはDB直接登録）

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # 2. 専門家統計ページにアクセス
        start_time = time.time()
        page.goto("http://localhost:5200/expert-stats.html")
        page.wait_for_selector("table.expert-stats-table")
        end_time = time.time()

        load_time = end_time - start_time

        # 3. 検証
        assert load_time < 2.0, f"Expected <2s, got {load_time:.2f}s"

        # 4. テーブル表示確認（50人全員）
        rows = page.query_selector_all("table.expert-stats-table tbody tr")
        assert len(rows) == 50

        browser.close()
```

**検証ポイント**:
- [ ] ページ読み込み時間 < 2秒
- [ ] 50人全員表示
- [ ] UIフリーズなし

---

## 6. テストデータ設計

### 6.1 データセット1: 専門家10人（標準）

**用途**: ユニットテスト、統合テスト、E2Eテスト

**データ構成**:
```python
# 専門家10人
experts = [
    {
        "user_id": "user_00",
        "username": "user_00",
        "full_name": "Expert 0",
        "email": "expert0@example.com",
        "specialization": "構造設計",
        "experience_years": 5,
        "is_available": True,
    },
    {
        "user_id": "user_01",
        "username": "user_01",
        "full_name": "Expert 1",
        "email": "expert1@example.com",
        "specialization": "土質調査",
        "experience_years": 6,
        "is_available": True,
    },
    # ... (省略、合計10人)
]

# 各専門家に評価5件
ratings = [
    {"expert_id": "expert_00", "rating": 5.0, "review": "Excellent"},
    {"expert_id": "expert_00", "rating": 4.5, "review": "Very Good"},
    {"expert_id": "expert_00", "rating": 4.0, "review": "Good"},
    {"expert_id": "expert_00", "rating": 5.0, "review": "Excellent"},
    {"expert_id": "expert_00", "rating": 4.5, "review": "Very Good"},
    # ... (専門家00の評価5件)
    # ... (専門家01〜09も同様)
]

# 各専門家に相談3件
consultations = [
    {"expert_id": "user_00", "title": "Consultation 0_0", "status": "completed"},
    {"expert_id": "user_00", "title": "Consultation 0_1", "status": "completed"},
    {"expert_id": "user_00", "title": "Consultation 0_2", "status": "completed"},
    # ... (専門家00の相談3件)
    # ... (専門家01〜09も同様)
]
```

**統計サマリー**:
- 専門家: 10人
- 評価: 50件（10人×5件）
- 相談: 30件（10人×3件）
- 合計: 90件

---

### 6.2 データセット2: 専門家50人（大量データ）

**用途**: E2Eテスト（大量データパフォーマンス検証）

**データ構成**:
```python
# 専門家50人
experts = [
    {
        "user_id": f"user_{i:03d}",
        "username": f"user_{i:03d}",
        "full_name": f"Expert {i}",
        "email": f"expert{i}@example.com",
        "specialization": ["構造設計", "土質調査", "施工管理", "測量", "CAD"][i % 5],
        "experience_years": 5 + (i % 10),
        "is_available": True,
    }
    for i in range(50)
]

# 各専門家に評価20件
ratings = [
    {
        "expert_id": f"expert_{i:03d}",
        "rating": 4.0 + (j % 2) * 0.5,
        "review": "Test review",
    }
    for i in range(50)
    for j in range(20)
]

# 各専門家に相談10件
consultations = [
    {
        "expert_id": f"user_{i:03d}",
        "title": f"Consultation {i}_{k}",
        "status": ["completed", "in_progress"][k % 2],
    }
    for i in range(50)
    for k in range(10)
]
```

**統計サマリー**:
- 専門家: 50人
- 評価: 1,000件（50人×20件）
- 相談: 500件（50人×10件）
- 合計: 1,550件

---

### 6.3 データセット3: プロジェクト1件、タスク10件（標準）

**用途**: 統合テスト、E2Eテスト（プロジェクト進捗検証）

**データ構成**:
```python
# プロジェクト1件
project = {
    "project_id": 1,
    "project_name": "橋梁建設プロジェクト",
    "description": "Test project",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
}

# タスク10件
tasks = [
    # 完了タスク（3件）
    {"project_id": 1, "task_name": "Task 0", "status": "completed", "progress_percentage": 100},
    {"project_id": 1, "task_name": "Task 1", "status": "completed", "progress_percentage": 100},
    {"project_id": 1, "task_name": "Task 2", "status": "completed", "progress_percentage": 100},
    # 進行中タスク（5件）
    {"project_id": 1, "task_name": "Task 3", "status": "in_progress", "progress_percentage": 50},
    {"project_id": 1, "task_name": "Task 4", "status": "in_progress", "progress_percentage": 50},
    {"project_id": 1, "task_name": "Task 5", "status": "in_progress", "progress_percentage": 50},
    {"project_id": 1, "task_name": "Task 6", "status": "in_progress", "progress_percentage": 50},
    {"project_id": 1, "task_name": "Task 7", "status": "in_progress", "progress_percentage": 50},
    # 保留タスク（2件）
    {"project_id": 1, "task_name": "Task 8", "status": "pending", "progress_percentage": 0},
    {"project_id": 1, "task_name": "Task 9", "status": "pending", "progress_percentage": 0},
]
```

**統計サマリー**:
- プロジェクト: 1件
- タスク: 10件（完了3件、進行中5件、保留2件）
- 進捗率: 30%

---

### 6.4 データ生成スクリプト（オプション）

**ファイル**: `backend/tests/fixtures/generate_test_data.py`

**機能**:
- データセット1〜3の自動生成
- PostgreSQLへの直接挿入
- テストデータのロールバック（クリーンアップ）

**実装例**:
```python
# backend/tests/fixtures/generate_test_data.py

from database import get_session_factory
from models import User, Expert, ExpertRating, Consultation, ProjectTask

def generate_expert_dataset_10():
    """データセット1: 専門家10人を生成"""
    factory = get_session_factory()
    db = factory()

    for i in range(10):
        user = User(
            username=f"user_{i:02d}",
            full_name=f"Expert {i}",
            email=f"expert{i}@example.com",
            password_hash="hash",
        )
        db.add(user)
        db.flush()

        expert = Expert(
            user_id=user.id,
            specialization=["構造設計", "土質調査", "施工管理", "測量", "CAD"][i % 5],
            experience_years=5 + i,
            is_available=True,
        )
        db.add(expert)
        db.flush()

        # 評価5件
        for j in range(5):
            rating = ExpertRating(
                expert_id=expert.id,
                user_id=user.id,
                rating=4.0 + (j % 2) * 0.5,
                review="Test review",
            )
            db.add(rating)

        # 相談3件
        for k in range(3):
            consultation = Consultation(
                expert_id=user.id,
                requester_id=user.id,
                title=f"Consultation {i}_{k}",
                question="Test question",
                category="Technical",
                status="completed",
            )
            db.add(consultation)

    db.commit()
    db.close()

if __name__ == "__main__":
    generate_expert_dataset_10()
    print("データセット1（専門家10人）を生成しました。")
```

**使用方法**:
```bash
python backend/tests/fixtures/generate_test_data.py
```

---

## 7. テスト実行計画

### 7.1 Phase 1: ユニットテスト実装（Week 1）

**期間**: 2日間

**タスク**:
1. Test Case #11-15の実装
2. `test_data_access_optimization.py`に追加
3. カバレッジ計測（目標: 95%以上）

**成果物**:
- `test_data_access_optimization.py`（追加5件、合計15件）
- カバレッジレポート（pytest-cov）

**実行コマンド**:
```bash
cd backend
pytest tests/unit/test_data_access_optimization.py -v --cov=data_access --cov-report=html
```

**成功基準**:
- [ ] 15件すべてPASS
- [ ] カバレッジ 95%以上
- [ ] クエリ実行回数検証PASS

---

### 7.2 Phase 2: 統合テスト実装（Week 1-2）

**期間**: 3日間

**タスク**:
1. Test Case #16-20の実装
2. `backend/tests/integration/test_expert_stats_api.py`作成
3. API動作確認

**成果物**:
- `test_expert_stats_api.py`（新規5件）
- 統合テストレポート

**実行コマンド**:
```bash
cd backend
pytest tests/integration/test_expert_stats_api.py -v
```

**成功基準**:
- [ ] 5件すべてPASS
- [ ] HTTP 200 OK確認
- [ ] API正常動作確認

---

### 7.3 Phase 3: E2Eテスト実装（Week 2）

**期間**: 2日間

**タスク**:
1. Test Case #21-23の実装
2. `backend/tests/e2e/test_expert_stats_page.spec.py`作成
3. Playwright実行

**成果物**:
- `test_expert_stats_page.spec.py`（新規3件）
- E2Eテストレポート
- Lighthouse スコアレポート

**実行コマンド**:
```bash
cd backend
pytest tests/e2e/test_expert_stats_page.spec.py -v --headed
```

**成功基準**:
- [ ] 3件すべてPASS
- [ ] ページ読み込み時間 < 1秒
- [ ] Lighthouse Performance 90+

---

### 7.4 全テスト実行（Week 2）

**実行コマンド**:
```bash
cd backend
pytest tests/ -v --cov=data_access --cov-report=html
```

**成功基準**:
- [ ] 23件すべてPASS（ユニット15 + 統合5 + E2E3）
- [ ] カバレッジ 93%以上
- [ ] CI/CD統合成功

---

## 8. テストカバレッジ目標

### 8.1 ユニットテストカバレッジ

| ファイル | 現状 | 目標 | 対象行数 |
|---------|------|------|----------|
| data_access.py | 90% | 95%以上 | 2,500行 |
| models.py | 85% | 90%以上 | 800行 |

**未カバー箇所（現状）**:
- DB接続エラー処理（Test Case #11で追加）
- NULL値処理（Test Case #14で追加）

**カバレッジ向上施策**:
- Test Case #11-15の実装
- エッジケーステスト追加

---

### 8.2 統合テストカバレッジ

| API | 現状 | 目標 | テスト件数 |
|-----|------|------|-----------|
| GET /api/v1/experts/stats | 0件 | 2件 | Test Case #16, #18 |
| GET /api/v1/projects/{id}/progress | 0件 | 1件 | Test Case #17 |

**カバレッジ向上施策**:
- Test Case #16-18の実装
- 認証テスト追加

---

### 8.3 E2Eテストカバレッジ

| シナリオ | 現状 | 目標 | テスト件数 |
|---------|------|------|-----------|
| 専門家統計ページ表示 | 0件 | 1件 | Test Case #21 |
| プロジェクト進捗更新 | 0件 | 1件 | Test Case #22 |
| 大量データパフォーマンス | 0件 | 1件 | Test Case #23 |

**カバレッジ向上施策**:
- Test Case #21-23の実装
- Lighthouse スコア計測

---

## 9. 完了基準（Definition of Done）

### 9.1 ユニットテスト（15件）

- [ ] Test Case #1-15 すべてPASS
- [ ] カバレッジ 95%以上
- [ ] クエリ実行回数検証PASS（≤3回, ≤2回）
- [ ] レスポンス時間検証PASS（< 100ms）

### 9.2 統合テスト（5件）

- [ ] Test Case #16-20 すべてPASS
- [ ] HTTP 200 OK確認
- [ ] API正常動作確認
- [ ] JWT認証テストPASS

### 9.3 E2Eテスト（3件）

- [ ] Test Case #21-23 すべてPASS
- [ ] ページ読み込み時間 < 1秒（標準）
- [ ] ページ読み込み時間 < 2秒（大量データ）
- [ ] Lighthouse Performance 90+

### 9.4 ドキュメント

- [ ] テスト設計書作成（本ドキュメント）
- [ ] テストケース仕様書作成（オプション）
- [ ] テスト実行レポート作成

### 9.5 CI/CD統合

- [ ] GitHub Actions統合
- [ ] テスト自動実行成功
- [ ] カバレッジレポート自動生成

---

## 10. リスクと対策

### 10.1 リスク1: テスト環境準備遅延

**リスク**: PostgreSQL環境構築遅延によるテスト実装遅延

**対策**:
- Dockerコンテナ使用（docker-compose.yml）
- CI/CD環境でPostgreSQLサービス起動

**影響度**: 中

---

### 10.2 リスク2: E2Eテスト不安定性

**リスク**: Playwrightテストがタイミング依存で不安定

**対策**:
- `page.wait_for_selector()`による明示的待機
- リトライ機構実装（3回まで）
- `--headed`オプションでデバッグ

**影響度**: 低

---

### 10.3 リスク3: パフォーマンステスト基準曖昧

**リスク**: レスポンス時間基準（< 100ms）が環境依存

**対策**:
- 環境変数で閾値設定（`RESPONSE_TIME_THRESHOLD_MS`）
- CI環境では閾値を緩和（200ms）
- 本番環境では厳格化（50ms）

**影響度**: 低

---

## 11. 参考資料

### 11.1 技術ドキュメント

- **pytest Documentation**: https://docs.pytest.org/
- **Playwright Python**: https://playwright.dev/python/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Flask Testing**: https://flask.palletsprojects.com/en/2.3.x/testing/

### 11.2 プロジェクト内部資料

- **code-reviewerレビューレポート**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/reviews/E2_code_review.json`
- **既存テストファイル**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/tests/unit/test_data_access_optimization.py`
- **データアクセスレイヤー**: `/mnt/LinuxHDD/Mirai-Knowledge-Systems/backend/data_access.py`

### 11.3 過去の参照実装

- **Phase D-3 MFA Tests**: `backend/tests/unit/test_totp_manager.py`（19件）
- **Phase D-4 MS365 Tests**: `backend/tests/unit/test_ms365_sync_service.py`（16件）
- **Phase D-5 PWA E2E Tests**: `backend/tests/e2e/pwa-functionality.spec.js`（11件）

---

## 12. 付録

### 12.1 pytest fixture一覧

| Fixture名 | 目的 | 提供内容 |
|----------|------|---------|
| `use_real_db` | PostgreSQL使用判定 | 環境変数`USE_POSTGRESQL`読み取り |
| `db_session` | テスト用DBセッション | トランザクション分離（rollback保証） |
| `query_counter` | クエリ実行回数カウント | SQLAlchemyイベントリスナー |
| `mock_session_factory` | DataAccessLayer用モック | テスト分離 |
| `client` | Flaskテストクライアント | API統合テスト用 |

### 12.2 テスト環境変数

| 変数名 | 用途 | デフォルト値 | 例 |
|--------|------|-------------|---|
| `USE_POSTGRESQL` | PostgreSQL使用判定 | `false` | `true` |
| `RESPONSE_TIME_THRESHOLD_MS` | レスポンス時間閾値 | `100` | `200` |
| `ENABLE_QUERY_OPTIMIZATION` | クエリ最適化ON/OFF | `true` | `false` |

### 12.3 テスト実行オプション

```bash
# 基本実行
pytest tests/unit/test_data_access_optimization.py -v

# カバレッジ計測
pytest tests/unit/test_data_access_optimization.py -v --cov=data_access --cov-report=html

# 特定テストのみ実行
pytest tests/unit/test_data_access_optimization.py::TestGetExpertStatsOptimization::test_get_expert_stats_query_count -v

# ログ出力表示
pytest tests/unit/test_data_access_optimization.py -v -s

# 失敗時即座停止
pytest tests/unit/test_data_access_optimization.py -v -x

# 並列実行（pytest-xdist）
pytest tests/unit/test_data_access_optimization.py -v -n 4

# E2Eテスト（ブラウザ表示）
pytest tests/e2e/test_expert_stats_page.spec.py -v --headed
```

---

## 13. 変更履歴

| バージョン | 日付 | 作成者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-02-16 | test-designer SubAgent | 初版作成 |

---

## 14. 承認

| 役割 | 氏名 | 承認日 | 署名 |
|------|------|--------|------|
| test-designer SubAgent | Claude Sonnet 4.5 | 2026-02-16 | ✅ |
| test-reviewer SubAgent | （レビュー待ち） | - | - |
| Human | （承認待ち） | - | - |

---

**ドキュメント終了**
