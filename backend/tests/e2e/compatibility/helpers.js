// @ts-check

/**
 * E2Eテスト用ヘルパー関数
 *
 * 共通で使用される機能をまとめたユーティリティ
 */

/**
 * ページロード時間を測定
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} url
 * @returns {Promise<number>} ロード時間（ミリ秒）
 */
async function measurePageLoad(page, url) {
  const startTime = Date.now();
  await page.goto(url);
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - startTime;
  return loadTime;
}

/**
 * スクリーンショットを撮影し、テストレポートに添付
 *
 * @param {import('@playwright/test').Page} page
 * @param {import('@playwright/test').TestInfo} testInfo
 * @param {string} name
 * @param {boolean} fullPage
 */
async function takeScreenshot(page, testInfo, name, fullPage = true) {
  const screenshot = await page.screenshot({ fullPage });
  await testInfo.attach(name, {
    body: screenshot,
    contentType: 'image/png'
  });
}

/**
 * 要素の可視性と位置情報を取得
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} selector
 * @returns {Promise<{visible: boolean, box: {x: number, y: number, width: number, height: number} | null}>}
 */
async function getElementInfo(page, selector) {
  const element = page.locator(selector).first();
  const count = await element.count();

  if (count === 0) {
    return { visible: false, box: null };
  }

  const isVisible = await element.isVisible();
  const box = await element.boundingBox();

  return {
    visible: isVisible,
    box: box ? { x: box.x, y: box.y, width: box.width, height: box.height } : null
  };
}

/**
 * レイアウトの整合性をチェック
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<{hasHorizontalScroll: boolean, bodyWidth: number, viewportWidth: number, isValid: boolean}>}
 */
async function checkLayoutIntegrity(page) {
  const hasHorizontalScroll = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });

  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewport = page.viewportSize();
  const viewportWidth = viewport ? viewport.width : 0;

  return {
    hasHorizontalScroll,
    bodyWidth,
    viewportWidth,
    isValid: !hasHorizontalScroll && bodyWidth <= viewportWidth
  };
}

/**
 * コンソールエラーを収集
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<string[]>} エラーメッセージの配列
 */
async function collectConsoleErrors(page) {
  const errors = [];

  page.on('pageerror', error => {
    errors.push(error.message);
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  return errors;
}

/**
 * ネットワークリクエストの失敗を収集
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Array<{url: string, failure: string}>}
 */
function collectFailedRequests(page) {
  const failedRequests = [];

  page.on('requestfailed', request => {
    failedRequests.push({
      url: request.url(),
      failure: request.failure()?.errorText || 'Unknown error'
    });
  });

  return failedRequests;
}

/**
 * パフォーマンスメトリクスを取得
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<{domContentLoaded: number, loadComplete: number, firstPaint: number, firstContentfulPaint: number}>}
 */
async function getPerformanceMetrics(page) {
  return await page.evaluate(() => {
    const navigation = performance.getEntriesByType('navigation')[0];
    const paint = performance.getEntriesByType('paint');

    const firstPaint = paint.find(entry => entry.name === 'first-paint');
    const firstContentfulPaint = paint.find(entry => entry.name === 'first-contentful-paint');

    return {
      domContentLoaded: navigation?.domContentLoadedEventEnd || 0,
      loadComplete: navigation?.loadEventEnd || 0,
      firstPaint: firstPaint?.startTime || 0,
      firstContentfulPaint: firstContentfulPaint?.startTime || 0
    };
  });
}

/**
 * ログイン処理（認証が必要なテスト用）
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} username
 * @param {string} password
 */
async function login(page, username, password) {
  await page.goto('/login');

  const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
  const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
  const submitButton = page.locator('button[type="submit"]').first();

  await usernameInput.fill(username);
  await passwordInput.fill(password);
  await submitButton.click();

  await page.waitForURL('/dashboard', { timeout: 10000 });
}

/**
 * ビューポートサイズを設定
 *
 * @param {import('@playwright/test').Page} page
 * @param {number} width
 * @param {number} height
 */
async function setViewport(page, width, height) {
  await page.setViewportSize({ width, height });
}

/**
 * スクロール操作
 *
 * @param {import('@playwright/test').Page} page
 * @param {number} x
 * @param {number} y
 */
async function scrollTo(page, x, y) {
  await page.evaluate(({ x, y }) => {
    window.scrollTo(x, y);
  }, { x, y });
}

/**
 * 要素までスクロール
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} selector
 */
async function scrollToElement(page, selector) {
  const element = page.locator(selector).first();
  await element.scrollIntoViewIfNeeded();
}

/**
 * 待機（デバッグ用）
 *
 * @param {number} ms
 */
async function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * CSSプロパティを取得
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} selector
 * @param {string} property
 * @returns {Promise<string>}
 */
async function getCSSProperty(page, selector, property) {
  const element = page.locator(selector).first();
  return await element.evaluate((el, prop) => {
    return window.getComputedStyle(el).getPropertyValue(prop);
  }, property);
}

/**
 * モバイルデバイスかどうかを判定
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<boolean>}
 */
async function isMobileViewport(page) {
  const viewport = page.viewportSize();
  return viewport ? viewport.width < 768 : false;
}

/**
 * タブレットデバイスかどうかを判定
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<boolean>}
 */
async function isTabletViewport(page) {
  const viewport = page.viewportSize();
  return viewport ? viewport.width >= 768 && viewport.width < 1024 : false;
}

/**
 * デスクトップビューかどうかを判定
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<boolean>}
 */
async function isDesktopViewport(page) {
  const viewport = page.viewportSize();
  return viewport ? viewport.width >= 1024 : false;
}

/**
 * アクセシビリティ違反をチェック（基本的なチェック）
 *
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<string[]>} 違反のリスト
 */
async function checkBasicAccessibility(page) {
  const violations = [];

  // 画像のalt属性チェック
  const imagesWithoutAlt = await page.locator('img:not([alt])').count();
  if (imagesWithoutAlt > 0) {
    violations.push(`${imagesWithoutAlt} images without alt attribute`);
  }

  // リンクテキストチェック
  const emptyLinks = await page.locator('a:not([aria-label])').evaluateAll(links => {
    return links.filter(link => !link.textContent?.trim()).length;
  });
  if (emptyLinks > 0) {
    violations.push(`${emptyLinks} links without text or aria-label`);
  }

  // フォームラベルチェック
  const inputsWithoutLabel = await page.locator('input:not([type="hidden"]):not([aria-label])').evaluateAll(inputs => {
    return inputs.filter(input => {
      const id = input.id;
      if (!id) return true;
      const label = document.querySelector(`label[for="${id}"]`);
      return !label;
    }).length;
  });
  if (inputsWithoutLabel > 0) {
    violations.push(`${inputsWithoutLabel} inputs without associated label`);
  }

  return violations;
}

module.exports = {
  measurePageLoad,
  takeScreenshot,
  getElementInfo,
  checkLayoutIntegrity,
  collectConsoleErrors,
  collectFailedRequests,
  getPerformanceMetrics,
  login,
  setViewport,
  scrollTo,
  scrollToElement,
  wait,
  getCSSProperty,
  isMobileViewport,
  isTabletViewport,
  isDesktopViewport,
  checkBasicAccessibility
};
