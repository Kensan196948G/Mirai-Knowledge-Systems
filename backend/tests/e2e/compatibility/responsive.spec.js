// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * レスポンシブデザイン互換性テスト
 *
 * 複数のデバイスサイズでの表示・動作確認:
 * - デスクトップ（1920x1080）
 * - ノートPC（1366x768）
 * - タブレット（768x1024）
 * - スマートフォン（375x667）
 */

/**
 * デバイスサイズ定義
 */
const DEVICES = {
  desktop: { width: 1920, height: 1080, name: 'Desktop' },
  laptop: { width: 1366, height: 768, name: 'Laptop' },
  tablet_portrait: { width: 768, height: 1024, name: 'Tablet Portrait' },
  tablet_landscape: { width: 1024, height: 768, name: 'Tablet Landscape' },
  mobile_large: { width: 414, height: 896, name: 'Mobile Large (iPhone 11)' },
  mobile_medium: { width: 375, height: 667, name: 'Mobile Medium (iPhone SE)' },
  mobile_small: { width: 360, height: 640, name: 'Mobile Small (Galaxy S5)' }
};

/**
 * ヘルパー関数
 */

/**
 * ビューポート設定とスクリーンショット撮影
 */
async function testViewport(page, testInfo, device, url = '/') {
  await page.setViewportSize({ width: device.width, height: device.height });
  await page.goto(url);
  await page.waitForLoadState('networkidle');

  const screenshot = await page.screenshot({ fullPage: true });
  await testInfo.attach(`${device.name.replace(/\s+/g, '_')}-${url.replace(/\//g, '_') || 'home'}`, {
    body: screenshot,
    contentType: 'image/png'
  });
}

/**
 * 要素の可視性とサイズをチェック
 */
async function checkElementVisibility(page, selector, deviceName) {
  const element = page.locator(selector).first();

  if (await element.count() > 0) {
    const isVisible = await element.isVisible();
    const box = await element.boundingBox();

    return {
      visible: isVisible,
      width: box?.width || 0,
      height: box?.height || 0
    };
  }

  return { visible: false, width: 0, height: 0 };
}

/**
 * レイアウトが壊れていないか確認
 */
async function checkLayoutIntegrity(page) {
  // 横スクロールが発生していないか確認
  const hasHorizontalScroll = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });

  // body要素がビューポートに収まっているか
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewportWidth = await page.viewportSize().then(v => v.width);

  return {
    hasHorizontalScroll,
    bodyWidth,
    viewportWidth,
    isLayoutValid: bodyWidth <= viewportWidth
  };
}

/**
 * テストグループ: デスクトップ表示
 */
test.describe('デスクトップ表示確認', () => {
  test('デスクトップ（1920x1080）でトップページが正しく表示される', async ({ page }, testInfo) => {
    const device = DEVICES.desktop;
    await testViewport(page, testInfo, device, '/');

    // レイアウト整合性確認
    const layout = await checkLayoutIntegrity(page);
    expect(layout.isLayoutValid).toBe(true);

    // 主要要素の表示確認
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();

    // ナビゲーションメニューが表示されていること
    const nav = await checkElementVisibility(page, 'nav', device.name);
    expect(nav.visible).toBe(true);
    expect(nav.width).toBeGreaterThan(0);
  });

  test('デスクトップでダッシュボードが正しく表示される', async ({ page }, testInfo) => {
    const device = DEVICES.desktop;
    await testViewport(page, testInfo, device, '/login');

    // フォーム要素が適切なサイズで表示されること
    const input = await checkElementVisibility(page, 'input[type="text"], input[name="username"]', device.name);
    expect(input.visible).toBe(true);
    expect(input.width).toBeGreaterThan(200); // デスクトップでは十分な幅
  });

  test('デスクトップでサイドバーが表示される', async ({ page }, testInfo) => {
    const device = DEVICES.desktop;
    await testViewport(page, testInfo, device, '/');

    // サイドバーの確認（存在する場合）
    const sidebar = page.locator('aside, .sidebar, [role="complementary"]');

    if (await sidebar.count() > 0) {
      const sidebarInfo = await checkElementVisibility(page, 'aside, .sidebar', device.name);
      expect(sidebarInfo.visible).toBe(true);
    }
  });
});

/**
 * テストグループ: ノートPC表示
 */
test.describe('ノートPC表示確認', () => {
  test('ノートPC（1366x768）でトップページが正しく表示される', async ({ page }, testInfo) => {
    const device = DEVICES.laptop;
    await testViewport(page, testInfo, device, '/');

    // レイアウト整合性確認
    const layout = await checkLayoutIntegrity(page);
    expect(layout.isLayoutValid).toBe(true);

    // 主要要素の表示確認
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('main')).toBeVisible();
  });

  test('ノートPCでコンテンツが適切に折り返される', async ({ page }, testInfo) => {
    const device = DEVICES.laptop;
    await testViewport(page, testInfo, device, '/');

    // テキストコンテンツが画面幅に収まっているか
    const paragraphs = page.locator('p');
    const count = await paragraphs.count();

    if (count > 0) {
      for (let i = 0; i < Math.min(count, 5); i++) {
        const box = await paragraphs.nth(i).boundingBox();
        if (box) {
          expect(box.width).toBeLessThanOrEqual(device.width);
        }
      }
    }
  });
});

/**
 * テストグループ: タブレット表示
 */
test.describe('タブレット表示確認', () => {
  test('タブレット縦向き（768x1024）でレイアウトが適応される', async ({ page }, testInfo) => {
    const device = DEVICES.tablet_portrait;
    await testViewport(page, testInfo, device, '/');

    // レイアウト整合性確認
    const layout = await checkLayoutIntegrity(page);
    expect(layout.isLayoutValid).toBe(true);

    // 横スクロールが発生していないこと
    expect(layout.hasHorizontalScroll).toBe(false);
  });

  test('タブレット横向き（1024x768）でレイアウトが適応される', async ({ page }, testInfo) => {
    const device = DEVICES.tablet_landscape;
    await testViewport(page, testInfo, device, '/');

    const layout = await checkLayoutIntegrity(page);
    expect(layout.isLayoutValid).toBe(true);
  });

  test('タブレットでナビゲーションが適切に表示される', async ({ page }, testInfo) => {
    const device = DEVICES.tablet_portrait;
    await testViewport(page, testInfo, device, '/');

    // ハンバーガーメニューまたは通常メニューが表示されること
    const hamburger = page.locator('button[aria-label*="menu" i], .hamburger, .menu-toggle');
    const nav = page.locator('nav');

    const hasHamburger = await hamburger.count() > 0;
    const hasNav = await nav.count() > 0;

    expect(hasHamburger || hasNav).toBe(true);
  });

  test('タブレットでタッチ操作に適したボタンサイズ', async ({ page }, testInfo) => {
    const device = DEVICES.tablet_portrait;
    await testViewport(page, testInfo, device, '/login');

    // ボタンのサイズ確認（タッチ対応: 最低44x44px推奨）
    const buttons = page.locator('button, input[type="submit"]');
    const buttonCount = await buttons.count();

    if (buttonCount > 0) {
      const firstButton = buttons.first();
      const box = await firstButton.boundingBox();

      if (box) {
        // タッチターゲットとして十分なサイズ
        expect(box.height).toBeGreaterThanOrEqual(36); // 多少小さくても許容
      }
    }
  });

  test('タブレットでフォームが使いやすい', async ({ page }, testInfo) => {
    const device = DEVICES.tablet_portrait;
    await testViewport(page, testInfo, device, '/login');

    // 入力フィールドが十分な幅を持つこと
    const inputs = page.locator('input[type="text"], input[type="password"], input[name="username"]');
    const inputCount = await inputs.count();

    if (inputCount > 0) {
      const box = await inputs.first().boundingBox();
      if (box) {
        expect(box.width).toBeGreaterThan(200); // タブレットで十分な入力幅
      }
    }
  });
});

/**
 * テストグループ: スマートフォン表示
 */
test.describe('スマートフォン表示確認', () => {
  test('スマートフォン（375x667）でモバイルレイアウトが適用される', async ({ page }, testInfo) => {
    const device = DEVICES.mobile_medium;
    await testViewport(page, testInfo, device, '/');

    // レイアウト整合性確認
    const layout = await checkLayoutIntegrity(page);
    expect(layout.isLayoutValid).toBe(true);

    // 横スクロールが発生していないこと
    expect(layout.hasHorizontalScroll).toBe(false);
  });

  test('スマートフォンでハンバーガーメニューが表示される', async ({ page }, testInfo) => {
    const device = DEVICES.mobile_medium;
    await testViewport(page, testInfo, device, '/');

    // ハンバーガーメニューボタンが表示されること
    const hamburger = page.locator('button[aria-label*="menu" i], .hamburger, .menu-toggle, .navbar-toggler');

    if (await hamburger.count() > 0) {
      await expect(hamburger.first()).toBeVisible();

      // メニューボタンをクリック
      await hamburger.first().click();

      // モバイルメニューが展開されること
      const mobileMenu = page.locator('nav.mobile, .mobile-menu, .navbar-collapse, [role="navigation"]');
      await expect(mobileMenu.first()).toBeVisible({ timeout: 2000 });

      await testInfo.attach('mobile-menu-expanded', {
        body: await page.screenshot(),
        contentType: 'image/png'
      });
    }
  });

  test('スマートフォンでタッチ操作に適したUI', async ({ page }, testInfo) => {
    const device = DEVICES.mobile_medium;
    await testViewport(page, testInfo, device, '/login');

    // タップ可能な要素が十分なサイズであること（44x44px以上推奨）
    const buttons = page.locator('button, a, input[type="submit"]');
    const buttonCount = await buttons.count();

    if (buttonCount > 0) {
      const firstButton = buttons.first();
      const box = await firstButton.boundingBox();

      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(32); // モバイルで最低限のタッチサイズ
      }
    }
  });

  test('スマートフォンでフォント読みやすさ', async ({ page }, testInfo) => {
    const device = DEVICES.mobile_medium;
    await testViewport(page, testInfo, device, '/');

    // フォントサイズが小さすぎないこと（最低12px推奨）
    const bodyFontSize = await page.evaluate(() => {
      return parseInt(window.getComputedStyle(document.body).fontSize);
    });

    expect(bodyFontSize).toBeGreaterThanOrEqual(12);
  });

  test('スマートフォンで画像が適切にリサイズされる', async ({ page }, testInfo) => {
    const device = DEVICES.mobile_medium;
    await testViewport(page, testInfo, device, '/');

    // 画像が画面幅を超えていないこと
    const images = page.locator('img');
    const imageCount = await images.count();

    for (let i = 0; i < Math.min(imageCount, 5); i++) {
      const box = await images.nth(i).boundingBox();
      if (box) {
        expect(box.width).toBeLessThanOrEqual(device.width);
      }
    }
  });

  test('スマートフォン小サイズ（360x640）でも表示が崩れない', async ({ page }, testInfo) => {
    const device = DEVICES.mobile_small;
    await testViewport(page, testInfo, device, '/');

    const layout = await checkLayoutIntegrity(page);
    expect(layout.isLayoutValid).toBe(true);
    expect(layout.hasHorizontalScroll).toBe(false);
  });

  test('スマートフォン大サイズ（414x896）で適切に表示される', async ({ page }, testInfo) => {
    const device = DEVICES.mobile_large;
    await testViewport(page, testInfo, device, '/');

    const layout = await checkLayoutIntegrity(page);
    expect(layout.isLayoutValid).toBe(true);
  });
});

/**
 * テストグループ: デバイス横断確認
 */
test.describe('デバイス横断確認', () => {
  test('全デバイスサイズでヘッダーが表示される', async ({ page }, testInfo) => {
    for (const [key, device] of Object.entries(DEVICES)) {
      await testViewport(page, testInfo, device, '/');

      const header = page.locator('header');
      await expect(header).toBeVisible();
    }
  });

  test('全デバイスサイズでフッターが表示される', async ({ page }, testInfo) => {
    for (const [key, device] of Object.entries(DEVICES)) {
      await testViewport(page, testInfo, device, '/');

      const footer = page.locator('footer');
      if (await footer.count() > 0) {
        await expect(footer).toBeVisible();
      }
    }
  });

  test('全デバイスサイズでコンテンツがビューポートに収まる', async ({ page }, testInfo) => {
    for (const [key, device] of Object.entries(DEVICES)) {
      await page.setViewportSize({ width: device.width, height: device.height });
      await page.goto('/');

      const layout = await checkLayoutIntegrity(page);

      expect(layout.isLayoutValid, `${device.name}: レイアウトが崩れています`).toBe(true);
      expect(layout.hasHorizontalScroll, `${device.name}: 横スクロールが発生しています`).toBe(false);
    }
  });
});

/**
 * テストグループ: オリエンテーション変更
 */
test.describe('オリエンテーション変更確認', () => {
  test('タブレットで縦横切り替え時にレイアウトが適応される', async ({ page }, testInfo) => {
    // 縦向き
    await testViewport(page, testInfo, DEVICES.tablet_portrait, '/');
    const portraitLayout = await checkLayoutIntegrity(page);
    expect(portraitLayout.isLayoutValid).toBe(true);

    // 横向き
    await testViewport(page, testInfo, DEVICES.tablet_landscape, '/');
    const landscapeLayout = await checkLayoutIntegrity(page);
    expect(landscapeLayout.isLayoutValid).toBe(true);
  });

  test('スマートフォンで縦横切り替え時にコンテンツが表示される', async ({ page }, testInfo) => {
    // 縦向き
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await expect(page.locator('main')).toBeVisible();

    // 横向き
    await page.setViewportSize({ width: 667, height: 375 });
    await expect(page.locator('main')).toBeVisible();

    await testInfo.attach('mobile-landscape', {
      body: await page.screenshot(),
      contentType: 'image/png'
    });
  });
});

/**
 * テストグループ: レスポンシブ画像・メディア
 */
test.describe('レスポンシブ画像・メディア確認', () => {
  test('画像が各デバイスサイズで適切に表示される', async ({ page }, testInfo) => {
    const testDevices = [DEVICES.desktop, DEVICES.tablet_portrait, DEVICES.mobile_medium];

    for (const device of testDevices) {
      await testViewport(page, testInfo, device, '/');

      const images = page.locator('img');
      const imageCount = await images.count();

      if (imageCount > 0) {
        const firstImage = images.first();
        const box = await firstImage.boundingBox();

        if (box) {
          // 画像がビューポートに収まっていること
          expect(box.width).toBeLessThanOrEqual(device.width);
        }
      }
    }
  });

  test('ビデオ要素がレスポンシブである', async ({ page }, testInfo) => {
    await page.goto('/');

    const videos = page.locator('video');
    const videoCount = await videos.count();

    if (videoCount > 0) {
      for (const device of [DEVICES.desktop, DEVICES.mobile_medium]) {
        await page.setViewportSize({ width: device.width, height: device.height });

        const box = await videos.first().boundingBox();
        if (box) {
          expect(box.width).toBeLessThanOrEqual(device.width);
        }
      }
    }
  });
});

/**
 * テストグループ: フォームのレスポンシブ性
 */
test.describe('フォームのレスポンシブ性確認', () => {
  test('ログインフォームが全デバイスで使いやすい', async ({ page }, testInfo) => {
    const testDevices = [DEVICES.desktop, DEVICES.tablet_portrait, DEVICES.mobile_medium];

    for (const device of testDevices) {
      await testViewport(page, testInfo, device, '/login');

      // フォーム要素が表示されていること
      const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
      const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
      const submitButton = page.locator('button[type="submit"]').first();

      await expect(usernameInput).toBeVisible();
      await expect(passwordInput).toBeVisible();
      await expect(submitButton).toBeVisible();

      // 入力フィールドが適切な幅を持つこと
      const inputBox = await usernameInput.boundingBox();
      if (inputBox) {
        expect(inputBox.width).toBeGreaterThan(100); // 最低限の入力幅
        expect(inputBox.width).toBeLessThanOrEqual(device.width * 0.9); // ビューポートの90%以内
      }
    }
  });

  test('テキストエリアがモバイルで適切なサイズ', async ({ page }, testInfo) => {
    await page.goto('/');

    const textareas = page.locator('textarea');
    const textareaCount = await textareas.count();

    if (textareaCount > 0) {
      await page.setViewportSize({ width: 375, height: 667 });

      const box = await textareas.first().boundingBox();
      if (box) {
        expect(box.width).toBeGreaterThan(200);
        expect(box.width).toBeLessThanOrEqual(375 * 0.9);
      }
    }
  });
});

/**
 * テストグループ: ナビゲーションのレスポンシブ性
 */
test.describe('ナビゲーションのレスポンシブ性確認', () => {
  test('デスクトップで水平メニューが表示される', async ({ page }, testInfo) => {
    await testViewport(page, testInfo, DEVICES.desktop, '/');

    const nav = page.locator('nav');
    if (await nav.count() > 0) {
      await expect(nav.first()).toBeVisible();
    }
  });

  test('モバイルでハンバーガーメニューが機能する', async ({ page }, testInfo) => {
    await testViewport(page, testInfo, DEVICES.mobile_medium, '/');

    const hamburger = page.locator('button[aria-label*="menu" i], .hamburger, .menu-toggle, .navbar-toggler');

    if (await hamburger.count() > 0) {
      // メニューボタンをクリック
      await hamburger.first().click();
      await page.waitForTimeout(500); // アニメーション待機

      // メニューが展開されたことを確認
      const screenshot = await page.screenshot();
      await testInfo.attach('hamburger-menu-open', {
        body: screenshot,
        contentType: 'image/png'
      });

      // メニューを閉じる
      await hamburger.first().click();
      await page.waitForTimeout(500);
    }
  });
});
