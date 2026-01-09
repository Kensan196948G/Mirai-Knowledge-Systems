import { test, expect } from '@playwright/test';

test('login flow', async ({ page }) => {
  // ログインページに移動
  await page.goto('/login.html');

  // ログイン情報を入力
  await page.fill('#username', 'admin');
  await page.fill('#password', 'admin123');

  // ログインボタンをクリック
  await page.click('#login-button');

  // ダッシュボードにリダイレクトされることを確認
  await expect(page).toHaveURL(/.*index\.html/);

  // ログアウトボタンが表示されていることを確認
  await expect(page.locator('#logout-button')).toBeVisible();
});

test('login with invalid credentials', async ({ page }) => {
  // ログインページに移動
  await page.goto('/login.html');

  // 無効なログイン情報を入力
  await page.fill('#username', 'invalid');
  await page.fill('#password', 'wrong');

  // ログインボタンをクリック
  await page.click('#login-button');

  // エラーメッセージが表示されることを確認
  await expect(page.locator('.error-message')).toBeVisible();
  await expect(page.locator('.error-message')).toContainText('Invalid username or password');
});