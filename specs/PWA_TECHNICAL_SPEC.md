# PWA Technical Specification - Mirai Knowledge Systems

**プロジェクト**: Mirai Knowledge Systems v1.3.0
**Phase**: D-5 - Progressive Web App Implementation
**作成日**: 2026-01-31
**ステータス**: 技術仕様完成

---

## 目次

1. [アーキテクチャ設計](#1-アーキテクチャ設計)
2. [Service Worker実装](#2-service-worker実装)
3. [キャッシュ戦略詳細](#3-キャッシュ戦略詳細)
4. [インストール体験](#4-インストール体験)
5. [バックグラウンド同期](#5-バックグラウンド同期)
6. [レスポンシブデザイン強化](#6-レスポンシブデザイン強化)
7. [テスト戦略](#7-テスト戦略)
8. [デプロイ計画](#8-デプロイ計画)
9. [監視とメトリクス](#9-監視とメトリクス)
10. [セキュリティ考慮事項](#10-セキュリティ考慮事項)

---

## 1. アーキテクチャ設計

### 1.1 システムアーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Web App (UI Layer)                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │  │ index.html│  │ app.js   │  │styles.css│            │ │
│  │  └──────────┘  └──────────┘  └──────────┘            │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────┼──────────────────────────────┐  │
│  │          Service Worker (sw.js)                       │  │
│  │                        │                               │  │
│  │  ┌────────────────────────────────────────┐           │  │
│  │  │        Cache Manager                    │           │  │
│  │  │  - Static Cache (v1.3.0-static)        │           │  │
│  │  │  - API Cache (v1.3.0-api)             │           │  │
│  │  │  - Images Cache (v1.3.0-images)       │           │  │
│  │  └────────────────────────────────────────┘           │  │
│  │                        │                               │  │
│  │  ┌────────────────────────────────────────┐           │  │
│  │  │        Sync Manager                     │           │  │
│  │  │  - Background Sync Queue                │           │  │
│  │  │  - Retry Logic                          │           │  │
│  │  └────────────────────────────────────────┘           │  │
│  └────────────────────────┼──────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┼──────────────────────────────┐  │
│  │          IndexedDB                                     │  │
│  │  - Encrypted JWT Tokens                               │  │
│  │  - Sync Queue (pending operations)                    │  │
│  │  - User Preferences                                    │  │
│  └────────────────────────┼──────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┼──────────────────────────────┐  │
│  │          Cache Storage                                 │  │
│  │  - v1.3.0-static (HTML/CSS/JS)                        │  │
│  │  - v1.3.0-api (API responses)                         │  │
│  │  - v1.3.0-images (Images)                             │  │
│  └────────────────────────┼──────────────────────────────┘  │
└────────────────────────────┼───────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   Network       │
                    │   (HTTPS)       │
                    └────────┬────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │   Flask Backend (192.168.0.187:9443)   │
        │   - REST API (46 endpoints)             │
        │   - PostgreSQL Database                 │
        │   - JWT Authentication                  │
        └─────────────────────────────────────────┘
```

### 1.2 ファイル構造

```
webui/
├── sw.js                        # Service Worker (NEW)
├── manifest.json                # Web App Manifest (NEW)
├── offline.html                 # Offline Fallback Page (NEW)
├── pwa/                         # PWA Modules (NEW)
│   ├── install-prompt.js        # Installation UI logic
│   ├── cache-manager.js         # Cache strategy implementation
│   ├── sync-manager.js          # Background sync logic
│   └── crypto-helper.js         # Token encryption utilities
├── icons/                       # PWA Icons (NEW)
│   ├── icon-72x72.png
│   ├── icon-96x96.png
│   ├── icon-128x128.png
│   ├── icon-144x144.png
│   ├── icon-152x152.png
│   ├── icon-192x192.png
│   ├── icon-384x384.png
│   ├── icon-512x512.png
│   └── maskable-icon-512x512.png
├── app.js                       # Existing (MODIFY for SW registration)
├── index.html                   # Existing (MODIFY manifest link)
├── login.html                   # Existing (MODIFY manifest link)
├── styles.css                   # Existing (ENHANCE responsive)
└── (other existing files)
```

---

## 2. Service Worker実装

### 2.1 Service Workerライフサイクル

**webui/sw.js** (約350行):

**主要機能**:
- インストール: 静的アセットのプリキャッシュ
- アクティベーション: 古いキャッシュの削除
- フェッチ: キャッシュ戦略の適用
- 同期: Background Sync処理

**キャッシュ名定義**:
```javascript
const SW_VERSION = 'v1.3.0';
const CACHE_PREFIX = 'mks-';

const CACHE_NAMES = {
  static: `${CACHE_PREFIX}static-${SW_VERSION}`,
  api: `${CACHE_PREFIX}api-${SW_VERSION}`,
  images: `${CACHE_PREFIX}images-${SW_VERSION}`,
};
```

**キャッシュ有効期限**:
```javascript
const CACHE_EXPIRATION = {
  static: 7 * 24 * 60 * 60 * 1000,      // 7日間
  apiSearch: 60 * 60 * 1000,             // 1時間
  apiDetail: 24 * 60 * 60 * 1000,        // 24時間
  images: 30 * 24 * 60 * 60 * 1000,      // 30日間
};
```

**静的アセット一覧**:
```javascript
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/login.html',
  '/admin.html',
  '/app.js',
  '/styles.css',
  '/dom-helpers.js',
  '/notifications.js',
  '/actions.js',
  '/mfa.js',
  '/ms365-sync.js',
  '/offline.html',
  '/pwa/install-prompt.js',
  '/pwa/cache-manager.js',
  '/pwa/sync-manager.js',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];
```

### 2.2 イベントハンドラ

**Installイベント**:
```javascript
self.addEventListener('install', (event) => {
  console.log('[SW] Install event:', SW_VERSION);

  event.waitUntil(
    caches.open(CACHE_NAMES.static)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting()) // 即座にアクティブ化
  );
});
```

**Activateイベント**:
```javascript
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate event:', SW_VERSION);

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        // 古いキャッシュを削除
        return Promise.all(
          cacheNames
            .filter((name) => name.startsWith(CACHE_PREFIX) &&
                             !Object.values(CACHE_NAMES).includes(name))
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});
```

**Fetchイベント**:
```javascript
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') return;

  // 戦略1: Cache First (静的アセット)
  if (STATIC_ASSETS.includes(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // 戦略2: Network First (API)
  if (API_CACHE_PATTERNS.some(p => p.test(url.pathname))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // 戦略3: Stale-While-Revalidate (画像)
  if (request.destination === 'image') {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // デフォルト: Network only
  event.respondWith(fetch(request));
});
```

### 2.3 Web App Manifest

**webui/manifest.json** (約70行):

```json
{
  "name": "Mirai Knowledge Systems - 建設土木ナレッジシステム",
  "short_name": "MKS",
  "description": "建設現場向け統合ナレッジ管理システム。SOP、規制情報、事故報告を一元管理。",
  "lang": "ja",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "any",
  "theme_color": "#2f4b52",
  "background_color": "#f1ece4",
  "categories": ["business", "productivity"],
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/maskable-icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "検索",
      "short_name": "Search",
      "description": "ナレッジを検索",
      "url": "/?action=search",
      "icons": [{ "src": "/icons/icon-search-96.png", "sizes": "96x96" }]
    }
  ]
}
```

---

## 3. キャッシュ戦略詳細

### 3.1 Cache First（静的アセット）

**対象ファイル**:
- HTML: index.html, login.html, admin.html（全16ページ）
- CSS: styles.css（約70KB）
- JavaScript: app.js（113KB）, detail-pages.js（105KB）, その他
- フォント: Google Fonts（Zen Kaku Gothic New, Shippori Mincho B1）

**実装**:
```javascript
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAMES.static);
  const cached = await cache.match(request);

  if (cached) {
    return cached; // キャッシュを即座に返す
  }

  try {
    const response = await fetch(request);
    cache.put(request, response.clone());
    return response;
  } catch (error) {
    // ナビゲーションリクエストの場合、オフラインページを返す
    if (request.mode === 'navigate') {
      return cache.match('/offline.html');
    }
    throw error;
  }
}
```

### 3.2 Network First（APIレスポンス）

**対象エンドポイント**:
- `/api/knowledge` - ナレッジ検索（有効期限: 1時間）
- `/api/sop/{id}` - SOP詳細（有効期限: 24時間）
- `/api/regulations` - 規制情報（有効期限: 24時間）
- `/api/notifications` - 通知（有効期限: 5分）

**実装**:
```javascript
async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAMES.api);

  try {
    const response = await fetch(request);

    if (response.ok) {
      // 有効期限メタデータを追加
      const clonedResponse = response.clone();
      const body = await clonedResponse.text();
      const headers = new Headers(clonedResponse.headers);
      headers.set('sw-cache-time', Date.now().toString());

      const cachedResponse = new Response(body, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: headers
      });

      cache.put(request, cachedResponse);
    }

    return response;
  } catch (error) {
    // ネットワーク失敗時、キャッシュを試す
    const cached = await cache.match(request);

    if (cached) {
      // キャッシュの有効期限をチェック
      const cacheTime = cached.headers.get('sw-cache-time');
      if (cacheTime) {
        const age = Date.now() - parseInt(cacheTime);
        const maxAge = request.url.includes('/search')
          ? CACHE_EXPIRATION.apiSearch
          : CACHE_EXPIRATION.apiDetail;

        if (age < maxAge) {
          return cached;
        }
      }
    }

    throw error;
  }
}
```

### 3.3 Stale-While-Revalidate（画像）

**対象**: すべての画像リクエスト（Content-Type: image/*）

**実装**:
```javascript
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAMES.images);
  const cached = await cache.match(request);

  // バックグラウンドでフェッチ
  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {});

  // キャッシュがあれば即座に返す
  return cached || fetchPromise;
}
```

---

## 4. インストール体験

### 4.1 インストールプロンプトUI

**webui/pwa/install-prompt.js** (約120行):

**主要機能**:
- `beforeinstallprompt`イベントのリスニング
- インストールバナーの表示制御
- ユーザー操作の追跡
- 7日間のクールダウン期間

**クラス構造**:
```javascript
class InstallPromptManager {
  constructor() {
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.init();
  }

  init() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
    });

    window.addEventListener('appinstalled', () => {
      this.isInstalled = true;
      this.hideInstallButton();
      this.trackInstallation();
    });
  }

  showInstallButton() {
    // クールダウン期間チェック
    const dismissedAt = localStorage.getItem('pwa-install-dismissed');
    if (dismissedAt) {
      const daysSinceDismissed = (Date.now() - parseInt(dismissedAt)) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) return;
    }

    // バナーUIの作成
    // ...
  }

  async promptInstall() {
    if (!this.deferredPrompt) return;

    this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;

    console.log('[PWA] Install outcome:', outcome);
    this.deferredPrompt = null;
    this.hideInstallButton();
  }
}
```

---

## 5. バックグラウンド同期

### 5.1 Sync Manager

**webui/pwa/sync-manager.js** (約200行):

**主要機能**:
- IndexedDBによる同期キュー管理
- Background Sync API統合
- リトライロジック（指数バックオフ）
- フォールバック処理（Background Sync非対応ブラウザ）

**クラス構造**:
```javascript
class SyncManager {
  constructor() {
    this.dbName = 'mks-pwa';
    this.storeName = 'sync-queue';
    this.db = null;
    this.init();
  }

  async addToQueue(url, method, headers, body) {
    const item = {
      url,
      method,
      headers,
      body,
      timestamp: Date.now(),
      retries: 0
    };

    const transaction = this.db.transaction([this.storeName], 'readwrite');
    await transaction.objectStore(this.storeName).add(item);
    await this.registerSync();

    return item;
  }

  async registerSync() {
    if ('serviceWorker' in navigator && 'sync' in self.registration) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-queue');
      } catch (error) {
        // フォールバック: 即座に同期
        await this.processSyncQueue();
      }
    } else {
      // Background Sync非対応: 即座に同期
      await this.processSyncQueue();
    }
  }

  async processSyncQueue() {
    const items = await this.getAllQueueItems();

    for (const item of items) {
      try {
        const response = await fetch(item.url, {
          method: item.method,
          headers: item.headers,
          body: item.body
        });

        if (response.ok) {
          await this.deleteQueueItem(item.id);
        } else if (item.retries < 5) {
          item.retries++;
          await this.updateQueueItem(item);
        }
      } catch (error) {
        if (item.retries < 5) {
          item.retries++;
          await this.updateQueueItem(item);
        }
      }
    }
  }
}
```

---

## 6. レスポンシブデザイン強化

### 6.1 CSSメディアクエリ

**webui/styles.css 追加** (約150行):

**PWA固有スタイル**:
```css
/* PWAインストールバナー */
.pwa-install-banner {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 16px 20px;
  z-index: 9999;
  max-width: 400px;
  width: 90%;
  animation: slideUp 0.3s ease-out;
}

/* オフライン表示 */
.offline-indicator {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: #f59e0b;
  color: white;
  padding: 8px;
  text-align: center;
  font-weight: 600;
  z-index: 9998;
  display: none;
}

.offline-indicator.visible {
  display: block;
}

/* モバイル最適化 */
@media (max-width: 768px) {
  .page {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .sidebar {
    position: fixed;
    left: -100%;
    top: 0;
    bottom: 0;
    width: 280px;
    transition: left 0.3s ease;
    z-index: 1000;
  }

  .sidebar.active {
    left: 0;
  }
}

/* タッチターゲット最適化 */
@media (hover: none) and (pointer: coarse) {
  button, a, .chip-button {
    min-height: 44px;
    min-width: 44px;
  }
}
```

---

## 7. テスト戦略

### 7.1 Lighthouse監査要件

**目標スコア**:
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+
- PWA: 90+

**主要チェック項目**:
- [x] Service Worker登録
- [x] オフライン時に200レスポンス
- [x] manifest.json存在
- [x] ホーム画面用アイコン
- [x] テーマカラー付きアドレスバー
- [x] Viewportメタタグ設定
- [x] HTTPS使用

### 7.2 E2Eテストケース

**backend/tests/e2e/pwa-functionality.spec.js**:

```javascript
const { test, expect } = require('@playwright/test');

test.describe('PWA Functionality', () => {
  test('Service Worker registers', async ({ page }) => {
    await page.goto('/');

    const swRegistered = await page.evaluate(() => {
      return navigator.serviceWorker.controller !== null;
    });

    expect(swRegistered).toBeTruthy();
  });

  test('Offline page loads when network disabled', async ({ page, context }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    await context.setOffline(true);
    await page.goto('/nonexistent-page');

    const content = await page.textContent('body');
    expect(content).toContain('オフライン');
  });

  test('Manifest is accessible', async ({ page }) => {
    const response = await page.goto('/manifest.json');
    expect(response.status()).toBe(200);

    const manifest = await response.json();
    expect(manifest.name).toContain('Mirai Knowledge');
  });
});
```

---

## 8. デプロイ計画

### 8.1 3週間ロードマップ

**Week 1: PWA基盤（2026-01-31 - 2026-02-06）**

Day 1-2:
- [ ] Service Worker基本実装（sw.js）
- [ ] Web App Manifest作成（manifest.json）
- [ ] アイコン生成（72x72〜512x512）
- [ ] オフラインフォールバックページ（offline.html）

Day 3-4:
- [ ] app.jsでService Worker登録
- [ ] インストールプロンプトUI（pwa/install-prompt.js）
- [ ] localhost:5200でテスト

Day 5-7:
- [ ] 192.168.0.187:9443でテスト
- [ ] インストールプロンプト改善
- [ ] Week 1完了レビュー

**Week 2: キャッシュ戦略（2026-02-07 - 2026-02-13）**

Day 8-10:
- [ ] Cache First実装（静的アセット）
- [ ] Network First実装（APIレスポンス）
- [ ] Stale-While-Revalidate（画像）
- [ ] キャッシュ有効期限ロジック

Day 11-12:
- [ ] Background Sync実装（pwa/sync-manager.js）
- [ ] IndexedDB同期キュー設定
- [ ] オフライン表示UI

Day 13-14:
- [ ] E2Eテスト（オフラインシナリオ）
- [ ] パフォーマンス最適化
- [ ] Week 2完了レビュー

**Week 3: UI最適化（2026-02-14 - 2026-02-20）**

Day 15-17:
- [ ] レスポンシブデザイン改善
- [ ] タッチターゲット最適化（44x44px最小）
- [ ] ハンバーガーメニュー（モバイル）
- [ ] Lighthouse監査（目標: 90+）

Day 18-19:
- [ ] クロスブラウザテスト（Chrome, Firefox, Safari）
- [ ] モバイルデバイステスト（Android, iOS）
- [ ] パフォーマンスチューニング

Day 20-21:
- [ ] ドキュメント更新
- [ ] ユーザートレーニング資料
- [ ] 本番デプロイ
- [ ] Phase D-5完了レポート

### 8.2 Nginx設定更新

**config/nginx.conf 追加**:

```nginx
# Service Worker MIME type
location ~ sw\.js$ {
  add_header Content-Type application/javascript;
  add_header Cache-Control "no-cache";
  add_header Service-Worker-Allowed "/";
}

# Manifest MIME type
location ~ manifest\.json$ {
  add_header Content-Type application/manifest+json;
  add_header Cache-Control "public, max-age=604800";
}

# PWA icons caching
location ~ ^/icons/ {
  add_header Cache-Control "public, max-age=2592000"; # 30日間
}
```

---

## 9. 監視とメトリクス

### 9.1 Prometheusメトリクス

**backend/app_v2.py 追加**:

```python
from prometheus_client import Counter, Histogram

pwa_install_counter = Counter(
    'pwa_install_total',
    'Total number of PWA installations'
)

pwa_offline_requests = Counter(
    'pwa_offline_requests_total',
    'Total number of requests served offline',
    ['resource_type']
)

@app.route('/api/metrics/pwa-install', methods=['POST'])
def track_pwa_install():
    pwa_install_counter.inc()
    return jsonify({'status': 'recorded'}), 200
```

### 9.2 Grafanaダッシュボード

**新規パネル: PWA Adoption**:
- PWAインストール数（Counter）
- キャッシュヒット率（Gauge）
- オフラインリクエスト率（Graph）
- Service Workerバージョン分布（Pie）

---

## 10. セキュリティ考慮事項

### 10.1 IndexedDBトークン暗号化

**webui/pwa/crypto-helper.js** (約100行):

**Web Crypto API使用**:
```javascript
class CryptoHelper {
  constructor() {
    this.algorithm = 'AES-GCM';
    this.keyLength = 256;
  }

  async encrypt(data) {
    const key = await this.getKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));

    const encrypted = await crypto.subtle.encrypt(
      { name: this.algorithm, iv },
      key,
      new TextEncoder().encode(data)
    );

    return {
      encrypted: Array.from(new Uint8Array(encrypted)),
      iv: Array.from(iv)
    };
  }

  async decrypt(encryptedData, iv) {
    const key = await this.getKey();

    const decrypted = await crypto.subtle.decrypt(
      { name: this.algorithm, iv: new Uint8Array(iv) },
      key,
      new Uint8Array(encryptedData)
    );

    return new TextDecoder().decode(decrypted);
  }
}
```

### 10.2 Content Security Policy更新

**backend/app_v2.py**:

```python
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://192.168.0.187:9443; "
        "worker-src 'self'; "
        "manifest-src 'self';"
    )
    return response
```

---

## 11. 付録

### 11.1 ブラウザサポートマトリクス

| 機能 | Chrome 90+ | Edge 90+ | Firefox 88+ | Safari 14+ |
|------|-----------|----------|-------------|-----------|
| Service Worker | ✅ | ✅ | ✅ | ✅ |
| Cache API | ✅ | ✅ | ✅ | ✅ |
| IndexedDB | ✅ | ✅ | ✅ | ✅ |
| Background Sync | ✅ | ✅ | ✅ | ❌ |
| Push Notifications | ✅ | ✅ | ✅ | ⚠️ (iOS 16.4+) |
| Install Prompt | ✅ | ✅ | ❌ | ❌ |

### 11.2 推定ファイルサイズ

| ファイル | 元サイズ | 最適化 | Gzip |
|---------|---------|--------|------|
| sw.js | - | 12KB | 4KB |
| manifest.json | - | 3KB | 1KB |
| offline.html | - | 5KB | 2KB |
| install-prompt.js | - | 8KB | 3KB |
| cache-manager.js | - | 10KB | 4KB |
| sync-manager.js | - | 12KB | 4KB |
| crypto-helper.js | - | 6KB | 2KB |
| アイコン（計9個） | - | 180KB | - |
| **新規アセット合計** | - | **236KB** | **20KB** |

### 11.3 参考ドキュメント

- [Service Worker API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest (W3C)](https://www.w3.org/TR/appmanifest/)
- [PWA Best Practices (web.dev)](https://web.dev/progressive-web-apps/)
- [Background Sync API (web.dev)](https://web.dev/periodic-background-sync/)
- [Cache Storage API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/CacheStorage)

---

## 12. 実装優先度

### 重要ファイル（実装優先順）

1. **webui/sw.js** - Service Workerコア（350行、NEW）
   - 理由: すべてのPWA機能の中心。キャッシュ戦略、オフラインフォールバック、ライフサイクル管理を実装

2. **webui/manifest.json** - Web App Manifest（70行、NEW）
   - 理由: PWAメタデータ、アイコン、インストール動作を定義。「ホーム画面に追加」とスタンドアロンモードに必須

3. **webui/pwa/install-prompt.js** - インストールUI（120行、NEW）
   - 理由: インストールUX管理。beforeinstallpromptイベントとユーザーエンゲージメントを処理

4. **webui/app.js** - メインアプリケーションロジック（既存2,500+行を修正）
   - 理由: Service Worker登録、オフライン検出、同期統合が必要。既存のJWTトークン管理ロジックを活用

5. **webui/pwa/sync-manager.js** - Background Sync（200行、NEW）
   - 理由: オフライン優先のデータ永続化を実装。建設現場の信頼性のためのIndexedDBキューとリトライロジック

---

**実装スコープ合計**:
- **新規ファイル**: 7個（sw.js, manifest.json, offline.html, 4 PWAモジュール）
- **修正ファイル**: 3個（app.js, index.html, styles.css）
- **新規アセット**: 9個のアイコン（72x72〜512x512）
- **推定LOC**: 約1,200行（新規）+ 200行（修正）
- **タイムライン**: 3週間（21日間）
- **依存関係**: 既存のJWT認証、Flask backend API（変更不要）

この設計は、モダンブラウザ向けのプログレッシブエンハンスメントを追加しつつ、完全な後方互換性を維持します。不安定なネットワーク環境での建設現場ナレッジアクセスという中核的なビジネスニーズに対応します。

---

## 承認

| 役割 | 氏名 | 承認日 | 署名 |
|------|------|--------|------|
| spec-planner | Claude Sonnet 4.5 | 2026-01-31 | ✅ |
| arch-reviewer | （承認待ち） | - | ⏳ |
| code-implementer | （承認待ち） | - | ⏳ |

---

**次のステップ**: arch-reviewerによる設計レビュー → 承認後、code-implementerによる実装開始
