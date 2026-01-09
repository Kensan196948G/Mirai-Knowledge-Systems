import { test, expect } from '@playwright/test';

test('knowledge search flow', async ({ page }) => {
  // ログイン
  await page.goto('/login.html');
  await page.fill('#username', 'admin');
  await page.fill('#password', 'admin123');
  await page.click('#login-button');
  await expect(page).toHaveURL(/.*index\.html/);

  // ナレッジ検索
  await page.fill('#search-input', '施工');
  await page.click('#search-button');

  // 検索結果が表示されることを確認
  await expect(page.locator('.knowledge-item')).toBeVisible();
});

test('knowledge creation flow', async ({ page }) => {
  // ログイン
  await page.goto('/login.html');
  await page.fill('#username', 'admin');
  await page.fill('#password', 'admin123');
  await page.click('#login-button');
  await expect(page).toHaveURL(/.*index\.html/);

  // ナレッジ作成ページに移動
  await page.click('#create-knowledge-button');
  await expect(page).toHaveURL(/.*create\.html/);

  // ナレッジ情報を入力
  await page.fill('#title', 'テストナレッジ');
  await page.fill('#content', 'これはテスト用のナレッジです。');
  await page.selectOption('#category', '施工計画');

  // 保存ボタンをクリック
  await page.click('#save-button');

  // 成功メッセージが表示されることを確認
  await expect(page.locator('.success-message')).toBeVisible();
  await expect(page.locator('.success-message')).toContainText('ナレッジが作成されました');
});