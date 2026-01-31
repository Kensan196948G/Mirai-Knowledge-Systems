/**
 * Service Worker - Mirai Knowledge Systems PWA
 * Version: 1.3.0
 *
 * Cache Strategies:
 * - Static Assets: Cache First
 * - API Responses: Network First with Cache Fallback
 * - Images: Stale-While-Revalidate
 */

// Service Worker Version
const SW_VERSION = 'v1.3.0';
const CACHE_PREFIX = 'mks-';

// Cache Names
const CACHE_NAMES = {
  static: `${CACHE_PREFIX}static-${SW_VERSION}`,
  api: `${CACHE_PREFIX}api-${SW_VERSION}`,
  images: `${CACHE_PREFIX}images-${SW_VERSION}`,
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
  console.log('[SW] Install event:', SW_VERSION);

  event.waitUntil(
    caches.open(CACHE_NAMES.static)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static cache complete');
        // Do NOT call skipWaiting() automatically
        // Wait for user confirmation (see PWA_IMPLEMENTATION_GUIDE.md)
        console.log('[SW] Installed, waiting for activation signal');
      })
      .catch((error) => {
        console.error('[SW] Install failed:', error);
      })
  );
});

// ============================================================
// Activate Event
// ============================================================
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate event:', SW_VERSION);

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
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[SW] Claiming clients');
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

  // Strategy 2: Network First (API Requests)
  if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Strategy 3: Stale-While-Revalidate (Images)
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
// Background Sync Event
// ============================================================
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

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
          console.log('[SW] Sync success:', item.id);
        } else if (item.retries < 5) {
          item.retries = (item.retries || 0) + 1;
          await store.put(item);
        }
      } catch (error) {
        console.error('[SW] Sync failed:', item.id, error);
        if ((item.retries || 0) < 5) {
          item.retries = (item.retries || 0) + 1;
          await store.put(item);
        }
      }
    }
  } catch (error) {
    console.error('[SW] Sync queue processing failed:', error);
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
    console.log('[SW] Skip waiting signal received');
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_ACCESS') {
    // Track cache access for LRU (handled by cache-manager.js)
    console.log('[SW] Cache access tracked:', event.data.url);
  }
});

console.log('[SW] Service Worker script loaded:', SW_VERSION);
