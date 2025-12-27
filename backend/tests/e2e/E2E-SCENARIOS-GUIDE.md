# E2Eシナリオテストガイド - Mirai Knowledge Systems

Playwright を使用したエンドツーエンド (E2E) シナリオテストスイートです。

## 概要

このテストスイートは、Mirai Knowledge Systems の主要な5つのビジネスシナリオをカバーしています:

### シナリオ 1: ナレッジライフサイクル
**ファイル**: `scenario1_knowledge_lifecycle.spec.js`

- ナレッジの作成
- 承認申請
- マネージャーによる承認
- ナレッジの公開
- 通知の確認
- 検索結果への表示

### シナリオ 2: 承認フロー
**ファイル**: `scenario2_approval_flow.spec.js`

- 承認 (Approve)
- 差戻し (Request Changes)
- 却下 (Reject)
- 承認履歴の表示
- 権限チェック

### シナリオ 3: 検索と閲覧
**ファイル**: `scenario3_search_and_view.spec.js`

- 全文検索
- カテゴリフィルター
- タグフィルター
- ソート機能
- ナレッジ詳細表示
- 関連ナレッジ表示
- 検索履歴
- エクスポート機能

### シナリオ 4: 事故レポート
**ファイル**: `scenario4_incident_report.spec.js`

- 事故レポート作成
- ステータス更新
- 担当者割当
- 関連ナレッジのリンク
- 完全なワークフロー (報告→調査→解決)
- 統計表示
- 通知

### シナリオ 5: 専門家相談
**ファイル**: `scenario5_expert_consultation.spec.js`

- 相談リクエスト作成
- 専門家による回答
- フィードバック (役立った)
- フィルター機能
- 専門家統計
- ナレッジ化
- フォローアップ質問
- 緊急相談の通知

## セットアップ

### 前提条件

- Node.js (v16 以上)
- npm
- Python 3.9+ (バックエンドサーバー用)

### インストール

```bash
# プロジェクトルートから
cd /mnt/LinuxHDD/Mirai-Knowledge-Systems/backend

# 依存関係のインストール
npm install

# Playwright ブラウザのインストール
npx playwright install
```

## テストの実行

### 全シナリオの実行

```bash
# スクリプトを使用 (推奨)
./tests/e2e/run-e2e-tests.sh

# または npm コマンド
npm run test:e2e
```

### 特定のシナリオの実行

```bash
# シナリオ1のみ実行
./tests/e2e/run-e2e-tests.sh --scenario 1

# シナリオ2のみ実行
./tests/e2e/run-e2e-tests.sh --scenario 2

# シナリオ3のみ実行
./tests/e2e/run-e2e-tests.sh --scenario 3

# シナリオ4のみ実行
./tests/e2e/run-e2e-tests.sh --scenario 4

# シナリオ5のみ実行
./tests/e2e/run-e2e-tests.sh --scenario 5
```

### オプション

```bash
# ヘッドモード (ブラウザを表示)
./tests/e2e/run-e2e-tests.sh --headed

# デバッグモード
./tests/e2e/run-e2e-tests.sh --debug

# UI モード (インタラクティブ)
./tests/e2e/run-e2e-tests.sh --ui

# 実行後にレポートを表示
./tests/e2e/run-e2e-tests.sh --report

# サーバーを起動しない (既に起動している場合)
./tests/e2e/run-e2e-tests.sh --no-server

# 組み合わせ例
./tests/e2e/run-e2e-tests.sh --scenario 1 --headed --report
```

### npm スクリプト

```bash
# 通常実行
npm run test:e2e

# ヘッドモード
npm run test:e2e:headed

# デバッグモード
npm run test:e2e:debug

# UI モード
npm run test:e2e:ui

# レポート表示
npm run test:e2e:report
```

## ディレクトリ構造

```
tests/e2e/
├── E2E-SCENARIOS-GUIDE.md                   # このファイル
├── run-e2e-tests.sh                         # テスト実行スクリプト
├── scenario1_knowledge_lifecycle.spec.js    # シナリオ1
├── scenario2_approval_flow.spec.js          # シナリオ2
├── scenario3_search_and_view.spec.js        # シナリオ3
├── scenario4_incident_report.spec.js        # シナリオ4
├── scenario5_expert_consultation.spec.js    # シナリオ5
└── helpers/
    ├── auth.js                              # 認証ヘルパー
    ├── api.js                               # API ヘルパー
    └── waiters.js                           # 待機ヘルパー
```

## テストユーザー

テストには以下のユーザーが使用されます:

| ユーザータイプ | メール | パスワード | 役割 |
|--------------|--------|-----------|------|
| Admin | admin@example.com | Admin123! | 管理者 |
| Manager | manager@example.com | Manager123! | マネージャー |
| Worker | worker@example.com | Worker123! | 作業者 |
| Expert | expert@example.com | Expert123! | 専門家 |

**注意**: これらは開発・テスト用のユーザーです。本番環境では使用しないでください。

## ヘルパー関数

### auth.js - 認証ヘルパー

```javascript
const { login, loginAPI, logout, isLoggedIn } = require('./helpers/auth');

// ブラウザでログイン
await login(page, 'worker');

// API経由でログイン (高速)
const { token } = await loginAPI(request, 'manager');

// ログアウト
await logout(page);

// ログイン状態確認
const loggedIn = await isLoggedIn(page);
```

### api.js - API ヘルパー

```javascript
const {
  createKnowledge,
  createApprovalRequest,
  processApproval,
  createIncident,
  createConsultation,
  answerConsultation,
  getNotifications
} = require('./helpers/api');

// ナレッジ作成
const knowledge = await createKnowledge(request, token, {
  title: 'テストナレッジ',
  content: '内容',
  category: 'safety'
});

// 承認申請
const approval = await createApprovalRequest(request, token, knowledgeId);

// 承認処理
await processApproval(request, managerToken, approvalId, 'approve', 'コメント');
```

### waiters.js - 待機ヘルパー

```javascript
const {
  waitForNotification,
  waitForText,
  waitForAPIResponse,
  waitForPageLoad
} = require('./helpers/waiters');

// 通知を待つ
await waitForNotification(page, /成功|success/i);

// テキストを待つ
await waitForText(page, 'ナレッジが作成されました');

// API レスポンスを待つ
await waitForAPIResponse(page, '/api/v1/knowledge');

// ページ読み込み完了を待つ
await waitForPageLoad(page);
```

## レポート

テスト実行後、以下のレポートが生成されます:

- **HTML レポート**: `tests/reports/e2e-html/index.html`
- **JSON レポート**: `tests/reports/e2e-results.json`
- **JUnit レポート**: `tests/reports/e2e-junit.xml`

HTML レポートを開く:
```bash
npm run test:e2e:report
# または
npx playwright show-report
```

## 設定

テスト設定は `playwright.config.js` で管理されています。

### 主な設定項目

- **ベース URL**: デフォルトは `http://localhost:8000`
- **タイムアウト**: テストごとに120秒
- **リトライ**: CI環境で2回
- **スクリーンショット**: 失敗時のみ
- **ビデオ**: 失敗時のみ保存

### 環境変数

```bash
# ベース URL を変更
export BASE_URL=http://localhost:8080

# サーバー起動をスキップ
export SKIP_WEBSERVER=true

# CI モード
export CI=true
```

## トラブルシューティング

### ブラウザがインストールされていない

```bash
npx playwright install
```

### タイムアウトエラー

- サーバーが起動していることを確認
- `playwright.config.js` でタイムアウトを増やす
- `--headed` オプションで実際の動作を確認

### テストが不安定

- 待機時間を調整 (`waiters.js`)
- ネットワークアイドル状態を待つ
- 要素の可視性を確認

### デバッグ

```bash
# デバッグモードで実行
./tests/e2e/run-e2e-tests.sh --debug

# UI モードで実行
./tests/e2e/run-e2e-tests.sh --ui

# ヘッドモードで実行
./tests/e2e/run-e2e-tests.sh --headed
```

## CI/CD 統合

### GitHub Actions の例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm install

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: ./tests/e2e/run-e2e-tests.sh

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/reports/
```

## ベストプラクティス

1. **テストの独立性**: 各テストは独立して実行できるようにする
2. **データのクリーンアップ**: テスト後はデータを適切にクリーンアップ
3. **明示的な待機**: `waitFor` を使用して確実に要素を待つ
4. **ページオブジェクト**: 複雑なページは Page Object パターンを使用
5. **エラーハンドリング**: 適切なエラーメッセージとフォールバック処理
6. **並列実行**: 可能な限りテストを並列化
7. **スクリーンショット**: デバッグ用にスクリーンショットを活用

## 新しいシナリオの追加

1. `tests/e2e/` に新しい `.spec.js` ファイルを作成
2. 必要に応じて `helpers/` にヘルパー関数を追加
3. `run-e2e-tests.sh` にシナリオを追加 (オプション)

### テンプレート

```javascript
const { test, expect } = require('@playwright/test');
const { login, loginAPI } = require('./helpers/auth');
const { waitForNotification } = require('./helpers/waiters');

test.describe('Scenario N: Your Scenario Name', () => {
  let userToken;

  test.beforeAll(async ({ request }) => {
    const auth = await loginAPI(request, 'worker');
    userToken = auth.token;
  });

  test('should perform main workflow', async ({ page, request }) => {
    console.log('=== Test: Main Workflow ===');

    await login(page, 'worker');

    // Your test steps here

    console.log('✓ Test completed successfully');
  });
});
```

## 参考資料

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Test Assertions](https://playwright.dev/docs/test-assertions)
- [Page Object Model](https://playwright.dev/docs/pom)

## サポート

問題が発生した場合:

1. GitHub Issues で既存の問題を確認
2. 新しい Issue を作成 (ログとスクリーンショットを添付)
3. 開発チームに連絡

## ライセンス

このテストスイートは Mirai Knowledge Systems プロジェクトの一部です。
