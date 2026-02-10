# Phase F-4: 既存コードリファクタリング - 機能要件書

**バージョン**: 1.0.0
**作成日**: 2026-02-10
**作成者**: spec-planner SubAgent
**ステータス**: Draft

---

## 1. 概要

### 1.1 機能名
Phase F-4: 既存コードリファクタリング（Legacy Code Refactoring）

### 1.2 目的
- 大規模ファイル（app.js: 3,895行、detail-pages.js: 3,291行）の分割
- ESモジュール構文への完全移行
- Phase F-2、F-3で作成したモジュールの活用
- 保守性・可読性の向上

### 1.3 優先度
**High** - Phase F-2、F-3完了後に実施

### 1.4 担当者
- **実装**: code-implementer SubAgent
- **レビュー**: code-reviewer SubAgent
- **テスト設計**: test-designer SubAgent

### 1.5 前提条件
- Phase F-1完了（Viteビルドシステム、コアモジュール）
- Phase F-2完了（機能モジュール分割）
- Phase F-3完了（ユーティリティモジュール分割）
- 既存機能の動作確認済み

---

## 2. 機能仕様

### 2.1 対象ファイル

#### 2.1.1 app.js（3,895行）
**分割対象**: メインアプリケーションロジック

##### 分割後の構成
```
webui/src/app/
├── index.js                    # エントリーポイント（約300行）
├── init.js                     # 初期化処理（約200行）
├── router.js                   # ルーティング（約150行）
├── event-handlers.js           # イベントハンドラー（約400行）
├── ui-controller.js            # UI制御（約500行）
├── data-loader.js              # データ読み込み（約300行）
├── notifications-handler.js    # 通知処理（約200行）
├── actions-handler.js          # アクション処理（約300行）
└── legacy-compat.js            # 後方互換性（約200行）
```

**削減行数**: 3,895行 → 8ファイル × 平均250行 = 約2,000行（削減率: 48%）

---

#### 2.1.2 detail-pages.js（3,291行）
**分割対象**: 詳細ページ表示ロジック

##### 分割後の構成
```
webui/src/pages/
├── knowledge-detail.js         # ナレッジ詳細（約500行）
├── sop-detail.js               # SOP詳細（約500行）
├── law-detail.js               # 法令詳細（約400行）
├── expert-detail.js            # 専門家詳細（約400行）
├── consultation-detail.js      # 相談詳細（約400行）
├── incident-detail.js          # インシデント詳細（約400行）
├── approval-detail.js          # 承認詳細（約300行）
└── page-renderer.js            # 共通レンダリング（約300行）
```

**削減行数**: 3,291行 → 8ファイル × 平均350行 = 約2,800行（削減率: 15%）

---

### 2.2 入力仕様

#### 2.2.1 app/index.js（エントリーポイント）

##### モジュールAPI
```javascript
/**
 * アプリケーションを初期化
 *
 * @param {Object} config - 設定オブジェクト
 * @param {boolean} config.isProduction - 本番環境かどうか
 * @param {Object} config.apiEndpoints - APIエンドポイント設定
 * @returns {Promise<void>}
 */
export async function initApp(config = {})

/**
 * ページをロード
 *
 * @param {string} page - ページ名 (dashboard, knowledge, sop, etc.)
 * @param {Object} params - パラメータ
 * @returns {Promise<void>}
 */
export async function loadPage(page, params = {})

/**
 * 現在のページを取得
 *
 * @returns {string} - 現在のページ名
 */
export function getCurrentPage()

/**
 * アプリケーションを破棄
 *
 * @returns {void}
 */
export function destroyApp()
```

---

#### 2.2.2 app/init.js（初期化処理）

##### モジュールAPI
```javascript
/**
 * 環境設定を初期化
 *
 * @returns {Object} - 環境設定
 */
export function initEnvironment()

/**
 * 認証状態を初期化
 *
 * @returns {Promise<Object>} - 現在のユーザー情報
 */
export async function initAuthentication()

/**
 * グローバルイベントリスナーを設定
 *
 * @returns {void}
 */
export function initGlobalEventListeners()

/**
 * Service Workerを登録
 *
 * @returns {Promise<void>}
 */
export async function initServiceWorker()

/**
 * ナビゲーションを初期化
 *
 * @returns {void}
 */
export function initNavigation()
```

---

#### 2.2.3 app/router.js（ルーティング）

##### モジュールAPI
```javascript
/**
 * ルートを定義
 *
 * @param {string} path - パス（例: '/knowledge/:id'）
 * @param {Function} handler - ハンドラー関数
 * @returns {void}
 */
export function defineRoute(path, handler)

/**
 * パスに移動
 *
 * @param {string} path - パス
 * @param {Object} state - 履歴状態（オプション）
 * @returns {void}
 */
export function navigateTo(path, state = {})

/**
 * 現在のパスを取得
 *
 * @returns {string} - 現在のパス
 */
export function getCurrentPath()

/**
 * パスパラメータを取得
 *
 * @param {string} path - パス（例: '/knowledge/:id'）
 * @returns {Object} - パラメータオブジェクト（例: { id: '123' }）
 */
export function getPathParams(path)

/**
 * ブラウザの戻るボタンを処理
 *
 * @param {Function} handler - 戻るボタンのハンドラー
 * @returns {void}
 */
export function onBackButton(handler)
```

---

#### 2.2.4 app/event-handlers.js（イベントハンドラー）

##### モジュールAPI
```javascript
/**
 * サイドバーメニューのイベントハンドラーを設定
 *
 * @returns {void}
 */
export function setupSidebarHandlers()

/**
 * 検索フォームのイベントハンドラーを設定
 *
 * @returns {void}
 */
export function setupSearchHandlers()

/**
 * ナレッジ一覧のイベントハンドラーを設定
 *
 * @returns {void}
 */
export function setupKnowledgeListHandlers()

/**
 * モーダルのイベントハンドラーを設定
 *
 * @returns {void}
 */
export function setupModalHandlers()

/**
 * 通知のイベントハンドラーを設定
 *
 * @returns {void}
 */
export function setupNotificationHandlers()

/**
 * ファイルアップロードのイベントハンドラーを設定
 *
 * @returns {void}
 */
export function setupFileUploadHandlers()
```

---

#### 2.2.5 app/ui-controller.js（UI制御）

##### モジュールAPI
```javascript
/**
 * サイドバーを表示/非表示
 *
 * @param {boolean} visible - 表示するかどうか
 * @returns {void}
 */
export function toggleSidebar(visible)

/**
 * ローディング画面を表示/非表示
 *
 * @param {boolean} visible - 表示するかどうか
 * @param {string} message - メッセージ（オプション）
 * @returns {void}
 */
export function toggleLoading(visible, message = '読み込み中...')

/**
 * エラーメッセージを表示
 *
 * @param {string} message - エラーメッセージ
 * @param {string} type - タイプ (error, warning, info)
 * @returns {void}
 */
export function showErrorMessage(message, type = 'error')

/**
 * 成功メッセージを表示
 *
 * @param {string} message - 成功メッセージ
 * @returns {void}
 */
export function showSuccessMessage(message)

/**
 * 確認ダイアログを表示
 *
 * @param {string} message - 確認メッセージ
 * @returns {Promise<boolean>} - OKがクリックされたかどうか
 */
export async function showConfirmDialog(message)

/**
 * ページタイトルを設定
 *
 * @param {string} title - タイトル
 * @returns {void}
 */
export function setPageTitle(title)

/**
 * アクティブメニューを設定
 *
 * @param {string} menuId - メニューID
 * @returns {void}
 */
export function setActiveMenu(menuId)
```

---

#### 2.2.6 pages/knowledge-detail.js（ナレッジ詳細）

##### モジュールAPI
```javascript
/**
 * ナレッジ詳細を表示
 *
 * @param {number} knowledgeId - ナレッジID
 * @returns {Promise<void>}
 */
export async function renderKnowledgeDetail(knowledgeId)

/**
 * ナレッジ編集フォームを表示
 *
 * @param {number} knowledgeId - ナレッジID
 * @returns {Promise<void>}
 */
export async function renderKnowledgeEditForm(knowledgeId)

/**
 * ナレッジを削除
 *
 * @param {number} knowledgeId - ナレッジID
 * @returns {Promise<void>}
 */
export async function deleteKnowledgeWithConfirmation(knowledgeId)

/**
 * ナレッジにコメントを追加
 *
 * @param {number} knowledgeId - ナレッジID
 * @param {string} comment - コメント内容
 * @returns {Promise<void>}
 */
export async function addKnowledgeComment(knowledgeId, comment)

/**
 * ナレッジを評価
 *
 * @param {number} knowledgeId - ナレッジID
 * @param {number} rating - 評価（1〜5）
 * @returns {Promise<void>}
 */
export async function rateKnowledge(knowledgeId, rating)
```

---

#### 2.2.7 pages/page-renderer.js（共通レンダリング）

##### モジュールAPI
```javascript
/**
 * ページコンテナをクリア
 *
 * @returns {void}
 */
export function clearPageContainer()

/**
 * ページヘッダーをレンダリング
 *
 * @param {Object} headerData - ヘッダーデータ
 * @param {string} headerData.title - タイトル
 * @param {string} headerData.subtitle - サブタイトル
 * @param {Array<Object>} headerData.actions - アクションボタン
 * @returns {HTMLElement} - ヘッダー要素
 */
export function renderPageHeader(headerData)

/**
 * テーブルをレンダリング
 *
 * @param {Object} tableData - テーブルデータ
 * @param {Array<Object>} tableData.columns - カラム定義
 * @param {Array<Object>} tableData.rows - 行データ
 * @param {Object} tableData.options - オプション
 * @returns {HTMLElement} - テーブル要素
 */
export function renderTable(tableData)

/**
 * フォームをレンダリング
 *
 * @param {Object} formData - フォームデータ
 * @param {Array<Object>} formData.fields - フィールド定義
 * @param {Function} formData.onSubmit - 送信ハンドラー
 * @returns {HTMLElement} - フォーム要素
 */
export function renderForm(formData)

/**
 * カードグリッドをレンダリング
 *
 * @param {Array<Object>} cards - カードデータ
 * @param {Object} options - オプション
 * @returns {HTMLElement} - カードグリッド要素
 */
export function renderCardGrid(cards, options = {})

/**
 * 詳細情報セクションをレンダリング
 *
 * @param {Object} detailData - 詳細データ
 * @returns {HTMLElement} - 詳細セクション要素
 */
export function renderDetailSection(detailData)
```

---

### 2.3 処理仕様

#### 2.3.1 分割プロセス

##### ステップ1: 依存関係の分析
```bash
# Phase F-2、F-3で作成したモジュールへの依存関係を確認
- api-client.js（APIアクセス）
- auth.js（認証）
- logger.js（ログ出力）
- search.js（検索機能）
- knowledge.js（ナレッジ管理）
- dom-helpers.js（DOM操作）
- date-formatter.js（日付フォーマット）
- validation.js（バリデーション）
- file-utils.js（ファイル操作）
```

##### ステップ2: 関数の分類と抽出
```javascript
// OLD (app.js内のグローバル関数)
function loadDashboard() {
  // ダッシュボード表示処理（約150行）
}

function loadKnowledgeList() {
  // ナレッジ一覧表示処理（約200行）
}

// NEW (app/data-loader.js)
import { getKnowledgeList } from '@features/knowledge.js';
import { renderTable } from '@pages/page-renderer.js';

export async function loadKnowledgeList() {
  const data = await getKnowledgeList();
  renderTable(data);
}
```

##### ステップ3: モジュール間の依存関係の整理
```javascript
// app/index.js（エントリーポイント）
import { initEnvironment, initAuthentication } from './init.js';
import { defineRoute, navigateTo } from './router.js';
import { loadPage } from './data-loader.js';

// 初期化
await initEnvironment();
await initAuthentication();

// ルート定義
defineRoute('/knowledge/:id', (params) => {
  loadPage('knowledge-detail', params);
});
```

##### ステップ4: 既存HTMLファイルの更新
```html
<!-- index.html -->
<script type="module">
  import { initApp } from '/src/app/index.js';

  // アプリケーション初期化
  initApp({
    isProduction: window.IS_PRODUCTION,
    apiEndpoints: {
      base: '/api/v1'
    }
  });
</script>
```

---

#### 2.3.2 後方互換性の維持

##### legacy-compat.js（後方互換性レイヤー）
```javascript
/**
 * 既存のグローバル関数を維持（段階的移行用）
 */
import { loadKnowledgeList } from './data-loader.js';
import { renderKnowledgeDetail } from '@pages/knowledge-detail.js';

// 既存のグローバル関数をwindow経由で公開
if (typeof window !== 'undefined') {
  window.loadKnowledgeList = loadKnowledgeList;
  window.showKnowledgeDetail = renderKnowledgeDetail;

  // 非推奨警告
  console.warn('[Deprecation] グローバル関数は非推奨です。ESモジュールをimportしてください。');
}
```

---

#### 2.3.3 テスト戦略

##### ユニットテスト（Jest）
```javascript
// tests/unit/app/router.test.js
import { defineRoute, navigateTo, getCurrentPath } from '@app/router.js';

describe('Router', () => {
  test('defineRoute should register route', () => {
    const handler = jest.fn();
    defineRoute('/knowledge/:id', handler);
    // ...
  });

  test('navigateTo should change path', () => {
    navigateTo('/knowledge/123');
    expect(getCurrentPath()).toBe('/knowledge/123');
  });
});
```

##### 統合テスト（Playwright）
```javascript
// tests/e2e/knowledge-detail.spec.js
import { test, expect } from '@playwright/test';

test('ナレッジ詳細を表示できる', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.click('a[href="/knowledge/1"]');
  await expect(page.locator('h1')).toContainText('ナレッジタイトル');
});
```

---

### 2.4 出力仕様

#### 2.4.1 正常時レスポンス

##### app/index.js
```javascript
// initApp()
{
  success: true,
  message: 'アプリケーションを初期化しました',
  user: { id: 1, username: 'test_user', role: 'admin' }
}
```

##### pages/knowledge-detail.js
```javascript
// renderKnowledgeDetail()
<div class="knowledge-detail">
  <h1>ナレッジタイトル</h1>
  <div class="knowledge-content">
    ナレッジ本文
  </div>
  <div class="knowledge-meta">
    作成日: 2026年2月10日
    作成者: test_user
  </div>
</div>
```

---

#### 2.4.2 異常時エラー

```javascript
// initApp() - 認証失敗
throw new Error('認証に失敗しました。ログイン画面に移動します。');

// renderKnowledgeDetail() - ナレッジが見つからない
throw new Error('ナレッジが見つかりません');

// loadPage() - 不正なページ名
throw new Error('不正なページ名です: invalid-page');
```

---

## 3. ビジネスルール

### 3.1 ファイルサイズの制約
- 1ファイルあたり500行以内を目標
- 最大でも1,000行を超えない
- 関数は50行以内を推奨

### 3.2 命名規則の統一
- **ファイル名**: ケバブケース（`knowledge-detail.js`）
- **関数名**: キャメルケース（`renderKnowledgeDetail`）
- **クラス名**: パスカルケース（`KnowledgeRenderer`）
- **定数**: SCREAMING_SNAKE_CASE（`MAX_PAGE_SIZE`）

### 3.3 循環依存の禁止
- モジュール間の循環依存は禁止
- 依存関係は一方向のみ
- 共通ロジックは別モジュールに抽出

### 3.4 グローバル変数の削除
- すべてのグローバル変数をモジュールスコープに変更
- `window` オブジェクトへの直接代入は禁止（後方互換性レイヤーを除く）

---

## 4. 制約事項

### 4.1 技術的制約
- **ブラウザ対応**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **ESモジュール**: 完全なESモジュール構文への移行
- **Viteビルド**: 開発時はVite Dev Server必須
- **既存機能**: すべての既存機能は動作継続

### 4.2 パフォーマンス制約
- ページロード時間は既存と同等（±10%以内）
- 初回ロード時間は500ms以内（キャッシュなし）
- Viteビルド後のファイルサイズは既存と同等（圧縮後）

### 4.3 互換性制約
- 既存HTMLファイルは動作継続
- 既存のスクリプトタグは段階的に移行可能
- 後方互換性レイヤーは Phase F-5 で削除予定

---

## 5. 受け入れ基準

### 5.1 実装完了基準
- [ ] app.js が8ファイルに分割されている（1ファイル500行以内）
- [ ] detail-pages.js が8ファイルに分割されている（1ファイル500行以内）
- [ ] すべての関数にJSDocコメントが付与されている
- [ ] ESモジュール構文（import/export）を使用している
- [ ] Phase F-2、F-3のモジュールを活用している
- [ ] 循環依存が発生していない

### 5.2 品質基準
- [ ] ESLintエラーが0件
- [ ] Prettierフォーマット済み
- [ ] すべてのモジュールに単体テストがある（Jest）
- [ ] テストカバレッジが90%以上
- [ ] E2Eテストがすべて成功する（Playwright）

### 5.3 パフォーマンス基準
- [ ] ページロード時間が既存と同等（±10%以内）
- [ ] Viteビルド時間が20秒以内
- [ ] ビルド成果物（dist/）が既存と同等（圧縮後）
- [ ] Lighthouse Performanceスコアが90点以上

### 5.4 後方互換性基準
- [ ] 既存HTMLファイルから正常に呼び出せる
- [ ] 既存のスクリプトタグが動作継続
- [ ] 後方互換性レイヤー（legacy-compat.js）が正常動作

### 5.5 ドキュメント基準
- [ ] 各モジュールのREADME.mdが存在する
- [ ] API仕様書が更新されている
- [ ] 移行ガイドが作成されている
- [ ] リファクタリングレポートが作成されている

---

## 6. マイグレーション計画

### 6.1 Phase F-4-1: app.js 分割（Week 1）

| ステップ | 作業内容 | 期間 |
|---------|---------|------|
| 1 | 依存関係分析 | 1日 |
| 2 | 8ファイルに分割 | 2日 |
| 3 | 単体テスト作成 | 1日 |
| 4 | E2Eテスト実行 | 0.5日 |
| 5 | レビュー・修正 | 0.5日 |

**成果物**:
- webui/src/app/ ディレクトリ（8ファイル）
- tests/unit/app/ ディレクトリ（単体テスト）
- docs/PHASE_F4_APP_REFACTORING.md

---

### 6.2 Phase F-4-2: detail-pages.js 分割（Week 2）

| ステップ | 作業内容 | 期間 |
|---------|---------|------|
| 1 | 依存関係分析 | 1日 |
| 2 | 8ファイルに分割 | 2日 |
| 3 | 単体テスト作成 | 1日 |
| 4 | E2Eテスト実行 | 0.5日 |
| 5 | レビュー・修正 | 0.5日 |

**成果物**:
- webui/src/pages/ ディレクトリ（8ファイル）
- tests/unit/pages/ ディレクトリ（単体テスト）
- docs/PHASE_F4_DETAIL_PAGES_REFACTORING.md

---

### 6.3 Phase F-4-3: 既存HTMLファイル更新（Week 3）

| ステップ | 作業内容 | 期間 |
|---------|---------|------|
| 1 | index.html 更新 | 0.5日 |
| 2 | その他HTMLファイル更新 | 1日 |
| 3 | E2Eテスト全実行 | 0.5日 |
| 4 | パフォーマンステスト | 0.5日 |
| 5 | 最終レビュー・修正 | 0.5日 |

**成果物**:
- 更新されたHTMLファイル（19ファイル）
- docs/PHASE_F4_COMPLETION_REPORT.md

---

## 7. リスク管理

### 7.1 リスク一覧

| リスク | 影響度 | 発生確率 | 対策 |
|-------|-------|---------|------|
| 既存機能の動作不良 | High | Medium | E2Eテストの徹底、段階的移行 |
| パフォーマンス劣化 | Medium | Low | パフォーマンステストの実施 |
| 循環依存の発生 | Medium | Medium | 依存関係の事前分析、ESLintチェック |
| 後方互換性の喪失 | High | Low | legacy-compat.js による互換性維持 |

---

## 8. 非機能要件（参照）

非機能要件の詳細は `phase_f4_non_functional.md` を参照してください。

---

## 9. 運用定義（参照）

運用定義の詳細は `phase_f4_operations.md` を参照してください。

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-02-10 | 初版作成 | spec-planner SubAgent |

---

**このドキュメントは ITSM および ISO 27001/9001 に準拠しています。**
