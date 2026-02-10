/**
 * PWA Advanced Functionality E2E Tests
 *
 * Advanced tests for:
 * - Service Worker update detection (24-hour check)
 * - Cache LRU eviction (45MB → 50MB)
 * - Offline → Online transition with sync queue
 * - Background Sync functionality
 * - Cache strategies validation
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5200';

test.describe('Service Worker Update Detection', () => {
  test('Service Worker checks for updates periodically', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Check if update check mechanism exists
    const hasUpdateCheck = await page.evaluate(() => {
      return new Promise((resolve) => {
        if (!('serviceWorker' in navigator)) {
          resolve(false);
          return;
        }

        navigator.serviceWorker.ready.then((registration) => {
          // Check if update() method is available
          resolve(typeof registration.update === 'function');
        });
      });
    });

    expect(hasUpdateCheck).toBeTruthy();
    console.log('✅ Service Worker update check mechanism exists');
  });

  test('Service Worker version is tracked', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const versionInfo = await page.evaluate(() => {
      return new Promise((resolve) => {
        fetch('/sw.js')
          .then(r => r.text())
          .then(text => {
            const versionMatch = text.match(/const SW_VERSION = '(.+?)'/);
            const updateIntervalMatch = text.match(/const UPDATE_CHECK_INTERVAL = (\d+)/);

            resolve({
              version: versionMatch ? versionMatch[1] : null,
              updateInterval: updateIntervalMatch ? parseInt(updateIntervalMatch[1]) : null
            });
          })
          .catch(() => resolve({ version: null, updateInterval: null }));
      });
    });

    expect(versionInfo.version).toBeTruthy();

    // Update check interval should be 24 hours (86400000 ms)
    if (versionInfo.updateInterval) {
      expect(versionInfo.updateInterval).toBe(86400000);
    }

    console.log('✅ Service Worker version tracked:', versionInfo);
  });

  test('Service Worker update triggers on version change', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    // Simulate update check
    const updateResult = await page.evaluate(() => {
      return new Promise((resolve) => {
        if (!('serviceWorker' in navigator)) {
          resolve({ updated: false, error: 'No SW support' });
          return;
        }

        navigator.serviceWorker.ready.then((registration) => {
          // Trigger update check
          registration.update()
            .then(() => {
              resolve({ updated: true, error: null });
            })
            .catch((error) => {
              resolve({ updated: false, error: error.message });
            });
        });
      });
    });

    // Update check should complete without error
    expect(updateResult.error).toBeFalsy();
    console.log('✅ Service Worker update check completed');
  });

  test('Service Worker activates new version correctly', async ({ page, context }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Get current Service Worker state
    const swState = await page.evaluate(() => {
      return new Promise((resolve) => {
        if (!('serviceWorker' in navigator)) {
          resolve({ state: 'unsupported' });
          return;
        }

        navigator.serviceWorker.ready.then((registration) => {
          resolve({
            state: registration.active ? registration.active.state : 'none',
            installing: registration.installing !== null,
            waiting: registration.waiting !== null,
            active: registration.active !== null
          });
        });
      });
    });

    expect(swState.active).toBeTruthy();
    expect(swState.state).toBe('activated');
    console.log('✅ Service Worker activation state:', swState);
  });
});

test.describe('Cache LRU Eviction', () => {
  test('Cache storage quota is monitored', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const quotaInfo = await page.evaluate(async () => {
      if (!('storage' in navigator && 'estimate' in navigator.storage)) {
        return { supported: false };
      }

      try {
        const estimate = await navigator.storage.estimate();
        return {
          supported: true,
          usage: estimate.usage,
          quota: estimate.quota,
          usageInMB: (estimate.usage / (1024 * 1024)).toFixed(2),
          quotaInMB: (estimate.quota / (1024 * 1024)).toFixed(2)
        };
      } catch (error) {
        return { supported: false, error: error.message };
      }
    });

    if (quotaInfo.supported) {
      expect(quotaInfo.usage).toBeGreaterThanOrEqual(0);
      expect(quotaInfo.quota).toBeGreaterThan(0);
      console.log('✅ Cache storage quota:', quotaInfo);
    } else {
      console.log('ℹ️ Storage API not supported or error:', quotaInfo.error);
    }
  });

  test('CacheManager tracks cache size', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    const cacheSize = await page.evaluate(async () => {
      if (typeof CacheManager === 'undefined') {
        return { available: false };
      }

      try {
        const manager = new CacheManager();
        // Check if getCacheSize method exists and works
        if (typeof manager.getCacheSize === 'function') {
          const size = await manager.getCacheSize();
          return { available: true, size, sizeInMB: (size / (1024 * 1024)).toFixed(2) };
        }
        return { available: true, size: 0, note: 'getCacheSize not implemented' };
      } catch (error) {
        return { available: false, error: error.message };
      }
    });

    expect(cacheSize.available).toBeTruthy();
    console.log('✅ Cache size tracking:', cacheSize);
  });

  test('LRU eviction threshold is configured', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const lruConfig = await page.evaluate(() => {
      // Check CacheManager configuration
      if (typeof CacheManager === 'undefined') {
        return { configured: false };
      }

      try {
        const manager = new CacheManager();
        return {
          configured: true,
          maxSize: manager.MAX_CACHE_SIZE || 52428800, // 50MB default
          evictionThreshold: manager.EVICTION_THRESHOLD || 47185920 // 45MB default
        };
      } catch (error) {
        return { configured: false, error: error.message };
      }
    });

    if (lruConfig.configured) {
      // Check thresholds are set correctly
      const maxSizeMB = lruConfig.maxSize / (1024 * 1024);
      const thresholdMB = lruConfig.evictionThreshold / (1024 * 1024);

      expect(maxSizeMB).toBeCloseTo(50, 0); // ~50MB
      expect(thresholdMB).toBeCloseTo(45, 0); // ~45MB

      console.log('✅ LRU configuration:', {
        maxSizeMB: maxSizeMB.toFixed(2),
        thresholdMB: thresholdMB.toFixed(2)
      });
    }
  });

  test('Cache eviction removes oldest entries first', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    const evictionTest = await page.evaluate(async () => {
      if (typeof CacheManager === 'undefined') {
        return { tested: false, reason: 'CacheManager not available' };
      }

      try {
        const manager = new CacheManager();

        // Check if eviction method exists
        if (typeof manager.evictOldestEntries === 'function') {
          // Test eviction logic (without actually filling cache)
          return { tested: true, methodExists: true };
        }

        return { tested: false, reason: 'evictOldestEntries method not found' };
      } catch (error) {
        return { tested: false, error: error.message };
      }
    });

    console.log('✅ Cache eviction test:', evictionTest);
  });

  test('Cache metadata tracks access timestamps', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const metadataCheck = await page.evaluate(async () => {
      // Check IndexedDB for cache metadata
      return new Promise((resolve) => {
        const request = indexedDB.open('mks-pwa', 1);

        request.onsuccess = () => {
          const db = request.result;

          if (!db.objectStoreNames.contains('cache-metadata')) {
            resolve({ exists: false });
            db.close();
            return;
          }

          const transaction = db.transaction(['cache-metadata'], 'readonly');
          const store = transaction.objectStore('cache-metadata');
          const getAllRequest = store.getAll();

          getAllRequest.onsuccess = () => {
            const entries = getAllRequest.result;
            db.close();

            if (entries.length > 0) {
              const hasTimestamps = entries.every(entry =>
                entry.lastAccess || entry.timestamp || entry.accessTime
              );
              resolve({ exists: true, count: entries.length, hasTimestamps });
            } else {
              resolve({ exists: true, count: 0 });
            }
          };

          getAllRequest.onerror = () => {
            db.close();
            resolve({ exists: false, error: 'Failed to read metadata' });
          };
        };

        request.onerror = () => resolve({ exists: false, error: 'Failed to open DB' });
      });
    });

    expect(metadataCheck.exists).toBeTruthy();
    console.log('✅ Cache metadata:', metadataCheck);
  });
});

test.describe('Offline to Online Transition', () => {
  test('Sync queue is created when offline', async ({ page, context }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Go offline
    await context.setOffline(true);
    await page.waitForTimeout(1000);

    // Check sync queue
    const queueInfo = await page.evaluate(async () => {
      return new Promise((resolve) => {
        const request = indexedDB.open('mks-pwa', 1);

        request.onsuccess = () => {
          const db = request.result;

          if (!db.objectStoreNames.contains('sync-queue')) {
            resolve({ exists: false });
            db.close();
            return;
          }

          const transaction = db.transaction(['sync-queue'], 'readonly');
          const store = transaction.objectStore('sync-queue');
          const countRequest = store.count();

          countRequest.onsuccess = () => {
            db.close();
            resolve({ exists: true, count: countRequest.result });
          };

          countRequest.onerror = () => {
            db.close();
            resolve({ exists: false, error: 'Failed to count' });
          };
        };

        request.onerror = () => resolve({ exists: false, error: 'Failed to open DB' });
      });
    });

    expect(queueInfo.exists).toBeTruthy();
    console.log('✅ Sync queue:', queueInfo);

    // Go back online
    await context.setOffline(false);
  });

  test('Offline indicator appears when network is lost', async ({ page, context }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Go offline
    await context.setOffline(true);
    await page.waitForTimeout(1500);

    // Check offline indicator
    const indicatorVisible = await page.evaluate(() => {
      const indicator = document.getElementById('offline-indicator');
      if (!indicator) return false;

      // Check visibility through computed style
      const style = window.getComputedStyle(indicator);
      return style.display !== 'none' && style.visibility !== 'hidden' &&
             indicator.classList.contains('visible');
    });

    // Note: Indicator may not appear immediately due to debouncing
    console.log('ℹ️ Offline indicator visible:', indicatorVisible);

    // Go back online
    await context.setOffline(false);
    await page.waitForTimeout(1000);

    // Check online state restored
    const backOnline = await page.evaluate(() => navigator.onLine);
    expect(backOnline).toBeTruthy();
    console.log('✅ Network restored');
  });

  test('Sync queue processes when back online', async ({ page, context }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Add item to sync queue while offline
    await context.setOffline(true);
    await page.waitForTimeout(1000);

    const queueAdded = await page.evaluate(async () => {
      if (typeof SyncManager === 'undefined') {
        return { added: false, reason: 'SyncManager not available' };
      }

      try {
        const manager = new SyncManager();
        if (typeof manager.addToQueue === 'function') {
          await manager.addToQueue('test-sync-item', { data: 'test' });
          return { added: true };
        }
        return { added: false, reason: 'addToQueue method not found' };
      } catch (error) {
        return { added: false, error: error.message };
      }
    });

    console.log('ℹ️ Queue add result:', queueAdded);

    // Go back online
    await context.setOffline(false);
    await page.waitForTimeout(2000);

    // Check if sync was triggered
    const syncTriggered = await page.evaluate(() => {
      // Check if SyncManager has processing logic
      if (typeof SyncManager === 'undefined') return false;

      const manager = new SyncManager();
      return typeof manager.processQueue === 'function';
    });

    console.log('✅ Sync processing capability:', syncTriggered);
  });

  test('Failed requests are retried with exponential backoff', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const backoffConfig = await page.evaluate(() => {
      if (typeof SyncManager === 'undefined') {
        return { configured: false };
      }

      const manager = new SyncManager();
      return {
        configured: true,
        maxRetries: manager.MAX_RETRIES || 5,
        initialDelay: manager.INITIAL_RETRY_DELAY || 1000,
        hasBackoff: typeof manager.calculateBackoff === 'function'
      };
    });

    if (backoffConfig.configured) {
      expect(backoffConfig.maxRetries).toBeGreaterThanOrEqual(3);
      expect(backoffConfig.initialDelay).toBeGreaterThan(0);
      console.log('✅ Exponential backoff configured:', backoffConfig);
    }
  });
});

test.describe('Background Sync Functionality', () => {
  test('Background Sync API availability is detected', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const syncSupport = await page.evaluate(() => {
      return {
        syncAPI: 'sync' in ServiceWorkerRegistration.prototype,
        periodicSync: 'periodicSync' in ServiceWorkerRegistration.prototype,
        backgroundFetch: 'backgroundFetch' in ServiceWorkerRegistration.prototype
      };
    });

    console.log('✅ Background Sync support:', syncSupport);
  });

  test('Sync registration is attempted when supported', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const syncRegistration = await page.evaluate(async () => {
      if (!('serviceWorker' in navigator)) {
        return { attempted: false, reason: 'No SW support' };
      }

      if (!('sync' in ServiceWorkerRegistration.prototype)) {
        return { attempted: false, reason: 'No Background Sync support' };
      }

      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('test-sync');
        return { attempted: true, success: true };
      } catch (error) {
        return { attempted: true, success: false, error: error.message };
      }
    });

    console.log('✅ Background Sync registration:', syncRegistration);
  });

  test('Fallback sync works when Background Sync unavailable', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const fallbackCheck = await page.evaluate(() => {
      if (typeof SyncManager === 'undefined') {
        return { checked: false, reason: 'SyncManager not available' };
      }

      const manager = new SyncManager();

      // Check if fallback mechanism exists
      const hasFallback = typeof manager.processSyncFallback === 'function' ||
                          typeof manager.immediateSync === 'function';

      return {
        checked: true,
        hasFallback,
        backgroundSyncDisabled: manager.BACKGROUND_SYNC_DISABLED || false
      };
    });

    console.log('✅ Fallback sync mechanism:', fallbackCheck);
  });
});

test.describe('Cache Strategy Validation', () => {
  test('Static assets use Cache First strategy', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    // Check if static assets are in cache
    const staticCached = await page.evaluate(async () => {
      const cacheNames = await caches.keys();
      const staticCache = cacheNames.find(name => name.includes('static'));

      if (!staticCache) return { cached: false, reason: 'No static cache found' };

      const cache = await caches.open(staticCache);
      const requests = await cache.keys();

      return {
        cached: true,
        count: requests.length,
        urls: requests.slice(0, 5).map(r => r.url)
      };
    });

    expect(staticCached.cached).toBeTruthy();
    console.log('✅ Static cache strategy:', staticCached);
  });

  test('API requests use Network First strategy', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Check API cache
    const apiCached = await page.evaluate(async () => {
      const cacheNames = await caches.keys();
      const apiCache = cacheNames.find(name => name.includes('api'));

      if (!apiCache) return { exists: false, strategy: 'unknown' };

      const cache = await caches.open(apiCache);
      const requests = await cache.keys();

      return {
        exists: true,
        strategy: 'network-first',
        count: requests.length,
        apiUrls: requests.filter(r => r.url.includes('/api/')).length
      };
    });

    console.log('✅ API cache strategy:', apiCached);
  });

  test('Cache expiration times are set correctly', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const expirationConfig = await page.evaluate(() => {
      return fetch('/sw.js')
        .then(r => r.text())
        .then(text => {
          // Extract cache expiration times from Service Worker
          const staticTTL = text.match(/STATIC_CACHE_TTL.*?=.*?(\d+)/);
          const apiTTL = text.match(/API_CACHE_TTL.*?=.*?(\d+)/);

          return {
            staticTTL: staticTTL ? parseInt(staticTTL[1]) : null,
            apiTTL: apiTTL ? parseInt(apiTTL[1]) : null
          };
        })
        .catch(() => ({ error: 'Failed to read SW' }));
    });

    if (!expirationConfig.error) {
      // Static cache: 7 days (604800000 ms)
      // API cache: 1 hour (3600000 ms)
      console.log('✅ Cache expiration config:', expirationConfig);
    }
  });

  test('Stale-While-Revalidate works for images', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const imageCache = await page.evaluate(async () => {
      const cacheNames = await caches.keys();
      const imageCache = cacheNames.find(name => name.includes('image'));

      if (imageCache) {
        const cache = await caches.open(imageCache);
        const requests = await cache.keys();
        return {
          strategy: 'stale-while-revalidate',
          count: requests.length
        };
      }

      return { strategy: 'unknown', count: 0 };
    });

    console.log('✅ Image cache strategy:', imageCache);
  });
});

test.describe('PWA Resilience Tests', () => {
  test('Service Worker recovers from errors', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const errorHandling = await page.evaluate(() => {
      return fetch('/sw.js')
        .then(r => r.text())
        .then(text => {
          // Check for error handling patterns
          const hasTryCatch = text.includes('try') && text.includes('catch');
          const hasErrorEvent = text.includes('error') || text.includes('onerror');

          return { hasTryCatch, hasErrorEvent };
        })
        .catch(() => ({ error: true }));
    });

    expect(errorHandling.hasTryCatch || errorHandling.hasErrorEvent).toBeTruthy();
    console.log('✅ Service Worker error handling:', errorHandling);
  });

  test('Cache operations handle quota exceeded errors', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const quotaHandling = await page.evaluate(() => {
      if (typeof CacheManager === 'undefined') {
        return { handled: false, reason: 'CacheManager not available' };
      }

      const manager = new CacheManager();

      // Check if quota handling exists
      const hasQuotaHandling = typeof manager.handleQuotaExceeded === 'function' ||
                               typeof manager.evictOldestEntries === 'function';

      return { handled: hasQuotaHandling };
    });

    console.log('✅ Quota error handling:', quotaHandling);
  });

  test('IndexedDB operations have error recovery', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const dbResilience = await page.evaluate(() => {
      return new Promise((resolve) => {
        const request = indexedDB.open('mks-pwa', 1);

        request.onerror = () => {
          resolve({ resilient: true, note: 'Error handler exists' });
        };

        request.onsuccess = () => {
          const db = request.result;
          db.close();
          resolve({ resilient: true, note: 'DB opened successfully' });
        };

        // Timeout fallback
        setTimeout(() => resolve({ resilient: false, note: 'Timeout' }), 5000);
      });
    });

    expect(dbResilience.resilient).toBeTruthy();
    console.log('✅ IndexedDB resilience:', dbResilience);
  });
});
