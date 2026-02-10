/**
 * Configuration Module - Mirai Knowledge Systems
 * Version: 1.4.0 (Phase E-4: Duplicate Declaration Fix)
 *
 * Centralized environment and configuration management
 *
 * Usage:
 *   import { IS_PRODUCTION, ENV_PORTS, API_BASE_URL } from './src/core/config.js';
 *
 * For files that cannot use ES6 modules (e.g., inline scripts):
 *   <script src="./src/core/config.js"></script>
 *   // IS_PRODUCTION is now available globally via window.IS_PRODUCTION
 */

// Wrap in IIFE to prevent duplicate declaration errors
(function() {
  'use strict';

  // Skip if already loaded (check both window and self contexts)
  if ((typeof window !== 'undefined' && window.MKS_CONFIG) ||
      (typeof self !== 'undefined' && self.MKS_CONFIG)) {
    return;
  }

// Environment ports configuration
const ENV_PORTS = {
  production: {
    http: 9100,
    https: 9443
  },
  development: {
    http: 5200,
    https: 5243
  }
};

/**
 * Environment Detection Logic
 *
 * Priority order:
 * 1. window.MKS_ENV (set by backend via HTML template)
 * 2. self.MKS_ENV (for Service Worker context)
 * 3. URL parameter (?env=production)
 * 4. localStorage.getItem('MKS_ENV')
 * 5. Port number matching ENV_PORTS
 * 6. Hostname (localhost/127.0.0.1 = development)
 * 7. Default: false (development)
 */
const IS_PRODUCTION = (() => {
  // Priority 1: Backend-set environment variable
  if (typeof window !== 'undefined' && window.MKS_ENV) {
    return window.MKS_ENV === 'production';
  }

  // Priority 2: Service Worker context
  if (typeof self !== 'undefined' && self.MKS_ENV) {
    return self.MKS_ENV === 'production';
  }

  // Priority 3: URL parameter (only in window context)
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('env') === 'production') return true;
    if (urlParams.get('env') === 'development') return false;
  }

  // Priority 4: localStorage (only in window context)
  if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
    const envSetting = localStorage.getItem('MKS_ENV');
    if (envSetting === 'production') return true;
    if (envSetting === 'development') return false;
  }

  // Priority 5: Port number detection
  const location = typeof self !== 'undefined' ? self.location :
                   typeof window !== 'undefined' ? window.location : null;

  if (location) {
    const port = location.port || '';
    if (port === String(ENV_PORTS.production.http) ||
        port === String(ENV_PORTS.production.https)) {
      return true;
    }
    if (port === String(ENV_PORTS.development.http) ||
        port === String(ENV_PORTS.development.https)) {
      return false;
    }

    // Priority 6: Hostname detection
    const hostname = location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return false;
    }
  }

  // Default: development
  return false;
})();

/**
 * API Base URL
 * Automatically determined based on current location
 */
const API_BASE_URL = (() => {
  const location = typeof self !== 'undefined' ? self.location :
                   typeof window !== 'undefined' ? window.location : null;

  if (!location) return '';

  return `${location.protocol}//${location.hostname}:${location.port}`;
})();

/**
 * Secure Logger (Fallback Definition)
 * Logs only in development mode to prevent information leakage
 *
 * Note: This is a fallback definition for environments where logger.js is not loaded.
 * Prefer using webui/src/core/logger.js for the canonical logger implementation.
 */
const logger = (typeof window !== 'undefined' && window.logger) ||
               (typeof self !== 'undefined' && self.logger) || {
  log: (...args) => { if (!IS_PRODUCTION) console.log(...args); },
  warn: (...args) => { if (!IS_PRODUCTION) console.warn(...args); },
  error: (...args) => { if (!IS_PRODUCTION) console.error(...args); },
  info: (...args) => { if (!IS_PRODUCTION) console.info(...args); },
  debug: (...args) => { if (!IS_PRODUCTION) console.debug(...args); }
};

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { IS_PRODUCTION, ENV_PORTS, API_BASE_URL, logger };
}

// Export for global scope (non-module scripts)
if (typeof window !== 'undefined') {
  window.IS_PRODUCTION = IS_PRODUCTION;
  window.ENV_PORTS = ENV_PORTS;
  window.API_BASE_URL = API_BASE_URL;
  window.MKS_CONFIG = { IS_PRODUCTION, ENV_PORTS, API_BASE_URL, logger };
}

// Export for Service Worker context
if (typeof self !== 'undefined' && typeof WorkerGlobalScope !== 'undefined') {
  self.IS_PRODUCTION = IS_PRODUCTION;
  self.ENV_PORTS = ENV_PORTS;
  self.API_BASE_URL = API_BASE_URL;
  self.MKS_CONFIG = { IS_PRODUCTION, ENV_PORTS, API_BASE_URL, logger };
}

})(); // End of IIFE
