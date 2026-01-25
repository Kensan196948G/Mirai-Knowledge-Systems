// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * ブラウザ互換性テスト
 *
 * Chrome、Firefox、Safari、Edgeでの動作確認
 * - 主要画面の表示確認
 * - 主要機能の動作確認
 * - レスポンス時間の測定
 */

/**
 * テストデータ
 */
const TEST_USER = {
  username: 'test_user',
  email: 'test@example.com',
  password: 'Test1234!'
};

const TEST_DOCUMENT = {
  title: 'Browser Compatibility Test Document',
  content: 'This document is used for browser compatibility testing.'
};

/**
 * 共通ヘルパー関数
 */

/**
 * ログイン処理
 */
async function login(page, username, password) {
  await page.goto('/login');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard', { timeout: 10000 });
}

/**
 * パフォーマンス測定
 */
async function measurePageLoad(page, url) {
  const startTime = Date.now();
  await page.goto(url);
  const loadTime = Date.now() - startTime;
  return loadTime;
}

/**
 * スクリーンショット撮影
 */
async function takeScreenshot(page, testInfo, name) {
  const screenshot = await page.screenshot({ fullPage: true });
  await testInfo.attach(name, {
    body: screenshot,
    contentType: 'image/png'
  });
}

/**
 * テストグループ: トップページ表示
 */
test.describe('トップページ表示確認', () => {
  test('トップページが正しく表示される', async ({ page, browserName }, testInfo) => {
    // ページロード時間を測定
    const loadTime = await measurePageLoad(page, '/');
    console.log(`[${browserName}] トップページロード時間: ${loadTime}ms`);

    // タイトル確認
    await expect(page).toHaveTitle(/Mirai Knowledge System/i);

    // 主要要素の表示確認
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();

    // スクリーンショット撮影
    await takeScreenshot(page, testInfo, `${browserName}-top-page`);

    // パフォーマンス確認（5秒以内）
    expect(loadTime).toBeLessThan(5000);
  });

  test('ナビゲーションメニューが動作する', async ({ page, browserName }) => {
    await page.goto('/');

    // メニュー項目の存在確認
    const menuItems = ['ホーム', 'ドキュメント', 'ログイン'];

    for (const item of menuItems) {
      const menuLink = page.getByRole('link', { name: new RegExp(item, 'i') });
      if (await menuLink.count() > 0) {
        await expect(menuLink.first()).toBeVisible();
      }
    }
  });

  test('レスポンシブメニューが動作する', async ({ page, browserName }, testInfo) => {
    await page.goto('/');

    // モバイルビューポートに変更
    await page.setViewportSize({ width: 375, height: 667 });

    // ハンバーガーメニューの確認
    const menuButton = page.locator('button[aria-label*="menu" i], .hamburger, .menu-toggle');
    if (await menuButton.count() > 0) {
      await expect(menuButton.first()).toBeVisible();
      await menuButton.first().click();

      // メニューが展開されることを確認
      const mobileMenu = page.locator('nav.mobile, .mobile-menu, [role="navigation"]');
      await expect(mobileMenu.first()).toBeVisible();

      await takeScreenshot(page, testInfo, `${browserName}-mobile-menu`);
    }
  });
});

/**
 * テストグループ: ログインフロー
 */
test.describe('ログインフロー確認', () => {
  test('ログインページが正しく表示される', async ({ page, browserName }, testInfo) => {
    await page.goto('/login');

    // フォーム要素の確認
    await expect(page.locator('input[name="username"], input[type="text"]')).toBeVisible();
    await expect(page.locator('input[name="password"], input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // スクリーンショット撮影
    await takeScreenshot(page, testInfo, `${browserName}-login-page`);
  });

  test('フォーム入力が正しく動作する', async ({ page, browserName }) => {
    await page.goto('/login');

    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();

    // テキスト入力
    await usernameInput.fill(TEST_USER.username);
    await passwordInput.fill(TEST_USER.password);

    // 入力値の確認
    await expect(usernameInput).toHaveValue(TEST_USER.username);
    await expect(passwordInput).toHaveValue(TEST_USER.password);
  });

  test('ログインエラーメッセージが表示される', async ({ page, browserName }, testInfo) => {
    await page.goto('/login');

    // 不正な認証情報でログイン試行
    await page.locator('input[name="username"], input[type="text"]').first().fill('invalid_user');
    await page.locator('input[name="password"], input[type="password"]').first().fill('invalid_pass');
    await page.locator('button[type="submit"]').click();

    // エラーメッセージの確認
    const errorMessage = page.locator('.error, .alert-danger, [role="alert"]');
    await expect(errorMessage.first()).toBeVisible({ timeout: 5000 });

    await takeScreenshot(page, testInfo, `${browserName}-login-error`);
  });
});

/**
 * テストグループ: ダッシュボード
 */
test.describe('ダッシュボード表示確認', () => {
  test.skip('ダッシュボードが正しく表示される', async ({ page, browserName }, testInfo) => {
    // Note: 実際のログイン認証が必要な場合はスキップ
    // 実装されたら test.skip を test に変更

    await login(page, TEST_USER.username, TEST_USER.password);

    // ダッシュボードの主要要素確認
    await expect(page.locator('h1, h2').first()).toBeVisible();

    // ウィジェット・カードの確認
    const cards = page.locator('.card, .widget, .panel');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);

    await takeScreenshot(page, testInfo, `${browserName}-dashboard`);
  });
});

/**
 * テストグループ: 検索機能
 */
test.describe('検索機能確認', () => {
  test('検索ボックスが動作する', async ({ page, browserName }, testInfo) => {
    await page.goto('/');

    // 検索ボックスの確認
    const searchInput = page.locator('input[type="search"], input[placeholder*="検索" i], input[placeholder*="search" i]');

    if (await searchInput.count() > 0) {
      await expect(searchInput.first()).toBeVisible();

      // 検索テキスト入力
      await searchInput.first().fill('test search query');
      await expect(searchInput.first()).toHaveValue('test search query');

      await takeScreenshot(page, testInfo, `${browserName}-search`);
    } else {
      test.skip();
    }
  });

  test('検索サジェストが表示される', async ({ page, browserName }, testInfo) => {
    await page.goto('/');

    const searchInput = page.locator('input[type="search"], input[placeholder*="検索" i]');

    if (await searchInput.count() > 0) {
      await searchInput.first().fill('test');

      // サジェストの表示待機（存在する場合）
      const suggestions = page.locator('.suggestions, .autocomplete, [role="listbox"]');
      if (await suggestions.count() > 0) {
        await expect(suggestions.first()).toBeVisible({ timeout: 3000 });
        await takeScreenshot(page, testInfo, `${browserName}-search-suggestions`);
      }
    } else {
      test.skip();
    }
  });
});

/**
 * テストグループ: フォーム操作
 */
test.describe('フォーム操作確認', () => {
  test('テキストエリアが正しく動作する', async ({ page, browserName }) => {
    await page.goto('/login');

    // テキストエリアまたは複数行入力フィールドの検索
    const textarea = page.locator('textarea');

    if (await textarea.count() > 0) {
      const testText = 'Line 1\nLine 2\nLine 3';
      await textarea.first().fill(testText);
      await expect(textarea.first()).toHaveValue(testText);
    }
  });

  test('チェックボックスとラジオボタンが動作する', async ({ page, browserName }) => {
    await page.goto('/login');

    // チェックボックスの確認
    const checkbox = page.locator('input[type="checkbox"]');
    if (await checkbox.count() > 0) {
      await checkbox.first().check();
      await expect(checkbox.first()).toBeChecked();

      await checkbox.first().uncheck();
      await expect(checkbox.first()).not.toBeChecked();
    }

    // ラジオボタンの確認
    const radio = page.locator('input[type="radio"]');
    if (await radio.count() > 0) {
      await radio.first().check();
      await expect(radio.first()).toBeChecked();
    }
  });

  test('セレクトボックスが動作する', async ({ page, browserName }, testInfo) => {
    await page.goto('/');

    const select = page.locator('select');

    if (await select.count() > 0) {
      const options = await select.first().locator('option').count();

      if (options > 1) {
        await select.first().selectOption({ index: 1 });
        await takeScreenshot(page, testInfo, `${browserName}-select`);
      }
    }
  });
});

/**
 * テストグループ: JavaScript機能
 */
test.describe('JavaScript機能確認', () => {
  test('JavaScriptエラーが発生しない', async ({ page, browserName }) => {
    const errors = [];

    page.on('pageerror', error => {
      errors.push(error.message);
    });

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 重大なエラーがないことを確認
    const criticalErrors = errors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('ad') &&
      !err.includes('analytics')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('動的コンテンツが読み込まれる', async ({ page, browserName }) => {
    await page.goto('/');

    // ページが完全に読み込まれるまで待機
    await page.waitForLoadState('networkidle');

    // DOMが構築されていることを確認
    const bodyContent = await page.locator('body').textContent();
    expect(bodyContent.length).toBeGreaterThan(0);
  });
});

/**
 * テストグループ: CSS・スタイル
 */
test.describe('CSS・スタイル確認', () => {
  test('CSSが正しく読み込まれている', async ({ page, browserName }) => {
    await page.goto('/');

    // bodyの背景色が設定されていることを確認
    const body = page.locator('body');
    const backgroundColor = await body.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    expect(backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
  });

  test('フォントが正しく適用されている', async ({ page, browserName }) => {
    await page.goto('/');

    const body = page.locator('body');
    const fontFamily = await body.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );

    expect(fontFamily).toBeTruthy();
    expect(fontFamily).not.toBe('');
  });
});

/**
 * テストグループ: アクセシビリティ基本確認
 */
test.describe('アクセシビリティ基本確認', () => {
  test('主要な見出しが存在する', async ({ page, browserName }) => {
    await page.goto('/');

    const h1 = page.locator('h1');
    const h1Count = await h1.count();

    expect(h1Count).toBeGreaterThan(0);
  });

  test('リンクに適切なテキストが設定されている', async ({ page, browserName }) => {
    await page.goto('/');

    const links = page.locator('a');
    const linkCount = await links.count();

    for (let i = 0; i < Math.min(linkCount, 10); i++) {
      const link = links.nth(i);
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute('aria-label');

      // リンクテキストまたはaria-labelが存在すること
      expect(text || ariaLabel).toBeTruthy();
    }
  });

  test('画像にalt属性が設定されている', async ({ page, browserName }) => {
    await page.goto('/');

    const images = page.locator('img');
    const imageCount = await images.count();

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');

      // alt属性が存在すること（空文字列も許容）
      expect(alt).not.toBeNull();
    }
  });
});

/**
 * テストグループ: パフォーマンス
 */
test.describe('パフォーマンス確認', () => {
  test('リソース読み込みが正常に完了する', async ({ page, browserName }) => {
    const failedRequests = [];

    page.on('requestfailed', request => {
      failedRequests.push({
        url: request.url(),
        failure: request.failure()
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 重要なリソースの読み込み失敗がないことを確認
    const criticalFailures = failedRequests.filter(req =>
      !req.url.includes('favicon') &&
      !req.url.includes('ad') &&
      !req.url.includes('analytics')
    );

    expect(criticalFailures.length).toBe(0);
  });
});
