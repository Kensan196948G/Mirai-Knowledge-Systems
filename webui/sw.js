/**
 * Service Worker - Mirai Knowledge Systems PWA
 * Version: 1.4.0 (Phase E-4: MS365 File Preview)
 *
 * Cache Strategies:
 * - Static Assets: Cache First
 * - API Responses: Network First with Cache Fallback
 * - Images: Stale-While-Revalidate
 * - Thumbnails: Cache First (NEW)
 * - Previews: Network First (NEW)
 */

// Import centralized configuration
// Note: Service Workers cannot use ES6 imports, so we use importScripts
try {
  importScripts('./src/core/config.js');
} catch (e) {
  // Fallback if config.js is not available
  self.IS_PRODUCTION = (() => {
    if (typeof self !== 'undefined' && self.MKS_ENV) {
      return self.MKS_ENV === 'production';
    }
    const port = self.location?.port || '';
    return port === '9100' || port === '9443';
  })();
}

// Use self.IS_PRODUCTION from config.js (or fallback)
const IS_PRODUCTION = self.IS_PRODUCTION;

// ロガー（Service Worker独立スコープ用）
// Note: Service Workerはwindowスコープにアクセスできないため、独自のlogger定義が必要
// Try to use logger from config.js (via MKS_CONFIG), otherwise use fallback
const logger = (self.MKS_CONFIG && self.MKS_CONFIG.logger) || {
  log: (...args) => { if (!IS_PRODUCTION) console.log(...args); },
  warn: (...args) => { if (!IS_PRODUCTION) console.warn(...args); },
  error: (...args) => { if (!IS_PRODUCTION) console.error(...args); }
};

// Service Worker Version
const SW_VERSION = 'v1.4.0';
const CACHE_PREFIX = 'mks-';

// Cache Names
const CACHE_NAMES = {
  static: `${CACHE_PREFIX}static-${SW_VERSION}`,
  api: `${CACHE_PREFIX}api-${SW_VERSION}`,
  images: `${CACHE_PREFIX}images-${SW_VERSION}`,
  thumbnails: `${CACHE_PREFIX}thumbnails-${SW_VERSION}`,
  previews: `${CACHE_PREFIX}previews-${SW_VERSION}`,
};

// Cache Expiration (milliseconds)
const CACHE_EXPIRATION = {
  static: 7 * 24 * 60 * 60 * 1000,      // 7 days
  apiSearch: 60 * 60 * 1000,             // 1 hour
  apiDetail: 24 * 60 * 60 * 1000,        // 24 hours
  images: 30 * 24 * 60 * 60 * 1000,      // 30 days
};

// Static Assets to Cache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/login.html',
  '/admin.html',
  '/dashboard.html',
  '/search.html',
  '/knowledge-detail.html',
  '/sop-detail.html',
  '/law-detail.html',
  '/incident-detail.html',
  '/expert-consult.html',
  '/mfa-setup.html',
  '/mfa-settings.html',
  '/ms365-sync-settings.html',
  '/app.js',
  '/styles.css',
  '/dom-helpers.js',
  '/notifications.js',
  '/actions.js',
  '/mfa.js',
  '/ms365-sync.js',
  '/file-preview.js',
  '/recommendations.js',
  '/search-history.js',
  '/search-pagination.js',
  '/auth-guard.js',
  '/offline.html',
  '/pwa/install-prompt.js',
  '/pwa/cache-manager.js',
  '/pwa/sync-manager.js',
  '/pwa/crypto-helper.js',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

// API Endpoints to Cache
const API_CACHE_PATTERNS = [
  /\/api\/knowledge/,
  /\/api\/sop/,
  /\/api\/regulations/,
  /\/api\/law/,
  /\/api\/incidents/,
  /\/api\/consultations/,
  /\/api\/notifications/,
  /\/api\/search/,
];

// ============================================================
// Install Event
// ============================================================
self.addEventListener('install', (event) => {
  logger.log('[SW] Install event:', SW_VERSION);

  event.waitUntil(
    caches.open(CACHE_NAMES.static)
      .then((cache) => {
        logger.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        logger.log('[SW] Static cache complete');
        // Do NOT call skipWaiting() automatically
        // Wait for user confirmation (see PWA_IMPLEMENTATION_GUIDE.md)
        logger.log('[SW] Installed, waiting for activation signal');
      })
      .catch((error) => {
        logger.error('[SW] Install failed:', error);
      })
  );
});

// ============================================================
// Activate Event
// ============================================================
self.addEventListener('activate', (event) => {
  logger.log('[SW] Activate event:', SW_VERSION);

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        // Delete old caches
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName.startsWith(CACHE_PREFIX) &&
                     !Object.values(CACHE_NAMES).includes(cacheName);
            })
            .map((cacheName) => {
              logger.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        logger.log('[SW] Claiming clients');
        return self.clients.claim();
      })
  );
});

// ============================================================
// Fetch Event - Cache Strategies
// ============================================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http(s) requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Strategy 1: Cache First (Static Assets)
  if (STATIC_ASSETS.some(asset => url.pathname === asset || url.pathname.endsWith(asset))) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Strategy 2: MS365 Thumbnails - Cache First (7 days)
  if (url.pathname.includes('/api/v1/integrations/microsoft365/files/') &&
      url.pathname.includes('/thumbnail')) {
    event.respondWith(cacheFirstMS365Thumbnail(request));
    return;
  }

  // Strategy 3: MS365 Previews - Network First with Cache Fallback (7 days)
  if (url.pathname.includes('/api/v1/integrations/microsoft365/files/') &&
      (url.pathname.includes('/preview') || url.pathname.includes('/download'))) {
    event.respondWith(networkFirstMS365Preview(request));
    return;
  }

  // Strategy 4: Network First (API Requests)
  if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Strategy 5: Stale-While-Revalidate (Images)
  if (request.destination === 'image') {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Default: Network only
  event.respondWith(fetch(request));
});

// ============================================================
// Cache First Strategy
// ============================================================
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAMES.static);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlinePage = await caches.match('/offline.html');
      if (offlinePage) {
        return offlinePage;
      }
    }
    throw error;
  }
}

// ============================================================
// Network First Strategy
// ============================================================
async function networkFirst(request) {
  try {
    const response = await fetch(request);

    if (response.ok) {
      // Add expiration metadata
      const clonedResponse = response.clone();
      const body = await clonedResponse.text();
      const headers = new Headers(clonedResponse.headers);
      headers.set('sw-cache-time', Date.now().toString());

      const cachedResponse = new Response(body, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: headers
      });

      const cache = await caches.open(CACHE_NAMES.api);
      cache.put(request, cachedResponse);
    }

    return response;
  } catch (error) {
    // Network failed, try cache
    const cached = await caches.match(request);

    if (cached) {
      // Check if cache is expired
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

// ============================================================
// Stale-While-Revalidate Strategy
// ============================================================
async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      caches.open(CACHE_NAMES.images).then(cache => {
        cache.put(request, response.clone());
      });
    }
    return response;
  }).catch(() => {});

  return cached || fetchPromise;
}

// ============================================================
// Cache First - MS365 Thumbnails (7 days)
// ============================================================
async function cacheFirstMS365Thumbnail(request) {
  const cache = await caches.open(CACHE_NAMES.thumbnails);
  const cached = await cache.match(request);

  if (cached) {
    // Check if cache is expired (7 days)
    const cacheTime = cached.headers.get('sw-cache-time');
    if (cacheTime) {
      const age = Date.now() - parseInt(cacheTime);
      if (age < CACHE_EXPIRATION.static) {
        logger.log('[SW] Thumbnail cache hit:', request.url);
        return cached;
      }
    }
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      // Clone response and add cache timestamp
      const clonedResponse = response.clone();
      const blob = await clonedResponse.blob();
      const headers = new Headers(clonedResponse.headers);
      headers.set('sw-cache-time', Date.now().toString());

      const cachedResponse = new Response(blob, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: headers
      });

      await cache.put(request, cachedResponse);
      logger.log('[SW] Thumbnail cached:', request.url);
    }
    return response;
  } catch (error) {
    // Network failed, return cached if available
    if (cached) {
      logger.log('[SW] Thumbnail offline fallback:', request.url);
      return cached;
    }
    throw error;
  }
}

// ============================================================
// Network First - MS365 Previews (7 days cache fallback)
// ============================================================
async function networkFirstMS365Preview(request) {
  const cache = await caches.open(CACHE_NAMES.previews);

  try {
    const response = await fetch(request);

    if (response.ok) {
      // Clone response and add cache timestamp
      const clonedResponse = response.clone();
      const blob = await clonedResponse.blob();
      const headers = new Headers(clonedResponse.headers);
      headers.set('sw-cache-time', Date.now().toString());

      const cachedResponse = new Response(blob, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: headers
      });

      await cache.put(request, cachedResponse);
      logger.log('[SW] Preview cached:', request.url);
    }

    return response;
  } catch (error) {
    // Network failed, try cache
    const cached = await cache.match(request);

    if (cached) {
      // Check if cache is expired (7 days)
      const cacheTime = cached.headers.get('sw-cache-time');
      if (cacheTime) {
        const age = Date.now() - parseInt(cacheTime);
        if (age < CACHE_EXPIRATION.static) {
          logger.log('[SW] Preview offline fallback:', request.url);
          return cached;
        }
      }
    }

    throw error;
  }
}

// ============================================================
// Background Sync Event
// ============================================================
self.addEventListener('sync', (event) => {
  logger.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-queue') {
    event.waitUntil(processSyncQueue());
  }
});

// ============================================================
// Process Background Sync Queue
// ============================================================
async function processSyncQueue() {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['sync-queue'], 'readwrite');
    const store = transaction.objectStore('sync-queue');
    const items = await getAllFromStore(store);

    for (const item of items) {
      try {
        const response = await fetch(item.url, {
          method: item.method,
          headers: item.headers,
          body: item.body,
        });

        if (response.ok) {
          await store.delete(item.id);
          logger.log('[SW] Sync success:', item.id);
        } else if (item.retries < 5) {
          item.retries = (item.retries || 0) + 1;
          await store.put(item);
        }
      } catch (error) {
        logger.error('[SW] Sync failed:', item.id, error);
        if ((item.retries || 0) < 5) {
          item.retries = (item.retries || 0) + 1;
          await store.put(item);
        }
      }
    }
  } catch (error) {
    logger.error('[SW] Sync queue processing failed:', error);
  }
}

// ============================================================
// IndexedDB Helper
// ============================================================
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('mks-pwa', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Create sync-queue store
      if (!db.objectStoreNames.contains('sync-queue')) {
        db.createObjectStore('sync-queue', { keyPath: 'id', autoIncrement: true });
      }

      // Create tokens store
      if (!db.objectStoreNames.contains('tokens')) {
        db.createObjectStore('tokens', { keyPath: 'key' });
      }

      // Create cache-metadata store with index
      if (!db.objectStoreNames.contains('cache-metadata')) {
        const store = db.createObjectStore('cache-metadata', { keyPath: 'key' });
        store.createIndex('last_accessed_at', 'last_accessed_at', { unique: false });
      }

      logger.log('[SW] IndexedDB upgraded, stores:', Array.from(db.objectStoreNames));
    };
  });
}

function getAllFromStore(store) {
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// ============================================================
// Message Handler (for skipWaiting)
// ============================================================
self.addEventListener('message', (event) => {
  if (event.data && event.data.action === 'SKIP_WAITING') {
    logger.log('[SW] Skip waiting signal received');
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_ACCESS') {
    // Track cache access for LRU (handled by cache-manager.js)
    logger.log('[SW] Cache access tracked:', event.data.url);
  }
});

logger.log('[SW] Service Worker script loaded:', SW_VERSION);
