/**
 * E2E Tests - Login Flow
 * ログイン機能のエンドツーエンドテスト
 */

const { test, expect } = require('@playwright/test');

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // ログインページに移動
    await page.goto('/login.html');
  });

  test('should display login form correctly', async ({ page }) => {
    // ページタイトルの確認
    await expect(page).toHaveTitle(/Mirai Knowledge Systems/);

    // ログインフォームの要素が表示されているか確認
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // 無効な認証情報を入力
    await page.fill('input[name="username"]', 'invalid_user');
    await page.fill('input[name="password"]', 'wrong_password');

    // ログインボタンをクリック
    await page.click('button[type="submit"]');

    // エラーメッセージが表示されることを確認
    const errorMessage = page.locator('.error-message, .alert-danger, [role="alert"]');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // 有効な認証情報を入力（テスト用ユーザー）
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');

    // ログインボタンをクリック
    await page.click('button[type="submit"]');

    // ダッシュボードにリダイレクトされることを確認
    await expect(page).toHaveURL(/\/index\.html/, { timeout: 10000 });

    // LocalStorageにトークンが保存されることを確認
    const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(accessToken).toBeTruthy();
  });

  test('should persist login session after page reload', async ({ page }) => {
    // ログイン
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // ダッシュボードが表示されるまで待機
    await expect(page).toHaveURL(/\/index\.html/, { timeout: 10000 });

    // ページをリロード
    await page.reload();

    // まだログイン状態であることを確認（ログインページにリダイレクトされない）
    await expect(page).not.toHaveURL(/\/login\.html/);

    // LocalStorageにトークンが残っていることを確認
    const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(accessToken).toBeTruthy();
  });

  test('should redirect to login page when accessing protected page without auth', async ({ page }) => {
    // 認証なしでダッシュボードにアクセス
    await page.goto('/index.html');

    // ログインページにリダイレクトされることを確認
    await expect(page).toHaveURL(/\/login\.html/, { timeout: 5000 });
  });

  test('should logout successfully', async ({ page }) => {
    // ログイン
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // ダッシュボードが表示されるまで待機
    await expect(page).toHaveURL(/\/index\.html/, { timeout: 10000 });

    // ログアウトボタンをクリック
    const logoutButton = page.locator('button:has-text("ログアウト"), a:has-text("ログアウト"), #logoutBtn');
    await logoutButton.click();

    // ログインページにリダイレクトされることを確認
    await expect(page).toHaveURL(/\/login\.html/, { timeout: 5000 });

    // LocalStorageからトークンが削除されることを確認
    const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(accessToken).toBeNull();
  });

  test('should prevent XSS in login form', async ({ page }) => {
    // XSS攻撃を試みる
    const xssPayload = '<script>alert("XSS")</script>';

    await page.fill('input[name="username"]', xssPayload);
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');

    // スクリプトが実行されないことを確認（ページがクラッシュしない）
    const pageTitle = await page.title();
    expect(pageTitle).toBeTruthy();

    // ダイアログが表示されないことを確認
    let dialogAppeared = false;
    page.on('dialog', () => {
      dialogAppeared = true;
    });

    await page.waitForTimeout(1000);
    expect(dialogAppeared).toBe(false);
  });
});

test.describe('Login Form Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login.html');
  });

  test('should require username field', async ({ page }) => {
    // パスワードのみ入力
    await page.fill('input[name="password"]', 'password123');

    // フォーム送信
    await page.click('button[type="submit"]');

    // HTML5バリデーションまたはカスタムエラーが表示される
    const usernameInput = page.locator('input[name="username"]');
    const validationMessage = await usernameInput.evaluate(el => el.validationMessage);

    // バリデーションメッセージが存在するか、required属性があることを確認
    const hasRequired = await usernameInput.evaluate(el => el.hasAttribute('required'));
    expect(hasRequired || validationMessage).toBeTruthy();
  });

  test('should require password field', async ({ page }) => {
    // ユーザー名のみ入力
    await page.fill('input[name="username"]', 'testuser');

    // フォーム送信
    await page.click('button[type="submit"]');

    // HTML5バリデーションまたはカスタムエラーが表示される
    const passwordInput = page.locator('input[name="password"]');
    const validationMessage = await passwordInput.evaluate(el => el.validationMessage);

    const hasRequired = await passwordInput.evaluate(el => el.hasAttribute('required'));
    expect(hasRequired || validationMessage).toBeTruthy();
  });
});
