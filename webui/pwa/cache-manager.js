/**
 * Cache Manager with LRU Eviction
 *
 * Features:
 * - LRU (Least Recently Used) eviction strategy
 * - 45MB threshold for eviction start
 * - 50MB maximum cache size
 * - IndexedDB metadata tracking
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

class CacheManager {
  constructor() {
    this.maxCacheSize = 50 * 1024 * 1024; // 50MB
    this.evictionThreshold = 45 * 1024 * 1024; // 45MB
    this.dbName = 'mks-pwa';
    this.storeName = 'cache-metadata';
  }

  /**
   * Get total cache size
   */
  async getTotalCacheSize() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return estimate.usage || 0;
    }

    // Fallback: calculate manually
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
   * Track cache access (for LRU)
   */
  async trackAccess(cacheKey) {
    try {
      const db = await this.openDB();
      const transaction = db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);

      // Get existing entry
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
   * Get LRU cache entries
   */
  async getLRUEntries(limit = 10) {
    try {
      const db = await this.openDB();
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
   * Evict LRU entries when threshold exceeded
   */
  async evictIfNeeded() {
    const totalSize = await this.getTotalCacheSize();

    logger.log(`[CacheManager] Current cache size: ${(totalSize / 1024 / 1024).toFixed(2)}MB`);

    if (totalSize < this.evictionThreshold) {
      return; // No eviction needed
    }

    logger.log('[CacheManager] Cache size exceeded threshold, starting LRU eviction...');

    const lruEntries = await this.getLRUEntries(20);
    const targetSize = this.maxCacheSize * 0.8; // Evict down to 80% capacity
    let evictedSize = 0;

    for (const entry of lruEntries) {
      if (totalSize - evictedSize < targetSize) {
        break;
      }

      // Delete from all caches
      const cacheNames = await caches.keys();
      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const deleted = await cache.delete(entry.key);

        if (deleted) {
          logger.log(`[CacheManager] Evicted: ${entry.key}`);
          // Estimate size (actual size calculation after deletion is complex)
          evictedSize += 10240; // Estimate 10KB per entry
        }
      }

      // Delete metadata
      try {
        const db = await this.openDB();
        const transaction = db.transaction([this.storeName], 'readwrite');
        await transaction.objectStore(this.storeName).delete(entry.key);
      } catch (error) {
        logger.error('[CacheManager] Metadata deletion failed:', error);
      }
    }

    logger.log(`[CacheManager] Evicted approximately ${(evictedSize / 1024 / 1024).toFixed(2)}MB`);
  }

  /**
   * Open IndexedDB
   */
  async openDB() {
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

        logger.log('[CacheManager] IndexedDB stores created');
      };
    });
  }

  /**
   * Clear all cache metadata
   */
  async clearMetadata() {
    try {
      const db = await this.openDB();
      const transaction = db.transaction([this.storeName], 'readwrite');
      await transaction.objectStore(this.storeName).clear();
      logger.log('[CacheManager] Metadata cleared');
    } catch (error) {
      logger.error('[CacheManager] Clear metadata failed:', error);
    }
  }
}

// Export
window.CacheManager = CacheManager;
