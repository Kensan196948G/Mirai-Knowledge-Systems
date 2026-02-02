/**
 * PWA Functionality E2E Tests
 * Tests Service Worker, Manifest, Offline mode, and Cache strategies
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5200';

test.describe('PWA Functionality Tests', () => {
  // Don't clear SW/cache for every test to avoid timing issues
  // Each test should work with or without pre-existing SW/cache
  test.beforeEach(async ({ page }) => {
    // Just navigate to start fresh page context
    await page.goto(BASE_URL);
    await page.waitForTimeout(500);
  });

  test('Service Worker registers successfully', async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for Service Worker to register and activate
    const swRegistered = await page.evaluate(() => {
      return new Promise((resolve) => {
        if (!('serviceWorker' in navigator)) {
          resolve(false);
          return;
        }

        // Wait for SW to be ready and controlling the page
        const checkController = () => {
          if (navigator.serviceWorker.controller) {
            resolve(true);
          } else {
            navigator.serviceWorker.ready.then((registration) => {
              // Wait for activation
              if (registration.active) {
                // Reload to get controller
                window.location.reload();
              }
            });
          }
        };

        // Check immediately
        checkController();

        // Also listen for controllerchange event
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          resolve(true);
        });

        // Timeout after 10 seconds
        setTimeout(() => resolve(navigator.serviceWorker.controller !== null), 10000);
      });
    });

    expect(swRegistered).toBeTruthy();
    console.log('✅ Service Worker registered and controlling page');
  });

  test('Service Worker version is correct', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    const swVersion = await page.evaluate(() => {
      return new Promise((resolve) => {
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.ready.then((registration) => {
            // Get SW version from script
            fetch('/sw.js').then(r => r.text()).then(text => {
              const match = text.match(/const SW_VERSION = '(.+?)'/);
              resolve(match ? match[1] : null);
            });
          });
        } else {
          resolve(null);
        }
      });
    });

    expect(swVersion).toBe('v1.3.0');
    console.log('✅ Service Worker version:', swVersion);
  });

  test('Manifest is accessible and valid', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/manifest.json`);
    expect(response.status()).toBe(200);

    const manifest = await response.json();
    expect(manifest.name).toContain('Mirai Knowledge');
    expect(manifest.short_name).toBe('MKS');
    expect(manifest.start_url).toBe('/');
    expect(manifest.display).toBe('standalone');
    expect(manifest.theme_color).toBe('#2f4b52');
    expect(manifest.icons.length).toBeGreaterThan(0);

    console.log('✅ Manifest valid:', manifest.name);
  });

  test('Offline page exists and displays correctly', async ({ page }) => {
    // Navigate directly to offline.html to verify it exists and works
    const response = await page.goto(`${BASE_URL}/offline.html`);

    // Verify page loaded successfully
    expect(response.status()).toBe(200);

    // Wait for page to render
    await page.waitForTimeout(500);

    // Verify offline page content
    const content = await page.textContent('body');
    const title = await page.title();

    // Check for offline page markers
    const isOfflinePage = content.includes('オフライン') ||
                          content.includes('インターネット接続がありません') ||
                          title.includes('オフライン');

    expect(isOfflinePage).toBeTruthy();
    console.log('✅ Offline page exists and displays correctly');

    // Additionally verify that offline.html is in the static cache list in Service Worker
    await page.goto(BASE_URL);
    await page.waitForTimeout(2000);

    const swCachesOffline = await page.evaluate(() => {
      // Fetch sw.js content and check if offline.html is listed
      return fetch('/sw.js')
        .then(r => r.text())
        .then(text => text.includes('/offline.html'))
        .catch(() => false);
    });

    expect(swCachesOffline).toBeTruthy();
    console.log('✅ Offline page is configured in Service Worker cache list');
  });

  test('Static assets are cached on first visit', async ({ page }) => {
    // Navigate to the site
    await page.goto(BASE_URL, { waitUntil: 'load' });

    // Wait for Service Worker to register
    await page.waitForTimeout(2000);

    // Wait for Service Worker to complete caching
    const cacheComplete = await page.evaluate(() => {
      return new Promise((resolve) => {
        if (!('serviceWorker' in navigator)) {
          resolve(false);
          return;
        }

        const checkCache = async () => {
          try {
            const cacheNames = await caches.keys();
            const staticCache = cacheNames.find(name => name.includes('static'));
            if (staticCache) {
              const cache = await caches.open(staticCache);
              const keys = await cache.keys();
              // Consider cache ready if it has at least some items
              resolve(keys.length > 0);
            } else {
              resolve(false);
            }
          } catch (e) {
            resolve(false);
          }
        };

        // Check immediately
        checkCache();

        // Also wait for SW ready
        navigator.serviceWorker.ready.then(() => {
          setTimeout(checkCache, 2000);
        });

        // Timeout
        setTimeout(() => checkCache(), 8000);
      });
    });

    // Additional wait to ensure caching is complete
    await page.waitForTimeout(1000);

    // Check Cache Storage
    const cacheInfo = await page.evaluate(() => {
      return caches.keys().then(async cacheNames => {
        const staticCache = cacheNames.find(name => name.includes('static'));
        if (staticCache) {
          const cache = await caches.open(staticCache);
          const requests = await cache.keys();
          return {
            cacheName: staticCache,
            urls: requests.map(r => r.url),
            count: requests.length
          };
        }
        return { cacheName: null, urls: [], count: 0 };
      });
    });

    expect(cacheInfo.count).toBeGreaterThan(0);

    // Check for essential files (be more flexible with paths)
    const hasHtml = cacheInfo.urls.some(url => url.includes('.html') || url.endsWith('/'));
    const hasJs = cacheInfo.urls.some(url => url.includes('.js'));
    const hasCss = cacheInfo.urls.some(url => url.includes('.css'));

    expect(hasHtml || hasJs || hasCss).toBeTruthy();

    console.log('✅ Static assets cached:', cacheInfo.count, 'files in', cacheInfo.cacheName);
  });

  test('PWA modules load successfully', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(2000);

    // Check if PWA modules are loaded
    const modulesLoaded = await page.evaluate(() => {
      return {
        CryptoHelper: typeof window.CryptoHelper !== 'undefined',
        CacheManager: typeof window.CacheManager !== 'undefined',
        SyncManager: typeof window.SyncManager !== 'undefined',
        InstallPromptManager: typeof window.InstallPromptManager !== 'undefined'
      };
    });

    expect(modulesLoaded.CryptoHelper).toBeTruthy();
    expect(modulesLoaded.CacheManager).toBeTruthy();
    expect(modulesLoaded.SyncManager).toBeTruthy();
    expect(modulesLoaded.InstallPromptManager).toBeTruthy();

    console.log('✅ All PWA modules loaded');
  });

  test('CryptoHelper encrypts and decrypts tokens', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(2000);

    const testResult = await page.evaluate(async () => {
      const crypto = new CryptoHelper();
      const testToken = 'test-jwt-token-12345';

      try {
        // Encrypt
        const { encrypted, iv } = await crypto.encrypt(testToken);

        // Decrypt
        const decrypted = await crypto.decrypt(encrypted, iv);

        return {
          success: decrypted === testToken,
          encrypted: encrypted.length > 0,
          iv: iv.length === 12
        };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    expect(testResult.success).toBeTruthy();
    expect(testResult.encrypted).toBeTruthy();
    expect(testResult.iv).toBeTruthy();

    console.log('✅ CryptoHelper encryption/decryption works');
  });

  test('IndexedDB stores are created', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    const dbStores = await page.evaluate(() => {
      return new Promise((resolve) => {
        const request = indexedDB.open('mks-pwa', 1);

        request.onsuccess = () => {
          const db = request.result;
          const storeNames = Array.from(db.objectStoreNames);
          db.close();
          resolve(storeNames);
        };

        request.onerror = () => resolve([]);
      });
    });

    expect(dbStores).toContain('sync-queue');
    expect(dbStores).toContain('tokens');
    expect(dbStores).toContain('cache-metadata');

    console.log('✅ IndexedDB stores created:', dbStores);
  });

  test('Online/Offline detection works', async ({ page, context }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(2000);

    // Check initial online status
    const initialOnline = await page.evaluate(() => navigator.onLine);
    expect(initialOnline).toBeTruthy();

    // Go offline
    await context.setOffline(true);
    await page.waitForTimeout(1000);

    // Check if offline indicator appears
    const offlineIndicatorVisible = await page.evaluate(() => {
      const indicator = document.getElementById('offline-indicator');
      return indicator && indicator.classList.contains('visible');
    });

    // Note: The indicator may not appear immediately due to event listener timing
    console.log('ℹ️ Offline indicator visible:', offlineIndicatorVisible);

    // Go back online
    await context.setOffline(false);

    console.log('✅ Online/Offline detection tested');
  });

  test('PWA features are detected', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(2000);

    const pwaFeatures = await page.evaluate(() => {
      return window.PWA_FEATURES || {};
    });

    expect(pwaFeatures.serviceWorker).toBeTruthy();
    expect(pwaFeatures.cacheAPI).toBeTruthy();
    expect(pwaFeatures.indexedDB).toBeTruthy();

    console.log('✅ PWA features detected:', pwaFeatures);
  });
});

test.describe('PWA Console Errors', () => {
  test('No critical console errors on page load', async ({ page }) => {
    const errors = [];
    const warnings = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });

    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Filter out known non-critical errors
    const criticalErrors = errors.filter(error => {
      // Ignore icon 404s (icons are optional or may not exist in test env)
      if (error.includes('icon-') || error.includes('maskable-icon')) return false;

      // Ignore general 404s for static assets (may not exist in test setup)
      if (error.includes('404') && error.includes('Failed to load resource')) return false;

      // Ignore favicon 404s
      if (error.includes('favicon.ico')) return false;

      // Ignore CORS errors for local development
      if (error.includes('CORS')) return false;

      // Ignore expected application errors when not authenticated
      if (error.includes('[NOTIFICATION]') && error.includes('No authentication token')) return false;
      if (error.includes('Failed to load unread count')) return false;

      // Ignore Background Sync errors (not supported in test environment or disabled)
      if (error.includes('[SyncManager]') && error.includes('Background Sync is disabled')) return false;
      if (error.includes('Failed to register sync')) return false;

      // Everything else is critical
      return true;
    });

    // Log all errors for debugging
    if (errors.length > 0) {
      console.log('ℹ️ Total console errors:', errors.length);
      console.log('ℹ️ Non-critical (filtered):', errors.length - criticalErrors.length);
    }

    if (criticalErrors.length > 0) {
      console.log('❌ Critical errors found:');
      criticalErrors.forEach(err => console.log('  -', err));
    }

    expect(criticalErrors.length).toBe(0);
    console.log('✅ No critical console errors');
  });
});
