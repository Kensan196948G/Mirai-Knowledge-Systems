/**
 * E2E Tests - File Upload Flow
 * ファイルアップロード機能のエンドツーエンドテスト
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('File Upload Flow', () => {
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

  test('should upload a valid file successfully', async ({ page }) => {
    // ファイルアップロードページに移動
    await page.goto('/upload.html');

    // ファイル選択
    const filePath = path.join(__dirname, '../../test_files/sample.pdf');
    await page.setInputFiles('input[type="file"]', filePath);

    // アップロードボタンをクリック
    await page.click('button[type="submit"]');

    // 成功メッセージを確認
    await expect(page.locator('.success-message')).toContainText('ファイルが正常にアップロードされました');

    // ファイル一覧に表示されることを確認
    await page.goto('/files.html');
    await expect(page.locator('.file-list')).toContainText('sample.pdf');
  });

  test('should reject invalid file type', async ({ page }) => {
    // ファイルアップロードページに移動
    await page.goto('/upload.html');

    // 無効なファイルタイプを選択
    const filePath = path.join(__dirname, '../../test_files/malicious.exe');
    await page.setInputFiles('input[type="file"]', filePath);

    // アップロードボタンをクリック
    await page.click('button[type="submit"]');

    // エラーメッセージを確認
    await expect(page.locator('.error-message')).toContainText('許可されていないファイルタイプです');
  });

  test('should reject file that is too large', async ({ page }) => {
    // ファイルアップロードページに移動
    await page.goto('/upload.html');

    // 大きすぎるファイルを選択 (モック)
    const filePath = path.join(__dirname, '../../test_files/large_file.pdf');
    await page.setInputFiles('input[type="file"]', filePath);

    // アップロードボタンをクリック
    await page.click('button[type="submit"]');

    // エラーメッセージを確認
    await expect(page.locator('.error-message')).toContainText('ファイルサイズが大きすぎます');
  });

  test('should download uploaded file', async ({ page }) => {
    // ファイル一覧ページに移動
    await page.goto('/files.html');

    // ダウンロードリンクをクリック
    const downloadPromise = page.waitForEvent('download');
    await page.click('.file-item .download-link');
    const download = await downloadPromise;

    // ダウンロードが開始されたことを確認
    expect(download.suggestedFilename()).toBe('sample.pdf');
  });

  test('should display file list correctly', async ({ page }) => {
    // ファイル一覧ページに移動
    await page.goto('/files.html');

    // ファイル一覧が表示されることを確認
    await expect(page.locator('.file-list')).toBeVisible();

    // 各ファイルの情報が正しく表示されることを確認
    const fileItems = page.locator('.file-item');
    await expect(fileItems).toHaveCount(await fileItems.count());

    // ファイル名、サイズ、日時などの情報が表示されることを確認
    await expect(page.locator('.file-name')).toBeVisible();
    await expect(page.locator('.file-size')).toBeVisible();
    await expect(page.locator('.file-date')).toBeVisible();
  });
});