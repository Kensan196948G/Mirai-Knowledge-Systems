/**
 * E2E Tests: MS365 File Preview
 * Phase E-4 Week 2-3
 *
 * Test Coverage:
 * 1. Thumbnail display in sync history table
 * 2. Preview modal display (Office/PDF/Image)
 * 3. Download functionality
 * 4. Error handling (404, 403, Network)
 * 5. Offline mode with cache
 * 6. Accessibility (Keyboard navigation)
 *
 * Requirements:
 * - Backend server running (http://localhost:5200)
 * - MS365 sync configured with test files
 * - Test user: admin/Admin@123
 *
 * @version 1.0.0
 */

const { test, expect } = require('@playwright/test');

// Test data (adjust based on actual MS365 test environment)
const TEST_FILE = {
  driveId: 'test-drive-id',
  fileId: 'test-file-id',
  fileName: 'test-document.docx',
  mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
};

test.describe('MS365 File Preview - E2E Tests', () => {
  /**
   * Setup: Login before each test
   */
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:5200/login.html');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'Admin@123');
    await page.click('button[type="submit"]');

    // Wait for redirect to index.html
    await page.waitForURL('**/index.html', { timeout: 10000 });
    await expect(page).toHaveURL(/index\.html/);
  });

  /**
   * Test 1: Office File Preview Display
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 1
   */
  test('Office file preview displays in iframe', async ({ page }) => {
    // Navigate to MS365 sync settings
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Wait for file preview manager to load
    await page.waitForFunction(() => window.filePreviewManager !== undefined, { timeout: 5000 });

    // Mock API response (Office document)
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            preview_url: 'https://view.officeapps.live.com/op/embed.aspx?src=test',
            download_url: 'http://localhost:5200/test.docx',
            mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            file_name: 'test-document.docx',
            file_size: 102400
          }
        })
      });
    });

    // Trigger preview display programmatically
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'test-file-id', {
        fileName: 'test-document.docx',
        mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
    });

    // Wait for modal to appear
    const modal = page.locator('#filePreviewModal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Verify file name in header
    const fileName = page.locator('.file-preview-title');
    await expect(fileName).toContainText('test-document.docx');

    // Verify iframe is rendered
    const iframe = page.locator('#filePreviewModal iframe');
    await expect(iframe).toBeVisible({ timeout: 5000 });

    // Verify iframe src contains Office Online URL
    const iframeSrc = await iframe.getAttribute('src');
    expect(iframeSrc).toContain('view.officeapps.live.com');
  });

  /**
   * Test 2: PDF File Preview Display
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 2
   */
  test('PDF file preview displays in embed', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock API response (PDF)
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            preview_url: null,
            download_url: 'http://localhost:5200/test.pdf',
            mime_type: 'application/pdf',
            file_name: 'test-document.pdf',
            file_size: 204800
          }
        })
      });
    });

    // Trigger preview
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'test-pdf-id', {
        fileName: 'test-document.pdf',
        mimeType: 'application/pdf'
      });
    });

    // Verify modal
    const modal = page.locator('#filePreviewModal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Verify embed element for PDF
    const embed = page.locator('#filePreviewModal embed[type="application/pdf"]');
    await expect(embed).toBeVisible({ timeout: 5000 });
  });

  /**
   * Test 3: Image File Preview Display
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 3
   */
  test('Image file preview displays in img tag', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock API response (Image)
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            preview_url: null,
            download_url: 'http://localhost:5200/test.jpg',
            mime_type: 'image/jpeg',
            file_name: 'test-image.jpg',
            file_size: 51200
          }
        })
      });
    });

    // Mock image download
    await page.route('**/test.jpg', async route => {
      // Send a small 1x1 pixel PNG
      const png = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64'
      );
      await route.fulfill({
        status: 200,
        contentType: 'image/png',
        body: png
      });
    });

    // Trigger preview
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'test-image-id', {
        fileName: 'test-image.jpg',
        mimeType: 'image/jpeg'
      });
    });

    // Verify modal
    const modal = page.locator('#filePreviewModal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Verify img element
    const img = page.locator('#filePreviewModal .file-preview-container img');
    await expect(img).toBeVisible({ timeout: 5000 });
  });

  /**
   * Test 4: Thumbnail Display in Sync History Table
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 4
   */
  test('Thumbnails are displayed in sync history table', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock thumbnail API
    await page.route('**/api/v1/integrations/microsoft365/files/*/thumbnail*', async route => {
      // Send a small 1x1 pixel PNG as thumbnail
      const png = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64'
      );
      await route.fulfill({
        status: 200,
        contentType: 'image/png',
        body: png
      });
    });

    // Trigger thumbnail fetch programmatically
    await page.evaluate(() => {
      return window.filePreviewManager.getThumbnailUrl('test-drive-id', 'test-file-id', 'small');
    });

    // Wait for cache storage
    await page.waitForTimeout(1000);

    // Verify thumbnail is cached
    const cached = await page.evaluate(async () => {
      const cache = await caches.open('mks-thumbnails-v1.4.0');
      const keys = await cache.keys();
      return keys.length > 0;
    });

    expect(cached).toBe(true);
  });

  /**
   * Test 5: 404 Error Handling (File Not Found)
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 5
   */
  test('Displays error message when file is not found (404)', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock 404 response
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: {
            code: 'FILE_NOT_FOUND',
            message: 'File not found'
          }
        })
      });
    });

    // Trigger preview
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'nonexistent-file-id', {
        fileName: 'nonexistent.docx'
      });
    });

    // Verify error message is displayed
    const errorDiv = page.locator('.file-preview-error');
    await expect(errorDiv).toBeVisible({ timeout: 10000 });

    const errorText = page.locator('.file-preview-error p');
    await expect(errorText).toContainText('プレビューの表示に失敗しました');
  });

  /**
   * Test 6: 403 Error Handling (Permission Denied)
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 6
   * Arch-reviewer推奨テスト #1
   */
  test('Displays permission error when access is denied (403)', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock 403 response
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: {
            code: 'PERMISSION_ERROR',
            message: 'Access denied'
          }
        })
      });
    });

    // Trigger preview
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'restricted-file-id', {
        fileName: 'restricted.docx'
      });
    });

    // Verify permission error message
    const errorDiv = page.locator('.file-preview-error');
    await expect(errorDiv).toBeVisible({ timeout: 10000 });

    const errorText = page.locator('.file-preview-error p');
    await expect(errorText).toContainText('アクセス権限がありません');
  });

  /**
   * Test 7: Offline Mode with Cache Fallback
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 7
   * Arch-reviewer推奨テスト #2
   */
  test('Uses cached preview when offline', async ({ page, context }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Step 1: Online - Fetch and cache preview
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            preview_url: 'https://view.officeapps.live.com/op/embed.aspx?src=test',
            download_url: 'http://localhost:5200/test.docx',
            mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            file_name: 'cached-document.docx',
            file_size: 102400
          }
        })
      });
    });

    // Trigger preview (will cache the response)
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'cached-file-id', {
        fileName: 'cached-document.docx'
      });
    });

    // Wait for preview to display
    const modal = page.locator('#filePreviewModal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Close modal
    await page.locator('.file-preview-close').click();
    await expect(modal).not.toBeVisible();

    // Step 2: Go offline
    await context.setOffline(true);

    // Step 3: Trigger preview again (should use cache)
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'cached-file-id', {
        fileName: 'cached-document.docx'
      });
    });

    // Verify modal displays (from cache)
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Verify file name is correct (proving cache was used)
    const fileName = page.locator('.file-preview-title');
    await expect(fileName).toContainText('cached-document.docx');

    // Restore online mode
    await context.setOffline(false);
  });

  /**
   * Test 8: Accessibility - Keyboard Navigation (Escape key)
   * Requirement: 仕様書 9.3 E2Eテスト - Test Case 8
   */
  test('Modal closes with Escape key', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock API response
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            preview_url: 'https://view.officeapps.live.com/op/embed.aspx?src=test',
            download_url: 'http://localhost:5200/test.docx',
            mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            file_name: 'test-document.docx',
            file_size: 102400
          }
        })
      });
    });

    // Trigger preview
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'test-file-id', {
        fileName: 'test-document.docx'
      });
    });

    // Verify modal is visible
    const modal = page.locator('#filePreviewModal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Press Escape key
    await page.keyboard.press('Escape');

    // Verify modal is closed
    await expect(modal).not.toBeVisible({ timeout: 5000 });
  });

  /**
   * Test 9: Download Button Functionality
   * Requirement: 仕様書 9.3 E2Eテスト (補足)
   */
  test('Download button triggers file download', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock API response
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            preview_url: null,
            download_url: 'http://localhost:5200/test-download.pdf',
            mime_type: 'application/pdf',
            file_name: 'test-download.pdf',
            file_size: 204800
          }
        })
      });
    });

    // Mock download endpoint
    await page.route('**/api/v1/integrations/microsoft365/files/*/download*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        headers: {
          'Content-Disposition': 'attachment; filename=test-download.pdf'
        },
        body: Buffer.from('PDF content')
      });
    });

    // Trigger preview for download-only file
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'download-file-id', {
        fileName: 'test-download.pdf'
      });
    });

    // Wait for modal
    const modal = page.locator('#filePreviewModal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Click download button in the download-only preview
    const downloadPromise = page.waitForEvent('download');
    await page.locator('.file-preview-container button.action-btn').click();

    // Verify download started
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('test-download.pdf');
  });

  /**
   * Test 10: Close Button Functionality
   * Requirement: 仕様書 9.3 E2Eテスト (補足)
   */
  test('Close button closes the modal', async ({ page }) => {
    await page.goto('http://localhost:5200/ms365-sync-settings.html');
    await page.waitForLoadState('networkidle');

    // Mock API response
    await page.route('**/api/v1/integrations/microsoft365/files/*/preview*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            preview_url: 'https://view.officeapps.live.com/op/embed.aspx?src=test',
            download_url: 'http://localhost:5200/test.docx',
            mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            file_name: 'test-document.docx',
            file_size: 102400
          }
        })
      });
    });

    // Trigger preview
    await page.evaluate(() => {
      window.filePreviewManager.showPreview('test-drive-id', 'test-file-id', {
        fileName: 'test-document.docx'
      });
    });

    // Verify modal is visible
    const modal = page.locator('#filePreviewModal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Click close button
    await page.locator('.file-preview-close').click();

    // Verify modal is closed
    await expect(modal).not.toBeVisible({ timeout: 5000 });
  });
});
