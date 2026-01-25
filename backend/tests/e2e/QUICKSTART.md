# E2E互換性テスト クイックスタートガイド

## 5分で始めるE2Eテスト

### ステップ1: セットアップ（初回のみ）

```bash
# E2Eディレクトリに移動
cd /path/to/Mirai-Knowledge-Systems/backend/tests/e2e

# 依存関係インストール
npm install

# Playwrightブラウザインストール
npx playwright install
```

### ステップ2: テスト実行

#### 最も簡単な方法

```bash
./compatibility/run_compatibility_tests.sh
```

これで以下が自動実行されます:
- 全ブラウザ（Chrome、Firefox、Safari）でのテスト
- 全デバイスサイズでのテスト
- スクリーンショット自動撮影
- HTMLレポート自動生成

#### 個別のテスト実行

**ブラウザテストのみ:**
```bash
npm run test:browsers
```

**レスポンシブテストのみ:**
```bash
npm run test:responsive
```

**特定のブラウザのみ:**
```bash
./compatibility/run_compatibility_tests.sh --browser chromium
```

### ステップ3: レポート確認

テスト完了後、自動的にHTMLレポートサーバーが起動します:

```
http://127.0.0.1:9323
```

ブラウザでこのURLにアクセスすると、詳細なテストレポートが表示されます。

## よく使うコマンド

### デバッグモード（ブラウザが表示される）

```bash
npm run test:headed
```

### UIモード（インタラクティブ）

```bash
npm run test:ui
```

テストを選択して実行できる便利なインターフェースが起動します。

### 特定のテストファイルのみ実行

```bash
npx playwright test compatibility/browsers.spec.js
npx playwright test compatibility/responsive.spec.js
```

## テスト内容

### browsers.spec.js
- Chrome、Firefox、Safari、Edgeでの動作確認
- ページ表示、フォーム操作、JavaScript動作
- パフォーマンス測定

### responsive.spec.js
- デスクトップ（1920x1080）
- ノートPC（1366x768）
- タブレット（768x1024）
- スマートフォン（375x667）
- レイアウト崩れチェック

## トラブルシューティング

### エラー: ブラウザがない

```bash
npx playwright install
```

### エラー: ポート5000が使用中

既にアプリケーションが起動している場合:

```bash
./compatibility/run_compatibility_tests.sh --no-server
```

### テストが遅い

ヘッドレスモード（デフォルト）で実行すると高速です:

```bash
npm run test
```

## ディレクトリ構成

```
tests/e2e/
├── compatibility/                    # 互換性テスト
│   ├── browsers.spec.js             # ブラウザテスト
│   ├── responsive.spec.js           # レスポンシブテスト
│   ├── helpers.js                   # ヘルパー関数
│   └── run_compatibility_tests.sh   # 実行スクリプト
├── playwright.config.js             # Playwright設定
├── package.json                     # npm設定
├── README.md                        # 詳細ドキュメント
└── QUICKSTART.md                    # このファイル
```

## 次のステップ

詳細な情報は [README.md](./README.md) を参照してください。

- テスト内容の詳細
- CI/CD統合方法
- カスタムテストの作成方法
- ベストプラクティス
