import { test, expect } from '@playwright/test';

test.describe('Experts Statistics UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン
    await page.goto('/login.html');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('#login-button');
    await expect(page).toHaveURL('/index.html');
  });

  test('should display experts statistics in dashboard', async ({ page }) => {
    // EXPERTSセクションが表示されているか確認
    await expect(page.locator('#expertsList')).toBeVisible();

    // 専門家一覧が表示されているか確認
    const expertsList = page.locator('#expertsList .nav-list li');
    await expect(expertsList.first()).toBeVisible();
  });

  test('should load experts stats data from API', async ({ page }) => {
    // API呼び出しを監視
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/v1/experts/stats')),
      page.reload()
    ]);

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data).toHaveProperty('total_experts');
    expect(data.data).toHaveProperty('available_experts');
    expect(data.data).toHaveProperty('specializations');
    expect(data.data).toHaveProperty('average_rating');
  });

  test('should load experts list from API', async ({ page }) => {
    // API呼び出しを監視
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/v1/experts') && !resp.url().includes('/stats')),
      page.reload()
    ]);

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(Array.isArray(data.data)).toBe(true);
  });

  test('should handle experts API errors gracefully', async ({ page }) => {
    // 存在しない専門家IDでAPIを呼び出す
    const response = await page.request.get('/api/v1/experts/999999');
    expect(response.status()).toBe(404);
  });

  test('should filter experts by specialization', async ({ page }) => {
    // 専門分野フィルターが存在するか確認
    const filterSelect = page.locator('#expertFieldFilter');
    await expect(filterSelect).toBeVisible();

    // フィルターを変更
    await filterSelect.selectOption('構造設計');

    // フィルター後の結果を確認（API呼び出しを監視）
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/v1/experts?specialization=')),
      filterSelect.selectOption('構造設計')
    ]);

    expect(response.status()).toBe(200);
  });
});