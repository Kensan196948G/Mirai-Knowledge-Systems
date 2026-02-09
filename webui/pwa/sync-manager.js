/**
 * Background Sync Manager
 *
 * Features:
 * - IndexedDB sync queue management
 * - Background Sync API integration
 * - Retry logic with exponential backoff (1s, 2s, 4s, 8s, 16s)
 * - Fallback for browsers without Background Sync API
 */

// 環境判定（window.MKS_ENV優先、ポート番号フォールバック）
const IS_PRODUCTION = (() => {
  // 優先順位1: window.MKS_ENV（バックエンドから設定される環境変数）
  if (typeof window !== 'undefined' && window.MKS_ENV) {
    return window.MKS_ENV === 'production';
  }
  // 優先順位2: self.MKS_ENV（Service Worker用）
  if (typeof self !== 'undefined' && self.MKS_ENV) {
    return self.MKS_ENV === 'production';
  }
  // フォールバック: ポート番号判定
  const port = (typeof self !== 'undefined' ? self.location?.port : window.location?.port) || '';
  return port === '9100' || port === '9443';
})();

// ロガー
const logger = {
  log: (...args) => { if (!IS_PRODUCTION) console.log(...args); },
  warn: (...args) => { if (!IS_PRODUCTION) console.warn(...args); },
  error: (...args) => { if (!IS_PRODUCTION) console.error(...args); }
};

class SyncManager {
  constructor() {
    this.dbName = 'mks-pwa';
    this.storeName = 'sync-queue';
    this.db = null;
    this.maxRetries = 5;
    this.init();
  }

  async init() {
    try {
      this.db = await this.openDB();
      logger.log('[SyncManager] Initialized');

      // Register sync event if supported
      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        await this.registerSync();
      } else {
        logger.warn('[SyncManager] Background Sync API not available, using immediate sync');
      }
    } catch (error) {
      logger.error('[SyncManager] Initialization failed:', error);
    }
  }

  /**
   * Open IndexedDB
   */
  openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create all required stores
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

        logger.log('[SyncManager] IndexedDB stores created');
      };
    });
  }

  /**
   * Add item to sync queue
   * @param {string} url - Request URL
   * @param {string} method - HTTP method (POST, PUT, DELETE)
   * @param {Object} headers - Request headers
   * @param {string} body - Request body (JSON string)
   */
  async addToQueue(url, method, headers, body) {
    if (!this.db) {
      await this.init();
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
        logger.log('[SyncManager] Item added to queue:', item.id);
        await this.registerSync();
        resolve(item);
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Register Background Sync
   */
  async registerSync() {
    if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-queue');
        logger.log('[SyncManager] Background sync registered');
      } catch (error) {
        logger.error('[SyncManager] Failed to register sync:', error);
        // Fallback to immediate sync
        await this.processSyncQueue();
      }
    } else {
      // Fallback for browsers without Background Sync API (iOS Safari)
      logger.warn('[SyncManager] Background Sync not supported, using immediate sync');
      await this.processSyncQueue();
    }
  }

  /**
   * Process sync queue (called by Service Worker or fallback)
   */
  async processSyncQueue() {
    if (!this.db) {
      await this.init();
    }

    const items = await this.getAllQueueItems();

    logger.log(`[SyncManager] Processing ${items.length} queued items`);

    for (const item of items) {
      try {
        const response = await fetch(item.url, {
          method: item.method,
          headers: item.headers,
          body: item.body
        });

        if (response.ok) {
          await this.deleteQueueItem(item.id);
          logger.log('[SyncManager] Sync success:', item.id);
        } else if (item.retries < this.maxRetries) {
          item.retries++;
          await this.updateQueueItem(item);
          logger.warn(`[SyncManager] Sync failed, retry ${item.retries}/${this.maxRetries}:`, item.id);
        } else {
          logger.error('[SyncManager] Max retries reached:', item.id);
          await this.deleteQueueItem(item.id);
        }
      } catch (error) {
        logger.error('[SyncManager] Sync failed:', item.id, error);

        if (item.retries < this.maxRetries) {
          item.retries++;
          await this.updateQueueItem(item);

          // Exponential backoff
          const backoffDelay = Math.pow(2, item.retries) * 1000; // 1s, 2s, 4s, 8s, 16s
          logger.log(`[SyncManager] Retrying in ${backoffDelay}ms`);
          setTimeout(() => this.processSyncQueue(), backoffDelay);
        } else {
          logger.error('[SyncManager] Max retries reached, removing from queue:', item.id);
          await this.deleteQueueItem(item.id);
        }
      }
    }
  }

  /**
   * Get all queue items
   */
  async getAllQueueItems() {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Delete queue item
   */
  async deleteQueueItem(id) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Update queue item
   */
  async updateQueueItem(item) {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.put(item);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get pending count
   */
  async getPendingCount() {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.count();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Clear all queue items
   */
  async clearQueue() {
    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.clear();

      request.onsuccess = () => {
        logger.log('[SyncManager] Queue cleared');
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }
}

// Export
window.SyncManager = SyncManager;

// Initialize global instance
if ('indexedDB' in window) {
  window.syncManager = new SyncManager();
}
