const { test, expect } = require('@playwright/test');

test.describe('Authentication Flow', () => {
  test('Login → Dashboard Flow', async ({ page }) => {
    // ログインページ表示
    await page.goto('/login.html');
    await expect(page).toHaveTitle(/ログイン/);

    // 認証情報入力
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');

    // ログイン
    await page.click('button[type="submit"]');

    // ダッシュボードリダイレクト確認
    await page.waitForURL('/index.html', { timeout: 5000 });
    await expect(page).toHaveURL('/index.html');

    // ユーザー情報表示確認
    await expect(page.locator('.user-info')).toContainText('Admin User');
  });

  test('Login Failure Handling', async ({ page }) => {
    // ログインページ表示
    await page.goto('/login.html');

    // 誤った認証情報入力
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'wrongpassword');

    // ログイン試行
    await page.click('button[type="submit"]');

    // エラーメッセージ確認（ページ留まり）
    await page.waitForTimeout(1000);
    await expect(page).toHaveURL('/login.html');
  });

  test('Logout Flow', async ({ page }) => {
    // ログイン
    await page.goto('/login.html');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/index.html');

    // ログアウト
    await page.click('.logout-btn');

    // ログインページリダイレクト
    await page.waitForURL('/login.html');
    await expect(page).toHaveURL('/login.html');

    // localStorage確認
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeNull();
  });
});
