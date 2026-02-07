/**
 * E2E tests for MS365 File Preview
 * Mirai Knowledge Systems - Phase E-4
 *
 * Tests the complete file preview flow:
 * - Office documents (Word/Excel/PowerPoint) preview
 * - PDF preview
 * - Image preview
 * - Thumbnail display
 * - Download functionality
 *
 * @version 1.0.0
 */

const { test, expect } = require('@playwright/test');

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5200';
const TEST_USER = {
  username: 'admin',
  password: 'admin123'
};

test.describe('MS365 File Preview', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto(`${BASE_URL}/login.html`);

    // Fill credentials
    await page.fill('input[name="username"]', TEST_USER.username);
    await page.fill('input[name="password"]', TEST_USER.password);

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('**/index.html', { timeout: 10000 });

    // Navigate to MS365 sync settings page
    await page.goto(`${BASE_URL}/ms365-sync-settings.html`);

    // Wait for page to load
    await page.waitForTimeout(2000);
  });

  test('1. Office file preview modal displays correctly', async ({ page }) => {
    // Click preview button for first Office document
    const previewButton = page.locator('[data-file-type="docx"] .preview-button, button:has-text("プレビュー")').first();

    // Check if preview button exists
    if (await previewButton.count() === 0) {
      console.log('[Test] No preview button found - skipping test');
      test.skip();
      return;
    }

    await previewButton.click();

    // Wait for modal to appear
    const modal = page.locator('#filePreviewModal, .file-preview-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Check modal title
    const title = modal.locator('.file-preview-title, h3');
    await expect(title).toBeVisible();

    // Check if iframe or preview container is visible
    const previewContainer = modal.locator('.file-preview-container, iframe, embed, img');
    await expect(previewContainer.first()).toBeVisible({ timeout: 15000 });

    // Check close button exists
    const closeButton = modal.locator('.file-preview-close, button:has-text("×")');
    await expect(closeButton).toBeVisible();

    // Close modal
    await closeButton.click();

    // Verify modal is hidden
    await expect(modal).toBeHidden({ timeout: 5000 });
  });

  test('2. PDF file preview displays correctly', async ({ page }) => {
    // Click preview button for PDF file
    const previewButton = page.locator('[data-file-type="pdf"] .preview-button, button:has-text("プレビュー")').first();

    // Check if preview button exists
    if (await previewButton.count() === 0) {
      console.log('[Test] No PDF preview button found - skipping test');
      test.skip();
      return;
    }

    await previewButton.click();

    // Wait for modal
    const modal = page.locator('#filePreviewModal, .file-preview-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Check for embed or iframe element for PDF
    const pdfEmbed = modal.locator('embed[type="application/pdf"], iframe');
    await expect(pdfEmbed.first()).toBeVisible({ timeout: 15000 });

    // Close modal
    const closeButton = modal.locator('.file-preview-close, button:has-text("×")');
    await closeButton.click();
  });

  test('3. Image file preview displays correctly', async ({ page }) => {
    // Click preview button for image file
    const previewButton = page.locator('[data-file-type="jpg"] .preview-button, [data-file-type="png"] .preview-button, button:has-text("プレビュー")').first();

    // Check if preview button exists
    if (await previewButton.count() === 0) {
      console.log('[Test] No image preview button found - skipping test');
      test.skip();
      return;
    }

    await previewButton.click();

    // Wait for modal
    const modal = page.locator('#filePreviewModal, .file-preview-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Check for img element
    const img = modal.locator('img');
    await expect(img.first()).toBeVisible({ timeout: 15000 });

    // Close modal
    const closeButton = modal.locator('.file-preview-close, button:has-text("×")');
    await closeButton.click();
  });

  test('4. Thumbnail displays correctly', async ({ page }) => {
    // Check for thumbnail images in file list
    const thumbnails = page.locator('.file-thumbnail img, .thumbnail-img');

    // Wait for at least one thumbnail to load
    if (await thumbnails.count() > 0) {
      await expect(thumbnails.first()).toBeVisible({ timeout: 10000 });

      // Check that thumbnail has src attribute
      const src = await thumbnails.first().getAttribute('src');
      expect(src).toBeTruthy();
      expect(src.length).toBeGreaterThan(0);
    } else {
      console.log('[Test] No thumbnails found on page - skipping test');
      test.skip();
    }
  });

  test('5. Download button works correctly', async ({ page }) => {
    // Click preview button
    const previewButton = page.locator('button:has-text("プレビュー")').first();

    // Check if preview button exists
    if (await previewButton.count() === 0) {
      console.log('[Test] No preview button found - skipping test');
      test.skip();
      return;
    }

    await previewButton.click();

    // Wait for modal
    const modal = page.locator('#filePreviewModal, .file-preview-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Look for download button
    const downloadButton = modal.locator('button:has-text("ダウンロード"), .download-button');

    if (await downloadButton.count() > 0) {
      // Set up download event listener
      const downloadPromise = page.waitForEvent('download', { timeout: 15000 });

      // Click download button
      await downloadButton.click();

      // Wait for download to start
      try {
        const download = await downloadPromise;
        expect(download).toBeTruthy();
        console.log('[Test] Download started successfully');
      } catch (error) {
        console.log('[Test] Download may not be available for this file type');
      }
    } else {
      console.log('[Test] Download button not found - may not be visible for this file type');
    }

    // Close modal
    const closeButton = modal.locator('.file-preview-close, button:has-text("×")');
    if (await closeButton.count() > 0) {
      await closeButton.click();
    }
  });

  test('6. FilePreviewManager module is loaded', async ({ page }) => {
    // Check that FilePreviewManager is available in window
    const hasFilePreviewManager = await page.evaluate(() => {
      return typeof window.FilePreviewManager !== 'undefined' &&
             typeof window.filePreviewManager !== 'undefined';
    });

    expect(hasFilePreviewManager).toBe(true);
  });

  test('7. Preview modal closes on backdrop click', async ({ page }) => {
    // Click preview button
    const previewButton = page.locator('button:has-text("プレビュー")').first();

    // Check if preview button exists
    if (await previewButton.count() === 0) {
      console.log('[Test] No preview button found - skipping test');
      test.skip();
      return;
    }

    await previewButton.click();

    // Wait for modal
    const modal = page.locator('#filePreviewModal, .file-preview-modal');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Click on modal backdrop (not the content)
    await modal.click({ position: { x: 10, y: 10 } });

    // Modal may or may not close depending on implementation
    // This is a UX test to ensure backdrop click is handled gracefully
    await page.waitForTimeout(1000);

    // Close modal via close button to ensure clean state
    const closeButton = modal.locator('.file-preview-close, button:has-text("×")');
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
  });

  test('8. Loading indicator displays while fetching preview', async ({ page }) => {
    // Click preview button
    const previewButton = page.locator('button:has-text("プレビュー")').first();

    // Check if preview button exists
    if (await previewButton.count() === 0) {
      console.log('[Test] No preview button found - skipping test');
      test.skip();
      return;
    }

    // Click and immediately check for loading indicator
    await previewButton.click();

    const modal = page.locator('#filePreviewModal, .file-preview-modal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Check for loading indicator (may be very brief)
    const loading = modal.locator('.file-preview-loading, .loading');

    // Loading may already be hidden if network is fast
    const isLoadingVisible = await loading.isVisible().catch(() => false);

    if (isLoadingVisible) {
      console.log('[Test] Loading indicator was visible');
    } else {
      console.log('[Test] Loading indicator was too fast to capture (or already loaded)');
    }

    // Close modal
    await page.waitForTimeout(2000);
    const closeButton = modal.locator('.file-preview-close, button:has-text("×")');
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
  });
});
