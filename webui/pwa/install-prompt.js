/**
 * PWA Install Prompt Manager
 * Manages installation UI and user engagement
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

class InstallPromptManager {
  constructor() {
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.dismissKey = 'pwa-install-dismissed';
    this.init();
  }

  init() {
    // Listen for beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      logger.log('[PWA] Install prompt ready');

      // Show install button after delay or page views
      this.scheduleInstallPrompt();
    });

    // Listen for appinstalled event
    window.addEventListener('appinstalled', () => {
      this.isInstalled = true;
      this.hideInstallButton();
      this.trackInstallation();
      logger.log('[PWA] App installed successfully');
    });

    // Check if already installed (standalone mode)
    if (window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true) {
      this.isInstalled = true;
      logger.log('[PWA] App running in standalone mode');
    }
  }

  scheduleInstallPrompt() {
    // Check cooldown period
    const dismissedAt = localStorage.getItem(this.dismissKey);
    if (dismissedAt) {
      const daysSinceDismissed = (Date.now() - parseInt(dismissedAt)) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) {
        logger.log('[PWA] Install prompt on cooldown');
        return;
      }
    }

    // Show after 2 minutes or 3 page views
    const pageViews = parseInt(localStorage.getItem('pwa-page-views') || '0') + 1;
    localStorage.setItem('pwa-page-views', pageViews.toString());

    if (pageViews >= 3) {
      this.showInstallButton();
    } else {
      setTimeout(() => {
        this.showInstallButton();
      }, 2 * 60 * 1000); // 2 minutes
    }
  }

  showInstallButton() {
    if (this.isInstalled || !this.deferredPrompt) {
      return;
    }

    // Remove existing banner if present
    const existing = document.getElementById('pwa-install-banner');
    if (existing) {
      existing.remove();
    }

    // Create install banner
    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.className = 'pwa-install-banner';
    banner.innerHTML = `
      <div class="pwa-install-content">
        <div class="pwa-install-icon">📱</div>
        <div class="pwa-install-text">
          <strong>アプリとしてインストール</strong>
          <p>オフラインでも使用できます</p>
        </div>
        <button class="cta" id="pwa-install-button">インストール</button>
        <button class="cta ghost" id="pwa-install-dismiss">後で</button>
      </div>
    `;

    document.body.appendChild(banner);

    // Event listeners
    document.getElementById('pwa-install-button').addEventListener('click', () => {
      this.promptInstall();
    });

    document.getElementById('pwa-install-dismiss').addEventListener('click', () => {
      this.dismissInstall();
    });

    logger.log('[PWA] Install banner displayed');
  }

  async promptInstall() {
    if (!this.deferredPrompt) {
      logger.warn('[PWA] No deferred prompt available');
      return;
    }

    // Show native install prompt
    this.deferredPrompt.prompt();

    // Wait for user choice
    const { outcome } = await this.deferredPrompt.userChoice;
    logger.log('[PWA] User choice:', outcome);

    if (outcome === 'accepted') {
      logger.log('[PWA] User accepted install');
    } else {
      logger.log('[PWA] User dismissed install');
    }

    // Clear deferred prompt
    this.deferredPrompt = null;
    this.hideInstallButton();
  }

  dismissInstall() {
    // Set cooldown period (7 days)
    localStorage.setItem(this.dismissKey, Date.now().toString());
    this.hideInstallButton();
    logger.log('[PWA] Install prompt dismissed');
  }

  hideInstallButton() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
      banner.classList.add('fade-out');
      setTimeout(() => {
        banner.remove();
      }, 300);
    }
  }

  trackInstallation() {
    // Send to analytics/backend
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

  // Show manual install instructions for browsers without prompt
  showManualInstructions() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);

    if (isIOS && isSafari) {
      const banner = document.createElement('div');
      banner.className = 'pwa-install-banner';
      banner.innerHTML = `
        <div class="pwa-install-content">
          <div class="pwa-install-icon">📱</div>
          <div class="pwa-install-text">
            <strong>ホーム画面に追加</strong>
            <p>Safari共有ボタン → 「ホーム画面に追加」をタップ</p>
          </div>
          <button class="cta ghost" onclick="this.parentElement.parentElement.remove()">OK</button>
        </div>
      `;
      document.body.appendChild(banner);
    }
  }
}

// CSS for install banner (inject if not present in styles.css)
if (!document.querySelector('style[data-pwa-install-styles]')) {
  const style = document.createElement('style');
  style.setAttribute('data-pwa-install-styles', 'true');
  style.textContent = `
    .pwa-install-banner {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: white;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      border-radius: 12px;
      padding: 16px 20px;
      z-index: 9999;
      max-width: 400px;
      width: 90%;
      animation: slideUp 0.3s ease-out;
    }

    @keyframes slideUp {
      from {
        transform: translate(-50%, 100%);
        opacity: 0;
      }
      to {
        transform: translate(-50%, 0);
        opacity: 1;
      }
    }

    .pwa-install-banner.fade-out {
      animation: fadeOut 0.3s ease-out forwards;
    }

    @keyframes fadeOut {
      to {
        opacity: 0;
        transform: translate(-50%, 20px);
      }
    }

    .pwa-install-content {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .pwa-install-icon {
      font-size: 32px;
    }

    .pwa-install-text {
      flex: 1;
      min-width: 150px;
    }

    .pwa-install-text strong {
      display: block;
      margin-bottom: 4px;
      color: #2f4b52;
    }

    .pwa-install-text p {
      margin: 0;
      font-size: 14px;
      color: #666;
    }

    @media (max-width: 600px) {
      .pwa-install-banner {
        bottom: 10px;
        left: 10px;
        right: 10px;
        width: auto;
        transform: none;
      }

      @keyframes slideUp {
        from {
          transform: translateY(100%);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }
    }
  `;
  document.head.appendChild(style);
}

// Initialize
if ('serviceWorker' in navigator) {
  window.installPromptManager = new InstallPromptManager();
}

// Export for manual usage
window.InstallPromptManager = InstallPromptManager;
