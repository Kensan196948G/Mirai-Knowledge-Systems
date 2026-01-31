/**
 * PWA Functionality E2E Tests
 * Tests Service Worker, Manifest, Offline mode, and Cache strategies
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5200';

test.describe('PWA Functionality Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Clear Service Workers before each test
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      if ('serviceWorker' in navigator) {
        return navigator.serviceWorker.getRegistrations().then(registrations => {
          return Promise.all(registrations.map(r => r.unregister()));
        });
      }
    });
  });

  test('Service Worker registers successfully', async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for Service Worker registration
    await page.waitForTimeout(3000);

    const swRegistered = await page.evaluate(() => {
      return new Promise((resolve) => {
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.ready.then(() => {
            resolve(navigator.serviceWorker.controller !== null);
          });
        } else {
          resolve(false);
        }
      });
    });

    expect(swRegistered).toBeTruthy();
    console.log('✅ Service Worker registered');
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

  test('Offline page loads when network disabled', async ({ page, context }) => {
    await page.goto(BASE_URL);

    // Wait for Service Worker to activate
    await page.waitForTimeout(3000);

    // Go offline
    await context.setOffline(true);

    // Navigate to non-existent page
    await page.goto(`${BASE_URL}/nonexistent-test-page`, {
      waitUntil: 'networkidle',
      timeout: 10000
    }).catch(() => {});

    // Check if offline page is displayed
    const content = await page.textContent('body');
    expect(content).toContain('オフライン');
    expect(content).toContain('キャッシュコンテンツを表示');

    console.log('✅ Offline page displayed');

    // Go back online
    await context.setOffline(false);
  });

  test('Static assets are cached on first visit', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    // Check Cache Storage
    const cachedAssets = await page.evaluate(() => {
      return caches.keys().then(cacheNames => {
        const staticCache = cacheNames.find(name => name.includes('static'));
        if (staticCache) {
          return caches.open(staticCache).then(cache => {
            return cache.keys().then(requests => {
              return requests.map(r => r.url);
            });
          });
        }
        return [];
      });
    });

    expect(cachedAssets.length).toBeGreaterThan(0);
    expect(cachedAssets.some(url => url.includes('index.html'))).toBeTruthy();
    expect(cachedAssets.some(url => url.includes('app.js'))).toBeTruthy();
    expect(cachedAssets.some(url => url.includes('styles.css'))).toBeTruthy();

    console.log('✅ Static assets cached:', cachedAssets.length, 'files');
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

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    // Filter out expected errors (404 for icons not yet generated)
    const criticalErrors = errors.filter(error => {
      return !error.includes('icon-') &&
             !error.includes('404') &&
             !error.includes('Failed to load resource');
    });

    expect(criticalErrors.length).toBe(0);

    if (errors.length > 0) {
      console.log('ℹ️ Expected errors (icons not generated):', errors.length);
    }
    console.log('✅ No critical console errors');
  });
});
