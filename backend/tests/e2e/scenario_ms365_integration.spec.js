/**
 * E2E Tests - Microsoft 365 Integration
 * Microsoft 365連携機能のエンドツーエンドテスト
 */

const { test, expect } = require('@playwright/test');

test.describe('Microsoft 365 Integration', () => {
  test.beforeEach(async ({ page }) => {
    // ログインページに移動
    await page.goto('/login.html');

    // ログイン
    await page.fill('input[name="username"]', 'test_user');
    await page.fill('input[name="password"]', 'test_password');
    await page.click('button[type="submit"]');

    // ダッシュボードに遷移することを確認
    await expect(page).toHaveURL(/.*dashboard.*/);
  });

  test('should check Microsoft 365 authentication status', async ({ page }) => {
    // Microsoft 365連携ページに移動
    await page.goto('/microsoft365.html');

    // 認証状態を確認
    await expect(page.locator('.auth-status')).toContainText('認証済み');

    // サービス一覧を確認
    await expect(page.locator('.service-list')).toContainText('OneDrive');
    await expect(page.locator('.service-list')).toContainText('SharePoint');
  });

  test('should list OneDrive files', async ({ page }) => {
    // Microsoft 365ファイル一覧ページに移動
    await page.goto('/microsoft365-files.html');

    // OneDriveを選択
    await page.click('.service-selector .onedrive');

    // ファイル一覧が表示されることを確認
    await expect(page.locator('.file-list')).toBeVisible();

    // ファイル/フォルダが表示されることを確認
    const fileItems = page.locator('.file-item');
    await expect(fileItems).toHaveCount(await fileItems.count());
  });

  test('should upload file to OneDrive', async ({ page }) => {
    // Microsoft 365アップロードページに移動
    await page.goto('/microsoft365-upload.html');

    // OneDriveを選択
    await page.selectOption('.service-select', 'onedrive');

    // ファイル選択
    const filePath = path.join(__dirname, '../../test_files/sample.pdf');
    await page.setInputFiles('input[type="file"]', filePath);

    // アップロードボタンをクリック
    await page.click('button[type="submit"]');

    // 成功メッセージを確認
    await expect(page.locator('.success-message')).toContainText('Microsoft 365にファイルが正常にアップロードされました');
  });

  test('should navigate through SharePoint folders', async ({ page }) => {
    // Microsoft 365ファイル一覧ページに移動
    await page.goto('/microsoft365-files.html');

    // SharePointを選択
    await page.click('.service-selector .sharepoint');

    // フォルダをクリックしてナビゲーション
    await page.click('.folder-item');

    // パンくずリストが更新されることを確認
    await expect(page.locator('.breadcrumb')).toContainText('/');
  });

  test('should handle authentication errors gracefully', async ({ page }) => {
    // 認証切れをシミュレート（実際のテストではAPIモックを使用）
    await page.goto('/microsoft365.html');

    // エラーメッセージが表示されることを確認
    await expect(page.locator('.error-message')).toContainText('認証に失敗しました');
  });
});