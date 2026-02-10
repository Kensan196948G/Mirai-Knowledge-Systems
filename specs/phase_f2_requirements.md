# Phase F-2: 機能モジュール分割 - 機能要件書

**バージョン**: 1.0.0
**作成日**: 2026-02-10
**作成者**: spec-planner SubAgent
**ステータス**: Draft

---

## 1. 概要

### 1.1 機能名
Phase F-2: 機能モジュール分割（Feature Modules Separation）

### 1.2 目的
- 既存の機能別JavaScriptファイルをESモジュール化
- `webui/src/features/` ディレクトリへの統合
- Viteビルドシステムでの最適なバンドリング
- 既存HTMLファイルとの後方互換性維持

### 1.3 優先度
**High** - フロントエンドアーキテクチャの中核を成す

### 1.4 担当者
- **実装**: code-implementer SubAgent
- **レビュー**: code-reviewer SubAgent
- **テスト設計**: test-designer SubAgent

### 1.5 前提条件
- Phase F-1完了（Viteビルドシステム、コアモジュール）
- 既存機能モジュールの動作確認済み
- ES6+モジュール構文の採用

---

## 2. 機能仕様

### 2.1 対象モジュール

以下の5つの機能モジュールを `webui/src/features/` に移行します。

#### 2.1.1 search.js
- **目的**: 統合検索機能のモジュール化
- **元ファイル**: app.js内の検索関連関数
- **想定行数**: 約300行
- **依存**: api-client.js, logger.js

#### 2.1.2 knowledge.js
- **目的**: ナレッジ管理機能のモジュール化
- **元ファイル**: app.js内のナレッジCRUD関数
- **想定行数**: 約400行
- **依存**: api-client.js, logger.js, dom-helpers.js

#### 2.1.3 mfa.js
- **目的**: 既存MFA機能のESモジュール化
- **元ファイル**: webui/mfa.js（351行）
- **想定行数**: 約380行（JSDoc追加）
- **依存**: api-client.js, logger.js

#### 2.1.4 ms365-sync.js
- **目的**: 既存MS365同期機能のESモジュール化
- **元ファイル**: webui/ms365-sync.js（852行）
- **想定行数**: 約900行（JSDoc追加）
- **依存**: api-client.js, logger.js, dom-helpers.js

#### 2.1.5 pwa.js
- **目的**: PWA関連機能の統合
- **元ファイル**:
  - webui/install-prompt.js（220行）
  - webui/cache-manager.js（200行）
  - webui/sync-manager.js（240行）
  - webui/crypto-helper.js（180行）
- **想定行数**: 約900行（統合＋JSDoc）
- **依存**: logger.js

---

### 2.2 入力仕様

#### 2.2.1 search.js

##### モジュールAPI
```javascript
/**
 * 統合検索を実行
 *
 * @param {string} query - 検索クエリ
 * @param {Object} options - 検索オプション
 * @param {string[]} options.types - 検索対象タイプ (knowledge, sop, law, expert)
 * @param {number} options.page - ページ番号（1から）
 * @param {number} options.pageSize - 1ページあたりの件数
 * @param {string} options.sortBy - ソート項目 (created_at, updated_at, title)
 * @param {string} options.order - ソート順序 (asc, desc)
 * @returns {Promise<Object>} - 検索結果
 */
export async function searchUnified(query, options = {})

/**
 * 検索履歴を取得
 *
 * @param {number} limit - 取得件数（デフォルト: 10）
 * @returns {Promise<Array>} - 検索履歴
 */
export async function getSearchHistory(limit = 10)

/**
 * 検索履歴に追加
 *
 * @param {string} query - 検索クエリ
 * @param {string[]} types - 検索対象タイプ
 * @returns {Promise<void>}
 */
export async function addSearchHistory(query, types)

/**
 * 人気検索ワードを取得
 *
 * @param {number} limit - 取得件数（デフォルト: 10）
 * @returns {Promise<Array>} - 人気検索ワード
 */
export async function getPopularSearchKeywords(limit = 10)
```

---

#### 2.2.2 knowledge.js

##### モジュールAPI
```javascript
/**
 * ナレッジ一覧を取得
 *
 * @param {Object} options - フィルタオプション
 * @param {string} options.category - カテゴリ
 * @param {string} options.search - 検索キーワード
 * @param {string} options.tags - タグ（カンマ区切り）
 * @param {number} options.page - ページ番号
 * @param {number} options.perPage - 1ページあたりの件数
 * @returns {Promise<Object>} - ナレッジ一覧とページネーション情報
 */
export async function getKnowledgeList(options = {})

/**
 * ナレッジ詳細を取得
 *
 * @param {number} knowledgeId - ナレッジID
 * @returns {Promise<Object>} - ナレッジ詳細
 */
export async function getKnowledgeDetail(knowledgeId)

/**
 * ナレッジを作成
 *
 * @param {Object} knowledgeData - ナレッジデータ
 * @param {string} knowledgeData.title - タイトル（必須）
 * @param {string} knowledgeData.content - 本文（必須）
 * @param {string} knowledgeData.category - カテゴリ
 * @param {string[]} knowledgeData.tags - タグ
 * @param {string} knowledgeData.visibility - 公開範囲 (public, private, limited)
 * @returns {Promise<Object>} - 作成されたナレッジ
 */
export async function createKnowledge(knowledgeData)

/**
 * ナレッジを更新
 *
 * @param {number} knowledgeId - ナレッジID
 * @param {Object} knowledgeData - 更新データ
 * @returns {Promise<Object>} - 更新されたナレッジ
 */
export async function updateKnowledge(knowledgeId, knowledgeData)

/**
 * ナレッジを削除
 *
 * @param {number} knowledgeId - ナレッジID
 * @returns {Promise<void>}
 */
export async function deleteKnowledge(knowledgeId)

/**
 * 人気ナレッジを取得
 *
 * @param {number} limit - 取得件数（デフォルト: 10）
 * @returns {Promise<Array>} - 人気ナレッジ
 */
export async function getPopularKnowledge(limit = 10)
```

---

#### 2.2.3 mfa.js

##### モジュールAPI
```javascript
/**
 * MFAステータスを取得
 *
 * @returns {Promise<Object>} - MFA有効/無効状態
 */
export async function getMFAStatus()

/**
 * MFAセットアップを開始（QRコード生成）
 *
 * @returns {Promise<Object>} - QRコードURL、シークレット
 */
export async function startMFASetup()

/**
 * MFAセットアップを完了（TOTP検証）
 *
 * @param {string} totpCode - 6桁のTOTPコード
 * @returns {Promise<Object>} - バックアップコード
 */
export async function completeMFASetup(totpCode)

/**
 * MFAを無効化
 *
 * @param {string} password - 現在のパスワード
 * @returns {Promise<void>}
 */
export async function disableMFA(password)

/**
 * MFA検証を実行（ログイン時）
 *
 * @param {string} mfaToken - MFAトークン
 * @param {string} code - TOTPコードまたはバックアップコード
 * @returns {Promise<Object>} - JWTトークン
 */
export async function verifyMFA(mfaToken, code)

/**
 * バックアップコードを再生成
 *
 * @param {string} password - 現在のパスワード
 * @returns {Promise<Array>} - 新しいバックアップコード
 */
export async function regenerateBackupCodes(password)
```

---

#### 2.2.4 ms365-sync.js

##### モジュールAPI
```javascript
/**
 * MS365同期設定一覧を取得
 *
 * @returns {Promise<Array>} - 同期設定一覧
 */
export async function getSyncConfigs()

/**
 * MS365同期設定を作成
 *
 * @param {Object} config - 同期設定
 * @param {string} config.name - 設定名
 * @param {string} config.source_type - ソースタイプ (sharepoint, onedrive)
 * @param {string} config.source_path - ソースパス
 * @param {string} config.schedule - cronスケジュール
 * @returns {Promise<Object>} - 作成された設定
 */
export async function createSyncConfig(config)

/**
 * MS365同期設定を更新
 *
 * @param {number} configId - 設定ID
 * @param {Object} config - 更新データ
 * @returns {Promise<Object>} - 更新された設定
 */
export async function updateSyncConfig(configId, config)

/**
 * MS365同期設定を削除
 *
 * @param {number} configId - 設定ID
 * @returns {Promise<void>}
 */
export async function deleteSyncConfig(configId)

/**
 * MS365同期を手動実行
 *
 * @param {number} configId - 設定ID
 * @returns {Promise<Object>} - 実行結果
 */
export async function executeSyncNow(configId)

/**
 * MS365同期履歴を取得
 *
 * @param {number} configId - 設定ID（オプション）
 * @param {number} limit - 取得件数（デフォルト: 50）
 * @returns {Promise<Array>} - 同期履歴
 */
export async function getSyncHistory(configId = null, limit = 50)

/**
 * MS365接続テストを実行
 *
 * @returns {Promise<Object>} - 接続状態
 */
export async function testMS365Connection()

/**
 * cron形式を日本語に変換
 *
 * @param {string} cronExpression - cron形式
 * @returns {string} - 日本語表記
 */
export function cronToJapanese(cronExpression)
```

---

#### 2.2.5 pwa.js

##### モジュールAPI
```javascript
/**
 * PWAインストールプロンプトを表示
 *
 * @returns {Promise<void>}
 */
export async function showInstallPrompt()

/**
 * PWAインストール可能状態を確認
 *
 * @returns {boolean} - インストール可能かどうか
 */
export function isInstallable()

/**
 * キャッシュマネージャーを初期化
 *
 * @param {Object} options - キャッシュオプション
 * @param {number} options.maxSize - 最大サイズ（MB）（デフォルト: 50）
 * @param {number} options.startCleanupAt - クリーンアップ開始サイズ（MB）（デフォルト: 45）
 * @returns {void}
 */
export function initCacheManager(options = {})

/**
 * キャッシュをクリア
 *
 * @returns {Promise<void>}
 */
export async function clearCache()

/**
 * 同期マネージャーを初期化
 *
 * @returns {void}
 */
export function initSyncManager()

/**
 * データを同期キューに追加
 *
 * @param {string} tag - 同期タグ
 * @param {Object} data - 同期データ
 * @returns {Promise<void>}
 */
export async function queueSync(tag, data)

/**
 * JWT暗号化（PBKDF2 + AES-GCM）
 *
 * @param {string} token - JWTトークン
 * @param {string} email - ユーザーEmail
 * @returns {Promise<string>} - 暗号化されたトークン（Base64）
 */
export async function encryptToken(token, email)

/**
 * JWT復号化
 *
 * @param {string} encryptedToken - 暗号化されたトークン（Base64）
 * @param {string} email - ユーザーEmail
 * @returns {Promise<string>} - 復号化されたJWTトークン
 */
export async function decryptToken(encryptedToken, email)

/**
 * PWA統計情報を取得
 *
 * @returns {Promise<Object>} - キャッシュサイズ、同期キュー数、Service Worker状態
 */
export async function getPWAStats()
```

---

### 2.3 処理仕様

#### 2.3.1 モジュール変換プロセス

各モジュールは以下のステップで変換します。

##### ステップ1: 関数抽出
```javascript
// OLD (app.js内のグローバル関数)
function searchKnowledge(query, options) {
  // ...
}

// NEW (search.js内のexport関数)
export async function searchKnowledge(query, options) {
  // ...
}
```

##### ステップ2: 依存モジュールのimport
```javascript
// NEW (search.js冒頭)
import { fetchAPI } from '@core/api-client.js';
import { logger } from '@core/logger.js';
```

##### ステップ3: window経由の公開（後方互換性）
```javascript
// NEW (search.js末尾)
if (typeof window !== 'undefined') {
  window.MKS_Search = {
    searchUnified,
    getSearchHistory,
    addSearchHistory,
    getPopularSearchKeywords
  };
}
```

##### ステップ4: JSDoc完全化
```javascript
/**
 * 統合検索を実行
 *
 * @param {string} query - 検索クエリ
 * @param {Object} options - 検索オプション
 * @param {string[]} options.types - 検索対象タイプ (knowledge, sop, law, expert)
 * @param {number} options.page - ページ番号（1から）
 * @param {number} options.pageSize - 1ページあたりの件数
 * @param {string} options.sortBy - ソート項目 (created_at, updated_at, title)
 * @param {string} options.order - ソート順序 (asc, desc)
 * @returns {Promise<Object>} - 検索結果
 * @throws {Error} - API呼び出し失敗時
 *
 * @example
 * const result = await searchUnified('建設', {
 *   types: ['knowledge', 'sop'],
 *   page: 1,
 *   pageSize: 20,
 *   sortBy: 'created_at',
 *   order: 'desc'
 * });
 */
export async function searchUnified(query, options = {}) {
  // ...
}
```

---

#### 2.3.2 既存コードの段階的移行

##### フェーズ1: モジュール作成（実装完了直後）
```
webui/src/features/
├── search.js        # NEW
├── knowledge.js     # NEW
├── mfa.js           # NEW (webui/mfa.js からコピー)
├── ms365-sync.js    # NEW (webui/ms365-sync.js からコピー)
└── pwa.js           # NEW (統合)
```

##### フェーズ2: 既存ファイル更新（実装完了後）
```javascript
// webui/app.js の冒頭に追加
import { searchUnified, getSearchHistory } from './src/features/search.js';
import { getKnowledgeList, createKnowledge } from './src/features/knowledge.js';
// ... 既存のグローバル関数を削除し、importした関数を使用
```

##### フェーズ3: 既存HTMLファイル更新（実装完了後）
```html
<!-- index.html -->
<script type="module">
  import { searchUnified } from '/src/features/search.js';
  import { getKnowledgeList } from '/src/features/knowledge.js';

  // 既存のwindow経由の呼び出しも互換性維持
  window.searchKnowledge = searchUnified;
</script>
```

---

### 2.4 出力仕様

#### 2.4.1 正常時レスポンス

各モジュール関数は以下の形式でレスポンスを返却します。

##### search.js
```javascript
// searchUnified()
{
  results: [
    { id: 1, type: 'knowledge', title: 'タイトル', content: '本文' },
    { id: 2, type: 'sop', title: 'SOP名', content: '手順' }
  ],
  total: 120,
  page: 1,
  page_size: 20,
  total_pages: 6
}
```

##### knowledge.js
```javascript
// getKnowledgeList()
{
  knowledge_list: [
    { id: 1, title: 'ナレッジ1', content: '本文', tags: ['建設', '安全'] }
  ],
  total: 50,
  page: 1,
  per_page: 20,
  total_pages: 3
}

// createKnowledge()
{
  success: true,
  message: 'ナレッジを作成しました',
  knowledge: { id: 123, title: '新規ナレッジ', ... }
}
```

##### mfa.js
```javascript
// getMFAStatus()
{
  mfa_enabled: true,
  backup_codes_count: 8
}

// completeMFASetup()
{
  success: true,
  message: 'MFAセットアップが完了しました',
  backup_codes: ['12345678', '87654321', ...]
}
```

##### ms365-sync.js
```javascript
// getSyncConfigs()
{
  success: true,
  configs: [
    { id: 1, name: '建設資料', source_type: 'sharepoint', enabled: true }
  ]
}

// executeSyncNow()
{
  success: true,
  message: '同期を開始しました',
  history_id: 456
}
```

##### pwa.js
```javascript
// getPWAStats()
{
  cache_size_mb: 12.5,
  sync_queue_count: 3,
  service_worker_active: true,
  last_update: '2026-02-10T12:00:00Z'
}
```

---

#### 2.4.2 異常時エラー

##### エラーコード体系
```javascript
// APIエラー（HTTP Status）
{
  error: 'Bad Request',
  message: 'パラメータが不正です',
  status: 400
}

// 認証エラー
{
  error: 'Unauthorized',
  message: 'トークンが無効です',
  status: 401
}

// 権限エラー
{
  error: 'Forbidden',
  message: '操作権限がありません',
  status: 403
}

// リソース未発見
{
  error: 'Not Found',
  message: 'ナレッジが見つかりません',
  status: 404
}

// サーバーエラー
{
  error: 'Internal Server Error',
  message: 'サーバーエラーが発生しました',
  status: 500
}
```

##### エラーハンドリング例
```javascript
try {
  const result = await searchUnified('建設', options);
  // 成功処理
} catch (error) {
  if (error.status === 401) {
    // 認証エラー → ログイン画面へリダイレクト
    window.location.href = '/login.html';
  } else if (error.status === 403) {
    // 権限エラー → エラーメッセージ表示
    alert('操作権限がありません');
  } else {
    // その他のエラー → エラーログ記録
    logger.error('Search failed:', error);
    alert('検索に失敗しました');
  }
}
```

---

## 3. ビジネスルール

### 3.1 モジュール命名規則
- **ファイル名**: ケバブケース（`search.js`, `ms365-sync.js`）
- **関数名**: キャメルケース（`searchUnified`, `getSyncConfigs`）
- **定数**: SCREAMING_SNAKE_CASE（`MAX_RESULTS`, `DEFAULT_PAGE_SIZE`）

### 3.2 後方互換性維持
- すべてのモジュール関数は `window.MKS_*` 経由でも呼び出し可能
- 既存HTMLファイルのスクリプトは動作継続
- 段階的な移行を許容（1ファイルずつ移行可能）

### 3.3 エラーハンドリング統一
- すべての非同期関数は `async/await` を使用
- エラーは `throw new Error()` で伝播
- `try/catch` は呼び出し側で実施
- エラーログは `logger.error()` で記録

### 3.4 依存関係の最小化
- コアモジュール（api-client, auth, logger）のみ依存
- 機能モジュール間の相互依存は禁止
- ユーティリティモジュール（Phase F-3）への依存は許可

---

## 4. 制約事項

### 4.1 技術的制約
- **ブラウザ対応**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **ESモジュール**: `type="module"` での読み込み必須
- **Viteビルド**: 開発時はVite Dev Server必須
- **既存コード**: app.js、detail-pages.js は Phase F-4 で分割

### 4.2 パフォーマンス制約
- 各モジュールは単独で100KB以下（圧縮前）
- 初回ロード時間は500ms以内（キャッシュなし）
- Viteビルド後のチャンクサイズは適切に分割

### 4.3 セキュリティ制約
- JWTトークンはSecure Storage（暗号化）に保存
- XSS対策: DOM APIを使用（innerHTML禁止）
- CSRF対策: トークンをHTTPヘッダーで送信

---

## 5. 受け入れ基準

### 5.1 実装完了基準
- [ ] 5つの機能モジュールが `webui/src/features/` に配置されている
- [ ] すべての関数にJSDocコメントが付与されている
- [ ] ESモジュール構文（import/export）を使用している
- [ ] `window.MKS_*` 経由でも呼び出し可能（後方互換性）
- [ ] 既存HTMLファイルから正常に呼び出せる

### 5.2 品質基準
- [ ] ESLintエラーが0件
- [ ] Prettierフォーマット済み
- [ ] すべての関数に単体テストがある（Jest）
- [ ] E2Eテストが成功する（Playwright）

### 5.3 パフォーマンス基準
- [ ] Viteビルド時間が10秒以内
- [ ] ビルド成果物（dist/）が5MB以下（圧縮前）
- [ ] Lighthouse Performanceスコアが90点以上

### 5.4 ドキュメント基準
- [ ] 各モジュールのREADME.mdが存在する
- [ ] API仕様書が更新されている
- [ ] 移行ガイドが作成されている

---

## 6. 非機能要件（参照）

非機能要件の詳細は `phase_f2_non_functional.md` を参照してください。

---

## 7. 運用定義（参照）

運用定義の詳細は `phase_f2_operations.md` を参照してください。

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-02-10 | 初版作成 | spec-planner SubAgent |

---

**このドキュメントは ITSM および ISO 27001/9001 に準拠しています。**
