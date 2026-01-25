# Mirai Knowledge Systems - フロントエンドテスト環境

このドキュメントでは、Mirai Knowledge Systemsのフロントエンド（Vanilla JavaScript）に対するテスト環境の構成と使用方法について説明します。

## 目次

1. [概要](#概要)
2. [テストフレームワーク](#テストフレームワーク)
3. [環境セットアップ](#環境セットアップ)
4. [テスト実行方法](#テスト実行方法)
5. [テストの種類](#テストの種類)
6. [カバレッジ目標](#カバレッジ目標)
7. [CI/CD統合](#cicd統合)
8. [ベストプラクティス](#ベストプラクティス)

---

## 概要

Mirai Knowledge Systemsのフロントエンドテスト環境は、以下の2つの主要なテストフレームワークで構成されています:

- **Jest**: ユニットテスト（DOM操作、ユーティリティ関数、XSS対策など）
- **Playwright**: E2Eテスト（ログインフロー、ナレッジ検索、専門家相談など）

### テスト対象ファイル

```
webui/
├── app.js              # 認証、RBAC、共通機能
├── dom-helpers.js      # セキュアなDOM操作ヘルパー
├── actions.js          # 共通アクション（トースト通知など）
├── notifications.js    # 通知システム
├── detail-pages.js     # 詳細ページ共通機能
└── detail-loader.js    # 詳細ページローダー
```

---

## テストフレームワーク

### 1. Jest (ユニットテスト)

- **バージョン**: 29.7.0
- **環境**: JSDOM (ブラウザDOM環境のシミュレート)
- **目的**: 個別関数のロジック検証、DOM操作の正確性、XSS対策の確認

**主要機能:**
- DOM操作のテスト
- LocalStorage/SessionStorageのモック
- Fetch APIのモック
- カバレッジレポート生成

### 2. Playwright (E2Eテスト)

- **バージョン**: 1.40.0
- **ブラウザ**: Chromium (デフォルト)
- **目的**: 実際のユーザーフローのエンドツーエンド検証

**主要機能:**
- 複数ブラウザ対応 (Chromium, Firefox, WebKit)
- スクリーンショット・動画キャプチャ
- ネットワークモック
- 並列テスト実行

---

## 環境セットアップ

### 前提条件

- Node.js 20.x以上
- Python 3.12以上 (E2Eテスト用のバックエンド起動)
- PostgreSQL 14以上 (E2Eテスト用)

### インストール手順

```bash
# プロジェクトルートに移動
cd /path/to/Mirai-Knowledge-Systems/backend

# Node.js依存パッケージをインストール
npm install

# Playwrightブラウザをインストール
npx playwright install chromium

# Python依存パッケージをインストール (E2E用)
pip install -r requirements.txt
```

### 環境変数設定

E2Eテスト用の環境変数を設定します（`.env.test`ファイルを作成可）:

```bash
# テスト用データベース
DATABASE_URL=postgresql://mirai_user:password@localhost/mirai_test

# ベースURL
BASE_URL=http://localhost:8000

# CI環境フラグ
CI=false
```

---

## テスト実行方法

### ユニットテスト (Jest)

```bash
# すべてのユニットテストを実行
npm run test:unit

# カバレッジレポート付きで実行
npm run test:unit:coverage

# ウォッチモード（開発時に便利）
npm run test:unit:watch

# 詳細ログ付きで実行
npm run test:unit:verbose
```

### E2Eテスト (Playwright)

```bash
# すべてのE2Eテストを実行
npm run test:e2e

# ヘッドモードで実行（ブラウザを表示）
npm run test:e2e:headed

# デバッグモードで実行
npm run test:e2e:debug

# UIモードで実行（インタラクティブ）
npm run test:e2e:ui

# レポートを表示
npm run test:e2e:report
```

### 全テストを実行

```bash
# ユニット + E2E
npm test

# CI環境用（カバレッジ付き）
npm run test:ci
```

---

## テストの種類

### ユニットテスト

#### 1. DOM操作テスト (`dom-helpers.test.js`)

```javascript
// XSS対策のエスケープ処理
test('should escape HTML special characters', () => {
  const input = '<script>alert("XSS")</script>';
  const expected = '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;';
  expect(escapeHtml(input)).toBe(expected);
});

// セキュアな要素作成
test('should create element with textContent', () => {
  const element = createSecureElement('span', { textContent: 'Hello World' });
  expect(element.textContent).toBe('Hello World');
});
```

#### 2. 認証・RBACテスト (`app-auth.test.js`)

```javascript
// 権限チェック
test('should return true when user has higher role', () => {
  localStorage.setItem('user', JSON.stringify({
    id: 1,
    username: 'admin',
    roles: ['admin']
  }));

  expect(checkPermission('partner')).toBe(true);
});
```

#### 3. 通知システムテスト (`notifications.test.js`)

```javascript
// バッジ表示
test('should display badge with count when count > 0', () => {
  updateNotificationBadge(5);
  const badge = document.querySelector('.notification-badge');
  expect(badge.textContent).toBe('5');
});
```

#### 4. アクションテスト (`actions.test.js`)

```javascript
// トースト通知
test('should create toast with correct message', () => {
  showToast('Hello World', 'success');
  const toast = document.querySelector('.toast');
  expect(toast.querySelector('.toast-message').textContent).toBe('Hello World');
});
```

### E2Eテスト

#### 1. ログインフロー (`login.spec.js`)

- 正常ログイン
- 不正な認証情報でのエラー表示
- セッション永続化
- ログアウト機能
- XSS攻撃の防御

#### 2. ナレッジ検索・表示 (`knowledge-search.spec.js`)

- 検索インターフェース表示
- 基本検索機能
- フィルタリング機能
- ソート機能
- 詳細ページへの遷移
- XSS攻撃の防御

#### 3. SOP詳細ページと専門家相談 (`sop-detail-expert-consult.spec.js`)

- SOP詳細ページ表示
- メタデータ表示
- PDFダウンロード機能
- 専門家相談フォーム表示・送信
- 相談一覧表示
- XSS攻撃の防御

---

## カバレッジ目標

### 目標値: 70%以上

すべてのメトリクスで70%以上のカバレッジを達成することを目標としています。

```json
{
  "coverageThreshold": {
    "global": {
      "branches": 70,
      "functions": 70,
      "lines": 70,
      "statements": 70
    }
  }
}
```

### カバレッジレポートの確認

```bash
# カバレッジレポートを生成
npm run test:unit:coverage

# HTMLレポートを開く
open backend/tests/coverage/index.html
```

### 現在のカバレッジ状況

カバレッジレポートは以下のディレクトリに生成されます:

```
backend/tests/coverage/
├── index.html          # HTMLレポート
├── lcov.info           # LCOV形式
├── coverage-summary.json
└── ...
```

---

## CI/CD統合

### GitHub Actions

フロントエンドテストは、GitHub Actionsで自動実行されます。

**ワークフロー**: `.github/workflows/frontend-tests.yml`

#### トリガー条件

- `main`, `develop`, `feature/*` ブランチへのpush
- `webui/` ディレクトリの変更
- テスト関連ファイルの変更

#### ジョブ構成

1. **unit-tests**: Jestによるユニットテスト
   - カバレッジレポート生成
   - 70%閾値チェック
   - Codecovへのアップロード

2. **e2e-tests**: PlaywrightによるE2Eテスト
   - PostgreSQLセットアップ
   - テストデータシード
   - スクリーンショット・動画保存

3. **test-summary**: テスト結果サマリー
   - 全体の成功/失敗判定
   - アーティファクトの集約

#### 実行結果の確認

- GitHub Actionsタブで実行結果を確認
- 失敗した場合、テストビデオとスクリーンショットがアーティファクトとして保存される
- カバレッジレポートはCodecovで確認可能

---

## ベストプラクティス

### 1. テスト作成のガイドライン

#### ユニットテスト

```javascript
// Good: 明確なテスト名
test('should escape HTML special characters', () => { ... });

// Bad: 不明確なテスト名
test('test1', () => { ... });

// Good: アレンジ・アクト・アサート (AAA)パターン
test('should display notification badge', () => {
  // Arrange
  document.body.innerHTML = '<div class="notification-badge"></div>';

  // Act
  updateNotificationBadge(5);

  // Assert
  const badge = document.querySelector('.notification-badge');
  expect(badge.textContent).toBe('5');
});
```

#### E2Eテスト

```javascript
// Good: ページオブジェクトパターンの使用
const loginPage = {
  usernameInput: page.locator('input[name="username"]'),
  passwordInput: page.locator('input[name="password"]'),
  submitButton: page.locator('button[type="submit"]')
};

// Good: 明示的な待機
await expect(page.locator('.results')).toBeVisible();

// Bad: 暗黙的な待機
await page.waitForTimeout(3000); // アンチパターン
```

### 2. XSS対策のテスト

すべてのユーザー入力箇所でXSS攻撃を防御するテストを実装します:

```javascript
test('should prevent XSS in input', () => {
  const xssPayload = '<script>alert("XSS")</script>';
  element.textContent = xssPayload;

  // スクリプトタグがエスケープされていることを確認
  expect(element.innerHTML).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
});
```

### 3. モック・スタブの使用

外部APIやストレージのモックを適切に使用します:

```javascript
// LocalStorageのモック
beforeEach(() => {
  localStorage.clear();
  localStorage.setItem('access_token', 'test-token');
});

// Fetch APIのモック
fetch.mockResponseOnce(JSON.stringify({ data: 'test' }));
```

### 4. テストの独立性

各テストは他のテストに依存せず、独立して実行できる必要があります:

```javascript
// Good
beforeEach(() => {
  // 各テストで初期状態をリセット
  document.body.innerHTML = '';
  localStorage.clear();
});

// Bad
let sharedState = {}; // テスト間で状態を共有しない
```

### 5. テストカバレッジの向上

- エッジケース（null, undefined, 空文字列）のテスト
- エラーハンドリングのテスト
- 境界値のテスト
- セキュリティ関連のテスト

### 6. デバッグのヒント

```bash
# 特定のテストファイルのみ実行
npm run test:unit -- dom-helpers.test.js

# 特定のテストケースのみ実行
npm run test:unit -- -t "should escape HTML"

# E2Eテストをデバッグモードで実行
npm run test:e2e:debug

# E2EテストをUIモードで実行
npm run test:e2e:ui
```

---

## トラブルシューティング

### よくある問題と解決策

#### 1. Jestのタイムアウトエラー

```javascript
// jest.config.jsでタイムアウトを延長
testTimeout: 10000
```

#### 2. Playwrightのブラウザ起動エラー

```bash
# ブラウザを再インストール
npx playwright install --with-deps chromium
```

#### 3. カバレッジが低い

```bash
# カバレッジレポートを確認して、未カバー箇所を特定
npm run test:unit:coverage
open backend/tests/coverage/index.html
```

#### 4. E2Eテストのタイムアウト

```javascript
// playwright.config.jsでタイムアウトを調整
timeout: 120 * 1000, // 2分
```

---

## 参考リンク

- [Jest公式ドキュメント](https://jestjs.io/)
- [Playwright公式ドキュメント](https://playwright.dev/)
- [JSDOM](https://github.com/jsdom/jsdom)
- [GitHub Actions](https://docs.github.com/ja/actions)

---

## 貢献ガイドライン

新しいフロントエンド機能を追加する際は、必ず対応するテストを追加してください:

1. ユニットテストを作成 (`tests/unit/`)
2. E2Eテストを作成（必要に応じて） (`tests/e2e/`)
3. カバレッジ70%以上を維持
4. CI/CDが成功することを確認

---

**最終更新日**: 2026-01-01
**バージョン**: 1.0.0
