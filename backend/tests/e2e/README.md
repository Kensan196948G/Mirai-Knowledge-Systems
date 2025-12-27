# E2E 互換性テスト

Mirai Knowledge Systemのブラウザ・デバイス互換性テストスイート。

## 概要

このテストスイートは、複数のブラウザとデバイスサイズでアプリケーションの動作を確認します。

### テスト対象ブラウザ

- **Chromium** (Chrome相当)
- **Firefox**
- **WebKit** (Safari相当)
- **Edge** (利用可能な場合)

### テスト対象デバイスサイズ

- **デスクトップ**: 1920x1080
- **ノートPC**: 1366x768
- **タブレット (縦)**: 768x1024
- **タブレット (横)**: 1024x768
- **スマートフォン (大)**: 414x896 (iPhone 11)
- **スマートフォン (中)**: 375x667 (iPhone SE)
- **スマートフォン (小)**: 360x640 (Galaxy S5)

## セットアップ

### 1. 依存関係のインストール

```bash
cd tests/e2e
npm install
```

### 2. Playwrightブラウザのインストール

```bash
npx playwright install
```

## テスト実行

### 全テスト実行

```bash
cd tests/e2e
./compatibility/run_compatibility_tests.sh
```

または

```bash
npm run test:compatibility
```

### ブラウザテストのみ

```bash
./compatibility/run_compatibility_tests.sh --browsers-only
```

または

```bash
npm run test:browsers
```

### レスポンシブテストのみ

```bash
./compatibility/run_compatibility_tests.sh --responsive-only
```

または

```bash
npm run test:responsive
```

### 特定のブラウザのみテスト

```bash
./compatibility/run_compatibility_tests.sh --browser chromium
./compatibility/run_compatibility_tests.sh --browser firefox
./compatibility/run_compatibility_tests.sh --browser webkit
```

### ヘッド付きモード（ブラウザ表示）

```bash
./compatibility/run_compatibility_tests.sh --headed
```

または

```bash
npm run test:headed
```

### デバッグモード

```bash
./compatibility/run_compatibility_tests.sh --debug
```

または

```bash
npm run test:debug
```

### UIモード（インタラクティブ）

```bash
./compatibility/run_compatibility_tests.sh --ui
```

または

```bash
npm run test:ui
```

## テストファイル構成

```
tests/e2e/
├── package.json                              # npm設定
├── playwright.config.js                      # Playwright設定
├── README.md                                 # このファイル
└── compatibility/
    ├── browsers.spec.js                      # ブラウザ互換性テスト
    ├── responsive.spec.js                    # レスポンシブデザインテスト
    └── run_compatibility_tests.sh            # テスト実行スクリプト
```

## テスト内容

### browsers.spec.js - ブラウザ互換性テスト

- **トップページ表示確認**
  - ページロード時間測定
  - 主要要素の表示確認
  - ナビゲーションメニュー動作確認
  - レスポンシブメニュー確認

- **ログインフロー確認**
  - ログインページ表示
  - フォーム入力動作
  - エラーメッセージ表示

- **ダッシュボード表示確認**
  - ダッシュボード要素確認
  - ウィジェット・カード表示

- **検索機能確認**
  - 検索ボックス動作
  - 検索サジェスト表示

- **フォーム操作確認**
  - テキストエリア動作
  - チェックボックス・ラジオボタン動作
  - セレクトボックス動作

- **JavaScript機能確認**
  - JavaScriptエラー検出
  - 動的コンテンツ読み込み確認

- **CSS・スタイル確認**
  - CSS読み込み確認
  - フォント適用確認

- **アクセシビリティ基本確認**
  - 見出し構造確認
  - リンクテキスト確認
  - 画像alt属性確認

- **パフォーマンス確認**
  - リソース読み込み確認
  - ページロード時間測定

### responsive.spec.js - レスポンシブデザインテスト

- **デスクトップ表示確認**
  - レイアウト整合性確認
  - サイドバー表示確認

- **ノートPC表示確認**
  - コンテンツ折り返し確認

- **タブレット表示確認**
  - 縦横オリエンテーション対応
  - タッチ操作対応（ボタンサイズ）
  - フォーム使いやすさ

- **スマートフォン表示確認**
  - モバイルレイアウト適用
  - ハンバーガーメニュー動作
  - タッチUI確認
  - フォント読みやすさ
  - 画像リサイズ確認

- **デバイス横断確認**
  - 全デバイスでのヘッダー・フッター表示
  - コンテンツのビューポート収まり確認

- **オリエンテーション変更確認**
  - 縦横切り替え時のレイアウト適応

- **レスポンシブ画像・メディア確認**
  - 画像・ビデオのレスポンシブ性

- **フォームのレスポンシブ性確認**
  - 各デバイスでのフォーム使いやすさ

- **ナビゲーションのレスポンシブ性確認**
  - デスクトップ・モバイルメニュー切り替え

## レポート

### HTMLレポート

テスト実行後、自動的にHTMLレポートが生成されます。

```bash
npm run report
```

レポートは `http://127.0.0.1:9323` で表示されます。

### スクリーンショット

- 失敗時のスクリーンショットは自動保存されます
- 保存先: `reports/screenshots_<timestamp>/`

### レポートファイル

- **HTMLレポート**: `reports/playwright-html/index.html`
- **JSONレポート**: `reports/playwright-results.json`
- **JUnitレポート**: `reports/playwright-junit.xml`

## トラブルシューティング

### ブラウザがインストールされていない

```bash
npx playwright install
```

### 特定のブラウザのみインストール

```bash
npx playwright install chromium
npx playwright install firefox
npx playwright install webkit
```

### Webサーバーが起動しない

既にサーバーが起動している場合:

```bash
./compatibility/run_compatibility_tests.sh --no-server
```

### テストがタイムアウトする

`playwright.config.js`のタイムアウト設定を調整:

```javascript
timeout: 60000,  // 60秒
```

### ヘッドレスモードでテストが失敗する

ヘッド付きモードで確認:

```bash
npm run test:headed
```

## CI/CD統合

### GitHub Actions例

```yaml
name: E2E Compatibility Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd tests/e2e
          npm install
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      - name: Run tests
        run: |
          cd tests/e2e
          ./compatibility/run_compatibility_tests.sh
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: tests/e2e/reports/
```

## ベストプラクティス

### テスト作成時

1. **セレクタの選択**
   - `data-testid` 属性を優先
   - `role`, `aria-label` を活用
   - CSS classは避ける（変更されやすい）

2. **待機処理**
   - `waitForLoadState('networkidle')` を使用
   - 明示的な待機（`waitForSelector`）を優先
   - `waitForTimeout` は最小限に

3. **スクリーンショット**
   - 失敗時のデバッグ用に活用
   - `fullPage: true` で全体を撮影

4. **並列実行**
   - テストは独立して実行可能に
   - 共有状態を避ける

### メンテナンス

1. **定期的な実行**
   - 毎日の自動テスト
   - リリース前の必須チェック

2. **レポート確認**
   - スクリーンショットの目視確認
   - パフォーマンス指標の監視

3. **テストの更新**
   - UI変更時にテストも更新
   - 新機能追加時にテストを追加

## 参考資料

- [Playwright公式ドキュメント](https://playwright.dev/)
- [Playwright設定リファレンス](https://playwright.dev/docs/test-configuration)
- [Playwrightベストプラクティス](https://playwright.dev/docs/best-practices)

## ライセンス

このテストスイートはMirai Knowledge Systemの一部です。
