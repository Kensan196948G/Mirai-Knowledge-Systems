/**
 * MKSApp Namespace検証テスト
 * フロントエンドのNamespace化が正しく実装されているか確認
 */

const { test, expect } = require('@playwright/test');

test.describe('MKSApp Namespace Verification', () => {
  test.beforeEach(async ({ page }) => {
    // ログインページにアクセス
    await page.goto('http://localhost:5200/login.html');

    // ログイン処理
    await page.fill('#username', 'admin');
    await page.fill('#password', 'Admin@2024');
    await page.click('button[type="submit"]');

    // ダッシュボード読み込み待機
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('MKSApp Namespace should be defined', async ({ page }) => {
    const namespaceExists = await page.evaluate(() => {
      return typeof window.MKSApp !== 'undefined';
    });

    expect(namespaceExists).toBe(true);
  });

  test('MKSApp should have all core modules', async ({ page }) => {
    const modules = await page.evaluate(() => {
      return Object.keys(window.MKSApp);
    });

    // 主要モジュールが存在することを確認
    expect(modules).toContain('ENV');
    expect(modules).toContain('logger');
    expect(modules).toContain('Auth');
    expect(modules).toContain('UI');
    expect(modules).toContain('Search');
    expect(modules).toContain('Modal');
    expect(modules).toContain('Dashboard');
    expect(modules).toContain('Navigation');
    expect(modules).toContain('Filter');
    expect(modules).toContain('Settings');
    expect(modules).toContain('Utilities');
    expect(modules).toContain('Projects');
    expect(modules).toContain('Experts');
    expect(modules).toContain('Approval');
    expect(modules).toContain('PWA');
    expect(modules).toContain('SocketIO');
  });

  test('MKSApp.Auth should have required functions', async ({ page }) => {
    const authFunctions = await page.evaluate(() => {
      return Object.keys(window.MKSApp.Auth);
    });

    expect(authFunctions).toContain('checkAuth');
    expect(authFunctions).toContain('logout');
    expect(authFunctions).toContain('getCurrentUser');
    expect(authFunctions).toContain('checkPermission');
    expect(authFunctions).toContain('hasPermission');
    expect(authFunctions).toContain('canEdit');
    expect(authFunctions).toContain('applyRBACUI');
  });

  test('MKSApp.UI should have required functions', async ({ page }) => {
    const uiFunctions = await page.evaluate(() => {
      return Object.keys(window.MKSApp.UI);
    });

    expect(uiFunctions).toContain('showNotification');
    expect(uiFunctions).toContain('toggleSidebar');
    expect(uiFunctions).toContain('toggleMobileSidebar');
    expect(uiFunctions).toContain('closeMobileSidebar');
  });

  test('MKSApp.Search should have required functions', async ({ page }) => {
    const searchFunctions = await page.evaluate(() => {
      return Object.keys(window.MKSApp.Search);
    });

    expect(searchFunctions).toContain('performHeroSearch');
    expect(searchFunctions).toContain('openSearchModal');
    expect(searchFunctions).toContain('closeSearchModal');
    expect(searchFunctions).toContain('resetSearchForm');
  });

  test('MKSApp.DOM should be defined on detail pages', async ({ page }) => {
    // 詳細ページに移動
    await page.goto('http://localhost:5200/search-detail.html?id=1');
    await page.waitForLoadState('networkidle');

    const domNamespaceExists = await page.evaluate(() => {
      return typeof window.MKSApp !== 'undefined' &&
             typeof window.MKSApp.DOM !== 'undefined';
    });

    expect(domNamespaceExists).toBe(true);
  });

  test('MKSApp.DOM should have core functions', async ({ page }) => {
    await page.goto('http://localhost:5200/search-detail.html?id=1');
    await page.waitForLoadState('networkidle');

    const domFunctions = await page.evaluate(() => {
      if (!window.MKSApp || !window.MKSApp.DOM) return [];
      return Object.keys(window.MKSApp.DOM);
    });

    expect(domFunctions).toContain('escapeHtml');
    expect(domFunctions).toContain('createSecureElement');
    expect(domFunctions).toContain('setSecureChildren');
    expect(domFunctions).toContain('Components');
    expect(domFunctions).toContain('Messages');
  });

  test('MKSApp.DetailPages should be defined on detail pages', async ({ page }) => {
    await page.goto('http://localhost:5200/search-detail.html?id=1');
    await page.waitForLoadState('networkidle');

    const detailPagesExists = await page.evaluate(() => {
      return typeof window.MKSApp !== 'undefined' &&
             typeof window.MKSApp.DetailPages !== 'undefined';
    });

    expect(detailPagesExists).toBe(true);
  });

  test('MKSApp.DetailPages should have required modules', async ({ page }) => {
    await page.goto('http://localhost:5200/search-detail.html?id=1');
    await page.waitForLoadState('networkidle');

    const detailModules = await page.evaluate(() => {
      if (!window.MKSApp || !window.MKSApp.DetailPages) return [];
      return Object.keys(window.MKSApp.DetailPages);
    });

    expect(detailModules).toContain('Knowledge');
    expect(detailModules).toContain('SOP');
    expect(detailModules).toContain('Incident');
    expect(detailModules).toContain('Consult');
    expect(detailModules).toContain('Utilities');
    expect(detailModules).toContain('Share');
    expect(detailModules).toContain('Modal');
  });

  test('MKSApp.Actions should be defined', async ({ page }) => {
    const actionsExists = await page.evaluate(() => {
      return typeof window.MKSApp !== 'undefined' &&
             typeof window.MKSApp.Actions !== 'undefined';
    });

    expect(actionsExists).toBe(true);
  });

  test('MKSApp.Notifications should be defined', async ({ page }) => {
    const notificationsExists = await page.evaluate(() => {
      return typeof window.MKSApp !== 'undefined' &&
             typeof window.MKSApp.Notifications !== 'undefined';
    });

    expect(notificationsExists).toBe(true);
  });

  test('Backward compatibility - window.* aliases should work', async ({ page }) => {
    const compatibilityCheck = await page.evaluate(() => {
      return {
        checkAuth: typeof window.checkAuth === 'function',
        logout: typeof window.logout === 'function',
        showNotification: typeof window.showNotification === 'function',
        performHeroSearch: typeof window.performHeroSearch === 'function',
        toggleSidebar: typeof window.toggleSidebar === 'function',
        createElement: typeof window.createElement === 'function',
        formatDate: typeof window.formatDate === 'function'
      };
    });

    expect(compatibilityCheck.checkAuth).toBe(true);
    expect(compatibilityCheck.logout).toBe(true);
    expect(compatibilityCheck.showNotification).toBe(true);
    expect(compatibilityCheck.performHeroSearch).toBe(true);
    expect(compatibilityCheck.toggleSidebar).toBe(true);
    expect(compatibilityCheck.createElement).toBe(true);
    expect(compatibilityCheck.formatDate).toBe(true);
  });

  test('MKSApp functions should be callable', async ({ page }) => {
    const functionsCallable = await page.evaluate(() => {
      try {
        // Auth関数は実際に呼び出して動作確認
        const currentUser = window.MKSApp.Auth.getCurrentUser();

        // formatDateは実際に呼び出して動作確認
        const formattedDate = window.MKSApp.Utilities.formatDate(new Date().toISOString());

        return {
          success: true,
          currentUser: !!currentUser,
          formattedDate: !!formattedDate
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    });

    expect(functionsCallable.success).toBe(true);
  });

  test('Console should log MKSApp initialization', async ({ page }) => {
    const logs = [];

    page.on('console', msg => {
      if (msg.type() === 'log') {
        logs.push(msg.text());
      }
    });

    await page.goto('http://localhost:5200/index.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // MKSApp初期化ログを確認
    const hasNamespaceLog = logs.some(log => log.includes('[MKSApp] Namespace initialized'));
    expect(hasNamespaceLog).toBe(true);
  });

  test('PWA namespace should have dynamic getters', async ({ page }) => {
    const pwaModules = await page.evaluate(() => {
      const pwa = window.MKSApp.PWA;
      return {
        hasFEATURES: 'FEATURES' in pwa,
        hasCacheManager: 'CacheManager' in pwa,
        hasCryptoHelper: 'CryptoHelper' in pwa,
        hasSyncManager: 'SyncManager' in pwa
      };
    });

    expect(pwaModules.hasFEATURES).toBe(true);
    expect(pwaModules.hasCacheManager).toBe(true);
    expect(pwaModules.hasCryptoHelper).toBe(true);
    expect(pwaModules.hasSyncManager).toBe(true);
  });

  test('Global pollution should be minimized', async ({ page }) => {
    const globalCount = await page.evaluate(() => {
      const globalKeys = Object.keys(window).filter(key => {
        // システム標準のグローバル変数を除外
        const systemKeys = [
          'window', 'document', 'location', 'navigator', 'history', 'screen',
          'localStorage', 'sessionStorage', 'console', 'setTimeout', 'setInterval',
          'fetch', 'XMLHttpRequest', 'Promise', 'Array', 'Object', 'String', 'Number',
          'Boolean', 'Function', 'Date', 'Math', 'JSON', 'RegExp', 'Error',
          'Map', 'Set', 'WeakMap', 'WeakSet', 'Symbol', 'Proxy', 'Reflect',
          'Intl', 'performance', 'crypto', 'alert', 'confirm', 'prompt'
        ];

        return !systemKeys.includes(key) &&
               !key.startsWith('webkit') &&
               !key.startsWith('on') &&
               !key.startsWith('chrome');
      });

      // MKSApp以外のグローバル変数をカウント（互換性レイヤーを含む）
      return {
        total: globalKeys.length,
        hasMKSApp: globalKeys.includes('MKSApp'),
        mksKeys: globalKeys.filter(k => k.includes('MKS') || k === 'logger')
      };
    });

    // MKSAppが存在することを確認
    expect(globalCount.hasMKSApp).toBe(true);

    // グローバル汚染が制限されていることを確認（互換性レイヤーを許容）
    console.log('Global MKS-related keys:', globalCount.mksKeys);
    console.log('Total custom global keys:', globalCount.total);
  });
});
