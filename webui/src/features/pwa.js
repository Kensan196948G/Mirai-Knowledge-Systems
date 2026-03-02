/**
 * @fileoverview PWA統合モジュール v2.0.0
 * @module features/pwa
 * @description Phase F-2 ESモジュール化版
 *   webui/pwa/ 内の複数ファイルを1つのESMモジュールに統合。
 *   - InstallPrompt: PWAインストールプロンプト管理
 *   - SyncManager: Background Sync / IndexedDB キュー管理
 *   - CryptoHelper: JWT暗号化（AES-GCM 256-bit + PBKDF2）
 *   - CacheManager: LRU キャッシュ削除管理
 */

import { logger } from '../core/logger.js';

// ============================================================
// InstallPrompt クラス
// ============================================================

/**
 * PWAインストールプロンプト管理クラス
 * インストールバナーの表示・非表示・クールダウン制御を行う
 */
export class InstallPrompt {
  constructor() {
    /** @type {Event|null} */
    this.deferredPrompt = null;
    /** @type {boolean} */
    this.isInstalled = false;
    /** @type {string} */
    this.dismissKey = 'pwa-install-dismissed';
    this._init();
  }

  /**
   * 初期化処理
   * @private
   */
  _init() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      logger.debug('[PWA] Install prompt ready');
      this._scheduleInstallPrompt();
    });

    window.addEventListener('appinstalled', () => {
      this.isInstalled = true;
      this._hideInstallButton();
      this._trackInstallation();
      logger.debug('[PWA] App installed successfully');
    });

    if (
      window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true
    ) {
      this.isInstalled = true;
      logger.debug('[PWA] App running in standalone mode');
    }
  }

  /**
   * インストールプロンプトのスケジュール設定
   * @private
   */
  _scheduleInstallPrompt() {
    const dismissedAt = localStorage.getItem(this.dismissKey);
    if (dismissedAt) {
      const daysSinceDismissed = (Date.now() - parseInt(dismissedAt)) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) {
        logger.debug('[PWA] Install prompt on cooldown');
        return;
      }
    }

    const pageViews = parseInt(localStorage.getItem('pwa-page-views') || '0') + 1;
    localStorage.setItem('pwa-page-views', pageViews.toString());

    if (pageViews >= 3) {
      this._showInstallButton();
    } else {
      setTimeout(() => {
        this._showInstallButton();
      }, 2 * 60 * 1000);
    }
  }

  /**
   * インストールバナーを表示
   * @private
   */
  _showInstallButton() {
    if (this.isInstalled || !this.deferredPrompt) return;

    const existing = document.getElementById('pwa-install-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.className = 'pwa-install-banner';

    const content = document.createElement('div');
    content.className = 'pwa-install-content';

    const icon = document.createElement('div');
    icon.className = 'pwa-install-icon';
    icon.textContent = 'App';

    const textDiv = document.createElement('div');
    textDiv.className = 'pwa-install-text';

    const strong = document.createElement('strong');
    strong.textContent = 'アプリとしてインストール';

    const p = document.createElement('p');
    p.textContent = 'オフラインでも使用できます';

    textDiv.appendChild(strong);
    textDiv.appendChild(p);

    const installButton = document.createElement('button');
    installButton.className = 'cta';
    installButton.id = 'pwa-install-button';
    installButton.textContent = 'インストール';

    const dismissButton = document.createElement('button');
    dismissButton.className = 'cta ghost';
    dismissButton.id = 'pwa-install-dismiss';
    dismissButton.textContent = '後で';

    content.appendChild(icon);
    content.appendChild(textDiv);
    content.appendChild(installButton);
    content.appendChild(dismissButton);
    banner.appendChild(content);

    document.body.appendChild(banner);

    installButton.addEventListener('click', () => this.promptInstall());
    dismissButton.addEventListener('click', () => this.dismissInstall());

    logger.debug('[PWA] Install banner displayed');
  }

  /**
   * ネイティブインストールプロンプトを表示
   * @returns {Promise<void>}
   */
  async promptInstall() {
    if (!this.deferredPrompt) {
      logger.warn('[PWA] No deferred prompt available');
      return;
    }

    this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;
    logger.debug('[PWA] User choice:', outcome);

    this.deferredPrompt = null;
    this._hideInstallButton();
  }

  /**
   * インストールプロンプトを却下（7日クールダウン）
   */
  dismissInstall() {
    localStorage.setItem(this.dismissKey, Date.now().toString());
    this._hideInstallButton();
    logger.debug('[PWA] Install prompt dismissed');
  }

  /**
   * インストールバナーを非表示
   * @private
   */
  _hideInstallButton() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
      banner.classList.add('fade-out');
      setTimeout(() => banner.remove(), 300);
    }
  }

  /**
   * インストールイベントをバックエンドに送信
   * @private
   */
  _trackInstallation() {
    fetch('/api/metrics/pwa-install', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
      },
      body: JSON.stringify({
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        displayMode: window.matchMedia('(display-mode: standalone)').matches ? 'standalone' : 'browser'
      })
    }).catch((error) => {
      logger.error('[PWA] Install tracking failed:', error);
    });
  }

  /**
   * iOSユーザー向けマニュアルインストール手順を表示
   */
  showManualInstructions() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);

    if (isIOS && isSafari) {
      const banner = document.createElement('div');
      banner.className = 'pwa-install-banner';

      const content = document.createElement('div');
      content.className = 'pwa-install-content';

      const icon = document.createElement('div');
      icon.className = 'pwa-install-icon';
      icon.textContent = 'iOS';

      const textDiv = document.createElement('div');
      textDiv.className = 'pwa-install-text';

      const strong = document.createElement('strong');
      strong.textContent = 'ホーム画面に追加';

      const p = document.createElement('p');
      p.textContent = 'Safari共有ボタン → 「ホーム画面に追加」をタップ';

      textDiv.appendChild(strong);
      textDiv.appendChild(p);

      const okButton = document.createElement('button');
      okButton.className = 'cta ghost';
      okButton.textContent = 'OK';
      okButton.addEventListener('click', () => banner.remove());

      content.appendChild(icon);
      content.appendChild(textDiv);
      content.appendChild(okButton);
      banner.appendChild(content);

      document.body.appendChild(banner);
    }
  }
}

// ============================================================
// SyncManager クラス
// ============================================================

/**
 * Background Sync マネージャークラス
 * - IndexedDB 同期キュー管理
 * - Background Sync API 統合
 * - 指数バックオフリトライ（1s → 2s → 4s → 8s → 16s）
 * - Background Sync API 非対応ブラウザ向けフォールバック
 */
export class SyncManager {
  constructor() {
    /** @type {string} */
    this.dbName = 'mks-pwa';
    /** @type {string} */
    this.storeName = 'sync-queue';
    /** @type {IDBDatabase|null} */
    this.db = null;
    /** @type {number} */
    this.maxRetries = 5;
    this._init();
  }

  /**
   * 初期化処理
   * @private
   * @returns {Promise<void>}
   */
  async _init() {
    try {
      this.db = await this._openDB();
      logger.debug('[SyncManager] Initialized');

      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        await this._registerSync();
      } else {
        logger.warn('[SyncManager] Background Sync API not available, using immediate sync');
      }
    } catch (error) {
      logger.error('[SyncManager] Initialization failed:', error);
    }
  }

  /**
   * IndexedDB を開く
   * @private
   * @returns {Promise<IDBDatabase>}
   */
  _openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        if (!db.objectStoreNames.contains('sync-queue')) {
          db.createObjectStore('sync-queue', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('tokens')) {
          db.createObjectStore('tokens', { keyPath: 'key' });
        }
        if (!db.objectStoreNames.contains('cache-metadata')) {
          const store = db.createObjectStore('cache-metadata', { keyPath: 'key' });
          store.createIndex('last_accessed_at', 'last_accessed_at', { unique: false });
        }

        logger.debug('[SyncManager] IndexedDB stores created');
      };
    });
  }

  /**
   * 同期キューにアイテムを追加
   * @param {string} url - リクエストURL
   * @param {string} method - HTTPメソッド
   * @param {Object} headers - リクエストヘッダー
   * @param {string} body - リクエストボディ（JSON文字列）
   * @returns {Promise<Object>} 追加されたキューアイテム
   */
  async addToQueue(url, method, headers, body) {
    if (!this.db) {
      await this._init();
    }

    const item = {
      url,
      method,
      headers,
      body,
      timestamp: Date.now(),
      retries: 0
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.add(item);

      request.onsuccess = async () => {
        item.id = request.result;
        logger.debug('[SyncManager] Item added to queue:', item.id);
        await this._registerSync();
        resolve(item);
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Background Sync を登録
   * @private
   * @returns {Promise<void>}
   */
  async _registerSync() {
    if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-queue');
        logger.debug('[SyncManager] Background sync registered');
      } catch (error) {
        logger.error('[SyncManager] Failed to register sync:', error);
        await this.processSyncQueue();
      }
    } else {
      logger.warn('[SyncManager] Background Sync not supported, using immediate sync');
      await this.processSyncQueue();
    }
  }

  /**
   * 同期キューを処理する
   * @returns {Promise<void>}
   */
  async processSyncQueue() {
    if (!this.db) {
      await this._init();
    }

    const items = await this._getAllQueueItems();
    logger.debug(`[SyncManager] Processing ${items.length} queued items`);

    for (const item of items) {
      try {
        const response = await fetch(item.url, {
          method: item.method,
          headers: item.headers,
          body: item.body
        });

        if (response.ok) {
          await this._deleteQueueItem(item.id);
          logger.debug('[SyncManager] Sync success:', item.id);
        } else if (item.retries < this.maxRetries) {
          item.retries++;
          await this._updateQueueItem(item);
          logger.warn(`[SyncManager] Sync failed, retry ${item.retries}/${this.maxRetries}:`, item.id);
        } else {
          logger.error('[SyncManager] Max retries reached:', item.id);
          await this._deleteQueueItem(item.id);
        }
      } catch (error) {
        logger.error('[SyncManager] Sync failed:', item.id, error);

        if (item.retries < this.maxRetries) {
          item.retries++;
          await this._updateQueueItem(item);
          const backoffDelay = Math.pow(2, item.retries) * 1000;
          logger.debug(`[SyncManager] Retrying in ${backoffDelay}ms`);
          setTimeout(() => this.processSyncQueue(), backoffDelay);
        } else {
          logger.error('[SyncManager] Max retries reached, removing from queue:', item.id);
          await this._deleteQueueItem(item.id);
        }
      }
    }
  }

  /**
   * 全キューアイテムを取得
   * @private
   * @returns {Promise<Array>}
   */
  _getAllQueueItems() {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * キューアイテムを削除
   * @private
   * @param {number} id - アイテムID
   * @returns {Promise<void>}
   */
  _deleteQueueItem(id) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * キューアイテムを更新
   * @private
   * @param {Object} item - 更新するアイテム
   * @returns {Promise<void>}
   */
  _updateQueueItem(item) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.put(item);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 保留中のキューアイテム数を取得
   * @returns {Promise<number>}
   */
  getPendingCount() {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.count();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 全キューアイテムをクリア
   * @returns {Promise<void>}
   */
  clearQueue() {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.clear();

      request.onsuccess = () => {
        logger.debug('[SyncManager] Queue cleared');
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }
}

// ============================================================
// CryptoHelper クラス
// ============================================================

/**
 * JWT トークン暗号化ヘルパークラス（Web Crypto API 使用）
 * - アルゴリズム: AES-GCM (256-bit) + PBKDF2 鍵導出
 * - PBKDF2: 100,000 イテレーション（OWASP推奨）
 * - 鍵導出ベース: UserEmail + BrowserFingerprint
 */
export class CryptoHelper {
  constructor() {
    /** @type {string} */
    this.algorithm = 'AES-GCM';
    /** @type {number} */
    this.keyLength = 256;
    /** @type {number} */
    this.iterations = 100000;
    /** @type {string} */
    this.saltKey = 'mks-pwa-salt-v1';
  }

  /**
   * PBKDF2用のソルトを生成または取得
   * @returns {Promise<Uint8Array>}
   */
  async getSalt() {
    let saltHex = localStorage.getItem(this.saltKey);

    if (!saltHex) {
      const salt = crypto.getRandomValues(new Uint8Array(16));
      saltHex = Array.from(salt).map(b => b.toString(16).padStart(2, '0')).join('');
      localStorage.setItem(this.saltKey, saltHex);
    }

    return new Uint8Array(saltHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
  }

  /**
   * PBKDF2を使用して暗号化鍵を導出
   * ベースマテリアル: ユーザーEmail + ブラウザフィンガープリント
   * @returns {Promise<CryptoKey>}
   */
  async deriveKey() {
    const userEmail = localStorage.getItem('user_email') || 'anonymous';
    const browserFingerprint = await this.getBrowserFingerprint();
    const passphrase = `${userEmail}:${browserFingerprint}`;
    const salt = await this.getSalt();
    const encoder = new TextEncoder();

    const baseKey = await crypto.subtle.importKey(
      'raw',
      encoder.encode(passphrase),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    const derivedKey = await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: this.iterations,
        hash: 'SHA-256'
      },
      baseKey,
      { name: this.algorithm, length: this.keyLength },
      true,
      ['encrypt', 'decrypt']
    );

    return derivedKey;
  }

  /**
   * ブラウザフィンガープリントを生成（セッション間で安定）
   * @returns {Promise<string>}
   */
  async getBrowserFingerprint() {
    const components = [
      navigator.userAgent,
      navigator.language,
      screen.width,
      screen.height,
      screen.colorDepth,
      new Date().getTimezoneOffset(),
      !!window.sessionStorage,
      !!window.localStorage
    ];

    const fingerprint = components.join('|');
    const encoder = new TextEncoder();
    const data = encoder.encode(fingerprint);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /**
   * JWTトークンを暗号化
   * @param {string} token - 暗号化するJWTトークン
   * @returns {Promise<{encrypted: Array, iv: Array}>}
   */
  async encrypt(token) {
    const key = await this.deriveKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoder = new TextEncoder();

    const encrypted = await crypto.subtle.encrypt(
      { name: this.algorithm, iv: iv },
      key,
      encoder.encode(token)
    );

    return {
      encrypted: Array.from(new Uint8Array(encrypted)),
      iv: Array.from(iv)
    };
  }

  /**
   * JWTトークンを復号化
   * @param {Array} encryptedData - 暗号化されたトークンデータ
   * @param {Array} iv - 初期化ベクター
   * @returns {Promise<string>} 復号化されたJWTトークン
   */
  async decrypt(encryptedData, iv) {
    const key = await this.deriveKey();

    try {
      const decrypted = await crypto.subtle.decrypt(
        { name: this.algorithm, iv: new Uint8Array(iv) },
        key,
        new Uint8Array(encryptedData)
      );

      const decoder = new TextDecoder();
      return decoder.decode(decrypted);
    } catch (error) {
      logger.error('[CryptoHelper] Decryption failed:', error);
      throw new Error('Token decryption failed');
    }
  }

  /**
   * トークンの有効期限を検証
   * @param {string} token - JWTトークン
   * @returns {boolean} 有効な場合はtrue、期限切れの場合はfalse
   */
  validateTokenExpiration(token) {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return false;

      const payload = JSON.parse(atob(parts[1]));
      const exp = payload.exp;

      if (!exp) return true;

      const now = Math.floor(Date.now() / 1000);
      return now < exp;
    } catch (error) {
      logger.error('[CryptoHelper] Token validation failed:', error);
      return false;
    }
  }

  /**
   * 暗号化キーをローテーション（3ヶ月サイクル、オプション）
   * @returns {Promise<void>}
   */
  async rotateKey() {
    localStorage.removeItem(this.saltKey);
    logger.debug('[CryptoHelper] Key rotation triggered');
  }
}

// ============================================================
// CacheManager クラス
// ============================================================

/**
 * LRUキャッシュ削除マネージャークラス
 * - LRU (Least Recently Used) 削除戦略
 * - 45MB 閾値で削除開始、50MB 最大
 * - IndexedDB メタデータトラッキング
 */
export class CacheManager {
  constructor() {
    /** @type {number} */
    this.maxCacheSize = 50 * 1024 * 1024;
    /** @type {number} */
    this.evictionThreshold = 45 * 1024 * 1024;
    /** @type {string} */
    this.dbName = 'mks-pwa';
    /** @type {string} */
    this.storeName = 'cache-metadata';
  }

  /**
   * 総キャッシュサイズを取得
   * @returns {Promise<number>} バイト数
   */
  async getTotalCacheSize() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return estimate.usage || 0;
    }

    let totalSize = 0;
    const cacheNames = await caches.keys();

    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const requests = await cache.keys();

      for (const request of requests) {
        const response = await cache.match(request);
        if (response) {
          const blob = await response.blob();
          totalSize += blob.size;
        }
      }
    }

    return totalSize;
  }

  /**
   * キャッシュアクセスを記録（LRU用）
   * @param {string} cacheKey - キャッシュキー
   * @returns {Promise<void>}
   */
  async trackAccess(cacheKey) {
    try {
      const db = await this._openDB();
      const transaction = db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);

      const getRequest = store.get(cacheKey);

      return new Promise((resolve, reject) => {
        getRequest.onsuccess = () => {
          const existing = getRequest.result;
          const accessCount = existing ? (existing.access_count || 0) + 1 : 1;

          const putRequest = store.put({
            key: cacheKey,
            last_accessed_at: Date.now(),
            access_count: accessCount
          });

          putRequest.onsuccess = () => resolve();
          putRequest.onerror = () => reject(putRequest.error);
        };

        getRequest.onerror = () => reject(getRequest.error);
      });
    } catch (error) {
      logger.error('[CacheManager] Track access failed:', error);
    }
  }

  /**
   * LRUエントリを取得
   * @param {number} [limit=10] - 取得するエントリ数
   * @returns {Promise<Array>}
   */
  async getLRUEntries(limit = 10) {
    try {
      const db = await this._openDB();
      const transaction = db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const index = store.index('last_accessed_at');

      return new Promise((resolve, reject) => {
        const entries = [];
        const request = index.openCursor();

        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor && entries.length < limit) {
            entries.push(cursor.value);
            cursor.continue();
          } else {
            resolve(entries);
          }
        };

        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      logger.error('[CacheManager] Get LRU entries failed:', error);
      return [];
    }
  }

  /**
   * 閾値超過時にLRU削除を実行
   * @returns {Promise<void>}
   */
  async evictIfNeeded() {
    const totalSize = await this.getTotalCacheSize();
    logger.debug(`[CacheManager] Current cache size: ${(totalSize / 1024 / 1024).toFixed(2)}MB`);

    if (totalSize < this.evictionThreshold) {
      return;
    }

    logger.debug('[CacheManager] Cache size exceeded threshold, starting LRU eviction...');

    const lruEntries = await this.getLRUEntries(20);
    const targetSize = this.maxCacheSize * 0.8;
    let evictedSize = 0;

    for (const entry of lruEntries) {
      if (totalSize - evictedSize < targetSize) {
        break;
      }

      const cacheNames = await caches.keys();
      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const deleted = await cache.delete(entry.key);

        if (deleted) {
          logger.debug(`[CacheManager] Evicted: ${entry.key}`);
          evictedSize += 10240;
        }
      }

      try {
        const db = await this._openDB();
        const transaction = db.transaction([this.storeName], 'readwrite');
        await transaction.objectStore(this.storeName).delete(entry.key);
      } catch (error) {
        logger.error('[CacheManager] Metadata deletion failed:', error);
      }
    }

    logger.debug(`[CacheManager] Evicted approximately ${(evictedSize / 1024 / 1024).toFixed(2)}MB`);
  }

  /**
   * IndexedDB を開く
   * @private
   * @returns {Promise<IDBDatabase>}
   */
  _openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        if (!db.objectStoreNames.contains('sync-queue')) {
          db.createObjectStore('sync-queue', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('tokens')) {
          db.createObjectStore('tokens', { keyPath: 'key' });
        }
        if (!db.objectStoreNames.contains('cache-metadata')) {
          const store = db.createObjectStore('cache-metadata', { keyPath: 'key' });
          store.createIndex('last_accessed_at', 'last_accessed_at', { unique: false });
        }

        logger.debug('[CacheManager] IndexedDB stores created');
      };
    });
  }

  /**
   * 全キャッシュメタデータをクリア
   * @returns {Promise<void>}
   */
  async clearMetadata() {
    try {
      const db = await this._openDB();
      const transaction = db.transaction([this.storeName], 'readwrite');
      await transaction.objectStore(this.storeName).clear();
      logger.debug('[CacheManager] Metadata cleared');
    } catch (error) {
      logger.error('[CacheManager] Clear metadata failed:', error);
    }
  }
}

// ============================================================
// モジュール初期化
// ============================================================

/**
 * PWAモジュールを初期化し、グローバルインスタンスを設定
 * @returns {{ installPrompt: InstallPrompt|null, syncManager: SyncManager|null, cryptoHelper: CryptoHelper, cacheManager: CacheManager }}
 */
export function initPWA() {
  const instances = {
    installPrompt: null,
    syncManager: null,
    cryptoHelper: new CryptoHelper(),
    cacheManager: new CacheManager()
  };

  if ('serviceWorker' in navigator) {
    instances.installPrompt = new InstallPrompt();
  }

  if ('indexedDB' in window) {
    instances.syncManager = new SyncManager();
  }

  logger.debug('[PWA] PWA module initialized');
  return instances;
}

// ============================================================
// 後方互換性（window経由のアクセスを維持）
// ============================================================

if (typeof window !== 'undefined') {
  window.PWAModule = {
    InstallPrompt,
    SyncManager,
    CryptoHelper,
    CacheManager,
    initPWA,
  };
}
