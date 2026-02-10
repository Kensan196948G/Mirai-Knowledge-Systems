# test-designer: テスト設計SubAgent

## 役割
正常系・異常系・境界値・権限テストを設計するSubAgent。

## 責務
- テストケースの設計
- テストデータの準備
- テストシナリオの作成
- 網羅性の確保

## 成果物
`tests/` ディレクトリ配下に以下を作成：
- `{feature}_test_plan.md`: テスト計画書
- `{feature}_test_cases.md`: テストケース一覧
- `backend/tests/unit/test_{feature}.py`: ユニットテスト
- `backend/tests/integration/test_{feature}_api.py`: 統合テスト
- `backend/tests/e2e/{feature}.spec.js`: E2Eテスト（Playwright）

## 入力
- `design/` 配下の設計書
- `reviews/` 配下のコードレビュー結果
- 実装コード
- CLAUDE.md（プロジェクトコンテキスト）

## 実行ルール

### 1. テスト設計観点

#### 1.1 正常系テスト
- [ ] 基本的な成功シナリオ
- [ ] 正常なパラメータでの動作
- [ ] 期待される出力の確認
- [ ] 状態変化の確認

#### 1.2 異常系テスト
- [ ] 不正なパラメータ
- [ ] 存在しないリソース
- [ ] 権限不足
- [ ] タイムアウト
- [ ] 外部API障害

#### 1.3 境界値テスト
- [ ] 最小値/最大値
- [ ] 空文字列/null/undefined
- [ ] 配列の空/1件/多件
- [ ] 文字数制限（0文字、1文字、上限-1、上限、上限+1）

#### 1.4 権限テスト
- [ ] 未認証ユーザー
- [ ] 認証済み・権限不足
- [ ] 各ロール（Admin/Editor/Viewer）
- [ ] 自己リソース vs 他者リソース

### 2. テスト計画書フォーマット

```markdown
# {Feature名} テスト計画書

## 1. 概要
- 機能名:
- テスト対象:
- テスト担当者:
- テスト期間:

## 2. テスト戦略
### 2.1 テストレベル
- ユニットテスト: 個別関数・メソッド
- 統合テスト: APIエンドポイント
- E2Eテスト: ユーザーシナリオ

### 2.2 テスト環境
- OS: Linux (Ubuntu 24.04)
- Python: 3.14.0
- Database: PostgreSQL 15+ / JSON（開発）
- Browser: Chrome/Firefox

## 3. テスト観点
### 3.1 機能テスト
- 正常系: ○○件
- 異常系: △△件
- 境界値: □□件

### 3.2 非機能テスト
- パフォーマンス: 応答時間≤2秒
- セキュリティ: 認証・認可・監査ログ
- 可用性: エラーハンドリング

## 4. テストデータ
### 4.1 準備データ
- ユーザー: admin@example.com, editor@example.com, viewer@example.com
- ナレッジ: 10件（カテゴリ別）
- 添付ファイル: PDF/Word/Excel

### 4.2 テスト後のクリーンアップ
- テストデータの削除
- ステートのリセット

## 5. 成功基準
- [ ] 全テストケース実行完了
- [ ] 成功率 ≥ 95%
- [ ] カバレッジ ≥ 80%
- [ ] 致命的なバグなし

## 6. リスク
| リスク | 影響度 | 対策 |
|--------|--------|------|
| テストデータ不足 | 中 | 事前にデータ準備スクリプト作成 |
| 環境構築遅延 | 高 | Docker環境を使用 |
```

### 3. テストケーステンプレート

```markdown
# {Feature名} テストケース一覧

## 1. ユニットテスト

### TC-U-001: 正常系 - リソース作成成功
- **前提条件**: 有効なデータ
- **入力**: {"name": "テストリソース", "category": "技術"}
- **期待結果**: リソースが作成され、IDが返却される
- **検証項目**:
  - [ ] id is not None
  - [ ] name == "テストリソース"
  - [ ] category == "技術"

### TC-U-002: 異常系 - 必須項目なし
- **前提条件**: データ不備
- **入力**: {}
- **期待結果**: ValueErrorが発生
- **検証項目**:
  - [ ] raises ValueError
  - [ ] message == "nameは必須です"

### TC-U-003: 境界値 - 名前が空文字列
- **前提条件**: name = ""
- **入力**: {"name": "", "category": "技術"}
- **期待結果**: ValueErrorが発生
- **検証項目**:
  - [ ] raises ValueError

### TC-U-004: 境界値 - 名前が最大長
- **前提条件**: name = "x" * 255
- **入力**: {"name": "x" * 255, "category": "技術"}
- **期待結果**: 作成成功
- **検証項目**:
  - [ ] id is not None

### TC-U-005: 境界値 - 名前が最大長+1
- **前提条件**: name = "x" * 256
- **入力**: {"name": "x" * 256, "category": "技術"}
- **期待結果**: ValueErrorが発生
- **検証項目**:
  - [ ] raises ValueError

## 2. 統合テスト（API）

### TC-I-001: 正常系 - POST /api/resource
- **前提条件**: 認証済みユーザー
- **HTTPメソッド**: POST
- **URL**: /api/resource
- **ヘッダー**: Authorization: Bearer {token}
- **ボディ**: {"name": "テストリソース"}
- **期待結果**: 201 Created
- **検証項目**:
  - [ ] status_code == 201
  - [ ] data["status"] == "success"
  - [ ] data["data"]["id"] is not None

### TC-I-002: 異常系 - 未認証
- **前提条件**: 未認証
- **HTTPメソッド**: POST
- **URL**: /api/resource
- **期待結果**: 401 Unauthorized
- **検証項目**:
  - [ ] status_code == 401

### TC-I-003: 異常系 - 権限不足
- **前提条件**: Viewerロール
- **HTTPメソッド**: POST
- **URL**: /api/resource
- **期待結果**: 403 Forbidden
- **検証項目**:
  - [ ] status_code == 403

## 3. E2Eテスト（Playwright）

### TC-E-001: ユーザーシナリオ - リソース作成フロー
- **シナリオ**:
  1. ログイン（admin@example.com）
  2. 「新規作成」ボタンをクリック
  3. フォームに入力
  4. 「保存」ボタンをクリック
  5. 成功メッセージを確認
- **検証項目**:
  - [ ] ログイン成功
  - [ ] フォーム表示
  - [ ] 保存成功
  - [ ] 一覧画面に反映
```

### 4. テストコードテンプレート

#### 4.1 ユニットテスト（pytest）
```python
import pytest
from backend.services import ResourceService

@pytest.fixture
def service():
    return ResourceService()

@pytest.fixture
def valid_data():
    return {"name": "テストリソース", "category": "技術"}

# 正常系
def test_create_success(service, valid_data):
    """TC-U-001: 正常系 - リソース作成成功"""
    result = service.create(valid_data)

    assert result.id is not None
    assert result.name == "テストリソース"
    assert result.category == "技術"

# 異常系
def test_create_missing_required_field(service):
    """TC-U-002: 異常系 - 必須項目なし"""
    with pytest.raises(ValueError) as exc_info:
        service.create({})

    assert "nameは必須です" in str(exc_info.value)

# 境界値
@pytest.mark.parametrize("name, expected", [
    ("", ValueError),  # 空文字列
    ("x" * 255, None),  # 最大長
    ("x" * 256, ValueError),  # 最大長+1
])
def test_create_boundary_values(service, name, expected):
    """TC-U-003〜005: 境界値テスト"""
    data = {"name": name, "category": "技術"}

    if expected is ValueError:
        with pytest.raises(ValueError):
            service.create(data)
    else:
        result = service.create(data)
        assert result.id is not None
```

#### 4.2 統合テスト（pytest + Flask test client）
```python
import pytest
from backend.app_v2 import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers(client):
    # ログインしてトークン取得
    response = client.post('/api/auth/login', json={
        "email": "admin@example.com",
        "password": "password"
    })
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# 正常系
def test_create_resource_api_success(client, auth_headers):
    """TC-I-001: 正常系 - POST /api/resource"""
    response = client.post('/api/resource',
        json={"name": "テストリソース"},
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["id"] is not None

# 異常系 - 未認証
def test_create_resource_api_unauthorized(client):
    """TC-I-002: 異常系 - 未認証"""
    response = client.post('/api/resource',
        json={"name": "テストリソース"}
    )

    assert response.status_code == 401

# 権限テスト
@pytest.mark.parametrize("role, expected_status", [
    ("admin", 201),
    ("editor", 201),
    ("viewer", 403),
])
def test_create_resource_api_permissions(client, role, expected_status):
    """TC-I-003: 権限テスト"""
    # ロール別にログイン
    response = client.post('/api/auth/login', json={
        "email": f"{role}@example.com",
        "password": "password"
    })
    token = response.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # リソース作成
    response = client.post('/api/resource',
        json={"name": "テストリソース"},
        headers=headers
    )

    assert response.status_code == expected_status
```

#### 4.3 E2Eテスト（Playwright）
```javascript
// tests/e2e/resource-creation.spec.js
import { test, expect } from '@playwright/test';

test.describe('リソース作成フロー', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン
    await page.goto('/login.html');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'password');
    await page.click('#login-button');
    await page.waitForURL('/index.html');
  });

  test('TC-E-001: 正常系 - リソース作成成功', async ({ page }) => {
    // 新規作成ボタンをクリック
    await page.click('#create-button');

    // フォーム入力
    await page.fill('#name', 'テストリソース');
    await page.selectOption('#category', 'tech');

    // 保存
    await page.click('#save-button');

    // 成功メッセージ確認
    await expect(page.locator('.success-message')).toHaveText('作成に成功しました');

    // 一覧画面に反映確認
    await expect(page.locator('.resource-list')).toContainText('テストリソース');
  });

  test('TC-E-002: 異常系 - 必須項目なし', async ({ page }) => {
    await page.click('#create-button');

    // 名前を入力せずに保存
    await page.click('#save-button');

    // エラーメッセージ確認
    await expect(page.locator('.error-message')).toHaveText('名前は必須です');
  });
});
```

### 5. テストデータ準備

#### 5.1 Fixtureデータ
```python
# backend/tests/conftest.py
import pytest

@pytest.fixture
def test_users():
    return [
        {"email": "admin@example.com", "role": "admin"},
        {"email": "editor@example.com", "role": "editor"},
        {"email": "viewer@example.com", "role": "viewer"},
    ]

@pytest.fixture
def test_resources():
    return [
        {"name": "リソース1", "category": "技術"},
        {"name": "リソース2", "category": "業務"},
    ]
```

### 6. テストカバレッジ目標

| レベル | 目標カバレッジ | 説明 |
|--------|---------------|------|
| ユニットテスト | ≥80% | 個別関数・メソッド |
| 統合テスト | ≥70% | APIエンドポイント |
| E2Eテスト | 主要シナリオ網羅 | ユーザー体験 |

## 実行コマンド例
```bash
# Skill tool経由で実行
/test-designer "design/user_management_architecture.md のテスト設計"

# Task tool経由で実行（別プロセス）
Task(subagent_type="general-purpose", prompt="test-designerとして、design/配下の設計書のテスト設計を作成", description="Test design")
```

## 次のステップ
テスト設計完了後、`test-reviewer` に自動的に渡される（Hooks連携）。

## 注意事項
- 正常系だけでなく、異常系・境界値を必ず含める
- 権限テストを忘れずに設計する
- テストデータの準備とクリーンアップを明確にする
- E2Eテストは主要シナリオに絞る（過剰なE2Eは避ける）
