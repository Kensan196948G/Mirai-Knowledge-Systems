# Phase E-4: MS365ファイルプレビュー機能 - アーキテクチャレビュー

**Version**: 1.0.0
**レビュー日**: 2026-02-06
**レビュアー**: arch-reviewer (Claude AI)
**仕様書**: specs/PHASE_E4_FILE_PREVIEW_SPEC.md (v1.0.0)

---

## 📋 目次

1. [エグゼクティブサマリー](#1-エグゼクティブサマリー)
2. [レビュー観点](#2-レビュー観点)
3. [既存コードベース適合性分析](#3-既存コードベース適合性分析)
4. [PWA統合の整合性分析](#4-pwa統合の整合性分析)
5. [セキュリティ観点分析](#5-セキュリティ観点分析)
6. [パフォーマンス観点分析](#6-パフォーマンス観点分析)
7. [テスト観点分析](#7-テスト観点分析)
8. [懸念事項と改善提案](#8-懸念事項と改善提案)
9. [総合判定](#9-総合判定)

---

## 1. エグゼクティブサマリー

### 1.1 レビュー結果

**判定**: **PASS_WITH_WARNINGS** ⚠️

Phase E-4仕様書は、全体として実装可能な品質に達していますが、**5つの中程度の懸念事項**があります。これらの懸念事項は実装前に対処することで、より堅牢なシステムを構築できます。

### 1.2 主要な強み

1. ✅ **既存PWA基盤との整合性**: Service Worker/CacheManagerとの統合設計が適切
2. ✅ **セキュリティ対策の網羅性**: STRIDE分析、XSS対策、CSP設定が明確
3. ✅ **詳細な実装仕様**: FilePreviewManagerクラスのフルコード提供で実装の曖昧さが排除
4. ✅ **テスト戦略の明確性**: E2E 8件のテストケースが具体的

### 1.3 主要な懸念事項

1. ⚠️ **app.js統合の複雑性**: 3,875行の既存コードへの影響範囲が不明確
2. ⚠️ **ms365-sync.js修正の具体性不足**: サムネイル統合のDOM操作詳細が不足
3. ⚠️ **Service Workerバージョン管理**: キャッシュ名の競合リスク
4. ⚠️ **オフライン対応の実装ギャップ**: 仕様と既存PWA実装の整合性に不明点
5. ⚠️ **パフォーマンス測定の実装不足**: Prometheusメトリクスの計測タイミングが不明

---

## 2. レビュー観点

### 2.1 レビュー範囲

| 観点 | 重要度 | レビュー対象 |
|------|--------|------------|
| 既存コードベース適合性 | 🔴 Critical | app.js, ms365-sync.js統合 |
| PWA統合の整合性 | 🔴 Critical | sw.js, cache-manager.js修正 |
| セキュリティ観点 | 🔴 Critical | XSS, CSP, STRIDE分析 |
| パフォーマンス観点 | 🟡 High | キャッシュ戦略、LRU削除 |
| テスト観点 | 🟡 High | E2Eテストカバレッジ |

### 2.2 評価基準

- **PASS**: すべての観点でブロッキング問題なし
- **PASS_WITH_WARNINGS**: 実装可能だが改善推奨事項あり（中程度の懸念事項）
- **FAIL**: 設計の根本的な問題があり、実装前の修正必須

---

## 3. 既存コードベース適合性分析

### 3.1 app.js (3,875行) との統合

#### 3.1.1 現状分析

**既存の環境設定**:
```javascript
// app.js: Line 26-54
const IS_PRODUCTION = (() => {
  // URLパラメータ、localStorage、ポート番号、ホスト名で環境判定
})();
```

**既存の認証管理**:
```javascript
// app.js: Line 103-136
function checkAuth() { /* JWT検証 */ }
function getCurrentUser() { /* ユーザー情報取得 */ }
```

**既存のRBAC**:
```javascript
// app.js: Line 146-268
const ROLE_HIERARCHY = { partner: 1, quality_assurance: 2, construction_manager: 3, admin: 4 };
function checkPermission(requiredRole) { /* 権限チェック */ }
```

**既存のAPI Client**:
```javascript
// app.js: Line 341-479
async function refreshAccessToken() { /* トークンリフレッシュ */ }
async function fetchAPI(endpoint, options = {}) { /* JWT付きリクエスト */ }
```

#### 3.1.2 統合設計の評価

| 項目 | 仕様書の設計 | 既存コードとの整合性 | 評価 |
|------|------------|---------------------|------|
| 認証方式 | `localStorage.getItem('access_token')` | ✅ app.js L104と一致 | **PASS** |
| API Base URL | `/api/v1/integrations/microsoft365/files` | ✅ `${API_BASE}${endpoint}` パターンと一致 | **PASS** |
| トークンリフレッシュ | 仕様書に記載なし | ⚠️ app.js L341-375に実装あり | **WARNING** |
| エラーハンドリング | `handleError(error)` | ✅ app.js L435-466と類似 | **PASS** |

**懸念事項 #1: トークンリフレッシュの欠落**

仕様書の`FilePreviewManager.fetchPreviewUrl()`（Line 742-760）は、401エラー時のトークンリフレッシュ処理が含まれていません。

**現状のapp.js実装**:
```javascript
// app.js: Line 408-432
if (response.status === 401 && !endpoint.includes('/auth/')) {
  const refreshed = await refreshAccessToken();
  if (refreshed) {
    // リクエストをリトライ
    response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  }
}
```

**推奨修正**:
```javascript
// file-preview.js: fetchPreviewUrl()に追加
if (!response.ok && response.status === 401) {
  // app.jsのrefreshAccessToken()を再利用
  const refreshed = await window.refreshAccessToken?.();
  if (refreshed) {
    const newToken = localStorage.getItem('access_token');
    response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${newToken}`,
        'Content-Type': 'application/json'
      }
    });
  }
}
```

---

### 3.2 ms365-sync.js (840行) との統合

#### 3.2.1 現状分析

**既存のDOM構築パターン**:
```javascript
// ms365-sync.js: Line 262-275
function renderConfigList(configs) {
  const tbody = document.getElementById('configListBody');
  tbody.textContent = ''; // XSS対策: 既存内容をクリア

  // DOM API使用
  const tr = document.createElement('tr');
  const td = document.createElement('td');
  td.textContent = config.name || 'Unnamed';
  tr.appendChild(td);
}
```

**既存のAPI呼び出しパターン**:
```javascript
// ms365-sync.js: Line 39-57
async function loadSyncConfigs() {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${API_BASE}/api/v1/integrations/microsoft365/sync/configs`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  // エラーハンドリング
  if (!response.ok) {
    throw new Error(data.error?.message || 'Failed to load sync configs');
  }
}
```

#### 3.2.2 統合設計の評価

| 項目 | 仕様書の設計 | 既存コードとの整合性 | 評価 |
|------|------------|---------------------|------|
| DOM構築方法 | `createElement()` | ✅ ms365-sync.js L262-275と一致 | **PASS** |
| XSS対策 | innerHTML禁止 | ✅ 既存コードも`textContent`使用 | **PASS** |
| API呼び出し | `fetch()` with JWT | ✅ パターン一致 | **PASS** |
| エラーハンドリング | `throw new Error()` | ✅ 既存と同じパターン | **PASS** |

**懸念事項 #2: ms365-sync.js修正の具体性不足**

仕様書の付録B（Line 1844-1928）には、`renderSyncHistoryRow()`の実装例がありますが、**既存のms365-sync.jsにこの関数が存在するかどうかが不明**です。

**調査が必要な箇所**:
1. 同期履歴テーブルのレンダリング関数名（`renderSyncHistoryRow()`が既存かどうか）
2. サムネイル列の追加位置（既存テーブル構造の確認）
3. `formatCronSchedule()`などのヘルパー関数の存在確認

**推奨アクション**:
```bash
# 実装前の調査コマンド
grep -n "renderSyncHistoryRow" webui/ms365-sync.js
grep -n "sync-history-table" webui/ms365-sync-settings.html
```

---

### 3.3 グローバル変数の競合リスク

#### 3.3.1 仕様書のグローバル変数

```javascript
// file-preview.js: Line 1053
const filePreviewManager = new FilePreviewManager();
```

#### 3.3.2 既存のグローバル変数

```javascript
// app.js: Line 92
window.logger = logger;

// app.js: Line 69-73
window.MKS_ENV = { isProduction, envName, ports };
```

**評価**: ✅ **PASS** - `filePreviewManager`という名前は既存のグローバル変数と競合しない

---

## 4. PWA統合の整合性分析

### 4.1 Service Worker (sw.js) 統合

#### 4.1.1 現状のキャッシュ構造

```javascript
// sw.js: Line 12-20
const SW_VERSION = 'v1.3.0';
const CACHE_NAMES = {
  static: `mks-static-v1.3.0`,
  api: `mks-api-v1.3.0`,
  images: `mks-images-v1.3.0`,
};
```

#### 4.1.2 仕様書の追加キャッシュ

```javascript
// 仕様書: Line 1152-1159
const CACHE_NAMES = {
  static: `${CACHE_PREFIX}static-${SW_VERSION}`,
  api: `${CACHE_PREFIX}api-${SW_VERSION}`,
  images: `${CACHE_PREFIX}images-${SW_VERSION}`,
  thumbnails: `${CACHE_PREFIX}thumbnails-${SW_VERSION}`,  // 新規追加
  previews: `${CACHE_PREFIX}previews-${SW_VERSION}`       // 新規追加
};
```

**懸念事項 #3: Service Workerバージョン管理**

仕様書では`SW_VERSION`を変更せずにキャッシュ名を追加していますが、これでは**既存のService Workerが更新されない**リスクがあります。

**問題点**:
- 既存のSW_VERSION = `v1.3.0`
- 仕様書で追加する変更 → `v1.4.0`にバージョンアップすべき
- しかし、仕様書にはバージョン更新の記載なし

**推奨修正**:
```javascript
// sw.js: Line 12を修正
const SW_VERSION = 'v1.4.0'; // v1.3.0 → v1.4.0にバージョンアップ

const CACHE_NAMES = {
  static: `mks-static-v1.4.0`,
  api: `mks-api-v1.4.0`,
  images: `mks-images-v1.4.0`,
  thumbnails: `mks-thumbnails-v1.4.0`,  // 新規
  previews: `mks-previews-v1.4.0`       // 新規
};
```

**影響範囲**:
- Service Worker自動更新トリガー（24時間ごと、またはページリロード時）
- 既存キャッシュの削除（activate イベントで処理、sw.js L105-128）
- PWA_IMPLEMENTATION_GUIDE.mdの更新必要

---

#### 4.1.3 キャッシュ戦略の評価

| ファイルタイプ | 仕様書の戦略 | 既存のsw.js戦略 | 整合性 |
|--------------|------------|----------------|--------|
| サムネイル | Cache First (7日) | - | ✅ 新規追加 |
| プレビューURL | Network First (1時間) | - | ✅ 新規追加 |
| Office Embed iframe | - | - | ⚠️ 戦略未定義 |

**懸念事項 #4: Office Online Embed URLのキャッシュ戦略**

仕様書のプレビュー戦略（Line 1228-1247）では、`/api/.../preview`エンドポイントのレスポンス（`preview_url`を含むJSON）をキャッシュしますが、**iframe内で読み込まれるOffice Online自体はキャッシュされません**。

**問題点**:
- `preview_url` = `https://view.officeapps.live.com/op/embed.aspx?src=...`
- このURLは外部サービス（Microsoft）のため、Service Workerでキャッシュ不可
- オフライン時に`preview_url`はキャッシュから取得できても、iframe表示は失敗する

**推奨対応**:
```javascript
// file-preview.js: showPreview()に追加
if (this.isOffline() && previewData.preview_type === 'office_embed') {
  // Office Embedはオフライン非対応を明示
  this.showOfflineWarning('Office文書のプレビューはオンライン時のみ利用可能です。');
  return;
}
```

---

### 4.2 CacheManager (cache-manager.js) 統合

#### 4.2.1 現状のLRU実装

```javascript
// cache-manager.js: Line 10-16
class CacheManager {
  constructor() {
    this.maxCacheSize = 50 * 1024 * 1024; // 50MB
    this.evictionThreshold = 45 * 1024 * 1024; // 45MB
    this.dbName = 'mks-pwa';
    this.storeName = 'cache-metadata';
  }
}
```

#### 4.2.2 仕様書の追加メソッド

```javascript
// 仕様書: Line 1273-1304
async getThumbnailCacheSize() { /* サムネイル専用キャッシュサイズ取得 */ }
async clearPreviewCache() { /* プレビューキャッシュクリア */ }
```

**評価**: ✅ **PASS** - 既存の`getTotalCacheSize()`パターンと一貫性あり

**追加提案**:
```javascript
// cache-manager.js: 既存のcacheNames配列に追加
this.cacheNames = [
  'mks-static-v1.4.0',
  'mks-api-v1.4.0',
  'mks-images-v1.4.0',
  'mks-thumbnails-v1.4.0',  // 新規
  'mks-previews-v1.4.0'      // 新規
];
```

---

### 4.3 オフライン対応の実装ギャップ

#### 4.3.1 仕様書のオフライン検出

```javascript
// 仕様書: Line 1319-1342
isOffline() {
  return !navigator.onLine;
}

async showPreview(driveId, fileId, options = {}) {
  if (this.isOffline()) {
    const cached = await this.getFromCache(driveId, fileId);
    if (cached) {
      return this.renderCachedPreview(cached);
    }
  }
}
```

**懸念事項 #5: getFromCache()の実装不足**

仕様書のフルコード（Line 544-1050）には、`getFromCache()`と`renderCachedPreview()`の実装が**含まれていません**。

**必要な実装**:
```javascript
// file-preview.js: 追加が必要
async getFromCache(driveId, fileId) {
  const cacheKey = `preview_${driveId}_${fileId}`;
  const cache = await caches.open('mks-previews-v1.4.0');
  const response = await cache.match(cacheKey);
  if (response) {
    return await response.json();
  }
  return null;
}

async renderCachedPreview(cachedData) {
  // プレビュータイプ別にレンダリング
  switch (cachedData.preview_type) {
    case 'office_embed':
      // オフラインでは表示不可を明示
      this.showOfflineWarning('オンライン接続が必要です。');
      break;
    case 'image':
      // キャッシュ済み画像を表示
      await this.renderImagePreview(cachedData.preview_url);
      break;
  }
}
```

**推奨アクション**: code-implementer に実装タスクとして明示的に指示

---

## 5. セキュリティ観点分析

### 5.1 STRIDE脅威分析の妥当性

| 脅威 | 仕様書の対策 | 評価 | 追加推奨 |
|------|------------|------|---------|
| **Spoofing** | JWT認証、ドライブID検証 | ✅ 適切 | - |
| **Tampering** | CSP `frame-src`制限、sandbox属性 | ✅ 適切 | - |
| **Repudiation** | 監査ログ（`log_access`） | ✅ 適切 | - |
| **Information Disclosure** | 短命トークン（1時間キャッシュ） | ✅ 適切 | - |
| **Denial of Service** | Rate limiting（5req/s） | ⚠️ 実装詳細不足 | 後述 |
| **Elevation of Privilege** | RBAC `ms365_sync.file.preview` | ✅ 適切 | - |

**懸念事項 #6: Rate Limitingの実装不足**

仕様書では「5req/s」と記載（Line 1076）されていますが、**バックエンド実装の詳細が不明**です。

**確認が必要な箇所**:
```python
# backend/app_v2.py: Rate limiting実装を確認
# 既存のFlask-Limiterデコレーターを使用しているか？
@app.route('/api/v1/integrations/microsoft365/files/<file_id>/thumbnail')
@jwt_required()
@limiter.limit("5 per second")  # ← この実装があるか確認
def get_thumbnail(file_id):
    pass
```

**推奨アクション**: Phase D-4 Week 1のバックエンド実装を確認（`backend/app_v2.py` L2000-2500付近）

---

### 5.2 XSS対策の評価

| 対策手法 | 仕様書の設計 | 評価 |
|---------|------------|------|
| DOM API使用 | ✅ `createElement()`, `textContent` | **PASS** |
| innerHTML禁止 | ✅ 明示的に禁止（Line 1103-1111） | **PASS** |
| URL自動エスケープ | ✅ `img.src = url` で自動エスケープ | **PASS** |
| イベントハンドラ | ✅ `addEventListener()`使用 | **PASS** |

**評価**: ✅ **PASS** - XSS対策は既存のapp.js/ms365-sync.jsと一貫性あり

---

### 5.3 CSP (Content Security Policy) 設定

#### 5.3.1 仕様書のCSP修正

```python
# 仕様書: Line 1083-1097
response.headers['Content-Security-Policy'] = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "frame-src 'self' https://view.officeapps.live.com; "  # Office Online許可
    "img-src 'self' data: blob: https://graph.microsoft.com; "  # Graph API画像許可
    "connect-src 'self' https://graph.microsoft.com; "
    "worker-src 'self';"
)
```

#### 5.3.2 既存のCSP（要確認）

**調査が必要**:
```bash
# backend/app_v2.pyの既存CSP設定を確認
grep -A 10 "Content-Security-Policy" backend/app_v2.py
```

**評価**: ⚠️ **WARNING** - 既存CSPとの統合確認が必要

---

## 6. パフォーマンス観点分析

### 6.1 キャッシュ戦略の効率性

| 項目 | 仕様書の設計 | 評価 | 根拠 |
|------|------------|------|------|
| サムネイル並列取得 | Promise.all（最大5並列） | ⚠️ 実装不足 | 仕様書に実装なし |
| IntersectionObserver遅延読み込み | 記載あり（Line 421） | ⚠️ 実装不足 | 仕様書に実装なし |
| 初回プレビュー表示 | 3秒以内目標 | ✅ 適切 | Lighthouse計測可 |

**懸念事項 #7: 並列取得の実装不足**

仕様書のLine 419には「サムネイル並列取得（Promise.all、最大5並列）」と記載されていますが、**実装コードに含まれていません**。

**推奨実装**:
```javascript
// ms365-sync.js: renderSyncHistoryRowの修正
async function renderSyncHistoryTable(histories) {
  // サムネイルを5件ずつバッチ取得
  const batchSize = 5;
  for (let i = 0; i < histories.length; i += batchSize) {
    const batch = histories.slice(i, i + batchSize);
    await Promise.all(
      batch.map(history =>
        filePreviewManager.getThumbnailUrl(history.drive_id, history.file_id, 'small')
          .then(dataUrl => {
            const img = document.querySelector(`#thumbnail-${history.id}`);
            if (img) img.src = dataUrl;
          })
      )
    );
  }
}
```

---

### 6.2 プレビュー表示時間の測定

#### 6.2.1 仕様書のパフォーマンス要件

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| 初回プレビュー表示 | 3秒以内 | Lighthouse Performance |
| サムネイル読み込み | 1秒以内（10件） | Chrome DevTools Network |
| キャッシュヒット時 | 500ms以内 | Performance API |

#### 6.2.2 Prometheusメトリクスの実装

```python
# 仕様書: Line 1606-1631
file_preview_requests_total = Counter(
    'file_preview_requests_total',
    'Total file preview requests',
    ['preview_type', 'status']
)

file_preview_duration_seconds = Histogram(
    'file_preview_duration_seconds',
    'File preview display duration',
    ['preview_type']
)
```

**懸念事項 #8: メトリクス計測タイミング不明**

バックエンドAPIでメトリクスを計測する場合、**フロントエンドのレンダリング時間は含まれません**。

**推奨アプローチ**:
```javascript
// file-preview.js: showPreview()修正
async showPreview(driveId, fileId, options = {}) {
  const startTime = performance.now();

  try {
    // ... プレビュー表示処理

    const duration = performance.now() - startTime;
    console.log(`[Performance] Preview displayed in ${duration.toFixed(0)}ms`);

    // 3秒超過時に警告
    if (duration > 3000) {
      console.warn('[Performance] Preview display exceeded 3s threshold');
    }
  } catch (error) {
    // ...
  }
}
```

---

## 7. テスト観点分析

### 7.1 E2Eテストカバレッジ

#### 7.1.1 仕様書のテストケース（8件）

| # | テストケース | カバレッジ範囲 | 評価 |
|---|------------|--------------|------|
| 1 | サムネイル一覧表示 | UI表示 | ✅ |
| 2 | プレビューモーダル表示 | UI動作 | ✅ |
| 3 | Office文書iframe表示 | 統合 | ✅ |
| 4 | 画像imgタグ表示 | 統合 | ✅ |
| 5 | ダウンロード機能 | 統合 | ✅ |
| 6 | 閉じるボタン | UI動作 | ✅ |
| 7 | Escapeキー | アクセシビリティ | ✅ |
| 8 | エラー時の再試行ボタン | エラーハンドリング | ✅ |

**評価**: ✅ **PASS** - 正常系・異常系・アクセシビリティを網羅

**追加推奨テスト**:
1. **権限エラー（403）のテスト**
   ```javascript
   test('権限エラー時にエラーメッセージが表示される', async ({ page }) => {
     await page.route('**/api/.../preview', route => {
       route.fulfill({ status: 403, body: JSON.stringify({ error: { message: 'Access denied' }}) });
     });

     await page.locator('.file-thumbnail').first().click();
     await expect(page.locator('#preview-error-text')).toContainText('アクセス権限がありません');
   });
   ```

2. **オフライン時のキャッシュフォールバック**
   ```javascript
   test('オフライン時にキャッシュが使用される', async ({ page, context }) => {
     // オンライン時にプレビュー表示してキャッシュ
     await page.locator('.file-thumbnail').first().click();
     await page.waitForSelector('#preview-container iframe');
     await page.click('#preview-close-btn');

     // オフラインモード
     await context.setOffline(true);

     // 再度プレビュー表示
     await page.locator('.file-thumbnail').first().click();
     await expect(page.locator('#preview-container')).toBeVisible();
   });
   ```

---

### 7.2 ユニットテストカバレッジ

#### 7.2.1 仕様書のテストケース（6件）

```javascript
// 仕様書: Line 1419-1487
describe('FilePreviewManager', () => {
  test('初期化でモーダルが生成される', () => {});
  test('showPreview()でAPIが呼ばれる', async () => {});
  test('getThumbnailUrl()でキャッシュが使われる', async () => {});
  test('エラー時にエラーメッセージが表示される', async () => {});
  test('Escapeキーで閉じる', () => {});
});
```

**評価**: ✅ **PASS** - 主要メソッドをカバー

**追加推奨テスト**:
1. **renderOfficeEmbed() のタイムアウトテスト**
   ```javascript
   test('iframe読み込みが10秒でタイムアウトする', async () => {
     jest.useFakeTimers();
     const manager = new FilePreviewManager();

     const promise = manager.renderOfficeEmbed('https://example.com/timeout');
     jest.advanceTimersByTime(10000);

     await expect(promise).rejects.toThrow();
   });
   ```

---

## 8. 懸念事項と改善提案

### 8.1 ブロッキング問題（0件）

なし ✅

---

### 8.2 中程度の懸念事項（5件）

#### 懸念事項 #1: トークンリフレッシュの欠落

**重要度**: 🟡 Medium
**影響範囲**: 認証切れ時のユーザー体験
**推奨対応**: file-preview.js の `fetchPreviewUrl()` に app.js の `refreshAccessToken()` 統合
**実装タイミング**: code-implementer 実装時

---

#### 懸念事項 #2: ms365-sync.js修正の具体性不足

**重要度**: 🟡 Medium
**影響範囲**: サムネイル一覧表示の実装
**推奨対応**:
1. 既存の同期履歴レンダリング関数を調査
2. テーブル構造の確認
3. 統合ポイントを明確化

**実装タイミング**: code-implementer 実装前の調査

---

#### 懸念事項 #3: Service Workerバージョン管理

**重要度**: 🟡 Medium
**影響範囲**: PWAキャッシュの更新
**推奨対応**: SW_VERSION を `v1.4.0` にバージョンアップ
**実装タイミング**: code-implementer 実装時

---

#### 懸念事項 #4: オフライン対応の実装ギャップ

**重要度**: 🟡 Medium
**影響範囲**: オフライン時のユーザー体験
**推奨対応**:
1. `getFromCache()` の実装
2. `renderCachedPreview()` の実装
3. Office Embed非対応の明示

**実装タイミング**: code-implementer 実装時

---

#### 懸念事項 #5: パフォーマンス測定の実装不足

**重要度**: 🟡 Medium
**影響範囲**: パフォーマンス監視
**推奨対応**:
1. フロントエンドでの Performance API 計測
2. 3秒超過時の警告ログ
3. Prometheusメトリクスとの統合

**実装タイミング**: code-implementer 実装時

---

### 8.3 軽微な改善提案（3件）

#### 改善提案 #1: サムネイル並列取得の実装

**重要度**: 🟢 Low
**効果**: サムネイル読み込み時間短縮（1秒以内達成）
**推奨実装**: Promise.all バッチ処理（最大5並列）

---

#### 改善提案 #2: IntersectionObserver遅延読み込み

**重要度**: 🟢 Low
**効果**: 初期表示時のネットワーク負荷軽減
**推奨実装**: スクロール時のサムネイル遅延読み込み

---

#### 改善提案 #3: E2Eテストの追加

**重要度**: 🟢 Low
**効果**: 権限エラー・オフライン動作の品質保証
**推奨実装**: 上記「7.1.1 追加推奨テスト」参照

---

## 9. 総合判定

### 9.1 判定結果

**判定**: **PASS_WITH_WARNINGS** ⚠️

Phase E-4仕様書は、以下の理由により実装可能です：

✅ **強み**:
1. 既存のPWA基盤（sw.js, cache-manager.js）との統合設計が適切
2. セキュリティ対策（STRIDE, XSS, CSP）が網羅的
3. FilePreviewManagerクラスのフルコード提供で実装の曖昧さが排除
4. E2Eテストケースが具体的（8件）

⚠️ **懸念事項**:
1. トークンリフレッシュの欠落（中）
2. ms365-sync.js修正の具体性不足（中）
3. Service Workerバージョン管理（中）
4. オフライン対応の実装ギャップ（中）
5. パフォーマンス測定の実装不足（中）

これらの懸念事項は**実装前の調査と設計補完**により解決可能であり、設計の根本的な問題ではありません。

---

### 9.2 実装前のアクションアイテム

| # | アクション | 担当 | 期限 |
|---|-----------|------|------|
| 1 | app.js の `refreshAccessToken()` 統合方法を確認 | code-implementer | Week 2 Day 1 |
| 2 | ms365-sync.js の既存テーブル構造を調査 | code-implementer | Week 2 Day 1 |
| 3 | sw.js のバージョンを `v1.4.0` に更新 | code-implementer | Week 2 Day 1 |
| 4 | `getFromCache()` と `renderCachedPreview()` の実装 | code-implementer | Week 2 Day 2 |
| 5 | Performance API計測コードを追加 | code-implementer | Week 2 Day 2 |
| 6 | E2Eテストに権限エラー/オフラインケースを追加 | test-designer | Week 3 Day 1 |

---

### 9.3 実装可否判断

**結論**: ✅ **実装可** (条件付き)

**条件**:
1. 上記のアクションアイテム1〜5を実装時に対処
2. code-implementer が仕様書を基準としつつ、既存コードとの整合性を確保
3. 懸念事項を修正した実装が code-reviewer のレビューを通過

**期待される成果物**:
- `webui/file-preview.js` (550行、追加実装含む)
- `webui/sw.js` (+30行修正)
- `webui/pwa/cache-manager.js` (+50行修正)
- `webui/ms365-sync.js` (+100行修正)
- `backend/tests/e2e/file-preview.spec.js` (450行、追加テスト含む)

---

## 付録A: 既存コードとの統合チェックリスト

### A.1 app.js統合

- [ ] `checkAuth()` の再利用確認
- [ ] `getCurrentUser()` の再利用確認
- [ ] `fetchAPI()` ではなく直接 `fetch()` を使用（JWTヘッダーは手動設定）
- [ ] `refreshAccessToken()` の統合（または再実装）
- [ ] `showNotification()` の再利用確認
- [ ] `logger` グローバル変数の使用

### A.2 ms365-sync.js統合

- [ ] 既存の同期履歴レンダリング関数の確認
- [ ] テーブル構造（`<thead>`, `<tbody>`）の確認
- [ ] サムネイル列の追加位置の決定
- [ ] `formatCronSchedule()` などヘルパー関数の確認

### A.3 PWA統合

- [ ] SW_VERSION を `v1.4.0` に更新
- [ ] CACHE_NAMES に `thumbnails`, `previews` を追加
- [ ] STATIC_ASSETS に `file-preview.js` を追加
- [ ] Fetch Handler にサムネイル/プレビューのルーティング追加
- [ ] CacheManager の `cacheNames` 配列更新

---

## 付録B: コードレビューチェックポイント（code-reviewerへの指示）

### B.1 必須チェック項目

1. **認証統合**
   - [ ] `localStorage.getItem('access_token')` の使用
   - [ ] 401エラー時のトークンリフレッシュ処理
   - [ ] JWT有効期限切れ時のログアウト処理

2. **XSS対策**
   - [ ] `innerHTML` の使用禁止
   - [ ] `createElement()` と `textContent` の使用
   - [ ] イベントハンドラは `addEventListener()` で登録

3. **Service Worker統合**
   - [ ] SW_VERSION が `v1.4.0` に更新されているか
   - [ ] キャッシュ名が正しく追加されているか
   - [ ] Fetch Handlerのルーティング実装

4. **オフライン対応**
   - [ ] `getFromCache()` の実装
   - [ ] `renderCachedPreview()` の実装
   - [ ] Office Embed非対応の明示

5. **パフォーマンス**
   - [ ] Performance API での計測
   - [ ] 3秒超過時の警告ログ

---

## 承認

| 役割 | 氏名 | 承認日 | 署名 |
|------|------|--------|------|
| **レビュアー** | arch-reviewer (Claude AI) | 2026-02-06 | ✅ |
| **承認者** | team-lead | 未実施 | - |

---

**変更履歴**:

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-02-06 | 初版作成（PASS_WITH_WARNINGS判定） | arch-reviewer |

---

**End of Document**
