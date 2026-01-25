import { test, expect } from '@playwright/test';

test.describe('Project Progress UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン
    await page.goto('/login.html');
    await page.fill('#username', 'admin');
    await page.fill('#password', 'admin123');
    await page.click('#login-button');
    await expect(page).toHaveURL('/index.html');
  });

  test('should display project progress in dashboard', async ({ page }) => {
    // 稼働モニタリングセクションの進捗が表示されているか確認
    await expect(page.locator('.progress-item').first()).toBeVisible();

    // 進捗バーが存在するか確認
    const progressBar = page.locator('.progress-fill').first();
    await expect(progressBar).toBeVisible();

    // 進捗パーセントが表示されているか確認
    const progressText = page.locator('.progress-meta').first();
    await expect(progressText).toContainText('%');
  });

  test('should load project progress data from API', async ({ page }) => {
    // API呼び出しを監視
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/v1/projects/') && resp.url().includes('/progress')),
      page.reload()
    ]);

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data).toHaveProperty('progress_percentage');
    expect(data.data).toHaveProperty('tasks_completed');
    expect(data.data).toHaveProperty('total_tasks');
  });

  test('should handle project progress API errors gracefully', async ({ page }) => {
    // 存在しないプロジェクトIDでAPIを呼び出す
    const response = await page.request.get('/api/v1/projects/999999/progress');
    expect(response.status()).toBe(404);
  });
});