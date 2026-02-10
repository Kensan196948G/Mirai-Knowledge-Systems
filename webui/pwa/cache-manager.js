/**
 * Cache Manager with LRU Eviction
 *
 * Features:
 * - LRU (Least Recently Used) eviction strategy
 * - 45MB threshold for eviction start
 * - 50MB maximum cache size
 * - IndexedDB metadata tracking
 */

// Use centralized configuration from config.js (window.IS_PRODUCTION, window.logger)
// config.js should be loaded in the HTML file before this script

// ロガー参照（グローバルスコープ汚染防止のため、window経由で参照）
// const logger は宣言せず、直接 window.logger または MKS_CONFIG.logger を使用

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
      (window.logger || window.MKS_CONFIG?.logger || console).error('[CacheManager] Track access failed:', error);
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
      (window.logger || window.MKS_CONFIG?.logger || console).error('[CacheManager] Get LRU entries failed:', error);
      return [];
    }
  }

  /**
   * Evict LRU entries when threshold exceeded
   */
  async evictIfNeeded() {
    const totalSize = await this.getTotalCacheSize();

    (window.logger || window.MKS_CONFIG?.logger || console).log(`[CacheManager] Current cache size: ${(totalSize / 1024 / 1024).toFixed(2)}MB`);

    if (totalSize < this.evictionThreshold) {
      return; // No eviction needed
    }

    (window.logger || window.MKS_CONFIG?.logger || console).log('[CacheManager] Cache size exceeded threshold, starting LRU eviction...');

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
          (window.logger || window.MKS_CONFIG?.logger || console).log(`[CacheManager] Evicted: ${entry.key}`);
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
        (window.logger || window.MKS_CONFIG?.logger || console).error('[CacheManager] Metadata deletion failed:', error);
      }
    }

    (window.logger || window.MKS_CONFIG?.logger || console).log(`[CacheManager] Evicted approximately ${(evictedSize / 1024 / 1024).toFixed(2)}MB`);
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

        (window.logger || window.MKS_CONFIG?.logger || console).log('[CacheManager] IndexedDB stores created');
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
      (window.logger || window.MKS_CONFIG?.logger || console).log('[CacheManager] Metadata cleared');
    } catch (error) {
      (window.logger || window.MKS_CONFIG?.logger || console).error('[CacheManager] Clear metadata failed:', error);
    }
  }
}

// Export
window.CacheManager = CacheManager;
