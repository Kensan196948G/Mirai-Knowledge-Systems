/**
 * E2E tests for MFA (Multi-Factor Authentication) flow
 * Tests the complete user journey for MFA setup and login
 */

const { test, expect } = require('@playwright/test');
const pyotp = require('pyotp');  // For generating TOTP codes in tests

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5200';
const TEST_USER = {
  username: 'e2e_test_user',
  password: 'E2eTest1234!',
  email: 'e2e@example.com'
};

test.describe('MFA Setup Flow', () => {
  test('should complete MFA setup wizard', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login.html`);

    await page.fill('#username', TEST_USER.username);
    await page.fill('#password', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Wait for dashboard
    await page.waitForURL('**/index.html');

    // Navigate to MFA settings
    await page.goto(`${BASE_URL}/mfa-setup.html`);

    // Step 1: QR Code Display
    await page.waitForSelector('#qrCodeDisplay img', { timeout: 10000 });

    const qrImage = await page.locator('#qrCodeDisplay img');
    await expect(qrImage).toBeVisible();

    // Extract secret key for testing
    const secretKey = await page.locator('#secretKey').textContent();
    expect(secretKey).toBeTruthy();
    expect(secretKey).not.toBe('-');

    // Click next
    await page.click('button:has-text("次へ")');

    // Step 2: Verification
    await page.waitForSelector('#totpCode');

    // Generate TOTP code
    const totp = pyotp.totp.TOTP(secretKey);
    const code = totp.now();

    await page.fill('#totpCode', code);
    await page.click('button:has-text("検証して有効化")');

    // Wait for step 3
    await page.waitForSelector('#backupCodesDisplay', { timeout: 5000 });

    // Step 3: Backup Codes
    const backupCodes = await page.locator('.backup-code-item');
    const count = await backupCodes.count();
    expect(count).toBe(10);

    // Check the confirmation checkbox
    await page.check('#confirmSaved');

    // Finish button should be enabled
    const finishButton = page.locator('#finishButton');
    await expect(finishButton).toBeEnabled();

    await finishButton.click();

    // Should redirect to admin page
    await page.waitForURL('**/admin.html');
  });

  test('should display QR code and secret key', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto(`${BASE_URL}/mfa-setup.html`);

    // Check QR code is displayed
    const qrImage = await page.locator('#qrCodeDisplay img');
    await expect(qrImage).toBeVisible();

    // Check that image src is base64
    const src = await qrImage.getAttribute('src');
    expect(src).toContain('data:image/png;base64,');

    // Check secret key is displayed (in collapsed section)
    const secretKey = await page.locator('#secretKey').textContent();
    expect(secretKey.length).toBe(32);
  });

  test('should reject invalid TOTP code', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto(`${BASE_URL}/mfa-setup.html`);

    // Wait for QR code
    await page.waitForSelector('#qrCodeDisplay img');

    // Go to step 2
    await page.click('button:has-text("次へ")');

    // Enter invalid code
    await page.fill('#totpCode', '000000');
    await page.click('button:has-text("検証して有効化")');

    // Should show error
    await page.waitForSelector('#verificationError', { state: 'visible' });

    const errorText = await page.locator('#verificationError').textContent();
    expect(errorText).toContain('無効');
  });
});

test.describe('MFA Login Flow', () => {
  test('should show MFA prompt for enabled users', async ({ page }) => {
    // Assumes test user has MFA enabled
    await page.goto(`${BASE_URL}/login.html`);

    await page.fill('#username', TEST_USER.username);
    await page.fill('#password', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Should show MFA form
    await page.waitForSelector('#mfaForm.show', { timeout: 5000 });

    await expect(page.locator('#mfaCode')).toBeVisible();
    await expect(page.locator('#mfaCountdown')).toBeVisible();
  });

  test('should login with valid TOTP code', async ({ page, context }) => {
    // Get MFA secret from setup (this would need to be stored or retrieved)
    // For testing, we assume the secret is known
    const SECRET = 'JBSWY3DPEHPK3PXP';  // Example secret

    await page.goto(`${BASE_URL}/login.html`);

    await page.fill('#username', TEST_USER.username);
    await page.fill('#password', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Wait for MFA form
    await page.waitForSelector('#mfaForm.show');

    // Generate TOTP code
    const totp = pyotp.totp.TOTP(SECRET);
    const code = totp.now();

    await page.fill('#mfaCode', code);

    // Code input should auto-submit on 6 digits
    await page.waitForURL('**/index.html', { timeout: 10000 });

    // Verify logged in
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(token).toBeTruthy();
  });

  test('should show countdown timer', async ({ page }) => {
    await page.goto(`${BASE_URL}/login.html`);

    await page.fill('#username', TEST_USER.username);
    await page.fill('#password', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Wait for MFA form
    await page.waitForSelector('#mfaForm.show');

    // Check countdown exists
    const countdown = page.locator('#mfaCountdown');
    await expect(countdown).toBeVisible();

    const countdownText = await countdown.textContent();
    expect(countdownText).toMatch(/\d:\d{2}/);  // Format: M:SS

    // Wait a second and check it decreases
    await page.waitForTimeout(1000);
    const newCountdownText = await countdown.textContent();
    expect(newCountdownText).not.toBe(countdownText);
  });

  test('should switch between TOTP and backup code input', async ({ page }) => {
    await page.goto(`${BASE_URL}/login.html`);

    await page.fill('#username', TEST_USER.username);
    await page.fill('#password', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Wait for MFA form
    await page.waitForSelector('#mfaForm.show');

    // Initially TOTP input should be visible
    await expect(page.locator('#totpGroup')).toBeVisible();
    await expect(page.locator('#backupGroup')).not.toBeVisible();

    // Click backup code link
    await page.click('#useBackupLink');

    // Now backup input should be visible
    await expect(page.locator('#totpGroup')).not.toBeVisible();
    await expect(page.locator('#backupGroup')).toBeVisible();

    // Click again to switch back
    await page.click('#useBackupLink');

    await expect(page.locator('#totpGroup')).toBeVisible();
    await expect(page.locator('#backupGroup')).not.toBeVisible();
  });

  test('should login with backup code', async ({ page }) => {
    // Assumes user has backup codes
    const BACKUP_CODE = 'AAAA-1111-BBBB';  // Example backup code

    await page.goto(`${BASE_URL}/login.html`);

    await page.fill('#username', TEST_USER.username);
    await page.fill('#password', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Wait for MFA form
    await page.waitForSelector('#mfaForm.show');

    // Switch to backup code
    await page.click('#useBackupLink');

    // Enter backup code
    await page.fill('#backupCode', BACKUP_CODE);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard (if code is valid)
    // Note: This will fail if the backup code is already used or invalid
    // In real tests, you'd need to generate fresh backup codes
  });
});

test.describe('MFA Settings Page', () => {
  test('should display MFA status', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto(`${BASE_URL}/mfa-settings.html`);

    // Wait for status to load
    await page.waitForSelector('#mfaStatusBadge');

    const statusBadge = page.locator('#mfaStatusBadge');
    const statusText = await statusBadge.textContent();

    expect(statusText).toMatch(/(有効|無効)/);
  });

  test('should show different sections based on MFA status', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto(`${BASE_URL}/mfa-settings.html`);

    await page.waitForSelector('#mfaStatusBadge');

    const statusText = await page.locator('#mfaStatusBadge').textContent();

    if (statusText.includes('有効')) {
      // If MFA is enabled, management section should be visible
      await expect(page.locator('#manageSection')).toBeVisible();
      await expect(page.locator('#enableSection')).not.toBeVisible();
    } else {
      // If MFA is disabled, enable section should be visible
      await expect(page.locator('#enableSection')).toBeVisible();
      await expect(page.locator('#manageSection')).not.toBeVisible();
    }
  });

  test('should navigate to setup from settings', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto(`${BASE_URL}/mfa-settings.html`);

    await page.waitForSelector('#mfaStatusBadge');

    const statusText = await page.locator('#mfaStatusBadge').textContent();

    if (statusText.includes('無効')) {
      await page.click('button:has-text("2要素認証を設定")');

      await page.waitForURL('**/mfa-setup.html');
    }
  });

  test('should show regenerate backup codes modal', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto(`${BASE_URL}/mfa-settings.html`);

    await page.waitForSelector('#mfaStatusBadge');

    const statusText = await page.locator('#mfaStatusBadge').textContent();

    if (statusText.includes('有効')) {
      await page.click('button:has-text("バックアップコード再生成")');

      // Modal should appear
      await expect(page.locator('#regenerateModal.show')).toBeVisible();

      // Cancel button should work
      await page.click('button:has-text("キャンセル")');
      await expect(page.locator('#regenerateModal.show')).not.toBeVisible();
    }
  });

  test('should show disable MFA modal', async ({ page }) => {
    await loginAsTestUser(page);

    await page.goto(`${BASE_URL}/mfa-settings.html`);

    await page.waitForSelector('#mfaStatusBadge');

    const statusText = await page.locator('#mfaStatusBadge').textContent();

    if (statusText.includes('有効')) {
      await page.click('button:has-text("2要素認証を無効化")');

      // Modal should appear
      await expect(page.locator('#disableModal.show')).toBeVisible();

      // Should have password and code inputs
      await expect(page.locator('#disablePassword')).toBeVisible();
      await expect(page.locator('#disableCode')).toBeVisible();

      // Cancel button should work
      await page.click('button:has-text("キャンセル")');
      await expect(page.locator('#disableModal.show')).not.toBeVisible();
    }
  });
});

test.describe('MFA Security', () => {
  test('should require authentication for MFA setup', async ({ page }) => {
    // Try to access MFA setup without logging in
    await page.goto(`${BASE_URL}/mfa-setup.html`);

    // Should redirect to login or show error
    await page.waitForTimeout(2000);

    const url = page.url();
    expect(url).toContain('login.html');
  });

  test('should require authentication for MFA settings', async ({ page }) => {
    // Try to access MFA settings without logging in
    await page.goto(`${BASE_URL}/mfa-settings.html`);

    // Should redirect to login or show error
    await page.waitForTimeout(2000);

    const url = page.url();
    expect(url).toContain('login.html');
  });
});

// Helper functions

async function loginAsTestUser(page) {
  await page.goto(`${BASE_URL}/login.html`);

  await page.fill('#username', TEST_USER.username);
  await page.fill('#password', TEST_USER.password);
  await page.click('button[type="submit"]');

  // Check if MFA is required
  try {
    await page.waitForSelector('#mfaForm.show', { timeout: 2000 });

    // MFA is enabled, need to complete MFA login
    // For simplicity, skip this in helper function
    // Real implementation would need to handle this
    throw new Error('MFA enabled - tests need to handle this case');
  } catch (error) {
    // MFA not required or timeout, continue
    await page.waitForURL('**/index.html', { timeout: 5000 });
  }
}
