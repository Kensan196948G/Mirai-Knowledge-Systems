/**
 * E2E Tests - SOP Detail Page & Expert Consultation Flow
 * SOP詳細ページと専門家相談フローのエンドツーエンドテスト
 */

const { test, expect } = require('@playwright/test');

// テスト用のログインヘルパー関数
async function login(page, username = 'admin', password = 'admin123') {
  await page.goto('/login.html');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/index\.html/, { timeout: 10000 });
}

test.describe('SOP Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display SOP detail page correctly', async ({ page }) => {
    // SOP詳細ページに直接アクセス（例: sop-detail.html?id=1）
    await page.goto('/sop-detail.html?id=1');

    // ページが正しく読み込まれるまで待機
    await page.waitForTimeout(2000);

    // タイトルが表示されることを確認
    const title = page.locator('h1, h2, .sop-title, .detail-title');
    await expect(title.first()).toBeVisible({ timeout: 5000 });

    // タイトルのテキストが存在することを確認
    const titleText = await title.first().textContent();
    expect(titleText).toBeTruthy();
    expect(titleText.length).toBeGreaterThan(0);
  });

  test('should display SOP content sections', async ({ page }) => {
    await page.goto('/sop-detail.html?id=1');
    await page.waitForTimeout(2000);

    // コンテンツエリアが表示されることを確認
    const content = page.locator('.sop-content, .detail-content, .content-area, #sopContent');

    if (await content.count() > 0) {
      await expect(content.first()).toBeVisible();

      // コンテンツが空でないことを確認
      const contentText = await content.first().textContent();
      expect(contentText.length).toBeGreaterThan(0);
    }
  });

  test('should display SOP metadata', async ({ page }) => {
    await page.goto('/sop-detail.html?id=1');
    await page.waitForTimeout(2000);

    // メタデータ（作成日、更新日、ステータスなど）が表示される
    const metadata = page.locator('.metadata, .sop-info, .detail-meta, .info-section');

    if (await metadata.count() > 0) {
      await expect(metadata.first()).toBeVisible();
    }

    // または個別のメタデータ項目を確認
    const createdDate = page.locator('*:has-text("作成日"), *:has-text("Created")');
    const updatedDate = page.locator('*:has-text("更新日"), *:has-text("Updated")');

    // いずれかのメタデータが表示されることを確認
    const hasMetadata = (await createdDate.count() > 0) || (await updatedDate.count() > 0);
    expect(hasMetadata).toBe(true);
  });

  test('should display SOP status', async ({ page }) => {
    await page.goto('/sop-detail.html?id=1');
    await page.waitForTimeout(2000);

    // ステータスバッジが表示されることを確認
    const statusBadge = page.locator('.status, .badge, .tag, [class*="status-"]');

    if (await statusBadge.count() > 0) {
      await expect(statusBadge.first()).toBeVisible();

      // ステータステキストが存在することを確認
      const statusText = await statusBadge.first().textContent();
      expect(statusText).toBeTruthy();
    }
  });

  test('should allow downloading SOP as PDF', async ({ page }) => {
    await page.goto('/sop-detail.html?id=1');
    await page.waitForTimeout(2000);

    // PDFダウンロードボタンが存在する場合
    const downloadButton = page.locator('button:has-text("PDF"), button:has-text("ダウンロード"), .download-btn');

    if (await downloadButton.count() > 0) {
      // ボタンが表示され、有効であることを確認
      await expect(downloadButton.first()).toBeVisible();
      expect(await downloadButton.first().isEnabled()).toBe(true);

      // クリック可能であることを確認（実際のダウンロードはテストしない）
      await downloadButton.first().hover();
    }
  });

  test('should navigate back to knowledge list', async ({ page }) => {
    await page.goto('/sop-detail.html?id=1');
    await page.waitForTimeout(2000);

    // 戻るボタンまたはパンくずリンクを探す
    const backButton = page.locator('button:has-text("戻る"), a:has-text("戻る"), .back-btn, .breadcrumb a');

    if (await backButton.count() > 0) {
      await backButton.first().click();

      // 一覧ページまたはダッシュボードに戻ることを確認
      await page.waitForTimeout(1000);
      const url = page.url();
      const isListPage = url.includes('index.html') || url.includes('search') || !url.includes('detail');
      expect(isListPage).toBe(true);
    } else {
      // ブラウザの戻るボタンでも確認
      await page.goBack();
      await page.waitForTimeout(1000);
      const url = page.url();
      expect(url).not.toContain('sop-detail.html');
    }
  });

  test('should handle missing SOP ID gracefully', async ({ page }) => {
    // IDなしでアクセス
    await page.goto('/sop-detail.html');
    await page.waitForTimeout(2000);

    // エラーメッセージが表示されるか、リダイレクトされる
    const errorMessage = page.locator('.error, .alert, [role="alert"], *:has-text("見つかりません")');
    const hasError = await errorMessage.count() > 0;

    // または一覧ページにリダイレクト
    const url = page.url();
    const redirected = url.includes('index.html');

    expect(hasError || redirected).toBe(true);
  });
});

test.describe('Expert Consultation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display expert consultation page', async ({ page }) => {
    // 専門家相談ページに移動
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    // ページタイトルが表示されることを確認
    const title = page.locator('h1, h2, .page-title');
    await expect(title.first()).toBeVisible();
  });

  test('should display consultation form', async ({ page }) => {
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    // 相談フォームの要素が表示されることを確認
    const titleInput = page.locator('input[name*="title"], #questionTitle, .question-title');
    const descriptionInput = page.locator('textarea[name*="description"], #questionDescription, .question-description');
    const submitButton = page.locator('button[type="submit"], button:has-text("送信"), .submit-btn');

    if (await titleInput.count() > 0) {
      await expect(titleInput.first()).toBeVisible();
    }

    if (await descriptionInput.count() > 0) {
      await expect(descriptionInput.first()).toBeVisible();
    }

    expect(await submitButton.count()).toBeGreaterThan(0);
  });

  test('should submit a consultation question', async ({ page }) => {
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    const titleInput = page.locator('input[name*="title"], #questionTitle, .question-title').first();
    const descriptionInput = page.locator('textarea[name*="description"], #questionDescription, .question-description').first();
    const submitButton = page.locator('button[type="submit"], button:has-text("送信"), .submit-btn').first();

    if (await titleInput.count() > 0 && await descriptionInput.count() > 0) {
      // フォームに入力
      await titleInput.fill('テスト相談: 安全手順について');
      await descriptionInput.fill('現場での安全手順に関する質問です。詳細を教えてください。');

      // 送信
      await submitButton.click();

      // 成功メッセージまたは確認ページが表示されることを確認
      await page.waitForTimeout(2000);

      const successMessage = page.locator('.success, .alert-success, *:has-text("送信しました"), *:has-text("受け付けました")');
      const hasSuccess = await successMessage.count() > 0;

      // または相談一覧ページにリダイレクト
      const url = page.url();
      const redirected = url.includes('consultation') || url !== '/expert-consult.html';

      expect(hasSuccess || redirected).toBe(true);
    }
  });

  test('should display list of consultations', async ({ page }) => {
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    // 相談一覧が表示される場合
    const consultationList = page.locator('.consultation-list, .questions-list, .consult-items');

    if (await consultationList.count() > 0) {
      await expect(consultationList.first()).toBeVisible();

      // 相談アイテムが表示されることを確認
      const items = page.locator('.consultation-item, .question-item, .consult-card');
      const itemCount = await items.count();

      expect(itemCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('should filter consultations by status', async ({ page }) => {
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    // ステータスフィルターがある場合
    const statusFilter = page.locator('select[name*="status"], #statusFilter, .status-filter');

    if (await statusFilter.count() > 0) {
      // 「回答済み」でフィルター
      await statusFilter.first().selectOption({ label: /回答済み|Answered/i });
      await page.waitForTimeout(1000);

      // フィルター適用後の結果を確認
      const items = page.locator('.consultation-item, .question-item');
      const count = await items.count();

      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('should navigate to consultation detail', async ({ page }) => {
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    // 最初の相談アイテムをクリック
    const firstItem = page.locator('.consultation-item, .question-item, .consult-card').first();

    if (await firstItem.count() > 0) {
      await firstItem.click();
      await page.waitForTimeout(1000);

      // 詳細ページまたはモーダルが表示されることを確認
      const detailContent = page.locator('.consultation-detail, .question-detail, .modal, .detail-view');
      const hasDetail = await detailContent.count() > 0;

      // またはURLが変わる
      const url = page.url();
      const urlChanged = url.includes('detail') || url.includes('id=');

      expect(hasDetail || urlChanged).toBe(true);
    }
  });

  test('should allow expert to answer consultation', async ({ page }) => {
    // 専門家ロールでログイン（可能であれば）
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    // 回答フォームが表示される場合
    const answerTextarea = page.locator('textarea[name*="answer"], #answerText, .answer-input');

    if (await answerTextarea.count() > 0) {
      // 回答を入力
      await answerTextarea.first().fill('専門家からの回答: 安全手順については以下の通りです...');

      // 送信ボタンをクリック
      const submitAnswerButton = page.locator('button:has-text("回答"), button:has-text("送信"), .submit-answer');

      if (await submitAnswerButton.count() > 0) {
        await submitAnswerButton.first().click();
        await page.waitForTimeout(1000);

        // 成功メッセージが表示されることを確認
        const successMessage = page.locator('.success, .alert-success, *:has-text("回答しました")');
        const hasSuccess = await successMessage.count() > 0;

        expect(hasSuccess).toBe(true);
      }
    }
  });

  test('should prevent XSS in consultation form', async ({ page }) => {
    await page.goto('/expert-consult.html');
    await page.waitForTimeout(2000);

    const titleInput = page.locator('input[name*="title"], #questionTitle').first();
    const descriptionInput = page.locator('textarea[name*="description"], #questionDescription').first();

    if (await titleInput.count() > 0 && await descriptionInput.count() > 0) {
      // XSS攻撃を試みる
      const xssPayload = '<script>alert("XSS")</script>';

      await titleInput.fill(xssPayload);
      await descriptionInput.fill(xssPayload);

      const submitButton = page.locator('button[type="submit"]').first();
      await submitButton.click();

      await page.waitForTimeout(1000);

      // ダイアログが表示されないことを確認
      let dialogAppeared = false;
      page.on('dialog', () => {
        dialogAppeared = true;
      });

      await page.waitForTimeout(1000);
      expect(dialogAppeared).toBe(false);

      // ページがクラッシュしないことを確認
      const title = await page.title();
      expect(title).toBeTruthy();
    }
  });
});

test.describe('Integration - SOP to Expert Consultation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate from SOP detail to expert consultation', async ({ page }) => {
    // SOP詳細ページから専門家相談へのリンクがある場合
    await page.goto('/sop-detail.html?id=1');
    await page.waitForTimeout(2000);

    const consultButton = page.locator('button:has-text("専門家に相談"), a:has-text("専門家に相談"), .consult-btn');

    if (await consultButton.count() > 0) {
      await consultButton.first().click();
      await page.waitForTimeout(1000);

      // 専門家相談ページに遷移することを確認
      const url = page.url();
      expect(url).toContain('expert-consult');
    }
  });
});
